"""
Document & Newspaper Highlighter Engine (Vox / Johnny Harris Style).
Generates cinematic animated newspaper & declassified FBI document clips with:
- Vintage paper texture & newspaper grid
- Red "DECLASSIFIED FILE" archive stamp
- Smooth Ken Burns camera zoom into the key evidence
- Animated neon yellow highlighter pen sweep across key phrases
- Fully responsive for both 9:16 Vertical (1080x1920) and 16:9 Horizontal (1920x1080)
"""
from __future__ import annotations

import math
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


def _get_font(name: str, size: int) -> ImageFont.FreeTypeFont:
    windows_fonts = {
        "serif_bold": "C:/Windows/Fonts/georgiab.ttf",
        "serif": "C:/Windows/Fonts/georgia.ttf",
        "sans_bold": "C:/Windows/Fonts/arialbd.ttf",
        "sans": "C:/Windows/Fonts/arial.ttf",
        "mono": "C:/Windows/Fonts/consola.ttf",
    }
    path = windows_fonts.get(name, "C:/Windows/Fonts/arial.ttf")
    if Path(path).exists():
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            pass
    return ImageFont.load_default()


def create_base_newspaper(
    headline: str,
    dateline: str,
    lead_paragraph: str,
    key_quote: str,
    aspect_ratio: str = "vertical",
    paper_title: str = "THE INVESTIGATION CHRONICLE",
) -> tuple[Image.Image, tuple[int, int, int, int]]:
    """
    Renders high-res vintage document/newspaper page formatted specifically
    for either 9:16 Vertical (Shorts) or 16:9 Horizontal (Docs).
    """
    if aspect_ratio == "vertical":
        width, height = 1600, 2844  # 9:16 ratio base canvas
    else:
        width, height = 2560, 1440  # 16:9 ratio base canvas

    img = Image.new("RGB", (width, height), color="#f7f1e3")
    draw = ImageDraw.Draw(img)

    margin = 80
    font_title = _get_font("serif_bold", 78 if aspect_ratio == "vertical" else 72)
    font_meta = _get_font("sans_bold", 26)
    font_headline = _get_font("serif_bold", 80 if aspect_ratio == "vertical" else 88)
    font_body = _get_font("serif", 34 if aspect_ratio == "vertical" else 30)
    font_quote = _get_font("serif_bold", 46 if aspect_ratio == "vertical" else 42)

    # Top Header Rules
    y = 90
    draw.line([(margin, y), (width - margin, y)], fill="#1f1f1f", width=4)
    draw.line([(margin, y + 8), (width - margin, y + 8)], fill="#444444", width=2)
    y += 26

    # Paper Title
    bbox_t = draw.textbbox((0, 0), paper_title, font=font_title)
    tw = bbox_t[2] - bbox_t[0]
    draw.text(((width - tw) // 2, y), paper_title, fill="#111111", font=font_title)
    y += bbox_t[3] - bbox_t[1] + 28

    # Sub-header bar
    draw.line([(margin, y), (width - margin, y)], fill="#444444", width=2)
    y += 12
    draw.text((margin + 10, y), dateline.upper(), fill="#333333", font=font_meta)
    label_report = "OFFICIAL INVESTIGATIVE DOSSIER"
    bbox_r = draw.textbbox((0, 0), label_report, font=font_meta)
    draw.text((width - margin - (bbox_r[2] - bbox_r[0]) - 10, y), label_report, fill="#333333", font=font_meta)
    y += 45
    draw.line([(margin, y), (width - margin, y)], fill="#1f1f1f", width=4)
    y += 40

    # Headline (Wrapped if long)
    words = headline.upper().split(" ")
    h_lines = []
    cur_line = []
    for w in words:
        test_line = " ".join(cur_line + [w])
        bw = draw.textbbox((0, 0), test_line, font=font_headline)[2]
        if bw < (width - 2 * margin):
            cur_line.append(w)
        else:
            h_lines.append(" ".join(cur_line))
            cur_line = [w]
    if cur_line:
        h_lines.append(" ".join(cur_line))

    for hl in h_lines[:2]:
        draw.text((margin, y), hl, fill="#0d0d0d", font=font_headline)
        y += 92

    y += 15
    draw.line([(margin, y), (width - margin, y)], fill="#666666", width=2)
    y += 45

    if aspect_ratio == "vertical":
        # Vertical Layout: Featured evidence quote block prominently in upper-middle
        draw.text((margin, y), "DECLASSIFIED EVIDENCE RECORD // EXHIBIT A", fill="#991b1b", font=_get_font("sans_bold", 30))
        y += 65

        # Key Quote Position
        quote_x = margin + 20
        quote_y = y
        bbox_q = draw.textbbox((quote_x, quote_y), key_quote, font=font_quote)
        quote_w = bbox_q[2] - bbox_q[0]
        quote_h = bbox_q[3] - bbox_q[1]

        # Draw quote text
        draw.text((quote_x, quote_y), key_quote, fill="#000000", font=font_quote)
        y += quote_h + 60

        draw.line([(margin, y), (width - margin, y)], fill="#cccccc", width=2)
        y += 45

        # 2 Sub-Columns for context with strict wrapping
        col_w = (width - 2 * margin - 80) // 2
        col1_x = margin
        col2_x = margin + col_w + 80

        c1_snippets = [
            "Official federal prison protocols remain active 24/7.",
            "Perimeter is guarded by armed military detachments.",
            "Surveillance cameras monitor every square meter.",
            "Inmates remain isolated under strict protocol.",
        ]
        c2_snippets = [
            "Transfers require special executive authorization.",
            "Blindfolds are placed on inmates during all transit.",
            "No spatial awareness of the facility is permitted.",
            "Official historical records verify zero escape attempts.",
        ]

        yc1 = y
        for text in c1_snippets:
            words = text.split(" ")
            line = ""
            for w in words:
                test = line + (" " if line else "") + w
                if draw.textbbox((0, 0), test, font=font_body)[2] < col_w:
                    line = test
                else:
                    draw.text((col1_x, yc1), line, fill="#2c2c2c", font=font_body)
                    yc1 += 44
                    line = w
            if line:
                draw.text((col1_x, yc1), line, fill="#2c2c2c", font=font_body)
                yc1 += 50

        yc2 = y
        for text in c2_snippets:
            words = text.split(" ")
            line = ""
            for w in words:
                test = line + (" " if line else "") + w
                if draw.textbbox((0, 0), test, font=font_body)[2] < col_w:
                    line = test
                else:
                    draw.text((col2_x, yc2), line, fill="#2c2c2c", font=font_body)
                    yc2 += 44
                    line = w
            if line:
                draw.text((col2_x, yc2), line, fill="#2c2c2c", font=font_body)
                yc2 += 50

        stamp_x = col1_x + 60
        stamp_y = yc1 + 120

    else:
        # Horizontal Layout (3 columns)
        col_w = (width - 2 * margin - 80) // 3
        col1_x = margin
        col2_x = margin + col_w + 40
        col3_x = col2_x + col_w + 40

        # Column 1
        yc1 = y
        for line in [lead_paragraph[:60], lead_paragraph[60:120], "Security protocols elevated to maximum tier.", "Surveillance continuous across exterior grounds."]:
            draw.text((col1_x, yc1), line, fill="#2c2c2c", font=font_body)
            yc1 += 46

        # Column 2 (Quote)
        yc2 = y
        draw.text((col2_x, yc2), "CONFIDENTIAL TRANSCRIPT:", fill="#991b1b", font=_get_font("sans_bold", 26))
        yc2 += 55
        quote_x = col2_x
        quote_y = yc2
        bbox_q = draw.textbbox((quote_x, quote_y), key_quote, font=font_quote)
        quote_w = bbox_q[2] - bbox_q[0]
        quote_h = bbox_q[3] - bbox_q[1]
        draw.text((quote_x, quote_y), key_quote, fill="#000000", font=font_quote)
        yc2 += quote_h + 35
        draw.text((col2_x, yc2), "All inmate communications strictly restricted.", fill="#2c2c2c", font=font_body)

        # Column 3
        yc3 = y
        for line in ["Solitary confinement active 23 hours a day.", "Guards escort inmates bent forward at 90 degrees.", "No natural sunlight reaches interior cell blocks."]:
            draw.text((col3_x, yc3), line, fill="#2c2c2c", font=font_body)
            yc3 += 46

        stamp_x = col1_x + 40
        stamp_y = yc1 + 80

    # Add red "DECLASSIFIED ARCHIVE" Stamp
    stamp_img = Image.new("RGBA", (480, 110), (0, 0, 0, 0))
    s_draw = ImageDraw.Draw(stamp_img)
    s_draw.rectangle([6, 6, 470, 100], outline="#dc2626", width=5)
    s_font = _get_font("sans_bold", 38)
    s_draw.text((25, 26), "DECLASSIFIED ARCHIVE", fill="#dc2626", font=s_font)
    stamp_rot = stamp_img.rotate(10, resample=Image.Resampling.BICUBIC, expand=True)

    img_rgba = img.convert("RGBA")
    img_rgba.paste(stamp_rot, (stamp_x, stamp_y), stamp_rot)
    img = img_rgba.convert("RGB")

    return img, (quote_x, quote_y, quote_w, quote_h)


def render_highlighter_video(
    headline: str,
    dateline: str,
    lead_paragraph: str,
    key_quote: str,
    output_path: Path,
    aspect_ratio: str = "vertical",  # "vertical" (1080x1920) or "horizontal" (1920x1080)
    paper_title: str = "THE INVESTIGATION CHRONICLE",
    duration_sec: float = 3.5,
    fps: int = 30,
) -> Path:
    """
    Renders an animated 1080p video with smooth zoom and yellow highlighter sweep.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if aspect_ratio == "vertical":
        out_w, out_h = 1080, 1920
    else:
        out_w, out_h = 1920, 1080

    base_img, (qx, qy, qw, qh) = create_base_newspaper(
        headline=headline,
        dateline=dateline,
        lead_paragraph=lead_paragraph,
        key_quote=key_quote,
        aspect_ratio=aspect_ratio,
        paper_title=paper_title,
    )

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

    # Highlight timeline:
    # 0 -> 22%: camera starts zooming into quote
    # 22% -> 72%: highlighter sweeps left to right
    # 72% -> 100%: hold on highlighted evidence
    sweep_start = int(0.22 * total_frames)
    sweep_end = int(0.72 * total_frames)

    target_cx = qx + qw / 2
    target_cy = qy + qh / 2
    base_cx = base_img.width / 2
    base_cy = base_img.height / 2

    for f in range(total_frames):
        t = f / max(1, total_frames - 1)  # 0.0 -> 1.0

        # Camera zoom: 1.0 -> 1.65 with smooth cosine curve
        zoom_factor = 1.0 + 0.65 * (1.0 - math.cos(t * math.pi / 2))
        cur_cx = base_cx + (target_cx - base_cx) * (0.80 * t)
        cur_cy = base_cy + (target_cy - base_cy) * (0.80 * t)

        crop_w = base_img.width / zoom_factor
        crop_h = crop_w * (out_h / out_w)

        left = int(cur_cx - crop_w / 2)
        top = int(cur_cy - crop_h / 2)
        right = int(left + crop_w)
        bottom = int(top + crop_h)

        # Ensure within image bounds
        if left < 0:
            right -= left
            left = 0
        if top < 0:
            bottom -= top
            top = 0
        if right > base_img.width:
            left -= (right - base_img.width)
            right = base_img.width
        if bottom > base_img.height:
            top -= (bottom - base_img.height)
            bottom = base_img.height

        frame_canvas = base_img.copy()

        # Draw highlighter
        if f >= sweep_start:
            h_prog = min(1.0, (f - sweep_start) / max(1, (sweep_end - sweep_start)))
            h_eased = 0.5 - 0.5 * math.cos(h_prog * math.pi)
            cur_hw = int(qw * h_eased)

            if cur_hw > 0:
                hl_overlay = Image.new("RGBA", frame_canvas.size, (255, 255, 255, 0))
                hl_draw = ImageDraw.Draw(hl_overlay)
                padding_y = 8
                hl_rect = [qx - 10, qy - padding_y, qx + cur_hw + 10, qy + qh + padding_y]
                # High-visibility neon yellow highlighter
                hl_draw.rectangle(hl_rect, fill=(255, 235, 59, 145))
                frame_canvas = Image.alpha_composite(frame_canvas.convert("RGBA"), hl_overlay).convert("RGB")

        # Crop and resize
        cropped = frame_canvas.crop((left, top, right, bottom))
        final_frame = cropped.resize((out_w, out_h), Image.Resampling.LANCZOS)
        proc.stdin.write(final_frame.tobytes())

    proc.stdin.close()
    proc.wait()
    print(f">> Documentary Newspaper Highlight rendered ({aspect_ratio}): {output_path}")
    return output_path


if __name__ == "__main__":
    out_vert = (Path(__file__).resolve().parent / "output/test_newspaper_vertical.mp4")
    render_highlighter_video(
        headline="Black Dolphin: Inmates Blindfolded for 24 Hours",
        dateline="October 14, 1999 • Sol-Iletsk, Russia",
        lead_paragraph="Located near the Kazakhstan border, Penal Colony No. 6 houses the most dangerous convicts in the nation.",
        key_quote="NOT A SINGLE PRISONER HAS EVER ESCAPED.",
        output_path=out_vert,
        aspect_ratio="vertical",
        duration_sec=3.5,
    )
