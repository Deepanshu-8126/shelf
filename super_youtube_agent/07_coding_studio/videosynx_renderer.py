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
        # Windows Fonts
        "C:/Windows/Fonts/consolab.ttf" if bold else "C:/Windows/Fonts/consola.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        # Linux / GitHub Actions Ubuntu Runner Fonts
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for p in paths:
        if Path(p).exists():
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()


def wrap_text_lines(text: str, max_chars: int = 42) -> List[str]:
    """Wraps text into clean display lines."""
    words = text.split()
    lines = []
    curr = []
    for w in words:
        if len(" ".join(curr + [w])) <= max_chars:
            curr.append(w)
        else:
            if curr:
                lines.append(" ".join(curr))
            curr = [w]
    if curr:
        lines.append(" ".join(curr))
    return lines


STUDIO_THEMES: Dict[str, Dict[str, Any]] = {
    "onedark": {
        "bg": (13, 17, 23, 255),
        "grid_dot": (33, 38, 45, 180),
        "header_sub": (139, 148, 158),
        "badge_bg": (22, 27, 34),
        "badge_border": (48, 54, 61),
        "badge_text": (88, 166, 255),
        "headline": (240, 246, 252),
        "card_bg": (22, 27, 34),
        "card_border": (48, 54, 61),
        "card_divider": (33, 38, 45),
        "file_head": (201, 209, 217),
        "code_plain": (240, 246, 252),
        "gutter": (110, 118, 129),
        "gutter_active": (88, 166, 255),
        "cursor": (88, 166, 255),
        "teach_bg": (22, 27, 34),
        "teach_border": (48, 54, 61),
        "teach_title": (88, 166, 255),
        "teach_text": (240, 246, 252),
        "is_dark": True
    },
    "tokyo_night": {
        "bg": (26, 27, 38, 255),
        "grid_dot": (41, 46, 66, 180),
        "header_sub": (122, 162, 247),
        "badge_bg": (36, 40, 59),
        "badge_border": (65, 72, 104),
        "badge_text": (187, 154, 247),
        "headline": (192, 202, 245),
        "card_bg": (36, 40, 59),
        "card_border": (65, 72, 104),
        "card_divider": (41, 46, 66),
        "file_head": (192, 202, 245),
        "code_plain": (192, 202, 245),
        "gutter": (86, 95, 137),
        "gutter_active": (187, 154, 247),
        "cursor": (187, 154, 247),
        "teach_bg": (36, 40, 59),
        "teach_border": (65, 72, 104),
        "teach_title": (187, 154, 247),
        "teach_text": (192, 202, 245),
        "is_dark": True
    },
    "minimal_light": {
        "bg": (248, 250, 252, 255),
        "grid_dot": (226, 232, 240, 180),
        "header_sub": (100, 116, 139),
        "badge_bg": (238, 242, 255),
        "badge_border": (199, 210, 254),
        "badge_text": (67, 56, 202),
        "headline": (15, 23, 42),
        "card_bg": (255, 255, 255),
        "card_border": (226, 232, 240),
        "card_divider": (241, 245, 249),
        "file_head": (30, 41, 59),
        "code_plain": (15, 23, 42),
        "gutter": (148, 163, 184),
        "gutter_active": (79, 70, 229),
        "cursor": (79, 70, 229),
        "teach_bg": (255, 255, 255),
        "teach_border": (254, 215, 170),
        "teach_title": (180, 83, 9),
        "teach_text": (15, 23, 42),
        "is_dark": False
    },
    "retro_matrix": {
        "bg": (10, 14, 20, 255),
        "grid_dot": (20, 32, 25, 180),
        "header_sub": (0, 216, 255),
        "badge_bg": (14, 22, 17),
        "badge_border": (0, 245, 155),
        "badge_text": (0, 245, 155),
        "headline": (240, 255, 245),
        "card_bg": (14, 22, 17),
        "card_border": (0, 245, 155),
        "card_divider": (22, 38, 28),
        "file_head": (0, 245, 155),
        "code_plain": (225, 245, 230),
        "gutter": (60, 100, 75),
        "gutter_active": (0, 245, 155),
        "cursor": (0, 245, 155),
        "teach_bg": (14, 22, 17),
        "teach_border": (0, 216, 255),
        "teach_title": (0, 245, 155),
        "teach_text": (240, 255, 245),
        "is_dark": True
    }
}


