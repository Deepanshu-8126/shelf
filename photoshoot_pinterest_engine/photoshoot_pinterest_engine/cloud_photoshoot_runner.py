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

MEMORY_DIR = CURRENT_DIR.parent / "data" / "memory"
MEMORY_DIR.mkdir(parents=True, exist_ok=True)
REGISTRY_FILE = MEMORY_DIR / "sent_photos_registry.json"

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8809830963:AAG22CFChal-D13uSkNLUmCoyHD3FGvgWjY").strip()
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "6486771356").strip()


def get_image_hash(filepath: Path) -> str:
    import hashlib
    hasher = hashlib.md5()
    try:
        with open(filepath, "rb") as f:
            buf = f.read(65536)
            while len(buf) > 0:
                hasher.update(buf)
                buf = f.read(65536)
        return hasher.hexdigest()
    except Exception:
        return ""


def load_photo_registry() -> dict:
    if REGISTRY_FILE.exists():
        try:
            with open(REGISTRY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"sent_hashes": [], "sent_filenames": []}


def save_photo_registry(reg: dict):
    try:
        with open(REGISTRY_FILE, "w", encoding="utf-8") as f:
            json.dump(reg, f, indent=2)
    except Exception as e:
        print(f"⚠️ Registry save notice: {e}")


def is_photo_locked(photo_path: Path, registry: dict) -> bool:
    if not photo_path.exists():
        return False
    if photo_path.name in registry.get("sent_filenames", []):
        return True
    f_hash = get_image_hash(photo_path)
    if f_hash and f_hash in registry.get("sent_hashes", []):
        return True
    return False


def register_sent_photos(photo_paths: list[Path], registry: dict):
    hashes = set(registry.get("sent_hashes", []))
    filenames = set(registry.get("sent_filenames", []))
    for p in photo_paths:
        if p.exists():
            h = get_image_hash(p)
            if h:
                hashes.add(h)
            filenames.add(p.name)
    registry["sent_hashes"] = list(hashes)
    registry["sent_filenames"] = list(filenames)
    save_photo_registry(registry)


def send_media_group_to_telegram(photo_paths: list[Path], title: str, price: str, category: str, mood: str, prompt: str) -> bool:
    """Dispatches multiple variations/angles of the SAME product together as a single swipeable album."""
    if not photo_paths:
        return False
    
    # Filter to only existing files (Max 10 per Telegram album)
    valid_photos = [p for p in photo_paths if p.exists()][:10]
    if not valid_photos:
        return False

    caption = (
        f"📸 *4K PHOTOSHOOT ALBUM: {title.upper()}* ✨\n\n"
        f"🥻 *Category:* {category} ({len(valid_photos)} Variations / Angles)\n"
        f"🎭 *Expression Mood:* {mood}\n"
        f"💰 *Deal Price:* `{price}` (Special Discount)\n"
        f"⭐ *Quality:* 4K UHD • Delogo Clean • Studio Grade\n\n"
        f"🎨 *Master Prompt:*\n"
        f"_{prompt[:280]}..._\n\n"
        f"🏷️ *Tags:* #MeeshoFashion #OOTD #SareeLookbook #Photoshoot #PinterestFashion"
    )

    if len(valid_photos) == 1:
        # Single photo dispatch
        return send_single_photo_to_telegram(valid_photos[0], caption)

    import uuid
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMediaGroup"
    boundary = f"----WebKitFormBoundary{uuid.uuid4().hex}"
    body = bytearray()

    media_array = []
    for i, p in enumerate(valid_photos):
        media_item = {
            "type": "photo",
            "media": f"attach://photo_{i}"
        }
        if i == 0:
            media_item["caption"] = caption[:1024]
            media_item["parse_mode"] = "Markdown"
        media_array.append(media_item)

    fields = {
        "chat_id": TELEGRAM_CHAT_ID,
        "media": json.dumps(media_array)
    }

    for k, v in fields.items():
        body.extend(f"--{boundary}\r\n".encode("utf-8"))
        body.extend(f'Content-Disposition: form-data; name="{k}"\r\n\r\n'.encode("utf-8"))
        body.extend(f"{v}\r\n".encode("utf-8"))

    for i, p in enumerate(valid_photos):
        body.extend(f"--{boundary}\r\n".encode("utf-8"))
        body.extend(f'Content-Disposition: form-data; name="photo_{i}"; filename="{p.name}"\r\n'.encode("utf-8"))
        body.extend(b"Content-Type: image/jpeg\r\n\r\n")
        with open(p, "rb") as f:
            body.extend(f.read())
        body.extend(b"\r\n")
    body.extend(f"--{boundary}--\r\n".encode("utf-8"))

    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"}
    )

    try:
        with urllib.request.urlopen(req, timeout=45) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            if res_data.get("ok"):
                print(f"  ✅ Delivered Album ({len(valid_photos)} photos together) to Telegram!")
                return True
            print(f"  ⚠️ Telegram response: {res_data}")
    except Exception as e:
        print(f"  ⚠️ Album dispatch error: {e}")
    return False


