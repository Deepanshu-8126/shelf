"""
==============================================================================
☁️ CLOUD PHOTOSHOOT & PINTEREST 4K POST RUNNER (GitHub Actions / Cloud)
==============================================================================
Runs in cloud or local:
1. Loads product CSV (`meesho-com-2026-10-03.csv`).
2. Generates brand-level 21yo Indian Model photoshoot prompts.
3. Downloads HD photos, cleanly erases Gemini/watermark logos (delogo).
4. Applies 4K Micro-Sharpening, Portra 400 color calibration, and Luxury Price Card.
5. Uploads / Dispatches rendered 4K pins to Telegram (6486771356).
==============================================================================
"""

import os
import sys
import json
import time
import argparse
import urllib.request
from pathlib import Path
from PIL import Image

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Import core processor functions
from photoshoot_pinterest_engine.process_all_125_photos import (
    extract_all_photo_records,
    download_and_polish_single,
    CSV_FILE,
    RAW_PHOTOS_DIR,
    RENDERED_DIR
)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8809830963:AAG22CFChal-D13uSkNLUmCoyHD3FGvgWjY").strip()
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "6486771356").strip()


def send_photo_to_telegram(photo_path: Path, title: str, price: str, category: str, mood: str, prompt: str) -> bool:
    """Dispatches 4K polished pin to Telegram with Pinterest/Instagram ready caption."""
    if not photo_path.exists():
        return False
    try:
        import uuid
        caption = (
            f"📸 *4K PHOTOSHOOT PIN: {title.upper()}* ✨\n\n"
            f"🥻 *Category:* {category}\n"
            f"🎭 *Expression Mood:* {mood}\n"
            f"💰 *Deal Price:* `{price}` (Limited Discount)\n"
            f"⭐ *Quality:* 4K UHD • Delogo Clean • Studio Grade\n\n"
            f"🎨 *Master Prompt (Veo/Imagen/Flux):*\n"
            f"_{prompt[:320]}..._\n\n"
            f"🏷️ *Tags:* #MeeshoFashion #OOTD #SareeLookbook #Photoshoot #PinterestFashion"
        )

        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
        boundary = f"----WebKitFormBoundary{uuid.uuid4().hex}"
        body = bytearray()

        fields = {
            "chat_id": TELEGRAM_CHAT_ID,
            "caption": caption[:1024],
            "parse_mode": "Markdown"
        }

        for k, v in fields.items():
            body.extend(f"--{boundary}\r\n".encode("utf-8"))
            body.extend(f'Content-Disposition: form-data; name="{k}"\r\n\r\n'.encode("utf-8"))
            body.extend(f"{v}\r\n".encode("utf-8"))

        body.extend(f"--{boundary}\r\n".encode("utf-8"))
        body.extend(f'Content-Disposition: form-data; name="photo"; filename="{photo_path.name}"\r\n'.encode("utf-8"))
        body.extend(b"Content-Type: image/jpeg\r\n\r\n")
        with open(photo_path, "rb") as f:
            body.extend(f.read())
        body.extend(b"\r\n")
        body.extend(f"--{boundary}--\r\n".encode("utf-8"))

        req = urllib.request.Request(
            url,
            data=body,
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}"}
        )

        with urllib.request.urlopen(req, timeout=30) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            if res_data.get("ok"):
                print(f"  ✅ Delivered 4K Pin to Telegram: {photo_path.name}")
                return True
    except Exception as e:
        print(f"  ⚠️ Telegram dispatch notice: {e}")
    return False


def run_cloud_photoshoot_pipeline(csv_path: Path, max_count: int = 5, dispatch_telegram: bool = True):
    print("=" * 75)
    print("🚀 RUNNING CLOUD 4K PHOTOSHOOT & PINTEREST ENGINE")
    print(f"📁 Target CSV: {csv_path.name} | Max Photos: {max_count}")
    print("=" * 75)

    records = extract_all_photo_records(csv_path)
    if not records:
        print("❌ No valid photo records found in CSV.")
        return

    if max_count > 0:
        records = records[:max_count]

    print(f"📋 Processing {len(records)} photos...")

    for idx, item in enumerate(records, 1):
        print(f"\n[{idx}/{len(records)}] Rendering: {item['title']} ({item['price']})")
        res = download_and_polish_single(idx, item)

        if res["status"] == "SUCCESS":
            rendered_path = Path(res["rendered_pin_path"])
            print(f"  ✨ [4K Ready]: {rendered_path.name}")
            if dispatch_telegram:
                send_photo_to_telegram(
                    rendered_path,
                    res["title"],
                    res["price"],
                    res["category"],
                    res["mood"],
                    res["prompt"]
                )
        else:
            print(f"  ❌ Failed: {res.get('error', 'Unknown')}")

        time.sleep(1)

    print("\n" + "=" * 75)
    print("🎉 CLOUD PHOTOSHOOT RUN COMPLETED!")
    print(f"🖼️ Output Directory: {RENDERED_DIR}")
    print("=" * 75)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cloud Photoshoot Post Runner")
    parser.add_argument("--csv", type=str, default=str(CSV_FILE), help="CSV path")
    parser.add_argument("--max", type=int, default=5, help="Max photos to process")
    parser.add_argument("--telegram", action="store_true", default=True, help="Dispatch to Telegram")
    args = parser.parse_args()

    run_cloud_photoshoot_pipeline(Path(args.csv), max_count=args.max, dispatch_telegram=args.telegram)
