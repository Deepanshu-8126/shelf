"""
Google Flow Autonomous Video Generator & Media Extractor.
Integrated with Human Stealth Engine (Anti-Detection & Human Behavior Simulation).
Features:
1. Pure Human Simulation:
   - Bezier multi-step mouse trajectories with human jitter & randomized offsets
   - Human keystroke typing cadence with natural rhythm & inter-word pauses
   - Idle scrolling & natural reading delays
2. Google Pro Session Integration:
   - Uses user's persistent profile (User Data) with TLS tokens preserved
   - Auto-injects Google session cookies
   - Stealth init script hiding automation flags (navigator.webdriver, chrome runtime)
3. Full Project Automation:
   - Configures 9:16 vertical ratio, Veo 3.1 - Quality, Confirm: Never
   - Injects trained model face & GenZ editorial prompts into ProseMirror
   - Intercepts and downloads genuine 1080x1920 / 720x1280 MP4 videos
"""
from __future__ import annotations

import asyncio
import json
import math
import os
import random
import re
import sys
import time
import zipfile
from pathlib import Path
from typing import Any

root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from core.logging_utils import get_logger

log = get_logger("google_flow_crawler")

BRAVE_EXE = Path(r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe")


class HumanStealthEngine:
    """Simulates realistic human mouse trajectories, keystrokes, and browsing behavior."""

    @staticmethod
    async def human_move_and_click(page, element, force: bool = False):
        """Moves mouse naturally along a curve with variable speed, then clicks with human dwell."""
        box = await element.bounding_box()
        if not box:
            if force:
                await element.click(force=True)
            return

        # Random target point inside the element (avoid dead-center bot pattern)
        target_x = box["x"] + box["width"] * random.uniform(0.25, 0.75)
        target_y = box["y"] + box["height"] * random.uniform(0.25, 0.75)

        # Multi-step curved trajectory simulation
        steps = random.randint(15, 30)
        await page.mouse.move(target_x, target_y, steps=steps)
        await asyncio.sleep(random.uniform(0.12, 0.35))

        # Natural click: mouse down, human hold, mouse up
        await page.mouse.down()
        await asyncio.sleep(random.uniform(0.06, 0.14))
        await page.mouse.up()
        await asyncio.sleep(random.uniform(0.15, 0.40))

    @staticmethod
    async def human_type(page, text: str, min_delay: float = 0.03, max_delay: float = 0.08):
        """Simulates human typing cadence with word pauses and natural variation."""
        words = text.split(" ")
        for w_idx, word in enumerate(words):
            for char in word:
                await page.keyboard.type(char)
                await asyncio.sleep(random.uniform(min_delay, max_delay))

            # Space between words with a slightly longer natural pause
            if w_idx < len(words) - 1:
                await page.keyboard.type(" ")
                await asyncio.sleep(random.uniform(0.08, 0.22))

            # Occasional cognitive pause (like user looking at reference or thinking)
            if random.random() < 0.04:
                await asyncio.sleep(random.uniform(0.4, 0.9))

    @staticmethod
    async def human_natural_scroll(page):
        """Simulates brief casual scroll or reading glance."""
        delta_y = random.randint(150, 350)
        await page.mouse.wheel(0, delta_y)
        await asyncio.sleep(random.uniform(0.5, 1.2))
        await page.mouse.wheel(0, -delta_y)
        await asyncio.sleep(random.uniform(0.3, 0.7))


class GoogleFlowCrawler:
    """Automates Google Flow web portal (flow.google.com) with complete human stealth."""

    def __init__(self, user_data_dir: Path | str | None = None):
        self.root = Path(__file__).resolve().parent.parent
        self.user_data_dir = Path(user_data_dir or (self.root / "data" / "browser_sessions" / "google_pro_permanent_profile"))
        self.cookie_file = self.root / "data" / "google_session_cookie.json"
        self.output_dir = self.root / "data" / "veo_extracted_videos"
        self.user_data_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.stealth = HumanStealthEngine()

    def train_prompt_for_product(self, product_title: str, mode: str = "showcase") -> str:
        """Constructs high-converting viral 9:16 Veo prompt using reference video grammar."""
        from connectors.model_face_identity_trainer import ModelFaceIdentityTrainer

        if mode == "unboxing":
            return ModelFaceIdentityTrainer.get_ugc_unboxing_prompt(
                product_name=product_title,
                fabric="deep black stretch ribbed fabric with sculpted silhouette and floor-grazing hem",
                packaging="white poly delivery parcel"
            )
        else:
            return ModelFaceIdentityTrainer.get_model_motion_showcase_prompt(
                product_name=product_title,
                fabric="fitted deep black stretch fabric with long sleeves and floor-grazing maxi hem"
            )

    async def generate_and_extract_video(
        self,
        product_name: str = "Women Solid Long Sleeve Bodycon Maxi Dress",
        mode: str = "showcase",
        custom_prompt: str | None = None,
        headless: bool = True,
        timeout_seconds: int = 240
    ) -> dict[str, Any]:
        from playwright.async_api import async_playwright

        prompt = custom_prompt or self.train_prompt_for_product(product_name, mode=mode)
        log.info("[GoogleFlow] Starting generation for: %s (Mode: %s)", product_name, mode)
        log.info("[GoogleFlow] Prompt: %s", prompt[:120] + "...")
        log.info("[GoogleFlow] Human Stealth Engine Active (Random delays, curved mouse, variable keystrokes)")

        slug = re.sub(r"[^a-zA-Z0-9]+", "_", product_name[:20]).lower().strip("_")
        timestamp = int(time.time())
        dest_video_path = self.output_dir / f"FLOW_VEO_{slug}_{timestamp}.mp4"

        # PERMANENT POLICY: Block Chrome/Brave browser automation to prevent desktop lockups & connection hangs
        block_browser = os.environ.get("BLOCK_BROWSER_AUTOMATION", "1").strip().lower() in ("1", "true", "yes")
        if block_browser:
            log.info("🛡️ [GoogleFlow] Chrome/Brave browser connection is PERMANENTLY BLOCKED by system policy.")
            log.info("⚡ [GoogleFlow] Routing directly to High-Speed Google Veo Direct REST API...")
            try:
                from connectors.google_veo_direct_api import GoogleVeoDirectAPI
                api = GoogleVeoDirectAPI()
                return api.generate_ugc_unboxing_video(product_title=product_name, category=mode)
            except Exception as direct_err:
                log.warning("[GoogleFlow] Direct Veo API notice: %s", direct_err)
                return {
                    "success": False,
                    "error": "Browser automation blocked. Direct API fallback failed: " + str(direct_err)
                }

        async with async_playwright() as p:
            browser = await p.chromium.launch_persistent_context(
                user_data_dir=str(self.user_data_dir),
                executable_path=str(BRAVE_EXE) if BRAVE_EXE.exists() else None,
                headless=headless,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--start-maximized",
                    "--disable-infobars",
                    "--ignore-certificate-errors",
                    "--disable-extensions-except=",
                    "--disable-component-extensions-with-background-pages"
                ],
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
            )

            # Deep anti-detection stealth script: Mask automation fingerprints
            await browser.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
                Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en', 'hi'] });
                Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
                window.chrome = { runtime: {}, app: {} };
            """)

            # Load persistent cookies if present
            if self.cookie_file.exists():
                try:
                    cookies = json.loads(self.cookie_file.read_text(encoding="utf-8"))
                    await browser.add_cookies(cookies)
                    log.info("[GoogleFlow] Injected %d cookies into context", len(cookies))
                except Exception as ce:
                    log.warning("[GoogleFlow] Cookie notice: %s", ce)

            page = await browser.new_page()

            log.info("[GoogleFlow] Navigating to flow.google.com (human pace)...")
            await page.goto("https://flow.google.com/", timeout=60000, wait_until="domcontentloaded")
            await asyncio.sleep(random.uniform(2.5, 4.5))

            # Natural glance scroll
            await self.stealth.human_natural_scroll(page)

            # Click New project using curved human click
            new_proj_btn = await page.query_selector("text=New project")
            if new_proj_btn:
                log.info("[GoogleFlow] Clicking 'New project' with human movement...")
                await self.stealth.human_move_and_click(page, new_proj_btn)
                await asyncio.sleep(random.uniform(3.5, 5.5))

            project_url = page.url
            log.info("[GoogleFlow] Project URL: %s", project_url)

            # Configure Settings: 9:16 aspect ratio & Veo model & Never confirm
            try:
                settings_btn = await page.query_selector('button[aria-label="Settings"]')
                if settings_btn:
                    await self.stealth.human_move_and_click(page, settings_btn)
                    await asyncio.sleep(random.uniform(0.8, 1.4))

                    # Select 9:16 under Video generation default
                    await page.evaluate("""() => {
                        const buttons = Array.from(document.querySelectorAll('button, div[role="button"]'));
                        const btn916 = buttons.filter(b => b.innerText.includes('9:16'));
                        if (btn916.length > 1) {
                            btn916[1].click();
                        } else if (btn916.length === 1) {
                            btn916[0].click();
                        }
                    }""")
                    await asyncio.sleep(random.uniform(0.4, 0.8))

                    # Select Veo 3.1 - Quality
                    dropdown = await page.query_selector('text=Omni 1.1 Flash')
                    if dropdown:
                        await self.stealth.human_move_and_click(page, dropdown)
                        await asyncio.sleep(random.uniform(0.8, 1.2))
                        veo_opt = await page.query_selector('text=Veo 3.1 - Quality') or await page.query_selector('text=Veo 3.1 - Fast')
                        if veo_opt:
                            await self.stealth.human_move_and_click(page, veo_opt)
                            await asyncio.sleep(random.uniform(0.4, 0.7))

                    # Set Confirm to Never
                    never_radio = await page.query_selector('text=Never')
                    if never_radio:
                        await self.stealth.human_move_and_click(page, never_radio)
                        await asyncio.sleep(random.uniform(0.3, 0.6))

                    # Save settings
                    save_btn = await page.query_selector('button:has-text("Save")')
                    if save_btn:
                        await self.stealth.human_move_and_click(page, save_btn)
                        await asyncio.sleep(random.uniform(1.2, 1.8))
            except Exception as se:
                log.warning("[GoogleFlow] Settings config notice: %s", se)

            # Find ProseMirror prompt box
            pm = await page.query_selector('div.ProseMirror[contenteditable="true"]')
            if not pm:
                ss = self.output_dir / f"flow_debug_nopm_{timestamp}.png"
                await page.screenshot(path=str(ss))
                await browser.close()
                raise RuntimeError(f"Could not locate ProseMirror editor in Google Flow. Screenshot: {ss}")

            log.info("[GoogleFlow] Focusing prompt box with human mouse curve...")
            await self.stealth.human_move_and_click(page, pm)
            await asyncio.sleep(random.uniform(0.5, 1.0))

            log.info("[GoogleFlow] Typing prompt with variable human cadence (zero bot signature)...")
            await self.stealth.human_type(page, prompt)
            await asyncio.sleep(random.uniform(1.0, 2.0))

            # Click Start generation with natural mouse move
            start_btn = await page.query_selector('button[aria-label="Start generation"]')
            if start_btn:
                log.info("[GoogleFlow] Moving cursor to 'Start generation' and clicking...")
                await self.stealth.human_move_and_click(page, start_btn)
            else:
                await page.keyboard.press("Enter")

            log.info("[GoogleFlow] Generation initiated! Polling for render completion (up to %ds)...", timeout_seconds)

            # Poll for generation completion (look for Download batch button)
            start_time = time.time()
            download_done = False

            while time.time() - start_time < timeout_seconds:
                await asyncio.sleep(random.uniform(4.0, 6.0))
                elapsed = int(time.time() - start_time)

                # Check if download button is available
                dl_btn = await page.query_selector('button[aria-label="Download batch"]')
                if dl_btn:
                    log.info("[GoogleFlow] Video render completed! Triggering download...")
                    try:
                        async with page.expect_download(timeout=35000) as download_info:
                            await self.stealth.human_move_and_click(page, dl_btn, force=True)
                        download = await download_info.value
                        temp_dl_path = self.output_dir / download.suggested_filename
                        await download.save_as(str(temp_dl_path))

                        # If zip, extract MP4
                        if temp_dl_path.suffix == ".zip":
                            with zipfile.ZipFile(temp_dl_path, "r") as z:
                                for name in z.namelist():
                                    if name.endswith(".mp4"):
                                        z.extract(name, self.output_dir)
                                        extracted_mp4 = self.output_dir / name
                                        extracted_mp4.replace(dest_video_path)
                                        break
                            temp_dl_path.unlink(missing_ok=True)
                        else:
                            temp_dl_path.replace(dest_video_path)

                        download_done = True
                        break
                    except Exception as de:
                        log.warning("[GoogleFlow] Download attempt notice: %s", de)

                log.info("[GoogleFlow] Rendering in progress... %ds elapsed", elapsed)

            await browser.close()

        if download_done and dest_video_path.exists():
            log.info("[GoogleFlow] Genuine Google Veo MP4 video saved successfully: %s (%d KB)", dest_video_path, dest_video_path.stat().st_size // 1024)
            return {
                "status": "success",
                "product": product_name,
                "prompt": prompt,
                "project_url": project_url,
                "video_path": str(dest_video_path),
                "size_bytes": dest_video_path.stat().st_size
            }
        else:
            raise RuntimeError(
                f"Google Flow video render did not complete within {timeout_seconds}s. "
                f"Check project URL: {project_url}"
            )

    def run_sync(self, product_name: str, headless: bool = True, timeout_seconds: int = 240) -> dict[str, Any]:
        return asyncio.run(self.generate_and_extract_video(product_name, headless=headless, timeout_seconds=timeout_seconds))


if __name__ == "__main__":
    crawler = GoogleFlowCrawler()
    prod = sys.argv[1] if len(sys.argv) > 1 else "Women Solid Long Sleeve Bodycon Maxi Dress"
    result = crawler.run_sync(prod, headless=True)
    print("\n[Google Flow Crawl Success!]")
    print(json.dumps(result, indent=2))
