"""
Cinematic Documentary Voiceover Engine.
Supports:
1. ElevenLabs API (Industry-standard documentary voices with custom stability/style tuning)
2. Edge-TTS (Free fallback with deep neural voices)
3. Sentence & Word level timestamp cues for kinetic subtitles
"""
from __future__ import annotations

import asyncio
import base64
import json
import os
import re
from pathlib import Path
from typing import Any
import requests
import edge_tts


# Curated ElevenLabs Voice IDs (The Best for Crime / Mystery / Documentaries)
ELEVENLABS_VOICES = {
    "adam": "pNInz6obpgDQGcFmaJgB",        # Deep gravelly baritone, undisputed documentary king
    "marcus": "FGY2WhTYpPnrIDTdsKH5",      # Authoritative, investigative journalist tone
    "george": "JBFqnCBsd6RMkjVDRZzb",      # British declassified archival tone
    "antoni": "ErXwobaYiN019PkySvjV",      # Smooth, cinematic storyteller
    "callum": "N2lVS1w4EtoT3dr4eOWO",      # Gritty, intense thriller edge
}

# Fine-Tuned Voice Settings for Documentary Tension:
# - Stability 0.38 (Lower stability gives natural human emotion, vocal fry, and dramatic tension)
# - Similarity 0.85 (High clarity, clean pronunciation)
# - Style 0.20 (Subtle dramatic weight without over-acting)
DOCUMENTARY_VOICE_SETTINGS = {
    "stability": 0.38,
    "similarity_boost": 0.85,
    "style": 0.20,
    "use_speaker_boost": True,
}

# Free Edge-TTS fallback profiles
EDGE_VOICE_PROFILES = {
    "deep_narrator": "en-US-ChristopherNeural",   # Deep, authoritative
    "dramatic_story": "en-US-BrianNeural",          # Gritty, engaging
    "mysterious": "en-GB-RyanNeural",              # British declassified archive style
    "hindi_deep": "hi-IN-MadhurNeural",             # Authoritative Hindi documentary
}


def _get_elevenlabs_api_key() -> str | None:
    """Checks environment variables and local .env for ElevenLabs key."""
    key = os.getenv("ELEVENLABS_API_KEY") or os.getenv("XI_API_KEY")
    if key:
        return key.strip()

    env_paths = [Path("d:/facts_yt/.env"), (Path(__file__).resolve().parent / ".env")]
    for p in env_paths:
        if p.exists():
            for line in p.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line.startswith("#"):
                    continue
                if line.startswith("ELEVENLABS_API_KEY=") or line.startswith("XI_API_KEY="):
                    val = line.split("=", 1)[1].strip().strip('"').strip("'")
                    if val:
                        return val
    return None


def synthesize_elevenlabs(
    text: str,
    output_audio: Path,
    voice_name: str = "adam",
    api_key: str | None = None,
    settings: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """
    Synthesizes speech using ElevenLabs API with timestamp metadata.
    """
    api_key = api_key or _get_elevenlabs_api_key()
    if not api_key:
        raise ValueError("ElevenLabs API Key not found.")

    voice_id = ELEVENLABS_VOICES.get(voice_name.lower(), voice_name)
    voice_settings = settings or DOCUMENTARY_VOICE_SETTINGS

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/with-timestamps"
    headers = {
        "xi-api-key": api_key,
        "Content-Type": "application/json",
    }
    payload = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": voice_settings,
    }

    res = requests.post(url, headers=headers, json=payload, timeout=30)
    if res.status_code != 200:
        # Fallback to standard endpoint if with-timestamps is unavailable on tier
        fallback_url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        res = requests.post(fallback_url, headers=headers, json=payload, timeout=30)
        if res.status_code != 200:
            raise RuntimeError(f"ElevenLabs synthesis failed: {res.status_code} {res.text[:200]}")
        output_audio.write_bytes(res.content)
        # Approximate sentence cues
        return _approximate_sentence_cues(text, output_audio)

    data = res.json()
    audio_base64 = data.get("audio_base64")
    if audio_base64:
        output_audio.write_bytes(base64.b64decode(audio_base64))

    # Parse character/word alignment timestamps into sentences
    alignment = data.get("alignment", {})
    cues = _parse_alignment_to_sentences(text, alignment)
    if not cues:
        cues = _approximate_sentence_cues(text, output_audio)
    return cues


def _parse_alignment_to_sentences(text: str, alignment: dict[str, Any]) -> list[dict[str, Any]]:
    """Parses ElevenLabs character timestamps into sentence boundaries."""
    chars = alignment.get("characters", [])
    starts = alignment.get("character_start_times_seconds", [])
    ends = alignment.get("character_end_times_seconds", [])
    if not chars or not starts:
        return []

    # Segment text by punctuation [.?!]
    sentences = [s.strip() for s in re.split(r"(?<=[.?!])\s+", text) if s.strip()]
    cues = []
    char_idx = 0
    total_chars = len(chars)

    for s in sentences:
        s_len = len(s)
        # Find start time
        start_time = starts[min(char_idx, total_chars - 1)]
        # Advance idx
        char_idx += s_len
        end_time = ends[min(char_idx - 1, total_chars - 1)]
        cues.append({
            "text": s,
            "start": round(start_time, 3),
            "end": round(end_time, 3),
            "duration": round(end_time - start_time, 3)
        })
    return cues


