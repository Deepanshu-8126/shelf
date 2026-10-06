"""
Suspenseful True Crime Voiceover Engine.
Powered by Kokoro-82M Hindi hm_omega (Speed: 0.85x, Netflix Crime Doc tone) with Edge-TTS fallback.
"""
from __future__ import annotations

import asyncio
from pathlib import Path
import soundfile as sf
import numpy as np


def generate_crime_voiceover(
    script_text: str,
    output_path: Path | str,
    voice: str = "hm_omega",
    speed: float = 0.85,
    lang: str = "h",
) -> tuple[Path, float]:
    """
    Synthesizes deep, slow, suspenseful true-crime narration.
    Returns (output_path, duration_seconds).
    """
    out_p = Path(output_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)

    # 1. Try Kokoro-82M Native Hindi Pipeline
    try:
        from kokoro import KPipeline
        pipeline = KPipeline(lang_code=lang)
        generator = pipeline(script_text, voice=voice, speed=speed, split_pattern=r"\n+")
        audio_chunks = []
        for _, _, chunk in generator:
            audio_chunks.append(chunk)

        if audio_chunks:
            full_audio = np.concatenate(audio_chunks)
            sf.write(str(out_p), full_audio, 24000)
            dur = len(full_audio) / 24000.0
            return out_p, dur
    except Exception as exc:
        print(f"⚠️ Kokoro local synthesis fell back to Edge-TTS: {exc}")

    # 2. Fallback to Edge-TTS hi-IN-MadhurNeural
    async def _fallback_edge():
        import edge_tts
        comm = edge_tts.Communicate(script_text, "hi-IN-MadhurNeural", rate="-10%", pitch="-3Hz")
        await comm.save(str(out_p))

    asyncio.run(_fallback_edge())
    
    # Calculate duration
    try:
        import soundfile as sf
        info = sf.info(str(out_p))
        return out_p, info.duration
    except Exception:
        return out_p, 45.0
