"""
Unified Studio Master (The Master Production Orchestrator)
==========================================================
One single CLI entrypoint for both viral video production pipelines:

1. AESTHETIC LYRIC PIPELINE (Husn / Lofi / Hindi Songs):
   - Whisper-powered zero-error vocal alignment
   - Rich Rozha One Devanagari calligraphy
   - Warm vintage ivory paper canvas
   - 16:9 Spinning Glowing Vinyl or 9:16 Vertical Reel Stack
   Usage:
   python core/studio_master.py --pipeline lyric --audio path/to/song.mp3 --ratio 16:9 --title "Husn" --artist "Anuv Jain"

2. PHONK SOUNDWAVE DAGGER PIPELINE (Gym / Phonk / Adrenaline):
   - Audio-reactive 808 frequency soundwave blade
   - High-contrast warrior manga art
   - 3D Depth bokeh particles & chromatic bass pump
   Usage:
   python core/studio_master.py --pipeline phonk --audio path/to/phonk.mp3 --title "[DOPAMINE]" --duration 5.0
"""

import os
import sys
import argparse
import yt_dlp

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Ensure core directory is on path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from aesthetic_lyric_engine import AestheticLyricEngine
from phonk_dagger_engine import PhonkDaggerEngine

def download_youtube_audio(url, output_dir=None):
    """Downloads audio from YouTube if a URL is supplied."""
    if output_dir is None:
        output_dir = os.path.join(parent_dir, "phonk_tracks")
    os.makedirs(output_dir, exist_ok=True)
    out_tmpl = os.path.join(output_dir, "downloaded_track.%(ext)s")
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': out_tmpl,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': False
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    
    final_mp3 = os.path.join(output_dir, "downloaded_track.mp3")
    return final_mp3

def main():
    parser = argparse.ArgumentParser(description="Unified Viral Video Studio Master")
    parser.add_argument("--pipeline", required=True, choices=["lyric", "phonk"], help="Production pipeline to use")
    
    # Common args
    parser.add_argument("--audio", help="Local audio path (mp3/wav)")
    parser.add_argument("--url", help="YouTube URL to download audio from")
    parser.add_argument("--title", default="Husn", help="Song or Brand title")
    parser.add_argument("--artist", default="Anuv Jain", help="Artist name")
    # Lyric Pipeline specific args
    parser.add_argument("--ratio", default="9:16", choices=["9:16", "16:9"], help="Aspect ratio for lyric video (default 9:16)")
    parser.add_argument("--vocal_start", type=float, default=70.0, help="Start timestamp of vocals (default 70.0s)")
    parser.add_argument("--duration", type=float, default=22.5, help="Duration in seconds (default 22.5s)")
    parser.add_argument("--output", help="Optional custom master output path")
    parser.add_argument("--player", action="store_true", help="Include Spotify player scrubber")
    parser.add_argument("--floral", action="store_true", help="Enable aesthetic summer botanical petals and leaves overlay")
    parser.add_argument("--lrc", help="Path to verified .lrc synced lyrics file")
    
    # Phonk Pipeline specific args
    parser.add_argument("--artwork", help="Custom artwork path (defaults to gym warrior)")
    parser.add_argument("--subtitle", default="will make you the main character", help="Phonk subtitle")
    parser.add_argument("--bass_start", type=float, default=20.0, help="Start timestamp of 808 bass drop")

    args = parser.parse_args()

    # 1. Resolve Audio Path
    audio_path = args.audio
    if not audio_path and args.url:
        print(f"Downloading audio from {args.url}...")
        audio_path = download_youtube_audio(args.url)
    
    if not audio_path:
        # Default fallbacks
        if args.pipeline == "lyric":
            audio_path = os.path.join(parent_dir, "indian-lofi-converter", "raw_stems", "husn_raw.mp3")
        else:
            audio_path = os.path.join(parent_dir, "phonk_tracks", "ainsi_bas_la_vida_phonk.mp3")

    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found at: {audio_path}")

    # =========================================================================
    # PIPELINE 1: AESTHETIC LYRIC VIDEO
    # =========================================================================
    if args.pipeline == "lyric":
        print("=== LAUNCHING AESTHETIC LYRIC PIPELINE (LOCKED) ===")
        engine = AestheticLyricEngine()
        
        # Parse synced lyrics if provided
        cards_parsed = None
        if getattr(args, 'lrc', None) and os.path.exists(args.lrc):
            cards_parsed = engine.parse_lrc_file(args.lrc, args.duration, is_16x9=(args.ratio == "16:9"))

        # Extract clean vocal slice or use direct master wav
        if audio_path.endswith(".wav") and (args.vocal_start == 0.0 or args.vocal_start is None):
            temp_wav = None
            render_audio = audio_path
        else:
            temp_wav = os.path.join(parent_dir, "output", "temp_vocal_slice.wav")
            engine.extract_audio_slice(audio_path, start_sec=args.vocal_start, duration_sec=args.duration, output_wav_path=temp_wav)
            render_audio = temp_wav
        
        mins = int(args.vocal_start) // 60
        secs = int(args.vocal_start) % 60
        start_label = f"{mins}:{secs:02d}"

        out_video = engine.render(
            audio_path=render_audio,
            title=args.title,
            artist=args.artist,
            aspect_ratio=args.ratio,
            duration=args.duration,
            cards_config=cards_parsed,
            output_mp4=args.output,
            show_player=getattr(args, 'player', False),
            enable_water_caustics=("husn" in args.title.lower() and not getattr(args, 'floral', False)),
            start_offset_label=start_label,
            artwork_path=getattr(args, 'artwork', None),
            enable_floral_overlay=getattr(args, 'floral', False)
        )
        if temp_wav and os.path.exists(temp_wav):
            try:
                os.remove(temp_wav)
            except Exception:
                pass
        print(f"\n[DONE] Master Lyric Video: {out_video}")

    # =========================================================================
    # PIPELINE 2: PHONK SOUNDWAVE DAGGER VIDEO
    # =========================================================================
    elif args.pipeline == "phonk":
        print("=== LAUNCHING PHONK SOUNDWAVE DAGGER PIPELINE (LOCKED) ===")
        engine = PhonkDaggerEngine()
        
        # Artwork
        artwork_path = args.artwork or os.path.join(parent_dir, "gym_warrior_1080p.png")
        if not os.path.exists(artwork_path):
            raise FileNotFoundError(f"Artwork not found at: {artwork_path}")

        # Extract 808 bass drop slice
        temp_wav = os.path.join(parent_dir, "output", "temp_phonk_slice.wav")
        engine.extract_audio_slice(audio_path, start_sec=args.bass_start, duration_sec=args.duration, output_wav_path=temp_wav)

        track_label = f"{args.title.replace('[', '').replace(']', '')}  •  SUPER SLOWED PHONK"

        out_video = engine.render(
            audio_path=temp_wav,
            base_img_path=artwork_path,
            title=args.title,
            subtitle=args.subtitle,
            track_label=track_label,
            duration=args.duration,
            output_mp4=args.output
        )
        if os.path.exists(temp_wav):
            os.remove(temp_wav)
        print(f"\n🎉 ALL DONE! Master Phonk Video: {out_video}")

if __name__ == "__main__":
    main()
