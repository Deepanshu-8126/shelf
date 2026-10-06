"""
Channel 7 — Coding & Tech Studio
Generates viral programming shorts, Python/JS hacks, AI tool breakdowns, and dev tutorials.
"""
import os
import sys
from pathlib import Path

# Add 01_facts_shorts to path
CURRENT_DIR = Path(__file__).resolve().parent
ROOT_DIR = CURRENT_DIR.parent
FACTS_SHORTS_DIR = ROOT_DIR / "01_facts_shorts"
sys.path.insert(0, str(FACTS_SHORTS_DIR))

# Ensure credentials point to token_coding.json if token.json is not present
os.environ["NICHE"] = "coding"
os.environ["VIDEO_MODE"] = os.getenv("VIDEO_MODE", "story")
os.environ["SCRIPT_STYLE"] = os.getenv("SCRIPT_STYLE", "punchy")

if __name__ == "__main__":
    from main import main
    # Pass along any CLI arguments or default to generating a coding short
    args = sys.argv[1:] if len(sys.argv) > 1 else ["--generate", "--niche", "coding", "--mode", "story"]
    sys.exit(main(args))
