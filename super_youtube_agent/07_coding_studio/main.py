"""
Channel 7 — Pedagogical Coding & Tech Studio.
Generates viral programming shorts, DSA patterns, LeetCode walkthroughs, and Python traps.
Completely standalone and decoupled from 01_facts_shorts.
"""
import argparse
import asyncio
import os
import sys
from pathlib import Path

# Add self to path
CURRENT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(CURRENT_DIR))

from vox_coding_studio import render_coding_short


def main():
    parser = argparse.ArgumentParser(description="Channel 7 Pedagogical Coding Studio")
    parser.add_argument("--topic", type=str, default="", help="Coding topic or LeetCode question")
    parser.add_argument("--lesson", type=str, default="", help="Specific lesson ID")
    parser.add_argument("--generate", action="store_true", help="Generate coding short")
    parser.add_argument("--mode", type=str, default="story", help="Video mode")
    parser.add_argument("--niche", type=str, default="coding", help="Niche")

    args = parser.parse_args()

    topic_query = args.topic or args.lesson or os.getenv("TOPIC_INPUT") or os.getenv("TOPIC") or ""
    print(f"🎬 [Channel 7 CLI] Starting generation with query: '{topic_query}'")

    out_video = asyncio.run(render_coding_short(topic_query if topic_query.strip() else None))
    print(f"✅ Video ready: {out_video}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
