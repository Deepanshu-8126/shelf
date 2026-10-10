"""
Visual Pop-Ups Engine - Keyword-Triggered Transparent PNG Overlays.
Extracts high-impact nouns from Whisper word timestamps and overlays
transparent PNG cutout stickers with smooth bounce-in animation.
AUTO-GENERATES procedural stickers if files missing (no manual download needed).
"""
import os
import json
import random
from pathlib import Path
from typing import List, Dict, Optional, Any
from moviepy import ImageClip, VideoFileClip, CompositeVideoClip
from moviepy.video.fx import Resize, FadeOut
from PIL import Image, ImageDraw, ImageFont
import io

STICKERS_DIR = Path(__file__).resolve().parent.parent / "assets" / "visual_stickers"
STICKERS_DIR.mkdir(parents=True, exist_ok=True)

# Keyword to sticker mapping (transparent PNG cutouts)
KEYWORD_STICKER_MAP = {
    "laptop": "laptop.png",
    "computer": "laptop.png",
    "phone": "phone.png",
    "mobile": "phone.png",
    "camera": "camera.png",
    "photo": "camera.png",
    "picture": "camera.png",
    "money": "money.png",
    "cash": "money.png",
    "dollar": "money.png",
    "dollars": "money.png",
    "thousand": "money.png",
    "thousands": "money.png",
    "pay": "money.png",
    "paid": "money.png",
    "salary": "money.png",
    "wage": "money.png",
    "boss": "boss.png",
    "manager": "boss.png",
    "supervisor": "boss.png",
    "police": "police.png",
    "cop": "police.png",
    "officer": "police.png",
    "eviction": "eviction.png",
    "evicted": "eviction.png",
    "evict": "eviction.png",
    "court": "eviction.png",
    "lawyer": "eviction.png",
    "notice": "eviction.png",
}

# High-emotion drama keywords for color highlighting (also used for SFX mapping)
DRAMA_KEYWORDS = {
    "fired", "cheating", "evicted", "thousands", "stole", "screaming",
    "betrayed", "humiliated", "destroyed", "ruined", "exposed", "caught",
    "revenge", "karma", "justice", "lawsuit", "arrested", "jail",
    "divorce", "affair", "cheated", "stolen", "fraud", "scam"
}

STICKER_SIZE = (350, 350)
STICKER_POSITION = ('center', 320)  # upper-third quadrant, well above subtitles
STICKER_DURATION = 1.6
BOUNCE_DURATION = 0.15


def find_sticker_path(keyword: str) -> Optional[Path]:
    """Find the sticker file for a given keyword. Auto-generates procedural PNG if missing."""
    filename = KEYWORD_STICKER_MAP.get(keyword.lower())
    if not filename:
        return None
    path = (STICKERS_DIR / filename).resolve()
    if path.exists():
        return path

    # Auto-generate procedural sticker if missing
    res = generate_procedural_sticker(keyword.lower(), filename)
    return res.resolve() if res else None


