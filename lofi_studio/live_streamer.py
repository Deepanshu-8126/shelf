"""
YouTube Live Streamer: Infinite 24/7 LoFi Live Stream via FFmpeg RTMP.

How it works:
  1. Generate (or use cached) LoFi audio + aesthetic B-roll/image
  2. Loop content infinitely using FFmpeg concat demuxer
  3. Stream to YouTube via RTMP with your Stream Key
  4. Runs forever until you stop it (Ctrl+C or process kill)

YouTube Live Stream Setup:
  1. Go to YouTube Studio → Go Live → Schedule Stream
  2. Copy your "Stream Key" (looks like: xxxx-xxxx-xxxx-xxxx-xxxx)
  3. Set YOUTUBE_STREAM_KEY in environment or pass via --stream-key
  4. Run: python live_streamer.py --style rain --duration 12h

IMPORTANT: Start YouTube Live "Schedule" first, THEN run this script.
The RTMP endpoint is: rtmp://a.rtmp.youtube.com/live2/<stream_key>

Legal Note: All content generated here is 100% original/synthesized.
"""
from __future__ import annotations

import os
import random
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from audio_dsp import STYLE_PRESETS, LofiStyle, apply_lofi_dsp, generate_ambient_track
from visual_engine import render_lofi_video
from music_fetcher import get_copyright_free_tracks

YOUTUBE_RTMP_URL = "rtmp://a.rtmp.youtube.com/live2"

# Visual themes per LoFi style (background colors / themes)
STYLE_VISUALS = {
    "hindi_sad": {
        "title_color": "0xFF9AA2",    # Soft pink
        "wave_color": "0xFF9AA2@0.8|0xFFD1DC@0.6",
        "bg_color": "0x0d0511",       # Deep dark purple
        "subtitle": "SLOWED + REVERB  •  HINDI SAD LOFI  •  NIGHT VIBES",
    },
    "study": {
        "title_color": "white",
        "wave_color": "0x90CAF9@0.8|0xE3F2FD@0.5",
        "bg_color": "0x0a1628",       # Dark navy blue
        "subtitle": "STUDY LOFI  •  FOCUS BEATS  •  NO DISTRACTIONS",
    },
    "rain": {
        "title_color": "0xB3E5FC",    # Light blue
        "wave_color": "0x4FC3F7@0.8|0xB3E5FC@0.5",
        "bg_color": "0x051219",       # Dark teal
        "subtitle": "RAINY NIGHT LOFI  •  CHILL BEATS  •  COZY VIBES",
    },
    "dark_midnight": {
        "title_color": "0xCE93D8",    # Purple
        "wave_color": "0x9C27B0@0.9|0xCE93D8@0.6",
        "bg_color": "0x050008",       # Almost black purple
        "subtitle": "DARK MIDNIGHT LOFI  •  DEEP FEELINGS  •  3AM VIBES",
    },
    "anime": {
        "title_color": "0xF48FB1",    # Sakura pink
        "wave_color": "0xFF80AB@0.85|0xFFCDD2@0.5",
        "bg_color": "0x100a1a",       # Deep violet
        "subtitle": "ANIME LOFI  •  TOKYO NIGHTS  •  SAKURA VIBES",
    },
    "jazz_cafe": {
        "title_color": "0xFFCC80",    # Warm amber
        "wave_color": "0xFFB74D@0.8|0xFFE0B2@0.5",
        "bg_color": "0x0f0800",       # Very dark brown
        "subtitle": "JAZZ CAFE LOFI  •  VINYL SESSIONS  •  COFFEE & BEATS",
    },
    "city_pop": {
        "title_color": "0x80CBC4",    # Teal
        "wave_color": "0x26A69A@0.85|0x80CBC4@0.5",
        "bg_color": "0x001a1a",       # Dark teal/cyan
        "subtitle": "CITY POP LOFI  •  80s RETRO VIBES  •  NIGHT DRIVE",
    },
}

