#!/usr/bin/env python3
"""
Import Gen-Z Viral Blokecore & Retro Football Jerseys
=====================================================
Streetwear / Blokecore aesthetic drop featuring trending Brazil, Real Madrid Mbappe,
Barcelona Yamal, Argentina Messi, Portugal CR7 embroidered luxury kits.
Zero duplication guaranteed.
"""

import os
import sys
import json
from smart_curator_import import import_curated_candidates, PRODUCTS_FILE

JERSEY_CANDIDATES = [
    {
        "id": "jersey-brazil-neymar-10",
        "title": "Brazil 24/25 Neymar Jr #10 Iconic Home Jersey",
        "subtitle": "Blokecore viral oversized aesthetic fit",
        "category": "Tops & Tunics",
        "collectionId": "blokecore-jerseys",
        "price": 549,
        "oldPrice": 899,
        "costPrice": 473,
        "rating": 4.3,
        "ratingCount": 437,
        "image": "https://images.meesho.com/images/products/439777824/j7nzy_512.webp",
        "galleryImages": [
            "https://images.meesho.com/images/products/439777824/j7nzy_512.webp",
            "https://images.meesho.com/images/products/439777824/j7nzy_512.webp"
        ],
        "sizes": ["S", "M", "L", "XL", "XXL"],
        "colors": ["Canary Yellow", "Navy Blue"],
        "productUrl": "https://www.meesho.com/brazil-neymar-jr-10-iconic-yellow-home-edition-premium-football-jersey-samba-legend-match-style/p/fb84d8",
        "store": "meesho"
    },
    {
        "id": "jersey-realmadrid-mbappe-10",
        "title": "Mbappe #10 Real Madrid 24/25 3rd Kit Embroidery",
        "subtitle": "Premium dot-knit luxury streetwear jersey",
        "category": "Tops & Tunics",
        "collectionId": "blokecore-jerseys",
        "price": 529,
        "oldPrice": 849,
        "costPrice": 408,
        "rating": 4.4,
        "ratingCount": 619,
        "image": "https://images.meesho.com/images/products/447287948/kgnq9_512.webp",
        "galleryImages": [
            "https://images.meesho.com/images/products/447287948/kgnq9_512.webp"
        ],
        "sizes": ["S", "M", "L", "XL", "XXL"],
        "colors": ["Charcoal Grey", "Emerald Green"],
        "productUrl": "https://www.meesho.com/mbappe-10-real-madrid-2026-27-3rd-kit-embroidery/p/hoorf4",
        "store": "meesho"
    },
    {
        "id": "jersey-argentina-messi-10",
        "title": "Argentina Midnight Blue #10 Messi Phantom Edition",
        "subtitle": "Embroidered 3-star champions luxury kit",
        "category": "Tops & Tunics",
        "collectionId": "blokecore-jerseys",
        "price": 549,
        "oldPrice": 899,
        "costPrice": 464,
        "rating": 4.3,
        "ratingCount": 628,
        "image": "https://images.meesho.com/images/products/437340242/4f4qm_512.webp",
        "galleryImages": [
            "https://images.meesho.com/images/products/437340242/4f4qm_512.webp"
        ],
        "sizes": ["S", "M", "L", "XL", "XXL"],
        "colors": ["Midnight Blue", "Sky Blue Stripes"],
        "productUrl": "https://www.meesho.com/embroidery-argentina-midnight-blue-10-messi-phantom-edition-premium-football-jersey/p/f9k9l6",
        "store": "meesho"
    },
    {
        "id": "jersey-barca-yamal-10",
        "title": "FC Barcelona Lamine Yamal #10 Blaugrana Kit",
        "subtitle": "Gen-Z viral match-style streetwear jersey",
        "category": "Tops & Tunics",
        "collectionId": "blokecore-jerseys",
        "price": 539,
        "oldPrice": 849,
        "costPrice": 414,
        "rating": 4.4,
        "ratingCount": 221,
        "image": "https://images.meesho.com/images/products/435133645/e4j5t_512.webp",
        "galleryImages": [
            "https://images.meesho.com/images/products/435133645/e4j5t_512.webp"
        ],
        "sizes": ["S", "M", "L", "XL", "XXL"],
        "colors": ["Blaugrana", "Purple Black"],
        "productUrl": "https://www.meesho.com/fc-barcelona-home-jersey-lamine-yamal-10-blaugrana-match-style-football-t-shirt/p/b8jiod",
        "store": "meesho"
    },
    {
        "id": "jersey-portugal-ronaldo-7",
        "title": "Portugal CR7 Ice Wave Edition Football Jersey",
        "subtitle": "Embroidered crest & iconic #7 detailing",
        "category": "Tops & Tunics",
        "collectionId": "blokecore-jerseys",
        "price": 549,
        "oldPrice": 899,
        "costPrice": 464,
        "rating": 4.4,
        "ratingCount": 954,
        "image": "https://images.meesho.com/images/products/438348822/0n6f3_512.webp",
        "galleryImages": [
            "https://images.meesho.com/images/products/438348822/0n6f3_512.webp"
        ],
        "sizes": ["S", "M", "L", "XL", "XXL"],
        "colors": ["Ice Wave Teal", "Classic Maroon"],
        "productUrl": "https://www.meesho.com/embroidery-portugal-ronaldo-7-ice-wave-edition-premium-football-jersey/p/ffva6i",
        "store": "meesho"
    },
    {
        "id": "jersey-manchester-city-haaland-9",
        "title": "Manchester City Haaland #9 Sky Blue Jersey",
        "subtitle": "Embroidered crest & premium breathable fabric",
        "category": "Tops & Tunics",
        "collectionId": "blokecore-jerseys",
        "price": 549,
        "oldPrice": 899,
        "costPrice": 463,
        "rating": 4.4,
        "ratingCount": 445,
        "image": "https://images.meesho.com/images/products/446268801/zsz5a_512.webp",
        "galleryImages": [
            "https://images.meesho.com/images/products/446268801/zsz5a_512.webp"
        ],
        "sizes": ["S", "M", "L", "XL", "XXL"],
        "colors": ["Sky Blue", "Moon White"],
        "productUrl": "https://www.meesho.com/manchester-city-haaland-9-sky-blue-embroidered-jersey/p/ha4eb9",
        "store": "meesho"
    }
]

if __name__ == "__main__":
    print("🚀 Importing Viral Gen-Z Blokecore Jerseys...")
    import_curated_candidates(JERSEY_CANDIDATES, target_file=PRODUCTS_FILE, markup_percent=25)
