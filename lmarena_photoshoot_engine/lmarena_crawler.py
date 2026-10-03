"""
==============================================================================
⚡ ULTRA-FAST LM ARENA (LMSYS / ARENA.AI) AI PHOTOSHOOT ENGINE
==============================================================================
Features:
1. 🔐 Interactive One-Time Login Mode (--login):
   - Opens visible Brave browser for user to authenticate & solve Cloudflare once.
   - Automatically saves all session cookies to permanent profile:
     data/browser_sessions/lmarena_fast_profile (Zero re-login required).
2. 🚀 Multi-Model Direct Image Arena:
   - Supports FLUX.1, Grok Imagine, Stable Diffusion 3.5, and Ideogram.
   - Automatically clears vote gates and handles image generation prompts.
3. 🧠 LLM Vision Director Integration:
   - Powered by UniversalLLMVisualTrainer for 100% authentic character identity,
     category detection, non-repeating dynamic expressions, and soft-skin preservation.
4. 📤 Telegram 4K Photoshoot Dispatch (6486771356).
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
from PIL import Image, ImageEnhance, ImageFilter

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

# Universal LLM Vision Director & Aesthetic Library
from connectors.universal_llm_visual_trainer import UniversalLLMVisualTrainer
from photoshoot_pinterest_engine.cloud_photoshoot_runner import send_single_photo_to_telegram

OUTPUT_DIR = CURRENT_DIR / "rendered_arena_photos"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

USER_DATA_DIR = str(PROJECT_ROOT / "data" / "browser_sessions" / "lmarena_fast_profile")
BRAVE_EXE = r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"


async def launch_interactive_arena_login():
    """
    Launches a visible, headful Brave browser on arena.ai/image.
    Allows user to log in or solve Cloudflare verification once.
    All session state & cookies are permanently saved to USER_DATA_DIR.
    """
    print("=" * 80)
    print("🔐 [LM ARENA / ARENA.AI ONE-TIME LOGIN SETUP]")
    print(f"📁 Session Storage: {USER_DATA_DIR}")
    print("=" * 80)

    launch_args = {
        "user_data_dir": USER_DATA_DIR,
        "headless": False,
        "args": [
            "--no-sandbox",
            "--disable-blink-features=AutomationControlled",
            "--start-maximized"
        ]
    }
    if Path(BRAVE_EXE).exists():
        launch_args["executable_path"] = BRAVE_EXE

    async with async_playwright() as p:
        print("  🌐 Launching visible Brave browser window...")
        browser = await p.chromium.launch_persistent_context(**launch_args)
        page = await browser.new_page()

        print("  🔗 Opening LM Arena Image Generation (https://arena.ai/image)...")
        try:
            await page.goto("https://arena.ai/image", timeout=45000, wait_until="domcontentloaded")
            await asyncio.sleep(2)
            # Auto-click terms Agree if present
            agree_btn = page.locator('button:has-text("Agree")').first
            if await agree_btn.count() > 0 and await agree_btn.is_visible():
                await agree_btn.click()
        except Exception as e:
            print(f"  Notice during initial navigation: {e}")

        print("\n" + "=" * 80)
        print("👉 BROWSER WINDOW IS NOW OPEN ON YOUR SCREEN!")
        print("👉 Please click 'Log In' / 'Continue with Google' and complete your authentication.")
        print("👉 Once you are logged in on arena.ai, press ENTER in this terminal to save and exit.")
        print("=" * 80 + "\n")

        # Wait for user confirmation in terminal
        await asyncio.to_thread(input, "Press [ENTER] when you have logged in to save session: ")

        print("  💾 Saving session cookies & closing browser...")
        await browser.close()
        print("  ✅ Session saved permanently! Subsequent photoshoot runs will use this profile without errors.\n")


async def crawl_and_generate_arena_photo(
    product_title: str = "Burgundy Lace Bodycon Maxi Evening Dress",
    price: str = "₹599",
    fabric: str = "Lace & Stretch Lycra",
    pose_key: str | None = None,
    headless: bool = True
) -> Path | None:
    """
    Connects to LM Arena Image Playground, submits trained prompt, captures rendered photo,
    and applies soft-skin optical profile.
    """
    directive = UniversalLLMVisualTrainer.auto_direct_outfit(
        product_title,
        fabric=fabric,
        price=price,
        preferred_preset=pose_key
    )
    category_name = directive["category_name"]
    prompt = directive["master_photo_prompt"]
    optical_recipe = directive["optical_recipe"]

    print("=" * 80)
    print("⚡ [LM ARENA DIRECT NEURAL PHOTOSHOOT]")
    print(f"👗 Outfit   : {product_title} ({price})")
    print(f"🏷️ Category : {category_name} [{directive['preset_key']}]")
    print(f"🎭 Express. : {directive['expression']}")
    print(f"🔬 Optical  : {optical_recipe['skin_profile']}")
    print("=" * 80)

    slug = "".join(c if c.isalnum() else "_" for c in product_title)[:16].lower()
    out_photo = OUTPUT_DIR / f"ARENA_FAST_{int(time.time())}_{slug}.jpg"

    async with async_playwright() as p:
        launch_args = {
            "user_data_dir": USER_DATA_DIR,
            "headless": headless,
            "args": [
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled",
                "--disable-web-security"
            ]
        }
        if Path(BRAVE_EXE).exists():
            launch_args["executable_path"] = BRAVE_EXE

        browser = await p.chromium.launch_persistent_context(**launch_args)
        page = await browser.new_page()

        print("  [1/4] Connecting to LMSYS / Arena.ai Image Playground (https://arena.ai/image)...")
        try:
            await page.goto("https://arena.ai/image", timeout=35000, wait_until="domcontentloaded")
            await asyncio.sleep(2)
        except Exception as e:
            print(f"  Navigation warning: {e}")

        # Check for Initial Terms Modal
        try:
            agree_btn = page.locator('button:has-text("Agree")').first
            if await agree_btn.count() > 0 and await agree_btn.is_visible():
                print("  📋 Accepting Terms of Use...")
                await agree_btn.click()
                await asyncio.sleep(1.0)
        except Exception:
            pass

        # 2. Check and bypass any existing Vote Lock
        try:
            vote_btns = page.locator('button:has-text("Tie"), button:has-text("Model A is better"), button:has-text("Model B is better"), button:has-text("Both are bad"), button:has-text("Clear")')
            if await vote_btns.count() > 0:
                first_vote = vote_btns.first
                if await first_vote.is_visible():
                    print("  🔓 Auto-clearing previous comparison vote gate...")
                    await first_vote.click(timeout=2000, force=True)
                    await asyncio.sleep(1.0)
        except Exception:
            pass

        # 3. Enter Master Pinterest Prompt from LLM Director
        print("  [2/4] Injecting Master LLM Editorial Prompt...")
        prompt_box = page.locator('textarea[placeholder*="Describe the image" i], textarea, div.ProseMirror, [contenteditable="true"]').first

        if await prompt_box.count() > 0:
            await prompt_box.click(timeout=3000)
            await prompt_box.fill(prompt)
            await asyncio.sleep(0.5)

            # Submit prompt
            send_btn = page.locator('button:has(svg), button:has-text("Generate"), button:has-text("Send"), button[type="submit"]').last
            if await send_btn.count() > 0 and await send_btn.is_visible():
                await send_btn.click(timeout=3000, force=True)
                print("  🚀 Sent prompt via Submit button!")
            else:
                await page.keyboard.press("Enter")
                print("  🚀 Sent prompt via Enter key!")
            await asyncio.sleep(2.0)

            # Check if Terms appeared post-submit
            agree_btn = page.locator('button:has-text("Agree")').first
            if await agree_btn.count() > 0 and await agree_btn.is_visible():
                print("  📋 Accepting Terms of Use post-submit...")
                await agree_btn.click()
                await asyncio.sleep(1.5)

            # Check if Login Modal appeared
            login_modal = page.locator('div:has-text("Log In or Create Account")').first
            if await login_modal.count() > 0 and await login_modal.is_visible():
                print("\n" + "!" * 80)
                print("⚠️ [ARENA AUTHENTICATION REQUIRED]")
                print("Arena.ai requires a one-time login to render images without restriction.")
                print("To log in visibly, run: python lmarena_photoshoot_engine/lmarena_crawler.py --login")
                print("!" * 80 + "\n")
        else:
            print("  ⚠️ Prompt box selector not found on arena.ai/image.")

        # 4. Stream Capture
        print("  [3/4] Monitoring Output Image Stream...")
        elapsed = 0
        max_wait = 35
        found_image = False

        while elapsed < max_wait:
            await asyncio.sleep(2.5)
            elapsed += 2.5

            try:
                vote_popup = page.locator('button:has-text("Tie"), button:has-text("Model A is better"), button:has-text("Model B is better")').first
                if await vote_popup.count() > 0 and await vote_popup.is_visible():
                    await vote_popup.click(timeout=1000, force=True)
            except Exception:
                pass

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

    # Fallback to Google Flow if needed
    if not out_photo.exists() or out_photo.stat().st_size < 5000:
        print("\n  ⚡ LM Arena unauthenticated/queuing, instantly executing Google Flow Engine...")
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
        print(f"\n✨ [LM Arena Shoot Ready]: {out_photo.name} ({out_photo.stat().st_size} bytes)")
        
        # Apply Optical Recipe from LLM Director (Soft skin preserved, zero crunch)
        img = Image.open(out_photo).convert("RGB")
        col_enh = ImageEnhance.Color(img).enhance(optical_recipe.get("color_factor", 1.02))
        cont_enh = ImageEnhance.Contrast(col_enh).enhance(optical_recipe.get("contrast_factor", 1.02))
        sharp_enh = ImageEnhance.Sharpness(cont_enh).enhance(optical_recipe.get("sharpness_factor", 1.01))
        
        if optical_recipe.get("unsharp_mask", {}).get("enabled", False):
            um = optical_recipe["unsharp_mask"]
            sharp_enh = sharp_enh.filter(ImageFilter.UnsharpMask(radius=um.get("radius", 1), percent=um.get("percent", 15), threshold=um.get("threshold", 6)))
            
        sharp_enh.save(out_photo, "JPEG", quality=98)

        # Dispatch to Telegram
        caption = (
            f"📸 *LM ARENA PHOTOSHOOT: {product_title.upper()}* ✨\n\n"
            f"🥻 *Model:* 21yo Indian Creator (Signature Bindi & Jhumkas)\n"
            f"🎭 *Category & Pose:* {category_name}\n"
            f"💰 *Deal Price:* `{price}`\n"
            f"🔬 *Optical:* {optical_recipe.get('skin_profile', 'Natural soft skin')}\n"
            f"⚡ *Engine:* LMSYS Arena / FLUX-Grok Tier • Zero Digital Crunch\n\n"
            f"🛍️ *Product:* {product_title}\n"
            f"🏷️ #LMArena #PinterestFashion #OOTD #SareeLookbook"
        )
        send_single_photo_to_telegram(out_photo, caption)
        return out_photo

    return None


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="LM Arena Fast Photoshoot Engine")
    parser.add_argument("--login", action="store_true", help="Launch visible browser to log in and save session")
    parser.add_argument("--headful", action="store_true", help="Run photoshoot in visible browser window")
    parser.add_argument("--title", type=str, default="Burgundy Lace Bodycon Maxi Evening Dress", help="Title")
    parser.add_argument("--price", type=str, default="₹599", help="Price")
    parser.add_argument("--fabric", type=str, default="Lace & Stretch Lycra", help="Fabric")
    parser.add_argument("--pose", type=str, default=None, help="Pose Key")
    args = parser.parse_args()

    if args.login:
        asyncio.run(launch_interactive_arena_login())
    else:
        asyncio.run(crawl_and_generate_arena_photo(
            product_title=args.title,
            price=args.price,
            fabric=args.fabric,
            pose_key=args.pose,
            headless=not args.headful
        ))
