"""Cinematic Color Grading & Audio Engineering Chains for Video-Use.

Includes:
- 6 Cinematic visual grading profiles (curves, saturation, contrast, warmth)
- Pop-free 30ms audio micro-fades on cut boundaries to eliminate clicks
- 9:16 vertical smart crop / framing
"""
from __future__ import annotations

# FFmpeg filter chains for each visual aesthetic
COLOR_GRADE_PROFILES: dict[str, str] = {
    "cinematic": (
        "eq=contrast=1.12:brightness=-0.02:saturation=1.20,"
        "colorbalance=rs=0.04:gs=-0.02:bs=-0.05:rm=0.03:gm=0.0:bm=-0.04"  # Subtle teal-orange warmth
    ),
    "warm_punch": (
        "eq=contrast=1.18:brightness=0.01:saturation=1.25,"
        "colorbalance=rs=0.06:gs=0.02:bs=-0.04"
    ),
    "dark_moody": (
        "eq=contrast=1.22:brightness=-0.06:saturation=1.05,"
        "curves=preset=darker"
    ),
    "cyberpunk": (
        "eq=contrast=1.25:brightness=-0.03:saturation=1.35,"
        "colorbalance=rs=0.08:gs=-0.05:bs=0.12"
    ),
    "clean_natural": (
        "eq=contrast=1.05:brightness=0.0:saturation=1.08"
    ),
}


def build_audio_fade_filter(duration: float, fade_sec: float = 0.03) -> str:
    """Creates a 30ms micro-fade in & out to eliminate audio pops and clicks."""
    fade_out_start = max(0.0, duration - fade_sec)
    return f"afade=t=in:ss=0:d={fade_sec:.3f},afade=t=out:st={fade_out_start:.3f}:d={fade_sec:.3f}"


def build_vertical_crop_filter(aspect_ratio: str = "9:16") -> str:
    """Crops landscape 16:9 into centered vertical 9:16 Shorts format (1080x1920)."""
    if aspect_ratio == "9:16":
        return "crop=ih*(9/16):ih,scale=1080:1920"
    return "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2"


def get_combined_video_filter(profile: str = "cinematic", make_vertical: bool = True) -> str:
    """Combines color grade and framing into a single FFmpeg -vf chain."""
    filters = []
    if make_vertical:
        filters.append(build_vertical_crop_filter("9:16"))

    grade = COLOR_GRADE_PROFILES.get(profile, COLOR_GRADE_PROFILES["cinematic"])
    filters.append(grade)
    return ",".join(filters)
