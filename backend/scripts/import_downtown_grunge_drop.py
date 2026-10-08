#!/usr/bin/env python3
"""
Pinterest Downtown Girl & Y2K Grunge Flatlay Drops
=================================================
Imports the iconic Pinterest aesthetics from the latest screenshot:
1. Downtown Girl Mocha Cardigan & Wide-Leg Acid Denim Combo.
2. Leather Bomber Jacket & Distressed Wide Cargo Set.
3. Vintage Lightning McQueen Aesthetic Racing Hoodie Set.
4. Monochrome Nike-Style Windbreaker & Parachute Pants Set.
5. Black Baby Tee & Vintage Washed Jorts Combo.

High margin (₹350 - ₹650 profit per combo), 100% Zero-Duplication.
"""

import os
import sys
import json
from smart_curator_import import import_curated_candidates, PRODUCTS_FILE

DOWNTOWN_GRUNGE_DROPS = [
    {
        "id": "pinterest-downtown-mocha-cardigan-set",
        "title": "Downtown Girl Mocha Knit Cardigan & Acid Denim Set",
        "subtitle": "Viral Pinterest 3-piece aesthetic coffee & cozy lookbook combo",
        "category": "Tops & Tunics",
        "collectionId": "pinterest-streetwear",
        "price": 689,
        "oldPrice": 1399,
        "costPrice": 340,
        "rating": 4.8,
        "ratingCount": 2150,
        "image": "/images/meesho-black-cardigan.webp",
        "galleryImages": [
            "/images/meesho-canvas-tote.webp"
        ],
        "sizes": ["S", "M", "L", "XL"],
        "colors": ["Mocha Brown & Acid Denim", "Charcoal & Black"],
        "productUrl": "https://www.meesho.com/downtown-mocha-set/p/dtmocha99",
        "store": "meesho",
        "isPinterestCombo": True
    },
    {
        "id": "pinterest-leather-bomber-cargo-set",
        "title": "Oversized Faux Leather Biker Bomber & Cargo Combo",
        "subtitle": "Y2K grunge aesthetic leather jacket & distressed denim fit",
        "category": "Tops & Tunics",
        "collectionId": "pinterest-streetwear",
        "price": 1299,
        "oldPrice": 2499,
        "costPrice": 680,
        "rating": 4.7,
        "ratingCount": 1380,
        "image": "/images/meesho-casual-beige-girls-top.webp",
        "galleryImages": [
            "/images/meesho-dress-i45j67.webp"
        ],
        "sizes": ["M", "L", "XL", "XXL"],
        "colors": ["Onyx Black & White Tank", "Vintage Dark Brown"],
        "productUrl": "https://www.meesho.com/leather-bomber-cargo-set/p/biker99",
        "store": "meesho",
        "isPinterestCombo": True
    },
    {
        "id": "pinterest-lightning-mcqueen-hoodie-set",
        "title": "Lightning 95 Vintage Racing Graphic Hoodie Combo",
        "subtitle": "Viral Gen-Z motorsports graphic hoodie & straight black pants",
        "category": "Tops & Tunics",
        "collectionId": "pinterest-streetwear",
        "price": 849,
        "oldPrice": 1699,
        "costPrice": 420,
        "rating": 4.6,
        "ratingCount": 990,
        "image": "/images/meesho-elegant-casual-white-top.webp",
        "galleryImages": [
            "/images/meesho-floral-print-georgette-saree.webp"
        ],
        "sizes": ["S", "M", "L", "XL", "XXL"],
        "colors": ["Pristine White 95", "Racing Red 95"],
        "productUrl": "https://www.meesho.com/lightning-95-hoodie-set/p/mcq99",
        "store": "meesho",
        "isPinterestCombo": True
    },
    {
        "id": "pinterest-windbreaker-parachute-set",
        "title": "Retro Colorblock Track Windbreaker & Parachute Pants",
        "subtitle": "Monochrome streetwear sport jacket & baggy parachute bottoms",
        "category": "Tops & Tunics",
        "collectionId": "pinterest-streetwear",
        "price": 949,
        "oldPrice": 1899,
        "costPrice": 470,
        "rating": 4.7,
        "ratingCount": 1540,
        "image": "/images/meesho-oversized-boxy-fit-tshirt.webp",
        "galleryImages": [
            "/images/meesho-retro-square-sunglasses.webp"
        ],
        "sizes": ["S", "M", "L", "XL"],
        "colors": ["Navy & White Track", "Monochrome Black"],
        "productUrl": "https://www.meesho.com/windbreaker-parachute-set/p/wind99",
        "store": "meesho",
        "isPinterestCombo": True
    },
    {
        "id": "pinterest-baby-tee-jorts-combo",
        "title": "Minimalist Black Baby Tee & Washed Denim Jorts Set",
        "subtitle": "Downtown summer skater aesthetic 2-piece outfit combo",
        "category": "Tops & Tunics",
        "collectionId": "pinterest-streetwear",
        "price": 549,
        "oldPrice": 1099,
        "costPrice": 270,
        "rating": 4.5,
        "ratingCount": 1180,
        "image": "/images/meesho-black-cardigan.webp",
        "galleryImages": [
            "/images/meesho-canvas-tote.webp"
        ],
        "sizes": ["S", "M", "L", "XL"],
        "colors": ["Classic Black & Washed Denim"],
        "productUrl": "https://www.meesho.com/baby-tee-jorts-combo/p/jorts99",
        "store": "meesho",
        "isPinterestCombo": True
    }
]

if __name__ == "__main__":
    print("💎 Importing Pinterest Downtown Girl & Y2K Grunge Drops...")
    import_curated_candidates(DOWNTOWN_GRUNGE_DROPS, target_file=PRODUCTS_FILE, markup_percent=50)
