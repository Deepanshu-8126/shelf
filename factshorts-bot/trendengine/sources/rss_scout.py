"""RSS scout: feeds from authoritative science publications (NASA, ScienceDaily, Phys.org)."""
from __future__ import annotations

import time
import feedparser
from typing import Any


DEFAULT_FEEDS = [
    {"name": "NASA Breaking", "url": "https://www.nasa.gov/rss/dyn/breaking_news.rss", "niche": "space"},
    {"name": "ScienceDaily", "url": "https://www.sciencedaily.com/rss/top/science.xml", "niche": "science"},
    {"name": "Phys.org Space", "url": "https://phys.org/rss-feed/space-news/", "niche": "space"},
]


class RSSScout:
    def __init__(self, feeds: list[dict[str, str]] | None = None) -> None:
        self.feeds = feeds or DEFAULT_FEEDS

    async def fetch_trends(self) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        now = time.time()

        for feed_info in self.feeds:
            name = feed_info.get("name", "RSS")
            url = feed_info.get("url", "")
            niche = feed_info.get("niche", "science")
            try:
                parsed = feedparser.parse(url)
                for entry in parsed.entries[:10]:
                    title = entry.get("title", "").strip()
                    summary = entry.get("summary", "").strip() or entry.get("description", "").strip()
                    link = entry.get("link", "")
                    
                    if not title:
                        continue
                    
                    # Freshness score
                    age_hours = 6.0
                    velocity = 25.0  # RSS baseline editorial value

                    results.append({
                        "title": title,
                        "summary": summary[:600] or title,
                        "source": f"rss/{name.lower().replace(' ', '_')}",
                        "source_url": link,
                        "niche": niche,
                        "raw_score": 500,
                        "velocity": velocity,
                        "age_hours": age_hours,
                        "fingerprint": f"rss:{title.lower()[:35]}",
                    })
            except Exception:
                continue
        return results
