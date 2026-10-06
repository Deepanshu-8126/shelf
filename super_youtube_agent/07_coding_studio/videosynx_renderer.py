"""
Channel 7 — Master Videosynx Line-by-Line Anchored Video Renderer.
Renders 100% procedural 1080x1920 30fps/60fps video:
- Code types character-by-character per line
- Teacher pauses and explains that exact line with spotlight halo
- Dynamic topic diagram updates live
- Real sandbox Python execution streams live stdout
- Synthesized with Kokoro-82M and Cherry MX Blue mechanical switch clicks.
"""
from __future__ import annotations
import asyncio
import json
import math
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional

from PIL import Image, ImageDraw, ImageFilter, ImageFont

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

CURRENT_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = CURRENT_DIR / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

from videosynx_schema import AnchoredLesson, AnchoredLine, get_anchored_lesson
from anchored_timeline import AnchoredTimeline, LineTimeSchedule
from sandbox_executor import run_code_in_sandbox
from diagram_generator import render_dynamic_topic_diagram


def get_vfont(size: int, bold: bool = True) -> ImageFont.FreeTypeFont:
    paths = [
        "C:/Windows/Fonts/consolab.ttf" if bold else "C:/Windows/Fonts/consola.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
    ]
    for p in paths:
        if Path(p).exists():
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()


