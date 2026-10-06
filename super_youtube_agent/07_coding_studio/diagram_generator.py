"""
Dynamic Educational Diagram & Visual Component Generator for Channel 7.
Procedurally renders topic-specific data structures:
- Array Partition / QuickSort recursion trees
- Hash Map key-value lookup tables (Two Sum)
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


def render_dynamic_topic_diagram(topic_id: str, current_line_idx: int, width: int = 900, height: int = 340) -> Image.Image:
    """
    Renders an animated, state-aware visual box for the active coding topic.
    """
    img = Image.new("RGBA", (width, height), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)

    f_title = get_diagram_font(20, bold=True)
    f_body = get_diagram_font(18, bold=False)
    f_val = get_diagram_font(22, bold=True)
    f_mono = get_diagram_font(17, bold=True)

    if "quicksort" in topic_id.lower() or "sort" in topic_id.lower():
        # QuickSort Interactive Array & Partitioning Visualizer
        draw.rounded_rectangle([0, 0, width, height], radius=24, fill=(255, 255, 255), outline=(226, 232, 240), width=2)
        draw.text((30, 22), "📊 Dynamic State: Partitioning & Recursion Tree", fill=(30, 58, 138), font=f_title)

        # Unsorted / Intermediate State
        tiles = [38, 27, 43, 3, 9, 82, 10]
        tile_w = 90
        tile_h = 75
        start_x = 45
        tile_y = 65

        for idx, val in enumerate(tiles):
            tx = start_x + idx * (tile_w + 18)
            is_pivot = (idx == 3)  # Pivot element 3 or 9
            
            # Highlight state based on current line index
            if current_line_idx <= 2:
                bg = (254, 243, 199) if is_pivot else (248, 250, 252)
                border = (245, 158, 11) if is_pivot else (203, 213, 225)
                val_col = (180, 83, 9) if is_pivot else (15, 23, 42)
            elif current_line_idx in (3, 4):
                # Partitioning phase
                is_left = (val < 9)
                bg = (239, 246, 255) if is_left else (250, 245, 255)
                border = (147, 197, 253) if is_left else (216, 180, 254)
                val_col = (29, 78, 216) if is_left else (126, 34, 206)
            else:
                # Sorted pass
                bg = (220, 252, 231)
                border = (74, 222, 128)
                val_col = (20, 83, 45)

            draw.rounded_rectangle([tx, tile_y, tx + tile_w, tile_y + tile_h], radius=14, fill=bg, outline=border, width=2)
            draw.text((tx + tile_w // 2, tile_y + tile_h // 2), str(val), fill=val_col, font=f_val, anchor="mm")
            draw.text((tx + tile_w // 2, tile_y + tile_h + 16), f"[{idx}]", fill=(148, 163, 184), font=get_diagram_font(14, bold=True), anchor="mm")

        # Partition Sub-arrays below
        sub_y = 190
        draw.rounded_rectangle([45, sub_y, 400, sub_y + 115], radius=16, fill=(239, 246, 255), outline=(147, 197, 253), width=2)
        draw.text((65, sub_y + 18), "LEFT SUBARRAY (< PIVOT 9)", fill=(29, 78, 216), font=f_mono)
        draw.text((65, sub_y + 55), "Elements: [3]", fill=(30, 58, 138), font=f_val)
        draw.text((65, sub_y + 85), "Status: Base case reached (sorted)", fill=(100, 116, 139), font=get_diagram_font(13))

        draw.rounded_rectangle([450, sub_y, width - 45, sub_y + 115], radius=16, fill=(250, 245, 255), outline=(216, 180, 254), width=2)
        draw.text((470, sub_y + 18), "RIGHT SUBARRAY (> PIVOT 9)", fill=(126, 34, 206), font=f_mono)
        draw.text((470, sub_y + 55), "Elements: [38, 27, 43, 82, 10]", fill=(107, 33, 168), font=f_val)
        draw.text((470, sub_y + 85), "Status: Recursive QuickSort call", fill=(100, 116, 139), font=get_diagram_font(13))

    else:
        # Generic / Hash Map Visualizer
        draw.rounded_rectangle([0, 0, width, height], radius=24, fill=(255, 255, 255), outline=(226, 232, 240), width=2)
        draw.text((30, 22), "📊 Hash Table State (O(1) Direct Lookup)", fill=(30, 58, 138), font=f_title)

        draw.rounded_rectangle([40, 65, width - 40, 175], radius=16, fill=(241, 245, 249))
        draw.text((60, 85), "Dictionary Storage: seen = { num : index }", fill=(15, 23, 42), font=f_mono)
        draw.text((60, 120), "• Instant key check via hash code: 'needed in seen' in O(1) time", fill=(51, 65, 85), font=f_body)

        draw.rounded_rectangle([40, 200, width - 40, height - 25], radius=16, fill=(220, 252, 231), outline=(74, 222, 128), width=2)
        draw.text((width // 2, 235), "⚡ ZERO QUADRATIC OVERHEAD • CONSTANT LOOKUP SPEED", fill=(20, 83, 45), font=f_mono, anchor="mm")

    return img
