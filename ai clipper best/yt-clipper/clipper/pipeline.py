"""Glue: URL -> N clips x M languages (mp4 + .ass + CapCut draft + metadata.json)."""
from __future__ import annotations

import json
import re
from pathlib import Path

from .config import settings


def slug(s: str, n: int = 40) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:n] or "clip"


def run_pipeline(url: str, languages: list[str] | None = None, n_clips: int | None = None,
                 mode: str = "blur", dry: bool = False, source: str | None = None) -> dict:
    from . import captions, capcut, download, render, select, transcribe, tts

    languages = languages or settings.languages
    out_root = Path(settings.work_dir)
    out_root.mkdir(parents=True, exist_ok=True)

    # 1. source
    if source:
        meta = {"id": Path(source).stem, "title": Path(source).stem, "path": source}
    else:
        print(f"[1/5] downloading {url}")
        meta = download.download(url)

    # 2. transcript
    print("[2/5] transcribing")
    tr = transcribe.transcribe(meta["path"])
    Path(meta["path"]).with_suffix(".srt").write_text(
        transcribe.to_srt(tr["segments"]), encoding="utf-8")

    # 3. clip selection
    print("[3/5] selecting clips")
    clips = select.select_clips(tr, n_clips)
    print(f"      -> {len(clips)} clips: " +
          ", ".join(f"{c['start']:.0f}-{c['end']:.0f}s" for c in clips))

    results = []
    for i, c in enumerate(clips, 1):
        base = f"{meta['id']}_{i:02d}_{slug(c.get('title', ''))}"
        for lang in languages:
            d = out_root / lang
            d.mkdir(parents=True, exist_ok=True)
            stem = d / base

            # 4. voiceover (translated if needed)
            vo = None
            words = [{**w, "start": w["start"] - c["start"], "end": w["end"] - c["start"]}
                     for w in c.get("words", [])]
            if settings.dub:
                print(f"[4/5] {base} [{lang}] tts")
                text = c["text"] if lang == tr.get("language") else tts.translate(c["text"], lang)
                if not dry:
                    vo = tts.synthesize(text, lang, stem.with_suffix(".mp3"))
                    words = vo["words"]          # dub-accurate timings
                    vo = vo["path"]

            ass = captions.build_ass(words, stem.with_suffix(".ass")) \
                if settings.caption_style != "none" else None

            # 5. render + draft
            print(f"[5/5] {base} [{lang}] render")
            cmd = render.render_clip(meta["path"], c["start"], c["end"],
                                     stem.with_suffix(".mp4"), ass=ass,
                                     voice_audio=vo, mode=mode, dry=dry)
            draft = None
            if settings.emit_capcut_draft:
                draft = str(capcut.build_draft(stem.with_suffix(".mp4"),
                                               c["end"] - c["start"], f"{base}_{lang}",
                                               words=words, voice_audio=vo))
            results.append({"clip": i, "lang": lang, "start": c["start"], "end": c["end"],
                            "title": c.get("title", ""), "hook": c.get("hook", ""),
                            "score": c.get("score"), "mp4": str(stem.with_suffix(".mp4")),
                            "ass": str(ass) if ass else None, "voice": vo,
                            "capcut_draft": draft, "ffmpeg": cmd if dry else None})

    out = {"source": meta, "language": tr.get("language"), "clips": results}
    (out_root / f"{meta['id']}.results.json").write_text(json.dumps(out, indent=2,
                                                                   ensure_ascii=False))
    return out
