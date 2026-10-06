"""
CLI Interface for Vox Video Studio.
Usage:
    python -m vox_studio.cli create "Bermuda Triangle"
    python -m vox_studio.cli trends
"""
import argparse
import sys
import random
import os
from pathlib import Path
from channel_5_vox_studio.director import StudioDirector
from fire_crawler.trends import GoogleTrendsCrawler

# Fix Windows console UTF-8 output
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


VIRAL_TOPIC_BANK = {
    "channel_1": [
        "James Webb Telescope Shocking Deep Space Anomaly",
        "Voyager 1 Mysterious Signal from Outside the Solar System",
        "What Happens If You Fall Into a Supermassive Black Hole",
        "The Impossible Ocean Beneath Europa's Ice Surface",
        "The Wow Signal: The Only Confirmed Alien Radio Burst",
        "The Boötes Void: The Terrifying 330 Million Light-Year Emptiness",
        "The Coldest Known Place in the Universe: The Boomerang Nebula",
        "Why Time Slows Down Near Massive Neutron Stars",
        "The Day the Earth Almost Lost Its Atmosphere",
        "The Mysterious Diamond Rain Falling on Neptune and Uranus",
        "What Existed Before the Big Bang",
        "The Great Attractor: The Invisible Force Pulling Our Galaxy",
        "The 10-Billion-Year-Old Star That Shouldn't Exist",
        "The Sound of a Supermassive Black Hole Collision"
    ],
    "channel_2": [
        "The Declassified 1945 Bermuda Triangle Flight 19 Audio",
        "The Mystery of the Lead Masks of Vintém Hill",
        "The Dyatlov Pass Incident: Newly Unsealed KGB Files",
        "The Missing Malaysian Flight MH370 Satellite Coordinates",
        "The Green Children of Woolpit: 12th Century Medical Mystery",
        "The Somerton Man: The Cold War Cipher Never Solved",
        "The Lost Roman Legion That Disappeared in the Scottish Mists",
        "The Oak Island Money Pit: The 200-Year Booby Trap",
        "The Silent Submarine: What Truly Happened to USS Scorpion",
        "The Lost City of Z: Percy Fawcett's Final Expedition",
        "The Mysterious Hum Heard in Taos New Mexico",
        "The Mary Celeste: The Ghost Ship Found Floating in Perfect Order",
        "The Tunguska Explosion: The Nuclear-Scale Blast Before Nuclear Weapons",
        "The Dark Mystery of the Bridgewater Triangle"
    ]
}


def get_fresh_topic(channel: str) -> str:
    """Dynamically discover a viral topic using Gemini or the rich viral bank."""
    gemini_key = os.getenv("GEMINI_API_KEY")
    ch_key = "channel_2" if "2" in channel or "mystery" in channel or "dark" in channel else "channel_1"
    
    if gemini_key:
        try:
            import google.generativeai as genai
            genai.configure(api_key=gemini_key)
            model = genai.GenerativeModel("gemini-1.5-flash")
            
            niche_desc = (
                "unsolved mysteries, eerie historical anomalies, secret archives, or unexplained disappearances"
                if ch_key == "channel_2" else
                "deep space mysteries, mind-bending astrophysics, planetary anomalies, or quantum universe facts"
            )
            
            prompt = (
                f"Give me 1 highly viral, curiosity-inducing documentary video topic about {niche_desc} in the style of Johnny Harris and Vox. "
                "Return ONLY the topic title (5-10 words maximum). Do not use quotation marks or extra text."
            )
            resp = model.generate_content(prompt)
            clean_topic = resp.text.strip().replace('"', '').replace("'", "")
            if len(clean_topic) > 5:
                return clean_topic
        except Exception:
            pass

    return random.choice(VIRAL_TOPIC_BANK[ch_key])


def main():
    parser = argparse.ArgumentParser(description="Channel 5: The Global Ledger — Geopolitical, Map & Investigative Video Engine")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Command: create
    create_parser = subparsers.add_parser("create", help="Create a Global Ledger map/geopolitical video on a topic")
    create_parser.add_argument("topic", type=str, nargs="?", default="", help="Topic name (or leave blank for auto-selection)")
    create_parser.add_argument("--channel", type=str, default="custom", help="Channel target: channel_1, channel_2, custom")
    create_parser.add_argument("--niche", type=str, default="global_ledger", help="Niche profile (global_ledger, dark_mystery, space_science)")
    create_parser.add_argument("--voice", type=str, default="brian", help="Narrator voice (brian, marcus, adam)")
    create_parser.add_argument("--thumbnail", action="store_true", default=True, help="Render high-CTR thumbnail")
    create_parser.add_argument("--quality", type=str, choices=["1080p", "4k"], default="4k", help="Video export quality (default: 4k)")
    create_parser.add_argument("--caption-style", type=str, choices=["vox_minimal", "hormozi_pop", "dark_dossier"], default="vox_minimal", help="Viral subtitle style")

    # Command: trends
    trends_parser = subparsers.add_parser("trends", help="Fetch breakout topics and generate videos")
    trends_parser.add_argument("--limit", type=int, default=3, help="Number of trends to fetch")
    trends_parser.add_argument("--auto-produce", action="store_true", help="Automatically produce video for top trend")

    args = parser.parse_args()

    if args.command == "create":
        topic = (args.topic or "").strip()
        channel = (args.channel or "channel_1").lower()

        if not topic:
            topic = get_fresh_topic(channel)
            icon = "🌐"
            print(f"{icon} [Auto-Topic Selected for THE GLOBAL LEDGER]: '{topic}'")

        director = StudioDirector()
        director.create_video(topic, niche=args.niche)

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