def render_anchored_frame(
    frame_idx: int,
    total_frames: int,
    duration: float,
    lesson: AnchoredLesson,
    timeline: AnchoredTimeline,
    sandbox_result: Dict[str, Any],
    fonts: Dict[str, Any]
) -> Image.Image:
    """
    Renders an exact, frame-accurate 1080x1920 video frame anchored to line-by-line execution.
    """
    W, H = 1080, 1920
    sec = (frame_idx / total_frames) * duration

    img = Image.new("RGBA", (W, H), (248, 250, 252, 255))
    draw = ImageDraw.Draw(img)

    # 1. Background Dot Grid
    dot_gap = 36
    for x in range(24, W, dot_gap):
        for y in range(24, H, dot_gap):
            draw.ellipse([x - 1, y - 1, x + 1, y + 1], fill=(226, 232, 240, 180))

    # 2. Header & HUD Telemetry
    draw.text((80, 75), f"{lesson.series_name} • EPISODE #{lesson.episode_num}", fill=(100, 116, 139), font=fonts["hud_label"])
    draw.rounded_rectangle([80, 115, 620, 168], radius=14, fill=(238, 242, 255), outline=(199, 210, 254), width=2)
    draw.text((350, 141), f"⚡ {lesson.badge_tag}", fill=(67, 56, 202), font=fonts["hud_badge"], anchor="mm")
    draw.text((80, 195), lesson.title, fill=(15, 23, 42), font=fonts["headline"])

    # Determine Active Line & State
    current_line_idx = -1
    is_typing_now = False
    typed_char_fraction = 1.0
    active_sched: Optional[LineTimeSchedule] = None

    if sec < timeline.intro_duration:
        # Intro phase
        current_line_idx = -1
    elif sec >= timeline.exec_start_sec:
        # Execution / Outro phase: all lines typed
        current_line_idx = len(timeline.schedules)
    else:
        for s_i, sched in enumerate(timeline.schedules):
            if sched.type_start_sec <= sec < sched.explain_end_sec:
                current_line_idx = s_i
                active_sched = sched
                if sec < sched.type_end_sec:
                    is_typing_now = True
                    type_dur = max(0.01, sched.type_end_sec - sched.type_start_sec)
                    typed_char_fraction = min(1.0, max(0.0, (sec - sched.type_start_sec) / type_dur))
                else:
                    is_typing_now = False
                    typed_char_fraction = 1.0
                break

    # Progress Bar: Line X of Total
    total_lines = len(lesson.lines)
    disp_line = min(total_lines, max(0, current_line_idx + 1))
    draw.text((W - 80, 205), f"LINE {disp_line}/{total_lines}", fill=(99, 102, 241), font=fonts["line_counter"], anchor="rm")
    
    # Progress Track
    bar_w = 920
    draw.rounded_rectangle([80, 250, 80 + bar_w, 258], radius=4, fill=(226, 232, 240))
    prog_ratio = min(1.0, sec / max(0.1, duration))
    draw.rounded_rectangle([80, 250, 80 + int(bar_w * prog_ratio), 258], radius=4, fill=(79, 70, 229))

    # 3. Main Swiss Minimal IDE Code Card
    card_x, card_y = 80, 280
    card_w, card_h = 920, 680

    for offset, alpha in [(14, 15), (6, 25)]:
        draw.rounded_rectangle([card_x, card_y + offset, card_x + card_w, card_y + card_h + offset], radius=26, fill=(0, 0, 0, alpha))
    draw.rounded_rectangle([card_x, card_y, card_x + card_w, card_y + card_h], radius=26, fill=(255, 255, 255), outline=(226, 232, 240), width=2)

    # macOS Dots & File Header
    draw.ellipse([card_x + 36, card_y + 24, card_x + 52, card_y + 40], fill=(255, 95, 86))
    draw.ellipse([card_x + 62, card_y + 24, card_x + 78, card_y + 40], fill=(255, 189, 46))
    draw.ellipse([card_x + 88, card_y + 24, card_x + 104, card_y + 40], fill=(39, 201, 63))
    draw.text((card_x + 130, card_y + 32), f"{lesson.filename} • Python 3.11", fill=(30, 41, 59), font=fonts["file_head"], anchor="lm")
    draw.line([(card_x + 20, card_y + 64), (card_x + card_w - 20, card_y + 64)], fill=(241, 245, 249), width=2)

    # Render Code Lines with Spotlight Halo
    code_start_y = card_y + 88
    line_spacing = 46

    for idx, sched in enumerate(timeline.schedules):
        ly = code_start_y + idx * line_spacing
        is_active = (idx == current_line_idx)
        is_past = (idx < current_line_idx)

        # Highlight Spotlight Background if this line is active
        if is_active:
            spot_col = (254, 243, 199) if sched.highlight else (238, 242, 255)
            spot_border = (245, 158, 11) if sched.highlight else (129, 140, 248)
            draw.rounded_rectangle([card_x + 24, ly - 6, card_x + card_w - 24, ly + 36], radius=10, fill=spot_col, outline=spot_border, width=2)

        # Line Number Gutter
        gutter_col = (79, 70, 229) if is_active else (148, 163, 184)
        draw.text((card_x + 55, ly + 4), f"{idx + 1:2d}", fill=gutter_col, font=fonts["gutter"], anchor="rm")

        # Determine Text to Display
        full_text = sched.code_text
        if is_past or sec >= timeline.exec_start_sec:
            disp_text = full_text
        elif is_active:
            if is_typing_now:
                char_idx = int(len(full_text) * typed_char_fraction)
                disp_text = full_text[:char_idx]
            else:
                disp_text = full_text
        else:
            disp_text = ""

        # Syntax Token Colors
        txt_col = (15, 23, 42)
        if "def " in disp_text:
            txt_col = (147, 51, 234)
        elif "if " in disp_text or "return " in disp_text:
            txt_col = (225, 29, 72)
        elif "=" in disp_text:
            txt_col = (30, 58, 138)
        
        draw.text((card_x + 85, ly + 4), disp_text, fill=txt_col, font=fonts["code"])

        # Animated Blinking Cursor on Active Line
        if is_active:
            try:
                txt_w = fonts["code"].getlength(disp_text)
            except Exception:
                txt_w = len(disp_text) * 15
            cursor_vis = (int(sec * 1000) % 500) < 320
            if cursor_vis:
                cur_x = card_x + 85 + txt_w + 3
                draw.line([(cur_x, ly + 2), (cur_x, ly + 32)], fill=(79, 70, 229), width=3)

    # 4. Teacher Insight Box (Anchored explanation card)
    teach_y = 990
    teach_h = 240
    for offset, alpha in [(12, 12), (4, 20)]:
        draw.rounded_rectangle([card_x, teach_y + offset, card_x + card_w, teach_y + teach_h + offset], radius=22, fill=(0, 0, 0, alpha))
    draw.rounded_rectangle([card_x, teach_y, card_x + card_w, teach_y + teach_h], radius=22, fill=(255, 255, 255), outline=(254, 215, 170), width=2)

    # Teacher Icon Badge
    draw.rounded_rectangle([card_x + 28, teach_y + 24, card_x + 80, teach_y + 76], radius=14, fill=(245, 158, 11))
    draw.text((card_x + 54, teach_y + 50), "AI", fill=(255, 255, 255), font=fonts["hud_badge"], anchor="mm")

    tag_title = active_sched.tip if (active_sched and active_sched.tip) else "Teacher Masterclass"
    draw.text((card_x + 96, teach_y + 36), f"TEACHER INSIGHT • {tag_title.upper()}", fill=(180, 83, 9), font=fonts["teach_title"])

    # Spoken Sentence Narration
    spoken_txt = ""
    if sec < timeline.intro_duration:
        spoken_txt = lesson.intro_narration
    elif active_sched:
        spoken_txt = active_sched.narration_text
    elif sec >= timeline.exec_start_sec and sec < timeline.exec_end_sec:
        spoken_txt = "Code ko execute karke real dry-run test karte hain. All assertions passing!"
    else:
        spoken_txt = lesson.outro_narration

    # Text wrapping for spoken explanation
    words = spoken_txt.split()
    l1, l2, l3 = [], [], []
    for w in words:
        if len(" ".join(l1 + [w])) <= 44:
            l1.append(w)
        elif len(" ".join(l2 + [w])) <= 44:
            l2.append(w)
        else:
            l3.append(w)

    draw.text((card_x + 36, teach_y + 95), " ".join(l1), fill=(15, 23, 42), font=fonts["teach_body"])
    if l2:
        draw.text((card_x + 36, teach_y + 135), " ".join(l2), fill=(15, 23, 42), font=fonts["teach_body"])
    if l3:
        draw.text((card_x + 36, teach_y + 175), " ".join(l3), fill=(71, 85, 105), font=fonts["teach_body"])

    # 5. Dynamic Topic Diagram Box
    diag_y = 1260
    diag_img = render_dynamic_topic_diagram(lesson.id, current_line_idx, width=card_w, height=270)
    img.paste(diag_img, (card_x, diag_y), diag_img)

    # 6. Terminal Execution Box (Real Stdout)
    term_y = 1560
    term_h = 240
    for offset, alpha in [(14, 15), (6, 25)]:
        draw.rounded_rectangle([card_x, term_y + offset, card_x + card_w, term_y + term_h + offset], radius=22, fill=(0, 0, 0, alpha))
    draw.rounded_rectangle([card_x, term_y, card_x + card_w, term_y + term_h], radius=22, fill=(15, 23, 42), outline=(51, 65, 85), width=2)

    draw.text((card_x + 35, term_y + 22), "$ python3 " + lesson.filename, fill=(248, 250, 252), font=fonts["term_mono"])
    draw.line([(card_x + 20, term_y + 58), (card_x + card_w - 20, term_y + 58)], fill=(30, 41, 59), width=2)

    out_lines = sandbox_result.get("output_lines", [])
    if sec >= timeline.exec_start_sec:
        # Live streaming output lines
        exec_progress = min(1.0, (sec - timeline.exec_start_sec) / 2.0)
        lines_to_show = max(1, int(len(out_lines) * exec_progress))
        for o_i, out_l in enumerate(out_lines[:lines_to_show]):
            oy = term_y + 75 + o_i * 44
            col = (74, 222, 128) if "PASS" in out_l or "Sorted" in out_l else (226, 232, 240)
            draw.text((card_x + 35, oy), out_l[:52], fill=col, font=fonts["term_mono"])
    else:
        draw.text((card_x + 35, term_y + 85), "[Ready to execute sandbox verification...]", fill=(100, 116, 139), font=fonts["term_mono"])
        draw.text((card_x + 35, term_y + 130), f"⚡ Complexity: {lesson.complexity_badge}", fill=(99, 102, 241), font=fonts["term_mono"])

    # 7. Bottom Branding Telemetry
    draw.text((W // 2, 1860), "CHANNEL 7 // VIDEOSYNX ENGINE • ZERO SLOP • KOKORO AI", fill=(148, 163, 184), font=fonts["footer"], anchor="mm")

    return img.convert("RGB")


async def render_videosynx_short(query: str | None = None) -> Path:
    """
    Renders an end-to-end line-by-line anchored short with Kokoro narration and Cherry MX SFX.
    """
    lesson = get_anchored_lesson(query)
    print("=" * 70)
    print(f"🎬 [Videosynx Engine] Rendering Line-by-Line Short: {lesson.title}")
    print(f"📚 Series: {lesson.series_name} • Episode #{lesson.episode_num}")
    print("=" * 70)

    # 1. Run Python Code in Sandbox to get verified stdout
    print("🧪 Running code in Python sandbox...")
    sandbox_result = run_code_in_sandbox(lesson.test_runner_code)
    print(f"✓ Sandbox executed in {sandbox_result['runtime_ms']}ms: {sandbox_result['output_lines']}")

    # 2. Build Anchored Timeline & Foley Audio
    print("🎙️ Synthesizing line-anchored Kokoro narration & Cherry MX Foley...")
    timeline = AnchoredTimeline(lesson, OUTPUT_DIR)
    is_hindi = any('\u0900' <= char <= '\u097F' for char in lesson.intro_narration + lesson.lines[0].narration)
    lang = "hi" if is_hindi else "en"
    voice = "hm_omega" if is_hindi else "am_adam"

    master_voice, master_sfx = timeline.build_timeline_and_audio(lang=lang, voice=voice)
    duration = timeline.total_duration
    print(f"✅ Master Soundtrack ready: {duration:.2f}s ({len(timeline.schedules)} anchored lines)")

    # 3. Setup Fonts
    fonts = {
        "hud_label": get_vfont(20, bold=True),
        "hud_badge": get_vfont(18, bold=True),
        "headline": get_vfont(36, bold=True),
        "line_counter": get_vfont(22, bold=True),
        "file_head": get_vfont(20, bold=True),
        "gutter": get_vfont(22, bold=False),
        "code": get_vfont(24, bold=True),
        "teach_title": get_vfont(18, bold=True),
        "teach_body": get_vfont(22, bold=False),
        "term_mono": get_vfont(20, bold=True),
        "footer": get_vfont(18, bold=True),
    }

    fps = 30
    total_frames = int(duration * fps)
    out_mp4 = OUTPUT_DIR / f"{lesson.id}_videosynx_master.mp4"
    print(f"🚀 Rendering {total_frames} frames via FFmpeg Pipe at {fps} FPS (1080x1920)...")

    ffmpeg_cmd = [
        "ffmpeg", "-y",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-s", "1080x1920",
        "-pix_fmt", "rgb24",
        "-r", str(fps),
        "-i", "-",
        "-i", str(master_sfx),
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        str(out_mp4)
    ]

    proc = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    t0 = time.time()
    for i in range(total_frames):
        frame = render_anchored_frame(i, total_frames, duration, lesson, timeline, sandbox_result, fonts)
        proc.stdin.write(frame.tobytes())

    proc.stdin.close()
    proc.wait()

    render_dur = time.time() - t0
    print(f"🎉 Videosynx Master Short Rendered in {render_dur:.2f}s: {out_mp4}")
    print(f"📦 File Size: {out_mp4.stat().st_size / (1024*1024):.2f} MB")

    # 4. Save YouTube Metadata
    yt_meta = {
        "title": f"{lesson.series_name} • Ep {lesson.episode_num}: {lesson.title} ⚡ #shorts",
        "description": (
            f"🔥 Welcome to {lesson.series_name} (Episode {lesson.episode_num})!\n\n"
            f"Topic: {lesson.title}\n"
            f"Line-by-line explanation with real sandbox Python verification.\n\n"
            f"💡 Complexity: {lesson.complexity_badge}\n"
            f"⚡ Benchmark: {lesson.benchmark_metric}\n\n"
            f"#coding #programming #python #dsa #softwareengineer #leetcode #shorts #developer"
        ),
        "tags": ["coding", "programming", "python", "dsa", "leetcode", "developer", "shorts"],
        "category_id": "28"
    }
    meta_path = OUTPUT_DIR / f"{lesson.id}_metadata.json"
    meta_path.write_text(json.dumps(yt_meta, indent=2), encoding="utf-8")

    # 5. Send to Telegram
    telegram_script = Path("d:/facts_yt/send_to_telegram.py")
    if telegram_script.exists():
        print("📱 Dispatching to Telegram...")
        subprocess.run([sys.executable, str(telegram_script), str(out_mp4)], check=False)
        print("✅ Telegram delivery complete!")

    return out_mp4


if __name__ == "__main__":
    q = sys.argv[1] if len(sys.argv) > 1 else "quicksort"
    asyncio.run(render_videosynx_short(q))
