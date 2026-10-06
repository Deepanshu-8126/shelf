"""
==============================================================================
🏛️ LM ARENA BATCH PHOTOSHOOT & TELEGRAM DISPATCHER
==============================================================================
Runs curated Pinterest high-fashion poses through LM Arena / Top-Tier AI Engine,
applies Kodak Portra 400 film calibration, groups variations into single Telegram 
albums, and registers hashes to avoid duplicates.
==============================================================================
"""

import os
import sys
import json
import time
import asyncio
from pathlib import Path
from PIL import Image, ImageEnhance

if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            getattr(sys.stdout, "reconfigure")(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            getattr(sys.stderr, "reconfigure")(encoding="utf-8", errors="replace")
    except Exception:
        pass

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from lmarena_photoshoot_engine.lmarena_crawler import crawl_and_generate_arena_photo
from photoshoot_pinterest_engine.cloud_photoshoot_runner import (
    send_telegram_photo_album,
    send_single_photo_to_telegram,
    load_photo_registry,
    register_sent_photos,
    is_photo_locked
)

CATALOG_PATH = PROJECT_ROOT / "photoshoot_pinterest_engine" / "curated_pinterest_poses_catalog.json"
OUTPUT_DIR = CURRENT_DIR / "rendered_arena_photos"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


async def run_lmarena_batch(max_items: int = 5):
    if not CATALOG_PATH.exists():
        print(f"❌ Catalog file not found: {CATALOG_PATH}")
        return

    with open(CATALOG_PATH, "r", encoding="utf-8") as f:
        catalog = json.load(f)

    print("=" * 80)
    print("🏛️ [LM ARENA BATCH RUNNER] Starting High-End Editorial AI Photoshoot Pipeline")
    print(f"📋 Total Curated Poses: {len(catalog)} | Target Count: {max_items}")
    print("=" * 80)

    generated_photos = []
    generated_details = []

    count = 0
    for item in catalog:
        if count >= max_items:
            break

        product_title = item.get("product_title", "Women Designer Dress")
        price = item.get("price", "₹499")
        fabric = item.get("fabric", "Lycra & Silk Blend")
        style_id = item.get("style_id", "GRAND_STAIRCASE_ELEGANCE")
        style_title = item.get("style_title", "Pinterest Editorial")

        # Check if already generated/locked
        lock_name = f"{product_title}_{style_id}"
        if is_photo_locked(lock_name):
            print(f"  ⏭️ Skipping already generated photoshoot: {lock_name}")
            continue

        print(f"\n[{count + 1}/{max_items}] 👗 Generating: {product_title} | Pose: {style_title}")

        photo_path = await crawl_and_generate_arena_photo(
            product_title=product_title,
            price=price,
            fabric=fabric,
            pose_key=style_id
        )

        if photo_path and photo_path.exists():
            generated_photos.append(photo_path)
            generated_details.append({
                "title": product_title,
                "price": price,
                "pose": style_title,
                "path": str(photo_path)
            })
            count += 1
            print(f"  ✅ Finished shoot {count}/{max_items}: {photo_path.name}")
        else:
            print(f"  ⚠️ Shoot failed or skipped for: {product_title}")

    # If multiple photos generated, group them into a single swipeable Telegram Album
    if len(generated_photos) > 1:
        print("\n" + "=" * 80)
        print(f"📦 Grouping {len(generated_photos)} Photos into Telegram Swipeable Album...")
        print("=" * 80)

        main_item = generated_details[0]
        album_caption = (
            f"📸 *PINTEREST HIGH-FASHION EDITORIAL COLLECTION* ✨\n\n"
            f"🥻 *Model:* 21yo Indian Creator (Authentic Portra 400 Film Tones)\n"
            f"💰 *Starting from:* `{main_item['price']}`\n"
            f"⭐ *AI Engine:* LMSYS LM Arena • FLUX/Midjourney Tier • Zero CGI/Plastic\n\n"
            f"🔥 *Featured Outfits:*\n"
        )
        for i, det in enumerate(generated_details, 1):
            album_caption += f"{i}. {det['title']} — _{det['pose']}_\n"

        album_caption += f"\n🏷️ #LMArena #EditorialShoot #IndianFashion #PinterestLookbook #OOTD"

        send_telegram_photo_album(generated_photos, album_caption)
        register_sent_photos(generated_photos)
    elif len(generated_photos) == 1:
        register_sent_photos(generated_photos)

    print("\n🎉 [LM ARENA BATCH COMPLETE] All requested high-fashion photos processed.")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="LM Arena Batch Photoshoot Runner")
    parser.add_argument("--max", type=int, default=3, help="Max items to process")
    args = parser.parse_args()

    asyncio.run(run_lmarena_batch(max_items=args.max))
