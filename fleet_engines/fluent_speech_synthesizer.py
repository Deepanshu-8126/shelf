"""
Fluent Bi-Lingual Speech Synthesizer for Shorts & Reels.
Engineered for:
1. Dual-Language Fluency: Smooth natural Indian Hindi + Polish English technical words.
2. Micro-pause Cadence: Injects breathing pauses (commas/periods) to prevent robotic run-ons.
3. Audio Pitch & Speed Tuning: +5% speed, -2Hz pitch for punchy, high-retention narration.
"""
import asyncio
import os
import re
import sys
from pathlib import Path
from typing import Dict, Any, Optional

import edge_tts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

FLEET_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = FLEET_DIR / "output" / "audio_stems"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Curated English Technical & Psychology Words preserved cleanly
ENGLISH_TECH_WORDS = {
    "dark psychology": "Dark Psychology",
    "psychology": "Psychology",
    "overthinking": "Overthinking",
    "manipulation": "Manipulation",
    "micro expressions": "Micro Expressions",
    "fbi": "FBI",
    "stoic": "Stoic",
    "stoicism": "Stoicism",
    "signals": "Signals",
    "mindset": "Mindset",
    "brain": "Brain",
    "secret": "Secret",
    "rules": "Rules",
    "tricks": "Tricks",
    "facts": "Facts"
}

# Common Hinglish Roman to Clean Hindi Devanagari Bridge for 100% fluent pronunciation
HINGLISH_TO_DEVANAGARI_MAP = [
    (r"\bagar\b", "अगर"),
    (r"\baapse\b", "आपसे"),
    (r"\baap\b", "आप"),
    (r"\bbaat\b", "बात"),
    (r"\bkarte\b", "करते"),
    (r"\bwaqt\b", "वक्त"),
    (r"\bnazar\b", "नज़र"),
    (r"\bnahi\b", "नहीं"),
    (r"\bmila\b", "मिला"),
    (r"\braha\b", "रहा"),
    (r"\brahe\b", "रहे"),
    (r"\btoh\b", "तो"),
    (r"\bkehti\b", "कहती"),
    (r"\bkehta\b", "कहता"),
    (r"\bhai\b", "है"),
    (r"\bhain\b", "हैं"),
    (r"\bki\b", "कि"),
    (r"\bwo\b", "वो"),
    (r"\bye\b", "ये"),
    (r"\bbaatein\b", "बातें"),
    (r"\bchupa\b", "छुपा"),
    (r"\bchhupa\b", "छुपा"),
    (r"\bduniya\b", "दुनिया"),
    (r"\bka\b", "का"),
    (r"\bki\b", "की"),
    (r"\bke\b", "के"),
    (r"\bsabse\b", "सबसे"),
    (r"\bkhatarnak\b", "खतरनाक"),
    (r"\bjo\b", "जो"),
    (r"\blog\b", "लोग"),
    (r"\banjaane\b", "अनजाने"),
    (r"\bme\b", "में"),
    (r"\buse\b", "use"),
    (r"\bkisko\b", "किसको"),
    (r"\bkyu\b", "क्यों"),
    (r"\bkyun\b", "क्यों"),
    (r"\bdekho\b", "देखो"),
    (r"\bsuno\b", "सुनो"),
    (r"\bjhooth\b", "झूठ"),
    (r"\bbolta\b", "बोलता"),
    (r"\bshareer\b", "शरीर"),
    (r"\bchinta\b", "चिंता"),
    (r"\bdimaag\b", "दिमाग"),
    (r"\bmitana\b", "मिटाना"),
    (r"\bseekho\b", "सीखो")
]


def sanitize_hinglish_speech_text(text: str) -> str:
    """
    Transforms Hinglish text into a bi-lingual phonetic script:
    1. Keeps modern English technical terms (Overthinking, Dark Psychology, Mindset) intact in English.
    2. Converts Hindi connectives to clean Devanagari so EdgeTTS / Microsoft Neural speaks with 100% Indian fluency.
    3. Injects rhythmic micro-pauses (commas) for human-like breathing cadence.
    """
    cleaned = text.strip()
    
    # 1. Clean Hinglish mapping
    for pat, rep in HINGLISH_TO_DEVANAGARI_MAP:
        cleaned = re.sub(pat, rep, cleaned, flags=re.IGNORECASE)

    # 2. Add breathing pauses if long run-on sentence without punctuation
    words = cleaned.split()
    spaced_words = []
    count = 0
    for w in words:
        spaced_words.append(w)
        count += 1
        if count >= 6 and not any(p in w for p in [",", ".", "!", "?", "।"]):
            spaced_words[-1] = w + ","
            count = 0

    return " ".join(spaced_words)


async def synthesize_fluent_voice(
    text: str,
    output_path: Path,
    language: str = "hi",
    speed_boost: str = "+5%",
    pitch_mod: str = "-2Hz"
) -> Path:
    """
    Generates studio-grade non-stuttering voiceover:
    - language == 'hi': uses hi-IN-MadhurNeural (Bi-lingual Indian Narrator)
    - language == 'en': uses en-US-ChristopherNeural (US Storyteller Narrator)
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    if language == "hi":
        voice = "hi-IN-MadhurNeural"
        speech_text = sanitize_hinglish_speech_text(text)
    else:
        voice = "en-US-ChristopherNeural"
        speech_text = text

    communicate = edge_tts.Communicate(
        text=speech_text,
        voice=voice,
        rate=speed_boost,
        pitch=pitch_mod
    )
    await communicate.save(str(output_path))
    return output_path


def generate_audio_sync(text: str, output_path: str, language: str = "hi") -> str:
    p = Path(output_path)
    asyncio.run(synthesize_fluent_voice(text, p, language=language))
    return str(p)


if __name__ == "__main__":
    # Test sample
    test_hi = "Agar koi insaan aapse baat karte waqt nazar nahi mila raha, toh Dark Psychology kehti hai ki wo ye 3 baatein chhupa raha hai."
    out_file = OUTPUT_DIR / "fluent_hinglish_demo.mp3"
    print("🎙️ Synthesizing Fluent Bi-lingual Speech...")
    res = generate_audio_sync(test_hi, str(out_file), language="hi")
    print(f"✅ Master Audio Stem ready: {res} ({out_file.stat().st_size} bytes)")
