"""Utility script to send newly generated video to Telegram."""
import os
import sys
import glob
from pathlib import Path
import httpx

# UTF-8 for console
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8809830963:AAG22CFChal-D13uSkNLUmCoyHD3FGvgWjY")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "6486771356")


def find_latest_video(search_dirs: list[str]) -> Path | None:
    all_videos = []
    for sdir in search_dirs:
        for p in Path(sdir).glob("**/*.mp4"):
            if not p.name.startswith("tg_") and p.is_file() and p.stat().st_size > 100000:
                all_videos.append(p)
    if not all_videos:
        return None
    # Sort by modification time, newest first
    all_videos.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    return all_videos[0]


def send_video(video_path: Path):
    if not BOT_TOKEN or not CHAT_ID:
        print("❌ Telegram BOT_TOKEN or CHAT_ID missing. Skipping Telegram notification.")
        return False

    size_mb = video_path.stat().st_size / (1024 * 1024)
    print(f"📦 Found generated video: {video_path.name} ({size_mb:.2f} MB)")
    print(f"🚀 Sending directly to Telegram Chat ID: {CHAT_ID}...")

    caption = (
        f"🎬 *New Video Generated!*\n\n"
        f"📁 *File:* `{video_path.name}`\n"
        f"📊 *Size:* `{size_mb:.2f} MB`\n\n"
        f"✅ Download and post to your channel manually if needed!"
    )

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendVideo"
    
    with open(video_path, "rb") as f:
        files = {"video": (video_path.name, f, "video/mp4")}
        data = {
            "chat_id": CHAT_ID,
            "caption": caption,
            "parse_mode": "Markdown",
            "supports_streaming": "true"
        }
        try:
            with httpx.Client(timeout=300.0) as client:
                resp = client.post(url, data=data, files=files)
                if resp.status_code == 200:
                    print("✅ VIDEO SUCCESSFULLY DELIVERED TO YOUR TELEGRAM!")
                    return True
                else:
                    print(f"⚠️ Telegram API response ({resp.status_code}): {resp.text}")
                    # Try sending as document fallback
                    doc_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument"
                    f.seek(0)
                    resp_doc = client.post(doc_url, data={"chat_id": CHAT_ID, "caption": caption}, files={"document": (video_path.name, f, "video/mp4")})
                    if resp_doc.status_code == 200:
                        print("✅ Video sent as document successfully to Telegram!")
                        return True
                    return False
        except Exception as exc:
            print(f"❌ Error sending to Telegram: {exc}")
            return False


if __name__ == "__main__":
    target_path = None
    if len(sys.argv) > 1 and os.path.exists(sys.argv[1]):
        target_path = Path(sys.argv[1])
    else:
        target_path = find_latest_video(["factshorts-bot/output", "vox_studio/output", "output", "."])

    if target_path and target_path.exists():
        send_video(target_path)
    else:
        print("⚠️ No output MP4 video found to send.")
