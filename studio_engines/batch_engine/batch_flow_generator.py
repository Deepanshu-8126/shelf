"""
==============================================================================
🚀 DEDICATED BATCH VEO GENERATOR ENGINE (Google Flow / Veo 2 / Omni 1.1)
==============================================================================
Designed for bulk generation (50 - 100+ videos per batch):
1. Reads CSV / Link list of Meesho products.
2. Dual-Conditioning: Consistent 21yo Indian Model Character Sheet + Scraped Product Reference Image.
3. Zero-Old-Video Reuse: Strictly verifies sent_videos_registry.json.
4. Clean 8K Master Output: Gemini watermark Delogo + Veo Native Audio + Luxury Popup Card.
5. Auto Telegram Delivery (6486771356) + Batch Resume Progress Tracking.
==============================================================================
"""

import os
import sys
import csv
import json
import time
import argparse
from pathlib import Path
from typing import List, Dict, Any

# Adjust path to import core affiliate modules
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Import core pipeline functions from global_v2 and generate_master_affiliate_video
from global_v2 import process_single_item, process_single_product, CHAR_SHEET_FILENAME
from generate_master_affiliate_video import (
    compose_master_10s_video,
    send_to_telegram,
    is_video_locked,
    register_sent_video,
    REGISTRY_FILE
)

PROGRESS_FILE = CURRENT_DIR / "batch_progress.json"


def load_progress() -> Dict[str, Any]:
    if PROGRESS_FILE.exists():
        try:
            with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"completed_urls": [], "failed_urls": [], "history": []}


def save_progress(progress: Dict[str, Any]):
    try:
        with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
            json.dump(progress, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"⚠️ Progress save notice: {e}")


def parse_csv_urls(csv_path: Path) -> List[str]:
    """Extracts product URLs from various CSV formats (with or without headers)."""
    urls = []
    if not csv_path.exists():
        print(f"❌ Error: CSV file not found at {csv_path}")
        return urls

    with open(csv_path, "r", encoding="utf-8", errors="ignore") as f:
        reader = csv.reader(f)
        for row in reader:
            if not row:
                continue
            for cell in row:
                cell_clean = cell.strip()
                if cell_clean.startswith("http://") or cell_clean.startswith("https://"):
                    if "meesho.com" in cell_clean or "ekaro.in" in cell_clean:
                        urls.append(cell_clean)
                        break

    # Deduplicate while preserving order
    seen = set()
    unique_urls = []
    for u in urls:
        if u not in seen:
            seen.add(u)
            unique_urls.append(u)

    return unique_urls


def run_batch_generation(csv_path: Path, delay_seconds: int = 10, max_items: int = 0):
    """Executes the batch pipeline for all URLs in the CSV."""
    print("=" * 70)
    print("🚀 STARTING BULK VEO GENERATION BATCH ENGINE")
    print(f"📁 CSV Target: {csv_path}")
    print("=" * 70)

    urls = parse_csv_urls(csv_path)
    if not urls:
        print("⚠️ No valid product URLs found in CSV. Please add Meesho links.")
        return

    if max_items > 0:
        urls = urls[:max_items]

    total = len(urls)
    print(f"📋 Total products queued in batch: {total}")

    progress = load_progress()
    completed_set = set(progress.get("completed_urls", []))

    success_count = 0
    skipped_count = 0
    failed_count = 0

    for idx, url in enumerate(urls, 1):
        print("\n" + "#" * 70)
        print(f"📦 BATCH ITEM [{idx}/{total}]: {url}")
        print("#" * 70)

        if url in completed_set:
            print("⏩ [SKIPPED] Product URL already completed in previous batch run.")
            skipped_count += 1
            continue

        try:
            # Process single product: Scrape + Dual Condition + Veo Flow Generation + Telegram
            result = process_single_item(product_url=url, generate_video=True)

            if result.get("generation_status") == "SUCCESS":
                video_path = result.get("video_path")
                print(f"✅ [SUCCESS] Batch item {idx} generated & dispatched: {video_path}")
                progress["completed_urls"].append(url)
                progress["history"].append({
                    "url": url,
                    "title": result.get("title"),
                    "price": result.get("price"),
                    "video_path": str(video_path),
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "status": "SUCCESS"
                })
                save_progress(progress)
                completed_set.add(url)
                success_count += 1
            else:
                print(f"⚠️ [NOTICE] Generation did not finish successfully for item {idx}")
                progress["failed_urls"].append(url)
                save_progress(progress)
                failed_count += 1

        except Exception as e:
            print(f"❌ Error processing batch item {idx}: {e}")
            progress["failed_urls"].append(url)
            save_progress(progress)
            failed_count += 1

        # Pause between generations to respect token & flow generation queue
        if idx < total:
            print(f"\n⏳ Waiting {delay_seconds}s before queueing next batch item...")
            time.sleep(delay_seconds)

    print("\n" + "=" * 70)
    print("🎉 BATCH ENGINE RUN COMPLETED!")
    print(f"   • Total Processed : {total}")
    print(f"   • Successfully Sent: {success_count}")
    print(f"   • Skipped (Already Done): {skipped_count}")
    print(f"   • Failed / Review  : {failed_count}")
    print("=" * 70)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Bulk Veo Affiliate Video Batch Generator")
    parser.add_argument("--csv", type=str, default=str(CURRENT_DIR / "sample_products.csv"), help="Path to products CSV")
    parser.add_argument("--delay", type=int, default=10, help="Delay in seconds between items")
    parser.add_argument("--max", type=int, default=0, help="Max items to process (0 = all)")
    args = parser.parse_args()

    target_csv = Path(args.csv)
    run_batch_generation(target_csv, delay_seconds=args.delay, max_items=args.max)
