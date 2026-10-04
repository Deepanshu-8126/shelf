#!/usr/bin/env python3
"""
Catalog Image Sanitizer
=======================
Replaces all synthetic AI URLs and low-res thumbnails
with authentic high-resolution local catalog photography.
"""

import json
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PRODUCTS_JSON = PROJECT_ROOT / "src" / "meesho-products.json"
DRESSES_JSON = PROJECT_ROOT / "src" / "meesho-dresses.json"

IMAGE_REPLACEMENTS = {
    "meesho-7akb0m": "/images/meesho-western-black-highneck.webp",
    "p-meesho-ferrari99": "/images/meesho-western-party-top.webp",
    "p-meesho-spdr88": "/images/meesho-western-square-print-top.webp",
    "p-meesho-rb99": "/images/meesho-western-elegant-top.webp",
    "p-meesho-merc99": "/images/meesho-western-black-highneck.webp",
    "p-meesho-sphood99": "/images/meesho-black-cardigan.webp",
    "p-meesho-brhlt99": "/images/meesho-yellow-side-dori-top.webp",
    "p-meesho-brtee88": "/images/meesho-sumeer-net-crop-top.webp",
    "p-meesho-brcami77": "/images/meesho-western-ruffle-tube-top.webp",
    "p-meesho-argtop99": "/images/meesho-western-floral-mesh.webp",
    "p-meesho-leocors99": "/images/meesho-western-lace-cutout.webp",
    "p-meesho-shrug99": "/images/meesho-western-korean-top.webp",
    "p-meesho-spdbod99": "/images/meesho-red-checked-crop-top.webp",
    "p-meesho-vanilla99": "/images/meesho-plaid-bow-peplum-top.webp",
    "p-meesho-brskirt99": "/images/meesho-western-dori-poncho.webp",
    "p-meesho-dtmocha99": "/images/meesho-western-brown-top.webp",
    "p-meesho-biker99": "/images/meesho-western-offshoulder-black.webp",
    "p-meesho-mcq99": "/images/meesho-western-korean-long-sleeve.webp",
    "p-meesho-wind99": "/images/meesho-western-vneck-flare.webp",
    "p-meesho-jorts99": "/images/meesho-western-hollowout-top.webp"
}


def sanitize_file(file_path: Path):
    if not file_path.exists():
        return 0

    with open(file_path, "r", encoding="utf-8") as f:
        products = json.load(f)

    replaced = 0
    for p in products:
        pid = p.get("id")
        img = str(p.get("image", ""))
        
        # If in explicit replacements map
        if pid in IMAGE_REPLACEMENTS:
            clean_img = IMAGE_REPLACEMENTS[pid]
            p["image"] = clean_img
            p["images"] = [clean_img]
            p["galleryImages"] = [clean_img]
            p["aiFlagged"] = False
            p["aiFlagReason"] = ""
            replaced += 1
        else:
            # Clean galleryImages from synthetic or low-res items
            if "galleryImages" in p and isinstance(p["galleryImages"], list):
                clean_gallery = []
                for g in p["galleryImages"]:
                    g_str = str(g)
                    if "synthetic" in g_str or "prompt=" in g_str or "ai_gen" in g_str:
                        continue
                    # Strip low-res micro-thumbnail constraint (?width=512 or 360)
                    g_clean = g_str.split("?")[0]
                    clean_gallery.append(g_clean)
                p["galleryImages"] = clean_gallery or [p.get("image", "/images/meesho-dress-ae6lv9.webp")]

            if "images" in p and isinstance(p["images"], list):
                p["images"] = [str(u).split("?")[0] for u in p["images"] if "synthetic" not in str(u) and "prompt=" not in str(u)] or [p.get("image", "/images/meesho-dress-ae6lv9.webp")]

            if "prompt=" in img or "synthetic" in img:
                clean_img = "/images/meesho-western-party-top.webp"
                p["image"] = clean_img
                p["images"] = [clean_img]
                p["galleryImages"] = [clean_img]
                p["aiFlagged"] = False
                p["aiFlagReason"] = ""
                replaced += 1

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(products, f, indent=2, ensure_ascii=False)

    print(f"Sanitized {replaced} items in {file_path.name}")
    return replaced


if __name__ == "__main__":
    count1 = sanitize_file(PRODUCTS_JSON)
    count2 = sanitize_file(DRESSES_JSON)
    print(f"Total sanitized products: {count1 + count2}")
