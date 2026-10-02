"""
LoFi Studio v2 — CLI Runner

Usage:
  python main_lofi.py --demo                    # Quick 15-sec test render
  python main_lofi.py --run                     # Full auto pipeline (fetch + render)
  python main_lofi.py --run --upload            # Full pipeline + YouTube upload
  python main_lofi.py --input song.mp3          # Convert your own song to LoFi
  python main_lofi.py --run --count 10          # Use 10 tracks
  python main_lofi.py --run --mood ambient      # Different mood/genre

Environment Variables (optional but recommended):
  PEXELS_API_KEY   - For real B-roll clips (free at pexels.com/api)
  JAMENDO_API_KEY  - For more music choices (free at developer.jamendo.com)
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from audio_dsp import apply_lofi_dsp, generate_ambient_track
from visual_engine import render_lofi_video
from lofi_pipeline import create_lofi_mixtape


BASE_DIR = Path(__file__).parent
ASSETS_DIR = BASE_DIR / "assets"
OUTPUT_DIR = BASE_DIR / "output"
CACHE_DIR = BASE_DIR / "cache"

MIXTAPE_TITLES = [
    "ALL TRENDING HINDI LOFI 2026 🌙 | Night Vibes & Self-Respect",
    "BEST BOLLYWOOD LOFI MIX | Slowed + Reverb | Midnight Feelings",
    "TOP HINDI LOFI SONGS 2026 | Study & Chill | Aesthetic Vibes",
    "SAD HINDI LOFI MIX 🌙 | Slowed Reverb | Late Night Feelings",
    "LOFI HINDI SONGS TO CRY TO | Emotional Night Vibes 2026",
]


def get_background_image() -> Path:
    """Get or create background image."""
    bg = ASSETS_DIR / "background.jpg"
    if bg.exists():
        return bg

    # Try the generated thumbnail from previous session
    for candidate in [
        BASE_DIR.parent / "hindi_lofi_bg.jpg",
        ASSETS_DIR / "bg.jpg",
        ASSETS_DIR / "thumbnail.jpg",
    ]:
        if candidate.exists():
            return candidate

    # Generate synthetic dark background using ffmpeg as last resort
    print("⚠️  No background image found. Generating synthetic dark aesthetic background...")
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    synth_bg = ASSETS_DIR / "background.jpg"
    import subprocess
    subprocess.run([
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-f", "lavfi",
        "-i", "color=c=0x0d0d1a:s=1920x1080:d=1",
        "-frames:v", "1",
        str(synth_bg)
    ], check=True)
    return synth_bg


def run_demo():
    """Generate a quick 15-second demo LoFi video."""
    print("\n🎵 LoFi Studio Demo Mode (15 seconds)")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    demo_audio = OUTPUT_DIR / "demo_ambient.m4a"
    print("  Generating ambient rain + vinyl audio...")
    generate_ambient_track(15.0, demo_audio)

    bg_image = get_background_image()
    demo_video = OUTPUT_DIR / "demo_lofi_render.mp4"
    print("  Rendering demo video (no shake, cinematic mode)...")
    render_lofi_video(
        background_source=bg_image,
        audio_path=demo_audio,
        output_video=demo_video,
        track_title="DEMO • Midnight Hindi LoFi",
        font_path=ASSETS_DIR / "font.ttf",
    )
    print(f"\n✅ Demo ready: {demo_video}")
    print("   Open it to check quality before running full pipeline!")


def run_single_track(input_path: str, title: str):
    """Convert a single audio file to LoFi video."""
    in_p = Path(input_path)
    if not in_p.exists():
        print(f"❌ File not found: {in_p}")
        return

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    bg_image = get_background_image()

    print(f"\n🎛️  Converting: {in_p.name}")
    out_dsp = OUTPUT_DIR / f"lofi_{in_p.stem}.m4a"
    apply_lofi_dsp(in_p, out_dsp)
    print("  ✅ DSP applied")

    out_vid = OUTPUT_DIR / f"lofi_{in_p.stem}.mp4"
    print("  🎬 Rendering video...")
    render_lofi_video(
        background_source=bg_image,
        audio_path=out_dsp,
        output_video=out_vid,
        track_title=title,
        font_path=ASSETS_DIR / "font.ttf",
    )
    print(f"\n✅ LoFi video ready: {out_vid}")


def main():
    import random
    parser = argparse.ArgumentParser(
        description="LoFi Studio v2: Autonomous Copyright-Free LoFi Video Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument("--demo", action="store_true", help="Generate quick 15s demo")
    parser.add_argument("--run", action="store_true", help="Run full auto pipeline")
    parser.add_argument("--input", type=str, help="Convert a specific audio file to LoFi")
    parser.add_argument("--title", type=str, default=None, help="Video title (random if not set)")
    parser.add_argument("--count", type=int, default=8, help="Number of tracks (default: 8)")
    parser.add_argument("--mood", type=str, default="lofi", help="Music mood/genre (default: lofi)")
    parser.add_argument("--upload", action="store_true", help="Auto-upload to YouTube after render")
    args = parser.parse_args()

    title = args.title or random.choice(MIXTAPE_TITLES)
    bg_image = get_background_image()

    if args.demo:
        run_demo()
        return

    if args.input:
        run_single_track(args.input, title)
        return

    if args.run:
        create_lofi_mixtape(
            output_dir=OUTPUT_DIR,
            background_image=bg_image,
            track_count=args.count,
            mixtape_title=title,
            mood=args.mood,
            upload_to_youtube=args.upload,
        )
        return

    print("ℹ️  LoFi Studio v2 — Usage:")
    print("  python main_lofi.py --demo         # Quick test render")
    print("  python main_lofi.py --run           # Full auto pipeline")
    print("  python main_lofi.py --run --upload  # Full + YouTube upload")
    print("  python main_lofi.py --input song.mp3  # Single track conversion")


if __name__ == "__main__":
    main()
