import asyncio
import os
import subprocess
from pathlib import Path
import edge_tts
import soundfile as sf
import numpy as np

OUTPUT_DIR = Path("d:/facts_yt/fleet_engines/output")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

test_script = (
    "क्या आपको पता है कि समंदर के 11 किलोमीटर नीचे मारियाना ट्रेंच में वैज्ञानिकों को क्या मिला? "
    "वहां का दबाव इतना भयानक है कि किसी भी इंसान की हड्डियां एक सेकंड में चकनाचूर हो जाएं, "
    "लेकिन फिर भी वहां रहस्यमयी जीव जिंदा तैर रहे हैं!"
)

# Mastering filter chain for ultra-crisp studio broadcast feel
STUDIO_AF = (
    "highpass=f=75,"
    "equalizer=f=120:width_type=h:width=80:g=2.4,"
    "equalizer=f=3400:width_type=h:width=600:g=2.5,"
    "acompressor=threshold=-16dB:ratio=3.0:attack=10:release=90,"
    "volume=1.10"
)

async def generate_edge(voice_name: str, raw_out: Path, final_out: Path):
    print(f"Generating Edge-TTS ({voice_name})...")
    communicate = edge_tts.Communicate(
        text=test_script,
        voice=voice_name,
        rate="+3%",      # Punchy pacing
        pitch="+0Hz"
    )
    await communicate.save(str(raw_out))
    
    # Apply FFmpeg Studio Mastering
    subprocess.run([
        "ffmpeg", "-y", "-i", str(raw_out),
        "-af", STUDIO_AF,
        str(final_out)
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    if raw_out.exists():
        raw_out.unlink()
    print(f"Saved: {final_out} ({final_out.stat().st_size} bytes)")

def generate_kokoro(final_out: Path):
    try:
        print("Generating Kokoro-82M Hindi...")
        from kokoro import KPipeline
        pipeline = KPipeline(lang_code='h')
        
        generator = pipeline(test_script, speed=1.0)
        all_audio = []
        for gs, ps, audio in generator:
            all_audio.append(audio)
            
        if all_audio:
            combined = np.concatenate(all_audio)
            sf.write(str(final_out), combined, 24000)
            print(f"Saved: {final_out} ({final_out.stat().st_size} bytes)")
    except Exception as e:
        print(f"Kokoro generation warning: {e}")

async def main():
    swara_raw = OUTPUT_DIR / "temp_swara.mp3"
    swara_final = OUTPUT_DIR / "sample_edge_swara_female.mp3"
    await generate_edge("hi-IN-SwaraNeural", swara_raw, swara_final)

    madhur_raw = OUTPUT_DIR / "temp_madhur.mp3"
    madhur_final = OUTPUT_DIR / "sample_edge_madhur_male.mp3"
    await generate_edge("hi-IN-MadhurNeural", madhur_raw, madhur_final)

    kokoro_final = OUTPUT_DIR / "sample_kokoro_hindi.wav"
    generate_kokoro(kokoro_final)

if __name__ == "__main__":
    asyncio.run(main())
