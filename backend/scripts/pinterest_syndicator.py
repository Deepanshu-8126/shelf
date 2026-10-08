#!/usr/bin/env python3
"""
Pinterest Viral Traffic Auto-Syndicator & API Engine (Official Pinterest CSV Schema)
==================================================================================
Formats CSV with official Pinterest Bulk Upload headers:
- Title
- Media URL
- Pinterest board
- Description
- Link
- Publish date
- Keywords
"""

import os
import sys
import json
import csv
from datetime import datetime

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRODUCTS_FILE = os.path.join(PROJECT_ROOT, "src", "meesho-products.json")
OUTPUT_PINS_CSV = os.path.join(PROJECT_ROOT, "pinterest_viral_pins.csv")
OUTPUT_PINS_JSON = os.path.join(PROJECT_ROOT, "scripts", "generated_pinterest_pins.json")

# Niche-calibrated viral hooks & hashtags
NICHE_PROFILES = {
    "navratri": {
        "board": "Navratri & Garba Outfits",
        "hook": "🔥 Navratri 2026: The viral garba fit that stops the scroll! ✨",
        "tags": ["Navratri 2026", "Garba Outfit", "Mirror Work Kurti", "Desi Aesthetic", "Festive Finds"]
    },
    "diwali": {
        "board": "Diwali & Wedding Glam",
        "hook": "✨ Royal Velvet & Cowl Glam for Festive Nights. Pure main-character energy.",
        "tags": ["Diwali Outfit", "Velvet Dress", "Festive Lookbook", "Party Wear", "Aesthetic Indian"]
    },
    "brasilcore": {
        "board": "Brasilcore & Y2K Fashion",
        "hook": "🇧🇷 That viral Pinterest Y2K Baby Tee you've been looking everywhere for.",
        "tags": ["Brasilcore", "Y2K Baby Tee", "Streetwear India", "Pinterest Outfit", "Aesthetic Tees"]
    },
    "racing": {
        "board": "Vintage F1 & Streetwear",
        "hook": "🏎️ Heavyweight Vintage F1 Racing Bomber. Instant outfit upgrade.",
        "tags": ["F1 Jacket", "Racing Bomber", "Streetwear Style", "Oversized Fit", "Vintage Lookbook"]
    },
    "winter": {
        "board": "Winter Cold-Girl Aesthetic",
        "hook": "❄️ Cold-girl era loading: Cozy cropped layers & soft knits under ₹999.",
        "tags": ["Winter Outfit", "Puffer Jacket", "Cold Girl Aesthetic", "Knitwear", "Aesthetic Winter"]
    },
    "default": {
        "board": "Aesthetic Fashion Curations",
        "hook": "✨ Effortless chic dailywear pick. Super comfortable and budget-friendly.",
        "tags": ["OOTD", "Aesthetic Fashion", "Gen Z Style", "Fashion Finds", "Pinterest Inspo"]
    }
}

def detect_niche(product):
    title = (product.get("title") or "").lower()
    cid = (product.get("collectionId") or "").lower()
    category = (product.get("category") or "").lower()
    
    if any(k in title or k in cid for k in ["navratri", "garba", "anarkali", "saree", "kurti"]):
        return "navratri"
    if any(k in title or k in cid for k in ["diwali", "wedding", "velvet", "satin", "cowl", "glam"]):
        return "diwali"
    if any(k in title or k in cid for k in ["brasil", "baby tee", "y2k", "chrome"]):
        return "brasilcore"
    if any(k in title or k in cid for k in ["racing", "f1", "bomber", "jersey", "blokecore"]):
        return "racing"
    if any(k in title or k in cid or k in category for k in ["winter", "puffer", "sweater", "cardigan", "knit"]):
        return "winter"
    return "default"

def generate_pinterest_feed():
    if not os.path.exists(PRODUCTS_FILE):
        print("Products catalog not found.")
        return []

    with open(PRODUCTS_FILE, "r", encoding="utf-8") as f:
        products = json.load(f)

    pins_csv = []
    pins_json = []

    today_date = datetime.now().strftime("%Y-%m-%d")

    for prod in products:
        title = (prod.get("title") or "Aesthetic Lookbook Pick").strip()
        price = prod.get("price", 399)
        category = prod.get("category", "Tops & Tunics")
        img_url = prod.get("image") or prod.get("aiEnhancedImage") or ""
        
        # Absolute image URL requirement for Pinterest
        if not img_url or img_url.startswith("/"):
            img_url = "https://images.meesho.com/images/products/542355935/8yqj09_512.webp"
            
        dest_url = prod.get("affiliateUrl") or prod.get("productUrl") or "https://www.meesho.com"
        
        niche_key = detect_niche(prod)
        niche_data = NICHE_PROFILES[niche_key]
        
        pin_title = f"{title} | Under ₹{price}"[:100]
        pin_description = f"{niche_data['hook']} Shop this exact look on shelf: {dest_url}"[:500]
        board_name = niche_data["board"]
        keywords = ", ".join(niche_data["tags"])
        
        # Exact official Pinterest Bulk Upload Column Names
        pin_obj = {
            "Title": pin_title,
            "Media URL": img_url,
            "Pinterest board": board_name,
            "Description": pin_description,
            "Link": dest_url,
            "Publish date": today_date,
            "Keywords": keywords
        }
        pins_csv.append(pin_obj)
        pins_json.append(pin_obj)

    # Write Official Pinterest Bulk Upload CSV
    fieldnames = ["Title", "Media URL", "Pinterest board", "Description", "Link", "Publish date", "Keywords"]
    with open(OUTPUT_PINS_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(pins_csv)

    # Write JSON cache
    with open(OUTPUT_PINS_JSON, "w", encoding="utf-8") as f:
        json.dump(pins_json, f, indent=2)

    print(f"✓ Generated {len(pins_csv)} pins matching 100% Pinterest official header schema.")
    print(f"✓ Saved to {os.path.basename(OUTPUT_PINS_CSV)}")
    return pins_json

if __name__ == "__main__":
    generate_pinterest_feed()
