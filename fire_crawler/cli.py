"""
FireCrawler Command Line Interface (CLI).
Usage:
  python -m fire_crawler.cli scrape <URL> [-o output.md] [--no-js]
  python -m fire_crawler.cli crawl <URL> [--max-pages 5] [--max-depth 2] [-o ./output_dir]
  python -m fire_crawler.cli research "<Topic>" [-o ./research_dir]
"""
import argparse
import sys
from pathlib import Path
from fire_crawler.crawler import FireCrawler


def main():
    # Ensure Windows console utf-8
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(
        description="🔥 FireCrawler - Local Open-Source Firecrawl Alternative"
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Scrape Single Page
    p_scrape = subparsers.add_parser("scrape", help="Scrape a single URL into clean Markdown")
    p_scrape.add_argument("url", help="URL to scrape")
    p_scrape.add_argument("-o", "--output", help="Output file path (.md)", default=None)
    p_scrape.add_argument("--no-js", action="store_true", help="Disable headless browser JS rendering for faster fetch")

    # Recursive Crawl
    p_crawl = subparsers.add_parser("crawl", help="Recursively crawl a domain")
    p_crawl.add_argument("url", help="Starting URL to crawl")
    p_crawl.add_argument("-m", "--max-pages", type=int, default=5, help="Maximum number of pages to crawl")
    p_crawl.add_argument("-d", "--max-depth", type=int, default=2, help="Max recursion link depth")
    p_crawl.add_argument("-o", "--output", help="Output directory to store markdown files", default="./crawled_output")
    p_crawl.add_argument("--no-js", action="store_true", help="Disable headless browser JS rendering")

    # Topic Research
    p_research = subparsers.add_parser("research", help="Research a fact or mystery topic")
    p_research.add_argument("topic", help="Topic name (e.g. 'Richat Structure')")
    p_research.add_argument("-o", "--output", help="Output directory", default="./research_output")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    crawler = FireCrawler()

    if args.command == "scrape":
        use_js = not args.no_js
        res = crawler.scrape(args.url, use_js=use_js)
        print(f"\n>> Title: {res.title}")
        print(f">> Description: {res.description[:100]}...")
        print(f">> Markdown Length: {len(res.markdown)} characters")
        
        if args.output:
            out_file = Path(args.output)
            res.save_markdown(out_file)
            print(f">> Saved Markdown to: {out_file}")
        else:
            print("\n--- EXTRACTED MARKDOWN PREVIEW ---\n")
            print(res.markdown[:1200])

    elif args.command == "crawl":
        use_js = not args.no_js
        res = crawler.crawl(
            start_url=args.url,
            max_pages=args.max_pages,
            max_depth=args.max_depth,
            output_dir=args.output,
            use_js=use_js,
        )
        print(f"\n>> Finished crawl! Total Pages: {res.total_pages}")
        print(f">> Files saved in: {args.output}")

    elif args.command == "research":
        res_list = crawler.research_topic(args.topic, output_dir=args.output)
        print(f"\n>> Research complete for: '{args.topic}'")
        print(f">> Saved dossiers in: {args.output}")


if __name__ == "__main__":
    main()
