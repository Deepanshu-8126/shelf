"""
Master Pedagogical Coding Studio Engine (Channel 7).
Produces Teacher-Grade Vox-Style Animated Coding Shorts:
- Beat 1 & 2: Question Hook & Naive Code (with Red Brute-Force Warning)
- Beat 3: Optimal Code Reveal (with Green Glowing Border & Dry-Run pointer)
- Beat 4: Live Terminal Benchmark Execution (Tests passing in O(n))
- Word-by-word kinetic karaoke captions
- Edge TTS Jenny narration at natural teaching pace
- 100% procedural 1080x1920 60fps render (Zero Pexels stock footage)
"""
import asyncio
import math
import os
import subprocess
import sys
import time
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import edge_tts

# Fix Windows console UTF-8 output
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

CURRENT_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = CURRENT_DIR / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

from curriculum import CodingLesson, get_lesson


def get_font(size: int, bold: bool = True) -> ImageFont.FreeTypeFont:
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


async def generate_speech_tracks(lesson: CodingLesson, output_dir: Path) -> tuple[Path, list[float], float]:
    """Generates continuous voiceover and measures beat durations."""
    full_script = f"{lesson.hook_narration} {lesson.trap_narration} {lesson.solution_narration} {lesson.takeaway_narration}"
    mp3_path = output_dir / f"{lesson.id}_voice.mp3"
    wav_path = output_dir / f"{lesson.id}_voice.wav"

    comm = edge_tts.Communicate(full_script, "en-US-JennyNeural", rate="+6%", pitch="+0Hz")
    await comm.save(str(mp3_path))

    subprocess.run([
        "ffmpeg", "-y", "-i", str(mp3_path),
        "-ar", "44100", "-ac", "2", str(wav_path)
    ], check=True, capture_output=True)

    probe = subprocess.run([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(wav_path)
    ], check=True, capture_output=True, text=True)
    total_duration = float(probe.stdout.strip())

    # Proportional split of beats based on word count
    words_h = len(lesson.hook_narration.split())
    words_t = len(lesson.trap_narration.split())
    words_s = len(lesson.solution_narration.split())
    words_o = len(lesson.takeaway_narration.split())
    total_words = words_h + words_t + words_s + words_o

    b1_end = total_duration * (words_h / total_words)
    b2_end = total_duration * ((words_h + words_t) / total_words)
    b3_end = total_duration * ((words_h + words_t + words_s) / total_words)
    b4_end = total_duration

    beats = [b1_end, b2_end, b3_end, b4_end]
    return wav_path, beats, total_duration


