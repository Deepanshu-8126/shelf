"""Channel branding: emoji title card + logo watermark.

Two gotchas baked in here:
  * Google's current Noto Color Emoji is COLRv1, which Pillow cannot rasterise — you get
    blank boxes. We composite Twemoji PNGs instead (assets/emoji/<codepoint>.png).
  * Variable fonts: libass ignores variation axes, so captions render thin. Ship a static
    instance (assets/NotoSansDevanagari-ExtraBold.ttf) and name that family in the profile.
"""
from __future__ import annotations

import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

TWEMOJI = ("https://cdn.jsdelivr.net/gh/jdecked/twemoji@latest/assets/72x72/{cp}.png",
           "https://cdn.jsdelivr.net/gh/twitter/twemoji@14.0.2/assets/72x72/{cp}.png")


def is_emoji(ch: str) -> bool:
    o = ord(ch)
    return (0x1F000 <= o <= 0x1FAFF or 0x2600 <= o <= 0x27BF
            or o in (0x2B50, 0x2B55) or 0x1F1E6 <= o <= 0x1F1FF)


def emoji_png(ch: str, emoji_dir: Path) -> Path | None:
    """Local Twemoji asset, downloaded on first use and cached."""
    emoji_dir.mkdir(parents=True, exist_ok=True)
    f = emoji_dir / f"{ord(ch):x}.png"
    if f.exists():
        return f
    for tpl in TWEMOJI:
        try:
            data = urllib.request.urlopen(tpl.format(cp=f"{ord(ch):x}"), timeout=20).read()
            if len(data) > 500:
                f.write_bytes(data)
                return f
        except Exception:
            continue
    return None


def title_card(text: str, out: Path, *, width: int, font_path: str, emoji_dir: Path,
               accent: str = "#E8192C", bg=(12, 14, 20, 235),
               size_pct: float = 0.072) -> Path:
    size = int(width * size_pct)
    font = ImageFont.truetype(font_path, size)
    try:
        font.set_variation_by_axes([800, 100])     # Weight, Width (no-op if static)
    except Exception:
        pass

    pieces: list[tuple[str, object]] = []
    buf = ""
    for ch in text:
        if is_emoji(ch):
            if buf:
                pieces.append(("txt", buf)); buf = ""
            p = emoji_png(ch, emoji_dir)
            if p:
                k = int(size * 1.12)
                pieces.append(("img", Image.open(p).convert("RGBA")
                               .resize((k, k), Image.LANCZOS)))
        elif ch in ("\ufe0f", "\u200d"):
            continue
        else:
            buf += ch
    if buf:
        pieces.append(("txt", buf))

    probe = ImageDraw.Draw(Image.new("RGBA", (8, 8)))
    widths = [int(probe.textlength(v, font=font)) if k == "txt" else v.width
              for k, v in pieces]
    pad, gap = int(size * 0.55), int(size * 0.12)
    W = sum(widths) + gap * max(len(pieces) - 1, 0) + pad * 2
    H = int(size * 2.0)
    card = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(card)
    d.rounded_rectangle((0, 0, W - 1, H - 1), radius=H // 2, fill=bg,
                        outline=accent, width=max(3, size // 16))
    x = pad
    for (kind, val), w in zip(pieces, widths):
        if kind == "txt":
            d.text((x, H // 2), val, font=font, fill="white", anchor="lm",
                   stroke_width=max(2, size // 22), stroke_fill=(0, 0, 0, 255))
        else:
            card.alpha_composite(val, (x, (H - val.height) // 2))
        x += w + gap
    out.parent.mkdir(parents=True, exist_ok=True)
    card.save(out)
    return out
