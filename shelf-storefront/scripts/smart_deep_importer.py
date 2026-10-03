"""
==============================================================================
⚡ REAL-TIME PLAYWRIGHT + CATALOG HYBRID MEESHO CRAWLER
==============================================================================
1. Live Browser Crawler (Playwright): When a URL is pasted, connects to live
   Meesho page and extracts all high-res gallery images (512px).
2. Bulletproof Text Parser: Parses title, price, discount, sizes, colors from paste.
3. CSV Batch Processor: 1-click batch ingestion from any CSV file.
4. Auto-Affiliate Routing: Generates official Creator Affiliate route.
==============================================================================
"""

import os
import sys
import json
import re
import csv
import asyncio
import urllib.parse
from datetime import datetime
from pathlib import Path

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

AFFILIATE_CREATOR_ID = "374453404"
CAMPAIGN_ID = "12492338"
SOURCE_PARAM = "youtube_long_form"

IGNORE_TITLE_WORDS = {
    "become a supplier", "investor relations", "profile", "cart", "cart1", "cart2", "cart3",
    "home", "women", "men", "kids", "beauty", "electronics", "western wear", "tshirts",
    "popular", "add to cart", "buy now", "similar products", "product highlights", "copy",
    "additional details", "sold by", "view shop", "check delivery date", "enter delivery pincode",
    "check", "dispatch in", "product ratings & reviews", "lowest price", "cash on delivery",
    "7-day returns", "14 days returns", "people also viewed", "shop non-stop on meesho",
    "trusted by crores of indians", "careers", "hall of fame", "sitemap", "legal and policies",
    "meesho tech blog", "notices and returns", "reach out to us", "contact us", "select size"
}

KNOWN_COLORS = [
    "Green", "Black", "White", "Maroon", "Red", "Pink", "Beige", "Brown", "Coffee",
    "Blue", "Navy", "Sage", "Olive", "Yellow", "Mustard", "Purple",
    "Lavender", "Rust", "Peach", "Cream", "Grey", "Silver", "Gold", "Multicolor"
]


def build_affiliate_route(url: str, p_id_default: str = "542355935") -> str:
    if not url:
        return ""
    ext_match = re.search(r'/p/([a-zA-Z0-9]+)', url)
    ext_id = ext_match.group(1) if ext_match else "item"
    pid_match = re.search(r'p_id=(\d+)', url)
    p_id = pid_match.group(1) if pid_match else p_id_default
    
    encoded_url = urllib.parse.quote(url, safe='')
    return f"https://www.meesho.com/af_invite/{AFFILIATE_CREATOR_ID}:{SOURCE_PARAM}:{CAMPAIGN_ID}?p_id={p_id}&ext_id={ext_id}&utm_source={SOURCE_PARAM}&url={encoded_url}"


def crawl_live_meesho_images(product_url: str) -> list[str]:
    """Uses Playwright to extract live high-res CDN images directly from Meesho page."""
    if not product_url or "meesho.com" not in product_url or "/p/" not in product_url:
        return []

    async def _extract():
        try:
            from playwright.async_api import async_playwright
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-blink-features=AutomationControlled'])
                page = await browser.new_page()
                await page.goto(product_url, wait_until='domcontentloaded', timeout=12000)
                imgs = await page.locator('img[src*="images.meesho.com"]').all()
                srcs = []
                for img in imgs:
                    src = await img.get_attribute('src') or ''
                    if src and 'products/' in src and 'avatar' not in src:
                        clean = src.split('?')[0].replace('width=100', 'width=512').replace('width=360', 'width=512')
                        if clean not in srcs:
                            srcs.append(clean)
                await browser.close()
                return srcs
        except Exception as e:
            print(f"  ℹ️ Live crawl notice: {e}")
            return []

    try:
        return asyncio.run(_extract())
    except Exception:
        return []


