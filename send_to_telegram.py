"""Utility script to send newly generated video and SEO details to Telegram."""
import os
import sys
import glob
import json
import sqlite3
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
    all_videos.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    return all_videos[0]


def get_video_seo(video_path: Path) -> dict:
    """Try to get video SEO info from database or adjacent json file."""
    seo = {"title": "", "description": "", "tags": ""}
    
    # Check SQLite DB
    db_paths = [
        video_path.parent.parent / "data" / "factshorts.db",
        Path("factshorts-bot/data/factshorts.db"),
        Path("data/factshorts.db")
    ]
    for db_path in db_paths:
        if db_path.exists():
            try:
                conn = sqlite3.connect(str(db_path))
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT title, description, tags FROM videos WHERE video_path LIKE ? ORDER BY id DESC LIMIT 1",
                    (f"%{video_path.name}%",)
                )
                row = cursor.fetchone()
                if row:
                    seo["title"] = row[0] or ""
                    seo["description"] = row[1] or ""
                    try:
                        tags_list = json.loads(row[2] or "[]")
                        seo["tags"] = " ".join([f"#{t.replace(' ', '')}" for t in tags_list[:8]])
                    except Exception:
                        seo["tags"] = row[2] or ""
                    conn.close()
                    return seo
                conn.close()
            except Exception:
                pass

    # Check json sidecar
    json_path = video_path.with_suffix(".json")
    if json_path.exists():
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                seo["title"] = data.get("title", "")
                seo["description"] = data.get("description", "")
        except Exception:
            pass

    return seo


def send_video(video_path: Path):
    if not BOT_TOKEN or not CHAT_ID:
        print("❌ Telegram BOT_TOKEN or CHAT_ID missing. Skipping Telegram notification.")
        return False

    size_mb = video_path.stat().st_size / (1024 * 1024)
    print(f"📦 Found generated video: {video_path.name} ({size_mb:.2f} MB)")
    print(f"🚀 Sending directly to Telegram Chat ID: {CHAT_ID}...")

    seo = get_video_seo(video_path)
    title = seo.get("title") or video_path.stem.replace("-", " ").title()
    tags = seo.get("tags") or "#Shorts #Facts #Viral #YouTubeShorts"

    caption = (
        f"🎬 *{title}*\n\n"
        f"📁 *File:* `{video_path.name}`\n"
        f"📊 *Size:* `{size_mb:.2f} MB`\n\n"
        f"🏷️ *Tags:* {tags}\n\n"
        f"✅ Video render complete! Ready to upload."
    )

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendVideo"
    
    with open(video_path, "rb") as f:
        files = {"video": (video_path.name, f, "video/mp4")}
        data = {
            "chat_id": CHAT_ID,
            "caption": caption[:1024],
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
                    print(f"⚠️ Telegram sendVideo response ({resp.status_code}): {resp.text}")
                    # Try fallback to sendDocument
                    doc_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument"
                    f.seek(0)
                    resp_doc = client.post(
                        doc_url,
                        data={"chat_id": CHAT_ID, "caption": caption[:1024], "parse_mode": "Markdown"},
                        files={"document": (video_path.name, f, "video/mp4")}
                    )
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
        arg_path = Path(sys.argv[1])
        if arg_path.is_file():
            target_path = arg_path
        elif arg_path.is_dir():
            target_path = find_latest_video([str(arg_path)])
    
    if not target_path:
        target_path = find_latest_video(["factshorts-bot/output", "vox_studio/output", "output", "."])

    if target_path and target_path.exists():
        send_video(target_path)
    else:
        print("⚠️ No output MP4 video found to send.")
