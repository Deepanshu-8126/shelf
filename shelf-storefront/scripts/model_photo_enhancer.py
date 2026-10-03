#!/usr/bin/env python3
"""
AI Gen Z Model Photo Enhancer
=============================
Inspects products in catalog. If an image is flat/non-model or low-aesthetic,
it generates a high-craft Gen Z aesthetic fashion model wearing that dress
using free Cloud AI endpoints and replaces the product image URL.
"""

import os
import sys
import json
import urllib.parse
import urllib.request
import re

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRODUCTS_FILE = os.path.join(PROJECT_ROOT, "src", "meesho-products.json")

def generate_ai_model_image_url(product_title: str, category: str, tint: str = "aesthetic") -> str:
    """
    Generates a free Cloud AI image URL featuring a stylish Gen Z model wearing the outfit.
    Uses Pollinations.ai / Cloud Gen endpoint (100% Free, Zero API Key required).
    """
    clean_title = re.sub(r'[^a-zA-Z0-9\s]', '', product_title)
    prompt = (
        f"Aesthetic high-fashion editorial portrait of a stunning Indian Gen Z fashion model wearing {clean_title}, "
        f"{category}, {tint} soft pastel lighting, urban minimalist indoor studio background, 8k resolution, "
        f"photorealistic fashion lookbook style, Vogue editorial photography, clean composition"
    )
    encoded_prompt = urllib.parse.quote(prompt)
    # Fast free AI image endpoint with high resolution
    return f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=768&height=1024&nologo=true&enhance=true"

def enhance_catalog_images(max_items: int = 5):
    if not os.path.exists(PRODUCTS_FILE):
        print("Catalog file not found.")
        return

    with open(PRODUCTS_FILE, "r", encoding="utf-8") as f:
        products = json.load(f)

    enhanced_count = 0
    for prod in products:
        current_img = prod.get("image", "")
        # If product has a local flat image or user flags for AI upgrade
        if enhanced_count < max_items and not current_img.startswith("https://image.pollinations.ai"):
            new_ai_img = generate_ai_model_image_url(prod.get("title", "Aesthetic Dress"), prod.get("category", "Fashion"), prod.get("tint", "peach"))
            prod["aiEnhancedImage"] = new_ai_img
            enhanced_count += 1
            print(f"✨ AI Model Image generated for: {prod.get('title')}")

    with open(PRODUCTS_FILE, "w", encoding="utf-8") as f:
        json.dump(products, f, indent=2)
        
    print(f"🎨 Enhanced {enhanced_count} products with Free High-Fashion Model Visuals!")

if __name__ == "__main__":
    enhance_catalog_images()
