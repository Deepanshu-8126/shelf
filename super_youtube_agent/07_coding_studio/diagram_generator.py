"""
Dynamic Educational Diagram & Visual Component Generator for Channel 7.
Procedurally renders topic-specific data structures:
- Array Partition / QuickSort recursion trees
- Hash Map key-value lookup tables (Two Sum)
- LIFO Stack visualizer (Valid Parentheses)
- Binary Search Pointer Halving
- Linked List Three-Pointer Reversal
- Greedy Buy/Sell Stock Curves
- Memory allocation byte bars (Generators)
"""
from __future__ import annotations
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
from typing import List, Tuple, Any


def get_diagram_font(size: int, bold: bool = True) -> ImageFont.FreeTypeFont:
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


def render_dynamic_topic_diagram(topic_or_lesson: Any, current_line_idx: int, width: int = 920, height: int = 270) -> Image.Image:
    """
    Renders an animated, state-aware visual box for the active coding topic.
    Supports dynamic diagram_rows, diagram_title, and diagram_caption directly from any lesson.
    """
    img = Image.new("RGBA", (width, height), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)

    f_title = get_diagram_font(20, bold=True)
    f_body = get_diagram_font(18, bold=False)
    f_val = get_diagram_font(22, bold=True)
    f_mono = get_diagram_font(17, bold=True)

    # Extract topic_id and dynamic attributes if lesson object passed
    if hasattr(topic_or_lesson, "id"):
        topic_id = getattr(topic_or_lesson, "id", "custom_topic")
        custom_title = getattr(topic_or_lesson, "diagram_title", "")
        custom_rows = getattr(topic_or_lesson, "diagram_rows", [])
        custom_caption = getattr(topic_or_lesson, "diagram_caption", "")
    else:
        topic_id = str(topic_or_lesson)
        custom_title = ""
        custom_rows = []
        custom_caption = ""

    t_lower = topic_id.lower()

    # Outer border card
    draw.rounded_rectangle([0, 0, width, height], radius=24, fill=(255, 255, 255), outline=(226, 232, 240), width=2)

    # 1. If lesson provides custom dynamic diagram rows, render them dynamically!
    if custom_rows:
        d_title = custom_title or "State Visualizer: Execution State Flow"
        draw.text((30, 18), d_title[:45], fill=(30, 58, 138), font=f_title)
        
        row_y = 56
        row_h = min(48, max(36, (height - 120) // max(1, len(custom_rows))))
        for r_i, row_str in enumerate(custom_rows[:4]):
            ry = row_y + r_i * (row_h + 8)
            is_active_row = (r_i == (current_line_idx % max(1, len(custom_rows))))
            bg = (238, 242, 255) if is_active_row else (248, 250, 252)
            outline_col = (129, 140, 248) if is_active_row else (226, 232, 240)
            text_col = (67, 56, 202) if is_active_row else (30, 41, 59)
            draw.rounded_rectangle([35, ry, width - 35, ry + row_h], radius=12, fill=bg, outline=outline_col, width=2)
            
            prefix = "▶ " if is_active_row else "• "
            draw.text((50, ry + row_h // 2), f"{prefix}{row_str}"[:48], fill=text_col, font=f_mono, anchor="lm")
        
        cap = custom_caption or "[✓] STATE SYNCHRONIZATION OPTIMAL"
        cap_y = height - 42
        draw.rounded_rectangle([35, cap_y - 6, width - 35, height - 12], radius=10, fill=(220, 252, 231), outline=(74, 222, 128), width=1)
        draw.text((width // 2, cap_y + 12), cap[:50], fill=(20, 83, 45), font=f_mono, anchor="mm")
        return img

    if "sort" in t_lower:

        # QuickSort Interactive Array & Partitioning Visualizer
        draw.text((30, 18), "State Visualizer: Partitioning & Recursion Tree", fill=(30, 58, 138), font=f_title)
        tiles = [38, 27, 43, 3, 9, 82, 10]
        tile_w = 90
        tile_h = 75
        start_x = 45
        tile_y = 55

        for idx, val in enumerate(tiles):
            tx = start_x + idx * (tile_w + 18)
            is_pivot = (idx == 3)
            
            if current_line_idx <= 2:
                bg = (254, 243, 199) if is_pivot else (248, 250, 252)
                border = (245, 158, 11) if is_pivot else (203, 213, 225)
                val_col = (180, 83, 9) if is_pivot else (15, 23, 42)
            elif current_line_idx in (3, 4, 5):
                is_left = (val < 9)
                bg = (239, 246, 255) if is_left else (250, 245, 255)
                border = (147, 197, 253) if is_left else (216, 180, 254)
                val_col = (29, 78, 216) if is_left else (126, 34, 206)
            else:
                bg = (220, 252, 231)
                border = (74, 222, 128)
                val_col = (20, 83, 45)

            draw.rounded_rectangle([tx, tile_y, tx + tile_w, tile_y + tile_h], radius=14, fill=bg, outline=border, width=2)
            draw.text((tx + tile_w // 2, tile_y + tile_h // 2), str(val), fill=val_col, font=f_val, anchor="mm")
            draw.text((tx + tile_w // 2, tile_y + tile_h + 16), f"[{idx}]", fill=(148, 163, 184), font=get_diagram_font(14, bold=True), anchor="mm")

        sub_y = 158
        draw.rounded_rectangle([45, sub_y, 420, sub_y + 95], radius=16, fill=(239, 246, 255), outline=(147, 197, 253), width=2)
        draw.text((65, sub_y + 14), "LEFT (< PIVOT 9)", fill=(29, 78, 216), font=f_mono)
        draw.text((65, sub_y + 45), "[3] (Base Case Reach)", fill=(30, 58, 138), font=f_val)

        draw.rounded_rectangle([450, sub_y, width - 45, sub_y + 95], radius=16, fill=(250, 245, 255), outline=(216, 180, 254), width=2)
        draw.text((470, sub_y + 14), "RIGHT (> PIVOT 9)", fill=(126, 34, 206), font=f_mono)
        draw.text((470, sub_y + 45), "[38, 27, 43, 82, 10]", fill=(107, 33, 168), font=f_val)

    elif "two_sum" in t_lower or "hash" in t_lower:
        # Two Sum Hash Map
        draw.text((30, 18), "State Visualizer: Hash Table Complement Lookup", fill=(30, 58, 138), font=f_title)
        draw.rounded_rectangle([40, 55, width - 40, 155], radius=16, fill=(241, 245, 249))
        draw.text((60, 75), "Hash Dictionary: seen = { 2: 0, 7: 1, 11: 2, 15: 3 }", fill=(15, 23, 42), font=f_mono)
        draw.text((60, 110), "Complement Formula: needed = 9 - num  -> Direct O(1) Memory Index Match", fill=(51, 65, 85), font=f_body)

        draw.rounded_rectangle([40, 175, width - 40, height - 20], radius=14, fill=(220, 252, 231), outline=(74, 222, 128), width=2)
        draw.text((width // 2, 210), "[METRIC] TIME COMPLEXITY: O(n) • ZERO QUADRATIC OVERHEAD", fill=(20, 83, 45), font=f_mono, anchor="mm")

    elif "paren" in t_lower or "stack" in t_lower:
        # Valid Parentheses Stack
        draw.text((30, 18), "State Visualizer: LIFO Stack Frame Trace", fill=(30, 58, 138), font=f_title)
        
        # Stack blocks
        items = ["(", "{", "["] if current_line_idx <= 4 else []
        box_x = 50
        draw.text((50, 55), "LIFO STACK MEMORY:", fill=(100, 116, 139), font=f_mono)
        for i, it in enumerate(items):
            draw.rounded_rectangle([box_x + i * 85, 90, box_x + i * 85 + 70, 150], radius=12, fill=(238, 242, 255), outline=(129, 140, 248), width=2)
            draw.text((box_x + i * 85 + 35, 120), it, fill=(67, 56, 202), font=f_val, anchor="mm")

        draw.rounded_rectangle([40, 175, width - 40, height - 20], radius=14, fill=(220, 252, 231), outline=(74, 222, 128), width=2)
        draw.text((width // 2, 210), "[✓] STACK EMPTY (return not stack) -> VALID STRING CONFIRMED", fill=(20, 83, 45), font=f_mono, anchor="mm")

    elif "binary" in t_lower:
        # Binary Search Halving Pointers
        draw.text((30, 18), "State Visualizer: Search Space Halving [O(log n)]", fill=(30, 58, 138), font=f_title)
        arr = [-1, 0, 3, 5, 9, 12]
        tile_w = 110
        for i, val in enumerate(arr):
            ax = 50 + i * (tile_w + 20)
            is_mid = (val == 9)
            bg = (220, 252, 231) if is_mid else (248, 250, 252)
            bor = (74, 222, 128) if is_mid else (203, 213, 225)
            draw.rounded_rectangle([ax, 60, ax + tile_w, 135], radius=14, fill=bg, outline=bor, width=2)
            draw.text((ax + tile_w // 2, 97), str(val), fill=(20, 83, 45) if is_mid else (15, 23, 42), font=f_val, anchor="mm")
            if is_mid:
                draw.text((ax + tile_w // 2, 152), "TARGET (MID)", fill=(22, 101, 52), font=get_diagram_font(13, bold=True), anchor="mm")

        draw.rounded_rectangle([40, 180, width - 40, height - 20], radius=14, fill=(241, 245, 249))
        draw.text((width // 2, 215), "[LOGARITHMIC] SEARCH SPACE HALVED: 10M ITEMS FOUND IN ONLY 24 STEPS", fill=(30, 41, 59), font=f_mono, anchor="mm")

    elif "reverse" in t_lower or "linked" in t_lower:
        # Reverse Linked List Pointers
        draw.text((30, 18), "State Visualizer: In-Place 3-Pointer Traversal", fill=(30, 58, 138), font=f_title)
        draw.rounded_rectangle([40, 60, width - 40, 150], radius=16, fill=(241, 245, 249))
        draw.text((60, 80), "Pointers: [prev] <--- [curr] ---> [nxt]", fill=(15, 23, 42), font=f_mono)
        draw.text((60, 115), "Operation: curr.next = prev (Links flipped in O(1) auxiliary space)", fill=(51, 65, 85), font=f_body)

        draw.rounded_rectangle([40, 175, width - 40, height - 20], radius=14, fill=(220, 252, 231), outline=(74, 222, 128), width=2)
        draw.text((width // 2, 210), "[✓] IN-PLACE HEAD FLIP ACHIEVED • O(1) MEMORY", fill=(20, 83, 45), font=f_mono, anchor="mm")

    elif "stock" in t_lower:
        # Buy/Sell Stock
        draw.text((30, 18), "State Visualizer: Single-Pass Min Tracking", fill=(30, 58, 138), font=f_title)
        draw.rounded_rectangle([40, 60, width - 40, 150], radius=16, fill=(241, 245, 249))
        draw.text((60, 80), "Stock Days: [7, 1, 5, 3, 6, 4]  -> Buy at 1, Sell at 6", fill=(15, 23, 42), font=f_mono)
        draw.text((60, 115), "Greedy Logic: max_p = max(max_p, price - min_price)", fill=(51, 65, 85), font=f_body)

        draw.rounded_rectangle([40, 175, width - 40, height - 20], radius=14, fill=(220, 252, 231), outline=(74, 222, 128), width=2)
        draw.text((width // 2, 210), "[✓] MAX PROFIT: +5 • EXECUTED IN A SINGLE O(n) PASS", fill=(20, 83, 45), font=f_mono, anchor="mm")

    elif "gen" in t_lower or "memory" in t_lower:
        # Memory Bar Gauge
        draw.text((30, 18), "State Visualizer: Memory Footprint Comparison", fill=(30, 58, 138), font=f_title)
        draw.rounded_rectangle([40, 60, width - 40, 110], radius=14, fill=(254, 226, 226), outline=(248, 113, 113), width=2)
        draw.text((60, 85), "List Comprehension: 80,000,000 Bytes (RAM Spike [!])", fill=(185, 28, 28), font=f_mono)

        draw.rounded_rectangle([40, 125, width - 40, 175], radius=14, fill=(220, 252, 231), outline=(74, 222, 128), width=2)
        draw.text((60, 150), "Generator Expression: 112 Bytes (99.9% Memory Saved [✓])", fill=(20, 83, 45), font=f_mono)

        draw.rounded_rectangle([40, 190, width - 40, height - 15], radius=12, fill=(241, 245, 249))
        draw.text((width // 2, 225), "[✓] O(1) CONSTANT BUFFER ALLOCATION VERIFIED", fill=(30, 41, 59), font=f_mono, anchor="mm")
    else:
        # Universal Dynamic Architecture & State Inspector Card
        title_str = custom_title or f"State Visualizer: {topic_id.replace('_', ' ').title()}"
        draw.text((30, 18), title_str[:45], fill=(30, 58, 138), font=f_title)
        
        draw.rounded_rectangle([40, 60, width - 40, 140], radius=14, fill=(241, 245, 249), outline=(203, 213, 225), width=2)
        draw.text((60, 80), f"Active Execution Phase: Step {current_line_idx + 1}", fill=(15, 23, 42), font=f_mono)
        draw.text((60, 108), "State Mutation: Clean in-memory scope verified", fill=(51, 65, 85), font=f_body)

        draw.rounded_rectangle([40, 160, width - 40, height - 20], radius=14, fill=(220, 252, 231), outline=(74, 222, 128), width=2)
        draw.text((width // 2, 195), "[✓] ZERO RUNTIME REGRESSIONS • PRODUCTION ARCHITECTURE", fill=(20, 83, 45), font=f_mono, anchor="mm")

    return img

