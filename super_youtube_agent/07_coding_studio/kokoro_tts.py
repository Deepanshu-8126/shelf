import sys
import os
from pathlib import Path
from typing import Tuple, List
import soundfile as sf
import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

_pipeline_cache = {}

def get_kokoro_pipeline(lang_code: str = 'h'):
    global _pipeline_cache
    if lang_code not in _pipeline_cache:
        from kokoro import KPipeline
        print(f"🎙️ [Kokoro Engine] Initializing Kokoro Pipeline for language '{lang_code}'...")
        _pipeline_cache[lang_code] = KPipeline(lang_code=lang_code)
    return _pipeline_cache[lang_code]


def generate_kokoro_narration(
    text: str,
    output_wav: Path,
    lang: str = "hi",
    voice: str = "hm_omega",
    speed: float = 0.94
) -> Tuple[Path, float]:
    """
    Generates natural voiceover using Kokoro-82M.
    lang='h' for Hindi (voices: hm_omega, hm_psi, hf_alpha, hf_beta)
    lang='a' for English (voices: am_adam, am_echo, af_bella, af_nicole)
    """
    lang_code = 'h' if lang.lower().startswith('hi') else 'a'
    
    # Sensible voice defaults
    if lang_code == 'h' and not voice.startswith('h'):
        voice = 'hm_omega'
    elif lang_code == 'a' and not voice.startswith('a'):
        voice = 'am_adam'

    pipeline = get_kokoro_pipeline(lang_code)
    
    print(f"🎙️ [Kokoro Engine] Synthesizing speech ({voice}, speed={speed})...")
    generator = pipeline(text, voice=voice, speed=speed)
    
    audio_chunks: List[np.ndarray] = []
    for _, _, audio in generator:
        if audio is not None and len(audio) > 0:
            audio_chunks.append(audio)

    if not audio_chunks:
        raise RuntimeError("Kokoro generation produced empty audio chunks.")

    full_audio = np.concatenate(audio_chunks)
    sample_rate = 24000

    output_wav.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(output_wav), full_audio, sample_rate)
    duration = len(full_audio) / float(sample_rate)

    print(f"✅ [Kokoro Engine] Rendered {duration:.2f}s audio -> {output_wav}")
    return output_wav, duration
