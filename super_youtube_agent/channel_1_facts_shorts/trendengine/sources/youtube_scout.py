"""YouTube trending scout: pulls viral science/space shorts topics."""
from __future__ import annotations

import os
import re
import urllib.parse
import httpx
from typing import Any


class YouTubeScout:
    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or os.getenv("YOUTUBE_API_KEY", "")

    async def fetch_trends(self, keywords: list[str] | None = None) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        kw_list = keywords or ["space facts shorts", "science mysteries shorts", "crazy psychology facts"]

        # If API key is provided, use official API
        if self.api_key:
            async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
                for kw in kw_list:
                    url = (
                        f"https://www.googleapis.com/youtube/v3/search?part=snippet&maxResults=5"
                        f"&q={urllib.parse.quote(kw)}&type=video&videoDuration=short&order=viewCount"
                        f"&key={self.api_key}"
                    )
                    try:
                        resp = await client.get(url)
                        if resp.status_code == 200:
                            data = resp.json()
                            for item in data.get("items", []):
                                snippet = item.get("snippet", {})
                                title = snippet.get("title", "")
                                desc = snippet.get("description", "")
                                vid_id = item.get("id", {}).get("videoId", "")
                                results.append({
                                    "title": title,
                                    "summary": desc or title,
                                    "source": "youtube_api",
                                    "source_url": f"https://youtube.com/watch?v={vid_id}",
                                    "niche": "space" if "space" in kw else "science",
                                    "raw_score": 1000,
                                    "velocity": 50.0,
                                    "age_hours": 12.0,
                                    "fingerprint": f"yt:{vid_id}",
                                })
                    except Exception:
                        continue
            return results

        # Key-less YouTube search RSS feed fallback
        async with httpx.AsyncClient(headers={"User-Agent": "Mozilla/5.0"}, timeout=httpx.Timeout(10.0)) as client:
            for kw in kw_list[:2]:
                url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(kw)}&sp=CAM%253D"
                try:
                    resp = await client.get(url)
                    if resp.status_code == 200:
                        # Extract video titles from initial data JSON
                        matches = re.findall(r'"title":\{"runs":\[\{"text":"([^"]+)"\}\]', resp.text)
                        for title in matches[:4]:
                            if len(title) > 15 and not any(r["title"] == title for r in results):
                                results.append({
                                    "title": title,
                                    "summary": title,
                                    "source": "youtube_trending",
                                    "source_url": "https://youtube.com",
                                    "niche": "space" if "space" in kw else "science",
                                    "raw_score": 800,
                                    "velocity": 35.0,
                                    "age_hours": 8.0,
                                    "fingerprint": f"yt_scrape:{title[:30]}",
                                })
                except Exception:
                    continue
        return results
