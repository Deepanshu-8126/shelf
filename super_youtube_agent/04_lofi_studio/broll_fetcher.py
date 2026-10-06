"""
LoFi B-Roll Fetcher: Downloads real aesthetic video clips from Pexels API.

Uses Pexels free API to get:
- Rainy windows, city nights, coffee shops
- Nature scenes: forests, rivers, moonlight
- Aesthetic interiors: cozy rooms, candles, books

All Pexels videos are royalty-free for commercial use.
"""
from __future__ import annotations

import json
import os
import random
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Optional

PEXELS_API_KEY = os.getenv("PEXELS_API_KEY", "")

# Search queries for aesthetic lofi B-roll
LOFI_BROLL_QUERIES = [
    "rain window night city",
    "cozy coffee shop aesthetic",
    "moonlight forest night",
    "candle books dark aesthetic",
    "cherry blossom night lofi",
    "city rain street lights",
    "autumn leaves falling slow",
    "snow falling night cozy",
    "fireplace cozy night",
    "sunset rooftop city",
    "rainy day window drops",
    "vintage cassette tape",
]

# Fallback: Pexels video IDs (pre-verified royalty-free aesthetic clips)
FALLBACK_VIDEO_IDS = [
    1105666,  # Rain on window
    3571264,  # City night timelapse
    3843166,  # Cozy fireplace
    4065876,  # Autumn leaves
    4622926,  # Coffee steam
    5319533,  # Night city rain
    6005391,  # Candle flame
    7640812,  # Snow falling
    4629874,  # Forest moonlight
    3163534,  # Aesthetic vintage
]


def fetch_pexels_videos(
    query: str,
    count: int = 3,
    orientation: str = "landscape"
) -> list[dict]:
    """Fetch video clips from Pexels API."""
    if not PEXELS_API_KEY:
        return []

    params = urllib.parse.urlencode({
        "query": query,
        "per_page": count,
        "orientation": orientation,
    })
    url = f"https://api.pexels.com/videos/search?{params}"
    headers = {"Authorization": PEXELS_API_KEY}

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())

        clips = []
        for video in data.get("videos", []):
            # Get HD video file
            files = sorted(
                video.get("video_files", []),
                key=lambda x: x.get("width", 0),
                reverse=True
            )
            hd_file = next(
                (f for f in files if f.get("width", 0) >= 1280 and f.get("width", 0) <= 1920),
                files[0] if files else None
            )
            if hd_file:
                clips.append({
                    "id": video["id"],
                    "url": hd_file["link"],
                    "width": hd_file.get("width", 1920),
                    "height": hd_file.get("height", 1080),
                    "duration": video.get("duration", 30),
                    "photographer": video.get("user", {}).get("name", "Pexels"),
                })
        return clips
    except Exception as e:
        print(f"  ⚠️  Pexels API error: {e}")
        return []


def fetch_pexels_video_by_id(video_id: int) -> Optional[dict]:
    """Fetch specific Pexels video by ID as fallback."""
    if not PEXELS_API_KEY:
        return None

    url = f"https://api.pexels.com/videos/videos/{video_id}"
    headers = {"Authorization": PEXELS_API_KEY}

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as resp:
            video = json.loads(resp.read().decode())

        files = sorted(
            video.get("video_files", []),
            key=lambda x: x.get("width", 0),
            reverse=True
        )
        hd_file = next(
            (f for f in files if 1280 <= f.get("width", 0) <= 1920),
            files[0] if files else None
        )
        if hd_file:
            return {
                "id": video["id"],
                "url": hd_file["link"],
                "width": hd_file.get("width", 1920),
                "height": hd_file.get("height", 1080),
                "duration": video.get("duration", 30),
                "photographer": video.get("user", {}).get("name", "Pexels"),
            }
    except Exception as e:
        print(f"  ⚠️  Pexels video ID {video_id} error: {e}")
    return None


def download_video_clip(clip: dict, output_dir: Path, idx: int = 0) -> Optional[Path]:
    """Download a video clip to local cache."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    out_path = output_dir / f"broll_{idx:02d}_{clip['id']}.mp4"
    if out_path.exists() and out_path.stat().st_size > 500_000:
        print(f"  📁 Cached B-roll: {out_path.name}")
        return out_path

    try:
        print(f"  ⬇️  Downloading B-roll {idx+1} (Pexels ID: {clip['id']})...")
        headers = {"User-Agent": "Mozilla/5.0 (compatible; LoFiStudio/1.0)"}
        req = urllib.request.Request(clip["url"], headers=headers)
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = resp.read()

        out_path.write_bytes(data)
        print(f"  ✅ B-roll saved: {out_path.name} ({len(data)//1024//1024} MB)")
        return out_path
    except Exception as e:
        print(f"  ❌ B-roll download failed: {e}")
        return None


def get_lofi_broll_clips(
    count: int = 4,
    output_dir: Path = Path("cache/broll"),
    mood: str = "night chill aesthetic"
) -> list[Path]:
    """
    Main function: Returns list of downloaded aesthetic B-roll video clips.
    
    With PEXELS_API_KEY: Fetches real search results
    Without key: Returns empty list (visual_engine uses static fallback image)
    """
    output_dir = Path(output_dir)
    all_clip_paths = []

    if not PEXELS_API_KEY:
        print("⚠️  No PEXELS_API_KEY — B-roll disabled. Will use static aesthetic image.")
        return []

    # Pick random aesthetic queries
    queries = random.sample(LOFI_BROLL_QUERIES, min(count, len(LOFI_BROLL_QUERIES)))
    all_clips = []

    for query in queries[:count]:
        clips = fetch_pexels_videos(query, count=2)
        all_clips.extend(clips)
        time.sleep(0.3)

    # Fallback to pre-verified IDs if needed
    if len(all_clips) < count:
        print(f"  🔄 Using fallback Pexels IDs...")
        fallback_ids = random.sample(FALLBACK_VIDEO_IDS, min(count, len(FALLBACK_VIDEO_IDS)))
        for vid_id in fallback_ids:
            clip = fetch_pexels_video_by_id(vid_id)
            if clip:
                all_clips.append(clip)

    # Download clips
    random.shuffle(all_clips)
    for idx, clip in enumerate(all_clips[:count]):
        local_path = download_video_clip(clip, output_dir, idx)
        if local_path:
            all_clip_paths.append(local_path)
        if len(all_clip_paths) >= count:
            break

    print(f"✅ B-roll ready: {len(all_clip_paths)} clips downloaded")
    return all_clip_paths