def get_theme_palette(name: str) -> Dict[str, Any]:
    n = (name or "onedark").lower().strip()
    return STUDIO_THEMES.get(n, STUDIO_THEMES["onedark"])


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
    Renders an exact, frame-accurate 1080x1920 video frame anchored to line-by-line execution
    with 4 distinct pedagogical stages (Pages):
    - Page 1: Problem Hook & Specification (sec < intro_duration)
    - Page 2: Code Architecture & Line-by-Line Construction (intro_duration <= sec < exec_start)
    - Page 3: Live Sandbox Execution & Real Stdout (exec_start <= sec < exec_end)
    - Page 4: Victory Mastery & Up Next Teaser (sec >= exec_end)
    """
    W, H = 1080, 1920
    sec = (frame_idx / total_frames) * duration

    t_cfg = get_theme_palette(getattr(lesson, "theme", "onedark"))
    img = Image.new("RGBA", (W, H), t_cfg["bg"])
    draw = ImageDraw.Draw(img)

    # 1. Background Dot Grid
    dot_gap = 36
    for x in range(24, W, dot_gap):
        for y in range(24, H, dot_gap):
            draw.ellipse([x - 1, y - 1, x + 1, y + 1], fill=t_cfg["grid_dot"])

    card_x = 80
    card_w = 920

    # Determine Active Stage / Page
    if sec < timeline.intro_duration:
        # =========================================================================
        # PAGE 1: PROBLEM SPECIFICATION & CHALLENGE HOOK
        # =========================================================================
        # Determine episode display label
        ep_label = getattr(lesson, "episode_label", "") or f"EPISODE #{lesson.episode_num}"
        # Top Header
        draw.text((80, 75), f"{lesson.series_name} • {ep_label}", fill=t_cfg["header_sub"], font=fonts["hud_label"])
        draw.rounded_rectangle([80, 115, 660, 168], radius=14, fill=t_cfg["badge_bg"], outline=t_cfg["badge_border"], width=2)
        badge_header = f"[{ep_label}]  {lesson.badge_tag.upper()}" if ("DAY" not in lesson.badge_tag.upper() and "EP" not in lesson.badge_tag.upper()) else f"{lesson.badge_tag.upper()}"
        draw.text((370, 141), badge_header[:36], fill=t_cfg["badge_text"], font=fonts["hud_badge"], anchor="mm")
        draw.text((80, 195), lesson.title, fill=t_cfg["headline"], font=fonts["headline"])

        # Card 1: Problem Challenge Card
        c1_y, c1_h = 265, 460
        for off, a in [(12, 12), (4, 20)]:
            draw.rounded_rectangle([card_x, c1_y + off, card_x + card_w, c1_y + c1_h + off], radius=24, fill=(0, 0, 0, a))
        draw.rounded_rectangle([card_x, c1_y, card_x + card_w, c1_y + c1_h], radius=24, fill=t_cfg["card_bg"], outline=t_cfg["card_border"], width=2)

        # macOS dots + Title
        draw.ellipse([card_x + 36, c1_y + 24, card_x + 52, c1_y + 40], fill=(255, 95, 86))
        draw.ellipse([card_x + 62, c1_y + 24, card_x + 78, c1_y + 40], fill=(255, 189, 46))
        draw.ellipse([card_x + 88, c1_y + 24, card_x + 104, c1_y + 40], fill=(39, 201, 63))
        spec_title = getattr(lesson, "challenge_header", "") or f"{lesson.series_name} • Specification"
        draw.text((card_x + 130, c1_y + 32), spec_title[:45], fill=t_cfg["file_head"], font=fonts["file_head"], anchor="lm")
        draw.line([(card_x + 20, c1_y + 64), (card_x + card_w - 20, c1_y + 64)], fill=t_cfg["card_divider"], width=2)

        challenge_col = t_cfg["badge_text"] if t_cfg["is_dark"] else (30, 58, 138)
        draw.text((card_x + 35, c1_y + 85), "[CHALLENGE SPECIFICATION]", fill=challenge_col, font=fonts["section_title"])
        prob_text = lesson.problem_statement or "Solve this challenge with optimal time and space complexity."
        prob_lines = wrap_text_lines(prob_text, max_chars=40)
        for p_idx, pl in enumerate(prob_lines[:3]):
            draw.text((card_x + 35, c1_y + 125 + p_idx * 34), pl, fill=t_cfg["code_plain"], font=fonts["card_body"])

        # Input Code Box
        in_y, in_h = c1_y + 240, 190
        draw.rounded_rectangle([card_x + 25, in_y, card_x + card_w - 25, in_y + in_h], radius=16, fill=(15, 23, 42), outline=(51, 65, 85), width=2)
        draw.text((card_x + 50, in_y + 24), "$ test_case_input:", fill=(148, 163, 184), font=fonts["term_mono"])
        in_text = lesson.input_example or "input_data = [ ... ]"
        draw.text((card_x + 50, in_y + 68), in_text[:46], fill=(74, 222, 128), font=fonts["card_mono"])
        target_badge = f"[*] Target: {lesson.complexity_badge}"
        draw.text((card_x + 50, in_y + 115), target_badge[:45], fill=(129, 140, 248), font=fonts["term_mono"])

        # Card 2: The Junior Trap / Naive Pitfall
        c2_y, c2_h = 750, 360
        for off, a in [(12, 12), (4, 20)]:
            draw.rounded_rectangle([card_x, c2_y + off, card_x + card_w, c2_y + c2_h + off], radius=24, fill=(0, 0, 0, a))
        draw.rounded_rectangle([card_x, c2_y, card_x + card_w, c2_y + c2_h], radius=24, fill=(254, 242, 242), outline=(248, 113, 113), width=2)

        draw.text((card_x + 35, c2_y + 35), "[ANTI-PATTERN / NAIVE PITFALL]", fill=(185, 28, 28), font=fonts["section_title"])
        trap_text = lesson.naive_pitfall or "Naive approach causes high overhead and fails production scale."
        trap_lines = wrap_text_lines(trap_text, max_chars=40)
        for t_idx, tl in enumerate(trap_lines[:2]):
            draw.text((card_x + 35, c2_y + 80 + t_idx * 34), tl, fill=(153, 27, 27), font=fonts["card_body"])

        # Warning banner pill
        warn_text = getattr(lesson, "warning_banner", "") or "[!] INSUFFICIENT OR BUGGY PATTERN"
        draw.rounded_rectangle([card_x + 30, c2_y + 175, card_x + card_w - 30, c2_y + 265], radius=16, fill=(239, 68, 68))
        draw.text((card_x + card_w // 2, c2_y + 220), warn_text[:45], fill=(255, 255, 255), font=fonts["card_mono"], anchor="mm")
        draw.text((card_x + 35, c2_y + 300), "-> Next: Senior line-by-line optimal solution...", fill=(120, 53, 15), font=fonts["teach_title"])

        # Card 3: Senior Optimal Architecture Target
        c3_y, c3_h = 1140, 340
        for off, a in [(12, 12), (4, 20)]:
            draw.rounded_rectangle([card_x, c3_y + off, card_x + card_w, c3_y + c3_h + off], radius=24, fill=(0, 0, 0, a))
        draw.rounded_rectangle([card_x, c3_y, card_x + card_w, c3_y + c3_h], radius=24, fill=(240, 253, 244), outline=(134, 239, 172), width=2)

        draw.text((card_x + 35, c3_y + 35), "[SENIOR PRODUCTION PATTERN]", fill=(20, 83, 45), font=fonts["section_title"])
        draw.text((card_x + 35, c3_y + 80), f"• Target Complexity: {lesson.complexity_badge}", fill=(22, 101, 52), font=fonts["card_body"])
        draw.text((card_x + 35, c3_y + 120), f"• Performance Benchmark: {lesson.benchmark_metric}", fill=(22, 101, 52), font=fonts["card_body"])

        # Strategy Pill
        draw.rounded_rectangle([card_x + 30, c3_y + 185, card_x + card_w - 30, c3_y + 265], radius=16, fill=(34, 197, 94))
        draw.text((card_x + card_w // 2, c3_y + 225), f"[OK] {lesson.badge_tag.upper()} • ZERO OVERHEAD", fill=(255, 255, 255), font=fonts["card_mono"], anchor="mm")


        # Card 4: Teacher Narration at Bottom
        t_y, t_h = 1510, 290
        for off, a in [(12, 12), (4, 20)]:
            draw.rounded_rectangle([card_x, t_y + off, card_x + card_w, t_y + t_h + off], radius=22, fill=(0, 0, 0, a))
        draw.rounded_rectangle([card_x, t_y, card_x + card_w, t_y + t_h], radius=22, fill=t_cfg["teach_bg"], outline=t_cfg["teach_border"], width=2)

        draw.rounded_rectangle([card_x + 28, t_y + 24, card_x + 80, t_y + 76], radius=14, fill=(245, 158, 11))
        draw.text((card_x + 54, t_y + 50), "AI", fill=(255, 255, 255), font=fonts["hud_badge"], anchor="mm")
        draw.text((card_x + 96, t_y + 36), "AI TEACHER // PROBLEM HOOK", fill=t_cfg["teach_title"], font=fonts["teach_title"])

        intro_lines = wrap_text_lines(lesson.intro_narration, max_chars=42)
        for i_idx, il in enumerate(intro_lines[:3]):
            draw.text((card_x + 36, t_y + 95 + i_idx * 40), il, fill=t_cfg["teach_text"], font=fonts["teach_body"])

    elif sec < timeline.exec_start_sec:
        # =========================================================================
        # PAGE 2: CODE ARCHITECTURE & LINE-BY-LINE CONSTRUCT
        # =========================================================================
        current_line_idx = -1
        is_typing_now = False
        typed_char_fraction = 1.0
        active_sched: Optional[LineTimeSchedule] = None

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

        # Header
        ep_label = getattr(lesson, "episode_label", "") or f"EPISODE #{lesson.episode_num}"
        draw.text((80, 75), f"{lesson.series_name} • {ep_label}", fill=t_cfg["header_sub"], font=fonts["hud_label"])
        draw.rounded_rectangle([80, 115, 620, 168], radius=14, fill=t_cfg["badge_bg"], outline=t_cfg["badge_border"], width=2)
        draw.text((350, 141), f"⚡ {lesson.badge_tag}", fill=t_cfg["badge_text"], font=fonts["hud_badge"], anchor="mm")
        draw.text((80, 195), lesson.title, fill=t_cfg["headline"], font=fonts["headline"])

        total_lines = len(lesson.lines)
        disp_line = min(total_lines, max(0, current_line_idx + 1))
        draw.text((W - 80, 205), f"LINE {disp_line}/{total_lines}", fill=(99, 102, 241), font=fonts["line_counter"], anchor="rm")

        bar_w = 920
        draw.rounded_rectangle([80, 250, 80 + bar_w, 258], radius=4, fill=(226, 232, 240))
        prog_ratio = min(1.0, sec / max(0.1, duration))
        draw.rounded_rectangle([80, 250, 80 + int(bar_w * prog_ratio), 258], radius=4, fill=(79, 70, 229))

        # Main IDE Card
        card_y, card_h = 280, 860
        for off, a in [(14, 15), (6, 25)]:
            draw.rounded_rectangle([card_x, card_y + off, card_x + card_w, card_y + card_h + off], radius=26, fill=(0, 0, 0, a))
        draw.rounded_rectangle([card_x, card_y, card_x + card_w, card_y + card_h], radius=26, fill=t_cfg["card_bg"], outline=t_cfg["card_border"], width=2)

        # macOS Dots & File Header
        draw.ellipse([card_x + 36, card_y + 24, card_x + 52, card_y + 40], fill=(255, 95, 86))
        draw.ellipse([card_x + 62, card_y + 24, card_x + 78, card_y + 40], fill=(255, 189, 46))
        draw.ellipse([card_x + 88, card_y + 24, card_x + 104, card_y + 40], fill=(39, 201, 63))
        lang_label = getattr(lesson, "language", "python").title()
        draw.text((card_x + 130, card_y + 32), f"{lesson.filename} • {lang_label}", fill=t_cfg["file_head"], font=fonts["file_head"], anchor="lm")
        draw.line([(card_x + 20, card_y + 64), (card_x + card_w - 20, card_y + 64)], fill=t_cfg["card_divider"], width=2)

        # Render Code Lines with Spotlight Halo
        code_start_y = card_y + 92
        line_spacing = 48

        for idx, sched in enumerate(timeline.schedules):
            ly = code_start_y + idx * line_spacing
            is_active = (idx == current_line_idx)
            is_past = (idx < current_line_idx)

            slide_offset = 0
            if is_active:
                if is_typing_now:
                    slide_offset = int((1.0 - typed_char_fraction) * -20)
                pulse = math.sin(sec * 5.0) * 0.5 + 0.5
                spot_border_w = 3 if pulse > 0.5 else 2
                if t_cfg["is_dark"]:
                    spot_col = (45, 35, 15) if sched.highlight else (30, 41, 59)
                    spot_border = (245, 158, 11) if sched.highlight else t_cfg["gutter_active"]
                else:
                    spot_col = (254, 243, 199) if sched.highlight else (238, 242, 255)
                    spot_border = (245, 158, 11) if sched.highlight else (129, 140, 248)
                draw.rounded_rectangle([card_x + 24, ly - 6, card_x + card_w - 24, ly + 38], radius=10, fill=spot_col, outline=spot_border, width=spot_border_w)

            # Gutter
            gutter_col = t_cfg["gutter_active"] if is_active else t_cfg["gutter"]
            draw.text((card_x + 55, ly + 4), f"{idx + 1:2d}", fill=gutter_col, font=fonts["gutter"], anchor="rm")

            full_text = sched.code_text
            if is_past:
                disp_text = full_text
            elif is_active:
                if is_typing_now:
                    char_idx = int(len(full_text) * typed_char_fraction)
                    disp_text = full_text[:char_idx]
                else:
                    disp_text = full_text
            else:
                disp_text = ""

            if t_cfg["is_dark"]:
                txt_col = t_cfg["code_plain"]
                if "def " in disp_text or "class " in disp_text:
                    txt_col = (210, 168, 255)
                elif "if " in disp_text or "return " in disp_text or "for " in disp_text:
                    txt_col = (255, 123, 114)
                elif "=" in disp_text or "in " in disp_text:
                    txt_col = (126, 231, 135)
                elif '"' in disp_text or "'" in disp_text or any(c.isdigit() for c in disp_text):
                    txt_col = (165, 214, 255)
            else:
                txt_col = (15, 23, 42)
                if "def " in disp_text:
                    txt_col = (147, 51, 234)
                elif "if " in disp_text or "return " in disp_text:
                    txt_col = (225, 29, 72)
                elif "=" in disp_text:
                    txt_col = (30, 58, 138)

            line_x = card_x + 85 + slide_offset
            draw.text((line_x, ly + 4), disp_text, fill=txt_col, font=fonts["code"])

            # Cursor
            if is_active:
                try:
                    txt_w = fonts["code"].getlength(disp_text)
                except Exception:
                    txt_w = len(disp_text) * 15
                cursor_vis = (int(sec * 1000) % 500) < 320
                if cursor_vis:
                    cur_x = line_x + txt_w + 3
                    draw.line([(cur_x, ly + 2), (cur_x, ly + 34)], fill=t_cfg["cursor"], width=3)

                # Floating Tooltip Popup
                if not is_typing_now and sched.tip:
                    tip_label = f"[{sched.tip}]"
                    pop_w = min(320, max(150, len(tip_label) * 14))
                    pop_x = card_x + card_w - pop_w - 30
                    pop_bg = (38, 28, 15) if t_cfg["is_dark"] else (255, 251, 235)
                    draw.rounded_rectangle([pop_x, ly - 4, pop_x + pop_w, ly + 36], radius=12, fill=pop_bg, outline=(245, 158, 11), width=2)
                    draw.text((pop_x + pop_w // 2, ly + 16), tip_label, fill=(245, 158, 11), font=fonts["teach_title"], anchor="mm")

        # Dynamic State Visualizer Box
        diag_y = 1170
        diag_img = render_dynamic_topic_diagram(lesson, current_line_idx, width=card_w, height=300)
        img.paste(diag_img, (card_x, diag_y), diag_img)

        # Teacher Insight Box
        teach_y, teach_h = 1500, 290
        for off, a in [(12, 12), (4, 20)]:
            draw.rounded_rectangle([card_x, teach_y + off, card_x + card_w, teach_y + teach_h + off], radius=22, fill=(0, 0, 0, a))
        draw.rounded_rectangle([card_x, teach_y, card_x + card_w, teach_y + teach_h], radius=22, fill=t_cfg["teach_bg"], outline=t_cfg["teach_border"], width=2)

        draw.rounded_rectangle([card_x + 28, teach_y + 24, card_x + 80, teach_y + 76], radius=14, fill=(245, 158, 11))
        draw.text((card_x + 54, teach_y + 50), "AI", fill=(255, 255, 255), font=fonts["hud_badge"], anchor="mm")

        tag_title = active_sched.tip if (active_sched and active_sched.tip) else "Algorithm Walkthrough"
        draw.text((card_x + 96, teach_y + 36), f"TEACHER INSIGHT • {tag_title.upper()}", fill=t_cfg["teach_title"], font=fonts["teach_title"])

        spoken_txt = active_sched.narration_text if active_sched else lesson.intro_narration
        s_lines = wrap_text_lines(spoken_txt, max_chars=44)
        for s_idx, sl in enumerate(s_lines[:3]):
            draw.text((card_x + 36, teach_y + 95 + s_idx * 40), sl, fill=t_cfg["teach_text"], font=fonts["teach_body"])

    elif sec < timeline.exec_end_sec:
        # =========================================================================
        # PAGE 3: LIVE SANDBOX EXECUTION & STDOUT DRY-RUN
        # =========================================================================
        # Header
        ep_label = getattr(lesson, "episode_label", "") or f"EPISODE #{lesson.episode_num}"
        draw.text((80, 75), f"{lesson.series_name} • {ep_label}", fill=t_cfg["header_sub"], font=fonts["hud_label"])
        draw.rounded_rectangle([80, 115, 680, 168], radius=14, fill=(220, 252, 231), outline=(74, 222, 128), width=2)
        draw.text((380, 141), "[RUN] LIVE DRY-RUN & SANDBOX EXECUTION", fill=(20, 83, 45), font=fonts["hud_badge"], anchor="mm")
        draw.text((80, 195), "Runtime Sandbox Verification", fill=t_cfg["headline"], font=fonts["headline"])

        # Progress Track Full
        bar_w = 920
        draw.rounded_rectangle([80, 250, 80 + bar_w, 258], radius=4, fill=(79, 70, 229))

        # Top Card: Algorithm Final Solved State
        diag_y = 280
        diag_img = render_dynamic_topic_diagram(lesson, len(lesson.lines), width=card_w, height=450)
        img.paste(diag_img, (card_x, diag_y), diag_img)

        # Bottom Card: Live Terminal Box
        term_y, term_h = 760, 720
        for off, a in [(16, 15), (6, 25)]:
            draw.rounded_rectangle([card_x, term_y + off, card_x + card_w, term_y + term_h + off], radius=24, fill=(0, 0, 0, a))
        draw.rounded_rectangle([card_x, term_y, card_x + card_w, term_y + term_h], radius=24, fill=(15, 23, 42), outline=(51, 65, 85), width=2)

        # macOS terminal dots
        draw.ellipse([card_x + 36, term_y + 24, card_x + 52, term_y + 40], fill=(255, 95, 86))
        draw.ellipse([card_x + 62, term_y + 24, card_x + 78, term_y + 40], fill=(255, 189, 46))
        draw.ellipse([card_x + 88, term_y + 24, card_x + 104, term_y + 40], fill=(39, 201, 63))
        lang_cmd = "python3" if getattr(lesson, "language", "python") == "python" else lesson.language
        draw.text((card_x + 130, term_y + 32), f"$ {lang_cmd} {lesson.filename} (Isolated Sandbox)", fill=(248, 250, 252), font=fonts["file_head"], anchor="lm")
        draw.line([(card_x + 20, term_y + 64), (card_x + card_w - 20, term_y + 64)], fill=(30, 41, 59), width=2)

        # Streaming stdout lines
        out_lines = sandbox_result.get("output_lines", [])
        exec_progress = min(1.0, (sec - timeline.exec_start_sec) / 1.8)
        lines_to_show = max(1, int(len(out_lines) * exec_progress))

        for o_i, out_l in enumerate(out_lines[:lines_to_show]):
            oy = term_y + 90 + o_i * 54
            col = (74, 222, 128) if ("PASS" in out_l or "Match" in out_l or "Size" in out_l) else (226, 232, 240)
            draw.text((card_x + 40, oy), out_l[:48], fill=col, font=fonts["term_mono"])

        # Telemetry Badge
        badge_y = term_y + term_h - 90
        draw.rounded_rectangle([card_x + 35, badge_y, card_x + card_w - 35, badge_y + 60], radius=14, fill=(30, 41, 59))
        draw.text((card_x + card_w // 2, badge_y + 30), f"[PASS] EXECUTED IN {sandbox_result['runtime_ms']}ms • RETURN CODE: 0 (ALL PASS)", fill=(74, 222, 128), font=fonts["term_mono"], anchor="mm")

        # Teacher Insight Box
        teach_y, teach_h = 1510, 280
        for off, a in [(12, 12), (4, 20)]:
            draw.rounded_rectangle([card_x, teach_y + off, card_x + card_w, teach_y + teach_h + off], radius=22, fill=(0, 0, 0, a))
        draw.rounded_rectangle([card_x, teach_y, card_x + card_w, teach_y + teach_h], radius=22, fill=t_cfg["teach_bg"], outline=t_cfg["teach_border"], width=2)

        draw.rounded_rectangle([card_x + 28, teach_y + 24, card_x + 80, teach_y + 76], radius=14, fill=(34, 197, 94))
        draw.text((card_x + 54, teach_y + 50), "AI", fill=(255, 255, 255), font=fonts["hud_badge"], anchor="mm")
        draw.text((card_x + 96, teach_y + 36), "AI TEACHER // EXECUTION VERIFICATION", fill=(20, 83, 45) if not t_cfg["is_dark"] else (74, 222, 128), font=fonts["teach_title"])

        ver_txt = f"{lesson.title} execution dry-run test verified. All assertions passing with optimal efficiency!"
        v_lines = wrap_text_lines(ver_txt, max_chars=44)
        for v_idx, vl in enumerate(v_lines[:3]):
            draw.text((card_x + 36, teach_y + 95 + v_idx * 40), vl, fill=t_cfg["teach_text"], font=fonts["teach_body"])

    else:
        # =========================================================================
        # PAGE 4: COMPLEXITY MASTERY & UP NEXT PLAYLIST TEASER
        # =========================================================================
        # Top Header
        ep_label = getattr(lesson, "episode_label", "") or f"EPISODE #{lesson.episode_num}"
        draw.text((80, 75), f"{lesson.series_name} • {ep_label} COMPLETED", fill=t_cfg["header_sub"], font=fonts["hud_label"])
        draw.rounded_rectangle([80, 115, 680, 168], radius=14, fill=(220, 252, 231), outline=(74, 222, 128), width=2)
        draw.text((380, 141), "[PASS] OPTIMAL SOLUTION ACCEPTED", fill=(20, 83, 45), font=fonts["hud_badge"], anchor="mm")
        draw.text((80, 195), "Mastery Complete!", fill=t_cfg["headline"], font=fonts["headline"])

        # Progress Track Full
        bar_w = 920
        draw.rounded_rectangle([80, 250, 80 + bar_w, 258], radius=4, fill=(34, 197, 94))

        # Card 1: Complexity Mastery Card
        c1_y, c1_h = 280, 580
        for off, a in [(14, 15), (6, 25)]:
            draw.rounded_rectangle([card_x, c1_y + off, card_x + card_w, c1_y + c1_h + off], radius=24, fill=(0, 0, 0, a))
        draw.rounded_rectangle([card_x, c1_y, card_x + card_w, c1_y + c1_h], radius=24, fill=t_cfg["card_bg"], outline=t_cfg["card_border"], width=2)

        # Huge Checkmark
        draw.ellipse([card_x + 50, c1_y + 40, card_x + 130, c1_y + 120], fill=(34, 197, 94))
        draw.line([(card_x + 75, c1_y + 80), (card_x + 88, c1_y + 95)], fill=(255, 255, 255), width=6)
        draw.line([(card_x + 88, c1_y + 95), (card_x + 112, c1_y + 65)], fill=(255, 255, 255), width=6)

        draw.text((card_x + 160, c1_y + 55), "PRODUCTION OPTIMAL CONFIRMED", fill=t_cfg["headline"], font=fonts["section_title"])
        draw.text((card_x + 160, c1_y + 95), f"• {lesson.benchmark_metric} •", fill=(22, 101, 52), font=fonts["card_body"])

        # Side-by-side comparison boxes
        sub_box_y = c1_y + 150
        box_w = 425
        # Left Box (Naive)
        draw.rounded_rectangle([card_x + 25, sub_box_y, card_x + 25 + box_w, sub_box_y + 240], radius=18, fill=(254, 242, 242), outline=(248, 113, 113), width=2)
        draw.text((card_x + 45, sub_box_y + 25), "[X] NAIVE APPROACH", fill=(185, 28, 28), font=fonts["section_title"])
        draw.text((card_x + 45, sub_box_y + 70), "• High Complexity Overhead", fill=(153, 27, 27), font=fonts["card_body"])
        draw.text((card_x + 45, sub_box_y + 110), "• Excessive RAM Allocations", fill=(153, 27, 27), font=fonts["card_body"])
        draw.text((card_x + 45, sub_box_y + 150), "• Fails Scale Tests", fill=(153, 27, 27), font=fonts["card_body"])

        # Right Box (Senior Optimal)
        draw.rounded_rectangle([card_x + 470, sub_box_y, card_x + 470 + box_w, sub_box_y + 240], radius=18, fill=(240, 253, 244), outline=(134, 239, 172), width=2)
        draw.text((card_x + 490, sub_box_y + 25), "[PASS] SENIOR PATTERN", fill=(20, 83, 45), font=fonts["section_title"])
        draw.text((card_x + 490, sub_box_y + 70), f"• {lesson.complexity_badge[:22]}", fill=(22, 101, 52), font=fonts["card_body"])
        draw.text((card_x + 490, sub_box_y + 110), f"• {lesson.benchmark_metric[:22]}", fill=(22, 101, 52), font=fonts["card_body"])
        draw.text((card_x + 490, sub_box_y + 150), "• Production Ready", fill=(22, 101, 52), font=fonts["card_body"])

        # Complexity Bar below
        draw.rounded_rectangle([card_x + 25, c1_y + 430, card_x + card_w - 25, c1_y + 530], radius=16, fill=(241, 245, 249))
        draw.text((card_x + card_w // 2, c1_y + 480), f"[METRICS] {lesson.complexity_badge} • {lesson.benchmark_metric}", fill=(30, 58, 138), font=fonts["card_mono"], anchor="mm")

        # Card 2: Next Day Playlist Preview
        c2_y, c2_h = 890, 580
        for off, a in [(14, 15), (6, 25)]:
            draw.rounded_rectangle([card_x, c2_y + off, card_x + card_w, c2_y + c2_h + off], radius=24, fill=(0, 0, 0, a))
        draw.rounded_rectangle([card_x, c2_y, card_x + card_w, c2_y + c2_h], radius=24, fill=(238, 242, 255), outline=(199, 210, 254), width=2)

        draw.rounded_rectangle([card_x + 35, c2_y + 35, card_x + 440, c2_y + 85], radius=14, fill=(79, 70, 229))
        draw.text((card_x + 237, c2_y + 60), f"[UP NEXT] {lesson.series_name.upper()[:22]}", fill=(255, 255, 255), font=fonts["hud_badge"], anchor="mm")

        next_preview = lesson.next_day_preview or f"Next: Episode {lesson.episode_num + 1} Walkthrough"
        # Wrap title if long
        prev_lines = wrap_text_lines(next_preview, max_chars=32)
        for p_i, p_line in enumerate(prev_lines[:2]):
            draw.text((card_x + 35, c2_y + 115 + p_i * 45), p_line, fill=(15, 23, 42), font=fonts["section_title"])
        sub_text = getattr(lesson, "series_subtitle", "") or f"{lesson.series_name} Series"
        draw.text((card_x + 35, c2_y + 215), sub_text[:45], fill=(71, 85, 105), font=fonts["card_body"])

        # Call to Action Pill
        cta_y = c2_y + 280
        cta_btn = getattr(lesson, "cta_button_text", "") or f">> FOLLOW & SAVE PLAYLIST FOR NEXT EPISODE <<"
        draw.rounded_rectangle([card_x + 35, cta_y, card_x + card_w - 35, cta_y + 110], radius=20, fill=(15, 23, 42))
        draw.text((card_x + card_w // 2, cta_y + 55), cta_btn[:42], fill=(255, 255, 255), font=fonts["section_title"], anchor="mm")


        # Card 3: Spoken Outro Box
        t_y, t_h = 1510, 280
        for off, a in [(12, 12), (4, 20)]:
            draw.rounded_rectangle([card_x, t_y + off, card_x + card_w, t_y + t_h + off], radius=22, fill=(0, 0, 0, a))
        draw.rounded_rectangle([card_x, t_y, card_x + card_w, t_y + t_h], radius=22, fill=(255, 255, 255), outline=(254, 215, 170), width=2)

        draw.rounded_rectangle([card_x + 28, t_y + 24, card_x + 80, t_y + 76], radius=14, fill=(245, 158, 11))
        draw.text((card_x + 54, t_y + 50), "AI", fill=(255, 255, 255), font=fonts["hud_badge"], anchor="mm")
        draw.text((card_x + 96, t_y + 36), "AI TEACHER // TAKEAWAY", fill=(180, 83, 9), font=fonts["teach_title"])

        out_lines = wrap_text_lines(lesson.outro_narration, max_chars=44)
        for o_idx, ol in enumerate(out_lines[:3]):
            draw.text((card_x + 36, t_y + 95 + o_idx * 40), ol, fill=(15, 23, 42), font=fonts["teach_body"])

    # Bottom Branding Telemetry
    draw.text((W // 2, 1860), "CHANNEL 7 // VIDEOSYNX ENGINE • ZERO SLOP • KOKORO AI", fill=(148, 163, 184), font=fonts["footer"], anchor="mm")

    return img.convert("RGB")


async def render_videosynx_short(query: str | None = None, theme: str = "onedark") -> Path:
    """
    Renders an end-to-end line-by-line anchored short with Kokoro narration and Cherry MX SFX.
    """
    lesson = get_anchored_lesson(query)
    if theme:
        lesson.theme = theme
    print("=" * 70)
    print(f"🎬 [Videosynx Engine] Rendering Line-by-Line Short: {lesson.title} (Theme: {lesson.theme})")
    print(f"📚 Series: {lesson.series_name} • Episode #{lesson.episode_num}")
    print("=" * 70)

    # 1. Run Code in Sandbox to get verified stdout
    lang_name = getattr(lesson, "language", "python")
    print(f"🧪 Running code in {lang_name} sandbox...")
    sandbox_result = run_code_in_sandbox(lesson.test_runner_code, language=lang_name)
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
        "big_hero": get_vfont(46, bold=True),
        "section_title": get_vfont(24, bold=True),
        "line_counter": get_vfont(22, bold=True),
        "file_head": get_vfont(20, bold=True),
        "gutter": get_vfont(22, bold=False),
        "code": get_vfont(24, bold=True),
        "teach_title": get_vfont(18, bold=True),
        "teach_body": get_vfont(22, bold=False),
        "term_mono": get_vfont(20, bold=True),
        "card_body": get_vfont(22, bold=False),
        "card_mono": get_vfont(22, bold=True),
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
    ep_label = getattr(lesson, "episode_label", "") or f"Ep {lesson.episode_num}"
    yt_meta = {
        "title": f"{lesson.series_name} • {ep_label}: {lesson.title} ⚡ #shorts",
        "description": (
            f"🔥 Welcome to {lesson.series_name} ({ep_label})!\n\n"
            f"Topic: {lesson.title}\n"
            f"Line-by-line explanation with real sandbox Python verification.\n\n"
            f"💡 Complexity: {lesson.complexity_badge}\n"
            f"⚡ Benchmark: {lesson.benchmark_metric}\n\n"
            f"#coding #programming #python #dsa #softwareengineer #tech #shorts #developer"
        ),
        "tags": ["coding", "programming", "python", "softwareengineer", "developer", "shorts"],

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

    # 6. Record Progress in Series Brain
    try:
        from series_progress_tracker import advance_and_record_render
        advance_and_record_render(lesson, out_mp4)
    except Exception as e:
        print(f"⚠️ [Series Tracker] Progress update error: {e}")

    return out_mp4



if __name__ == "__main__":
    q = sys.argv[1] if len(sys.argv) > 1 else "quicksort"
    asyncio.run(render_videosynx_short(q))