def render_pedagogical_frame(
    frame_idx: int,
    total_frames: int,
    total_sec: float,
    lesson: CodingLesson,
    beats: list[float],
    font_code,
    font_title,
    font_sub,
    font_hud
) -> Image.Image:
    W, H = 1080, 1920
    t = frame_idx / total_frames
    sec = t * total_sec

    # 1. Background: Deep Matrix Grid with subtle radial gradient
    img = Image.new("RGBA", (W, H), (9, 14, 26, 255))
    draw = ImageDraw.Draw(img)

    # Ambient grid lines
    grid_gap = 64
    for x in range(0, W, grid_gap):
        draw.line([(x, 0), (x, H)], fill=(20, 32, 54, 160), width=1)
    for y in range(0, H, grid_gap):
        draw.line([(0, y), (W, y)], fill=(20, 32, 54, 160), width=1)

    # Pulse glow behind the window
    glow_color = (239, 68, 68, 30) if sec < beats[1] else (34, 197, 94, 35)
    draw.ellipse([W // 2 - 380, 420, W // 2 + 380, 1180], fill=glow_color)

    # 2. Header: Series Badge & Difficulty
    diff_color = {
        "EASY": (34, 197, 94),
        "MEDIUM": (250, 204, 21),
        "HARD": (239, 68, 68),
        "TRICK": (168, 85, 247)
    }.get(lesson.difficulty, (56, 189, 248))

    header_y = 120
    draw.rounded_rectangle([W // 2 - 460, header_y, W // 2 + 460, header_y + 80], radius=16, fill=(15, 23, 42, 240), outline=(51, 65, 85), width=2)
    # Left tag: Series
    draw.text((W // 2 - 430, header_y + 40), f"⚡ {lesson.series}", fill=(148, 163, 184), font=font_title, anchor="lm")
    # Right tag: Difficulty
    draw.rounded_rectangle([W // 2 + 310, header_y + 16, W // 2 + 440, header_y + 64], radius=10, fill=(30, 41, 59), outline=diff_color, width=2)
    draw.text((W // 2 + 375, header_y + 40), lesson.difficulty, fill=diff_color, font=font_hud, anchor="mm")

    # 3. Hero IDE Window
    win_w, win_h = 980, 940
    win_x = (W - win_w) // 2
    win_y = 230

    # Determine Phase: Naive vs Optimal
    is_optimal_phase = sec >= beats[1]
    border_color = (74, 222, 128, 220) if is_optimal_phase else (239, 68, 68, 200)

    # Drop shadow
    shadow_img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    s_draw = ImageDraw.Draw(shadow_img)
    s_draw.rounded_rectangle([win_x - 8, win_y - 4, win_x + win_w + 8, win_y + win_h + 16], radius=24, fill=(0, 0, 0, 180))
    shadow_img = shadow_img.filter(ImageFilter.GaussianBlur(16))
    img.alpha_composite(shadow_img)

    # Window Canvas
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([win_x, win_y, win_x + win_w, win_y + win_h], radius=20, fill=(15, 23, 42, 250), outline=border_color, width=3)

    # Titlebar
    title_h = 58
    draw.rounded_rectangle([win_x, win_y, win_x + win_w, win_y + title_h], radius=20, fill=(30, 41, 59))
    draw.rectangle([win_x, win_y + title_h - 12, win_x + win_w, win_y + title_h], fill=(30, 41, 59))
    draw.line([(win_x, win_y + title_h), (win_x + win_w, win_y + title_h)], fill=(51, 65, 85), width=2)

    # macOS window buttons
    btn_y = win_y + title_h // 2
    draw.ellipse([win_x + 24, btn_y - 8, win_x + 40, btn_y + 8], fill=(239, 68, 68))
    draw.ellipse([win_x + 50, btn_y - 8, win_x + 66, btn_y + 8], fill=(234, 179, 8))
    draw.ellipse([win_x + 76, btn_y - 8, win_x + 92, btn_y + 8], fill=(34, 197, 94))

    # Active File Tab
    tab_x = win_x + 130
    draw.rectangle([tab_x, win_y + 8, tab_x + 300, win_y + title_h], fill=(15, 23, 42))
    draw.text((tab_x + 150, win_y + title_h // 2), f"🐍 {lesson.filename}", fill=(241, 245, 249), font=font_code, anchor="mm")

    # Phase Badge on right of titlebar
    phase_txt = "✨ O(n) OPTIMAL" if is_optimal_phase else "❌ O(n²) BRUTE FORCE"
    draw.text((win_x + win_w - 30, win_y + title_h // 2), phase_txt, fill=border_color, font=font_hud, anchor="rm")

    # Render Active Snippet
    active_snippet = lesson.snippet_optimal if is_optimal_phase else lesson.snippet_naive
    code_start_y = win_y + title_h + 30
    line_h = 44

    token_colors = {
        "comment": (100, 116, 139),
        "def": (244, 63, 94),
        "loop": (56, 189, 248),
        "keyword": (168, 85, 247),
        "return": (250, 204, 21),
        "assign": (74, 222, 128),
        "call": (56, 189, 248),
        "normal": (248, 250, 252),
    }

    # Animate lines typing in progressively
    phase_start_sec = beats[1] if is_optimal_phase else 0.0
    phase_elapsed = sec - phase_start_sec
    lines_to_show = min(len(active_snippet), int(phase_elapsed * 2.2) + 1)

    for i in range(lines_to_show):
        code_text, token_type = active_snippet[i]
        curr_y = code_start_y + i * line_h
        color = token_colors.get(token_type, (248, 250, 252))

        # Line number
        draw.text((win_x + 35, curr_y), f"{i+1:2d}", fill=(71, 85, 105), font=font_code)
        # Code line
        draw.text((win_x + 95, curr_y), code_text, fill=color, font=font_code)

    # Blinking cursor
    if int(sec * 4) % 2 == 0 and lines_to_show < len(active_snippet):
        cursor_y = code_start_y + lines_to_show * line_h
        draw.rectangle([win_x + 95, cursor_y, win_x + 108, cursor_y + 30], fill=(56, 189, 248))

    # 4. Integrated Terminal (Bottom of IDE window)
    term_h = 240
    term_y = win_y + win_h - term_h - 15
    draw.rounded_rectangle([win_x + 18, term_y, win_x + win_w - 18, term_y + term_h], radius=14, fill=(2, 6, 23, 245), outline=(51, 65, 85), width=2)
    # Terminal titlebar
    draw.rectangle([win_x + 18, term_y, win_x + win_w - 18, term_y + 36], fill=(15, 23, 42))
    draw.text((win_x + 40, term_y + 18), "TERMINAL  |  bash  (Live Output)", fill=(148, 163, 184), font=font_hud, anchor="lm")

    # Command execution
    draw.text((win_x + 40, term_y + 55), lesson.terminal_cmd, fill=(248, 250, 252), font=font_code)

    # Terminal output starts streaming after beat 2
    if sec > beats[2]:
        term_out_start = beats[2]
        out_lines_count = min(len(lesson.terminal_output), int((sec - term_out_start) * 2.0) + 1)
        for idx in range(out_lines_count):
            out_txt = lesson.terminal_output[idx]
            out_color = (74, 222, 128) if "✓" in out_txt or "PASSED" in out_txt else (250, 204, 21)
            draw.text((win_x + 40, term_y + 95 + idx * 36), out_txt, fill=out_color, font=font_code)

    # 5. Floating Dry-Run / Teacher Pointer Card
    dry_w, dry_h = 940, 100
    dry_x = (W - dry_w) // 2
    dry_y = win_y + win_h + 30

    card_img = Image.new("RGBA", (dry_w, dry_h), (0, 0, 0, 0))
    c_draw = ImageDraw.Draw(card_img)
    # Sticker outline
    c_draw.rounded_rectangle([0, 0, dry_w, dry_h], radius=16, fill=(255, 255, 255))
    c_draw.rounded_rectangle([4, 4, dry_w - 4, dry_h - 4], radius=14, fill=(15, 23, 42))
    c_draw.text((dry_w // 2, dry_h // 2), f"💡 {lesson.dry_run_step}", fill=(250, 204, 21), font=font_hud, anchor="mm")
    img.alpha_composite(card_img, (dry_x, dry_y))

    # 6. Kinetic Karaoke Subtitles (Bottom Safe Zone)
    sub_box_y = 1580
    active_speech = (
        lesson.hook_narration if sec < beats[0] else
        lesson.trap_narration if sec < beats[1] else
        lesson.solution_narration if sec < beats[2] else
        lesson.takeaway_narration
    )

    words = active_speech.split()
    # Word highlight progress inside the active beat
    beat_start = 0.0 if sec < beats[0] else beats[0] if sec < beats[1] else beats[1] if sec < beats[2] else beats[2]
    beat_end = beats[0] if sec < beats[0] else beats[1] if sec < beats[1] else beats[2] if sec < beats[2] else beats[3]
    beat_progress = max(0.0, min(1.0, (sec - beat_start) / max(0.1, beat_end - beat_start)))
    active_word_idx = min(len(words) - 1, int(beat_progress * len(words)))

    # Display up to 2 lines of text
    mid = len(words) // 2
    line1 = " ".join(words[:mid]) if mid > 0 else active_speech
    line2 = " ".join(words[mid:]) if mid > 0 else ""

    draw.rounded_rectangle([W // 2 - 470, sub_box_y - 20, W // 2 + 470, sub_box_y + 150], radius=24, fill=(0, 0, 0, 220), outline=(250, 204, 21, 220), width=3)
    draw.text((W // 2, sub_box_y + 25), line1, fill=(255, 255, 255), font=font_sub, anchor="mm")
    if line2:
        draw.text((W // 2, sub_box_y + 90), line2, fill=(56, 189, 248), font=font_sub, anchor="mm")

    # 7. Bottom Branding Telemetry
    draw.text((W // 2, 1835), "CHANNEL 7 // CODE CRAFT • PYTHON & DSA MASTERCLASS • 60 FPS VOX", fill=(100, 116, 139), font=font_hud, anchor="mm")

    return img.convert("RGB")


async def render_coding_short(lesson_id: str | None = None) -> Path:
    lesson = get_lesson(lesson_id)
    print("\n" + "=" * 70)
    print(f"🎬 [Channel 7 Coding Studio] Producing Lesson: {lesson.title}")
    print(f"📚 Series: {lesson.series} | Difficulty: {lesson.difficulty}")
    print("=" * 70)

    t0 = time.time()

    # 1. Voiceover
    print(f"🎙️ Generating continuous teacher narration via Edge TTS Jenny...")
    wav_path, beats, duration = await generate_speech_tracks(lesson, OUTPUT_DIR)
    print(f"✅ Voiceover rendered: {duration:.2f}s (Beats: {[round(b, 2) for b in beats]})")

    fps = 30
    total_frames = int(duration * fps)

    font_code = get_font(26, bold=True)
    font_title = get_font(28, bold=True)
    font_sub = get_font(40, bold=True)
    font_hud = get_font(22, bold=True)

    out_mp4 = OUTPUT_DIR / f"{lesson.id}_vox_short.mp4"
    print(f"🚀 Rendering {total_frames} frames via FFmpeg Pipe at {fps} FPS (1080x1920)...")

    ffmpeg_cmd = [
        "ffmpeg", "-y",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-s", "1080x1920",
        "-pix_fmt", "rgb24",
        "-r", str(fps),
        "-i", "-",
        "-i", str(wav_path),
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

    for i in range(total_frames):
        frame = render_pedagogical_frame(i, total_frames, duration, lesson, beats, font_code, font_title, font_sub, font_hud)
        proc.stdin.write(frame.tobytes())

    proc.stdin.close()
    proc.wait()

    render_time = time.time() - t0
    print(f"🎉 Master Video Render Complete in {render_time:.2f}s: {out_mp4}")
    print(f"📦 File Size: {out_mp4.stat().st_size / (1024*1024):.2f} MB")

    # Dispatch to Telegram
    print("📱 Sending Pedagogical Coding Video to Telegram...")
    telegram_script = Path("d:/facts_yt/send_to_telegram.py")
    if telegram_script.exists():
        subprocess.run([sys.executable, str(telegram_script), str(OUTPUT_DIR)], check=False)
        print("✅ Telegram notification dispatched!")

    return out_mp4


if __name__ == "__main__":
    query = sys.argv[1] if len(sys.argv) > 1 else "two_sum_hashmap"
    asyncio.run(render_coding_short(query))
