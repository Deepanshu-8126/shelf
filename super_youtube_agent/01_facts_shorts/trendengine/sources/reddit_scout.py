"""Reddit trend scout: extracts high-velocity viral posts from key subreddits."""
from __future__ import annotations

import time
import httpx
from typing import Any


class RedditScout:
    def __init__(self, subreddits: list[str] | None = None, limit: int = 15) -> None:
        self.subreddits = subreddits or [
            "space", "science", "interestingasfuck", "todayilearned", "damnthatsinteresting"
        ]
        self.limit = limit
        self.headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) FactShortsTrendEngine/1.0"}

    async def fetch_trends(self) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        now = time.time()
        
        async with httpx.AsyncClient(headers=self.headers, timeout=httpx.Timeout(10.0), follow_redirects=True) as client:
            for sub in self.subreddits:
                url = f"https://www.reddit.com/r/{sub}/top.json?limit={self.limit}&t=day"
                try:
                    resp = await client.get(url)
                    if resp.status_code != 200:
                        continue
                    data = resp.json()
                    children = data.get("data", {}).get("children", [])
                    for child in children:
                        post = child.get("data", {})
                        if post.get("over_18") or post.get("stickied"):
                            continue
                        
                        score = post.get("score", 0)
                        num_comments = post.get("num_comments", 0)
                        created_utc = post.get("created_utc", now)
                        age_hours = max(0.5, (now - created_utc) / 3600.0)
                        velocity = (score + num_comments * 2.5) / age_hours

                        title = post.get("title", "").strip()
                        selftext = post.get("selftext", "").strip()[:500]
                        url_post = f"https://reddit.com{post.get('permalink', '')}"

                        niche = "space" if sub == "space" else "science"
                        if "interesting" in sub or "todayilearned" in sub:
                            niche = "facts"

                        results.append({
                            "title": title,
                            "summary": selftext or title,
                            "source": f"reddit/r/{sub}",
                            "source_url": url_post,
                            "niche": niche,
                            "raw_score": score,
                            "velocity": velocity,
                            "age_hours": age_hours,
                            "fingerprint": f"reddit:{post.get('id', title[:30])}",
                        })
                except Exception:
                    continue
        return results