def lookup_local_catalog(product_url: str) -> dict | None:
    """Checks local database for instant 0ms match."""
    if not product_url:
        return None
    ext_match = re.search(r'/p/([a-zA-Z0-9]+)', product_url)
    ext_id = ext_match.group(1).lower() if ext_match else ""

    csv_paths = [
        PROJECT_ROOT.parent / "photoshoot_pinterest_engine" / "meesho-com-2026-10-03.csv",
        PROJECT_ROOT / "meesho-com-2026-10-03-shelf-ready.csv",
        PROJECT_ROOT.parent / "photoshoot_pinterest_engine" / "curated_photoshoot_prompts.json"
    ]

    for p in csv_paths:
        if not p.exists():
            continue
        try:
            if p.suffix == ".json":
                with open(p, "r", encoding="utf-8") as jf:
                    data = json.load(jf)
                    for item in data:
                        if ext_id and ext_id in item.get("link", "").lower():
                            return {
                                "title": item.get("title", ""),
                                "price": int(re.sub(r'\D', '', item.get("price", "399")) or 399),
                                "image": item.get("image_url", ""),
                                "fabric": item.get("fabric", "Lycra"),
                                "sizes": ["XS", "S", "M", "L", "XL", "XXL"]
                            }
            elif p.suffix == ".csv":
                with open(p, "r", encoding="utf-8", errors="replace") as cf:
                    reader = csv.DictReader(cf)
                    for row in reader:
                        u1 = row.get("web_scraper_start_url", "")
                        u2 = row.get("item_page_link", "")
                        if (ext_id and (ext_id in u1.lower() or ext_id in u2.lower())) or (product_url in u1 or product_url in u2):
                            title = row.get("name_2") or row.get("name") or row.get("title") or ""
                            price_str = row.get("price") or row.get("price_1") or row.get("data") or "399"
                            price = int(re.sub(r'\D', '', price_str) or 399)
                            img = row.get("image") or row.get("image_1") or row.get("image2") or ""
                            fabric = (row.get("product_fabric") or "Cotton").replace("Fabric :", "").strip()
                            return {
                                "title": title.replace("\n", " ").strip(),
                                "price": price,
                                "image": img,
                                "fabric": fabric,
                                "sizes": ["XS", "S", "M", "L", "XL", "XXL"]
                            }
        except Exception:
            continue
    return None


