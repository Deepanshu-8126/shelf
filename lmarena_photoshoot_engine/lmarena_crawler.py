"""
==============================================================================
⚡ ULTRA-FAST LM ARENA (LMSYS) AI PHOTOSHOOT ENGINE
==============================================================================
Features:
1. 🚀 Direct Fast Mode: Targets FLUX.1 Schnell / Grok Imagine / SD3.5 / Ideogram.
2. 🔓 Auto-Vote Bypass: Automatically clears Model A vs Model B voting locks.
3. ⏱️ 5-15s Super-Fast Image Stream Capture.
4. 🎞️ Soft Kodak Portra 400 Film Calibration.
5. 📤 Telegram 4K Photoshoot Dispatch (6486771356).
==============================================================================
"""

import os
import sys
import time
import json
import asyncio
import urllib.request
from pathlib import Path
from playwright.async_api import async_playwright
from PIL import Image, ImageEnhance

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from photoshoot_pinterest_engine.pinterest_editorial_aesthetic_library import get_pinterest_brand_prompt
from photoshoot_pinterest_engine.cloud_photoshoot_runner import (
    send_single_photo_to_telegram,
    load_photo_registry,
    register_sent_photos,
    is_photo_locked
)

OUTPUT_DIR = CURRENT_DIR / "rendered_arena_photos"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

USER_DATA_DIR = str(PROJECT_ROOT / "data" / "browser_sessions" / "lmarena_fast_profile")
BRAVE_EXE = r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"


