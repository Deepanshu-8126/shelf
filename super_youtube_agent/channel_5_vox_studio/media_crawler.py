"""
Vox Studio Media & Archival Crawler.
Pulls authentic historical images, satellite ocean maps, and open-license video B-roll.
Zero fake placeholders.
"""
from __future__ import annotations

import base64
import json
import re
import urllib.parse
from pathlib import Path
from typing import Any
import requests

from channel_5_vox_studio.config import IMAGES_DIR, VIDEOS_DIR
from channel_5_vox_studio.video_extractor import VideoExtractor

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
}


class MediaCrawler:
    """Unified crawler for topic research, archival photographs, and video B-roll."""

    def __init__(self, images_dir: Path = IMAGES_DIR, videos_dir: Path = VIDEOS_DIR):
        self.images_dir = Path(images_dir)
        self.videos_dir = Path(videos_dir)
        self.images_dir.mkdir(parents=True, exist_ok=True)
        self.videos_dir.mkdir(parents=True, exist_ok=True)

    def fetch_topic_media(self, topic: str) -> dict[str, list[Path]]:
        """
        Fetches a complete media kit for the topic:
        - Real historical maps
        - Vintage newspaper clippings
        - Historical photos (planes/ships/evidence)
        - Open B-roll video clips
        """
        print(f"\n[MediaCrawler] Searching authentic media kit for: '{topic}'...")
        media_kit: dict[str, list[Path]] = {
            "maps": [],
            "documents": [],
            "photos": [],
            "videos": [],
        }

        # 1. Fetch Real Map Image
        map_query = f"{topic} map"
        maps = self._search_wikimedia(map_query, limit=2)
        for url, title in maps:
            p = self._download_file(url, self.images_dir, prefix=f"map_{self._slug(topic)}")
            if p:
                media_kit["maps"].append(p)
                break

        # 2. Fetch Real Archival Newspaper / Document
        doc_query = f"{topic} newspaper 1945" if "bermuda" in topic.lower() else f"{topic} newspaper"
        docs = self._search_wikimedia(doc_query, limit=2)
        if not docs:
            docs = self._search_duckduckgo_images(f"{topic} historical newspaper clipping", limit=2)
        for item in docs:
            url = item if isinstance(item, str) else item[0]
            p = self._download_file(url, self.images_dir, prefix=f"doc_{self._slug(topic)}")
            if p:
                media_kit["documents"].append(p)
                break

        # 3. Fetch Real Historical Evidence Photos (e.g. Flight 19, TBM Avenger, wreckage)
        photo_query = f"{topic} flight 19" if "bermuda" in topic.lower() else f"{topic} history"
        photos = self._search_wikimedia(photo_query, limit=3)
        if not photos:
            photos = self._search_duckduckgo_images(f"{topic} historical archival photo", limit=3)
        for item in photos:
            url = item if isinstance(item, str) else item[0]
            p = self._download_file(url, self.images_dir, prefix=f"photo_{self._slug(topic)}")
            if p:
                media_kit["photos"].append(p)

        # 4. Fetch Real HD B-Roll Video Clip
        try:
            extractor = VideoExtractor(self.videos_dir)
            video_clip = extractor.fetch_video_broll(topic, target_seconds=4.0)
            if video_clip:
                media_kit["videos"].append(video_clip)
        except Exception as e:
            print(f"[MediaCrawler] Video extractor notice: {e}")

        print(f">> Media kit collected: {len(media_kit['maps'])} maps, {len(media_kit['documents'])} docs, {len(media_kit['photos'])} photos, {len(media_kit['videos'])} videos.")
        return media_kit

    def _fetch_open_broll(self, topic: str) -> Path | None:
        """Pulls authentic open CC0 B-roll video clip (e.g., ocean swells, dark stormy clouds)."""
        # Search query based on topic vibe
        search_terms = "dark stormy ocean waves" if "bermuda" in topic.lower() or "ocean" in topic.lower() else "cinematic dark clouds"
        
        # Method: Pexels Public Open Video Search
        try:
            url = f"https://api.pexels.com/videos/search?query={urllib.parse.quote(search_terms)}&per_page=1&orientation=portrait"
            headers = {"Authorization": "563492ad6f91700001000001859c235b91b94d93b3f20f065a782b83"}
            res = requests.get(url, headers=headers, timeout=10)
            if res.status_code == 200:
                data = res.json()
                videos = data.get("videos", [])
                if videos:
                    files = videos[0].get("video_files", [])
                    # Pick 720p or 1080p MP4
                    for vf in files:
                        if vf.get("quality") in ["hd", "sd"] and "mp4" in vf.get("file_type", ""):
                            v_url = vf.get("link")
                            if v_url:
                                saved_p = self._download_file(v_url, self.videos_dir, prefix=f"broll_{self._slug(topic)}", ext=".mp4")
                                if saved_p:
                                    return saved_p
        except Exception as e:
            print(f"[MediaCrawler] Open video search notice: {e}")
        return None

    def _search_wikimedia(self, query: str, limit: int = 4) -> list[tuple[str, str]]:
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
            res = requests.get(api_url, params=params, headers=HEADERS, timeout=15)
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
                if url and ("jpeg" in mime or "png" in mime or "jpg" in mime):
                    if info.get("size", 0) > 30000 or info.get("width", 0) >= 600:
                        results.append((url, page_data.get("title", "")))
                        if len(results) >= limit:
                            break
            return results
        except Exception:
            return []

    def _search_duckduckgo_images(self, query: str, limit: int = 3) -> list[str]:
        try:
            vqd_url = "https://duckduckgo.com/"
            res = requests.get(vqd_url, params={"q": query}, headers=HEADERS, timeout=10)
            vqd_match = re.search(r'vqd=([\d-]+)&', res.text) or re.search(r'vqd="([\d-]+)"', res.text)
            if not vqd_match:
                return []
            vqd = vqd_match.group(1)
            api_url = "https://duckduckgo.com/i.js"
            params = {"l": "us-en", "o": "json", "q": query, "vqd": vqd, "f": ",,,", "p": "1"}
            res = requests.get(api_url, params=params, headers=HEADERS, timeout=10)
            if res.status_code == 200:
                data = res.json()
                results = []
                for item in data.get("results", []):
                    img_url = item.get("image")
                    if img_url and any(ext in img_url.lower() for ext in [".jpg", ".jpeg", ".png"]):
                        results.append(img_url)
                        if len(results) >= limit:
                            break
                return results
        except Exception:
            pass
        return []

    def _download_file(self, url: str, target_dir: Path, prefix: str = "file", ext: str = None) -> Path | None:
        try:
            res = requests.get(url, headers=HEADERS, timeout=20, stream=True)
            if res.status_code != 200:
                return None
            if not ext:
                content_type = res.headers.get("content-type", "")
                if "png" in content_type:
                    ext = ".png"
                elif "webp" in content_type:
                    ext = ".webp"
                elif "mp4" in content_type:
                    ext = ".mp4"
                else:
                    ext = ".jpg"
            
            import random
            filename = f"{prefix}_{random.randint(10000, 99999)}{ext}"
            file_path = target_dir / filename
            with open(file_path, "wb") as f:
                for chunk in res.iter_content(chunk_size=65536):
                    f.write(chunk)
            if file_path.stat().st_size > 15000:
                return file_path
            else:
                file_path.unlink(missing_ok=True)
        except Exception:
            pass
        return None

    def _slug(self, text: str) -> str:
        return re.sub(r"[^a-zA-Z0-9]+", "_", text).strip("_").lower()[:30]


def to_base64_data_uri(file_path: Path | str) -> str:
    """Converts a local image/video to a base64 data URI for zero-CORS browser embedding."""
    p = Path(file_path)
    if not p.exists():
        return ""
    ext = p.suffix.lower().replace(".", "")
    mime_map = {
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "webp": "image/webp",
        "mp4": "video/mp4",
    }
    mime = mime_map.get(ext, "image/jpeg")
    raw = p.read_bytes()
    b64 = base64.b64encode(raw).decode("utf-8")
    return f"data:{mime};base64,{b64}"
