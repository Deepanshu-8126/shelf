"""Step 2 - word-level transcript via faster-whisper (4-8x faster than openai-whisper)."""
from __future__ import annotations

import json
from pathlib import Path

from .config import settings


def transcribe(video_path: str | Path, language: str | None = None) -> dict:
    """Return {'language', 'text', 'segments':[{start,end,text,words:[{word,start,end}]}]}.

    Cached next to the video as <stem>.transcript.json.
    """
    video_path = Path(video_path)
    cache = video_path.with_suffix(".transcript.json")
    if cache.exists():
        return json.loads(cache.read_text())

    if settings.whisper_backend == "faster":
        data = _faster_whisper(video_path, language)
    else:
        data = _openai_whisper(video_path, language)

    cache.write_text(json.dumps(data, ensure_ascii=False))
    return data


def _faster_whisper(path: Path, language: str | None) -> dict:
    from faster_whisper import WhisperModel

    model = WhisperModel(settings.whisper_model, device="auto", compute_type="auto")
    segments, info = model.transcribe(
        str(path), language=language, word_timestamps=True, vad_filter=True,
        vad_parameters={"min_silence_duration_ms": 400},
    )
    segs = []
    for s in segments:
        segs.append({
            "start": round(s.start, 3),
            "end": round(s.end, 3),
            "text": s.text.strip(),
            "words": [
                {"word": w.word.strip(), "start": round(w.start, 3), "end": round(w.end, 3)}
                for w in (s.words or [])
            ],
        })
    return {
        "language": info.language,
        "text": " ".join(s["text"] for s in segs),
        "segments": segs,
    }


def _openai_whisper(path: Path, language: str | None) -> dict:
    import whisper

    model = whisper.load_model(settings.whisper_model)
    r = model.transcribe(str(path), language=language, word_timestamps=True)
    segs = [{
        "start": round(s["start"], 3),
        "end": round(s["end"], 3),
        "text": s["text"].strip(),
        "words": [{"word": w["word"].strip(), "start": round(w["start"], 3),
                   "end": round(w["end"], 3)} for w in s.get("words", [])],
    } for s in r["segments"]]
    return {"language": r.get("language", "en"), "text": r["text"], "segments": segs}


def to_srt(segments: list[dict]) -> str:
    def ts(t: float) -> str:
        h, r = divmod(t, 3600)
        m, s = divmod(r, 60)
        return f"{int(h):02d}:{int(m):02d}:{int(s):02d},{int((s % 1) * 1000):03d}"

    out = []
    for i, s in enumerate(segments, 1):
        out.append(f"{i}\n{ts(s['start'])} --> {ts(s['end'])}\n{s['text']}\n")
    return "\n".join(out)
