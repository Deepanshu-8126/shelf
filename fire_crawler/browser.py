"""
Headless Browser Engine for FireCrawler.
Handles dynamic JavaScript SPAs (React, Next.js, Vue), anti-bot headers, 
and fallback HTTP requests for high-speed scraping.
"""
from __future__ import annotations

import time
from typing import Any
import requests

USER_AGENTS = [
    "FactsBotResearch/1.0 (Mozilla/5.0 Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
]


class BrowserFetcher:
    """Manages web fetching via either fast HTTP requests or Playwright headless Chromium."""

    def __init__(self, use_js: bool = True, timeout_sec: int = 30):
        self.use_js = use_js
        self.timeout_sec = timeout_sec

    def fetch_static(self, url: str) -> tuple[str, int]:
        """Fast HTTP GET request without launching browser."""
        headers = {
            "User-Agent": "FactsAIResearchBot/1.0 (contact: facts@bot.com; Windows NT 10.0)",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }
        res = requests.get(url, headers=headers, timeout=self.timeout_sec)
        return res.text, res.status_code

    def fetch_js_rendered(self, url: str) -> tuple[str, int]:
        """Launches headless Chromium via Playwright to fully execute JavaScript."""
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=["--disable-blink-features=AutomationControlled", "--no-sandbox"]
            )
            context = browser.new_context(
                user_agent=USER_AGENTS[0],
                viewport={"width": 1280, "height": 800},
                device_scale_factor=1,
            )
            page = context.new_page()
            
            # Optional: Block heavy media to speed up crawling
            page.route("**/*.{png,jpg,jpeg,webp,svg,gif,woff,woff2}", lambda route: route.abort())

            try:
                response = page.goto(url, wait_until="domcontentloaded", timeout=self.timeout_sec * 1000)
                # Wait for any dynamic hydration
                page.wait_for_load_state("networkidle", timeout=5000)
            except Exception:
                pass  # Proceed even if networkidle times out
            
            html_content = page.content()
            status_code = response.status if response else 200
            browser.close()
            return html_content, status_code

    def fetch(self, url: str, force_js: bool | None = None) -> tuple[str, int]:
        """Unified fetch router."""
        should_use_js = self.use_js if force_js is None else force_js
        if should_use_js:
            try:
                return self.fetch_js_rendered(url)
            except Exception as e:
                # Fallback to static on browser error
                print(f"[BrowserFetcher] JS Render failed ({e}), falling back to static request...")
                return self.fetch_static(url)
        else:
            return self.fetch_static(url)
