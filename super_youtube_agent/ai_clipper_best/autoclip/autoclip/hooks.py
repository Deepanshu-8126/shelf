"""Pick the clip-worthy moments.

`llm_select` (needs OPENAI_API_KEY) is best. Without a key the lexicon scorer runs:
drama/fight/reveal words in Hindi + English + Spanish, question density, numbers,
speech rate, and snapping to a natural pause so clips don't start mid-word.
Tuned lexicons per genre: `vlog`, `reality` (Bigg Boss style), `gaming`, `news`.
"""
from __future__ import annotations

import json
import re

GENERIC_HI = ["अरे", "देखो", "सुनो", "भाई", "यार", "सच", "क्यों", "कैसे", "मत",
              "पहली बार", "सबसे बड़ा", "पागल", "गलती"]
DRAMA_HI = ["लड़ाई", "झगड़ा", "गाली", "गुस्सा", "चिल्ला", "बदतमीजी", "पुलिस",
            "चोरी", "डर", "रो", "आंसू", "शिकायत", "बेइज्जती", "धोखा", "सच्चाई",
            "माफी", "दुश्मनी", "खौफ", "हंगामा", "विवाद", "बहस", "तू", "औकात",
            "शर्म", "नाटक", "गेम", "दोस्ती", "प्यार", "ब्रेकअप", "सफाई"]
DRAMA_EN = ["fight", "fought", "shouting", "abuse", "police", "crying", "shocked",
            "exposed", "betrayal", "apology", "argument", "drama", "slap", "angry",
            "insane", "crazy", "nobody", "secret", "mistake", "never", "biggest",
            "truth", "actually", "wait", "listen"]
DRAMA_ES = ["pelea", "gritando", "policía", "llorando", "traición", "mentira",
            "nadie", "increíble", "secreto", "nunca", "verdad", "escucha", "espera"]

GENERIC_ES = ["mira", "escucha", "oye", "por qué", "cómo", "nunca", "primera vez",
              "lo peor", "lo mejor", "increíble", "no vas a creer"]

# Every genre carries all three lexicons: a Spanish vlog and a Hindi vlog score on the
# same genre key, and bilingual sources (Hinglish, Spanglish) hit both lists.
GENRES = {
    "vlog": GENERIC_HI + GENERIC_ES + DRAMA_HI[:12] + DRAMA_EN[:12] + DRAMA_ES[:8],
    "reality": GENERIC_HI + GENERIC_ES + DRAMA_HI + DRAMA_EN + DRAMA_ES,
    "gaming": DRAMA_EN + DRAMA_ES[:6] + ["clutch", "insane", "glitch", "leak",
                                          "update", "trailer", "tramposo", "partida"],
    "news": DRAMA_EN + DRAMA_ES + DRAMA_HI[:10] + ["breaking", "exclusive", "report",
                                                    "alert", "última hora", "exclusiva"],
}

SYSTEM = """You are a short-form editor. You get a numbered menu of candidate
clips from one video, each with its id, timestamps and transcript.
Pick the {n} most likely to stop the scroll on Shorts/Reels/TikTok: a strong hook,
conflict, a surprising number, a punchline, or an emotional beat. Avoid rambling
setup and anything that only makes sense with missing context.
For each pick also write a 3-6 word on-screen title with 1-2 fitting emoji, in the
same language as the transcript.
Return ONLY JSON: {{"clips":[{{"id":int,"title":str,"score":int}}]}}"""


def _lines(words: list[dict], gap: float = 0.7) -> list[dict]:
    """Group words into pause-delimited lines; these are our cut candidates."""
    out, cur = [], []
    for w in words:
        if cur and w["start"] - cur[-1]["end"] > gap:
            out.append({"start": cur[0]["start"], "end": cur[-1]["end"],
                        "text": " ".join(x["word"] for x in cur)})
            cur = []
        cur.append(w)
    if cur:
        out.append({"start": cur[0]["start"], "end": cur[-1]["end"],
                    "text": " ".join(x["word"] for x in cur)})
    return out


def _clamp(c: dict, words: list[dict], hi: float) -> dict:
    """Hard-cap a candidate at `hi` seconds, snapped to a word boundary.

    Auto-captions often run for minutes without a pause longer than the grouping gap,
    so a single "line" can be 130 s. Without this, max_clip_s is silently ignored and
    you get a 2-minute "short".
    """
    if c["end"] - c["start"] <= hi:
        return c
    limit = c["start"] + hi
    ends = [w["end"] for w in words if c["start"] < w["end"] <= limit]
    c = dict(c, end=round(ends[-1] if ends else limit, 2))
    return c


