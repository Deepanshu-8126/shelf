"""
LoFi Studio v3 — Master CLI

COMMANDS:
  --demo                          Quick 15s test render (any style)
  --run                           Generate full video mixtape
  --live                          Start 24/7 YouTube Live Stream
  --live-rotate                   Multi-style rotation stream (12h+)
  --test-live                     Test live stream (saves to file, no YouTube)
  --input <file>                  Convert your own song to LoFi

OPTIONS:
  --style <style>                 LoFi style (see below)
  --count <n>                     Number of tracks (default: 8)
  --stream-key <key>              YouTube Stream Key (for --live)
  --hours <n>                     Hours per style in rotation (default: 4)
  --upload                        Auto-upload to YouTube after render
  --list-styles                   Show all available styles

LOFI STYLES:
  hindi_sad      🌙  Slowed + Reverb + Rain (Bollywood feel)
  study          📚  Clean + Warm + Focus beats
  rain           🌧️  Rainy night + Chill ambient
  dark_midnight  🖤  Dark bass + Thunder + 3AM vibes
  anime          🌸  Bright + Tokyo night + Sakura vibes
  jazz_cafe      ☕  Vinyl crackle + Coffee shop + Jazz
  city_pop       🏙️  80s Retro + Night drive + Synth

EXAMPLES:
  python main_lofi.py --demo --style rain
  python main_lofi.py --run --style dark_midnight --count 10
  python main_lofi.py --live --stream-key xxxx-xxxx-xxxx-xxxx
  python main_lofi.py --live-rotate --hours 3
  python main_lofi.py --test-live --style anime
  python main_lofi.py --list-styles
"""
from __future__ import annotations

import argparse
import os
import random
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from audio_dsp import STYLE_PRESETS, LofiStyle, apply_lofi_dsp, generate_ambient_track
from visual_engine import render_lofi_video
from lofi_pipeline import create_lofi_mixtape

BASE_DIR = Path(__file__).parent
ASSETS_DIR = BASE_DIR / "assets"
OUTPUT_DIR = BASE_DIR / "output"

ALL_STYLES = list(STYLE_PRESETS.keys())


def get_background_image(style: str = "hindi_sad") -> Path:
    """Get or create style-appropriate background."""
    bg = ASSETS_DIR / "background.jpg"
    if bg.exists():
        return bg

    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    import subprocess
    from audio_dsp import STYLE_VISUALS  # type: ignore
    # Import local
    from live_streamer import _generate_style_background
    return _generate_style_background(style, ASSETS_DIR)


def cmd_list_styles():
    """Display all available LoFi styles."""
    print("\n🎵 Available LoFi Styles:")
    print("─" * 50)
    for key, preset in STYLE_PRESETS.items():
        print(f"  {preset['emoji']}  {key:<15}  {preset['name']}")
    print("─" * 50)
    print("\nUsage: python main_lofi.py --run --style <style_name>")


def cmd_demo(style: str):
    """15-second demo render for any style."""
    preset = STYLE_PRESETS.get(style, STYLE_PRESETS["hindi_sad"])
    print(f"\n{preset['emoji']} Demo Mode: {preset['name']} (15 seconds)")
    print("─" * 50)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)

    demo_audio = OUTPUT_DIR / f"demo_{style}.mp3"
    print("  🎹 Generating ambient track...")
    generate_ambient_track(15.0, demo_audio, style=style)

    bg = get_background_image(style)
    from live_streamer import STYLE_VISUALS
    visual = STYLE_VISUALS[style]
    demo_video = OUTPUT_DIR / f"demo_{style}.mp4"

    print("  🎬 Rendering video (no jitter mode)...")
    render_lofi_video(
        background_source=bg,
        audio_path=demo_audio,
        output_video=demo_video,
        track_title=f"DEMO • {preset['name']}",
        font_path=ASSETS_DIR / "font.ttf",
    )
    print(f"\n✅ Demo ready: {demo_video}")
    print("  Watch this to preview quality before running full pipeline!")


def cmd_run(style: str, count: int, upload: bool, voice: str | None = None):
    """Full video mixtape generation."""
    preset = STYLE_PRESETS.get(style, STYLE_PRESETS["hindi_sad"])
    from live_streamer import STYLE_TITLES
    title = random.choice(STYLE_TITLES.get(style, STYLE_TITLES["hindi_sad"]))
    bg = get_background_image(style)

    create_lofi_mixtape(
        output_dir=OUTPUT_DIR / style,
        background_image=bg,
        track_count=count,
        mixtape_title=title,
        mood="lofi",
        upload_to_youtube=upload,
        style=style,
        voice=voice,
    )


