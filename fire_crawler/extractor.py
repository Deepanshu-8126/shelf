"""
Content Extractor & Markdown Converter.
Converts raw HTML into clean, high-signal, LLM-ready GitHub Markdown.
Strips boilerplate, ads, cookie notices, navbars, and scripts.
"""
from __future__ import annotations

import re
from typing import Any
from bs4 import BeautifulSoup
import html2text
import trafilatura


def extract_metadata(html: str, url: str = "") -> dict[str, Any]:
    """Extracts rich page metadata (title, description, og:image, date, author)."""
    soup = BeautifulSoup(html, "html.parser")
    
    # Title
    title = ""
    og_title = soup.find("meta", property="og:title")
    if og_title and og_title.get("content"):
        title = str(og_title["content"]).strip()
    elif soup.title and soup.title.string:
        title = soup.title.string.strip()
        
    # Description
    desc = ""
    meta_desc = soup.find("meta", attrs={"name": re.compile(r"description", re.I)}) or \
                soup.find("meta", property="og:description")
    if meta_desc and meta_desc.get("content"):
        desc = str(meta_desc["content"]).strip()
        
    # Image
    image = ""
    og_img = soup.find("meta", property="og:image")
    if og_img and og_img.get("content"):
        image = str(og_img["content"]).strip()

    # Canonical
    canonical = url
    link_canon = soup.find("link", rel="canonical")
    if link_canon and link_canon.get("href"):
        canonical = str(link_canon["href"]).strip()

    # Published date & Author
    author = ""
    meta_author = soup.find("meta", attrs={"name": re.compile(r"author", re.I)})
    if meta_author and meta_author.get("content"):
        author = str(meta_author["content"]).strip()

    return {
        "title": title,
        "description": desc,
        "og_image": image,
        "canonical_url": canonical or url,
        "author": author,
    }


def extract_clean_markdown(
    html: str,
    url: str = "",
    include_links: bool = True,
    include_images: bool = True,
) -> tuple[str, dict[str, Any]]:
    """
    Primary Firecrawl-style extractor:
    1. Runs trafilatura precision content extractor.
    2. Fallback to readability-lxml + html2text if trafilatura returns sparse text.
    3. Returns (clean_markdown, metadata).
    """
    metadata = extract_metadata(html, url)
    
    # Method 1: Trafilatura (Industry standard for precision article extraction)
    extracted_md = trafilatura.extract(
        html,
        url=url,
        output_format="markdown",
        include_links=include_links,
        include_images=include_images,
        include_tables=True,
        favor_recall=True,
    )

    if extracted_md and len(extracted_md.strip()) > 150:
        return extracted_md.strip(), metadata

    # Method 2: Fallback with BeautifulSoup cleaning + html2text
    soup = BeautifulSoup(html, "html.parser")
    
    # Strip non-content elements
    for tag in soup(["script", "style", "nav", "footer", "header", "noscript", "svg", "form", "iframe"]):
        tag.decompose()

    # Remove ad/cookie containers by class or id pattern
    for tag in soup.find_all(attrs={"class": re.compile(r"cookie|banner|ad-|advert|popup|modal|sidebar", re.I)}):
        tag.decompose()
    for tag in soup.find_all(attrs={"id": re.compile(r"cookie|banner|ad-|advert|popup|modal|sidebar", re.I)}):
        tag.decompose()

    # Convert to markdown via html2text
    h2t = html2text.HTML2Text()
    h2t.ignore_links = not include_links
    h2t.ignore_images = not include_images
    h2t.body_width = 0  # No hard wrapping
    h2t.ignore_emphasis = False
    h2t.mark_code = True
    
    fallback_md = h2t.handle(str(soup)).strip()
    # Clean excessive newlines
    fallback_md = re.sub(r"\n{3,}", "\n\n", fallback_md)
    
    return fallback_md, metadata
