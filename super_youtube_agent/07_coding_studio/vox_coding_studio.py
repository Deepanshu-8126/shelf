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
import json
from typing import Any
import math
import os
import subprocess
import sys
import time
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import edge_tts
from sfx_foley import build_teacher_foley_soundtrack
from code_highlighter import tokenize_code

# Fix Windows console UTF-8 output
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

CURRENT_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = CURRENT_DIR / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

from curriculum import CodingLesson, get_lesson
from teacher_brain import TeacherLesson, get_next_teacher_lesson, MASTER_SERIES_CATALOG

# Image caching for efficient reuse
_image_cache = {}

def load_image_cached(image_path: str) -> Image.Image:
    """Load and cache an image to avoid reloading from disk every frame."""
    if image_path not in _image_cache:
        try:
            _image_cache[image_path] = Image.open(image_path).convert("RGBA")
        except Exception as e:
            print(f"⚠️ Failed to load image {image_path}: {e}")
            # Return a placeholder image if loading fails
            _image_cache[image_path] = Image.new("RGBA", (100, 100), (255, 0, 0, 128))
    return _image_cache[image_path]


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


async def generate_speech_tracks(lesson: Any, output_dir: Path) -> tuple[Path, list[float], float]:
    """Generates continuous voiceover using Kokoro-82M per pedagogical beat."""
    hook = getattr(lesson, "intro_hook", None) or getattr(lesson, "hook_narration", "")
    trap = getattr(lesson, "concept_walkthrough", None) or getattr(lesson, "trap_narration", "")
    solution = getattr(lesson, "code_explanation", None) or getattr(lesson, "solution_narration", "")
    takeaway = getattr(lesson, "outro_homework", None) or getattr(lesson, "takeaway_narration", "")

    les_id = getattr(lesson, "id", None) or f"{lesson.series_name.lower().replace(' ', '_')}_{lesson.episode_num}"
    wav_path = output_dir / f"{les_id}_voice.wav"

    try:
        from kokoro_tts import generate_kokoro_narration
        import soundfile as sf
        import numpy as np

        is_hindi = any('\u0900' <= char <= '\u097F' for char in f"{hook} {trap} {solution}")
        lang = "hi" if is_hindi else "en"
        voice = "hm_omega" if is_hindi else "am_adam"

        audios = []
        beats = []
        accum = 0.0

        for idx, text in enumerate([hook, trap, solution, takeaway]):
            if not text.strip():
                continue
            seg_wav = output_dir / f"{les_id}_seg_{idx}.wav"
            _, seg_dur = generate_kokoro_narration(text, seg_wav, lang=lang, voice=voice, speed=0.96)
            seg_data, _ = sf.read(str(seg_wav))
            audios.append(seg_data)
            accum += seg_dur
            beats.append(accum)

        full_audio = np.concatenate(audios)
        raw_kokoro_wav = output_dir / f"{les_id}_kokoro_raw.wav"
        sf.write(str(raw_kokoro_wav), full_audio, 24000)

        # Resample to 44.1kHz stereo for master pipeline
        subprocess.run([
            "ffmpeg", "-y", "-i", str(raw_kokoro_wav),
            "-ar", "44100", "-ac", "2", str(wav_path)
        ], check=True, capture_output=True)

        print(f"🎙️ [Kokoro Engine] Successfully rendered {accum:.2f}s voice across 4 beats: {[round(b, 2) for b in beats]}")
        return wav_path, beats, accum
    except Exception as e:
        print(f"⚠️ Kokoro TTS fallback to Edge TTS ({e})")
        full_script = f"{hook} {trap} {solution} {takeaway}"
        mp3_path = output_dir / f"{les_id}_voice.mp3"
        comm = edge_tts.Communicate(full_script, "en-US-JennyNeural", rate="+6%", pitch="+0Hz")
        await comm.save(str(mp3_path))
        subprocess.run(["ffmpeg", "-y", "-i", str(mp3_path), "-ar", "44100", "-ac", "2", str(wav_path)], check=True, capture_output=True)
        probe = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(wav_path)], check=True, capture_output=True, text=True)
        total_duration = float(probe.stdout.strip())
        words_h = len(hook.split())
        words_t = len(trap.split())
        words_s = len(solution.split())
        words_o = len(takeaway.split())
        total_words = words_h + words_t + words_s + words_o
        b1_end = total_duration * (words_h / max(1, total_words))
        b2_end = total_duration * ((words_h + words_t) / max(1, total_words))
        b3_end = total_duration * ((words_h + words_t + words_s) / max(1, total_words))
        return wav_path, [b1_end, b2_end, b3_end, total_duration], total_duration



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

    # Climax threshold: Last 22% of the video switches to the Comparison Screen (Image 2 style)
    climax_start = beats[2] if len(beats) > 2 else total_sec * 0.75
    is_climax_beat = sec >= climax_start

    # Common typography
    font_huge = get_font(52, bold=True)
    font_bread = get_font(38, bold=True)
    font_card_head = get_font(28, bold=True)
    font_mono = get_font(26, bold=True)
    font_tip_title = get_font(28, bold=True)
    font_tip_body = get_font(24, bold=False)
    font_head_comp = get_font(26, bold=True)
    font_vs = get_font(36, bold=True)

    series_name = getattr(lesson, "series_name", "100 DAYS OF PYTHON")
    ep_num = getattr(lesson, "episode_num", 14)
    topic_title = getattr(lesson, "topic_title", "Memory Optimization")

    if is_climax_beat:
        # =========================================================================
        # STYLE 2: SIDE-BY-SIDE COMPARISON CLIMAX SCREEN (Exact match to Image 2)
        # =========================================================================
        img = Image.new("RGBA", (W, H), (255, 255, 255, 255))
        draw = ImageDraw.Draw(img)

        # Subtle micro-dot grid
        for x in range(24, W, 40):
            for y in range(24, H, 40):
                draw.ellipse([x - 1, y - 1, x + 1, y + 1], fill=(241, 245, 249, 180))

        # Main Big Headline
        # Dynamic Big Headline
        ser_head = series_name.upper()
        if "100" in ser_head or "PYTHON" in ser_head:
            head_line1 = "100 DAYS OF"
            head_line2 = f"PYTHON • DAY {ep_num}"
        else:
            head_line1 = ser_head[:22]
            head_line2 = f"EPISODE #{ep_num}"

        draw.text((W // 2, 160), head_line1, fill=(15, 23, 42), font=font_huge, anchor="mm")
        draw.text((W // 2, 235), head_line2, fill=(15, 23, 42), font=font_huge, anchor="mm")

        # Side-by-side vertical cards
        card_w, card_h = 430, 840
        card_y = 340
        left_x = 75
        right_x = 575

        # Left Card: Soft Coral Red (Naive / Pitfall)
        left_title = "NAIVE PATTERN"
        
        # Get the appropriate code snippets based on lesson type
        if hasattr(lesson, 'snippet_naive'):  # CodingLesson
            naive_code = lesson.snippet_naive
            optimal_code = lesson.snippet_optimal
        else:  # TeacherLesson
            naive_code = lesson.code_before
            optimal_code = lesson.code_after
        
        for l_t, _ in naive_code:
            if l_t.startswith("# ❌"):
                left_title = l_t.replace("# ❌", "").split("(")[0].strip()[:20]
                break
        left_sub = getattr(lesson, "badge_tag", "EAGER")[:18]

        left_pill = ""
        for l_t, _ in naive_code:
            if not l_t.startswith("#") and len(l_t.strip()) > 3:
                left_pill = l_t.strip()[:26]
                break
        if not left_pill:
            left_pill = "Naive Code"

        # Card borders and backgrounds
        for offset, alpha in [(12, 15), (6, 25)]:
            draw.rounded_rectangle([left_x, card_y + offset, left_x + card_w, card_y + card_h + offset], radius=32, fill=(0, 0, 0, alpha))
            draw.rounded_rectangle([right_x, card_y + offset, right_x + card_w, card_y + card_h + offset], radius=32, fill=(0, 0, 0, alpha))
            
        draw.rounded_rectangle([left_x, card_y, left_x + card_w, card_y + card_h], radius=32, fill=(254, 242, 242), outline=(251, 113, 133), width=2)
        draw.rounded_rectangle([right_x, card_y, right_x + card_w, card_y + card_h], radius=32, fill=(240, 253, 244), outline=(52, 211, 153), width=2)

        # Left Header
        draw.rounded_rectangle([left_x + 30, card_y + 35, left_x + card_w - 30, card_y + 85], radius=14, fill=(254, 226, 226))
        draw.text((left_x + card_w // 2, card_y + 60), f"[x] {left_title}", fill=(185, 28, 28), font=get_font(20, bold=True), anchor="mm")
        draw.text((left_x + card_w // 2, card_y + 115), f"• {left_sub} •", fill=(190, 18, 60), font=get_font(22, bold=True), anchor="mm")

        # Right Header
        right_title = "OPTIMAL FIX"
        for l_t, _ in optimal_code:
            if l_t.startswith("# ✨"):
                right_title = l_t.replace("# ✨", "").split("(")[0].strip()[:20]
                break
        right_sub = "PRODUCTION CLEAN"
        draw.rounded_rectangle([right_x + 30, card_y + 35, right_x + card_w - 30, card_y + 85], radius=14, fill=(220, 252, 231))
        draw.text((right_x + card_w // 2, card_y + 60), f"[✓] {right_title}", fill=(20, 83, 45), font=get_font(20, bold=True), anchor="mm")
        draw.text((right_x + card_w // 2, card_y + 115), f"• {right_sub} •", fill=(4, 120, 87), font=get_font(22, bold=True), anchor="mm")

        # Left Code Box (Dark Card)
        cbox_y = card_y + 155
        cbox_h = 390
        draw.rounded_rectangle([left_x + 16, cbox_y, left_x + card_w - 16, cbox_y + cbox_h], radius=18, fill=(24, 24, 27))
        font_code_comp = get_font(18, bold=True)
        code_lines_left = [l_t for l_t, _ in naive_code if not l_t.startswith("#")][:6]
        for c_idx, cl in enumerate(code_lines_left):
            draw.text((left_x + 30, cbox_y + 24 + c_idx * 34), cl[:28], fill=(244, 244, 245), font=font_code_comp)

        # Right Code Box (Dark Card)
        draw.rounded_rectangle([right_x + 16, cbox_y, right_x + card_w - 16, cbox_y + cbox_h], radius=18, fill=(24, 24, 27))
        code_lines_right = [l_t for l_t, _ in optimal_code if not l_t.startswith("#")][:6]
        for c_idx, cl in enumerate(code_lines_right):
            draw.text((right_x + 30, cbox_y + 24 + c_idx * 34), cl[:28], fill=(220, 252, 231) if c_idx == 0 else (244, 244, 245), font=font_code_comp)

        # Bullets Below Code Boxes
        bullets_y = cbox_y + cbox_h + 30
        draw.text((left_x + 35, bullets_y), "• O(n²) Slow Execution", fill=(185, 28, 28), font=get_font(21, bold=True))
        draw.text((left_x + 35, bullets_y + 40), "• Nested Loop Overhead", fill=(185, 28, 28), font=get_font(21, bold=True))
        draw.text((left_x + 35, bullets_y + 80), "• Fails Scale Tests", fill=(153, 27, 27), font=get_font(21, bold=True))

        draw.text((right_x + 35, bullets_y), "• O(n log n) Divide & Conquer", fill=(20, 83, 45), font=get_font(21, bold=True))
        draw.text((right_x + 35, bullets_y + 40), "• 160x Faster Speedup", fill=(20, 83, 45), font=get_font(21, bold=True))
        draw.text((right_x + 35, bullets_y + 80), "• Production Standard", fill=(4, 120, 87), font=get_font(21, bold=True))

        # Center VS Badge
        vs_cx, vs_cy = W // 2, cbox_y + cbox_h // 2
        draw.ellipse([vs_cx - 44, vs_cy - 44, vs_cx + 44, vs_cy + 44], fill=(255, 255, 255), outline=(226, 232, 240), width=4)
        draw.text((vs_cx, vs_cy), "VS", fill=(15, 23, 42), font=get_font(30, bold=True), anchor="mm")

        # Bottom Metric Saved Card (Soft Blue)
        save_x, save_y = 75, 1240
        save_w, save_h = 930, 240
        for offset, alpha in [(12, 15), (6, 25)]:
            draw.rounded_rectangle([save_x, save_y + offset, save_x + save_w, save_y + save_h + offset], radius=28, fill=(0, 0, 0, alpha))
        draw.rounded_rectangle([save_x, save_y, save_x + save_w, save_y + save_h], radius=28, fill=(191, 219, 254), outline=(96, 165, 250), width=2)
        # Checkmark circle
        draw.ellipse([save_x + 50, save_y + 50, save_x + 120, save_y + 120], fill=(59, 130, 246))
        draw.line([(save_x + 72, save_y + 85), (save_x + 82, save_y + 98)], fill=(255, 255, 255), width=5)
        draw.line([(save_x + 82, save_y + 98), (save_x + 102, save_y + 72)], fill=(255, 255, 255), width=5)

        bot_metric = "Production Optimal •"
        # Get the appropriate terminal attributes based on lesson type
        if hasattr(lesson, 'terminal_cmd'):  # CodingLesson
            terminal_output = lesson.terminal_output
        else:  # TeacherLesson
            terminal_output = getattr(lesson, "terminal_logs", [])
        
        if terminal_output:
            bot_metric = terminal_output[-1].replace(">>", "").replace("[+]", "").strip()[:32] + " •"
        # Get the appropriate outro/takeaway attribute based on lesson type
        if hasattr(lesson, 'takeaway_narration'):  # CodingLesson
            bot_sub = lesson.takeaway_narration if lesson.takeaway_narration else lesson.teacher_tip
        else:  # TeacherLesson
            bot_sub = lesson.outro_homework if lesson.outro_homework else lesson.teacher_tip

        draw.text((save_x + 145, save_y + 80), bot_metric, fill=(30, 58, 138), font=get_font(30, bold=True), anchor="lm")
        # Multi-line wrap for takeaway
        sub_words = bot_sub.split()
        sub_l1 = " ".join(sub_words[:8])
        sub_l2 = " ".join(sub_words[8:16])
        draw.text((save_x + 145, save_y + 130), sub_l1, fill=(30, 64, 175), font=font_tip_body, anchor="lm")
        if sub_l2:
            draw.text((save_x + 145, save_y + 168), sub_l2, fill=(30, 64, 175), font=font_tip_body, anchor="lm")

    elif sec < beats[0]:
        # =========================================================================
        # SCENE 1: THE HOOK & VISUAL PROBLEM / UNSORTED DATA CARD (0s -> beats[0])
        # =========================================================================
        img = Image.new("RGBA", (W, H), (250, 250, 250, 255))
        draw = ImageDraw.Draw(img)

        # Subtle micro-dot grid
        for x in range(24, W, 36):
            for y in range(24, H, 36):
                draw.ellipse([x - 1, y - 1, x + 1, y + 1], fill=(226, 232, 240, 200))

        # Breadcrumb
        category = "Python" if "PYTHON" in series_name.upper() else "DSA" if "LEETCODE" in series_name.upper() else "DevTools"
        tag_str = getattr(lesson, "badge_tag", "Mastery").split("•")[0].strip()[:16]
        bread_y = 130
        draw.text((110, bread_y), f"{category} > {series_name[:16]} > Day {ep_num}", fill=(148, 163, 184), font=font_bread)

        # Hero Pill
        draw.rounded_rectangle([110, 190, 680, 246], radius=16, fill=(254, 226, 226), outline=(248, 113, 113), width=2)
        draw.text((395, 218), f"[!] CHALLENGE: {tag_str}", fill=(185, 28, 28), font=get_font(22, bold=True), anchor="mm")

        # Headline
        draw.text((110, 275), topic_title[:38], fill=(15, 23, 42), font=get_font(38, bold=True))

        # 1. Visual Problem Component Card
        card_x, card_y, card_w, card_h = 90, 360, 900, 480
        for offset, alpha in [(16, 15), (10, 25), (4, 45)]:
            draw.rounded_rectangle([card_x - 2, card_y + offset, card_x + card_w + 2, card_y + card_h + offset], radius=28, fill=(0, 0, 0, alpha))
        draw.rounded_rectangle([card_x, card_y, card_x + card_w, card_y + card_h], radius=28, fill=(255, 255, 255), outline=(226, 232, 240), width=2)

        # macOS dots + Title
        draw.ellipse([card_x + 40, card_y + 26, card_x + 58, card_y + 44], fill=(255, 95, 86))
        draw.ellipse([card_x + 68, card_y + 26, card_x + 86, card_y + 44], fill=(255, 189, 46))
        draw.ellipse([card_x + 96, card_y + 26, card_x + 114, card_y + 44], fill=(39, 201, 63))
        draw.text((card_x + 140, card_y + 35), f"Input Problem State • {lesson.filename}", fill=(15, 23, 42), font=font_card_head, anchor="lm")
        draw.line([(card_x + 20, card_y + 68), (card_x + card_w - 20, card_y + 68)], fill=(241, 245, 249), width=2)

        if "quicksort" in lesson.filename.lower() or "sort" in topic_title.lower() or "array" in topic_title.lower():
            # Render Unsorted Array Component
            tiles = [38, 27, 43, 3, 9, 82, 10]
            tile_w, tile_h = 100, 120
            tile_y = card_y + 130
            start_tx = card_x + 50
            gap = 18

            for idx, val in enumerate(tiles):
                tx = start_tx + idx * (tile_w + gap)
                is_mid = (idx == len(tiles) // 2)
                border_col = (245, 158, 11) if is_mid else (203, 213, 225)
                bg_col = (254, 243, 199) if is_mid else (248, 250, 252)
                text_col = (180, 83, 9) if is_mid else (15, 23, 42)
                draw.rounded_rectangle([tx, tile_y, tx + tile_w, tile_y + tile_h], radius=20, fill=bg_col, outline=border_col, width=2)
                draw.text((tx + tile_w // 2, tile_y + tile_h // 2), str(val), fill=text_col, font=get_font(36, bold=True), anchor="mm")
                draw.text((tx + tile_w // 2, tile_y + tile_h + 26), f"[{idx}]", fill=(148, 163, 184), font=get_font(20, bold=True), anchor="mm")

            draw.rounded_rectangle([card_x + 60, card_y + 350, card_x + card_w - 60, card_y + 430], radius=18, fill=(241, 245, 249))
            draw.text((card_x + card_w // 2, card_y + 390), "⚡ Challenge: Sort without O(n) auxiliary allocation!", fill=(51, 65, 85), font=get_font(24, bold=True), anchor="mm")
        else:
            # Render Memory Gauge or General Trap Preview
            draw.text((card_x + 60, card_y + 130), "Memory Profile • Eager Allocation", fill=(30, 58, 138), font=get_font(28, bold=True))
            draw.rounded_rectangle([card_x + 60, card_y + 190, card_x + card_w - 60, card_y + 270], radius=20, fill=(254, 226, 226), outline=(248, 113, 113), width=2)
            draw.rounded_rectangle([card_x + 64, card_y + 194, card_x + int((card_w - 128) * 0.88), card_y + 266], radius=16, fill=(239, 68, 68))
            draw.text((card_x + card_w // 2, card_y + 230), "80.0 MB RAM ALLOCATED (10M Integers)", fill=(255, 255, 255), font=font_mono, anchor="mm")
            draw.text((card_x + 60, card_y + 320), "⚠️ Every element is created eagerly at definition time!", fill=(185, 28, 28), font=get_font(24, bold=False))
            draw.rounded_rectangle([card_x + 60, card_y + 370, card_x + card_w - 60, card_y + 440], radius=18, fill=(241, 245, 249))
            draw.text((card_x + card_w // 2, card_y + 405), "⚡ Goal: Achieve O(1) memory with generator lazy evaluation", fill=(51, 65, 85), font=get_font(24, bold=True), anchor="mm")

        # 2. Trap Card Below
        trap_y = 880
        trap_h = 360
        for offset, alpha in [(12, 15), (6, 25)]:
            draw.rounded_rectangle([card_x, trap_y + offset, card_x + card_w, trap_y + trap_h + offset], radius=28, fill=(0, 0, 0, alpha))
        draw.rounded_rectangle([card_x, trap_y, card_x + card_w, trap_y + trap_h], radius=28, fill=(254, 242, 242), outline=(248, 113, 113), width=2)

        draw.text((card_x + 50, trap_y + 40), "[x] THE JUNIOR TRAP: NAIVE APPROACH", fill=(185, 28, 28), font=font_card_head)
        draw.text((card_x + 50, trap_y + 90), "• Inefficient complexity or uncontrolled memory consumption", fill=(153, 27, 27), font=get_font(24, bold=False))
        draw.text((card_x + 50, trap_y + 130), "• Times out or triggers Out-Of-Memory in production!", fill=(153, 27, 27), font=get_font(24, bold=False))

        # Formula / Warning pill
        draw.rounded_rectangle([card_x + 50, trap_y + 190, card_x + card_w - 50, trap_y + 270], radius=16, fill=(239, 68, 68))
        draw.text((card_x + card_w // 2, trap_y + 230), "ANTI-PATTERN: HIGH COMPLEXITY / WASTED RESOURCES", fill=(255, 255, 255), font=font_mono, anchor="mm")
        draw.text((card_x + 50, trap_y + 310), "💡 Next: Watch how senior engineers solve this cleanly...", fill=(120, 53, 15), font=get_font(22, bold=True))

    elif beats[1] <= sec < beats[2]:
        # =========================================================================
        # SCENE 3: STEP-BY-STEP EXECUTION DRY RUN (beats[1] -> beats[2])
        # =========================================================================
        img = Image.new("RGBA", (W, H), (250, 250, 250, 255))
        draw = ImageDraw.Draw(img)

        for x in range(24, W, 36):
            for y in range(24, H, 36):
                draw.ellipse([x - 1, y - 1, x + 1, y + 1], fill=(226, 232, 240, 200))

        draw.text((110, 130), f"Step-by-Step Execution • {topic_title[:28]}", fill=(148, 163, 184), font=font_bread)

        # Hero Pill
        draw.rounded_rectangle([110, 190, 680, 246], radius=16, fill=(220, 252, 231), outline=(74, 222, 128), width=2)
        draw.text((395, 218), "[*] LIVE DRY-RUN • STEP-BY-STEP TRACE", fill=(20, 83, 45), font=get_font(22, bold=True), anchor="mm")

        draw.text((110, 275), "Execution Trace: Logic Explained", fill=(15, 23, 42), font=get_font(36, bold=True))

        card_x, card_y, card_w, card_h = 90, 350, 900, 1000
        for offset, alpha in [(16, 15), (10, 25), (4, 45)]:
            draw.rounded_rectangle([card_x - 2, card_y + offset, card_x + card_w + 2, card_y + card_h + offset], radius=28, fill=(0, 0, 0, alpha))
        draw.rounded_rectangle([card_x, card_y, card_x + card_w, card_y + card_h], radius=28, fill=(255, 255, 255), outline=(226, 232, 240), width=2)

        draw.ellipse([card_x + 40, card_y + 26, card_x + 58, card_y + 44], fill=(255, 95, 86))
        draw.ellipse([card_x + 68, card_y + 26, card_x + 86, card_y + 44], fill=(255, 189, 46))
        draw.ellipse([card_x + 96, card_y + 26, card_x + 114, card_y + 44], fill=(39, 201, 63))
        draw.text((card_x + 140, card_y + 35), "Dry Run Visualizer • Runtime Trace", fill=(15, 23, 42), font=font_card_head, anchor="lm")
        draw.line([(card_x + 20, card_y + 68), (card_x + card_w - 20, card_y + 68)], fill=(241, 245, 249), width=2)

        if "quicksort" in lesson.filename.lower() or "sort" in topic_title.lower():
            # QuickSort Partitioning Trace
            y_s1 = card_y + 100
            draw.text((card_x + 50, y_s1), "STEP 1: SELECT PIVOT (Middle Element)", fill=(30, 58, 138), font=get_font(26, bold=True))
            draw.rounded_rectangle([card_x + 50, y_s1 + 40, card_x + 240, y_s1 + 130], radius=16, fill=(254, 243, 199), outline=(245, 158, 11), width=2)
            draw.text((card_x + 145, y_s1 + 85), "PIVOT = 9", fill=(180, 83, 9), font=get_font(28, bold=True), anchor="mm")
            draw.text((card_x + 265, y_s1 + 85), "← Middle index: len(arr) // 2", fill=(100, 116, 139), font=get_font(22, bold=False), anchor="lm")

            y_s2 = card_y + 270
            draw.text((card_x + 50, y_s2), "STEP 2: PARTITION ELEMENTS AROUND PIVOT", fill=(30, 58, 138), font=get_font(26, bold=True))

            draw.rounded_rectangle([card_x + 50, y_s2 + 40, card_x + 420, y_s2 + 200], radius=18, fill=(239, 246, 255), outline=(147, 197, 253), width=2)
            draw.text((card_x + 70, y_s2 + 70), "LEFT (< PIVOT)", fill=(29, 78, 216), font=get_font(22, bold=True))
            draw.rounded_rectangle([card_x + 70, y_s2 + 105, card_x + 160, y_s2 + 175], radius=12, fill=(255, 255, 255), outline=(191, 219, 254))
            draw.text((card_x + 115, y_s2 + 140), "3", fill=(30, 58, 138), font=get_font(32, bold=True), anchor="mm")

            draw.rounded_rectangle([card_x + 460, y_s2 + 40, card_x + 850, y_s2 + 200], radius=18, fill=(250, 245, 255), outline=(216, 180, 254), width=2)
            draw.text((card_x + 480, y_s2 + 70), "RIGHT (> PIVOT)", fill=(126, 34, 206), font=get_font(22, bold=True))
            right_vals = [38, 27, 43, 82, 10]
            for r_i, r_v in enumerate(right_vals):
                rx = card_x + 480 + r_i * 68
                draw.rounded_rectangle([rx, y_s2 + 105, rx + 60, y_s2 + 175], radius=12, fill=(255, 255, 255), outline=(233, 213, 255))
                draw.text((rx + 30, y_s2 + 140), str(r_v), fill=(107, 33, 168), font=get_font(22, bold=True), anchor="mm")

            y_s3 = card_y + 510
            draw.text((card_x + 50, y_s3), "STEP 3: RECURSIVE CONCATENATION", fill=(30, 58, 138), font=get_font(26, bold=True))
            formula_str = "quicksort(left) + [pivot] + quicksort(right)"
            draw.rounded_rectangle([card_x + 50, y_s3 + 40, card_x + 850, y_s3 + 120], radius=16, fill=(39, 39, 42))
            draw.text((card_x + 450, y_s3 + 80), formula_str, fill=(255, 255, 255), font=get_font(26, bold=True), anchor="mm")

            y_s4 = card_y + 680
            draw.text((card_x + 50, y_s4), "STEP 4: FINAL SORTED ARRAY [✓ PASS]", fill=(20, 83, 45), font=get_font(26, bold=True))
            sorted_vals = [3, 9, 10, 27, 38, 43, 82]
            for s_i, s_v in enumerate(sorted_vals):
                sx = card_x + 50 + s_i * (100 + 16)
                draw.rounded_rectangle([sx, y_s4 + 40, sx + 100, y_s4 + 140], radius=16, fill=(220, 252, 231), outline=(74, 222, 128), width=2)
                draw.text((sx + 50, y_s4 + 90), str(s_v), fill=(20, 83, 45), font=get_font(34, bold=True), anchor="mm")

            draw.rounded_rectangle([card_x + 50, card_y + 870, card_x + 850, card_y + 950], radius=16, fill=(241, 245, 249))
            draw.text((card_x + 450, card_y + 910), "⚡ TIME COMPLEXITY: O(n log n) AVERAGE • 160x FASTER!", fill=(15, 23, 42), font=get_font(24, bold=True), anchor="mm")
        else:
            # Memory Profiling & State Trace for Other Lessons
            y_s1 = card_y + 100
            draw.text((card_x + 50, y_s1), "STEP 1: MEMORY USAGE COMPARISON", fill=(30, 58, 138), font=get_font(26, bold=True))
            draw.text((card_x + 50, y_s1 + 50), "List Comprehension (Eager):", fill=(71, 85, 105), font=get_font(24, bold=True))
            draw.rounded_rectangle([card_x + 50, y_s1 + 90, card_x + 850, y_s1 + 150], radius=16, fill=(254, 226, 226), outline=(248, 113, 113), width=2)
            draw.rounded_rectangle([card_x + 54, y_s1 + 94, card_x + 800, y_s1 + 146], radius=12, fill=(239, 68, 68))
            draw.text((card_x + 450, y_s1 + 120), "80,000,000 BYTES (~80 MB RAM)", fill=(255, 255, 255), font=font_mono, anchor="mm")

            draw.text((card_x + 50, y_s1 + 190), "Generator Expression (Lazy):", fill=(71, 85, 105), font=get_font(24, bold=True))
            draw.rounded_rectangle([card_x + 50, y_s1 + 230, card_x + 850, y_s1 + 290], radius=16, fill=(220, 252, 231), outline=(74, 222, 128), width=2)
            draw.rounded_rectangle([card_x + 54, y_s1 + 234, card_x + 120, y_s1 + 286], radius=12, fill=(34, 197, 94))
            draw.text((card_x + 450, y_s1 + 260), "112 BYTES ONLY (99.9% SAVED!)", fill=(20, 83, 45), font=font_mono, anchor="mm")

            y_s2 = card_y + 440
            draw.text((card_x + 50, y_s2), "STEP 2: HOW GENERATORS WORK UNDER THE HOOD", fill=(30, 58, 138), font=get_font(26, bold=True))
            draw.rounded_rectangle([card_x + 50, y_s2 + 40, card_x + 850, y_s2 + 200], radius=18, fill=(241, 245, 249))
            draw.text((card_x + 70, y_s2 + 75), "• Generates values one-by-one via iterator protocol (__next__)", fill=(30, 41, 59), font=get_font(24, bold=False))
            draw.text((card_x + 70, y_s2 + 115), "• State suspended between yields -> Constant O(1) memory", fill=(30, 41, 59), font=get_font(24, bold=False))
            draw.text((card_x + 70, y_s2 + 155), "• Never allocates full list in RAM!", fill=(22, 101, 52), font=get_font(24, bold=True))

            draw.rounded_rectangle([card_x + 50, card_y + 870, card_x + 850, card_y + 950], radius=16, fill=(220, 252, 231), outline=(74, 222, 128), width=2)
            draw.text((card_x + 450, card_y + 910), "⚡ RESULT: 112 BYTES FIXED RAM • ZERO CRASHES", fill=(20, 83, 45), font=get_font(24, bold=True), anchor="mm")

    else:
        # =========================================================================
        # SCENE 2: THE IDE CODE CARD & CHAR-BY-CHAR TYPING (beats[0] -> beats[1])
        # =========================================================================
        img = Image.new("RGBA", (W, H), (250, 250, 250, 255))
          draw = ImageDraw.Draw(img)

          # Add educational illustration background if available
          try:
              # Define image display schedule: which image to show when
              image_schedule = [
                  # (start_time, end_time, image_filename, fade_in_duration, fade_out_duration)
                  (beats[0] + 0.5, beats[0] + 2.5, "image.png", 0.5, 0.5),      # Show image 1 during early part
                  (beats[0] + 2.5, beats[0] + 4.5, "image copy.png", 0.5, 0.5), # Show image 2 during middle
                  (beats[0] + 4.5, beats[1] - 0.5, "image copy 2.png", 0.5, 0.5), # Show image 3 during late part
              ]
              
              # Check if current time falls within any image display window
              for start_time, end_time, img_filename, fade_in, fade_out in image_schedule:
                  if start_time <= sec < end_time:
                      # Load and composite the image
                      img_path = f"super_youtube_agent\\07_coding_studio\\assets\\images\\{img_filename}"
                      bg_img = load_image_cached(img_path)
                      
                      # Calculate alpha for fade-in/fade-out
                      alpha = 1.0
                      if sec < start_time + fade_in:
                          # Fade in
                          alpha = (sec - start_time) / fade_in
                      elif sec > end_time - fade_out:
                          # Fade out
                          alpha = (end_time - sec) / fade_out
                          
                      # Resize image to fit screen while maintaining aspect ratio
                      bg_width, bg_height = bg_img.size
                      target_ratio = W / H
                      img_ratio = bg_width / bg_height
                      
                      if img_ratio > target_ratio:
                          # Image is wider than screen ratio
                          new_width = W
                          new_height = int(W / img_ratio)
                      else:
                          # Image is taller than screen ratio
                          new_height = H
                          new_width = int(H * img_ratio)
                          
                      # Resize and center the image
                      resized_img = bg_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                      paste_x = (W - new_width) // 2
                      paste_y = (H - new_height) // 2
                      
                      # Create a temporary image with the calculated alpha
                      if alpha < 1.0:
                          # Apply alpha to the image
                          alpha_img = Image.new("RGBA", resized_img.size, (255, 255, 255, int(255 * alpha)))
                          img_to_paste = Image.blend(resized_img, alpha_img, 1.0 - alpha)
                      else:
                          img_to_paste = resized_img
                          
                      # Composite the image onto the background
                      img.paste(img_to_paste, (paste_x, paste_y), img_to_paste)
                      break  # Only show one image at a time
          except Exception as e:
              # If there's any error with image processing, continue without background
              pass

          # 1. Subtle dot grid background
          dot_gap = 36
          for x in range(24, W, dot_gap):
              for y in range(24, H, dot_gap):
                  draw.ellipse([x - 1, y - 1, x + 1, y + 1], fill=(226, 232, 240, 200))

        # 2. Dynamic Breadcrumb Navigation
        category = "Python" if "PYTHON" in series_name.upper() else "DSA" if "LEETCODE" in series_name.upper() else "DevTools"
        tag_str = getattr(lesson, "badge_tag", "Mastery").split("•")[0].strip()[:14]
        bread_y = 130
        draw.text((110, bread_y), category, fill=(148, 163, 184), font=font_bread)
        draw.text((250, bread_y), ">", fill=(203, 213, 225), font=font_bread)
        draw.text((290, bread_y), f"Day {ep_num}" if "100" in series_name else f"Ep {ep_num}", fill=(148, 163, 184), font=font_bread)
        draw.text((440, bread_y), ">", fill=(203, 213, 225), font=font_bread)
        draw.text((480, bread_y), tag_str, fill=(15, 23, 42), font=font_bread)

        # 3. White IDE Card
        card_x, card_y = 90, 215
        card_w, card_h = 900, 770

        # Elevation Drop Shadow
        for offset, alpha in [(16, 15), (10, 25), (4, 45)]:
            draw.rounded_rectangle([card_x - 2, card_y + offset, card_x + card_w + 2, card_y + card_h + offset], radius=28, fill=(0, 0, 0, alpha))
        draw.rounded_rectangle([card_x, card_y, card_x + card_w, card_y + card_h], radius=28, fill=(255, 255, 255), outline=(226, 232, 240), width=2)

        # Header bar: macOS dots + filename + dots menu
        title_bar_h = 68
        draw.ellipse([card_x + 40, card_y + 26, card_x + 58, card_y + 44], fill=(255, 95, 86))
        draw.ellipse([card_x + 68, card_y + 26, card_x + 86, card_y + 44], fill=(255, 189, 46))
        draw.ellipse([card_x + 96, card_y + 26, card_x + 114, card_y + 44], fill=(39, 201, 63))
        draw.text((card_x + 140, card_y + 35), f"{lesson.filename} • Python 3.11", fill=(15, 23, 42), font=font_card_head, anchor="lm")
        draw.text((card_x + card_w - 70, card_y + 24), "•••", fill=(148, 163, 184), font=font_huge)
        draw.line([(card_x + 20, card_y + title_bar_h), (card_x + card_w - 20, card_y + title_bar_h)], fill=(241, 245, 249), width=2)

        # Get optimal solution code for IDE display
        if hasattr(lesson, 'snippet_optimal'):
            active_code = lesson.snippet_optimal
        else:
            active_code = lesson.code_after

        full_code_raw = "\n".join([line_tuple[0] for line_tuple in active_code[:6]])
        
        # Progressive Typing Cadence (CodeVideoRenderer Style)
        type_start = beats[0]
        type_dur = max(1.2, min(2.5, (beats[1] - beats[0]) * 0.45))
        type_prog = min(1.0, max(0.0, (sec - type_start) / type_dur))

        is_typing = type_prog < 1.0
        if is_typing:
            ease_prog = 1.0 - (1.0 - type_prog) ** 1.6
            char_limit = max(1, int(len(full_code_raw) * ease_prog))
        else:
            char_limit = None

        tokenized_lines, cursor_info = tokenize_code(
            full_code_raw, language="python", is_dark=False, char_limit=char_limit
        )

        highlight_idx = 1
        for idx, (l_text, l_tok) in enumerate(active_code[:6]):
            if any(k in l_text for k in ["pivot", "seen", "basket=", "yield", "range(", "diff", "[x*", "(x*"]):
                highlight_idx = idx
                break

        start_code_y = card_y + title_bar_h + 45
        line_spacing = 66
        focus_line_y = start_code_y + highlight_idx * line_spacing

        for i, code_line in enumerate(tokenized_lines[:6]):
            curr_y = start_code_y + i * line_spacing
            draw.text((card_x + 60, curr_y), str(i + 1), fill=(148, 163, 184), font=font_mono)

            # Highlighter Wipe on key line
            if i == highlight_idx and not is_typing:
                gen_start = type_start + type_dur
                gen_sweep = min(1.0, max(0.0, (sec - gen_start) / 0.7))
                curr_w = int(740 * (1.0 - (1.0 - gen_sweep) ** 2))
                if curr_w > 0:
                    draw.rounded_rectangle([card_x + 120, curr_y - 6, card_x + 120 + curr_w, curr_y + 44], radius=8, fill=(209, 250, 229, 230))

            # Draw Token Runs
            cur_run_x = card_x + 130
            for run in code_line.runs:
                sanitized_text = run.text.replace("❌", "[x]").replace("✨", "[*]").replace("⚠️", "[!]").replace("💡", "[TIP]")
                run_color = (15, 23, 42) if (i == highlight_idx and not is_typing) else run.color
                draw.text((cur_run_x, curr_y), sanitized_text, fill=run_color, font=font_code)
                try:
                    cur_run_x += font_code.getlength(sanitized_text)
                except Exception:
                    cur_run_x += len(sanitized_text) * 16

            # Cursor Auto-Tracking
            if cursor_info and cursor_info[0] == i:
                cursor_visible = ((int(sec * 1000) % 450) < 320)
                if cursor_visible:
                    cur_line_w = cur_run_x
                    draw.line([(cur_line_w + 3, curr_y - 2), (cur_line_w + 3, curr_y + 38)], fill=(14, 165, 233), width=3)

        # Docked Tooltip Callout Badge at Bottom of IDE Card
        if not is_typing:
            badge_w = 520
            badge_x = card_x + card_w - badge_w - 40
            badge_y = card_y + card_h - 72
            draw.rounded_rectangle([badge_x, badge_y, badge_x + badge_w, badge_y + 46], radius=14, fill=(220, 252, 231), outline=(74, 222, 128), width=2)
            draw.text((badge_x + badge_w // 2, badge_y + 23), "⚡ Production Clean (Optimal Solution) [*]", fill=(20, 83, 45), font=get_font(21, bold=True), anchor="mm")

        # 4. Terminal Card Underneath
        term_x, term_y = 90, 1035
        term_w, term_h = 900, 260
        for offset, alpha in [(10, 15), (4, 30)]:
            draw.rounded_rectangle([term_x, term_y + offset, term_x + term_w, term_y + term_h + offset], radius=24, fill=(0, 0, 0, alpha))
        draw.rounded_rectangle([term_x, term_y, term_x + term_w, term_y + term_h], radius=24, fill=(255, 255, 255), outline=(226, 232, 240), width=2)
        draw.text((term_x + 50, term_y + 20), "Terminal", fill=(100, 116, 139), font=font_card_head)

        in_box_y = term_y + 62
        terminal_command = getattr(lesson, "terminal_cmd", getattr(lesson, "terminal_command", "$ python3 main.py"))
        terminal_output = getattr(lesson, "terminal_output", getattr(lesson, "terminal_logs", []))
        draw.rounded_rectangle([term_x + 25, in_box_y, term_x + term_w - 25, term_y + term_h - 20], radius=16, fill=(24, 24, 27))
        draw.text((term_x + 55, in_box_y + 36), terminal_command, fill=(244, 244, 245), font=font_mono, anchor="lm")

        if terminal_output:
            for log_idx, log_line in enumerate(terminal_output[:2]):
                log_color = (74, 222, 128) if any(k in log_line for k in ["✓", "PASS", "SPEEDUP", "RESULT", "Test", "SORTED"]) else (248, 113, 113) if "⚠️" in log_line or "Peak: 8" in log_line or "BUG" in log_line else (244, 244, 245)
                draw.text((term_x + 55, in_box_y + 78 + log_idx * 36), log_line[:52], fill=log_color, font=font_mono, anchor="lm")

        # 5. Teacher Tip Card
        tip_x, tip_y = 90, 1335
        tip_w, tip_h = 900, 220
        for offset, alpha in [(8, 12), (3, 20)]:
            draw.rounded_rectangle([tip_x, tip_y + offset, tip_x + tip_w, tip_y + tip_h + offset], radius=24, fill=(0, 0, 0, alpha))
        draw.rounded_rectangle([tip_x, tip_y, tip_x + tip_w, tip_y + tip_h], radius=24, fill=(254, 243, 199), outline=(253, 230, 138), width=2)

        draw.rounded_rectangle([tip_x + 35, tip_y + 35, tip_x + 115, tip_y + 115], radius=20, fill=(251, 191, 36))
        draw.text((tip_x + 75, tip_y + 75), "TIP", fill=(120, 53, 15), font=get_font(24, bold=True), anchor="mm")
        draw.text((tip_x + 140, tip_y + 44), "Teacher Tip", fill=(146, 64, 14), font=font_tip_title)

        raw_tip = getattr(lesson, "teacher_tip", "Clean code wins!").replace("TEACHER TIP:", "").strip()
        words_tip = raw_tip.split()
        tip_lines = []
        curr_l = []
        for w in words_tip:
            if len(" ".join(curr_l + [w])) > 54:
                tip_lines.append(" ".join(curr_l))
                curr_l = [w]
            else:
                curr_l.append(w)
        if curr_l:
            tip_lines.append(" ".join(curr_l))

        for idx, l in enumerate(tip_lines[:3]):
            draw.text((tip_x + 140, tip_y + 88 + idx * 34), l, fill=(180, 83, 9), font=font_tip_body)


    # =========================================================================
    # 6. KINETIC KARAOKE SUBTITLES (Safe Margin 9:16 - Fixed overlay)
    # =========================================================================
    sub_box_y = 1660
    hook_txt = getattr(lesson, "intro_hook", "")
    trap_txt = getattr(lesson, "concept_walkthrough", "")
    sol_txt = getattr(lesson, "code_explanation", "")
    out_txt = getattr(lesson, "outro_homework", "")

    active_speech = (
        hook_txt if sec < beats[0] else
        trap_txt if sec < beats[1] else
        sol_txt if sec < beats[2] else
        out_txt
    )

    words = active_speech.split()
    lines_sub = []
    curr_line = []
    for w in words:
        test_line = " ".join(curr_line + [w])
        if len(test_line) > 36:
            lines_sub.append(" ".join(curr_line))
            curr_line = [w]
        else:
            curr_line.append(w)
    if curr_line:
        lines_sub.append(" ".join(curr_line))

    line1 = lines_sub[0] if len(lines_sub) > 0 else ""
    line2 = lines_sub[1] if len(lines_sub) > 1 else ""

    box_w = 940
    font_sub_cal = get_font(28, bold=True)
    draw.rounded_rectangle([W // 2 - box_w // 2, sub_box_y - 20, W // 2 + box_w // 2, sub_box_y + 125], radius=22, fill=(15, 23, 42), outline=(250, 204, 21), width=3)
    draw.text((W // 2, sub_box_y + 24), line1, fill=(255, 255, 255), font=font_sub_cal, anchor="mm")
    if line2:
        draw.text((W // 2, sub_box_y + 76), line2, fill=(56, 189, 248), font=font_sub_cal, anchor="mm")

    # 7. Bottom Branding Telemetry
    draw.text((W // 2, 1835), "CHANNEL 7 // CODE CRAFT • 100 DAYS OF PYTHON • 60 FPS", fill=(148, 163, 184), font=font_hud, anchor="mm")

    return img.convert("RGB")



async def render_coding_short(lesson_id: str | None = None) -> Path:
    lesson = None
    if lesson_id:
        # First check curriculum lessons (advanced CS topics)
        curriculum_lesson = get_lesson(lesson_id)
        if curriculum_lesson:
            lesson = curriculum_lesson
        else:
            clean_id = lesson_id.strip().lower()

            # 1. Check if specific day/episode number requested (e.g. "day 1", "1", "day 14")
            parts = clean_id.split()
            for p in parts:
                if p.isdigit():
                    target_num = int(p)
                    for tl in MASTER_SERIES_CATALOG:
                        if tl.episode_num == target_num:
                            lesson = tl
                            break
                    if lesson:
                        break

            # 2. Match directly in MASTER_SERIES_CATALOG by string
            if not lesson:
                for tl in MASTER_SERIES_CATALOG:
                    if clean_id in tl.topic_title.lower() or clean_id in tl.series_name.lower() or clean_id in tl.filename.lower():
                        lesson = tl
                        break

    # 3. If not matched, query Teacher Brain (AI Dynamic Generator or Sequential progression)
    if not lesson:
        lesson = get_next_teacher_lesson(lesson_id)

    title = getattr(lesson, "topic_title", getattr(lesson, "title", "Coding Lesson"))
    series = getattr(lesson, "series_name", getattr(lesson, "series", "Python Masterclass"))
    ep = getattr(lesson, "episode_num", 1)
    les_id = getattr(lesson, "id", f"{series.lower().replace(' ', '_')}_{ep}")
    
    print("\n" + "=" * 70)
    print(f"🎬 [Channel 7 Coding Studio] Producing Teacher Masterclass: {title}")
    print(f"📚 Series: {series} • Episode #{ep}")
    print("=" * 70)

    t0 = time.time()

    # 1. Voiceover
    print(f"🎙️ Generating teacher narration via Kokoro-82M...")
    wav_path, beats, duration = await generate_speech_tracks(lesson, OUTPUT_DIR)
    print(f"✅ Voiceover rendered: {duration:.2f}s (Beats: {[round(b, 2) for b in beats]})")

    # 2. Sound Design: Mix Mechanical Keyboard, Marker Wipe, Enter Key Click, Ding
    print("🎧 Synthesizing Diegetic Coding Foley & Keyboard Keystrokes SFX...")
    master_soundtrack = OUTPUT_DIR / f"{les_id}_master_soundtrack.wav"
    try:
        # Define helper functions for typing synchronization
        def is_optimal_phase(sec):
            return sec >= beats[1] if len(beats) > 1 else False
            
        def get_active_code():
            # Get the appropriate code snippets based on lesson type
            if hasattr(lesson, 'snippet_naive'):  # CodingLesson
                naive_code = lesson.snippet_naive
                optimal_code = lesson.snippet_optimal
            else:  # TeacherLesson
                naive_code = lesson.code_before
                optimal_code = lesson.code_after
            return optimal_code if is_optimal_phase(0) else naive_code  # Default to naive for getting active code
            
        def get_full_code_raw():
            active_code = get_active_code()
            return "\n".join([line_tuple[0] for line_tuple in active_code[:6]])
            
        def get_type_start(sec):
            # Determine if we're in optimal phase at this second
            if is_optimal_phase(sec):
                return beats[1] if len(beats) > 1 else 0.5
            else:
                return 0.5
                
        def get_type_duration(sec):
            # Determine if we're in optimal phase at this second
            if is_optimal_phase(sec):
                return 1.7  # Optimal phase typing duration
            else:
                return 1.9  # Naive phase typing duration
        
        build_teacher_foley_soundtrack(
            wav_path, 
            master_soundtrack, 
            beats,
            lesson=lesson,
            is_optimal_phase_func=is_optimal_phase,
            get_active_code_func=get_active_code,
            get_full_code_raw_func=get_full_code_raw,
            get_type_start_func=get_type_start,
            get_type_duration_func=get_type_duration
        )
        final_audio_path = master_soundtrack
        print("✅ Foley & SFX sound track mixed seamlessly!")
    except Exception as e:
        print(f"⚠️ SFX mixing notice ({e}), using raw voiceover")
        final_audio_path = wav_path

    fps = 30
    total_frames = int(duration * fps)

    font_code = get_font(26, bold=True)
    font_title = get_font(28, bold=True)
    font_sub = get_font(40, bold=True)
    font_hud = get_font(22, bold=True)

    out_mp4 = OUTPUT_DIR / f"{les_id}_vox_short.mp4"
    print(f"🚀 Rendering {total_frames} frames via FFmpeg Pipe at {fps} FPS (1080x1920)...")

    ffmpeg_cmd = [
        "ffmpeg", "-y",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-s", "1080x1920",
        "-pix_fmt", "rgb24",
        "-r", str(fps),
        "-i", "-",
        "-i", str(final_audio_path),
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

    # Save YouTube & Playlist Metadata
    yt_meta = {
        "title": f"{series} • Ep {ep}: {title} ⚡ #shorts",
        "description": (
            f"🔥 Welcome to {series} (Episode {ep})!\n\n"
            f"Topic: {title}\n"
            f"Series Playlist: {series} Masterclass\n\n"
            f"💡 Teacher Pro-Tip:\n{getattr(lesson, 'teacher_tip', 'Clean code wins!')}\n\n"
            f"Subscribe to Channel 7 for daily Senior Software Engineer breakdowns, DSA patterns, and modern Python tools.\n\n"
            f"#coding #programming #python #dsa #softwareengineer #webdev #shorts #developer"
        ),
        "playlist_title": f"{series} Masterclass",
        "tags": ["coding", "programming", "python", "dsa", "leetcode", "software engineer", "developer", "tech", "shorts"],
        "category_id": "28",
        "privacy": os.getenv("PRIVACY_OPT", "unlisted")
    }
    meta_path = OUTPUT_DIR / f"{les_id}_metadata.json"
    meta_path.write_text(json.dumps(yt_meta, indent=2), encoding="utf-8")
    print(f"📄 YouTube Playlist Metadata saved: {meta_path}")

    # Dispatch to Telegram
    print("📱 Sending Pedagogical Coding Video to Telegram...")
    repo_root = CURRENT_DIR.parents[1]
    telegram_script = repo_root / "send_to_telegram.py"
    if not telegram_script.exists():
        telegram_script = Path("d:/facts_yt/send_to_telegram.py")

    if telegram_script.exists():
        subprocess.run([sys.executable, str(telegram_script), str(OUTPUT_DIR)], check=False)
        print("✅ Telegram notification dispatched!")

    return out_mp4


if __name__ == "__main__":
    query = sys.argv[1] if len(sys.argv) > 1 else "two_sum_hashmap"
    asyncio.run(render_coding_short(query))
