"""
Cinematic Map & Satellite Radar Locator Engine (Vox / Johnny Harris Style).
Generates motion-graphic coordinates & pulsing radar target clips:
- Dark topographic / tactical grid with latitude & longitude telemetry
- Pulsing radar reticle over the mystery location
- Smooth camera zoom into target coordinates
- 1080p 60fps/30fps MP4 (Supports Vertical 9:16 Shorts & Horizontal 16:9)
"""
from __future__ import annotations

import math
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


def _get_font(size: int, bold: bool = True) -> ImageFont.FreeTypeFont:
    path = "C:/Windows/Fonts/consola.ttf" if not bold else "C:/Windows/Fonts/arialbd.ttf"
    if Path(path).exists():
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            pass
    return ImageFont.load_default()


def render_map_locator_clip(
    location_name: str,
    coordinates: str,
    output_path: Path,
    aspect_ratio: str = "vertical",  # "vertical" or "horizontal"
    duration_sec: float = 3.5,
    fps: int = 30,
) -> Path:
    """
    Renders a high-tech tactical satellite map locator with pulsing radar ring.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if aspect_ratio == "vertical":
        out_w, out_h = 1080, 1920
    else:
        out_w, out_h = 1920, 1080

    total_frames = int(duration_sec * fps)
    cx, cy = out_w // 2, out_h // 2

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

    font_title = _get_font(42, bold=True)
    font_coords = _get_font(28, bold=False)
    font_telemetry = _get_font(20, bold=False)

    for f in range(total_frames):
        t = f / max(1, total_frames - 1)  # 0.0 -> 1.0

        # Dark tactical navy / charcoal background
        frame = Image.new("RGB", (out_w, out_h), color=(10, 14, 22))
        draw = ImageDraw.Draw(frame)

        # 1. Draw Grid Lines (Subtle tactical radar grid)
        grid_spacing = 80
        grid_alpha_color = (25, 36, 52)
        for gx in range(0, out_w, grid_spacing):
            draw.line([(gx, 0), (gx, out_h)], fill=grid_alpha_color, width=1)
        for gy in range(0, out_h, grid_spacing):
            draw.line([(0, gy), (out_w, gy)], fill=grid_alpha_color, width=1)

        # 2. Concentric Tactical Radar Rings
        max_r = 380
        for ring_r in [120, 240, 360]:
            draw.ellipse(
                [cx - ring_r, cy - ring_r, cx + ring_r, cy + ring_r],
                outline=(38, 55, 78),
                width=1
            )

        # 3. Rotating Radar Sweep Line
        angle = (f * 6.5) * (math.pi / 180)
        sweep_x = cx + int(max_r * math.cos(angle))
        sweep_y = cy + int(max_r * math.sin(angle))
        draw.line([(cx, cy), (sweep_x, sweep_y)], fill=(56, 189, 248), width=2)

        # 4. Pulsing Neon Target Reticle
        pulse = 0.5 + 0.5 * math.sin(f * 0.35)
        reticle_r = int(45 + 15 * pulse)
        # Outer red ring
        draw.ellipse(
            [cx - reticle_r, cy - reticle_r, cx + reticle_r, cy + reticle_r],
            outline=(239, 68, 68),
            width=3
        )
        # Center target dot
        draw.ellipse([cx - 6, cy - 6, cx + 6, cy + 6], fill=(239, 68, 68))
        # Crosshair lines
        ch_len = 30
        draw.line([(cx - ch_len - reticle_r, cy), (cx - reticle_r + 5, cy)], fill=(239, 68, 68), width=2)
        draw.line([(cx + reticle_r - 5, cy), (cx + ch_len + reticle_r, cy)], fill=(239, 68, 68), width=2)
        draw.line([(cx, cy - ch_len - reticle_r), (cx, cy - reticle_r + 5)], fill=(239, 68, 68), width=2)
        draw.line([(cx, cy + reticle_r - 5), (cx, cy + ch_len + reticle_r)], fill=(239, 68, 68), width=2)

        # 5. Telemetry & Target Header
        # Top-left telemetry box
        top_y = 140 if aspect_ratio == "vertical" else 70
        draw.text((80, top_y), f"SATELLITE RECON PROTOCOL // ACTIVE", fill=(56, 189, 248), font=font_telemetry)
        draw.text((80, top_y + 35), f"TARGET: {location_name.upper()}", fill=(255, 255, 255), font=font_title)
        draw.text((80, top_y + 90), f"COORDINATES: {coordinates}", fill=(239, 68, 68), font=font_coords)

        # Frame progress counter (military timecode)
        timecode = f"REC 00:00:{f//30:02d}.{int((f%30)*(100/30)):02d}"
        draw.text((out_w - 320, top_y), timecode, fill=(239, 68, 68), font=font_telemetry)

        # Corner Tactical Crosses
        c_size = 20
        draw.line([(50, 50), (50 + c_size, 50)], fill=(56, 189, 248), width=2)
        draw.line([(50, 50), (50, 50 + c_size)], fill=(56, 189, 248), width=2)
        draw.line([(out_w - 50, 50), (out_w - 50 - c_size, 50)], fill=(56, 189, 248), width=2)
        draw.line([(out_w - 50, 50), (out_w - 50, 50 + c_size)], fill=(56, 189, 248), width=2)

        proc.stdin.write(frame.tobytes())

    proc.stdin.close()
    proc.wait()
    print(f">> Map Locator motion clip rendered: {output_path}")
    return output_path


if __name__ == "__main__":
    out_map = (Path(__file__).resolve().parent / "output/test_map_locator.mp4")
    render_map_locator_clip(
        location_name="Black Dolphin Penal Colony No. 6",
        coordinates="51°09'21\"N 54°59'35\"E",
        output_path=out_map,
        aspect_ratio="vertical",
        duration_sec=3.0,
    )
