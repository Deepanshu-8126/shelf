#!/usr/bin/env python3
"""
Pinterest & Instagram Organic Growth Automation Engine
======================================================
Transforms curated catalog items into viral, high-ranking Pinterest Pins
and Instagram Reel hooks/captions with deep-links to your shelf. storefront.

Zero ad spend — 100% organic fashion traffic.
"""

import os
import sys
import json
from datetime import datetime

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRODUCTS_FILE = os.path.join(PROJECT_ROOT, "src", "meesho-products.json")
DRESSES_FILE = os.path.join(PROJECT_ROOT, "src", "meesho-dresses.json")
OUTPUT_PINS_FILE = os.path.join(PROJECT_ROOT, "scripts", "generated_pinterest_pins.json")

# Aesthetic Pinterest Trend Matrix & High-CTR Copy Formulas
TREND_AESTHETICS = {
    "Dresses": {
        "vibe": "Clean Girl & Main Character Energy",
        "pin_titles": [
            "Zara / Savana Dupe Under ₹499 | {title}",
            "Pinterest Aesthetic Outfit Inspo: {title}",
            "The Viral Bodycon You Need in Your Wardrobe | Free Delivery",
            "Effortless Date Night Look under ₹500 | {title}"
        ],
        "tags": ["#pinterestfashion", "#savanafinds", "#zaradupes", "#cleangirlaesthetic", "#outfitinspo", "#affordablefashionindia", "#bodycondress"]
    },
    "Tops": {
        "vibe": "Y2K, Coquette & Blokecore Trend",
        "pin_titles": [
            "Savana Style Y2K Top Under ₹399 | {title}",
            "Blokecore Aesthetic Fit Inspo: {title}",
            "Gen-Z Summer Top Drop | {title}",
            "Affordable Pinterest Wardrobe Finds | {title}"
        ],
        "tags": ["#blokecore", "#y2kaesthetic", "#pinteresttops", "#coquettecore", "#trendyfits", "#indianfashionblogger"]
    },
    "Kurtis": {
        "vibe": "Desi Aesthetic & Modern Ethnic",
        "pin_titles": [
            "Modern Desi Aesthetic Kurti Under ₹499 | {title}",
            "College / Office Kurti Inspo | {title}",
            "Effortless Everyday Ethnic Edit | {title}"
        ],
        "tags": ["#desiaesthetic", "#kurtilove", "#ethnicwearinspo", "#collegewear", "#indianstreetfashion"]
    }
}

def generate_pinterest_feed(base_store_url="https://shelf-store.vercel.app/?view=storefront"):
    print("\n📌 Generating High-Converting Pinterest & Instagram Organic Campaign...")
    
    all_products = []
    for fpath in [DRESSES_FILE, PRODUCTS_FILE]:
        if os.path.exists(fpath):
            with open(fpath, "r", encoding="utf-8") as f:
                all_products.extend(json.load(f))

    generated_pins = []

    for item in all_products:
        pid = item.get("id")
        title = item.get("title") or "Aesthetic Fashion Pick"
        price = item.get("price") or 450
        img = item.get("image")
        category = item.get("category") or "Women Dresses"
        
        # Categorize vibe
        if "dress" in category.lower() or "dress" in title.lower():
            preset = TREND_AESTHETICS["Dresses"]
        elif "kurti" in category.lower():
            preset = TREND_AESTHETICS["Kurtis"]
        else:
            preset = TREND_AESTHETICS["Tops"]

        pin_title = preset["pin_titles"][hash(pid) % len(preset["pin_titles"])].format(title=title)
        
        destination_url = f"{base_store_url}&product={pid}"
        
        pin_payload = {
            "productId": pid,
            "pinTitle": pin_title,
            "board": "Pinterest Aesthetic Outfits 2026",
            "priceTag": f"₹{price}",
            "imageMediaUrl": img,
            "destinationLink": destination_url,
            "vibeCategory": preset["vibe"],
            "description": (
                f"✨ {title} — {preset['vibe']}. Get the exact luxury editorial look at wholesale price (₹{price}). "
                f"Free Express Doorstep Delivery & 7-Day Hassle-Free Exchange across India! "
                f"Tap the link to order now via Cash on Delivery (COD)."
            ),
            "hashtags": " ".join(preset["tags"]),
            "instagramReelHook": f"Stop paying ₹2,500 on Savana/Zara for this look! Found the exact piece for only ₹{price} ✨ Link in bio!",
            "createdAt": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        generated_pins.append(pin_payload)

    with open(OUTPUT_PINS_FILE, "w", encoding="utf-8") as f:
        json.dump(generated_pins, f, indent=2)

    print(f"✓ Successfully synthesized {len(generated_pins)} Pinterest Pins & Instagram Reel Hooks.")
    print(f"✓ Saved to {os.path.basename(OUTPUT_PINS_FILE)}")
    
    # Print sample top pin
    if generated_pins:
        sample = generated_pins[0]
        print("\n🔥 Sample Generated Viral Pin:")
        print(f"   📌 Title: {sample['pinTitle']}")
        print(f"   🔗 Deep Link: {sample['destinationLink']}")
        print(f"   📸 Image: {sample['imageMediaUrl']}")
        print(f"   💬 Reel Hook: {sample['instagramReelHook']}")
        print(f"   🏷️ Hashtags: {sample['hashtags']}")
    print("=======================================================\n")
    return generated_pins

if __name__ == "__main__":
    generate_pinterest_feed()
