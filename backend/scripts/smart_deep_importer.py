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
if str(PROJECT_ROOT.parent) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT.parent))

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
    """Extracts live high-res CDN images using Context.dev cloud AI scraper or Playwright fallback."""
    if not product_url or "meesho.com" not in product_url or "/p/" not in product_url:
        return []

    # 1. Try Context.dev AI Cloud Scraper first (no local chromium needed, bypasses 403)
    try:
        from connectors.context_dev_scraper import ContextDevScraper
        scraper = ContextDevScraper()
        if scraper.is_configured:
            print(f"  🌐 [Context.dev Cloud Scraper] Extracting high-res images for: {product_url}...")
            ctx_data = scraper.extract_product_data(product_url)
            if ctx_data.get("images"):
                return ctx_data["images"]
    except Exception as e:
        print(f"  ℹ️ Context.dev crawl notice: {e}")

    # 2. Fallback to Playwright local crawler
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
        PROJECT_ROOT / "scripts" / "meesho-products-with-links.csv",
        PROJECT_ROOT / "uploads" / "meesho-com-2026-10-03.csv",
        PROJECT_ROOT.parent / "batch_engine" / "meesho-com-2026-10-03.csv",
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

    if not title and product_url:
        slug_match = re.search(r'meesho\.com/([a-zA-Z0-9-]+)/p/', product_url)
        if slug_match:
            slug_text = slug_match.group(1).replace('-', ' ').strip()
            if len(slug_text) > 4:
                title = slug_text.title()

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

    # Context.dev AI Enrichment (Bypasses anti-bot, extracts real title, price & images if URL pasted)
    ctx_extracted = None
    if product_url and ("/p/" in product_url or "meesho.com" in product_url):
        try:
            from connectors.context_dev_scraper import ContextDevScraper
            ctx_scraper = ContextDevScraper()
            if ctx_scraper.is_configured:
                if title == "Aesthetic Gen Z Trending Outfit" or not cleaned_images or len(raw_lines) <= 4:
                    print(f"  🌐 [Context.dev AI] Cloud-extracting details for: {product_url}...")
                    ctx_extracted = ctx_scraper.extract_product_data(product_url)
                    if ctx_extracted.get("title") and ctx_extracted.get("source") != "offline_fallback":
                        title = ctx_extracted["title"]
                    if ctx_extracted.get("images"):
                        for im in ctx_extracted["images"]:
                            if im not in cleaned_images:
                                cleaned_images.append(im)
        except Exception as e:
            print(f"  ℹ️ Context.dev notice: {e}")

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
    elif ctx_extracted and ctx_extracted.get("price"):
        p_val = int(re.sub(r'\D', '', str(ctx_extracted["price"])) or 299)
        price = p_val
        orig_val = int(re.sub(r'\D', '', str(ctx_extracted.get("original_price", ""))) or int(p_val * 1.25))
        old_price = max(orig_val, int(p_val * 1.25))
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
    if ctx_extracted and ctx_extracted.get("fabric"):
        fabric = ctx_extracted["fabric"].strip()[:30]
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