# Titles for each style (rotated randomly)
STYLE_TITLES = {
    "hindi_sad": [
        "ALL TRENDING HINDI LOFI 2026 🌙 | Slowed + Reverb | Night Vibes",
        "BEST BOLLYWOOD SAD LOFI | Slowed Reverb | Midnight Feelings",
        "HINDI SAD LOFI MIX 🖤 | Self Respect | Late Night Feelings",
    ],
    "study": [
        "STUDY LOFI BEATS 📚 | Focus Music | 2026 Playlist",
        "LOFI BEATS TO STUDY/RELAX TO | Chill Hip Hop Mix",
        "FOCUS MUSIC LOFI 🎧 | Study Session | No Lyrics",
    ],
    "rain": [
        "RAINY NIGHT LOFI 🌧️ | Chill Beats | Cozy Vibes 2026",
        "LOFI RAIN SONGS | Slowed Reverb | Rainy Day Feels",
        "RAIN LOFI MIX ☔ | Study & Chill | Late Night Vibes",
    ],
    "dark_midnight": [
        "DARK MIDNIGHT LOFI 🖤 | 3AM Playlist | Deep Feelings",
        "DARK LOFI MIX | Bass Boosted | Sad Night Vibes",
        "MIDNIGHT LOFI 🌑 | Emotional Beats | Self Reflection",
    ],
    "anime": [
        "ANIME LOFI MIX 🌸 | Tokyo Night Vibes | Aesthetic 2026",
        "JAPANESE LOFI BEATS | Sakura Season | Chill Anime Music",
        "ANIME LOFI RADIO 🎌 | Studio Ghibli Feels | Relaxing",
    ],
    "jazz_cafe": [
        "JAZZ LOFI CAFE ☕ | Vinyl Sessions | Coffee & Beats",
        "LOFI JAZZ MIX | Late Night Coffee Shop | Chill Vibes",
        "JAZZ CAFE BEATS 🎷 | Study & Work | Smooth Lofi",
    ],
    "city_pop": [
        "80s CITY POP LOFI 🏙️ | Retro Night Drive | Aesthetic",
        "CITY POP MIX | Japanese 80s Vibes | Night Drive Lofi",
        "RETRO LOFI BEATS 🌃 | City Pop Radio | Late Night",
    ],
}


def generate_lofi_content(
    style: LofiStyle,
    output_dir: Path,
    track_count: int = 5,
    custom_tracks: list[dict] | None = None,
) -> tuple[Path, Path]:
    """
    Generates LoFi audio + static background for the given style.
    Returns (master_audio_path, background_image_path)
    """
    output_dir = Path(output_dir)
    cache_dir = output_dir / "cache" / style
    cache_dir.mkdir(parents=True, exist_ok=True)

    style_info = STYLE_PRESETS[style]
    print(f"\n{style_info['emoji']} Preparing {style_info['name']}...")

    # Get tracks
    if custom_tracks:
        tracks = custom_tracks
    else:
        tracks = get_copyright_free_tracks(
            count=track_count,
            output_dir=cache_dir / "music",
            mood="lofi"
        )

    if not tracks:
        print("  🎹 No tracks found, generating synthetic...")
        tracks = []

    # Apply DSP to each track
    processed = []
    for idx, t in enumerate(tracks):
        in_path = Path(t["path"])
        out_path = cache_dir / f"dsp_{idx:02d}_{in_path.stem}.m4a"
        print(f"  🎚️  [{idx+1}/{len(tracks)}] {style_info['emoji']} {t['title']}")
        try:
            apply_lofi_dsp(in_path, out_path, style=style)
            processed.append(out_path)
        except Exception as e:
            print(f"  ❌ DSP error: {e}")

    # Add synthetic tracks if not enough
    while len(processed) < track_count:
        idx = len(processed)
        synth_path = cache_dir / f"synth_{idx:02d}.mp3"
        print(f"  🎹 Synthesizing ambient track {idx+1}...")
        try:
            generate_ambient_track(190.0, synth_path, style=style)
            processed.append(synth_path)
        except Exception as e:
            print(f"  ❌ Synthesis error: {e}")
            break

    # Concatenate all into master audio
    master_audio = cache_dir / "master.m4a"
    concat_file = cache_dir / "audio_list.txt"
    with open(concat_file, "w", encoding="utf-8") as f:
        for p in processed:
            f.write(f"file '{p.resolve().as_posix()}'\n")

    subprocess.run([
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-f", "concat", "-safe", "0", "-i", str(concat_file),
        "-c", "copy", str(master_audio)
    ], check=True)

    # Generate background image (colored aesthetic dark frame)
    bg_image = _generate_style_background(style, cache_dir)

    return master_audio, bg_image


def _generate_style_background(style: LofiStyle, output_dir: Path) -> Path:
    """Generate a styled dark background image for the given LoFi style."""
    output_dir = Path(output_dir)
    bg_path = output_dir / "background.jpg"

    visual = STYLE_VISUALS[style]
    bg_color = visual["bg_color"]

    # Check for existing background in assets
    asset_bg = Path(__file__).parent / "assets" / "background.jpg"
    if asset_bg.exists() and not bg_path.exists():
        import shutil
        shutil.copy(asset_bg, bg_path)
        return bg_path

    if not bg_path.exists():
        subprocess.run([
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-f", "lavfi",
            "-i", f"color=c={bg_color}:s=1920x1080:d=1",
            "-frames:v", "1", str(bg_path)
        ], check=True)

    return bg_path


