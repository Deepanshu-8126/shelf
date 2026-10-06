"""Word-level timings.

Order matters for speed AND quality:
  1. YouTube auto-captions via yt-dlp (json3)  -> ~2 s, word timings included
  2. faster-whisper                            -> minutes, needed for non-YouTube sources

Measured on a 16-minute Hindi vlog: YouTube captions 2 s and clean Devanagari;
faster-whisper `base` int8/CPU took 18.7 min and produced unusable mixed-script text.
Always try captions first for Hindi/Hinglish.
"""
from __future__ import annotations

import glob
import json
import os
import tempfile
from pathlib import Path

MAX_WORD = 0.6


def youtube_captions(url: str, langs: tuple[str, ...] = ("hi", "en")) -> list[dict] | None:
    """Auto-captions as word timings. ~2 s, and for Hindi far better than Whisper.

    Languages are requested ONE AT A TIME: asking for several at once means a single
    HTTP 429 on any of them aborts the whole call, even if the first language already
    downloaded fine. `ignoreerrors` keeps a partial failure non-fatal too.
    """
    import yt_dlp

    for lg in langs:
        with tempfile.TemporaryDirectory() as td:
            opts = {"quiet": True, "no_warnings": True, "skip_download": True,
                    "ignoreerrors": True, "writeautomaticsub": True,
                    "writesubtitles": True, "subtitleslangs": [lg],
                    "subtitlesformat": "json3", "outtmpl": os.path.join(td, "s"),
                    "extractor_args": {"youtube": {"player_client": ["ios", "android", "mweb"]}}}
            try:
                with yt_dlp.YoutubeDL(opts) as ydl:
                    ydl.extract_info(url, download=True)   # needed to WRITE sub files
            except Exception:
                continue
            files = sorted(glob.glob(os.path.join(td, "*.json3")))
            if not files:
                continue
            content = Path(files[0]).read_text(encoding="utf-8").strip()
            if not content:
                continue
            try:
                data = json.loads(content)
            except Exception:
                continue

        words = []
        for ev in data.get("events", []):
            if not ev.get("segs"):
                continue
            base = ev.get("tStartMs", 0)
            for s in ev["segs"]:
                txt = s.get("utf8", "")
                if txt.strip():
                    words.append({"word": txt.strip(),
                                  "start": round((base + s.get("tOffsetMs", 0)) / 1000, 2)})
        if len(words) < 20:
            continue
        for i, w in enumerate(words):
            nxt = words[i + 1]["start"] if i + 1 < len(words) else w["start"] + MAX_WORD
            w["end"] = round(min(w["start"] + MAX_WORD, max(nxt, w["start"] + 0.08)), 2)
        return words
    return None


def whisper_words(media: str, model: str = "base", language: str | None = None) -> list[dict]:
    import numpy as np
    from faster_whisper import WhisperModel

    from .ffmpeg import binary, run

    wav = Path(media).with_suffix(".16k.wav")
    if not wav.exists():
        run(["-i", str(media), "-vn", "-ac", "1", "-ar", "16000", str(wav)])
    import wave

    with wave.open(str(wav)) as w:
        pcm = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16)
    audio = pcm.astype(np.float32) / 32768.0

    m = WhisperModel(model, device="auto", compute_type="auto",
                     cpu_threads=max(2, (os.cpu_count() or 2)))
    segs, _ = m.transcribe(audio, language=language, word_timestamps=True,
                           vad_filter=True,
                           vad_parameters={"min_silence_duration_ms": 400})
    out = []
    for s in segs:
        for x in (s.words or []):
            out.append({"word": x.word.strip(), "start": round(x.start, 2),
                        "end": round(x.end, 2)})
    return out


def get_words(url: str | None, media: str | None, cache: Path,
              langs: tuple[str, ...] = ("hi", "en"), model: str = "base",
              prefer: str = "captions") -> tuple[list[dict], str]:
    if cache.exists():
        if cache.stat().st_size > 0:
            try:
                d = json.loads(cache.read_text(encoding="utf-8"))
                if isinstance(d, dict) and "words" in d:
                    return d["words"], d.get("source", "cache")
            except Exception:
                cache.unlink(missing_ok=True)
        else:
            cache.unlink(missing_ok=True)

    words, src = None, ""
    if prefer == "captions" and url:
        words = youtube_captions(url, langs)
        src = "youtube-captions"
    if not words and media:
        words = whisper_words(media, model=model,
                              language=langs[0] if langs else None)
        src = f"whisper-{model}"
    if not words:
        raise RuntimeError("no transcript: captions unavailable and no media for whisper")

    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps({"source": src, "words": words}, ensure_ascii=False))
    return words, src


def dedupe(words: list[dict], gap: float = 0.12) -> list[dict]:
    """Drop the duplicate words YouTube's rolling auto-captions emit.

    A rolling cue re-prints the tail of the previous line, so the word stream
    contains back-to-back repeats ("it's it's almost almost") with a near-zero
    gap. A genuine spoken repeat ("no no no") normally has a real pause, so we
    only collapse pairs closer than `gap` seconds.
    """
    out: list[dict] = []
    for w in words:
        if out:
            prev = out[-1]
            same = prev["word"].strip().lower() == w["word"].strip().lower()
            if same and w["start"] - prev["end"] <= gap:
                prev["end"] = max(prev["end"], w["end"])   # keep the longer span
                continue
        out.append(dict(w))
    return out
