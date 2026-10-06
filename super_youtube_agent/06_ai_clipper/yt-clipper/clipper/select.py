"""Step 3 - pick the viral segments.

Two scorers:
  * llm_select()       - asks an LLM to return JSON clip boundaries (best quality)
  * heuristic_select() - zero-dependency fallback: hook words, speech density,
                         question/number density, sentence-boundary snapping.
`select_clips()` tries the LLM and silently falls back.
"""
from __future__ import annotations

import json
import re

from .config import settings

HOOKS_EN = ["crazy", "insane", "nobody", "secret", "mistake", "never", "biggest", "wrong",
            "truth", "actually", "here's why", "the problem", "what if", "listen", "wait"]
HOOKS_ES = ["increíble", "nadie", "secreto", "error", "nunca", "verdad", "en realidad",
            "el problema", "escucha", "espera", "lo más"]
# Hindi/Hinglish vlog hooks: conflict, shock, reveal, direct address
HOOKS_HI = ["पुलिस", "गाली", "लड़ाई", "झगड़ा", "गुस्सा", "चोरी", "डर", "रात", "सच",
            "गलती", "कभी नहीं", "पहली बार", "देखो", "सुनो", "भाई", "अरे", "यार",
            "मत करना", "क्यों", "कैसे", "सबसे बड़ा", "पागल", "बहुत बुरा", "शिकायत",
            "problem", "police", "fight", "shock"]
SYSTEM = """You are a short-form video editor. From the timestamped transcript pick the
{n} segments most likely to retain viewers on YouTube Shorts / TikTok.
Rules: each clip {lo}-{hi} seconds, must start on a hook and end on a complete thought,
no overlap. Return ONLY JSON: {{"clips":[{{"start":float,"end":float,"title":str,
"hook":str,"score":int}}]}}"""


def _flatten(transcript: dict) -> list[dict]:
    return transcript["segments"]


def llm_select(transcript: dict, n: int | None = None) -> list[dict]:
    from openai import OpenAI

    n = n or settings.clips_per_video
    client = OpenAI(api_key=settings.llm_api_key)
    lines = "\n".join(f"[{s['start']:.1f}-{s['end']:.1f}] {s['text']}" for s in _flatten(transcript))
    lines = lines[:120_000]
    r = client.chat.completions.create(
        model=settings.llm_model,
        response_format={"type": "json_object"},
        temperature=0.4,
        messages=[
            {"role": "system", "content": SYSTEM.format(
                n=n, lo=int(settings.min_clip_s), hi=int(settings.max_clip_s))},
            {"role": "user", "content": lines},
        ],
    )
    clips = json.loads(r.choices[0].message.content)["clips"]
    return _sanitize(clips, transcript)


def heuristic_select(transcript: dict, n: int | None = None) -> list[dict]:
    n = n or settings.clips_per_video
    segs = _flatten(transcript)
    hooks = HOOKS_EN + HOOKS_ES + HOOKS_HI
    cands = []
    for i, s in enumerate(segs):
        start = s["start"]
        j, end = i, s["end"]
        while end - start < settings.min_clip_s and j + 1 < len(segs):
            j += 1
            end = segs[j]["end"]
        if end - start < settings.min_clip_s * 0.6:
            continue
        while end - start > settings.max_clip_s and j > i:
            j -= 1
            end = segs[j]["end"]
        text = " ".join(x["text"] for x in segs[i:j + 1])
        low = text.lower()
        words = len(text.split())
        dur = max(end - start, 1e-6)
        score = 0.0
        score += 4 * sum(h in low for h in hooks)
        score += 2 * low.count("?")
        score += 1.5 * len(re.findall(r"\b\d[\d,.]*\b", text))     # numbers = concrete
        score += min(words / dur, 4.0)                              # speech density (wps)
        score += 2 if text.rstrip().endswith((".", "!", "?", "।")) else 0
        cands.append({"start": round(start, 2), "end": round(end, 2),
                      "score": round(score, 2), "title": text[:60].strip(),
                      "hook": segs[i]["text"][:80]})

    cands.sort(key=lambda c: -c["score"])
    picked: list[dict] = []
    for c in cands:
        if all(c["end"] <= p["start"] or c["start"] >= p["end"] for p in picked):
            picked.append(c)
        if len(picked) == n:
            break
    picked.sort(key=lambda c: c["start"])
    return _sanitize(picked, transcript)


def _sanitize(clips: list[dict], transcript: dict) -> list[dict]:
    dur = transcript["segments"][-1]["end"] if transcript["segments"] else 0
    out = []
    for c in clips:
        s = max(0.0, float(c["start"]))
        e = min(float(c["end"]), dur)
        if e - s < 5:
            continue
        e = min(e, s + settings.max_clip_s)
        c = dict(c, start=round(s, 2), end=round(e, 2))
        c["words"] = [w for seg in transcript["segments"] for w in seg.get("words", [])
                      if w["start"] >= s and w["end"] <= e]
        c["text"] = " ".join(seg["text"] for seg in transcript["segments"]
                             if seg["start"] >= s and seg["end"] <= e)
        out.append(c)
    return out


def select_clips(transcript: dict, n: int | None = None) -> list[dict]:
    if settings.llm_api_key:
        try:
            return llm_select(transcript, n)
        except Exception as exc:  # noqa: BLE001
            print(f"[select] LLM failed ({exc}); using heuristic scorer")
    return heuristic_select(transcript, n)