def _candidates(words: list[dict], genre: str = "vlog",
                lo: float = 18.0, hi: float = 58.0) -> list[dict]:
    """Every plausible clip window, scored by the genre lexicon, best first."""
    lex = [k.lower() for k in GENRES.get(genre, GENRES["vlog"])]
    lines = _lines(words)
    cands = []
    for i, ln in enumerate(lines):
        start = ln["start"]
        j, end = i, ln["end"]
        while end - start < lo and j + 1 < len(lines):
            j += 1
            end = lines[j]["end"]
        if end - start < lo * 0.6:
            continue
        while end - start > hi and j > i:
            j -= 1
            end = lines[j]["end"]
        text = " ".join(x["text"] for x in lines[i:j + 1])
        low = text.lower()
        dur = max(end - start, 1e-6)
        nwords = len(text.split())
        score = (4.0 * sum(k in low for k in lex)
                 + 2.0 * low.count("?")
                 + 1.5 * len(re.findall(r"\b\d[\d,.]*\b", text))
                 + min(nwords / dur, 4.0)
                 + (2.0 if text.rstrip().endswith((".", "!", "?", "।")) else 0.0))
        cands.append({"start": round(start, 2), "end": round(end, 2),
                      "score": round(score, 2), "hook": lines[i]["text"][:90],
                      "text": text})
    cands.sort(key=lambda c: -c["score"])
    return [_clamp(c, words, hi) for c in cands]


def _pick_spread(cands: list[dict], n: int) -> list[dict]:
    """Top-scoring, non-overlapping."""
    picked: list[dict] = []
    for c in cands:
        if all(c["end"] <= p["start"] or c["start"] >= p["end"] for p in picked):
            picked.append(c)
        if len(picked) == n:
            break
    return picked


def lexicon_select(words: list[dict], n: int = 2, genre: str = "vlog",
                   lo: float = 18.0, hi: float = 58.0) -> list[dict]:
    cands = _candidates(words, genre, lo, hi)
    picked: list[dict] = []
    for c in cands:
        if all(c["end"] <= p["start"] or c["start"] >= p["end"] for p in picked):
            picked.append(c)
        if len(picked) == n:
            break
    picked.sort(key=lambda c: c["start"])
    return picked


def llm_select(words: list[dict], n: int = 2, lo: float = 18.0, hi: float = 58.0,
               model: str = "gpt-4o-mini", api_key: str | None = None,
               base_url: str | None = None, genre: str = "vlog",
               shortlist: int = 14, max_chars: int = 320) -> list[dict]:
    """Rank a lexicon shortlist with an LLM, instead of sending the whole transcript.

    Works with any OpenAI-compatible endpoint. Groq is free (no card):
        export GROQ_API_KEY=gsk_...

    A 53-minute episode is ~40 k characters, which blows past Groq's free
    8 000 tokens/minute limit (HTTP 413). So we score every window locally
    first, then ask the model to judge only the best `shortlist` of them.
    That keeps a request near ~2 k tokens for any video length, and the model
    gets to compare real candidates rather than skim an entire transcript.
    """
    from openai import OpenAI

    cands = _pick_spread(_candidates(words, genre, lo, hi), shortlist)
    if not cands:
        return []
    menu = "\n".join(
        f"[{i}] {c['start']:.0f}-{c['end']:.0f}s  {c['text'][:max_chars]}"
        for i, c in enumerate(cands))

    r = OpenAI(api_key=api_key, base_url=base_url).chat.completions.create(
        model=model, response_format={"type": "json_object"}, temperature=0.4,
        messages=[{"role": "system", "content": SYSTEM.format(n=n)},
                  {"role": "user", "content": menu}])
    data = json.loads(r.choices[0].message.content)

    out = []
    for item in data.get("clips", [])[:n]:
        try:
            c = cands[int(item["id"])]
        except (KeyError, ValueError, IndexError, TypeError):
            continue
        out.append({**c, "title": item.get("title") or "",
                    "score": item.get("score", c.get("score", 0))})
    out.sort(key=lambda c: c["start"])
    return out or _pick_spread(cands, n)


def select(words: list[dict], n: int = 2, genre: str = "vlog", lo: float = 18.0,
           hi: float = 58.0, api_key: str | None = None, model: str = "gpt-4o-mini",
           base_url: str | None = None) -> list[dict]:
    if api_key:
        try:
            return [_clamp(c, words, hi)
                    for c in llm_select(words, n, lo, hi, model, api_key,
                                        base_url, genre)]
        except Exception as exc:  # noqa: BLE001
            print(f"[hooks] LLM failed ({exc}); using lexicon scorer")
    return lexicon_select(words, n, genre, lo, hi)
