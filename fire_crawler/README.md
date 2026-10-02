# 🔥 FireCrawler (Local Open-Source Firecrawl Engine)

A 100% free, local Python web crawler and scraper that mirrors **Firecrawl** functionality without any paid API keys or subscription limits.

---

## ⚡ Features
1. **Dynamic JS Execution**: Full JavaScript & SPA rendering via headless Chromium (Playwright).
2. **Precision Content Extraction**: Strips navbars, ads, cookie banners, headers, and footers using `trafilatura` and `readability`.
3. **LLM-Ready Clean Markdown**: Outputs GitHub-Flavored Markdown with tables, links, images, and frontmatter.
4. **Recursive Crawling**: Automatically traverses internal domain links up to `max_depth` and `max_pages`.
5. **Research Engine**: Instantly scrapes and creates structured dossiers for mystery/fact topics.

---

## 💻 CLI Usage

### 1. Scrape a Single URL into Markdown
```bash
python -m fire_crawler.cli scrape "https://en.wikipedia.org/wiki/Richat_Structure" -o output.md
```

### 2. Recursively Crawl an Entire Website
```bash
python -m fire_crawler.cli crawl "https://example.com" --max-pages 10 --max-depth 2 -o ./crawled_data
```

### 3. Research a Fact / Mystery Topic
```bash
python -m fire_crawler.cli research "Bermuda Triangle" -o ./research_dossiers
```

---

## 🐍 Python API Usage

```python
from fire_crawler import FireCrawler

crawler = FireCrawler(use_js=True)

# 1. Scrape single page
result = crawler.scrape("https://en.wikipedia.org/wiki/Richat_Structure")
print("Title:", result.title)
print("Markdown:\n", result.markdown[:500])

# 2. Recursive domain crawl
crawl_res = crawler.crawl("https://example.com", max_pages=5, output_dir="./crawled_site")
print(f"Crawled {crawl_res.total_pages} pages!")

# 3. Topic Research
research_results = crawler.research_topic("Atlantis Mauritania", output_dir="./research")
```
