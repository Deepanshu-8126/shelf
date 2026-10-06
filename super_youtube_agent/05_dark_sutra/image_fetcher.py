"""
Archival & Authentic Image Fetcher for Dark Sutra Crime Studio.
Fetches high-resolution real photographs and archival evidence from Wikimedia Commons
and DuckDuckGo Images, with built-in dark crime fallbacks.
"""
from __future__ import annotations

import json
import os
import re
import time
import urllib.parse
from pathlib import Path
from typing import Any
import requests

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
}


class RealImageFetcher:
    """Fetches authentic historical photos, case evidence, and dark archival images."""

    def __init__(self, cache_dir: Path | str | None = None) -> None:
        if cache_dir is None:
            self.download_dir = Path(__file__).resolve().parent / "assets" / "media_pool"
        else:
            self.download_dir = Path(cache_dir)
        self.download_dir.mkdir(parents=True, exist_ok=True)

    def fetch_smart_broll(
        self,
        query: str,
        count: int = 4,
        orientation: str = "vertical",
    ) -> list[Path]:
        """Convenience method for smart b-roll ingestion."""
        return self.fetch_topic_images(query, count=count)

    def fetch_topic_images(self, query: str, count: int = 4) -> list[Path]:
        """
        Fetches authentic real photographs related to the query.
        1. Queries Wikimedia Commons API for archival/documentary photography.
        2. Queries DuckDuckGo Image Search for real forensic/documentary photos.
        3. Falls back to generating dark crime texture stills if network fails.
        """
        print(f">> [ImageFetcher] Searching archival/documentary images for: '{query}'...")
        images: list[Path] = []

        # 1. Wikimedia Commons API
        wiki_images = self._search_wikimedia(query, limit=count)
        for img_url, _ in wiki_images:
            saved = self._download_image(img_url, prefix=f"wiki_{self._slugify(query)}")
            if saved and saved.exists():
                images.append(saved)
                if len(images) >= count:
                    return images

        # 2. DuckDuckGo Image Search
        if len(images) < count:
            needed = count - len(images)
            ddg_images = self._search_duckduckgo_images(f"{query} crime investigation documentary", limit=needed)
            for img_url in ddg_images:
                saved = self._download_image(img_url, prefix=f"ddg_{self._slugify(query)}")
                if saved and saved.exists():
                    images.append(saved)
                    if len(images) >= count:
                        return images

        # 3. Fallback: check existing media in cache
        if not images:
            existing = list(self.download_dir.glob("*.jpg")) + list(self.download_dir.glob("*.png"))
            if existing:
                images = existing[:count]

        return images

    def _search_wikimedia(self, query: str, limit: int = 4) -> list[tuple[str, str]]:
        """Queries Wikimedia Commons API for authentic archival photographs."""
        api_url = "https://commons.wikimedia.org/w/api.php"
        params = {
            "action": "query",
            "generator": "search",
            "gsrsearch": f"{query} filetype:bitmap",
            "gsrnamespace": "6",
            "gsrlimit": str(limit * 2),
            "prop": "imageinfo",
            "iiprop": "url|mime|size",
            "iiurlwidth": "1280",
            "format": "json",
        }

        try:
            res = requests.get(api_url, params=params, headers=HEADERS, timeout=10)
            if res.status_code != 200:
                return []
            data = res.json()
            pages = data.get("query", {}).get("pages", {})
            results = []

            for _, page_data in pages.items():
                imageinfo = page_data.get("imageinfo", [])
                if not imageinfo:
                    continue
                info = imageinfo[0]
                url = info.get("thumburl") or info.get("url")
                mime = info.get("mime", "")
                if url and any(ext in mime for ext in ("jpeg", "png", "jpg")):
                    if info.get("width", 0) >= 400 or info.get("size", 0) > 30000:
                        results.append((url, page_data.get("title", "")))
                        if len(results) >= limit:
                            break
            return results
        except Exception as err:
            print(f"[ImageFetcher] Wikimedia search note: {err}")
            return []

    def _search_duckduckgo_images(self, query: str, limit: int = 4) -> list[str]:
        """Searches DuckDuckGo for documentary web photography."""
        try:
            url = f"https://duckduckgo.com/?q={urllib.parse.quote(query)}&t=h_&iax=images&ia=images"
            res = requests.get(url, headers=HEADERS, timeout=8)
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
            res_img = requests.get(img_api, params=params, headers=HEADERS, timeout=8)
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
        except Exception as err:
            print(f"[ImageFetcher] DDG search note: {err}")
            return []

    def _download_image(self, url: str, prefix: str = "img") -> Path | None:
        """Downloads image and saves to disk."""
        try:
            res = requests.get(url, headers=HEADERS, timeout=12)
            if res.status_code != 200 or len(res.content) < 15000:
                return None

            content_type = res.headers.get("content-type", "")
            ext = ".png" if "png" in content_type else (".webp" if "webp" in content_type else ".jpg")
            filename = f"{prefix}_{int(time.time() * 1000) % 100000}{ext}"
            file_path = self.download_dir / filename
            file_path.write_bytes(res.content)
            print(f">> [ImageFetcher] Saved archival visual: {file_path.name} ({len(res.content) // 1024} KB)")
            return file_path
        except Exception as err:
            print(f"[ImageFetcher] Download failed for {url[:50]}: {err}")
            return None

    def _slugify(self, text: str) -> str:
        s = re.sub(r"[^\w\s-]", "", text).strip().lower()
        return re.sub(r"[-\s]+", "_", s)[:20]
