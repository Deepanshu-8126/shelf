"""
Master Multi-Channel Registry & Real-Time Production Tracker for Super YouTube Agent.
Scans and monitors real filesystem outputs, video assets, YouTube metadata,
and execution status across all 7 production channels.
"""
from __future__ import annotations
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
CHANNELS_DIR = Path(__file__).resolve().parent
DATA_DIR = CHANNELS_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
REGISTRY_CACHE_FILE = DATA_DIR / "master_channels_state.json"

CHANNELS_CONFIG = {
    1: {
        "id": "chan1_facts",
        "name": "Channel 1: Viral Facts Shorts",
        "badge": "🎬 FACTS SHORTS",
        "folder": "01_facts_shorts",
        "format": "9:16 Shorts (30-60s)",
        "output_dirs": ["output", "01_facts_shorts/output"],
        "runner_cmd": [sys.executable, "super_youtube_agent/unified_creative_engine.py", "--channel", "1"],
        "default_arg": "--demo"
    },
    2: {
        "id": "chan2_story",
        "name": "Channel 2: Story & Gaming Studio",
        "badge": "🕹️ STORY STUDIO",
        "folder": "02_story_studio",
        "format": "16:9 & 9:16 Stories",
        "output_dirs": ["output", "02_story_studio/data/packages", "02_story_studio/data/gaming_sources"],
        "runner_cmd": [sys.executable, "super_youtube_agent/unified_creative_engine.py", "--channel", "2"],
        "default_arg": ""
    },
    3: {
        "id": "chan3_vox",
        "name": "Channel 3: Vox & Geopolitics Studio",
        "badge": "🌐 VOX LEDGER",
        "folder": "03_vox_studio",
        "format": "9:16 & 16:9 Map Docs",
        "output_dirs": ["output", "03_vox_studio/output"],
        "runner_cmd": [sys.executable, "super_youtube_agent/unified_creative_engine.py", "--channel", "3"],
        "default_arg": "--generate"
    },
    4: {
        "id": "chan4_lofi",
        "name": "Channel 4: Lofi 24/7 Music Studio",
        "badge": "☕ LOFI AMBIENT",
        "folder": "04_lofi_studio",
        "format": "16:9 Audio DSP Streams",
        "output_dirs": ["output", "04_lofi_studio/output"],
        "runner_cmd": [sys.executable, "super_youtube_agent/unified_creative_engine.py", "--channel", "4"],
        "default_arg": "--generate"
    },
    5: {
        "id": "chan5_dark",
        "name": "Channel 5: Dark Sutra Crime Studio",
        "badge": "🕵️ DARK SUTRA",
        "folder": "05_dark_sutra",
        "format": "9:16 & 16:9 True Crime",
        "output_dirs": ["output", "05_dark_sutra/output"],
        "runner_cmd": [sys.executable, "super_youtube_agent/unified_creative_engine.py", "--channel", "5"],
        "default_arg": "--case"
    },
    6: {
        "id": "chan6_clipper",
        "name": "Channel 6: AI Auto Clipper",
        "badge": "✂️ AI CLIPPER",
        "folder": "06_ai_clipper",
        "format": "9:16 Viral Cuts",
        "output_dirs": ["output", "06_ai_clipper/Shorts", "06_ai_clipper/video_use_workspace"],
        "runner_cmd": [sys.executable, "super_youtube_agent/unified_creative_engine.py", "--channel", "6"],
        "default_arg": ""
    },
    7: {
        "id": "chan7_coding",
        "name": "Channel 7: Coding & Tech Studio",
        "badge": "💻 CODING STUDIO",
        "folder": "07_coding_studio",
        "format": "9:16 Line-by-Line IDE",
        "output_dirs": ["output", "07_coding_studio/output"],
        "runner_cmd": [sys.executable, "super_youtube_agent/unified_creative_engine.py", "--channel", "7"],
        "default_arg": "--next"
    }
}