def generate_procedural_sticker(keyword: str, filename: str) -> Path:
    """Generate a clean procedural PNG sticker on-the-fly."""
    from PIL import Image, ImageDraw, ImageFont

    path = STICKERS_DIR / filename

    # Create transparent canvas
    img = Image.new('RGBA', STICKER_SIZE, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Color scheme per category
    colors = {
        "laptop": ("#3B82F6", "#1E40AF"),      # Blue
        "computer": ("#3B82F6", "#1E40AF"),
        "phone": ("#10B981", "#059669"),        # Emerald
        "mobile": ("#10B981", "#059669"),
        "camera": ("#8B5CF6", "#7C3AED"),       # Violet
        "photo": ("#8B5CF6", "#7C3AED"),
        "picture": ("#8B5CF6", "#7C3AED"),
        "money": ("#F59E0B", "#D97706"),        # Amber
        "cash": ("#F59E0B", "#D97706"),
        "dollar": ("#F59E0B", "#D97706"),
        "dollars": ("#F59E0B", "#D97706"),
        "thousand": ("#F59E0B", "#D97706"),
        "thousands": ("#F59E0B", "#D97706"),
        "pay": ("#F59E0B", "#D97706"),
        "paid": ("#F59E0B", "#D97706"),
        "salary": ("#F59E0B", "#D97706"),
        "wage": ("#F59E0B", "#D97706"),
        "boss": ("#EF4444", "#DC2626"),         # Red
        "manager": ("#EF4444", "#DC2626"),
        "supervisor": ("#EF4444", "#DC2626"),
        "police": ("#1E3A8A", "#1E40AF"),       # Dark Blue
        "cop": ("#1E3A8A", "#1E40AF"),
        "officer": ("#1E3A8A", "#1E40AF"),
        "eviction": ("#DC2626", "#991B1B"),     # Deep Red
        "evicted": ("#DC2626", "#991B1B"),
        "evict": ("#DC2626", "#991B1B"),
        "court": ("#DC2626", "#991B1B"),
        "lawyer": ("#DC2626", "#991B1B"),
        "notice": ("#DC2626", "#991B1B"),
    }

    primary, secondary = colors.get(keyword, ("#6366F1", "#4F46E5"))  # Default indigo

    # Draw shape based on keyword category
    center = (STICKER_SIZE[0] // 2, STICKER_SIZE[1] // 2)
    radius = 140

    # Main circle background with gradient effect (simulated with two circles)
    draw.ellipse(
        [center[0] - radius, center[1] - radius, center[0] + radius, center[1] + radius],
        fill=primary + "CC",  # 80% opacity
        outline=secondary,
        width=4
    )

    # Inner highlight circle
    draw.ellipse(
        [center[0] - radius + 10, center[1] - radius + 10, center[0] + radius - 10, center[1] + radius - 10],
        outline=primary + "88",
        width=2
    )

    # Draw icon symbol based on keyword
    icon_color = "white"
    icon_size = 60

    if keyword in ["laptop", "computer"]:
        # Laptop outline
        x, y = center[0] - 50, center[1] - 35
        draw.rounded_rectangle([x, y, x + 100, y + 70], radius=8, outline=icon_color, width=5)
        # Screen
        draw.rectangle([x + 10, y + 10, x + 90, y + 50], outline=icon_color, width=3)
        # Base
        draw.rectangle([x + 20, y + 70, x + 80, y + 80], fill=icon_color)

    elif keyword in ["phone", "mobile"]:
        # Phone outline
        x, y = center[0] - 35, center[1] - 60
        draw.rounded_rectangle([x, y, x + 70, y + 120], radius=15, outline=icon_color, width=5)
        # Screen
        draw.rectangle([x + 8, y + 15, x + 62, y + 105], outline=icon_color, width=3)
        # Home indicator
        draw.line([center[0] - 15, y + 110, center[0] + 15, y + 110], fill=icon_color, width=4)

    elif keyword in ["camera", "photo", "picture"]:
        # Camera body
        x, y = center[0] - 50, center[1] - 35
        draw.rounded_rectangle([x, y, x + 100, y + 70], radius=10, outline=icon_color, width=5)
        # Lens
        draw.ellipse([center[0] - 25, center[1] - 25, center[0] + 25, center[1] + 25], outline=icon_color, width=5)
        draw.ellipse([center[0] - 15, center[1] - 15, center[0] + 15, center[1] + 15], outline=icon_color, width=3)
        # Flash
        draw.rectangle([x + 80, y + 10, x + 90, y + 25], fill=icon_color)

    elif keyword in ["money", "cash", "dollar", "dollars", "thousand", "thousands", "pay", "paid", "salary", "wage"]:
        # Dollar sign
        draw.text((center[0], center[1] - 10), "$", font_size=100, fill=icon_color, anchor="mm", stroke_width=3, stroke_fill=secondary)
        # Money bag hint
        draw.ellipse([center[0] - 40, center[1] + 30, center[0] + 40, center[1] + 110], outline=icon_color, width=3)
        draw.line([center[0], center[1] + 30, center[0], center[1] - 10], fill=icon_color, width=3)

    elif keyword in ["boss", "manager", "supervisor"]:
        # Person silhouette with tie
        # Head
        draw.ellipse([center[0] - 25, center[1] - 60, center[0] + 25, center[1] - 10], outline=icon_color, width=4)
        # Body
        draw.rectangle([center[0] - 35, center[1] - 10, center[0] + 35, center[1] + 50], outline=icon_color, width=4)
        # Tie
        draw.polygon([
            (center[0], center[1] - 5),
            (center[0] - 12, center[1] + 25),
            (center[0] + 12, center[1] + 25)
        ], fill=secondary)
        # Arms
        draw.line([center[0] - 35, center[1] + 10, center[0] - 55, center[1] + 30], fill=icon_color, width=4)
        draw.line([center[0] + 35, center[1] + 10, center[0] + 55, center[1] + 30], fill=icon_color, width=4)

    elif keyword in ["police", "cop", "officer"]:
        # Badge
        draw.ellipse([center[0] - 45, center[1] - 45, center[0] + 45, center[1] + 45], outline=icon_color, width=5)
        draw.ellipse([center[0] - 30, center[1] - 30, center[0] + 30, center[1] + 30], outline=icon_color, width=3)
        # Star in center
        star_points = []
        for i in range(5):
            angle = i * 2 * 3.14159 / 5 - 3.14159 / 2
            r = 20 if i % 2 == 0 else 10
            star_points.append((center[0] + r * __import__('math').cos(angle), center[1] + r * __import__('math').sin(angle)))
        draw.polygon(star_points, fill=icon_color)

    elif keyword in ["eviction", "evicted", "evict", "court", "lawyer", "notice"]:
        # Document with "!" or "X"
        x, y = center[0] - 40, center[1] - 50
        draw.rounded_rectangle([x, y, x + 80, y + 100], radius=5, outline=icon_color, width=5)
        # Exclamation mark
        draw.text((center[0], center[1] + 5), "!", font_size=80, fill=icon_color, anchor="mm", stroke_width=3, stroke_fill=secondary)
        # Clip at top
        draw.rectangle([center[0] - 15, y - 5, center[0] + 15, y + 5], fill=secondary)

    # Save
    img.save(path, "PNG")
    print(f"   AUTO-GENERATED: {filename} for keyword '{keyword}'")
    return path


def extract_visual_keywords(whisper_words: List[Dict], max_popups: int = 4) -> List[Dict]:
    """
    Extract high-impact visual nouns from Whisper word timestamps.
    Returns list of {keyword, timestamp, sticker_path, sfx_type} dicts.
    """
    candidates = []

    for word_data in whisper_words:
        word = word_data.get("word", "").lower().strip()
        start = word_data.get("start", 0)

        # Check if word maps to a visual sticker
        if word in KEYWORD_STICKER_MAP:
            sticker_path = find_sticker_path(word)
            if sticker_path:
                # Determine SFX type based on keyword category
                sfx_type = "whoosh"  # default
                if word in ["money", "cash", "dollar", "dollars", "thousand", "thousands", "pay", "paid", "salary", "wage"]:
                    sfx_type = "cash"
                elif word in ["camera", "photo", "picture"]:
                    sfx_type = "click"
                elif word in ["eviction", "evicted", "evict", "court", "lawyer", "notice"]:
                    sfx_type = "boom"
                elif word in ["boss", "manager", "supervisor"]:
                    sfx_type = "boom"
                elif word in ["police", "cop", "officer"]:
                    sfx_type = "boom"

                candidates.append({
                    "keyword": word,
                    "timestamp": start,
                    "sticker_path": str(sticker_path),
                    "sfx_type": sfx_type
                })

    # Sort by timestamp and pick top N spread across the video
    candidates.sort(key=lambda x: x["timestamp"])

    # Spread selection to avoid clustering
    if len(candidates) <= max_popups:
        return candidates

    # Pick evenly distributed across timeline
    selected = []
    step = len(candidates) / max_popups
    for i in range(max_popups):
        idx = min(int(i * step + step / 2), len(candidates) - 1)
        selected.append(candidates[idx])

    return selected


def create_sticker_clip(sticker_path: str, start_time: float, duration: float = STICKER_DURATION) -> ImageClip:
    """
    Create an animated sticker clip with bounce-in effect.
    Entry: scale 0.7 -> 1.0 over 0.15s with drop shadow
    """
    img = ImageClip(str(Path(sticker_path).resolve()), duration=duration)

    # Resize to target size (MoviePy v2: positional or new_size)
    img = img.with_effects([Resize(STICKER_SIZE), FadeOut(0.3)])

    # Position at upper-third quadrant
    def position_func(t):
        if t < BOUNCE_DURATION:
            progress = t / BOUNCE_DURATION
            scale = 0.7 + 0.3 * (1 - (1 - progress) ** 3)
            if progress > 0.8:
                scale = 1.0 + 0.05 * (progress - 0.8) / 0.2
        else:
            scale = 1.0

        w, h = STICKER_SIZE
        x = (1080 - w * scale) / 2
        y = STICKER_POSITION[1] - (h * (scale - 1)) / 2
        return (x, y)

    img = img.with_position(position_func, relative=False)
    img = img.with_start(start_time)
    return img


def create_popup_composite(base_video: VideoFileClip, popups: List[Dict]) -> CompositeVideoClip:
    """Composite all popup stickers onto the base video."""
    clips = [base_video]

    for popup in popups:
        try:
            sticker_clip = create_sticker_clip(
                popup["sticker_path"],
                popup["timestamp"],
                STICKER_DURATION
            )
            clips.append(sticker_clip)
        except Exception as e:
            print(f"⚠️ Skipping popup {popup.get('keyword')}: {e}", flush=True)

    return CompositeVideoClip(clips, size=base_video.size)


def is_drama_keyword(word: str) -> bool:
    """Check if a word is a high-emotion drama keyword."""
    return word.lower().strip() in DRAMA_KEYWORDS


def get_drama_color(word: str) -> str:
    """Get the highlight color for a drama keyword."""
    word_lower = word.lower().strip()
    # Neon Yellow for money/value words, Neon Green for action/conflict words
    if word_lower in ["thousands", "money", "cash", "dollar", "dollars", "salary", "wage", "pay", "paid"]:
        return "#FFE600"  # Neon Yellow
    return "#00FF66"  # Neon Green