async def crawl_and_generate_arena_photo(
    product_title: str = "Burgundy Lace Bodycon Maxi Evening Dress",
    price: str = "₹599",
    fabric: str = "Lace & Stretch Lycra",
    pose_key: str = "GRAND_STAIRCASE_ELEGANCE"
) -> Path | None:
    pose_name, prompt = get_pinterest_brand_prompt(product_title, fabric=fabric, pose_key=pose_key)

    print("=" * 80)
    print("⚡ [LM ARENA ULTRA-FAST ENGINE] Direct Neural Image Photoshoot")
    print(f"👗 Outfit: {product_title} ({price}) | Pose: {pose_name}")
    print("=" * 80)

    slug = "".join(c if c.isalnum() else "_" for c in product_title)[:16].lower()
    out_photo = OUTPUT_DIR / f"ARENA_FAST_{int(time.time())}_{slug}.jpg"

    async with async_playwright() as p:
        launch_args = {
            "user_data_dir": USER_DATA_DIR,
            "headless": True,
            "args": [
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled",
                "--disable-web-security",
                "--disable-features=IsolateOrigins,site-per-process"
            ]
        }
        if Path(BRAVE_EXE).exists():
            launch_args["executable_path"] = BRAVE_EXE

        browser = await p.chromium.launch_persistent_context(**launch_args)
        page = await browser.new_page()

        print("  [1/4] Connecting to LMSYS Playground...")
        target_urls = [
            "https://lmarena.ai/?leaderboard=image",
            "https://lmarena.ai/?arena=direct",
            "https://lmarena.ai/?arena=image",
            "https://lmarena.ai"
        ]
        
        for url in target_urls:
            try:
                await page.goto(url, timeout=20000, wait_until="domcontentloaded")
                await asyncio.sleep(2)
                break
            except Exception:
                continue

        # 1. Switch to Direct / Image Mode
        print("  [2/4] Optimizing Fast Model mode (Direct / Image tab)...")
        try:
            # Check for Direct Chat tab or Image tab
            fast_tabs = [
                'button:has-text("Direct")',
                'a:has-text("Direct")',
                'button:has-text("Image")',
                'button:has-text("Text-to-Image")',
                '[role="tab"]:has-text("Image")'
            ]
            for sel in fast_tabs:
                tab = page.locator(sel).first
                if await tab.count() > 0 and await tab.is_visible():
                    await tab.click(timeout=2000, force=True)
                    await asyncio.sleep(1.0)
                    print(f"  ⚡ Fast tab active: {sel}")
                    break
        except Exception:
            pass

        # 2. Check and bypass any existing Vote Lock
        try:
            vote_btns = page.locator('button:has-text("Tie"), button:has-text("Model A is better"), button:has-text("Both are bad"), button:has-text("Clear")')
            if await vote_btns.count() > 0:
                first_vote = vote_btns.first
                if await first_vote.is_visible():
                    print("  🔓 Auto-clearing previous comparison vote gate...")
                    await first_vote.click(timeout=2000, force=True)
                    await asyncio.sleep(1.0)
        except Exception:
            pass

        # 3. Enter Master Pinterest Prompt
        print("  [3/4] Injecting Master Pinterest Editorial Prompt...")
        prompt_box = page.locator('textarea, input[placeholder*="prompt" i], input[placeholder*="message" i], div.ProseMirror, [contenteditable="true"]').first
        submitted = False

        if await prompt_box.count() > 0:
            await prompt_box.click(timeout=3000)
            await prompt_box.fill(prompt)
            await asyncio.sleep(0.5)

            # Submit
            send_btn = page.locator('button:has-text("Generate"), button:has-text("Send"), button:has-text("Submit"), button[aria-label*="send" i], button.submit-btn').first
            if await send_btn.count() > 0 and await send_btn.is_visible():
                await send_btn.click(timeout=3000, force=True)
                print("  🚀 Sent prompt via Fast Submit button!")
                submitted = True
            else:
                await page.keyboard.press("Enter")
                print("  🚀 Sent prompt via Enter key!")
                submitted = True

        # 4. Super-Fast Stream Capture (Poll every 2 seconds)
        print("  [4/4] Monitoring Ultra-Fast Output Image Stream...")
        elapsed = 0
        max_wait = 45
        found_image = False

        while elapsed < max_wait:
            await asyncio.sleep(2.5)
            elapsed += 2.5

            # Auto-clear voting popups if they appear during generation
            try:
                vote_popup = page.locator('button:has-text("Tie"), button:has-text("Model A is better")').first
                if await vote_popup.count() > 0 and await vote_popup.is_visible():
                    await vote_popup.click(timeout=1000, force=True)
            except Exception:
                pass

            # Check rendered image elements
            all_imgs = await page.locator('img').all()
            for img_el in all_imgs:
                try:
                    src = await img_el.get_attribute("src") or ""
                    if not src:
                        continue

                    src_lower = src.lower()
                    if any(x in src_lower for x in ["avatar", "icon", "logo", "badge", "favicon", "google", "lmsys", "static"]):
                        continue

                    box = await img_el.bounding_box()
                    if box and box["width"] >= 200 and box["height"] >= 200:
                        print(f"  🎉 CAPTURED RENDERED AI IMAGE at {elapsed}s! Size: {int(box['width'])}x{int(box['height'])}")
                        await img_el.screenshot(path=str(out_photo))
                        found_image = True
                        break
                except Exception:
                    continue

            if found_image:
                break

        await browser.close()

    # Fallback directly to Google Flow if needed
    if not out_photo.exists() or out_photo.stat().st_size < 5000:
        print("  ⚡ LM Arena queue busy, syncing with Top-Tier Neural Engine...")
        from photoshoot_pinterest_engine.generate_google_flow_photo import generate_single_flow_photo
        flow_res = await generate_single_flow_photo(
            product_title=product_title,
            price=price,
            fabric=fabric,
            pose_key=pose_key
        )
        if flow_res and flow_res.exists():
            return flow_res

    if out_photo.exists():
        print(f"✨ [LM Arena Fast Shoot Ready]: {out_photo.name} ({out_photo.stat().st_size} bytes)")
        
        # Soft Kodak Portra 400 Film Calibration
        img = Image.open(out_photo).convert("RGB")
        img_color = ImageEnhance.Color(img).enhance(1.03)
        img_color.save(out_photo, "JPEG", quality=98)

        caption = (
            f"📸 *LM ARENA FAST PHOTOSHOOT: {product_title.upper()}* ✨\n\n"
            f"🥻 *Model:* 21yo Indian Creator (Authentic Portra 400)\n"
            f"🎭 *Editorial Pose:* {pose_name}\n"
            f"💰 *Deal Price:* `{price}`\n"
            f"⚡ *Engine:* LMSYS Direct Fast / FLUX-Grok Tier • Zero Plastic\n\n"
            f"🛍️ *Product:* {product_title}\n"
            f"🏷️ #LMArena #PinterestFashion #OOTD #SareeLookbook"
        )
        send_single_photo_to_telegram(out_photo, caption)
        return out_photo

    return None


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="LM Arena Fast Photoshoot")
    parser.add_argument("--title", type=str, default="Burgundy Lace Bodycon Maxi Evening Dress", help="Title")
    parser.add_argument("--price", type=str, default="₹599", help="Price")
    parser.add_argument("--fabric", type=str, default="Lace & Stretch Lycra", help="Fabric")
    parser.add_argument("--pose", type=str, default="GRAND_STAIRCASE_ELEGANCE", help="Pose")
    args = parser.parse_args()

    asyncio.run(crawl_and_generate_arena_photo(
        product_title=args.title,
        price=args.price,
        fabric=args.fabric,
        pose_key=args.pose
    ))
