"""
Master LoFi Pipeline v2: Full copyright-free automated LoFi video factory.

Flow:
  1. music_fetcher → Downloads CC0/CC-BY tracks (Jamendo or built-in pool)
  2. audio_dsp     → Transforms each track: Slowed + Reverb + Vinyl + Rain
  3. broll_fetcher → Downloads aesthetic B-roll clips (Pexels)
  4. visual_engine → Renders cinematic HD video (NO jitter/shake)
  5. uploader      → Uploads to YouTube as unlisted
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from audio_dsp import apply_lofi_dsp
from visual_engine import render_lofi_video
from music_fetcher import get_copyright_free_tracks
from broll_fetcher import get_lofi_broll_clips


@dataclass
class TrackInfo:
    title: str
    artist: str
    audio_path: Path
    duration: float = 0.0


def get_audio_duration(file_path: Path) -> float:
    cmd = [
        "ffprobe", "-v", "error", "-show_entries",
        "format=duration", "-of", "default=noprint_wrappers=1:nokey=1",
        str(file_path)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    try:
        return float(result.stdout.strip())
    except ValueError:
        return 0.0


def format_timestamp(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def create_lofi_mixtape(
    output_dir: Path,
    background_image: Path,
    track_count: int = 8,
    mixtape_title: str = "ALL TRENDING HINDI LOFI 2026 | Night Vibes & Self-Respect",
    mood: str = "lofi chill",
    upload_to_youtube: bool = False,
    custom_tracks: list[dict] | None = None,
    style: str = "hindi_sad",
) -> dict:
    """
    Full pipeline: Copyright-free music → LoFi DSP → Cinematic Video → YouTube.
    
    Args:
        output_dir: Where to save the final video + description
        background_image: Aesthetic image as video background
        track_count: Number of tracks to use (default 8)
        mixtape_title: YouTube video title
        mood: Music search mood (lofi/chill/ambient)
        upload_to_youtube: Auto-upload after rendering
        custom_tracks: Optional list of {title, artist, path} dicts
        style: LoFi DSP style (hindi_sad/study/rain/dark_midnight/anime/jazz_cafe/city_pop)
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    cache_dir = output_dir / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)

    print("\n" + "="*60)
    print("🎵  LoFi Studio v2 — Full Auto Pipeline")
    print("="*60)

    # ── STEP 1: Get copyright-free music ─────────────────────────
    print("\n[1/5] 🎵 Fetching copyright-free music...")
    if custom_tracks:
        tracks = custom_tracks
        print(f"  ✅ Using {len(tracks)} custom-provided tracks")
    else:
        tracks = get_copyright_free_tracks(
            count=track_count,
            output_dir=cache_dir / "music",
            mood=mood
        )

    if not tracks:
        print("❌ No tracks available. Aborting.")
        return {"error": "No tracks available"}

    # ── STEP 2: Apply LoFi DSP ───────────────────────────────────
    print(f"\n[2/5] 🎛️ Applying LoFi DSP to {len(tracks)} tracks...")
    processed_tracks = []
    current_time = 0.0
    timestamps = []

    for idx, t in enumerate(tracks):
        in_path = Path(t["path"])
        out_dsp = cache_dir / f"lofi_{idx:02d}_{in_path.stem}.m4a"

        print(f"  🎚️  Processing [{idx+1}/{len(tracks)}]: {t['title']} by {t['artist']}")
        try:
            apply_lofi_dsp(in_path, out_dsp, style=style)
            dur = get_audio_duration(out_dsp)
            if dur < 5:
                print(f"  ⚠️  Track too short ({dur:.1f}s), skipping")
                continue

            timestamps.append({
                "timestamp": format_timestamp(current_time),
                "title": t["title"],
                "artist": t["artist"]
            })
            current_time += dur
            processed_tracks.append(out_dsp)
            print(f"  ✅  Done: {dur:.0f}s (playlist pos: {timestamps[-1]['timestamp']})")
        except subprocess.CalledProcessError as e:
            print(f"  ❌ DSP failed for {t['title']}: {e}")
            continue

    if not processed_tracks:
        print("❌ No tracks processed successfully. Aborting.")
        return {"error": "DSP processing failed"}

    # ── STEP 3: Assemble master audio ────────────────────────────
    print(f"\n[3/5] 🎶 Assembling master LoFi audio ({len(processed_tracks)} tracks)...")
    master_audio = cache_dir / "master_lofi_mix.m4a"
    concat_txt = cache_dir / "audio_concat.txt"

    with open(concat_txt, "w", encoding="utf-8") as f:
        for p in processed_tracks:
            f.write(f"file '{p.resolve().as_posix()}'\n")

    subprocess.run([
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-f", "concat", "-safe", "0", "-i", str(concat_txt),
        "-c", "copy", str(master_audio)
    ], check=True)
    total_duration = get_audio_duration(master_audio)
    print(f"  ✅ Master audio: {format_timestamp(total_duration)} total length")

    # ── STEP 4: Fetch B-roll + Render Video ─────────────────────
    print(f"\n[4/5] 🎬 Fetching B-roll & rendering video...")
    broll_clips = get_lofi_broll_clips(
        count=4,
        output_dir=cache_dir / "broll",
        mood="night aesthetic lofi"
    )

    final_video = output_dir / "final_lofi_mashup.mp4"
    font_path = Path(__file__).parent / "assets" / "font.ttf"

    render_lofi_video(
        background_source=background_image,
        audio_path=master_audio,
        output_video=final_video,
        track_title=mixtape_title,
        broll_clips=broll_clips if broll_clips else None,
        font_path=font_path if font_path.exists() else None,
    )

    # ── STEP 5: Generate YouTube description + timestamps ────────
    print(f"\n[5/5] 📋 Generating YouTube description...")
    seo_tags = (
        "#HindiLoFi #SlowedReverb #NightVibes #BollywoodLoFi #LofiBeats "
        "#ChillMusic #StudyMusic #LofiMix #SadLofi #MidnightVibes "
        "#IndianLofi #SlowedSongs #LofiChill #RainyNight #SelfRespect"
    )

    desc_lines = [
        f"🌙 {mixtape_title}",
        "",
        "✨ Slowed + Reverb | LoFi Chill | Night Vibes ✨",
        "🎧 Perfect for: studying, sleeping, chilling, late nights",
        "",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "🎵 TRACKLIST:",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
    ]
    for ts in timestamps:
        desc_lines.append(f"{ts['timestamp']} ▶ {ts['title']} — {ts['artist']}")

    desc_lines.extend([
        "",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "🌌 All tracks are copyright-free / Creative Commons licensed.",
        "👉 Subscribe for daily LoFi & Slowed+Reverb drops!",
        "🔔 Hit the bell to never miss an upload!",
        "",
        seo_tags,
    ])

    desc_text = "\n".join(desc_lines)
    desc_file = output_dir / "youtube_description.txt"
    desc_file.write_text(desc_text, encoding="utf-8")
    print(f"  ✅ Description saved to: {desc_file}")

    # Save metadata JSON
    meta = {
        "video_path": str(final_video),
        "description": desc_text,
        "title": mixtape_title,
        "timestamps": timestamps,
        "total_duration_sec": total_duration,
        "total_duration_fmt": format_timestamp(total_duration),
        "track_count": len(processed_tracks),
    }
    meta_file = output_dir / "metadata.json"
    meta_file.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")

    print("\n" + "="*60)
    print(f"🎉 DONE! LoFi Mixtape complete!")
    print(f"   📹 Video: {final_video}")
    print(f"   ⏱️  Duration: {format_timestamp(total_duration)}")
    print(f"   🎵  Tracks: {len(processed_tracks)}")
    print("="*60)

    # ── Optional: Auto-upload to YouTube ────────────────────────
    if upload_to_youtube:
        print("\n📤 Uploading to YouTube (unlisted)...")
        _upload_to_youtube(final_video, mixtape_title, desc_text)

    return meta


