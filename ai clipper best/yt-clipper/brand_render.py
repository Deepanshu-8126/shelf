#!/usr/bin/env python3
"""Branded short renderer — logo watermark, emoji title card, punch-in cuts,
colour grade and proper Devanagari karaoke captions.

Config-driven (brand/channel.json) so the same system runs several channels:
    python brand_render.py clips.json --config /home/user/brand/channel.json

clips.json: [{"name","start","end","title","punches":[[t0,t1],...]}]
Word timings come from a YouTube json3 caption dump or any [{word,start,end}] list.
"""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

FFMPEG = "/home/user/bin/ffmpeg"
EMOJI_PX = 109  # NotoColorEmoji is a bitmap font: only this size renders


def is_emoji(ch: str) -> bool:
    o = ord(ch)
    return (0x1F000 <= o <= 0x1FAFF or 0x2600 <= o <= 0x27BF
            or o in (0x2B50, 0x2B55, 0xFE0F, 0x200D) or 0x1F1E6 <= o <= 0x1F1FF)


def runs(text: str):
    """Split into (is_emoji, substring) runs so each uses the right font."""
    out, cur, flag = [], "", None
    for ch in text:
        f = is_emoji(ch)
        if flag is None or f == flag:
            cur += ch
        else:
            out.append((flag, cur)); cur = ch
        flag = f
    if cur:
        out.append((flag, cur))
    return out


