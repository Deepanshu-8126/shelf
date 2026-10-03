"""Zero-dependency Telegram video delivery script (pure Python standard library)."""
import os
import sys
import json
import sqlite3
import urllib.request
import urllib.parse
import uuid
from pathlib import Path

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
    seo = {"title": "", "description": "", "tags": ""}
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


def upload_multipart(url: str, fields: dict, file_field: str, file_path: Path) -> bool:
    """Send multipart/form-data via standard library urllib."""
    boundary = f"----WebKitFormBoundary{uuid.uuid4().hex}"
    body = bytearray()

    for k, v in fields.items():
        body.extend(f"--{boundary}\r\n".encode("utf-8"))
        body.extend(f'Content-Disposition: form-data; name="{k}"\r\n\r\n'.encode("utf-8"))
        body.extend(f"{v}\r\n".encode("utf-8"))

    filename = file_path.name
    body.extend(f"--{boundary}\r\n".encode("utf-8"))
    body.extend(f'Content-Disposition: form-data; name="{file_field}"; filename="{filename}"\r\n'.encode("utf-8"))
    body.extend(b"Content-Type: video/mp4\r\n\r\n")
    with open(file_path, "rb") as f:
        body.extend(f.read())
    body.extend(b"\r\n")
    body.extend(f"--{boundary}--\r\n".encode("utf-8"))

    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"}
    )

    try:
        with urllib.request.urlopen(req, timeout=300) as response:
            resp_data = json.loads(response.read().decode("utf-8"))
            if resp_data.get("ok"):
                return True
            print(f"⚠️ Telegram returned: {resp_data}")
            return False
    except Exception as exc:
        print(f"⚠️ Upload failed: {exc}")
        return False


def send_video(video_path: Path):
    if not BOT_TOKEN or not CHAT_ID:
        print("❌ Telegram BOT_TOKEN or CHAT_ID missing. Skipping Telegram notification.")
        return False

    size_mb = video_path.stat().st_size / (1024 * 1024)
    print(f"📦 Found video: {video_path.name} ({size_mb:.2f} MB)")
    print(f"🚀 Sending to Telegram Chat ID: {CHAT_ID}...")

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

    fields = {
        "chat_id": CHAT_ID,
        "caption": caption[:1024],
        "parse_mode": "Markdown",
        "supports_streaming": "true"
    }

    # First try sendVideo
    success = upload_multipart(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendVideo",
        fields,
        "video",
        video_path
    )

    if not success:
        print("🔄 Retrying as document...")
        fields.pop("supports_streaming", None)
        success = upload_multipart(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument",
            fields,
            "document",
            video_path
        )

    if success:
        print("✅ VIDEO SUCCESSFULLY DELIVERED TO YOUR TELEGRAM!")
    return success


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