def scan_channel_real_metrics(chan_num: int) -> Dict[str, Any]:
    """Scans physical disk for actual rendered MP4 files and metadata for a channel."""
    cfg = CHANNELS_CONFIG.get(chan_num)
    if not cfg:
        return {}

    rendered_files: List[Dict[str, Any]] = []
    total_bytes = 0

    for rel_out in cfg["output_dirs"]:
        out_path = CHANNELS_DIR / rel_out
        if out_path.exists():
            for mp4 in out_path.rglob("*.mp4"):
                try:
                    stat = mp4.stat()
                    total_bytes += stat.st_size
                    rendered_files.append({
                        "name": mp4.name,
                        "path": str(mp4),
                        "size_mb": round(stat.st_size / (1024 * 1024), 2),
                        "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                        "mtime": stat.st_mtime
                    })
                except Exception:
                    pass

    # Sort newest first
    rendered_files.sort(key=lambda x: x["mtime"], reverse=True)
    latest_video = rendered_files[0] if rendered_files else None

    # Check Channel 7 series progress specifically if applicable
    extra_meta: Dict[str, Any] = {}
    if chan_num == 7:
        prog_file = DATA_DIR / "series_progress.json"
        if prog_file.exists():
            try:
                p_data = json.loads(prog_file.read_text(encoding="utf-8"))
                extra_meta["current_day"] = p_data.get("core_series", {}).get("current_day", 1)
                extra_meta["secondary_niche"] = p_data.get("secondary_series", {}).get("active_niche", "java")
            except Exception:
                pass

    return {
        "channel_num": chan_num,
        "name": cfg["name"],
        "badge": cfg["badge"],
        "format": cfg["format"],
        "folder": cfg["folder"],
        "total_videos": len(rendered_files),
        "total_storage_mb": round(total_bytes / (1024 * 1024), 2),
        "latest_video": latest_video,
        "extra_meta": extra_meta,
        "is_ready": True
    }


def scan_all_channels() -> Dict[str, Any]:
    """Scans all 7 channels and returns a unified production snapshot."""
    channels_data = {}
    grand_total_videos = 0
    grand_total_mb = 0.0

    for ch_num in range(1, 8):
        m = scan_channel_real_metrics(ch_num)
        channels_data[ch_num] = m
        grand_total_videos += m["total_videos"]
        grand_total_mb += m["total_storage_mb"]

    snapshot = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_channels": 7,
        "grand_total_videos": grand_total_videos,
        "grand_total_storage_gb": round(grand_total_mb / 1024.0, 2),
        "channels": channels_data
    }

    # Save to cache
    try:
        REGISTRY_CACHE_FILE.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception as e:
        print(f"⚠️ [Registry] Cache write error: {e}")

    return snapshot


def get_live_matrix_markdown() -> str:
    """Formats a dense, high-signal Telegram Markdown dashboard of all 7 channels."""
    snap = scan_all_channels()
    now_str = datetime.now().strftime("%d %b %Y • %I:%M %p")

    lines = [
        "🌐 *SUPER YOUTUBE AGENT // 7-CHANNEL MISSION CONTROL*",
        f"🕒 Status Snapshot: `{now_str}`",
        f"📦 *Total Fleet Output*: `{snap['grand_total_videos']} Master Videos` (`{snap['grand_total_storage_gb']} GB`)",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    ]

    icons = {1: "🎬", 2: "🕹️", 3: "🌐", 4: "☕", 5: "🕵️", 6: "✂️", 7: "💻"}

    for ch_num in range(1, 8):
        ch = snap["channels"][ch_num]
        latest = ch["latest_video"]
        latest_str = f"`{latest['name'][:26]}` ({latest['size_mb']}MB)" if latest else "_No renders yet_"

        extra_info = ""
        if ch_num == 7:
            day = ch.get("extra_meta", {}).get("current_day", 1)
            extra_info = f" • *Day {day}/100*"

        lines.append(f"{icons[ch_num]} *Ch {ch_num}*: *{ch['badge']}*{extra_info}")
        lines.append(f"   📊 `{ch['total_videos']} videos` ({ch['total_storage_mb']}MB) • Latest: {latest_str}")

    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("📱 *Tap a button below to trigger or inspect any channel!*")
    return "\n".join(lines)


if __name__ == "__main__":
    print(get_live_matrix_markdown())
