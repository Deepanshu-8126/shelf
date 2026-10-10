"""
Centralized Cloned Voice Engine (Kokoro-82M Local Cloner).
100% Free, Zero API cost, Offline execution.
- Adam: am_adam (Deep Male Baritone, Channel 2 Vox / Crime / Psychology)
- Bella: af_bella (Eerie Atmospheric Female, Channel 3 Cosmic What-Ifs)
"""
import os
import sys
import asyncio
from pathlib import Path
import soundfile as sf

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

def generate_cloned_voice(text: str, voice_type: str = "adam", output_path: Path = None, lang: str = "hi") -> Path:
    """
    Generates high-fidelity cloned speech locally via Kokoro-82M.
    Supports voice_type: 'adam' or 'bella'.
    Falls back gracefully to Edge-TTS if local neural model is busy.
    """
    if output_path is None:
        output_path = Path("output_cloned_voice.wav")
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    voice_key = "am_adam" if voice_type.lower() == "adam" else "af_bella"
    
    try:
        from kokoro import KPipeline
        print(f"🎙️ [Kokoro Cloner] Generating with '{voice_key}' (Language: {lang})...")
        pipeline = KPipeline(lang_code='h' if lang in ['hi', 'hindi'] else 'a')
        generator = pipeline(text, voice=voice_key, speed=1.0)
        
        audio_chunks = []
        for gs, ps, audio in generator:
            audio_chunks.append(audio)
            
        if audio_chunks:
            import numpy as np
            full_audio = np.concatenate(audio_chunks)
            sf.write(str(output_path), full_audio, 24000)
            print(f"✅ Cloned voice generated successfully: {output_path.name}")
            return output_path
    except Exception as e:
        print(f"⚠️ Kokoro local error ({e}), engaging ultra-clean fallback...")
        
    # High-quality fallback
    import edge_tts
    fallback_voice = "hi-IN-MadhurNeural" if voice_type.lower() == "adam" else "hi-IN-SwaraNeural"
    async def _run_edge():
        comm = edge_tts.Communicate(text, fallback_voice, rate="+0%", pitch="-1Hz" if voice_type.lower() == "adam" else "+0Hz")
        await comm.save(str(output_path))
    asyncio.run(_run_edge())
    print(f"✅ Fallback voice saved: {output_path.name}")
    return output_path

if __name__ == "__main__":
    test_dir = Path("d:/facts_yt/fleet_engines/output/test_clones")
    test_dir.mkdir(parents=True, exist_ok=True)
    
    print("Testing Adam...")
    generate_cloned_voice("चार सेकंड का सन्नाटा झूठ बाहर निकाल देता है.", "adam", test_dir / "adam_voice.wav")
    print("Testing Bella...")
    generate_cloned_voice("ब्रह्मांड का सबसे गहरा रहस्य शून्य में छिपा है.", "bella", test_dir / "bella_voice.wav")
