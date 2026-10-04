"""
Meesho Smart Product Picker
============================
Reads downloaded Meesho CSV exports, filters products with:
- Rating >= 4.2 stars
- Review count >= 300
- Valid product image

Returns best candidates for video generation.
"""
import csv
import os
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DOWNLOADS_DIR = Path(os.environ["USERPROFILE"]) / "Downloads"
OUT_DIR = Path("D:/affi;ate/trend-earning-system/data/scraped_products")
OUT_DIR.mkdir(parents=True, exist_ok=True)


def parse_all_csvs():
    """Parse all Meesho CSVs from Downloads folder."""
    candidates = []
    seen_urls = set()
    
    csv_files = sorted(DOWNLOADS_DIR.glob("meesho*.csv"), key=lambda f: f.stat().st_mtime, reverse=True)
    csv_files += sorted(DOWNLOADS_DIR.glob("3.csv"), key=lambda f: f.stat().st_mtime, reverse=True)
    
    for csv_path in csv_files:
        try:
            with open(csv_path, "r", encoding="utf-8", errors="replace") as f:
                rows = list(csv.DictReader(f))
        except Exception as e:
            print(f"Error reading {csv_path.name}: {e}")
            continue
        
        print(f"Processing {csv_path.name}: {len(rows)} rows")
        
        for r in rows:
            url = r.get("item_page_link", "").strip()
            if not url or url in seen_urls:
                continue
            seen_urls.add(url)
            
            rv = r.get("ratingValue", "").strip()
            rc = r.get("reviewCount", "").strip()
            name = r.get("name", "").strip()
            price = r.get("price", "").strip()
            
            if not rv or not name:
                continue
            
            try:
                rating = float(rv)
            except ValueError:
                continue
            
            # Extract numeric review count
            m = re.search(r"([\d,]+)", rc)
            review_num = int(m.group(1).replace(",", "")) if m else 0
            
            # Get best image (first from image_1, prefer 1024 size)
            img_raw = (r.get("image_1", "") or r.get("image", "")).strip().split("\n")[0].strip()
            # Upgrade to 1024
            img_hires = re.sub(r"_(\d+)\.(webp|jpg)", "_1024.jpg", img_raw)
            
            if rating >= 4.2 and review_num >= 300 and name and img_raw:
                candidates.append({
                    "url": url,
                    "name": name,
                    "price": price,
                    "rating": rating,
                    "reviews": review_num,
                    "fabric": r.get("product_fabric", "").replace("Fabric :", "").strip(),
                    "pattern": r.get("product_pattern", "").replace("Pattern :", "").strip(),
                    "description": r.get("product_description", "").strip()[:200],
                    "highlights": r.get("product_highlights", "").strip()[:400],
                    "sizes": r.get("sizes_available", "").replace("\n", ", ").strip(),
                    "seller": r.get("seller_name", "").strip(),
                    "image_url": img_raw,
                    "image_hires": img_hires,
                    "source_csv": csv_path.name
                })
    
    # Sort: highest rating, then highest reviews
    candidates.sort(key=lambda x: (x["rating"], x["reviews"]), reverse=True)
    return candidates


def download_product_image(item: dict) -> Path:
    """Download product image to local scraped_products folder."""
    import urllib.request
    slug = re.sub(r"[^a-zA-Z0-9]", "_", item["name"][:20]).lower()
    local_path = OUT_DIR / f"auto_{slug}.jpg"
    
    if local_path.exists() and local_path.stat().st_size > 10000:
        print(f"  Image already cached: {local_path.name}")
        return local_path
    
    for img_url in [item["image_hires"], item["image_url"]]:
        try:
            req = urllib.request.Request(
                img_url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            )
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = resp.read()
                if len(data) > 10000:
                    local_path.write_bytes(data)
                    print(f"  Downloaded image: {local_path.name} ({len(data)//1024}KB)")
                    return local_path
        except Exception as e:
            print(f"  Image download attempt failed ({img_url[:60]}...): {e}")
    
    return None


if __name__ == "__main__":
    print("=" * 60)
    print("MEESHO SMART PRODUCT PICKER")
    print("=" * 60)
    
    candidates = parse_all_csvs()
    print(f"\nTotal qualifying products (rating >= 4.2, reviews >= 300): {len(candidates)}")
    print()
    
    for i, c in enumerate(candidates[:10]):
        print(f"[{i+1}] {c['rating']}* | {c['reviews']:,} reviews | {c['price']} | {c['name'][:45]}")
        print(f"     URL: {c['url']}")
        print(f"     Fabric: {c['fabric']} | Pattern: {c['pattern']}")
        print(f"     Sizes: {c['sizes'][:40]}")
        print()
    
    if candidates:
        print("Downloading best product image...")
        best = candidates[0]
        img_path = download_product_image(best)
        if img_path:
            print(f"\nBEST PRODUCT READY FOR VIDEO GENERATION:")
            print(f"  Name: {best['name']}")
            print(f"  Rating: {best['rating']}* ({best['reviews']:,} reviews)")
            print(f"  Price: {best['price']}")
            print(f"  Fabric: {best['fabric']}")
            print(f"  URL: {best['url']}")
            print(f"  Local Image: {img_path}")
