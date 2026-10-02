"""
Ken Burns Archival Photo Motion Engine (Vox / Johnny Harris Style).
Transforms static archival photos into cinematic motion clips:
- 2.5D smooth zoom / drift with cosine easing
- Blurred ambient background fill for vertical 9:16 Shorts (no empty black borders)
- Subtle dark vignette and documentary evidence stamp
- 60fps / 30fps 1080p MP4 output via direct FFmpeg raw frame pipe
"""
from __future__ import annotations

import math
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont


def _get_font(size: int, bold: bool = True) -> ImageFont.FreeTypeFont:
    path = "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"
    if Path(path).exists():
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            pass
    return ImageFont.load_default()


def apply_vignette(image: Image.Image, intensity: float = 0.5) -> Image.Image:
    """Applies a smooth dark radial vignette to the frame."""
    w, h = image.size
    vignette = Image.new("L", (w, h), 0)
    draw = ImageDraw.Draw(vignette)
    
    # Draw radial gradient via concentric ellipses
    max_radius = math.hypot(w / 2, h / 2)
    steps = 40
    for i in range(steps):
        r_frac = (i + 1) / steps
        rx = (w / 2) * (1.0 + 0.4 * r_frac)
        ry = (h / 2) * (1.0 + 0.4 * r_frac)
        alpha = int(255 * (1.0 - (1.0 - r_frac) ** 2) * intensity)
        draw.ellipse(
            [w / 2 - rx, h / 2 - ry, w / 2 + rx, h / 2 + ry],
            outline=alpha,
            width=int(max_radius / steps) + 2
        )
    
    vignette = vignette.filter(ImageFilter.GaussianBlur(radius=int(w * 0.05)))
    dark_layer = Image.new("RGB", (w, h), (0, 0, 0))
    return Image.composite(dark_layer, image, vignette)


def render_kenburns_clip(
    image_path: Path,
    output_path: Path,
    duration_sec: float = 4.0,
    fps: int = 30,
    aspect_ratio: str = "vertical",  # "vertical" (1080x1920) or "horizontal" (1920x1080)
    badge_text: str = "DEEP INVESTIGATION DOSSIER",
    zoom_direction: str = "in",  # "in" or "out"
) -> Path:
    """
    Renders a cinematic Ken Burns clip from a single archival photo.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if aspect_ratio == "vertical":
        out_w, out_h = 1080, 1920
    else:
        out_w, out_h = 1920, 1080

    src_img = Image.open(image_path).convert("RGB")
    total_frames = int(duration_sec * fps)

    ffmpeg_cmd = [
        "ffmpeg", "-hide_banner", "-loglevel", "warning", "-y",
        "-f", "rawvideo",
        "-pix_fmt", "rgb24",
        "-s", f"{out_w}x{out_h}",
        "-r", str(fps),
        "-i", "-",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        str(output_path)
    ]
    proc = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE)

    # For vertical videos with landscape photos: create a heavily blurred ambient background
    blurred_bg = None
    if aspect_ratio == "vertical" and src_img.width > src_img.height:
        # Scale to fill vertical height, heavily blur
        bg_scale = max(out_w / src_img.width, out_h / src_img.height) * 1.1
        bg_w, bg_h = int(src_img.width * bg_scale), int(src_img.height * bg_scale)
        blurred_bg = src_img.resize((bg_w, bg_h), Image.Resampling.BILINEAR)
        # Crop to canvas
        left = (bg_w - out_w) // 2
        top = (bg_h - out_h) // 2
        blurred_bg = blurred_bg.crop((left, top, left + out_w, top + out_h))
        blurred_bg = blurred_bg.filter(ImageFilter.GaussianBlur(radius=35))
        # Darken ambient background
        dark_dim = Image.new("RGB", (out_w, out_h), (12, 12, 16))
        blurred_bg = Image.blend(blurred_bg, dark_dim, 0.55)

    badge_font = _get_font(24, bold=True)
    sub_font = _get_font(18, bold=False)

    for f in range(total_frames):
        t = f / max(1, total_frames - 1)  # 0.0 -> 1.0
        # Cosine smooth easing
        eased_t = 0.5 - 0.5 * math.cos(t * math.pi)

        if zoom_direction == "in":
            scale = 1.0 + 0.18 * eased_t
        else:
            scale = 1.18 - 0.18 * eased_t

        frame_canvas = Image.new("RGB", (out_w, out_h), (10, 10, 12))
        if blurred_bg:
            frame_canvas.paste(blurred_bg, (0, 0))

        # Size of the foreground photo
        if aspect_ratio == "vertical":
            # Scale photo to comfortably fit 90% of width with subtle border
            fit_w = int(out_w * 0.92 * scale)
            fit_h = int((src_img.height / src_img.width) * fit_w)
            # Center coordinates
            cur_x = (out_w - fit_w) // 2
            cur_y = (out_h - fit_h) // 2
            photo_resized = src_img.resize((fit_w, fit_h), Image.Resampling.BILINEAR)

            # Paste with a sleek 2px white-film border
            border_box = [cur_x - 4, cur_y - 4, cur_x + fit_w + 4, cur_y + fit_h + 4]
            draw = ImageDraw.Draw(frame_canvas)
            draw.rectangle(border_box, fill="#1c1c24", outline="#ffffff", width=2)
            frame_canvas.paste(photo_resized, (cur_x, cur_y))
        else:
            # Full 16:9 cinematic fill with Ken Burns crop
            crop_scale = scale * max(out_w / src_img.width, out_h / src_img.height)
            cw, ch = int(src_img.width * crop_scale), int(src_img.height * crop_scale)
            scaled = src_img.resize((cw, ch), Image.Resampling.BILINEAR)
            cl = (cw - out_w) // 2
            ct = (ch - out_h) // 2
            frame_canvas = scaled.crop((cl, ct, cl + out_w, ct + out_h))

        # Apply dark cinematic vignette
        frame_canvas = apply_vignette(frame_canvas, intensity=0.45)

        # Draw Archival Badge Overlay
        draw = ImageDraw.Draw(frame_canvas)
        badge_y = out_h - 180 if aspect_ratio == "vertical" else out_h - 110
        badge_x = 70
        badge_w = 420
        badge_h = 56
        
        # Translucent dark red / black badge box
        badge_box = [badge_x, badge_y, badge_x + badge_w, badge_y + badge_h]
        draw.rectangle(badge_box, fill="#111116", outline="#dc2626", width=2)
        # Red indicator dot
        draw.ellipse([badge_x + 16, badge_y + 18, badge_x + 36, badge_y + 38], fill="#ef4444")
        draw.text((badge_x + 48, badge_y + 14), badge_text.upper(), fill="#ffffff", font=badge_font)

        proc.stdin.write(frame_canvas.tobytes())

    proc.stdin.close()
    proc.wait()
    print(f">> Ken Burns motion clip rendered: {output_path} ({duration_sec}s)")
    return output_path


if __name__ == "__main__":
    sample_img = Path("d:/facts_yt/dark_case_studio/assets/downloads/Black_Dolphin_Prison/lead_archive.jpg")
    if sample_img.exists():
        out = Path("d:/facts_yt/dark_case_studio/output/test_kenburns_vertical.mp4")
        render_kenburns_clip(sample_img, out, duration_sec=3.5, aspect_ratio="vertical", badge_text="EVIDENCE FILE: #01")
