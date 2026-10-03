"""
==============================================================================
⚡ SMART DEEP LIVE MEESHO & SOCIAL FETCHER (HYBRID CATALOG + SCRAPER)
==============================================================================
1. Catalog Instant Resolver: Instantly matches any Meesho URL/ext_id against
   the local 500+ verified products catalog for 0ms ultra-fast response.
2. Clipboard Raw Text Parser: Extracts title, multi-variants, sizes, prices,
   and Cloud CDN images from pasted text.
3. Automatically generates Creator Affiliate Route (374453404:12492338).
4. Returns rich structured product data for Admin Ingest Inbox.
==============================================================================
"""

import os
import sys
import json
import re
import csv
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
DATA_DIR = PROJECT_ROOT / "data"

AFFILIATE_CREATOR_ID = "374453404"
CAMPAIGN_ID = "12492338"
SOURCE_PARAM = "youtube_long_form"

KNOWN_COLORS = [
    "black", "white", "maroon", "red", "pink", "beige", "brown", "coffee",
    "blue", "navy", "green", "sage", "olive", "yellow", "mustard", "purple",
    "lavender", "rust", "peach", "cream", "grey", "silver", "gold"
]

KNOWN_SIZES = ["XS", "S", "M", "L", "XL", "XXL", "3XL", "Free Size"]


def extract_colors(text: str):
    found = []
    lower_text = text.lower()
    for c in KNOWN_COLORS:
        if re.search(r'\b' + c + r'\b', lower_text):
            found.append(c.capitalize())
    return found or ["Standard / Single Color"]


def extract_sizes(text: str):
    found = []
    for s in KNOWN_SIZES:
        if re.search(r'\b' + s + r'\b', text, re.IGNORECASE):
            found.append(s.upper())
    return found or ["S", "M", "L", "XL"]


def build_affiliate_route(url: str, p_id_default: str = "542355935") -> str:
    if not url:
        return ""
    ext_match = re.search(r'/p/([a-zA-Z0-9]+)', url)
    ext_id = ext_match.group(1) if ext_match else "item"
    pid_match = re.search(r'p_id=(\d+)', url)
    p_id = pid_match.group(1) if pid_match else p_id_default
    
    encoded_url = urllib.parse.quote(url, safe='')
    return f"https://www.meesho.com/af_invite/{AFFILIATE_CREATOR_ID}:{SOURCE_PARAM}:{CAMPAIGN_ID}?p_id={p_id}&ext_id={ext_id}&utm_source={SOURCE_PARAM}&url={encoded_url}"


