"""
Google Trends & Breaking News Monitor for FireCrawler.
Fetches real-time search surges (US, India, Global), extracts source news articles,
and creates clean research dossiers ready for Vox video generation.
"""
from __future__ import annotations

import json
import urllib.parse
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Any
import requests
from fire_crawler.crawler import FireCrawler


@dataclass
class TrendingStory:
    title: str
    approx_traffic: str
    news_source: str
    news_url: str
    pub_date: str
    geo: str


class GoogleTrendsCrawler:
    """Monitors real-time breakout Google Search Trends and extracts full news articles."""

    GEO_MAP = {
        "us": "US",
        "india": "IN",
        "uk": "GB",
        "global": "US",
    }

    def __init__(self):
        self.crawler = FireCrawler(use_js=False)

    def fetch_trending_topics(self, geo: str = "us", limit: int = 5) -> list[TrendingStory]:
        """
        Fetches official real-time daily breakout trends from Google Trends RSS.
        """
        geo_code = self.GEO_MAP.get(geo.lower(), "US")
        rss_url = f"https://trends.google.com/trending/rss?geo={geo_code}"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Accept": "application/rss+xml,application/xml;q=0.9,*/*;q=0.8",
        }
        
        res = requests.get(rss_url, headers=headers, timeout=15)
        if res.status_code != 200:
            print(f"[TrendsCrawler] Failed to fetch RSS: {res.status_code}")
            return []

        root = ET.fromstring(res.content)
        stories: list[TrendingStory] = []

        for item in root.findall(".//item")[:limit]:
            title_el = item.find("title")
            title = title_el.text.strip() if title_el is not None and title_el.text else "Trending Topic"

            # Approx traffic (e.g. 500K+, 200K+)
            traffic = "100K+"
            for child in item:
                if "approx_traffic" in child.tag and child.text:
                    traffic = child.text.strip()

            # Source news link
            news_url = ""
            news_source = "News"
            for child in item:
                if "news_item" in child.tag:
                    for sub in child:
                        if "news_item_url" in sub.tag and sub.text:
                            news_url = sub.text.strip()
                        if "news_item_source" in sub.tag and sub.text:
                            news_source = sub.text.strip()

            link_el = item.find("link")
            if not news_url and link_el is not None and link_el.text:
                news_url = link_el.text.strip()

            pub_el = item.find("pubDate")
            pub_date = pub_el.text.strip() if pub_el is not None and pub_el.text else ""

            stories.append(
                TrendingStory(
                    title=title,
                    approx_traffic=traffic,
                    news_source=news_source,
                    news_url=news_url,
                    pub_date=pub_date,
                    geo=geo_code,
                )
            )

        return stories

    def get_trending_dossier(self, story: TrendingStory, output_dir: Path | str | None = None) -> dict[str, Any]:
        """
        Takes a trending story, scrapes the source news article into clean Markdown,
        and returns a complete dossier ready for video script generation.
        """
        print(f">> [TrendsCrawler] Scraping source article: {story.news_url or story.title}")
        article_md = ""
        
        if story.news_url:
            try:
                page_res = self.crawler.scrape(story.news_url, use_js=False)
                article_md = page_res.markdown
            except Exception as e:
                print(f">> Fallback to Wikipedia/Web research due to: {e}")
        
        # If article is too short or blocked, research topic directly
        if len(article_md.strip()) < 200:
            res_list = self.crawler.research_topic(story.title)
            article_md = res_list[0].markdown if res_list else ""

        dossier = {
            "trending_title": story.title,
            "search_traffic": story.approx_traffic,
            "geo_region": story.geo,
            "news_source": story.news_source,
            "source_url": story.news_url,
            "markdown_content": article_md,
        }

        if output_dir:
            out_p = Path(output_dir)
            out_p.mkdir(parents=True, exist_ok=True)
            slug = urllib.parse.quote(story.title.replace(" ", "_"))
            file_p = out_p / f"trend_{story.geo}_{slug[:40]}.json"
            file_p.write_text(json.dumps(dossier, indent=2), encoding="utf-8")
            print(f">> Saved Trending Dossier to: {file_p}")

        return dossier
