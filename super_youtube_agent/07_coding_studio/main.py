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
from videosynx_renderer import render_videosynx_short


def main():
    parser = argparse.ArgumentParser(description="Channel 7 Pedagogical Coding Studio")
    parser.add_argument("--day", type=int, default=0, help="Specific Day in 100 Days of Python (e.g. 1, 7, 14)")
    parser.add_argument("--episode", type=int, default=0, help="Specific Episode number")
    parser.add_argument("--series", type=str, default="", help="Series filter (e.g. python, leetcode, tools, sysdesign)")
    parser.add_argument("--topic", type=str, default="", help="Coding topic or LeetCode question")
    parser.add_argument("--lesson", type=str, default="", help="Specific lesson ID")
    parser.add_argument("--engine", type=str, default="videosynx", choices=["videosynx", "vox"], help="Rendering engine (videosynx: line-by-line anchored, vox: 4-scene overview)")
    parser.add_argument("--auto", action="store_true", help="Autonomously curate trending topic and render")
    parser.add_argument("--next", action="store_true", help="Render next scheduled video in 100 Days / Evening series")
    parser.add_argument("--status", action="store_true", help="Show series progression status summary")
    parser.add_argument("--generate", action="store_true", help="Generate coding short")
    parser.add_argument("--mode", type=str, default="story", help="Video mode")
    parser.add_argument("--niche", type=str, default="", help="Niche filter (dsa, python, java, ai_tools, sysdesign, web_backend)")

    args = parser.parse_args()

    if args.status:
        from series_progress_tracker import get_series_status_summary
        print(get_series_status_summary())
        return 0

    topic_query = ""
    if args.next:
        from series_progress_tracker import get_next_scheduled_slot
        slot_info = get_next_scheduled_slot()
        topic_query = slot_info.get("query", "")
        print(f"📅 [Series Progression] Rendering Next Slot ({slot_info.get('slot')}): '{topic_query}'")
    elif args.auto or (args.niche and not args.topic and not args.day and not args.episode):
        from ai_curriculum_generator import curate_viral_topic
        topic_query = curate_viral_topic(args.niche)
        print(f"🤖 [Autonomous Topic Curator] Curated viral topic ({args.niche or 'any'}): '{topic_query}'")
    elif args.day > 0:
        topic_query = f"day {args.day}"
    elif args.episode > 0 and args.series:
        topic_query = f"{args.series} {args.episode}"
    elif args.series:
        topic_query = args.series
    elif args.topic:
        topic_query = args.topic
    elif args.lesson:
        topic_query = args.lesson
    else:
        topic_query = os.getenv("TOPIC_INPUT") or os.getenv("TOPIC") or ""

    print(f"🎬 [Channel 7 CLI] Starting generation with engine='{args.engine}', query='{topic_query}'")



    if args.engine == "videosynx":
        out_video = asyncio.run(render_videosynx_short(topic_query if topic_query.strip() else None))
    else:
        out_video = asyncio.run(render_coding_short(topic_query if topic_query.strip() else None))

    print(f"✅ Video ready: {out_video}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
