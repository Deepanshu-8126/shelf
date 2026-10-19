"""
Production-grade Telegram Dispatcher for Fleet Video Channels.
Delivers:
  1. Rendered MP4 Short directly to user's Telegram phone.
  2. Beautiful Markdown Card with:
     - Channel Badge (Channel 1: Funcyous / Channel 2: Hindi Mystery)
     - Curated Title with emojis
     - Full Description with viral tags & hashtags
     - Direct YouTube Video URL (if uploaded)
     - Privacy Status: Unlisted (Safe Mode)
     - Dynamic Viral Timing Recommendation (IST Prime Time)
"""
from __future__ import annotations
import os
import sys
import json
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional
import httpx

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent

DEFAULT_BOT_TOKEN = "8809830963:AAG22CFChal-D13uSkNLUmCoyHD3FGvgWjY"
DEFAULT_CHAT_ID = "6486771356"

BOT_TOKEN = (os.getenv("TELEGRAM_BOT_TOKEN") or DEFAULT_BOT_TOKEN).strip()
CHAT_ID = (os.getenv("TELEGRAM_CHAT_ID") or DEFAULT_CHAT_ID).strip()
API_BASE = f"https://api.telegram.org/bot{BOT_TOKEN}"


def calculate_optimal_viral_time() -> Dict[str, str]:
    """Calculates peak Indian viewer prime-time recommendations dynamically."""
    # Current IST (UTC+5:30)
    ist = timezone(timedelta(hours=5, minutes=30))
    now = datetime.now(ist)
    current_hour = now.hour

    if current_hour < 12:
        slot = "🚀 Today 1:00 PM – 2:30 PM IST (Lunch Spike)"
        reason = "College & office break audience browsing feeds."
    elif current_hour < 17:
        slot = "🔥 Today 6:30 PM – 8:30 PM IST (Prime Peak)"
        reason = "Highest engagement & algorithmic watch-time window."
    elif current_hour < 21:
        slot = "🌙 Today 9:30 PM – 11:00 PM IST (Night Chill)"
        reason = "Extended session times & highest comment-to-view ratio."
    else:
        slot = "🌅 Tomorrow 12:30 PM – 2:00 PM IST"
        reason = "Schedule for tomorrow's midday algorithmic reset."

    return {
        "best_slot": slot,
        "reason": reason,
        "current_ist": now.strftime("%I:%M %p IST (%d %b)")
    }


def send_fleet_video_to_telegram(
    video_path: Path,
    channel: int,
    title: str,
    description: str,
    tags: Optional[List[str]] = None,
    youtube_url: Optional[str] = None,
    privacy: str = "unlisted"
) -> bool:
    """Delivers video file and comprehensive metadata report to Telegram."""
    if not video_path.exists():
        print(f"⚠️ Video not found: {video_path}")
        return False

    tags = tags or []
    hashtags_str = " ".join([f"#{t.replace(' ', '')}" for t in tags[:10] if not t.startswith("#")])
    timing = calculate_optimal_viral_time()

    if channel == 1:
        channel_name = "Channel 1: Funcyous (Reddit Drama)"
        channel_badge = "🎭 VIRAL REDDIT DRAMA & CONFESSIONS"
        channel_slot = "Daily 4:30 PM IST (11:00 UTC)"
        extra_tags = "#shorts #redditstories #reddit #drama #viral"
    elif channel == 3:
        channel_name = "Channel 3: Cosmic What-If (हिंदी)"
        channel_badge = "🌌 COSMIC WHAT-IF & DEEP UNIVERSE"
        channel_slot = "Daily 8:30 PM IST (15:00 UTC)"
        extra_tags = "#shorts #cosmic #space #science #whatif #universe #hindi"
    else:
        channel_name = "Channel 2: Mystery & Curiosity"
        channel_badge = "🕵️ VOX MYSTERY & UNSOLVED ANOMALIES"
        channel_slot = "Daily 6:30 PM IST (13:00 UTC)"
        extra_tags = "#shorts #mystery #unsolved #facts #science #viral"

    # Clean title to prevent Markdown crash
    safe_title = title.replace("*", "").replace("_", "").replace("`", "").strip()
    safe_desc = description[:160].replace("*", "").replace("_", "").replace("`", "").strip()

    caption_lines = [
        f"🎬 *{channel_badge}*",
        f"📺 *Channel:* `{channel_name}`",
        f"⏰ *Timeline Slot:* `{channel_slot}`",
        "",
        f"📌 *Video Title:*",
        f"*{safe_title}*",
        "",
        f"📝 *Synopsis:* {safe_desc}...",
        f"`{hashtags_str} {extra_tags}`",
        ""
    ]

    if youtube_url:
        caption_lines.append(f"🔗 *YouTube Link:* {youtube_url} ({privacy.upper()})")
    else:
        caption_lines.append(f"🔒 *Status:* Rendered & Verified (Ready to upload)")

    caption_lines.append(f"🚀 *Peak Viral Window:* {timing['best_slot']}")

    single_caption = "\n".join(caption_lines)
    if len(single_caption) > 1020:
        single_caption = single_caption[:1015] + "..."

    print(f"📱 Delivering video to Telegram ({video_path.name})...", flush=True)

    try:
        size_mb = video_path.stat().st_size / (1024 * 1024)
        print(f"📊 Video file size: {size_mb:.2f} MB", flush=True)

        with open(video_path, "rb") as vf:
            files = {"video": (video_path.name, vf, "video/mp4")}
            data = {
                "chat_id": CHAT_ID,
                "caption": single_caption,
                "parse_mode": "Markdown",
                "supports_streaming": "true"
            }
            with httpx.Client(timeout=120) as client:
                res = client.post(f"{API_BASE}/sendVideo", data=data, files=files)
                if res.status_code != 200:
                    # Retry without Markdown in case of syntax character clash
                    data.pop("parse_mode", None)
                    plain_caption = single_caption.replace("*", "").replace("`", "")
                    data["caption"] = plain_caption
                    vf.seek(0)
                    res = client.post(f"{API_BASE}/sendVideo", data=data, files=files)
                
            if res.status_code == 200:
                print("✅ Telegram video delivery SUCCESSFUL! (Single high-signal notification)", flush=True)
                return True
            else:
                print(f"⚠️ Telegram video upload returned {res.status_code}: {res.text}", flush=True)
                return False

    except Exception as e:
        print(f"⚠️ Telegram delivery error: {e}", flush=True)
        return False


if __name__ == "__main__":
    t = calculate_optimal_viral_time()
    print("Optimal timing preview:", json.dumps(t, indent=2))
