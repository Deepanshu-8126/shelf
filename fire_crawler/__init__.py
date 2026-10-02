"""
FireCrawler - Open-Source Local Firecrawl Alternative for Python.
Provides JS-rendered web scraping, recursive domain crawling, 
clean LLM-ready markdown extraction, and archival research.
"""
from fire_crawler.crawler import FireCrawler, CrawlResult, PageResult
from fire_crawler.extractor import extract_clean_markdown, extract_metadata

__all__ = [
    "FireCrawler",
    "CrawlResult",
    "PageResult",
    "extract_clean_markdown",
    "extract_metadata",
]