def title_card(text: str, cfg: dict, out_png: Path) -> Path:
    """Devanagari + colour-emoji title banner as RGBA PNG."""
    W = cfg["width"]
    size = int(W * 0.072)
    font = ImageFont.truetype(cfg["title_font"], size)
    try:
        font.set_variation_by_axes([800, 100])   # axes order: Weight, Width -> ExtraBold
    except Exception:
        pass
    emoji_dir = Path(cfg.get("emoji_dir", "/home/user/brand/emoji"))

    pieces = []
    for emo, s in runs(text):
        if not s.strip() and not emo:
            pieces.append(("space", int(size * 0.30)))
            continue
        if emo:
            # Noto Color Emoji is COLRv1 — Pillow cannot rasterise it. Use Twemoji PNGs.
            for ch in s:
                if ch in ("\ufe0f", "\u200d"):
                    continue
                f = emoji_dir / f"{ord(ch):x}.png"
                if not f.exists():
                    continue
                k = int(size * 1.12)
                pieces.append(("img", Image.open(f).convert("RGBA")
                               .resize((k, k), Image.LANCZOS)))
        else:
            pieces.append(("txt", s))

    pad, gap = int(size * 0.55), int(size * 0.12)
    probe = Image.new("RGBA", (10, 10)); pd = ImageDraw.Draw(probe)
    widths = []
    for kind, val in pieces:
        if kind == "txt":
            widths.append(int(pd.textlength(val, font=font)))
        elif kind == "img":
            widths.append(val.width)
        else:
            widths.append(val)
    total = sum(widths) + gap * (len(pieces) - 1) + pad * 2
    H = int(size * 2.0)
    card = Image.new("RGBA", (total, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(card)
    accent = cfg.get("accent", "#E8192C")
    d.rounded_rectangle((0, 0, total - 1, H - 1), radius=H // 2,
                        fill=(12, 14, 20, 235), outline=accent, width=max(3, size // 16))

    x = pad
    for (kind, val), w in zip(pieces, widths):
        if kind == "txt":
            d.text((x, H // 2), val, font=font, fill="white", anchor="lm",
                   stroke_width=max(2, size // 22), stroke_fill=(0, 0, 0, 255))
        elif kind == "img":
            card.alpha_composite(val, (x, (H - val.height) // 2))
        x += w + gap

    out_png.parent.mkdir(parents=True, exist_ok=True)
    card.save(out_png)
    return out_png


ASS_HEAD = """[Script Info]
ScriptType: v4.00+
PlayResX: {w}
PlayResY: {h}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Pop,{font},{size},{pri},{sec},&H00000000,&HA0000000,-1,0,0,0,100,100,0,0,1,{outline},3,2,70,70,{mv},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def ts(t: float) -> str:
    t = max(t, 0); h, r = divmod(t, 3600); m, s = divmod(r, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def build_ass(words: list[dict], out: Path, cfg: dict, max_words: int = 3) -> Path:
    size = int(cfg["height"] * cfg["caption_size_pct"])
    body = [ASS_HEAD.format(w=cfg["width"], h=cfg["height"], font=cfg["caption_font"],
                            size=size, pri=cfg["caption_color"], sec=cfg["caption_highlight"],
                            outline=max(4, size // 12),
                            mv=int(cfg["height"] * cfg["caption_margin_v_pct"]))]
    groups, cur = [], []
    for w in words:
        if cur and (len(cur) >= max_words or w["start"] - cur[-1]["end"] > 0.65):
            groups.append(cur); cur = []
        cur.append(w)
    if cur:
        groups.append(cur)

    for g in groups:
        st, en = g[0]["start"], g[-1]["end"]
        parts = [rf"{{\k{max(int((w['end'] - w['start']) * 100), 1)}}}{w['word']}" for w in g]
        # pop-in scale so captions feel kinetic, not static
        fx = r"{\fad(70,70)\t(0,110,\fscx112\fscy112)\t(110,220,\fscx100\fscy100)}"
        body.append(f"Dialogue: 0,{ts(st)},{ts(en + 0.14)},Pop,,0,0,0,,{fx}" + " ".join(parts))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(body) + "\n", encoding="utf-8")
    return out


def zoom_expr(punches: list[list[float]], z: float) -> str:
    """Punch-in 'cuts': crop tighter during the listed windows."""
    if not punches:
        return "1"
    terms = "+".join(f"{z - 1:.3f}*between(t,{a:.2f},{b:.2f})" for a, b in punches)
    return f"(1+{terms})"


def render(clip: dict, words: list[dict], src: str, cfg: dict, outdir: Path) -> dict:
    s, e = clip["start"], clip["end"]
    dur = e - s
    W, H = cfg["width"], cfg["height"]
    name = clip["name"]
    ass = build_ass(words, outdir / f"{name}.ass", cfg)
    card = title_card(clip["title"], cfg, outdir / f"{name}_title.png")
    mp4 = outdir / f"{name}.mp4"

    z = zoom_expr(clip.get("punches", []), cfg["punch_zoom"])
    wm_w = int(W * cfg["watermark_scale"])
    m = cfg["watermark_margin"]
    pos = {"top-right": (f"W-w-{m}", f"{m+10}"), "top-left": (f"{m}", f"{m+10}"),
           "bottom-right": (f"W-w-{m}", f"H-h-{m}")}[cfg["watermark_pos"]]
    tsec = cfg["title_seconds"]
    esc = str(ass).replace(":", r"\:")

    fc = (
        # blurred 9:16 backdrop
        f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
        f"gblur=sigma=26,eq=brightness=-0.08[bg];"
        # foreground with punch-in crop + grade
        f"[0:v]crop=w='iw/{z}':h='ih/{z}':x='(iw-ow)/2':y='(ih-oh)/2',"
        f"scale={W}:-2:force_original_aspect_ratio=decrease,{cfg['grade']}[fg];"
        f"[bg][fg]overlay=(W-w)/2:(H-h)/2,setsar=1[base];"
        # logo watermark
        f"[1:v]scale={wm_w}:-1,format=rgba,colorchannelmixer=aa={cfg['watermark_opacity']}[wm];"
        f"[base][wm]overlay={pos[0]}:{pos[1]}[wmd];"
        # emoji title card, fades out
        f"[2:v]scale={int(W*0.86)}:-1,format=rgba,"
        f"fade=t=in:st=0:d=0.3:alpha=1,fade=t=out:st={tsec-0.45:.2f}:d=0.45:alpha=1[tc];"
        f"[wmd][tc]overlay=(W-w)/2:{int(H*0.13)}:enable='lt(t,{tsec})'[titled];"
        # captions last so nothing covers them
        f"[titled]ass='{esc}':fontsdir='{cfg['caption_fontdir']}'[vout]"
    )
    # A still PNG decodes as ONE frame at t=0, so fade/enable see no timeline and the
    # overlay stays invisible. -loop 1 -framerate N -t dur turns each into a real stream.
    fps = str(cfg["fps"])
    cmd = [FFMPEG, "-y", "-v", "error", "-ss", f"{s:.3f}", "-t", f"{dur:.3f}", "-i", src,
           "-loop", "1", "-framerate", fps, "-t", f"{dur:.3f}", "-i", cfg["watermark"],
           "-loop", "1", "-framerate", fps, "-t", f"{dur:.3f}", "-i", str(card),
           "-filter_complex", fc, "-map", "[vout]", "-map", "0:a",
           "-r", str(cfg["fps"]), "-c:v", "libx264", "-preset", "medium",
           "-crf", str(cfg["crf"]), "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", str(mp4)]
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode:
        raise RuntimeError(p.stderr[-2500:])
    return {"name": name, "mp4": str(mp4), "duration": round(dur, 2),
            "size_mb": round(mp4.stat().st_size / 1e6, 1), "title": clip["title"]}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("clips", help="clips.json")
    ap.add_argument("--words", required=True, help="word-timing json [{w/word,t/start,end}]")
    ap.add_argument("--src", required=True)
    ap.add_argument("--config", default="/home/user/brand/channel.json")
    ap.add_argument("--outdir", default="/home/user/Shorts")
    a = ap.parse_args()

    cfg = json.loads(Path(a.config).read_text())
    allw = json.loads(Path(a.words).read_text())
    norm = [{"word": x.get("word", x.get("w")), "start": x.get("start", x.get("t")),
             "end": x["end"]} for x in allw]
    outdir = Path(a.outdir); outdir.mkdir(parents=True, exist_ok=True)

    res = []
    for c in json.loads(Path(a.clips).read_text()):
        w = [{"word": x["word"], "start": x["start"] - c["start"],
              "end": x["end"] - c["start"]}
             for x in norm if c["start"] <= x["start"] < c["end"]]
        r = render(c, w, a.src, cfg, outdir)
        print(f"  ✓ {r['name']}  {r['duration']}s  {r['size_mb']} MB  |  {r['title']}")
        res.append(r)
    (outdir / "render.json").write_text(json.dumps(res, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
