"""
Cinematic Documentary Voiceover Engine.
Powered by Edge-TTS (Free, high-fidelity neural voices) with ElevenLabs support.
Generates:
- High-fidelity voice narration MP3
- Sentence-level timestamps for kinetic caption synchronization
- Support for dramatic pauses and pacing
"""
from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any
import edge_tts


# Curated documentary voices
VOICE_PROFILES = {
    "deep_narrator": "en-US-ChristopherNeural",   # Deep, authoritative, investigation style
    "dramatic_story": "en-US-BrianNeural",          # Gritty, engaging crime storytelling
    "mysterious": "en-GB-RyanNeural",              # British declassified archive style
    "hindi_deep": "hi-IN-MadhurNeural",             # Authoritative Hindi documentary
}


async def _synthesize_edge_async(
    text: str,
    output_audio: Path,
    voice: str = "en-US-ChristopherNeural",
    rate: str = "-4%",  # Slightly slower for dramatic suspense
    pitch: str = "-2Hz", # Slightly deeper
) -> list[dict[str, Any]]:
    """Synthesizes speech and records sentence boundaries."""
    communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
    cues = []
    
    with open(output_audio, "wb") as f_out:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                f_out.write(chunk["data"])
            elif chunk["type"] == "SentenceBoundary":
                # offset and duration are in 100-nanoseconds (10,000,000 = 1s)
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
    voice_key: str = "deep_narrator",
    rate: str = "-4%",
    pitch: str = "-2Hz"
) -> tuple[Path, list[dict[str, Any]]]:
    """
    Synchronous wrapper to generate documentary voiceover and timing metadata.
    """
    output_audio = Path(output_audio)
    output_audio.parent.mkdir(parents=True, exist_ok=True)
    voice = VOICE_PROFILES.get(voice_key, voice_key)

    cues = asyncio.run(_synthesize_edge_async(
        text=script_text,
        output_audio=output_audio,
        voice=voice,
        rate=rate,
        pitch=pitch,
    ))

    # Save timing cues to JSON
    cues_json = output_audio.with_suffix(".cues.json")
    cues_json.write_text(json.dumps(cues, indent=2), encoding="utf-8")
    print(f">> Voiceover generated: {output_audio}")
    print(f">> Cues recorded: {len(cues)} sentences in {cues_json.name}")
    return output_audio, cues


if __name__ == "__main__":
    sample_script = (
        "October 1999. Deep in the freezing Russian steppes, "
        "a maximum security colony was reinforced with a single mandate. "
        "Not a single prisoner has ever escaped."
    )
    out_mp3 = Path("d:/facts_yt/dark_case_studio/output/test_voice.mp3")
    generate_voiceover(sample_script, out_mp3)
