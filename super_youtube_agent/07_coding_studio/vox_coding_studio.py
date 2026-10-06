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
    """Generates continuous voiceover and measures beat durations."""
    hook = getattr(lesson, "intro_hook", None) or getattr(lesson, "hook_narration", "")
    trap = getattr(lesson, "concept_walkthrough", None) or getattr(lesson, "trap_narration", "")
    solution = getattr(lesson, "code_explanation", None) or getattr(lesson, "solution_narration", "")
    takeaway = getattr(lesson, "outro_homework", None) or getattr(lesson, "takeaway_narration", "")

    full_script = f"{hook} {trap} {solution} {takeaway}"
    les_id = getattr(lesson, "id", None) or f"{lesson.series_name.lower().replace(' ', '_')}_{lesson.episode_num}"
    mp3_path = output_dir / f"{les_id}_voice.mp3"
    wav_path = output_dir / f"{les_id}_voice.wav"

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
    words_h = len(hook.split())
    words_t = len(trap.split())
    words_s = len(solution.split())
    words_o = len(takeaway.split())
    total_words = words_h + words_t + words_s + words_o

    b1_end = total_duration * (words_h / max(1, total_words))
    b2_end = total_duration * ((words_h + words_t) / max(1, total_words))
    b3_end = total_duration * ((words_h + words_t + words_s) / max(1, total_words))
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

        for offset, alpha in [(12, 15), (6, 25)]:
            draw.rounded_rectangle([left_x, card_y + offset, left_x + card_w, card_y + card_h + offset], radius=32, fill=(0, 0, 0, alpha))
        draw.rounded_rectangle([left_x, card_y, left_x + card_w, card_y + card_h], radius=32, fill=(254, 205, 211), outline=(251, 113, 133), width=2)
        draw.text((left_x + card_w // 2, card_y + 90), left_title, fill=(159, 18, 57), font=font_head_comp, anchor="mm")
        draw.text((left_x + card_w // 2, card_y + 135), f"• {left_sub}", fill=(190, 18, 60), font=font_head_comp, anchor="mm")
        # Code pill
        draw.rounded_rectangle([left_x + 20, card_y + 360, left_x + card_w - 20, card_y + 440], radius=20, fill=(39, 39, 42))
        draw.text((left_x + card_w // 2, card_y + 400), left_pill, fill=(255, 255, 255), font=font_mono, anchor="mm")

        # Right Card: Soft Mint Green (Optimal / Production)
        right_title = "OPTIMAL FIX"
        for l_t, _ in optimal_code:
            if l_t.startswith("# ✨"):
                right_title = l_t.replace("# ✨", "").split("(")[0].strip()[:20]
                break
        right_sub = "PRODUCTION CLEAN"

        right_pill = ""
        for l_t, _ in optimal_code:
            if not l_t.startswith("#") and len(l_t.strip()) > 3:
                right_pill = l_t.strip()[:26]
                break
        if not right_pill:
            right_pill = "Clean Code"

        for offset, alpha in [(12, 15), (6, 25)]:
            draw.rounded_rectangle([right_x, card_y + offset, right_x + card_w, card_y + card_h + offset], radius=32, fill=(0, 0, 0, alpha))
        draw.rounded_rectangle([right_x, card_y, right_x + card_w, card_y + card_h], radius=32, fill=(209, 250, 229), outline=(52, 211, 153), width=2)
        draw.text((right_x + card_w // 2, card_y + 90), right_title, fill=(6, 95, 70), font=font_head_comp, anchor="mm")
        draw.text((right_x + card_w // 2, card_y + 135), f"• {right_sub}", fill=(4, 120, 87), font=font_head_comp, anchor="mm")
        # Code pill
        draw.rounded_rectangle([right_x + 20, card_y + 360, right_x + card_w - 20, card_y + 440], radius=20, fill=(39, 39, 42))
        draw.text((right_x + card_w // 2, card_y + 400), right_pill, fill=(255, 255, 255), font=font_mono, anchor="mm")

        # Center VS Badge
        vs_cx, vs_cy = W // 2, card_y + 400
        draw.ellipse([vs_cx - 48, vs_cy - 48, vs_cx + 48, vs_cy + 48], fill=(255, 255, 255), outline=(226, 232, 240), width=3)
        draw.text((vs_cx, vs_cy), "VS", fill=(15, 23, 42), font=font_vs, anchor="mm")

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

        draw.text((save_x + 145, save_y + 85), bot_metric, fill=(30, 58, 138), font=get_font(32, bold=True), anchor="lm")
        draw.text((save_x + 145, save_y + 150), bot_sub[:62], fill=(30, 64, 175), font=font_tip_body, anchor="lm")

    else:
        # =========================================================================
        # STYLE 1: WHITE MINIMAL SWISS UI (Exact match to Image 1 & 3)
        # =========================================================================
        img = Image.new("RGBA", (W, H), (250, 250, 250, 255))
        draw = ImageDraw.Draw(img)

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

        # Determine Phase (Naive vs Optimal) - Handle both CodingLesson and TeacherLesson
        is_optimal_phase = sec >= beats[1]
        
        # Get the appropriate code snippets based on lesson type
        if hasattr(lesson, 'snippet_naive'):  # CodingLesson
            naive_code = lesson.snippet_naive
            optimal_code = lesson.snippet_optimal
        else:  # TeacherLesson
            naive_code = lesson.code_before
            optimal_code = lesson.code_after
            
        active_code = optimal_code if is_optimal_phase else naive_code

        # Reconstruct raw string for syntax tokenization and progressive typing
        full_code_raw = "\n".join([line_tuple[0] for line_tuple in active_code[:6]])
        
        # Progressive Typing Cadence (CodeVideoRenderer Style)
        if not is_optimal_phase:
            type_start = 0.5
            type_dur = 1.9
            type_prog = min(1.0, max(0.0, (sec - type_start) / type_dur))
        else:
            type_start = beats[1]
            type_dur = 1.7
            type_prog = min(1.0, max(0.0, (sec - type_start) / type_dur))

        is_typing = type_prog < 1.0
        if is_typing:
            # Ease-out typing curve with tactile cadence
            ease_prog = 1.0 - (1.0 - type_prog) ** 1.6
            char_limit = max(1, int(len(full_code_raw) * ease_prog))
        else:
            char_limit = None

        # Tokenize code with Pygments syntax engine
        tokenized_lines, cursor_info = tokenize_code(
            full_code_raw, language="python", is_dark=False, char_limit=char_limit
        )

        # Determine which line to highlight dynamically:
        highlight_idx = 1
        for idx, (l_text, l_tok) in enumerate(active_code[:6]):
            if any(k in l_text for k in ["⚠️", "BUG", "range(", "basket=", "visited", "slow =", "[x*", "(x*", "pl.col"]):
                highlight_idx = idx
                break
            elif l_tok in ["def", "assign", "loop"] and idx > 0:
                highlight_idx = idx
                break

        start_code_y = card_y + title_bar_h + 45
        line_spacing = 66
        focus_line_y = start_code_y + highlight_idx * line_spacing

        # Render code lines with token-level Pygments syntax highlighting
        for i, code_line in enumerate(tokenized_lines[:6]):
            curr_y = start_code_y + i * line_spacing
            
            # Line number
            draw.text((card_x + 60, curr_y), str(i + 1), fill=(148, 163, 184), font=font_mono)

            # Highlighter / Execution Backgrounds (Active once typing completes)
            if i == highlight_idx and not is_typing:
                if not is_optimal_phase:
                    # Animated yellow highlighter marker sweep
                    marker_start = 2.6
                    sweep_prog = min(1.0, max(0.0, (sec - marker_start) / 0.8))
                    ease_sweep = 1.0 - (1.0 - sweep_prog) ** 2
                    curr_w = int(740 * ease_sweep)
                    if curr_w > 0:
                        draw.rounded_rectangle([card_x + 120, curr_y - 6, card_x + 120 + curr_w, curr_y + 44], radius=8, fill=(254, 240, 138, 230))
                else:
                    # Phase 2: Animated mint green sweep
                    gen_start = beats[1] + type_dur
                    gen_sweep = min(1.0, max(0.0, (sec - gen_start) / 0.7))
                    curr_w = int(740 * (1.0 - (1.0 - gen_sweep) ** 2))
                    if curr_w > 0:
                        draw.rounded_rectangle([card_x + 120, curr_y - 6, card_x + 120 + curr_w, curr_y + 44], radius=8, fill=(209, 250, 229, 230))

            # Execution Indicator Pointer when Terminal is actively evaluating
            if sec >= beats[0] and sec < beats[1] and i == highlight_idx:
                draw.ellipse([card_x + 35, curr_y + 12, card_x + 47, curr_y + 24], fill=(239, 68, 68))

            # Draw Token Runs with Pygments Syntax Colors
            cur_run_x = card_x + 130
            for run in code_line.runs:
                # Sanitize emojis from raw code text for clean Consolas rendering
                sanitized_text = (
                    run.text.replace("❌", "[x]")
                    .replace("✨", "[*]")
                    .replace("⚠️", "[!]")
                    .replace("💡", "[TIP]")
                )
                run_color = (15, 23, 42) if (i == highlight_idx and not is_typing) else run.color
                draw.text((cur_run_x, curr_y), sanitized_text, fill=run_color, font=font_code)
                try:
                    cur_run_x += font_code.getlength(sanitized_text)
                except Exception:
                    cur_run_x += len(sanitized_text) * 16

            # Cursor Auto-Tracking (ExploreMaths / CodeVideoRenderer style)
            if cursor_info and cursor_info[0] == i:
                cursor_visible = ((int(sec * 1000) % 450) < 320)
                if cursor_visible:
                    cur_line_w = cur_run_x
                    draw.line(
                        [(cur_line_w + 3, curr_y - 2), (cur_line_w + 3, curr_y + 38)],
                        fill=(14, 165, 233), width=3
                    )

        # Docked Tooltip Callout Badge at Bottom of IDE Card (Zero text collision)
        if not is_typing:
            if not is_optimal_phase:
                marker_start = 2.6
                sweep_prog = min(1.0, max(0.0, (sec - marker_start) / 0.8))
                ease_sweep = 1.0 - (1.0 - sweep_prog) ** 2
                if ease_sweep > 0.35:
                    badge_pop = min(1.0, (ease_sweep - 0.35) / 0.65)
                    tooltip_txt = "Allocates 10M ints → ~80MB RAM [!]" if ("10M" in full_code_raw or "14" in str(ep_num)) else "Pitfall: Inefficient Pattern [!]"
                    badge_w = int(500 * badge_pop)
                    badge_x = card_x + card_w - badge_w - 40
                    badge_y = card_y + card_h - 72
                    if badge_w > 80:
                        draw.rounded_rectangle([badge_x, badge_y, badge_x + badge_w, badge_y + 46], radius=14, fill=(254, 249, 195), outline=(253, 224, 71), width=2)
                        if badge_pop >= 0.85:
                            draw.text((badge_x + badge_w // 2, badge_y + 23), tooltip_txt, fill=(113, 63, 18), font=get_font(21, bold=True), anchor="mm")
            else:
                gen_start = beats[1] + type_dur
                gen_sweep = min(1.0, max(0.0, (sec - gen_start) / 0.7))
                if gen_sweep > 0.3:
                    badge_w = 480
                    badge_x = card_x + card_w - badge_w - 40
                    badge_y = card_y + card_h - 72
                    draw.rounded_rectangle([badge_x, badge_y, badge_x + badge_w, badge_y + 46], radius=14, fill=(220, 252, 231), outline=(74, 222, 128), width=2)
                    draw.text((badge_x + badge_w // 2, badge_y + 23), "Production Clean: 112 Bytes (O(1)) [*]", fill=(20, 83, 45), font=get_font(21, bold=True), anchor="mm")

        # 4. Dynamic Terminal Card
        term_x, term_y = 90, 1035
        term_w, term_h = 900, 260
        for offset, alpha in [(10, 15), (4, 30)]:
            draw.rounded_rectangle([term_x, term_y + offset, term_x + term_w, term_y + term_h + offset], radius=24, fill=(0, 0, 0, alpha))
        draw.rounded_rectangle([term_x, term_y, term_x + term_w, term_y + term_h], radius=24, fill=(255, 255, 255), outline=(226, 232, 240), width=2)
        draw.text((term_x + 50, term_y + 20), "Terminal", fill=(100, 116, 139), font=font_card_head)

        in_box_y = term_y + 62
        # Get the appropriate terminal attributes based on lesson type
        if hasattr(lesson, 'terminal_cmd'):  # CodingLesson
            terminal_command = lesson.terminal_cmd
            terminal_output = lesson.terminal_output
        else:  # TeacherLesson
            terminal_command = getattr(lesson, "terminal_command", "$ python3 main.py")
            terminal_output = getattr(lesson, "terminal_logs", [])
        
        draw.rounded_rectangle([term_x + 25, in_box_y, term_x + term_w - 25, term_y + term_h - 20], radius=16, fill=(24, 24, 27))
        draw.text((term_x + 55, in_box_y + 36), terminal_command, fill=(244, 244, 245), font=font_mono, anchor="lm")

        # Dynamic terminal logs streaming
        if sec > beats[0] and terminal_output:
            elapsed_term = sec - beats[0]
            for log_idx, log_line in enumerate(terminal_output[:3]):
                if elapsed_term >= 0.4 + log_idx * 0.7:
                    log_color = (74, 222, 128) if any(k in log_line for k in ["✓", "PASS", "SPEEDUP", "RESULT", "Test", "SORTED"]) else (248, 113, 113) if "⚠️" in log_line or "Peak: 8" in log_line or "BUG" in log_line else (244, 244, 245)
                    draw.text((term_x + 55, in_box_y + 78 + log_idx * 36), log_line[:52], fill=log_color, font=font_mono, anchor="lm")

        # 5. Dynamic Teacher Tip Card (Crisp Vector Badge)
        tip_x, tip_y = 90, 1335
        tip_w, tip_h = 900, 220
        for offset, alpha in [(8, 12), (3, 20)]:
            draw.rounded_rectangle([tip_x, tip_y + offset, tip_x + tip_w, tip_y + tip_h + offset], radius=24, fill=(0, 0, 0, alpha))
        draw.rounded_rectangle([tip_x, tip_y, tip_x + tip_w, tip_y + tip_h], radius=24, fill=(254, 243, 199), outline=(253, 230, 138), width=2)

        draw.rounded_rectangle([tip_x + 35, tip_y + 35, tip_x + 115, tip_y + 115], radius=20, fill=(251, 191, 36))
        draw.text((tip_x + 75, tip_y + 75), "TIP", fill=(120, 53, 15), font=get_font(24, bold=True), anchor="mm")
        draw.text((tip_x + 140, tip_y + 44), "Teacher Tip", fill=(146, 64, 14), font=font_tip_title)

        # Clean auto-wrapping for teacher tip
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

        # Dynamic Camera Zoom on the highlighted line
        zoom = 1.0
        if 2.5 <= sec <= 8.5:
            zoom_factor = math.sin((sec - 2.5) / 6.0 * math.pi)
            zoom = 1.0 + 0.12 * zoom_factor

        if zoom > 1.005:
            crop_w = int(W / zoom)
            crop_h = int(H / zoom)
            focus_x = W // 2
            focus_y = int(card_y + title_bar_h + 100)
            x1 = max(0, min(W - crop_w, focus_x - crop_w // 2))
            y1 = max(0, min(H - crop_h, focus_y - crop_h // 2))
            cropped = img.crop((x1, y1, x1 + crop_w, y1 + crop_h))
            img = cropped.resize((W, H), Image.Resampling.BILINEAR)
            draw = ImageDraw.Draw(img)

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
    print(f"🎙️ Generating continuous teacher narration via Edge TTS Jenny...")
    wav_path, beats, duration = await generate_speech_tracks(lesson, OUTPUT_DIR)
    print(f"✅ Voiceover rendered: {duration:.2f}s (Beats: {[round(b, 2) for b in beats]})")

    # 2. Sound Design: Mix Mechanical Keyboard, Marker Wipe, Enter Key Click, Ding
    print("🎧 Synthesizing Diegetic Coding Foley & Keyboard Keystrokes SFX...")
    master_soundtrack = OUTPUT_DIR / f"{les_id}_master_soundtrack.wav"
    try:
        build_teacher_foley_soundtrack(wav_path, master_soundtrack, beats)
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