def _build_live_filtergraph(
    style: LofiStyle,
    title: str,
    w: int = 1920,
    h: int = 1080,
) -> str:
    """Build the FFmpeg filtergraph for live stream overlay."""
    visual = STYLE_VISUALS[style]
    title_color = visual["title_color"]
    wave_color = visual["wave_color"].split("|")[0]  # primary wave color
    subtitle = visual["subtitle"]

    # Escape for drawtext
    def esc(t):
        return t.replace(":", "\\:").replace("'", "\\'").replace(",", "\\,")

    clean_title = esc(title[:80])
    clean_sub = esc(subtitle)

    fg = (
        # Background: static image, no movement (no jitter)
        f"[0:v]scale={w}:{h}:force_original_aspect_ratio=increase,"
        f"crop={w}:{h},"
        f"eq=contrast=1.06:brightness=-0.08:saturation=0.75,"
        f"vignette=PI/5[bg];"

        # Waveform from audio input
        f"[1:a]showwaves=s={int(w*0.65)}x90:mode=cline:rate=30:"
        f"colors={wave_color}:scale=lin[wave_raw];"
        f"[wave_raw]format=rgba,boxblur=lr=4:lp=1[wave_glow];"
        f"[wave_glow][wave_raw]overlay=0:0[wave_fx];"

        # Combine bg + wave at bottom
        f"[bg][wave_fx]overlay=x=(W-w)/2:y={h-200}[v_wave];"

        # Dark gradient band for text
        f"[v_wave]drawbox=x=0:y={h-240}:w={w}:h=240:color=black@0.55:t=fill[v_bar];"

        # LIVE badge (top-left)
        f"[v_bar]drawbox=x=30:y=30:w=100:h=42:color=red@0.9:t=fill,"
        f"drawtext=text='● LIVE':fontcolor=white:fontsize=22:"
        f"x=40:y=42:shadowcolor=black@0.5:shadowx=1:shadowy=1,"

        # Main title
        f"drawtext=text='{clean_title}':"
        f"fontcolor={title_color}:fontsize=36:x=(w-text_w)/2:y={h-188}:"
        f"shadowcolor=black@0.9:shadowx=2:shadowy=2,"

        # Subtitle
        f"drawtext=text='{clean_sub}':"
        f"fontcolor=white@0.7:fontsize=19:x=(w-text_w)/2:y={h-120}:"
        f"shadowcolor=black@0.6:shadowx=1:shadowy=1,"

        # Viewer count placeholder (timestamp as proxy)
        f"drawtext=text='%{{pts\\:hms}}':fontcolor=white@0.5:fontsize=16:"
        f"x={w-160}:y=42:shadowcolor=black@0.4:shadowx=1:shadowy=1"

        f"[vout]"
    )
    return fg