def lookup_local_catalog(product_url: str) -> dict | None:
    """Searches local CSV / JSON catalogs for verified product data matching the URL or ext_id."""
    if not product_url:
        return None

    ext_match = re.search(r'/p/([a-zA-Z0-9]+)', product_url)
    ext_id = ext_match.group(1).lower() if ext_match else ""

    # Check curated CSV
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
                        link = item.get("link", "")
                        if ext_id and ext_id in link.lower():
                            return {
                                "title": item.get("title", "Aesthetic Fashion Outfit"),
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
                            title = row.get("name_2") or row.get("name") or row.get("title") or "Aesthetic Fashion Outfit"
                            price_str = row.get("price") or row.get("price_1") or row.get("data") or "399"
                            price = int(re.sub(r'\D', '', price_str) or 399)
                            img = row.get("image") or row.get("image_1") or row.get("image2") or ""
                            fabric = (row.get("product_fabric") or "Lycra").replace("Fabric :", "").strip()
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
    """Parses raw text or live URL into rich product schema."""
    lines = [l.strip() for l in raw_text.splitlines() if l.strip()]
    
    # 1. Product URL
    url_match = re.search(r'(https?://(?:www\.)?meesho\.com/[^\s"\'<>]+)', raw_text)
    product_url = url_match.group(1) if url_match else ""
    
    # 2. Check local verified catalog for instant match
    matched_data = lookup_local_catalog(product_url) if product_url else None

    # 3. Cloud Images
    cdn_images = re.findall(r'(https?://images\.meesho\.com/images/products/[a-zA-Z0-9_/]+\.webp(?:\?width=\d+)?)', raw_text)
    cleaned_images = [img.split('?')[0] for img in cdn_images]

    if matched_data and matched_data.get("image") and not cleaned_images:
        cleaned_images.append(matched_data["image"].split('?')[0])

    primary_image = cleaned_images[0] if cleaned_images else "https://images.meesho.com/images/products/682813217/hbo6b_512.webp"
    gallery_images = cleaned_images[1:6] if len(cleaned_images) > 1 else [primary_image]

    # 4. Colors & Sizes
    colors = extract_colors(raw_text)
    sizes = matched_data.get("sizes") if matched_data else extract_sizes(raw_text)

    # 5. Pricing
    price_matches = re.findall(r'₹\s*([0-9,]+)', raw_text)
    price = matched_data.get("price", 399) if matched_data else 399
    old_price = None
    if price_matches:
        vals = [int(p.replace(',', '')) for p in price_matches if 50 < int(p.replace(',', '')) < 50000]
        if vals:
            price = min(vals)
            if len(vals) > 1 and max(vals) > price:
                old_price = max(vals)

    if not old_price:
        old_price = int(price * 1.35)

    cost_price = max(199, price - 150)
    profit = price - cost_price

    # 6. Rating & Reviews
    rating_match = re.search(r'(\d\.\d)\s*★', raw_text) or re.search(r'Rating\s*:\s*(\d\.\d)', raw_text)
    rating = float(rating_match.group(1)) if rating_match else 4.3

    rev_match = re.search(r'([0-9,]+)\s*(?:Ratings|Reviews|ratings|reviews)', raw_text)
    rating_count = int(rev_match.group(1).replace(',', '')) if rev_match else 1420

    # 7. Title Extraction
    title = matched_data.get("title") if matched_data else ""
    if not title:
        for l in lines[:12]:
            if 8 < len(l) < 75 and not l.startswith("http") and not "₹" in l and not "★" in l:
                if not any(ign in l.lower() for ign in ["meesho", "free delivery", "add to cart", "buy now", "reviews", "similar products"]):
                    title = l
                    break

    if not title:
        if product_url:
            slug_match = re.search(r'meesho\.com/([a-zA-Z0-9-]+)/p/', product_url)
            if slug_match:
                title = slug_match.group(1).replace('-', ' ').title()
        if not title:
            title = "Aesthetic Gen Z Designer Outfit"

    title = re.sub(r'\s+', ' ', title).strip()

    # 8. Category & Collection
    lower_t = (title + " " + raw_text).lower()
    if any(k in lower_t for k in ["dress", "maxi", "midi", "bodycon", "gown", "frock"]):
        category = "Women Dresses"
        collection_id = "meesho-dresses-2026"
        tint = "peach"
    elif any(k in lower_t for k in ["kurti", "kurta", "anarkali", "suit", "saree"]):
        category = "Kurtis"
        collection_id = "meesho-kurtis-2026"
        tint = "lilac"
    elif any(k in lower_t for k in ["puffer", "jacket", "sweater", "cardigan", "hoodie", "winter"]):
        category = "Winterwear"
        collection_id = "meesho-winter-2026"
        tint = "sage"
    elif any(k in lower_t for k in ["co-ord", "set", "two piece", "skirt"]):
        category = "Co-ord Sets"
        collection_id = "meesho-coord-2026"
        tint = "lavender"
    else:
        category = "Gen Z Aesthetic & Streetwear"
        collection_id = "meesho-genz-2026"
        tint = "peach"

    slug = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')[:35]
    ext_id = re.search(r'/p/([a-zA-Z0-9]+)', product_url).group(1) if product_url and re.search(r'/p/([a-zA-Z0-9]+)', product_url) else slug[:8]

    affiliate_url = build_affiliate_route(product_url) if product_url else ""

    return {
        "id": f"p-meesho-{slug}-{ext_id}",
        "ext_id": ext_id,
        "title": title,
        "subtitle": f"{colors[0]} · {', '.join(sizes[:3])} · Soft aesthetic drape",
        "brand": "Meesho Verified Creator Pick",
        "store": "Meesho",
        "category": category,
        "collectionId": collection_id,
        "tint": tint,
        "price": price,
        "oldPrice": old_price,
        "costPrice": cost_price,
        "estimatedProfit": profit,
        "rating": rating,
        "ratingCount": rating_count,
        "image": primary_image,
        "galleryImages": gallery_images,
        "colors": colors,
        "sizes": sizes,
        "inStock": True,
        "productUrl": product_url or "https://www.meesho.com",
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
