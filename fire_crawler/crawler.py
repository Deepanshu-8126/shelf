"""
FireCrawler Master Engine.
Provides single-page scraping, recursive domain crawling, 
and automated fact-finding research pipelines.
"""
from __future__ import annotations

import json
import re
import urllib.parse
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any
from bs4 import BeautifulSoup
from fire_crawler.browser import BrowserFetcher
from fire_crawler.extractor import extract_clean_markdown, extract_metadata


@dataclass
class PageResult:
    url: str
    title: str
    markdown: str
    description: str = ""
    status_code: int = 200
    metadata: dict[str, Any] = field(default_factory=dict)
    internal_links: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def save_markdown(self, file_path: Path) -> Path:
        """Saves page to markdown with YAML frontmatter header."""
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        frontmatter = (
            "---\n"
            f"title: \"{self.title}\"\n"
            f"source_url: \"{self.url}\"\n"
            f"description: \"{self.description}\"\n"
            "---\n\n"
        )
        content = frontmatter + self.markdown
        file_path.write_text(content, encoding="utf-8")
        return file_path


@dataclass
class CrawlResult:
    base_url: str
    total_pages: int
    pages: list[PageResult] = field(default_factory=list)
    output_directory: Path | None = None

    def get_combined_markdown(self) -> str:
        """Combines all crawled pages into a single LLM-friendly master document."""
        chunks = [f"# Crawled Dataset: {self.base_url}\nTotal Pages: {self.total_pages}\n\n---\n"]
        for p in self.pages:
            chunks.append(f"## Page: {p.title}\n**Source:** {p.url}\n\n{p.markdown}\n\n---\n")
        return "\n".join(chunks)


class FireCrawler:
    """Production Firecrawl-grade crawler running locally in Python."""

    def __init__(self, use_js: bool = True, timeout_sec: int = 30):
        self.fetcher = BrowserFetcher(use_js=use_js, timeout_sec=timeout_sec)

    def scrape(self, url: str, use_js: bool | None = None) -> PageResult:
        """
        Scrapes a single URL and returns clean Markdown + structured metadata.
        """
        html, status_code = self.fetcher.fetch(url, force_js=use_js)
        markdown, metadata = extract_clean_markdown(html, url=url)
        
        # Extract internal links
        internal_links = self._extract_links(html, url)
        
        return PageResult(
            url=url,
            title=metadata.get("title", ""),
            description=metadata.get("description", ""),
            markdown=markdown,
            status_code=status_code,
            metadata=metadata,
            internal_links=internal_links,
        )

    def crawl(
        self,
        start_url: str,
        max_pages: int = 5,
        max_depth: int = 2,
        output_dir: Path | str | None = None,
        use_js: bool | None = None,
    ) -> CrawlResult:
        """
        Recursively crawls a website up to max_pages and max_depth.
        Saves each page as clean Markdown in output_dir.
        """
        parsed_base = urllib.parse.urlparse(start_url)
        base_domain = parsed_base.netloc
        
        visited: set[str] = set()
        queue: list[tuple[str, int]] = [(start_url, 0)]
        results: list[PageResult] = []

        out_path = Path(output_dir) if output_dir else None
        if out_path:
            out_path.mkdir(parents=True, exist_ok=True)

        print(f">> [FireCrawler] Starting domain crawl on: {start_url} (Max: {max_pages} pages)")

        while queue and len(results) < max_pages:
            current_url, depth = queue.pop(0)
            clean_url = current_url.split("#")[0].rstrip("/")
            
            if clean_url in visited or depth > max_depth:
                continue

            visited.add(clean_url)
            print(f">> [FireCrawler] Scraping ({len(results)+1}/{max_pages}): {clean_url}")
            
            try:
                page_res = self.scrape(clean_url, use_js=use_js)
                results.append(page_res)
                
                # Save individual markdown file if directory provided
                if out_path:
                    slug = self._slugify(page_res.title or f"page_{len(results)}")
                    file_name = out_path / f"{len(results):02d}_{slug[:50]}.md"
                    page_res.save_markdown(file_name)

                # Add new internal links to queue
                if depth < max_depth:
                    for link in page_res.internal_links:
                        p_link = urllib.parse.urlparse(link)
                        if p_link.netloc == base_domain and link not in visited:
                            queue.append((link, depth + 1))
                            
            except Exception as e:
                print(f"[FireCrawler] Error scraping {clean_url}: {e}")

        # Save manifest.json
        if out_path:
            manifest = {
                "base_url": start_url,
                "total_pages": len(results),
                "pages": [p.to_dict() for p in results]
            }
            (out_path / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
            (out_path / "COMBINED_CRAWL.md").write_text(
                CrawlResult(base_url=start_url, total_pages=len(results), pages=results).get_combined_markdown(),
                encoding="utf-8"
            )

        return CrawlResult(
            base_url=start_url,
            total_pages=len(results),
            pages=results,
            output_directory=out_path
        )

    def research_topic(self, topic: str, max_sources: int = 3, output_dir: Path | str | None = None) -> list[PageResult]:
        """
        Researches a historical mystery or factual topic across Wikipedia and encyclopedias.
        """
        # Formulate query URL on Wikipedia
        slug = urllib.parse.quote(topic.replace(" ", "_"))
        wiki_url = f"https://en.wikipedia.org/wiki/{slug}"
        
        print(f">> [FireCrawler] Researching topic: '{topic}' -> {wiki_url}")
        res = self.scrape(wiki_url, use_js=False)
        
        if output_dir:
            out_p = Path(output_dir)
            out_p.mkdir(parents=True, exist_ok=True)
            res.save_markdown(out_p / f"research_{self._slugify(topic)}.md")
            
        return [res]

    def _extract_links(self, html: str, base_url: str) -> list[str]:
        soup = BeautifulSoup(html, "html.parser")
        links = []
        for a in soup.find_all("a", href=True):
            href = str(a["href"]).strip()
            if not href or href.startswith(("#", "javascript:", "mailto:", "tel:")):
                continue
            abs_url = urllib.parse.urljoin(base_url, href)
            links.append(abs_url)
        return list(dict.fromkeys(links))  # Deduplicate while preserving order

    def _slugify(self, text: str) -> str:
        s = re.sub(r"[^\w\s-]", "", text).strip().lower()
        return re.sub(r"[-\s]+", "_", s)