def start_live_stream(
    stream_key: str,
    style: LofiStyle = "hindi_sad",
    output_dir: Path = Path("output/live"),
    track_count: int = 6,
    custom_tracks: list[dict] | None = None,
    resolution: tuple[int, int] = (1920, 1080),
    fps: int = 30,
    video_bitrate: str = "4500k",
    audio_bitrate: str = "192k",
    test_mode: bool = False,   # If True, outputs to file instead of YouTube
) -> None:
    """
    Start an infinite 24/7 LoFi live stream to YouTube.

    Args:
        stream_key: YouTube Stream Key (from YouTube Studio → Go Live)
        style: LoFi style to stream
        output_dir: Directory for cached files
        track_count: Number of tracks to generate per cycle
        test_mode: If True, saves to file instead of streaming (for testing)
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    style_info = STYLE_PRESETS[style]
    title = random.choice(STYLE_TITLES[style])

    print("\n" + "="*65)
    print(f"📡  YouTube 24/7 Live Stream — {style_info['emoji']} {style_info['name']}")
    print(f"🎵  Title: {title}")
    print(f"📺  Mode: {'TEST (local file)' if test_mode else 'YOUTUBE LIVE'}")
    print("="*65)

    # Step 1: Generate content
    print("\n[1/3] Generating LoFi content...")
    master_audio, bg_image = generate_lofi_content(
        style=style,
        output_dir=output_dir,
        track_count=track_count,
        custom_tracks=custom_tracks,
    )
    print(f"  ✅ Content ready: {master_audio}")

    # Step 2: Build FFmpeg command for infinite loop
    w, h = resolution
    filtergraph = _build_live_filtergraph(style, title, w, h)

    # Output target
    if test_mode:
        output_target = [
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", audio_bitrate,
            "-t", "60",   # 60 second test clip
            str(output_dir / f"test_live_{style}.mp4")
        ]
        print("\n[2/3] Rendering 60-second test clip...")
    else:
        rtmp_url = f"{YOUTUBE_RTMP_URL}/{stream_key}"
        output_target = [
            # Video encoding — optimized for live streaming
            "-c:v", "libx264",
            "-preset", "veryfast",    # Fast encode for real-time
            "-b:v", video_bitrate,
            "-maxrate", video_bitrate,
            "-bufsize", str(int(video_bitrate[:-1]) * 2) + "k",
            "-pix_fmt", "yuv420p",
            "-r", str(fps),
            "-g", str(fps * 2),       # GOP size = 2x fps
            # Audio
            "-c:a", "aac", "-b:a", audio_bitrate, "-ar", "44100",
            # RTMP output
            "-f", "flv",
            rtmp_url
        ]
        print(f"\n[2/3] Starting live stream to YouTube...")
        print(f"  RTMP: {YOUTUBE_RTMP_URL}/{stream_key[:8]}...")

    # Step 3: Build the full FFmpeg command
    # Key: -stream_loop -1 loops the input forever
    cmd = [
        "ffmpeg", "-hide_banner", "-loglevel", "warning", "-y",

        # Input 1: Background image (looped forever)
        "-loop", "1", "-framerate", str(fps),
        "-i", str(bg_image),

        # Input 2: Audio (looped forever)
        "-stream_loop", "-1",
        "-i", str(master_audio),

        # Filter
        "-filter_complex", filtergraph,
        "-map", "[vout]",
        "-map", "1:a",
    ] + output_target

    print(f"\n[3/3] {'Streaming' if not test_mode else 'Rendering'} LIVE...")
    if not test_mode:
        print("  💡 Press Ctrl+C to stop the stream")
        print("  ⏳ Stream will run FOREVER until you stop it\n")

    # Handle graceful shutdown
    process = None
    def _shutdown(sig, frame):
        print("\n\n🛑 Stopping stream gracefully...")
        if process:
            process.terminate()
        sys.exit(0)

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    try:
        process = subprocess.Popen(cmd)
        process.wait()
    except KeyboardInterrupt:
        print("\n🛑 Stream stopped by user")
        if process:
            process.terminate()

    if test_mode:
        test_file = output_dir / f"test_live_{style}.mp4"
        if test_file.exists():
            print(f"\n✅ Test clip saved: {test_file}")
            print("   Watch it to verify quality before going live!")


def start_multi_style_rotation(
    stream_key: str,
    styles: list[LofiStyle] = None,
    cycle_hours: float = 4.0,
    output_dir: Path = Path("output/live"),
) -> None:
    """
    Rotates through multiple LoFi styles automatically.
    Each style streams for cycle_hours, then switches to next.
    
    Example: 4-style rotation, 3h each = 12 hour stream
    """
    if not styles:
        styles = ["hindi_sad", "rain", "anime", "jazz_cafe"]

    output_dir = Path(output_dir)
    cycle_seconds = int(cycle_hours * 3600)

    print(f"\n🔄 Multi-Style Rotation: {len(styles)} styles × {cycle_hours}h = {len(styles)*cycle_hours}h stream")
    for s in styles:
        info = STYLE_PRESETS[s]
        print(f"   {info['emoji']} {info['name']}")

    idx = 0
    while True:
        style = styles[idx % len(styles)]
        info = STYLE_PRESETS[style]
        print(f"\n{'='*60}")
        print(f"🎵 Now streaming: {info['emoji']} {info['name']}")
        print(f"⏱️  Duration: {cycle_hours}h")
        print(f"{'='*60}")

        # Generate content for this style
        master_audio, bg_image = generate_lofi_content(
            style=style, output_dir=output_dir / style, track_count=6
        )
        title = random.choice(STYLE_TITLES[style])
        w, h = 1920, 1080
        filtergraph = _build_live_filtergraph(style, title, w, h)
        rtmp_url = f"{YOUTUBE_RTMP_URL}/{stream_key}"

        cmd = [
            "ffmpeg", "-hide_banner", "-loglevel", "warning",
            "-loop", "1", "-framerate", "30", "-i", str(bg_image),
            "-stream_loop", "-1", "-i", str(master_audio),
            "-filter_complex", filtergraph,
            "-map", "[vout]", "-map", "1:a",
            "-c:v", "libx264", "-preset", "veryfast", "-b:v", "4500k",
            "-maxrate", "4500k", "-bufsize", "9000k", "-pix_fmt", "yuv420p",
            "-r", "30", "-g", "60",
            "-c:a", "aac", "-b:a", "192k", "-ar", "44100",
            "-t", str(cycle_seconds),   # Stream for cycle_seconds then switch
            "-f", "flv", rtmp_url
        ]

        try:
            subprocess.run(cmd)
        except KeyboardInterrupt:
            print("\n🛑 Rotation stopped")
            break

        idx += 1
        print(f"\n🔄 Switching to next style...")
        time.sleep(5)
