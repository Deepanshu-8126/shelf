import asyncio
from pathlib import Path
import edge_tts

out_dir = Path("output/hindi_voices")
out_dir.mkdir(parents=True, exist_ok=True)

text_hindi = (
    "क्या आप जानते हैं? अगर एक न्यूट्रॉन तारे का सिर्फ एक छोटा चम्मच टुकड़ा पृथ्वी पर लाया जाए, "
    "तो उसका वजन छह सौ करोड़ टन होगा — यानी पूरे माउंट एवरेस्ट पर्वत से भी ज्यादा भारी!"
)

text_hinglish = (
    "Did you know? Agar ek neutron star ka ek chammach piece earth par laya jaye, "
    "to uska weight 600 crore ton hoga, pure Mount Everest se bhi heavy!"
)

voices = [
    ("01_madhur_default.mp3", "hi-IN-MadhurNeural", text_hindi, "+0Hz", "+0%"),
    ("02_madhur_deep_cinematic.mp3", "hi-IN-MadhurNeural", text_hindi, "-8Hz", "+0%"),
    ("03_swara_female.mp3", "hi-IN-SwaraNeural", text_hindi, "+0Hz", "+0%"),
    ("04_salman_deep_documentary.mp3", "ur-IN-SalmanNeural", text_hindi, "-6Hz", "+0%"),
    ("05_neerja_expressive_hinglish.mp3", "en-IN-NeerjaExpressiveNeural", text_hinglish, "+0Hz", "+0%"),
    ("06_prabhat_indian_male.mp3", "en-IN-PrabhatNeural", text_hinglish, "+0Hz", "+0%"),
]

async def main():
    print("Generating Hindi voice samples...")
    for fname, vname, txt, pitch, rate in voices:
        target = out_dir / fname
        c = edge_tts.Communicate(txt, vname, pitch=pitch, rate=rate)
        await c.save(str(target))
        print(f"[OK] Generated: {target.name} ({vname}, pitch={pitch})")
    print("All 6 samples generated successfully in output/hindi_voices/")

if __name__ == "__main__":
    asyncio.run(main())
