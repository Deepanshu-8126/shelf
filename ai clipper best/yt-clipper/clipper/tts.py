"""Step 4 - translation + Edge-TTS voiceover with word timings.

Edge-TTS streams WordBoundary events, so we get word-level timestamps for the
*dubbed* audio for free - no second Whisper pass needed for caption sync.
"""
from __future__ import annotations

import asyncio
from pathlib import Path

from .config import VOICES, settings


def translate(text: str, target: str) -> str:
    """EN<->ES translation. Uses the LLM if a key exists, else returns text unchanged."""
    if not settings.llm_api_key:
        return text
    from openai import OpenAI

    names = {"en": "English", "es": "Spanish (neutral Latin-American)"}
    client = OpenAI(api_key=settings.llm_api_key)
    r = client.chat.completions.create(
        model=settings.llm_model,
        temperature=0.2,
        messages=[
            {"role": "system", "content":
             f"Translate to {names.get(target, target)}. Keep it punchy and spoken-style, "
             f"same length or shorter. Output only the translation."},
            {"role": "user", "content": text},
        ],
    )
    return r.choices[0].message.content.strip()


async def _speak(text: str, voice: str, out: Path, rate: str, pitch: str):
    import edge_tts

    # edge-tts >= 7.x defaults to SentenceBoundary; we need per-word timings for
    # karaoke captions. Older versions have no `boundary` kwarg and emit words.
    try:
        comm = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch,
                                    boundary="WordBoundary")
    except TypeError:
        comm = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
    words: list[dict] = []
    with open(out, "wb") as f:
        async for chunk in comm.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                words.append({
                    "word": chunk["text"],
                    "start": round(chunk["offset"] / 1e7, 3),            # 100ns ticks -> s
                    "end": round((chunk["offset"] + chunk["duration"]) / 1e7, 3),
                })
    return words


def _restore_punctuation(words: list[dict], source: str) -> list[dict]:
    """Edge-TTS WordBoundary strips punctuation; walk the source text to put it back
    so captions read '...resets.' instead of '...resets'."""
    import re as _re

    cursor = 0
    for w in words:
        m = _re.search(_re.escape(w["word"]), source[cursor:])
        if not m:
            continue
        end = cursor + m.end()
        tail = _re.match(r"[^\w\s]+", source[end:])
        if tail:
            w["word"] += tail.group(0)
            end += tail.end()
        cursor = end
    return words


def synthesize(text: str, lang: str, out_path: str | Path,
               rate: str = "+8%", pitch: str = "+0Hz") -> dict:
    """Write mp3 at out_path. Returns {'path', 'voice', 'words':[...]}."""
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    voice = VOICES.get(lang, lang)  # pass a full voice name to override
    words = _restore_punctuation(asyncio.run(_speak(text, voice, out_path, rate, pitch)), text)
    return {"path": str(out_path), "voice": voice, "lang": lang, "words": words}


def list_voices(prefix: str = "es") -> list[str]:
    import edge_tts

    async def _go():
        return [v["ShortName"] for v in await edge_tts.list_voices()
                if v["ShortName"].startswith(prefix)]

    return asyncio.run(_go())
