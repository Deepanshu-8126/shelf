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

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", DEFAULT_BOT_TOKEN).strip()
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", DEFAULT_CHAT_ID).strip()
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
        channel_name = "Channel 1: Funcyous"
        channel_badge = "🎭 VIRAL REDDIT DRAMA & CONFESSIONS"
        extra_tags = "#shorts #redditstories #reddit #drama #viral"
    elif channel == 3:
        channel_name = "Channel 3: Cosmic What-If"
        channel_badge = "🌌 COSMIC WHAT-IF & DEEP UNIVERSE"
        extra_tags = "#shorts #cosmic #space #science #whatif #universe #hindi"
    else:
        channel_name = "Channel 2: Mystery & Curiosity"
        channel_badge = "🕵️ ZACK D. FILMS / VOX HINDI MYSTERY"
        extra_tags = "#shorts #mystery #unsolved #facts #science #viral"

    caption_card = [
        f"🎬 *{channel_badge}*",
        f"📺 *Channel:* `{channel_name}`",
        f"🕒 *Rendered at:* `{timing['current_ist']}`",
        "",
        f"📌 *Video Title:*",
        f"*{title}*",
        "",
        f"📝 *Description & Hashtags:*",
        f"{description[:250]}...",
        f"`{hashtags_str} {extra_tags}`",
        ""
    ]

    if youtube_url:
        caption_card.extend([
            f"🔗 *YouTube Direct Link:*",
            f"👉 {youtube_url}",
            f"🔒 *Privacy:* `{privacy.upper()}` (Safe Pre-Publish)",
            ""
        ])
    else:
        caption_card.extend([
            f"🔒 *Status:* Rendered & Verified (Ready to upload)",
            ""
        ])

    caption_card.extend([
        f"⏰ *Dynamic Viral Timing Recommendation:*",
        f"• *Optimal Publish Window:* *{timing['best_slot']}*",
        f"• *Algorithmic Reason:* _{timing['reason']}_",
        f"• *Growth Tip:* Pin a controversial debate comment in the first 10 minutes to supercharge watch time! 🚀"
    ])

    full_text = "\n".join(caption_card)
    short_caption = "\n".join(caption_card[:7]) + f"\n\n🔗 YouTube: {youtube_url or 'Rendered'}\n⏰ Best Time: {timing['best_slot']}"

    print(f"📱 Delivering video to Telegram ({video_path.name})...", flush=True)

    try:
        # Check size (Telegram Bot API limit is 50MB for bots)
        size_mb = video_path.stat().st_size / (1024 * 1024)
        print(f"📊 Video file size: {size_mb:.2f} MB", flush=True)

        with open(video_path, "rb") as vf:
            files = {"video": (video_path.name, vf, "video/mp4")}
            data = {
                "chat_id": CHAT_ID,
                "caption": short_caption[:1000],
                "parse_mode": "Markdown",
                "supports_streaming": "true"
            }
            with httpx.Client(timeout=120) as client:
                res = client.post(f"{API_BASE}/sendVideo", data=data, files=files)
                
            if res.status_code == 200:
                print("✅ Telegram video delivery SUCCESSFUL!", flush=True)
            else:
                print(f"⚠️ Telegram video upload returned {res.status_code}: {res.text}", flush=True)

        # Send full metadata as follow-up message
        with httpx.Client(timeout=30) as client:
            client.post(f"{API_BASE}/sendMessage", json={
                "chat_id": CHAT_ID,
                "text": full_text,
                "parse_mode": "Markdown",
                "disable_web_page_preview": False
            })

        return True
    except Exception as e:
        print(f"⚠️ Telegram delivery error: {e}", flush=True)
        return False


if __name__ == "__main__":
    t = calculate_optimal_viral_time()
    print("Optimal timing preview:", json.dumps(t, indent=2))
