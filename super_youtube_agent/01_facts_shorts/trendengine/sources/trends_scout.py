"""Google Trends scout: extracts real-time trending searches and breakout queries."""
from __future__ import annotations

import re
import time
import xml.etree.ElementTree as ET
import httpx
from typing import Any


class TrendsScout:
    def __init__(self, geo: str = "IN") -> None:
        self.geo = geo.upper()
        self.headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) TrendsScout/1.0"}

    async def fetch_trends(self) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        # Google Trends daily search trends RSS feed
        url = f"https://trends.google.com/trending/rss?geo={self.geo}"
        now = time.time()

        try:
            async with httpx.AsyncClient(headers=self.headers, timeout=httpx.Timeout(10.0), follow_redirects=True) as client:
                resp = await client.get(url)
                if resp.status_code == 200:
                    root = ET.fromstring(resp.text)
                    channel = root.find("channel")
                    if channel is not None:
                        for item in channel.findall("item"):
                            title_elem = item.find("title")
                            desc_elem = item.find("description")
                            traffic_elem = item.find("{https://trends.google.com/trending/rss}approx_traffic")
                            link_elem = item.find("link")

                            title = title_elem.text.strip() if title_elem is not None and title_elem.text else ""
                            desc = desc_elem.text.strip() if desc_elem is not None and desc_elem.text else ""
                            # Clean HTML tags from description
                            clean_desc = re.sub(r"<[^>]+>", " ", desc).strip()
                            traffic_str = traffic_elem.text if traffic_elem is not None and traffic_elem.text else "10,000+"
                            
                            # Parse traffic number (e.g. 50,000+ -> 50000)
                            traffic = int(re.sub(r"[^\d]", "", traffic_str) or 10000)
                            velocity = traffic / 1000.0

                            link = link_elem.text if link_elem is not None and link_elem.text else ""

                            if title:
                                results.append({
                                    "title": title,
                                    "summary": clean_desc or title,
                                    "source": f"google_trends/{self.geo}",
                                    "source_url": link,
                                    "niche": "trending",
                                    "raw_score": traffic,
                                    "velocity": velocity,
                                    "age_hours": 1.0,
                                    "fingerprint": f"gtrends:{title.lower().replace(' ', '_')}",
                                })
        except Exception:
            pass
        return results
