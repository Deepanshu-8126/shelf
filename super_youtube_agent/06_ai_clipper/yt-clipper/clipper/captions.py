"""Step 5 - kinetic word-by-word captions as an .ass subtitle file.

ASS beats drawtext: one file, ffmpeg burns it in a single pass, and \\k karaoke
tags give per-word highlight without generating hundreds of filter nodes.
"""
from __future__ import annotations

from pathlib import Path

from .config import settings

HEADER = """[Script Info]
ScriptType: v4.00+
PlayResX: {w}
PlayResY: {h}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Pop,{font},{size},&H00FFFFFF,&H0000E5FF,&H00101010,&H90000000,-1,0,0,0,100,100,0,0,1,{outline},2,2,80,80,{mv},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def _ts(t: float) -> str:
    t = max(t, 0)
    h, r = divmod(t, 3600)
    m, s = divmod(r, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def chunk_words(words: list[dict], max_words: int = 4, max_gap: float = 0.7) -> list[list[dict]]:
    groups, cur = [], []
    for w in words:
        if cur and (len(cur) >= max_words or w["start"] - cur[-1]["end"] > max_gap):
            groups.append(cur)
            cur = []
        cur.append(w)
    if cur:
        groups.append(cur)
    return groups


def build_ass(words: list[dict], out_path: str | Path, offset: float = 0.0,
              max_words: int = 4) -> Path:
    """words: [{word,start,end}] in *clip* time. offset shifts them (e.g. clip start)."""
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    size = int(settings.height * 0.052)
    body = [HEADER.format(w=settings.width, h=settings.height, font=settings.font,
                          size=size, outline=max(3, size // 14),
                          mv=int(settings.height * 0.30))]

    for group in chunk_words(words, max_words):
        start, end = group[0]["start"] - offset, group[-1]["end"] - offset
        if settings.caption_style == "block":
            text = r"{\fad(80,80)}" + " ".join(w["word"].upper() for w in group)
        else:  # karaoke: each word flips to the secondary colour as it is spoken
            parts = []
            for w in group:
                cs = max(int((w["end"] - w["start"]) * 100), 1)
                parts.append(rf"{{\k{cs}}}{w['word'].upper()}")
            text = r"{\fad(60,60)}" + " ".join(parts)
        body.append(f"Dialogue: 0,{_ts(start)},{_ts(end + 0.12)},Pop,,0,0,0,,{text}")

    out_path.write_text("\n".join(body) + "\n", encoding="utf-8")
    return out_path