def cmd_live(stream_key: str, style: str, test_mode: bool = False):
    """Start 24/7 live stream."""
    from live_streamer import start_live_stream
    start_live_stream(
        stream_key=stream_key,
        style=style,
        output_dir=OUTPUT_DIR / "live" / style,
        track_count=6,
        test_mode=test_mode,
    )


def cmd_live_rotate(stream_key: str, styles: list, hours: float, test_mode: bool):
    """Multi-style rotation stream."""
    from live_streamer import start_multi_style_rotation
    start_multi_style_rotation(
        stream_key=stream_key,
        styles=styles,
        cycle_hours=hours,
        output_dir=OUTPUT_DIR / "live",
    )


def main():
    parser = argparse.ArgumentParser(
        description="LoFi Studio v3 — Copyright-Free LoFi Video & Live Stream Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    # Commands
    parser.add_argument("--demo", action="store_true", help="Quick 15s demo render")
    parser.add_argument("--run", action="store_true", help="Generate full video mixtape")
    parser.add_argument("--live", action="store_true", help="Start 24/7 YouTube Live Stream")
    parser.add_argument("--live-rotate", action="store_true", help="Multi-style rotation stream")
    parser.add_argument("--test-live", action="store_true", help="Test live (saves file, no YouTube)")
    parser.add_argument("--input", type=str, help="Convert your own audio file to LoFi")
    parser.add_argument("--list-styles", action="store_true", help="Show all styles")

    # Options
    parser.add_argument("--style", type=str, default="hindi_sad",
                        choices=ALL_STYLES, help="LoFi style")
    parser.add_argument("--styles", type=str, nargs="+",
                        help="Styles for rotation (e.g. --styles hindi_sad rain anime)")
    parser.add_argument("--count", type=int, default=8, help="Number of tracks")
    parser.add_argument("--stream-key", type=str,
                        default=os.getenv("YOUTUBE_STREAM_KEY", ""),
                        help="YouTube Stream Key")
    parser.add_argument("--hours", type=float, default=4.0,
                        help="Hours per style in rotation (default: 4)")
    parser.add_argument("--upload", action="store_true", help="Auto-upload to YouTube")
    parser.add_argument("--title", type=str, help="Custom video title")
    parser.add_argument("--voice", default=None, help="Voice overlay for vocal elements (e.g. am_michael, af_bella)")

    args = parser.parse_args()

    # Route commands
    if args.list_styles:
        cmd_list_styles()

    elif args.demo:
        cmd_demo(args.style)

    elif args.run:
        cmd_run(args.style, args.count, args.upload, args.voice)

    elif args.live:
        key = args.stream_key or os.getenv("YOUTUBE_STREAM_KEY", "")
        if not key:
            print("❌ Stream key required! Use --stream-key or set YOUTUBE_STREAM_KEY env var")
            print("   Get it from: YouTube Studio → Go Live → Stream Key")
            return
        cmd_live(key, args.style)

    elif args.test_live:
        cmd_live(stream_key="test", style=args.style, test_mode=True)

    elif args.live_rotate:
        key = args.stream_key or os.getenv("YOUTUBE_STREAM_KEY", "")
        if not key:
            print("❌ Stream key required!")
            return
        styles = args.styles or ["hindi_sad", "rain", "anime", "jazz_cafe"]
        cmd_live_rotate(key, styles, args.hours, test_mode=False)

    elif args.input:
        in_p = Path(args.input)
        if not in_p.exists():
            print(f"❌ File not found: {in_p}")
            return
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        out_dsp = OUTPUT_DIR / f"lofi_{in_p.stem}.m4a"
        print(f"🎛️  Converting: {in_p.name} → {args.style} style")
        apply_lofi_dsp(in_p, out_dsp, style=args.style)
        bg = get_background_image(args.style)
        out_vid = OUTPUT_DIR / f"lofi_{in_p.stem}_{args.style}.mp4"
        render_lofi_video(
            background_source=bg, audio_path=out_dsp, output_video=out_vid,
            track_title=args.title or f"LoFi {in_p.stem}",
        )
        print(f"✅ Done: {out_vid}")

    else:
        print(__doc__)
        print("\nQuick start:")
        print("  python main_lofi.py --list-styles")
        print("  python main_lofi.py --demo --style rain")
        print("  python main_lofi.py --test-live --style anime")


if __name__ == "__main__":
    main()