def send_single_photo_to_telegram(photo_path: Path, caption: str) -> bool:
    import uuid
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

    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            if res_data.get("ok"):
                print(f"  ✅ Delivered Single 4K Pin to Telegram: {photo_path.name}")
                return True
    except Exception as e:
        print(f"  ⚠️ Single photo dispatch error: {e}")
    return False


def run_cloud_photoshoot_pipeline(csv_path: Path, max_products: int = 5, dispatch_telegram: bool = True):
    print("=" * 75)
    print("🚀 RUNNING GROUPED 4K PHOTOSHOOT & PINTEREST ENGINE (ZERO REPEATS)")
    print(f"📁 Target CSV: {csv_path.name} | Max Products: {max_products}")
    print("=" * 75)

    records = extract_all_photo_records(csv_path)
    if not records:
        print("❌ No valid photo records found in CSV.")
        return

    registry = load_photo_registry()

    # Group photos by product (so variations are kept together)
    grouped_products = {}
    for r in records:
        p_key = (r["product_index"], r["title"], r["price"], r["fabric"])
        grouped_products.setdefault(p_key, []).append(r)

    product_items = list(grouped_products.items())
    if max_products > 0:
        product_items = product_items[:max_products]

    print(f"📋 Total Products in queue: {len(product_items)} (Grouping variations together)\n")

    for p_idx, (p_info, photo_variants) in enumerate(product_items, 1):
        prod_index, title, price, fabric = p_info
        print(f"📦 PRODUCT [{p_idx}/{len(product_items)}]: {title} ({price}) — {len(photo_variants)} Variations")

        rendered_paths = []
        lead_res = None

        for v_idx, variant in enumerate(photo_variants, 1):
            global_idx = (prod_index - 1) * 10 + v_idx
            res = download_and_polish_single(global_idx, variant)

            if res["status"] == "SUCCESS":
                p_path = Path(res["rendered_pin_path"])
                if is_photo_locked(p_path, registry):
                    print(f"    ⏩ [SKIPPED - LOCKED] Variation {v_idx} already delivered previously.")
                    continue
                rendered_paths.append(p_path)
                if not lead_res:
                    lead_res = res
            else:
                print(f"    ⚠️ Variation {v_idx} error: {res.get('error')}")

        if not rendered_paths:
            print("  ℹ️ All variations of this product are already delivered / locked. Skipping.")
            continue

        if dispatch_telegram and lead_res:
            print(f"  🚀 Dispatching {len(rendered_paths)} variations TOGETHER to Telegram...")
            ok = send_media_group_to_telegram(
                rendered_paths,
                lead_res["title"],
                lead_res["price"],
                lead_res["category"],
                lead_res["mood"],
                lead_res["prompt"]
            )
            if ok:
                register_sent_photos(rendered_paths, registry)

        time.sleep(2)

    print("\n" + "=" * 75)
    print("🎉 ALL GROUPED PHOTOSHOOTS DELIVERED (ZERO DUPLICATES)!")
    print(f"🖼️ Output Directory: {RENDERED_DIR}")
    print("=" * 75)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Grouped Cloud Photoshoot Post Runner")
    parser.add_argument("--csv", type=str, default=str(CSV_FILE), help="CSV path")
    parser.add_argument("--max", type=int, default=5, help="Max products to process (0 = all)")
    parser.add_argument("--telegram", action="store_true", default=True, help="Dispatch to Telegram")
    args = parser.parse_args()

    run_cloud_photoshoot_pipeline(Path(args.csv), max_products=args.max, dispatch_telegram=args.telegram)
