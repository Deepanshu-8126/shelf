"""
CLI Interface for Vox Video Studio.
Usage:
    python -m vox_studio.cli create "Bermuda Triangle"
    python -m vox_studio.cli trends
"""
import argparse
import sys
from vox_studio.director import StudioDirector
from fire_crawler.trends import GoogleTrendsCrawler

# Fix Windows console UTF-8 output
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def main():
    parser = argparse.ArgumentParser(description="Vox Autonomous Video Production Studio")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Command: create
    create_parser = subparsers.add_parser("create", help="Create a Vox-style short video on a topic")
    create_parser.add_argument("topic", type=str, nargs="?", default="", help="Topic name (or leave blank for channel auto-selection)")
    create_parser.add_argument("--channel", type=str, default="custom", help="Channel target: channel_1, channel_2, channel_3, channel_4, channel_5, custom")
    create_parser.add_argument("--niche", type=str, default="dark_mystery", help="Niche profile (space_science, dark_mystery, dark_web, bizarre_history, etc.)")
    create_parser.add_argument("--voice", type=str, default="brian", help="Narrator voice (brian, marcus, adam)")
    create_parser.add_argument("--thumbnail", action="store_true", default=True, help="Render high-CTR thumbnail")

    # Command: trends
    trends_parser = subparsers.add_parser("trends", help="Fetch breakout topics and generate videos")
    trends_parser.add_argument("--limit", type=int, default=3, help="Number of trends to fetch")
    trends_parser.add_argument("--auto-produce", action="store_true", help="Automatically produce video for top trend")

    args = parser.parse_args()

    if args.command == "create":
        topic = args.topic.strip()
        channel = args.channel.lower()

        # Fallback to channel-specific viral topics if no topic provided
        if not topic:
            if "channel_1" in channel or "factshorts" in channel or "space" in channel:
                import random
                topic = random.choice([
                    "James Webb Telescope Shocking Deep Space Anomaly",
                    "Voyager 1 Mysterious Signal from Outside the Solar System",
                    "What Happens If You Fall Into a Supermassive Black Hole",
                    "The Impossible Ocean Beneath Europa's Ice Surface"
                ])
                print(f"🌌 [Channel 1 Auto-Topic Selected]: '{topic}'")
            elif "channel_2" in channel or "dark" in channel or "mystery" in channel:
                import random
                topic = random.choice([
                    "The Declassified 1945 Bermuda Triangle Flight 19 Audio",
                    "The Mystery of the Lead Masks of Vintém Hill",
                    "The Dyatlov Pass Incident: Newly Unsealed KGB Files",
                    "The Missing Malaysian Flight MH370 Satellite Coordinates"
                ])
                print(f"🕵️ [Channel 2 Auto-Topic Selected]: '{topic}'")
            elif "channel_3" in channel or "psychology" in channel:
                import random
                topic = random.choice([
                    "The Dark Psychology of Mirror Neurons",
                    "The Stanford Prison Experiment Unseen Tapes",
                    "Why Your Brain Lies to You About Memory"
                ])
                print(f"🧠 [Channel 3 Auto-Topic Selected]: '{topic}'")
            elif "channel_4" in channel or "finance" in channel:
                import random
                topic = random.choice([
                    "The Trillion Dollar Math Error That Broke Wall Street",
                    "How the 2008 Housing Crash Was Predicted by One Analyst",
                    "The Dark History of the Silk Road Crypto Seizure"
                ])
                print(f"💰 [Channel 4 Auto-Topic Selected]: '{topic}'")
            elif "channel_5" in channel or "legal" in channel:
                import random
                topic = random.choice([
                    "The Most Bizarre Supreme Court Case in US History",
                    "The Loophole That Legally Allowed Someone to Claim an Island"
                ])
                print(f"⚖️ [Channel 5 Auto-Topic Selected]: '{topic}'")
            else:
                topic = "The Mystery of the Bermuda Triangle"
                print(f"🎬 [Default Topic Selected]: '{topic}'")

        director = StudioDirector()
        director.create_video(topic)
    elif args.command == "trends":
        crawler = GoogleTrendsCrawler()
        trends = crawler.fetch_daily_breakouts(geo="US", min_volume=100_000)
        print("\n🔥 Top Breakout Trends:")
        for i, t in enumerate(trends[:args.limit], 1):
            print(f"  {i}. {t['title']} ({t['traffic']} searches) - {t['summary'][:60]}...")
        if args.auto_produce and trends:
            top_topic = trends[0]["title"]
            print(f"\n>> Auto-producing video for top breakout: '{top_topic}'...")
            director = StudioDirector()
            director.create_video(top_topic)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