def _upload_to_youtube(video_path: Path, title: str, description: str):
    """Upload the final video to YouTube as unlisted using the factshorts uploader."""
    try:
        # Try to use the existing uploader from factshorts-bot
        uploader_path = Path(__file__).parent.parent / "factshorts-bot" / "factshorts" / "uploader.py"
        if not uploader_path.exists():
            print("⚠️  factshorts uploader not found. Manual upload required.")
            return

        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload
        import google.oauth2.credentials

        creds_path = Path(__file__).parent.parent / "factshorts-bot" / "credentials" / "token.json"
        if not creds_path.exists():
            print("⚠️  YouTube credentials not found. Manual upload required.")
            return

        creds_data = json.loads(creds_path.read_text())
        creds = google.oauth2.credentials.Credentials(**creds_data)
        youtube = build("youtube", "v3", credentials=creds)

        request_body = {
            "snippet": {
                "title": title[:100],
                "description": description[:5000],
                "tags": ["hindi lofi", "slowed reverb", "night vibes", "lofi beats", "bollywood lofi"],
                "categoryId": "10",  # Music
            },
            "status": {"privacyStatus": "unlisted"}
        }
        media = MediaFileUpload(str(video_path), chunksize=-1, resumable=True, mimetype="video/mp4")
        response = youtube.videos().insert(
            part="snippet,status",
            body=request_body,
            media_body=media
        ).execute()

        video_id = response.get("id", "unknown")
        print(f"✅ Uploaded! YouTube URL: https://www.youtube.com/watch?v={video_id}")
    except Exception as e:
        print(f"❌ Upload failed: {e}")
        print(f"📁 Manual upload: {video_path}")