def _approximate_sentence_cues(text: str, audio_file: Path) -> list[dict[str, Any]]:
    """Approximates sentence timestamps based on audio duration and word counts."""
    import subprocess
    probe_cmd = [
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(audio_file)
    ]
    res = subprocess.run(probe_cmd, capture_output=True, text=True)
    total_dur = float(res.stdout.strip() or "15.0")

    sentences = [s.strip() for s in re.split(r"(?<=[.?!])\s+", text) if s.strip()]
    total_words = sum(len(s.split()) for s in sentences) or 1

    cues = []
    current_t = 0.1
    for s in sentences:
        w_count = len(s.split())
        s_dur = (w_count / total_words) * (total_dur - 0.2)
        cues.append({
            "text": s,
            "start": round(current_t, 3),
            "end": round(current_t + s_dur, 3),
            "duration": round(s_dur, 3)
        })
        current_t += s_dur
    return cues


async def _synthesize_edge_async(
    text: str,
    output_audio: Path,
    voice: str = "en-US-ChristopherNeural",
    rate: str = "-4%",
    pitch: str = "-2Hz",
) -> list[dict[str, Any]]:
    communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
    cues = []
    with open(output_audio, "wb") as f_out:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                f_out.write(chunk["data"])
            elif chunk["type"] == "SentenceBoundary":
                start_sec = chunk["offset"] / 10_000_000.0
                dur_sec = chunk["duration"] / 10_000_000.0
                cues.append({
                    "text": chunk["text"],
                    "start": round(start_sec, 3),
                    "end": round(start_sec + dur_sec, 3),
                    "duration": round(dur_sec, 3)
                })
    return cues


def generate_voiceover(
    script_text: str,
    output_audio: Path,
    provider: str = "auto",  # "auto", "elevenlabs", or "edge"
    voice_name: str = "adam",
    elevenlabs_settings: dict[str, Any] | None = None,
) -> tuple[Path, list[dict[str, Any]]]:
    """
    Master voice generator:
    - If ElevenLabs API key is present and provider != "edge", uses ElevenLabs!
    - Otherwise falls back to Edge-TTS automatically.
    """
    output_audio = Path(output_audio)
    output_audio.parent.mkdir(parents=True, exist_ok=True)

    eleven_key = _get_elevenlabs_api_key()
    cues = []

    if provider in ["auto", "elevenlabs"] and eleven_key:
        print(f">> [ElevenLabs] Synthesizing with voice [{voice_name.upper()}]...")
        try:
            cues = synthesize_elevenlabs(
                text=script_text,
                output_audio=output_audio,
                voice_name=voice_name,
                api_key=eleven_key,
                settings=elevenlabs_settings,
            )
            print(f">> [ElevenLabs] Narration ready: {output_audio.name}")
        except Exception as e:
            print(f">> [ElevenLabs Error] {e}. Falling back to Edge-TTS...")
            cues = []

    if provider in ["kokoro", "auto"] and (voice_name in ["hm_omega", "hindi_deep", "kokoro"] or "hindi" in voice_name.lower()):
        try:
            print(f">> [Kokoro-82M] Synthesizing Hindi/Hinglish narration with [hm_omega] at 0.85x...")
            from kokoro import KPipeline
            import soundfile as sf
            import numpy as np
            pipeline = KPipeline(lang_code='h')
            generator = pipeline(script_text, voice='hm_omega', speed=0.85, split_pattern=r'\n+')
            audio_chunks = []
            cues = []
            curr_time = 0.0
            for i, (gs, ps, audio) in enumerate(generator):
                audio_chunks.append(audio)
                dur = len(audio) / 24000.0
                cues.append({
                    "text": gs,
                    "start": round(curr_time, 3),
                    "end": round(curr_time + dur, 3),
                    "duration": round(dur, 3)
                })
                curr_time += dur
            if audio_chunks:
                full_audio = np.concatenate(audio_chunks)
                sf.write(str(output_audio), full_audio, 24000)
                print(f">> [Kokoro-82M] Narration ready: {output_audio.name} ({curr_time:.1f}s)")
        except Exception as e:
            print(f">> [Kokoro-82M Notice] {e}. Falling back...")
            cues = []

    if not cues:
        # Edge-TTS Fallback
        edge_voice = EDGE_VOICE_PROFILES.get(voice_name, EDGE_VOICE_PROFILES.get("hindi_deep", "hi-IN-MadhurNeural"))
        print(f">> [Edge-TTS] Synthesizing with voice [{edge_voice}]...")
        cues = asyncio.run(_synthesize_edge_async(
            text=script_text,
            output_audio=output_audio,
            voice=edge_voice,
            rate="-8%",
            pitch="-2Hz",
        ))

    cues_json = output_audio.with_suffix(".cues.json")
    cues_json.write_text(json.dumps(cues, indent=2), encoding="utf-8")
    return output_audio, cues


if __name__ == "__main__":
    sample = "Over eleven thousand years ago, an advanced civilization vanished without a trace."
    out = (Path(__file__).resolve().parent / "output/test_voice_engine.mp3")
    generate_voiceover(sample, out, voice_name="adam")
    print(f">> Done: {out}")