def parse_deep_listing(raw_text: str) -> dict:
    """Bulletproof parsing of raw copied Meesho page text or URLs."""
    raw_lines = [l.strip() for l in raw_text.splitlines() if l.strip()]

    # 1. Product Link Extraction
    product_urls = re.findall(r'(https?://(?:www\.)?meesho\.com/[a-zA-Z0-9-]+/p/([a-zA-Z0-9]+))', raw_text)
    product_url = ""
    ext_id = ""
    if product_urls:
        product_url = product_urls[0][0]
        ext_id = product_urls[0][1]
    else:
        any_urls = re.findall(r'(https?://(?:www\.)?meesho\.com/[^\s"\'<>]+)', raw_text)
        for u in any_urls:
            if not any(ign in u for ign in ["cart", "supplier", "legal", "sitemap", "jobs", "blog"]):
                product_url = u
                ext_match = re.search(r'/p/([a-zA-Z0-9]+)', u)
                if ext_match:
                    ext_id = ext_match.group(1)
                break

    # 2. Check local database first
    matched = lookup_local_catalog(product_url) if product_url else None

    # 3. Product Title Extraction
    title = ""
    for i, line in enumerate(raw_lines):
        clean_l = line.lower().strip()
        if clean_l in ["add to cart", "buy now", "1 similar products", "select size"]:
            if i > 0:
                prev = raw_lines[i - 1].strip()
                if len(prev) > 8 and prev.lower() not in IGNORE_TITLE_WORDS and not prev.startswith("http") and not prev.startswith("₹") and not prev.startswith("["):
                    title = prev
                    break

    if not title and matched and matched.get("title"):
        title = matched["title"]

    if not title:
        for line in raw_lines:
            clean_l = line.lower().strip()
            if len(line) > 10 and clean_l not in IGNORE_TITLE_WORDS and not line.startswith("http") and not line.startswith("₹") and not line.startswith("[") and not line.startswith("(") and not line.startswith("@"):
                if not any(cat in clean_l for cat in ["women western wear", "women tshirts", "all sarees", "kurti, saree"]):
                    title = line
                    break

    if not title:
        title = "Aesthetic Gen Z Trending Outfit"

    title = re.sub(r'\s+', ' ', title).strip()
    if not ext_id:
        ext_id = "".join(c for c in title if c.isalnum())[:8].lower()

    if not product_url:
        slug = re.sub(r'[^a-zA-Z0-9]+', '-', title).lower().strip('-')
        product_url = f"https://www.meesho.com/{slug}/p/{ext_id}"

    # 4. Images (Hybrid: Paste Regex -> Local Catalog -> Live Playwright Crawler)
    cdn_images = re.findall(r'(https?://images\.meesho\.com/images/products/[a-zA-Z0-9_/]+\.webp(?:\?width=\d+)?)', raw_text)
    cleaned_images = [img.split('?')[0].replace('width=100', 'width=512').replace('width=360', 'width=512') for img in cdn_images]

    if not cleaned_images and matched and matched.get("image"):
        cleaned_images.append(matched["image"].split('?')[0].replace('width=100', 'width=512').replace('width=360', 'width=512'))

    # If still no image and we have a product URL, run the live crawler
    if not cleaned_images and product_url and "/p/" in product_url:
        print(f"  🌐 [Smart Crawler] Crawling live Meesho CDN images for: {product_url}...")
        crawled = crawl_live_meesho_images(product_url)
        if crawled:
            cleaned_images.extend(crawled)

    primary_image = cleaned_images[0] if cleaned_images else "https://images.meesho.com/images/products/682813217/hbo6b_512.webp"
    gallery_images = cleaned_images[1:6] if len(cleaned_images) > 1 else [primary_image]

    # 5. Prices & Margins
    price_tokens = re.findall(r'₹\s*([0-9]+)', raw_text)
    price = matched.get("price", 245) if matched else 245
    old_price = 299

    cleaned_prices = []
    for pt in price_tokens:
        val = int(pt)
        if val > 1000 and ("4% off" in raw_text or "off" in raw_text):
            s_val = str(val)
            if len(s_val) == 4 and int(s_val[:3]) < 800:
                val = int(s_val[:3])
        if 80 <= val <= 25000:
            cleaned_prices.append(val)

    if cleaned_prices:
        price = cleaned_prices[0]
        if len(cleaned_prices) > 1 and cleaned_prices[1] > price:
            old_price = cleaned_prices[1]
        else:
            old_price = int(price * 1.25)
    elif matched and matched.get("price"):
        price = matched["price"]
        old_price = int(price * 1.25)

    cost_price = max(149, price - 100)
    profit = price - cost_price

    # 6. Color & Fabric
    color = "Green"
    color_match = re.search(r'Color\s*:?\s*([A-Za-z]+)', raw_text, re.IGNORECASE)
    if color_match:
        cand = color_match.group(1).capitalize()
        if any(c.lower() == cand.lower() for c in KNOWN_COLORS):
            color = cand
    else:
        for c in KNOWN_COLORS:
            if re.search(r'\b' + c + r'\b', raw_text, re.IGNORECASE):
                color = c
                break

    fabric = matched.get("fabric", "Cotton") if matched else "Cotton"
    fabric_match = re.search(r'Fabric\s*:?\s*([A-Za-z\s&]+)', raw_text, re.IGNORECASE)
    if fabric_match:
        fabric = fabric_match.group(1).splitlines()[0].strip()[:25]

    # 7. Sizes
    sizes = []
    if "SMLXL" in raw_text or re.search(r'S\s*M\s*L\s*XL', raw_text):
        sizes = ["S", "M", "L", "XL"]
    elif "XXS" in raw_text or "XXL" in raw_text:
        sizes = ["XS", "S", "M", "L", "XL", "XXL"]
    else:
        for s in ["XS", "S", "M", "L", "XL", "XXL", "Free Size"]:
            if re.search(r'\b' + s + r'\b', raw_text):
                sizes.append(s)
    if not sizes:
        sizes = ["S", "M", "L", "XL"]

    # 8. Category & Collection
    lower_all = (title + " " + raw_text).lower()
    if any(k in lower_all for k in ["brasil", "rio", "graphic", "tee", "tshirt", "t-shirt", "streetwear", "y2k", "oversized"]):
        category = "Gen Z Aesthetic & Streetwear"
        collection_id = "meesho-genz-2026"
        tint = "sage"
    elif any(k in lower_all for k in ["dress", "maxi", "midi", "bodycon", "gown"]):
        category = "Women Dresses"
        collection_id = "meesho-dresses-2026"
        tint = "peach"
    elif any(k in lower_all for k in ["kurti", "kurta", "anarkali", "suit"]):
        category = "Kurtis"
        collection_id = "meesho-kurtis-2026"
        tint = "lilac"
    elif any(k in lower_all for k in ["co-ord", "set", "two piece"]):
        category = "Co-ord Sets"
        collection_id = "meesho-coord-2026"
        tint = "lavender"
    else:
        category = "Tops & Tunics"
        collection_id = "meesho-western-2026"
        tint = "peach"

    affiliate_url = build_affiliate_route(product_url)
    slug = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')[:35]

    return {
        "id": f"p-meesho-{slug}-{ext_id}",
        "ext_id": ext_id,
        "title": title,
        "subtitle": f"{color} · {fabric} · {', '.join(sizes)} · Gen Z Viral Fit",
        "brand": "Meesho Verified Creator Supplier",
        "store": "Meesho",
        "category": category,
        "collectionId": collection_id,
        "tint": tint,
        "price": price,
        "oldPrice": old_price,
        "costPrice": cost_price,
        "estimatedProfit": profit,
        "rating": 4.2,
        "ratingCount": 180,
        "image": primary_image,
        "galleryImages": gallery_images,
        "colors": [color],
        "sizes": sizes,
        "inStock": True,
        "productUrl": product_url,
        "affiliateUrl": affiliate_url,
        "status": "pending_review",
        "isRealListing": True,
        "source": "smart-live-crawler",
        "gallery": gallery_images,
        "imagePosition": "50% 40%",
        "imageFit": "cover",
        "clicks": 0,
        "commission": "15%",
        "saved": False,
        "priceCheckedAt": datetime.now().strftime("%Y-%m-%d")
    }


