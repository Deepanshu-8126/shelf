#!/usr/bin/env python3
"""
Smart 1-Click Meesho Paste Importer (Cloud CDN & Auto-Affiliate)
===============================================================
Takes raw copied text (Ctrl+A -> Ctrl+C) or raw URL from any Meesho page:
1. Automatically parses Title, Price, Discount, Sizes, Rating, and Review count.
2. Extracts High-Res Meesho Cloud CDN Image URLs (0 bytes downloaded locally).
3. Automatically attaches Creator Affiliate ID (374453404) & Campaign ID (12492338).
4. Categorizes into correct collection (Tops & Tunics, Women Dresses, Kurtis, Winterwear).
5. Upserts directly into src/meesho-products.json without breaking schema.
"""

import os
import sys
import re
import json
import urllib.parse
from datetime import datetime

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

AFFILIATE_CREATOR_ID = "374453404"
CAMPAIGN_ID = "12492338"
SOURCE_PARAM = "youtube_long_form"

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRODUCTS_JSON_PATH = os.path.join(PROJECT_ROOT, "src", "meesho-products.json")
DRESSES_JSON_PATH = os.path.join(PROJECT_ROOT, "src", "meesho-dresses.json")

def build_affiliate_url(product_url: str) -> str:
    """Generates the official Meesho Creator af_invite redirect route."""
    if not product_url:
        return ""
    # Extract ext_id (e.g. /p/8yqj09 -> 8yqj09)
    ext_match = re.search(r'/p/([a-zA-Z0-9]+)', product_url)
    ext_id = ext_match.group(1) if ext_match else "product"
    
    # Extract p_id if present
    pid_match = re.search(r'p_id=(\d+)', product_url)
    p_id = pid_match.group(1) if pid_match else "542355935"
    
    encoded_url = urllib.parse.quote(product_url, safe='')
    return f"https://www.meesho.com/af_invite/{AFFILIATE_CREATOR_ID}:{SOURCE_PARAM}:{CAMPAIGN_ID}?p_id={p_id}&ext_id={ext_id}&utm_source={SOURCE_PARAM}&url={encoded_url}"

def categorize_product(title: str, subtitle: str = ""):
    """Intelligently detects the collection and category for Gen Z curation."""
    text = (title + " " + subtitle).lower()
    
    if any(k in text for k in ["dress", "gown", "midi", "maxi", "bodycon", "frock"]):
        return "Women Dresses", "meesho-dresses-2026", "peach"
    elif any(k in text for k in ["kurti", "kurta", "anarkali", "ethnic"]):
        return "Kurtis", "meesho-kurtis-2026", "lilac"
    elif any(k in text for k in ["puffer", "jacket", "vest", "sweater", "cardigan", "hoodie", "winter"]):
        return "Winterwear", "meesho-winter-2026", "sage"
    else:
        return "Tops & Tunics", "meesho-western-2026", "peach"

def parse_pasted_content(raw_text: str):
    """Extracts structured product data from raw copied Meesho page text."""
    lines = [l.strip() for l in raw_text.splitlines() if l.strip()]
    
    # 1. Extract Product URL
    url_match = re.search(r'(https?://(?:www\.)?meesho\.com/[^\s]+)', raw_text)
    product_url = url_match.group(1) if url_match else ""
    
    # 2. Extract Cloud CDN Images
    images = re.findall(r'(https?://images\.meesho\.com/images/products/[^\s"\')]+)', raw_text)
    primary_image = images[0] if images else ""
    
    # 3. Extract Price
    price_matches = re.findall(r'₹\s*([0-9,]+)', raw_text)
    price = 399
    old_price = None
    if price_matches:
        prices = [int(p.replace(',', '')) for p in price_matches]
        price = min(prices)
        if len(prices) > 1 and max(prices) > price:
            old_price = max(prices)
            
    # 4. Extract Rating & Review Count
    rating_match = re.search(r'(\d\.\d)\s*★', raw_text) or re.search(r'Rating\s*:\s*(\d\.\d)', raw_text)
    rating = float(rating_match.group(1)) if rating_match else 4.3
    
    review_match = re.search(r'([0-9,]+)\s*(?:Ratings|Reviews|ratings|reviews)', raw_text)
    rating_count = int(review_match.group(1).replace(',', '')) if review_match else 1250
    
    # 5. Extract Title
    title = "Trendy Gen Z Aesthetic Fashion"
    for line in lines[:10]:
        if not line.startswith("http") and not line.startswith("₹") and not "★" in line and len(line) > 10 and len(line) < 80:
            if not any(ign in line.lower() for ign in ["meesho", "free delivery", "add to cart", "buy now", "reviews"]):
                title = line
                break
                
    # 6. Extract Fabric / Subtitle
    subtitle = "Premium fabric · Soft breathable · Modern fit"
    for line in lines:
        if any(f in line.lower() for f in ["cotton", "rayon", "polyester", "georgette", "lycra", "crepe", "satin"]):
            subtitle = line[:50]
            break

    category, collection_id, tint = categorize_product(title, subtitle)
    slug = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')[:35]
    
    # Fallback image if no CDN URL in text: Use default curated CDN template
    if not primary_image:
        primary_image = "https://images.meesho.com/images/products/542355935/8yqj09_512.webp"

    product_item = {
        "id": f"p-meesho-{slug}",
        "title": title,
        "subtitle": subtitle,
        "brand": "Meesho listing",
        "store": "Meesho",
        "category": category,
        "collectionId": collection_id,
        "image": primary_image,  # 100% Cloud CDN URL (0 MB on local disk)
        "imagePosition": "50% 40%",
        "imageFit": "cover",
        "tint": tint,
        "price": price,
        "oldPrice": old_price,
        "clicks": 0,
        "commission": "",
        "saved": False,
        "affiliateUrl": build_affiliate_url(product_url),
        "productUrl": product_url,
        "isRealListing": True,
        "rating": rating,
        "ratingCount": rating_count,
        "priceCheckedAt": datetime.now().strftime("%Y-%m-%d")
    }
    return product_item

def save_to_catalog(product_data: dict):
    """Inserts or updates product in meesho-products.json catalog."""
    target_file = PRODUCTS_JSON_PATH
    if "dress" in product_data["category"].lower() and os.path.exists(DRESSES_JSON_PATH):
        target_file = DRESSES_JSON_PATH

    products = []
    if os.path.exists(target_file):
        with open(target_file, "r", encoding="utf-8") as f:
            try:
                products = json.load(f)
            except Exception:
                products = []

    # Check for existing product by productUrl or ID
    existing_idx = next((i for i, p in enumerate(products) if p.get("productUrl") == product_data["productUrl"] or p.get("id") == product_data["id"]), None)
    
    if existing_idx is not None:
        products[existing_idx].update(product_data)
        print(f"✅ Updated existing product: {product_data['title']} (Price: ₹{product_data['price']})")
    else:
        products.insert(0, product_data)
        print(f"✨ Added NEW product: {product_data['title']} (Price: ₹{product_data['price']}, Cloud CDN Image linked)")

    with open(target_file, "w", encoding="utf-8") as f:
        json.dump(products, f, indent=2)
    print(f"💾 Catalog saved to {os.path.basename(target_file)} (Total: {len(products)} products)")

if __name__ == "__main__":
    import sys
    print("📋 Smart Meesho Paste Importer ready.")
    print("Paste raw copied text from Meesho below and press Enter (or Ctrl+Z then Enter on Windows):")
    
    content = sys.stdin.read()
    if content.strip():
        parsed = parse_pasted_content(content)
        save_to_catalog(parsed)
    else:
        print("No content received.")
