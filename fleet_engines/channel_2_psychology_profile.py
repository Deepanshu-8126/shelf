"""
Channel 2 Production Profile: Dark Psychology & Bizarre Hindi Facts.
Engine: MoneyPrinterTurbo Bridge.
Zero pollution to internal repos — runs as clean external launcher.
"""
import json
import os
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

FLEET_DIR = Path(__file__).resolve().parent
WORKSPACE_ROOT = FLEET_DIR.parent
MONEYPRINTER_DIR = FLEET_DIR / "MoneyPrinterTurbo"
OUTPUT_DIR = FLEET_DIR / "output" / "channel_2_facts"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Curated High-Retention Hindi Dark Psychology Topics
VIRAL_PSYCHOLOGY_HOOKS = [
    {
        "hook": "Agar koi insaan aapse baat karte waqt nazar nahi mila raha, toh Dark Psychology kehti hai...",
        "topic": "Eye Contact Psychology Tricks",
        "keywords": ["dark psychology", "human behavior", "body language", "secrets"]
    },
    {
        "hook": "Duniya ka sabse khatarnak psychological trick jo log anjaane me aap par use karte hain...",
        "topic": "Reverse Psychology Manipulation",
        "keywords": ["mind tricks", "psychology facts", "brain hacks"]
    },
    {
        "hook": "99% log ye nahi jaante ki jab koi aapse jhooth bolta hai, toh uska shareer ye 3 signals deta hai...",
        "topic": "Lie Detection Micro Expressions",
        "keywords": ["detect lies", "fbi interrogation", "psychology"]
    },
    {
        "hook": "Marcus Aurelius ka wo 1 stoic rule jo aapke dimaag se overthinking ko 10 second me mita dega...",
        "topic": "Stoic Mindset vs Overthinking",
        "keywords": ["stoicism", "mental strength", "wisdom", "motivation"]
    }
]

def get_channel_2_config():
    return {
        "channel_id": 2,
        "niche": "dark_psychology_facts",
        "target_audience": "Mass Indian Hindi Audience (Rapid Viral Reach)",
        "language": "hi",
        "voice": "hindi_deep_stoic",
        "background_visuals": "4k_pexels_cinematic_moody",
        "caption_style": "hindi_devnagari_active_highlight",
        "output_dir": str(OUTPUT_DIR)
    }

def generate_psychology_facts_short(custom_topic: str = ""):
    import random
    cfg = get_channel_2_config()
    chosen_item = random.choice(VIRAL_PSYCHOLOGY_HOOKS)
    hook = chosen_item["hook"] if not custom_topic else custom_topic
    
    print("=" * 70)
    print("⚡ [CHANNEL 2 PRODUCTION: DARK PSYCHOLOGY & HINDI FACTS]")
    print(f"📖 Hook: \"{hook}\"")
    print(f"🎯 Target Audience: {cfg['target_audience']}")
    print(f"🎞️ Visual Style: {cfg['background_visuals']}")
    print(f"📁 Output Directory: {OUTPUT_DIR}")
    print("=" * 70)
    
    slug = "".join([c if c.isalnum() else "_" for c in chosen_item["topic"][:24]]).strip("_")
    brief = {
        "hook": hook,
        "topic": chosen_item["topic"],
        "engine": "MoneyPrinterTurbo",
        "channel": 2,
        "language": "hi",
        "niche": "dark_psychology",
        "captions": cfg["caption_style"],
        "voice": cfg["voice"]
    }
    brief_file = OUTPUT_DIR / f"{slug}_brief.json"
    brief_file.write_text(json.dumps(brief, indent=2), encoding="utf-8")
    print(f"✓ Production brief ready: {brief_file.name}")
    return brief

if __name__ == "__main__":
    topic_arg = sys.argv[1] if len(sys.argv) > 1 else ""
    generate_psychology_facts_short(topic_arg)