def deep_scrape_meesho_url(target_url: str, max_items: int = 8, profit_margin_pct: float = 0.45, collection_id: str = None) -> list[dict]:
    """Autonomous deep scraper for Meesho categories, searches, and product pages."""
    import urllib.request
    import urllib.error

    if not target_url or "meesho.com" not in target_url:
        raise ValueError("Please provide a valid meesho.com URL")

    # If it's a single product URL (/p/...)
    if "/p/" in target_url:
        raw_text = f"{target_url}\n"
        # Try fetching the page HTML for maximum detail
        try:
            req = urllib.request.Request(
                target_url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"}
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                html = resp.read().decode("utf-8", errors="ignore")
                raw_text += html
        except Exception:
            pass
        product = parse_deep_listing(raw_text)
        if collection_id:
            product["collectionId"] = collection_id
        return [product]

    # If it's a category/search page, crawl and extract product links
    product_urls = []
    page_html = ""
    try:
        req = urllib.request.Request(
            target_url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"}
        )
        with urllib.request.urlopen(req, timeout=12) as resp:
            page_html = resp.read().decode("utf-8", errors="ignore")
    except Exception as e:
        print(f"  ⚠️ Category fetch error: {e}")

    # Extract all /p/ links
    found_paths = re.findall(r'href="(/[a-zA-Z0-9-]+/p/([a-zA-Z0-9]+))"', page_html)
    for p_path, p_ext in found_paths:
        full_u = f"https://www.meesho.com{p_path}"
        if full_u not in product_urls and not any(ign in full_u for ign in ["cart", "supplier", "account", "legal"]):
            product_urls.append(full_u)

    # Fallback to local catalog if no links discovered from raw HTML
    if not product_urls:
        csv_path = PROJECT_ROOT.parent / "photoshoot_pinterest_engine" / "meesho-com-2026-10-03.csv"
        if csv_path.exists():
            with open(csv_path, "r", encoding="utf-8", errors="replace") as cf:
                reader = csv.DictReader(cf)
                for row in reader:
                    u = row.get("item_page_link") or row.get("web_scraper_start_url") or ""
                    if u and "meesho.com" in u and "/p/" in u and u not in product_urls:
                        product_urls.append(u)
                        if len(product_urls) >= max_items:
                            break

    results = []
    for p_url in product_urls[:max_items]:
        try:
            prod_text = f"{p_url}\n"
            try:
                p_req = urllib.request.Request(
                    p_url,
                    headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"}
                )
                with urllib.request.urlopen(p_req, timeout=8) as p_resp:
                    p_html = p_resp.read().decode("utf-8", errors="ignore")
                    prod_text += p_html
            except Exception:
                pass

            item = parse_deep_listing(prod_text)
            if collection_id:
                item["collectionId"] = collection_id
            results.append(item)
        except Exception as e:
            print(f"  ⚠️ Error parsing item {p_url}: {e}")

    return results

