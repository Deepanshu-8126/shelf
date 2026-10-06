"""Kinetic captions as .ass, with automatic safe placement.

Placement logic: Shorts UI covers the bottom ~16 % (title, handle, buttons) and the
right edge (action rail). When the source is letterboxed over a blurred backdrop we
also want captions to sit *inside* the video band if it is tall enough, otherwise just
above the UI zone. `auto_margin_v` works that out from the source aspect ratio.

Styles (``--caption-style``):
    karaoke  word-by-word colour fill via {\\k} tags (default)
    hormozi  whole phrase stays up, the spoken word pops in the accent colour
    bounce   springy all-caps pop, no fill
    glow     soft blurred neon edge
    plain    static, no animation
"""
from __future__ import annotations

from pathlib import Path

HEAD = """[Script Info]
ScriptType: v4.00+
PlayResX: {w}
PlayResY: {h}
WrapStyle: 2
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.709

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Pop,{font},{size},{pri},{sec},{outcol},&HB0000000,-1,0,0,0,100,100,0,0,{bstyle},{outline},{shadow},2,{ml},{mr},{mv},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

FX = {
    # fade + small overshoot; the colour fill itself comes from the {\k} tags
    "karaoke": r"{\fad(70,70)\t(0,110,\fscx112\fscy112)\t(110,220,\fscx100\fscy100)}",
    # springy pop, no fill
    "bounce": (r"{\fad(40,40)\t(0,90,\fscx128\fscy128)\t(90,190,\fscx94\fscy94)"
               r"\t(190,260,\fscx100\fscy100)}"),
    # soft neon edge
    "glow": (r"{\fad(90,90)\blur2\t(0,120,\fscx108\fscy108)"
             r"\t(120,240,\fscx100\fscy100)}"),
    "plain": r"{\fad(60,60)}",
}

# High-impact words worth colouring even when they are not the active word.
# Idea borrowed from CapShorts' auto-keywords; the list is ours.
KEYWORDS = {
    "en": ("never", "always", "everyone", "nobody", "insane", "crazy", "shocked",
           "secret", "truth", "lied", "money", "free", "worst", "best", "first",
           "stop", "don't", "actually", "literally", "million", "billion"),
    "hi": ("कभी", "सबसे", "कोई", "पागल", "सच", "झूठ", "पैसा", "मुफ़्त", "सबूत",
           "बिल्कुल", "रुको", "देखो", "करोड़", "लाख", "गलत", "सही"),
    "es": ("nunca", "siempre", "nadie", "todos", "loco", "verdad", "mentira",
           "dinero", "gratis", "peor", "mejor", "para", "mira", "millón"),
}


def _kw_set(langs=("en", "hi", "es")) -> set[str]:
    out: set[str] = set()
    for k in langs:
        out |= {w.lower() for w in KEYWORDS.get(k, ())}
    return out


STYLES = ("karaoke", "hormozi", "bounce", "glow", "plain")


def ts(t: float) -> str:
    t = max(t, 0.0)
    h, r = divmod(t, 3600)
    m, s = divmod(r, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def auto_margin_v(width: int, height: int, src_w: int, src_h: int,
                  blur_bg: bool = True) -> int:
    """Vertical margin (px from bottom) that clears the Shorts UI."""
    ui_safe = int(height * 0.17)          # buttons / title overlay
    if not blur_bg or not src_w or not src_h:
        return max(ui_safe, int(height * 0.14))
    band_h = int(width * src_h / src_w)   # height of the fitted video band
    band_bottom = (height - band_h) // 2  # px from frame bottom to band bottom
    inside = band_bottom + int(band_h * 0.06)   # just inside the video band
    return max(ui_safe, inside)


def chunk(words: list[dict], max_words: int = 3, max_gap: float = 0.65,
          max_chars: int = 22) -> list[list[dict]]:
    groups, cur = [], []
    for w in words:
        too_long = sum(len(x["word"]) + 1 for x in cur) + len(w["word"]) > max_chars
        if cur and (len(cur) >= max_words or too_long
                    or w["start"] - cur[-1]["end"] > max_gap):
            groups.append(cur)
            cur = []
        cur.append(w)
    if cur:
        groups.append(cur)
    return groups


def build(words: list[dict], out: Path, *, width: int, height: int, font: str,
          size_pct: float = 0.062, margin_v: int | None = None,
          primary: str = "&H00FFFFFF", highlight: str = "&H0024E8FF",
          style: str = "karaoke", max_words: int = 3,
          max_cps: float = 20.0, keyword_color: str = "&H005CF0FF",
          keywords: set[str] | None = None, box: bool = False,
          box_color: str = "&H00141414") -> Path:
    """`box=True` paints a solid plate behind the text.

    Needed more often than you would think: a plain outline disappears over a
    white table or a busy on-screen logo, which is most podcast and TV footage.

    The plate is opaque on purpose. libass draws one box per colour run, so a
    semi-transparent plate shows a darker seam everywhere the colour changes --
    which, in karaoke and hormozi, is on every single word.
    """
    kw = _kw_set() if keywords is None else {k.lower() for k in keywords}
    size = int(height * size_pct)
    mv = margin_v if margin_v is not None else int(height * 0.17)
    head = HEAD.format(w=width, h=height, font=font, size=size,
                       pri=primary, sec=highlight,
                       bstyle=3 if box else 1,
                       outcol=box_color if box else "&H00101010",
                       shadow=0 if box else 3,
                       outline=(max(6, size // 10) if box else max(4, size // 12)),
                       ml=int(width * 0.07), mr=int(width * 0.07), mv=mv)
    body = [head]

    groups = chunk(words, max_words)
    for gi, g in enumerate(groups):
        st, en = g[0]["start"], g[-1]["end"]
        # a line must disappear before the next one appears, else libass stacks them
        nxt = groups[gi + 1][0]["start"] if gi + 1 < len(groups) else None
        hold = en + 0.14 if nxt is None else min(en + 0.14, nxt - 0.01)
        hold = max(hold, en)
        # Keep the line on screen long enough to actually read. A line faster
        # than max_cps characters/second is unreadable; stretch it into the
        # pause that follows, never into the next line.
        if max_cps > 0:
            chars = len(" ".join(w["word"] for w in g))
            need = st + chars / max_cps
            ceiling = (nxt - 0.01) if nxt is not None else need
            hold = max(hold, min(need, ceiling))

        if style == "hormozi":
            # One Dialogue per word: the phrase stays on screen while the word
            # being spoken pops in the accent colour.
            for i, w in enumerate(g):
                parts = []
                for j, x in enumerate(g):
                    t = x["word"].upper()
                    if j != i and x["word"].strip(".,!?¿¡").lower() in kw:
                        parts.append("{\\c" + keyword_color + "}" + t
                                     + "{\\c" + primary + "}")
                        continue
                    if j == i:
                        # With a plate behind the text, scaling the active word
                        # changes the line width every word and the plate jitters.
                        # Colour alone is emphasis enough there.
                        big = "" if box else "\\fscx118\\fscy118"
                        rst = "" if box else "\\fscx100\\fscy100"
                        parts.append("{\\c" + highlight + big + "}" + t
                                     + "{\\c" + primary + rst + "}")
                    else:
                        parts.append(t)
                a = w["start"]
                b = g[i + 1]["start"] if i + 1 < len(g) else hold
                # fade only on the way in and out of the whole phrase - fading
                # every word made the line strobe once per syllable
                fin = 60 if i == 0 else 0
                fout = 60 if i == len(g) - 1 else 0
                body.append(f"Dialogue: 0,{ts(a)},{ts(b)},Pop,,0,0,0,,"
                            + "{\\fad(%d,%d)}" % (fin, fout) + " ".join(parts))
            continue

        if style == "karaoke":
            bits = []
            for w in g:
                k = max(int((w["end"] - w["start"]) * 100), 1)
                word = w["word"]
                if word.strip(".,!?¿¡").lower() in kw:
                    word = "{\\c" + keyword_color + "}" + word + "{\\c" + primary + "}"
                bits.append("{\\k%d}%s" % (k, word))
            txt = " ".join(bits)
        elif style == "bounce":
            txt = " ".join(w["word"] for w in g).upper()
        else:
            txt = " ".join(w["word"] for w in g)

        fx = FX.get(style, FX["karaoke"])
        body.append(f"Dialogue: 0,{ts(st)},{ts(hold)},Pop,,0,0,0,,{fx}{txt}")

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(body) + "\n", encoding="utf-8")
    return out


def to_srt(words: list[dict], max_words: int = 8) -> str:
    def t(x: float) -> str:
        h, r = divmod(max(x, 0), 3600)
        m, s = divmod(r, 60)
        return f"{int(h):02d}:{int(m):02d}:{int(s):02d},{int((s % 1)*1000):03d}"

    out = []
    for i, g in enumerate(chunk(words, max_words, 1.2, 80), 1):
        out.append(f"{i}\n{t(g[0]['start'])} --> {t(g[-1]['end'])}\n"
                   f"{' '.join(w['word'] for w in g)}\n")
    return "\n".join(out)