def deep_scrape_meesho_url(
    target_url: str,
    max_items: int = 8,
    profit_margin_pct: float = 0.45,
    collection_id: str = "meesho-genz-2026"
) -> list[dict]:
    """
    Autonomous multi-tier deep scraper for Meesho categories, searches, and products.
    Tier 1: Context.dev Cloud AI Scraper (bypasses anti-bot 403 blocks).
    Tier 2: Single Product Deep Parser (when target is a specific /p/ product).
    Tier 3: Curated & Web Scraper Catalog Engine (extracts matching items from rich local datasets).
    """
    clean_url = target_url.strip()
    if not clean_url:
        return []

    # Case 1: Direct single product link
    if "/p/" in clean_url:
        single_item = parse_deep_listing(clean_url)
        if single_item:
            cost = single_item.get("price", 399)
            retail = int(cost * (1.0 + profit_margin_pct))
            single_item["oldPrice"] = max(single_item.get("oldPrice", 0), retail)
            single_item["costPrice"] = cost
            single_item["estimatedProfit"] = retail - cost
            single_item["collectionId"] = collection_id
            single_item["status"] = "pending_review"
            return [single_item]

    # Case 2: Category / Search / Collection Link
    results = []

    # Attempt 1: Context.dev Cloud Scraper
    try:
        from connectors.context_dev_scraper import ContextDevScraper
        scraper = ContextDevScraper()
        if scraper.is_configured:
            print(f"  🌐 [Context.dev AI] Crawling category markdown from: {clean_url}...")
            md = scraper.scrape_markdown(clean_url)
            if md:
                product_links = list(dict.fromkeys(
                    re.findall(r'https?://(?:www\.)?meesho\.com/[a-zA-Z0-9-]+/p/[a-zA-Z0-9]+', md)
                ))
                for link in product_links[:max_items]:
                    item = parse_deep_listing(link)
                    if item:
                        item["collectionId"] = collection_id
                        item["status"] = "pending_review"
                        results.append(item)
    except Exception as exc:
        print(f"  ℹ️ Context.dev category crawl notice: {exc}")

    if results:
        return results[:max_items]

    # Attempt 2: Rich Local Datasets (Web Scraper CSV / Curated Datasets)
    csv_candidates = [
        PROJECT_ROOT / "scripts" / "meesho-products-with-links.csv",
        PROJECT_ROOT / "uploads" / "meesho-com-2026-10-03.csv",
        PROJECT_ROOT.parent / "batch_engine" / "meesho-com-2026-10-03.csv",
        PROJECT_ROOT.parent / "photoshoot_pinterest_engine" / "meesho-com-2026-10-03.csv"
    ]

    # Extract search keywords from target_url
    url_slugs = re.sub(r'https?://[^/]+/', '', clean_url).lower()
    keywords = [w for w in re.split(r'[/_?&=-]+', url_slugs) if len(w) > 2 and w not in ["com", "meesho", "www", "search", "html", "pl"]]

    extracted = []
    seen_ids = set()

    for csv_file in csv_candidates:
        if not csv_file.exists():
            continue
        try:
            with open(csv_file, mode="r", encoding="utf-8", errors="ignore") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    u = row.get("item_page_link") or row.get("product_url") or row.get("web_scraper_start_url") or ""
                    title = (row.get("name_2") or row.get("name") or row.get("title") or row.get("item_page_title") or "").replace("\n", " ").strip()
                    if not title or len(title) < 5:
                        continue

                    low_title = (title + " " + u).lower()
                    matches_keywords = not keywords or any(kw in low_title for kw in keywords)

                    price_str = row.get("price") or row.get("price_1") or row.get("data") or "399"
                    digits = re.sub(r'\D', '', price_str)
                    price = int(digits) if digits else 399
                    cost_price = max(149, price)
                    retail_price = int(cost_price * (1.0 + profit_margin_pct))

                    img = row.get("image_4") or row.get("image") or row.get("image_1") or row.get("image2") or ""
                    if img:
                        img = img.split("?")[0].replace("width=100", "width=512").replace("width=360", "width=512")
                    if not img:
                        continue

                    ext_match = re.search(r'/p/([a-zA-Z0-9]+)', u)
                    ext_id = ext_match.group(1).lower() if ext_match else "".join(c for c in title if c.isalnum())[:8].lower()
                    if ext_id in seen_ids:
                        continue
                    seen_ids.add(ext_id)

                    fabric = (row.get("product_fabric") or "Cotton Blend").replace("Fabric :", "").strip()[:25]
                    prod_url = u if (u and "meesho.com" in u) else f"https://www.meesho.com/{re.sub(r'[^a-zA-Z0-9]+', '-', title).lower()[:30]}/p/{ext_id}"
                    slug = re.sub(r'[^a-zA-Z0-9]+', '-', title).lower().strip('-')[:35]

                    gallery = [img]
                    for g_key in ["image_1", "image_2", "image_3", "image_5", "image_6"]:
                        g_img = row.get(g_key, "")
                        if g_img and g_img != img:
                            gallery.append(g_img.split("?")[0])

                    raw_r = str(row.get("rating") or row.get("ratingValue") or row.get("rating_1") or "4.3")
                    r_match = re.search(r'([0-5](?:\.\d+)?)', raw_r)
                    rating_val = float(r_match.group(1)) if r_match else 4.3
                    r_count = int(re.sub(r'\D', '', str(row.get("rating_count") or row.get("reviewCount") or "240")) or 240)

                    item = {
                        "id": f"p-meesho-{slug}-{ext_id}",
                        "ext_id": ext_id,
                        "title": title[:55],
                        "subtitle": f"{fabric} · XS, S, M, L, XL · {collection_id} Viral Fit",
                        "brand": "Meesho Verified Creator Supplier",
                        "store": "Meesho",
                        "category": "Gen Z Aesthetic & Streetwear",
                        "collectionId": collection_id,
                        "tint": "peach",
                        "price": cost_price,
                        "oldPrice": retail_price,
                        "costPrice": cost_price,
                        "estimatedProfit": retail_price - cost_price,
                        "rating": rating_val,
                        "ratingCount": r_count,
                        "image": img,
                        "galleryImages": gallery[:6],
                        "colors": ["Viral Colorways"],
                        "sizes": ["XS", "S", "M", "L", "XL", "XXL"],
                        "inStock": True,
                        "productUrl": prod_url,
                        "affiliateUrl": build_affiliate_route(prod_url),
                        "status": "pending_review",
                        "isRealListing": True,
                        "source": "autonomous-deep-scraper",
                        "gallery": gallery[:6],
                        "imagePosition": "50% 40%",
                        "imageFit": "cover",
                        "clicks": 0,
                        "commission": f"{int(profit_margin_pct * 100)}%",
                        "saved": False,
                        "priceCheckedAt": datetime.now().strftime("%Y-%m-%d")
                    }

                    if matches_keywords:
                        extracted.insert(0, item)
                    else:
                        extracted.append(item)

                    if len(extracted) >= max_items * 3:
                        break
        except Exception as e:
            print(f"  ℹ️ CSV read notice ({csv_file.name}): {e}")

    if extracted:
        return extracted[:max_items]

    starter = parse_deep_listing(clean_url)
    starter["collectionId"] = collection_id
    starter["status"] = "pending_review"
    return [starter]
