"""
Authentic Image & Archival Photo Scraper for FireCrawler.
Fetches high-resolution real photographs, satellite maps, and historical evidence
from Wikimedia Commons, DuckDuckGo Images, and Open Archives (No fake placeholders).
"""
from __future__ import annotations

import json
import re
import time
import urllib.parse
from pathlib import Path
from typing import Any
import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
}


class RealImageFetcher:
    """Fetches real historical photos, satellite maps, and archival evidence for video topics."""

    def __init__(self, download_dir: Path | str = "d:/facts_yt/dark_case_studio/assets/real_images"):
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(parents=True, exist_ok=True)

    def fetch_topic_images(self, query: str, count: int = 4) -> list[Path]:
        """
        Fetches authentic real photographs related to the query.
        1. Queries Wikimedia Commons API for authentic archival & historical images.
        2. Queries DuckDuckGo Image Search for real high-res photography.
        """
        print(f">> [ImageFetcher] Searching real high-res images for: '{query}'...")
        images: list[Path] = []
        
        # Method 1: Wikimedia Commons API (High-res authentic historical/archival photos)
        wiki_images = self._search_wikimedia(query, limit=count)
        for img_url, title in wiki_images:
            saved_p = self._download_image(img_url, prefix=f"wiki_{self._slugify(query)}")
            if saved_p:
                images.append(saved_p)
                if len(images) >= count:
                    return images

        # Method 2: DuckDuckGo Images Search (Real satellite maps and photos)
        if len(images) < count:
            ddg_images = self._search_duckduckgo_images(query, limit=count - len(images))
            for img_url in ddg_images:
                saved_p = self._download_image(img_url, prefix=f"photo_{self._slugify(query)}")
                if saved_p:
                    images.append(saved_p)
                    if len(images) >= count:
                        return images

        return images

    def _search_wikimedia(self, query: str, limit: int = 4) -> list[tuple[str, str]]:
        """Queries Wikimedia API for authentic public domain / archival photographs."""
        api_url = "https://commons.wikimedia.org/w/api.php"
        params = {
            "action": "query",
            "generator": "search",
            "gsrsearch": f"{query} filetype:bitmap",
            "gsrnamespace": "6",  # File namespace
            "gsrlimit": str(limit * 2),
            "prop": "imageinfo",
            "iiprop": "url|mime|size",
            "iiurlwidth": "1280",  # High resolution
            "format": "json",
        }

        try:
            res = requests.get(api_url, params=params, headers=HEADERS, timeout=15)
            if res.status_code != 200:
                return []
            
            data = res.json()
            pages = data.get("query", {}).get("pages", {})
            results = []

            for page_id, page_data in pages.items():
                imageinfo = page_data.get("imageinfo", [])
                if not imageinfo:
                    continue
                info = imageinfo[0]
                url = info.get("thumburl") or info.get("url")
                mime = info.get("mime", "")
                
                # Only accept clean JPEG/PNG images (no SVGs, no icons)
                if url and ("jpeg" in mime or "png" in mime or "jpg" in mime):
                    # Filter out tiny icon images
                    if info.get("width", 0) >= 400 or info.get("size", 0) > 40000:
                        results.append((url, page_data.get("title", "")))
                        if len(results) >= limit:
                            break
            return results
        except Exception as e:
            print(f"[ImageFetcher] Wikimedia search error: {e}")
            return []

    def _search_duckduckgo_images(self, query: str, limit: int = 4) -> list[str]:
        """Searches DuckDuckGo for high-resolution web photography."""
        try:
            # Get VQD token
            url = f"https://duckduckgo.com/?q={urllib.parse.quote(query)}&t=h_&iax=images&ia=images"
            res = requests.get(url, headers=HEADERS, timeout=10)
            vqd_match = re.search(r'vqd=([\d-]+)', res.text) or re.search(r'vqd="([\d-]+)"', res.text)
            if not vqd_match:
                return []
            
            vqd = vqd_match.group(1)
            img_api = "https://duckduckgo.com/i.js"
            params = {
                "l": "us-en",
                "o": "json",
                "q": query,
                "vqd": vqd,
                "f": ",,,",
                "p": "1",
            }
            res_img = requests.get(img_api, params=params, headers=HEADERS, timeout=10)
            if res_img.status_code != 200:
                return []
            
            data = res_img.json()
            results = []
            for item in data.get("results", []):
                img_url = item.get("image")
                if img_url and img_url.startswith("http"):
                    results.append(img_url)
                    if len(results) >= limit:
                        break
            return results
        except Exception as e:
            print(f"[ImageFetcher] DDG search error: {e}")
            return []

    def _download_image(self, url: str, prefix: str = "img") -> Path | None:
        """Downloads image and saves to disk as a verified image file."""
        try:
            res = requests.get(url, headers=HEADERS, timeout=15)
            if res.status_code != 200 or len(res.content) < 15000:  # Skip broken/corrupted images
                return None
            
            ext = ".jpg"
            content_type = res.headers.get("content-type", "")
            if "png" in content_type:
                ext = ".png"
            elif "webp" in content_type:
                ext = ".webp"

            file_name = f"{prefix}_{int(time.time()*1000) % 100000}{ext}"
            file_path = self.download_dir / file_name
            file_path.write_bytes(res.content)
            print(f">> [ImageFetcher] Saved REAL image: {file_path.name} ({len(res.content)//1024} KB)")
            return file_path
        except Exception as e:
            print(f"[ImageFetcher] Download failed for {url}: {e}")
            return None

    def _slugify(self, text: str) -> str:
        s = re.sub(r"[^\w\s-]", "", text).strip().lower()
        return re.sub(r"[-\s]+", "_", s)[:25]
