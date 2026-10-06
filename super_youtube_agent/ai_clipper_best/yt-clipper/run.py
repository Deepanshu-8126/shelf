#!/usr/bin/env python3
"""CLI:  python run.py <youtube-url> --langs en es --clips 3
        python run.py --source local.mp4 --dry      # plan only, no ffmpeg
        python run.py --demo                        # offline sanity check
"""
from __future__ import annotations

import argparse
import json

from clipper.config import settings


def main() -> None:
    p = argparse.ArgumentParser(description="Automated YouTube -> Shorts clipper")
    p.add_argument("url", nargs="?", help="YouTube / any yt-dlp supported URL")
    p.add_argument("--source", help="use a local video file instead of downloading")
    p.add_argument("--langs", nargs="+", default=settings.languages, help="e.g. en es es-mx")
    p.add_argument("--clips", type=int, default=settings.clips_per_video)
    p.add_argument("--mode", choices=["blur", "crop"], default="blur")
    p.add_argument("--model", default=settings.whisper_model)
    p.add_argument("--captions", choices=["karaoke", "block", "none"], default="karaoke")
    p.add_argument("--no-dub", action="store_true", help="keep original audio, no TTS")
    p.add_argument("--no-draft", action="store_true", help="skip CapCut draft output")
    p.add_argument("--dry", action="store_true", help="print the ffmpeg plan, render nothing")
    p.add_argument("--demo", action="store_true", help="run the offline sample test")
    a = p.parse_args()

    if a.demo:
        import demo
        demo.main()
        return
    if not (a.url or a.source):
        p.error("give a URL or --source")

    settings.whisper_model = a.model
    settings.caption_style = a.captions
    settings.dub = not a.no_dub
    settings.emit_capcut_draft = not a.no_draft
    settings.clips_per_video = a.clips
    settings.languages = a.langs

    from clipper.pipeline import run_pipeline
    res = run_pipeline(a.url, languages=a.langs, n_clips=a.clips, mode=a.mode,
                       dry=a.dry, source=a.source)
    print(json.dumps(res, indent=2, ensure_ascii=False)[:4000])


if __name__ == "__main__":
    main()
