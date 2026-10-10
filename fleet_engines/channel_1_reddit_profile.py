"""
Channel 1 Production Profile: Reddit Drama & Crazy Confessions.
Engine: ShortGPT Bridge.
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
SHORTGPT_DIR = FLEET_DIR / "ShortGPT"
OUTPUT_DIR = FLEET_DIR / "output" / "channel_1_reddit"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Curated Viral Subreddits & Sample Hooks
VIRAL_REDDIT_HOOKS = [
    "AITA for canceling my wedding 3 days before after finding my fiancé's secret notebook?",
    "My best friend gave me a key to his house, but I discovered a hidden room in the basement...",
    "I took a DNA test for fun and accidentally exposed a 25-year family secret.",
    "AITA for exposing my boss in front of the entire company after he stole my promotion?",
    "My neighbor kept complaining about noise, so I set up a hidden camera and caught this..."
]

def get_channel_1_config():
    return {
        "channel_id": 1,
        "niche": "reddit_drama",
        "target_audience": "US / UK / Global English (High Dollar RPM)",
        "language": "en",
        "voice": "en_us_001",
        "background_gameplay": "minecraft_parkour",
        "caption_style": "mrbeast_bouncy_yellow",
        "output_dir": str(OUTPUT_DIR)
    }

def generate_reddit_drama_short(custom_story: str = ""):
    import random
    cfg = get_channel_1_config()
    chosen_hook = custom_story or random.choice(VIRAL_REDDIT_HOOKS)
    
    print("=" * 70)
    print("🎭 [CHANNEL 1 PRODUCTION: REDDIT DRAMA & CONFESSIONS]")
    print(f"📖 Hook: \"{chosen_hook}\"")
    print(f"🎯 Target Audience: {cfg['target_audience']}")
    print(f"🎮 Background Gameplay: {cfg['background_gameplay']}")
    print(f"📁 Output Directory: {OUTPUT_DIR}")
    print("=" * 70)
    
    # Save production brief
    slug = "".join([c if c.isalnum() else "_" for c in chosen_hook[:24]]).strip("_")
    brief = {
        "hook": chosen_hook,
        "engine": "ShortGPT",
        "channel": 1,
        "niche": "reddit_drama",
        "captions": cfg["caption_style"],
        "voice": cfg["voice"]
    }
    brief_file = OUTPUT_DIR / f"{slug}_brief.json"
    brief_file.write_text(json.dumps(brief, indent=2), encoding="utf-8")
    print(f"✓ Production brief ready: {brief_file.name}")
    return brief

if __name__ == "__main__":
    story_arg = sys.argv[1] if len(sys.argv) > 1 else ""
    generate_reddit_drama_short(story_arg)
