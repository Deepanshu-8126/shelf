#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import json

import os

from . import captions
from .pipeline import run


def _load_env(path: str = ".env") -> None:
    """Load KEY=VALUE lines from .env so secrets stay out of the shell history.

    Real environment variables always win, so `GROQ_API_KEY=... autoclip ...`
    still overrides the file.
    """
    for base in (Path.cwd(), Path(__file__).resolve().parent.parent):
        f = base / path
        if not f.is_file():
            continue
        for line in f.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
        return


def main(argv=None) -> int:
    _load_env()
    p = argparse.ArgumentParser(
        prog="autoclip",
        description="YouTube link / channel / search -> branded vertical shorts",
        epilog="examples:\n"
               "  autoclip 'https://youtu.be/VIDEOID' --clips 2\n"
               "  autoclip 'https://www.youtube.com/@BiggBoss' --limit 3 --genre reality\n"
               "  autoclip 'ytsearch5:bigg boss fight' --genre reality --safe 2\n",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("target", help="video URL, playlist, channel, or ytsearchN:query")
    p.add_argument("--clips", type=int, default=2, help="clips per video")
    p.add_argument("--limit", type=int, default=1, help="videos to take from a channel/search")
    p.add_argument("--genre", default="vlog", choices=["vlog", "reality", "gaming", "news"])
    p.add_argument("--profile", default=None, help="brand profile json")
    p.add_argument("--crf", type=int, default=None,
                   help="x264 quality, lower=better (default 23)")
    p.add_argument("--caption-box", action="store_true", default=None,
                   help="solid plate behind captions; use on bright or busy "
                        "footage where the outline alone disappears")
    p.add_argument("--caption-style", default=None,
                   choices=list(captions.STYLES),
                   help="caption animation (default: karaoke, or profile setting)")
    p.add_argument("--outdir", default="Shorts")
    p.add_argument("--safe", type=int, default=1, choices=[0, 1, 2, 3],
                   help="fingerprint-breaking level: 0 none .. 3 mirror+speed+grain")
    p.add_argument("--langs", nargs="+", default=["hi", "en"])
    p.add_argument("--whisper", default="base", help="fallback whisper model size")
    p.add_argument("--height", type=int, default=1080,
                   help="max source resolution to download (default 1080)")
    p.add_argument("--workers", type=int, default=None)
    p.add_argument("--cookies", default=None, help="cookies.txt for age/bot-gated videos")
    a = p.parse_args(argv)

    res = run(a.target, clips=a.clips, genre=a.genre, outdir=a.outdir,
              caption_style=a.caption_style, caption_box=a.caption_box, crf=a.crf,
              profile=a.profile, limit=a.limit, safe_level=a.safe,
              langs=tuple(a.langs), whisper_model=a.whisper, height=a.height,
              workers=a.workers, cookies=a.cookies)
    print(json.dumps(res, indent=2, ensure_ascii=False)[:2000])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
