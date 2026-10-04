#!/usr/bin/env python3
"""Sync published blog articles, ebooks, and update sitemap in storefront."""
import os
import shutil
from pathlib import Path

STOREFRONT_PUBLIC = Path("d:/affi;ate/shelf-storefront/public")
PUBLISHED_DIR = Path("d:/affi;ate/trend-earning-system/data/published")
EBOOKS_DIR = Path("d:/affi;ate/trend-earning-system/data/ebooks")

def sync_assets():
    # 1. Sync blog articles
    blog_dest = STOREFRONT_PUBLIC / "blog"
    blog_dest.mkdir(parents=True, exist_ok=True)
    
    blog_urls = []
    if PUBLISHED_DIR.exists():
        for f in PUBLISHED_DIR.glob("*.html"):
            shutil.copy2(f, blog_dest / f.name)
            if f.name != "index.html":
                blog_urls.append(f"https://shelf.store/blog/{f.name}")
        print(f"✓ Copied {len(blog_urls)} blog articles to {blog_dest}")

    # 2. Sync eBooks
    ebook_dest = STOREFRONT_PUBLIC / "ebooks"
    ebook_dest.mkdir(parents=True, exist_ok=True)
    
    ebook_urls = []
    if EBOOKS_DIR.exists():
        for f in EBOOKS_DIR.glob("*.html"):
            shutil.copy2(f, ebook_dest / f.name)
            ebook_urls.append(f"https://shelf.store/ebooks/{f.name}")
        print(f"✓ Copied {len(ebook_urls)} ebooks to {ebook_dest}")

    # 3. Generate Master Sitemap
    sitemap_lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
        '  <url>',
        '    <loc>https://shelf.store/</loc>',
        '    <lastmod>2026-10-04</lastmod>',
        '    <changefreq>daily</changefreq>',
        '    <priority>1.0</priority>',
        '  </url>',
        '  <url>',
        '    <loc>https://shelf.store/#wishlink</loc>',
        '    <lastmod>2026-10-04</lastmod>',
        '    <changefreq>daily</changefreq>',
        '    <priority>0.9</priority>',
        '  </url>'
    ]
    
    # Add blog index
    sitemap_lines.extend([
        '  <url>',
        '    <loc>https://shelf.store/blog/index.html</loc>',
        '    <lastmod>2026-10-04</lastmod>',
        '    <changefreq>daily</changefreq>',
        '    <priority>0.9</priority>',
        '  </url>'
    ])
    
    for url in blog_urls:
        sitemap_lines.extend([
            '  <url>',
            f'    <loc>{url}</loc>',
            '    <lastmod>2026-10-04</lastmod>',
            '    <changefreq>weekly</changefreq>',
            '    <priority>0.8</priority>',
            '  </url>'
        ])

    for url in ebook_urls:
        sitemap_lines.extend([
            '  <url>',
            f'    <loc>{url}</loc>',
            '    <lastmod>2026-10-04</lastmod>',
            '    <changefreq>monthly</changefreq>',
            '    <priority>0.7</priority>',
            '  </url>'
        ])
        
    sitemap_lines.append('</urlset>')
    
    sitemap_file = STOREFRONT_PUBLIC / "sitemap.xml"
    sitemap_file.write_text("\n".join(sitemap_lines), encoding="utf-8")
    print(f"✓ Master sitemap.xml generated with {len(blog_urls) + len(ebook_urls) + 3} URLs.")

if __name__ == "__main__":
    sync_assets()
