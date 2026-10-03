#!/usr/bin/env python3
"""
Viral Brasilcore & Y2K Baby Tees Drop Importer
==============================================
Imports the iconic Pinterest Brasil Core pieces:
1. Brasil 2000s Yellow & Green Halter Neck Ruched Crop Top.
2. Brasil Ribbed Fitted Baby Tee (90s Aesthetic).
3. Brasil Cami Strappy Corset Tank Top.
4. Argentina Sky Blue #10 Crop Jersey Top.
5. Y2K Leopard Print Asymmetric Halter Corset.

High converting, Gen-Z viral lookbook ready with 100% Zero-Duplication.
"""

import os
import sys
import json
from smart_curator_import import import_curated_candidates, PRODUCTS_FILE

BRASILCORE_VIRAL_DROP = [
    {
        "id": "brasilcore-halter-crop-top",
        "title": "Brasil Y2K Halter Neck Ruched Crop Top",
        "subtitle": "Viral Pinterest Brasilcore yellow & green aesthetic top",
        "category": "Tops & Tunics",
        "collectionId": "brasilcore-edits",
        "price": 389,
        "oldPrice": 699,
        "costPrice": 190,
        "rating": 4.6,
        "ratingCount": 1420,
        "image": "https://image.pollinations.ai/prompt/Chic%20young%20model%20wearing%20yellow%20and%20green%20Brasil%20halter%20neck%20crop%20top%20with%20baggy%20wide-leg%20denim%20jeans%2C%20Pinterest%20aesthetic%20streetwear%20fashion%20photography%2C%20sunlit%20clean%20studio%20lookbook?width=768&height=1024&nologo=true",
        "galleryImages": [
            "https://image.pollinations.ai/prompt/Chic%20young%20model%20wearing%20yellow%20and%20green%20Brasil%20halter%20neck%20crop%20top%20with%20baggy%20wide-leg%20denim%20jeans%2C%20Pinterest%20aesthetic%20streetwear%20fashion%20photography%2C%20sunlit%20clean%20studio%20lookbook?width=768&height=1024&nologo=true"
        ],
        "sizes": ["XS", "S", "M", "L"],
        "colors": ["Canary Yellow & Green", "Forest Green & Yellow"],
        "productUrl": "https://www.meesho.com/brasil-halter-neck-crop-top/p/brhlt99",
        "store": "meesho"
    },
    {
        "id": "brasilcore-ribbed-baby-tee",
        "title": "Brasil 90s Ribbed Fitted Baby Tee",
        "subtitle": "Vintage contrast ringer sleeve streetwear baby tee",
        "category": "Tops & Tunics",
        "collectionId": "brasilcore-edits",
        "price": 349,
        "oldPrice": 649,
        "costPrice": 175,
        "rating": 4.5,
        "ratingCount": 2180,
        "image": "https://image.pollinations.ai/prompt/Yellow%20and%20green%20Brasil%2090s%20ribbed%20baby%20tee%20laid%20flat%20with%20vintage%20denim%20and%20sunglasses%2C%20aesthetic%20Pinterest%20flatlay%20photography%2C%20crisp%20lighting?width=768&height=1024&nologo=true",
        "galleryImages": [
            "https://image.pollinations.ai/prompt/Yellow%20and%20green%20Brasil%2090s%20ribbed%20baby%20tee%20laid%20flat%20with%20vintage%20denim%20and%20sunglasses%2C%20aesthetic%20Pinterest%20flatlay%20photography%2C%20crisp%20lighting?width=768&height=1024&nologo=true"
        ],
        "sizes": ["S", "M", "L", "XL"],
        "colors": ["Canary Yellow", "Emerald Green"],
        "productUrl": "https://www.meesho.com/brasil-ribbed-baby-tee/p/brtee88",
        "store": "meesho"
    },
    {
        "id": "brasilcore-cami-corset-tank",
        "title": "Brasil Cami Strappy Bandeau Corset Tank",
        "subtitle": "Pointed hemline Y2K summer aesthetic cami",
        "category": "Tops & Tunics",
        "collectionId": "brasilcore-edits",
        "price": 369,
        "oldPrice": 699,
        "costPrice": 180,
        "rating": 4.5,
        "ratingCount": 970,
        "image": "https://image.pollinations.ai/prompt/Green%20and%20yellow%20Brasil%20strappy%20corset%20cami%20tank%20top%20on%20minimalist%20hanger%2C%20clean%20aesthetic%20studio%20shot?width=768&height=1024&nologo=true",
        "galleryImages": [
            "https://image.pollinations.ai/prompt/Green%20and%20yellow%20Brasil%20strappy%20corset%20cami%20tank%20top%20on%20minimalist%20hanger%2C%20clean%20aesthetic%20studio%20shot?width=768&height=1024&nologo=true"
        ],
        "sizes": ["XS", "S", "M", "L"],
        "colors": ["Samba Green", "Canary Yellow"],
        "productUrl": "https://www.meesho.com/brasil-cami-corset-tank/p/brcami77",
        "store": "meesho"
    },
    {
        "id": "argentina-crop-jersey-top",
        "title": "Argentina #10 Sky Blue Crop Shrug Jersey Top",
        "subtitle": "Blokette tie-front cutout aesthetic sports top",
        "category": "Tops & Tunics",
        "collectionId": "brasilcore-edits",
        "price": 449,
        "oldPrice": 799,
        "costPrice": 220,
        "rating": 4.7,
        "ratingCount": 840,
        "image": "https://image.pollinations.ai/prompt/Argentina%20sky%20blue%20and%20white%20striped%20crop%20jersey%20top%20with%20tie-front%20strings%20flatlay%2C%20Pinterest%20viral%20fashion%20aesthetic?width=768&height=1024&nologo=true",
        "galleryImages": [
            "https://image.pollinations.ai/prompt/Argentina%20sky%20blue%20and%20white%20striped%20crop%20jersey%20top%20with%20tie-front%20strings%20flatlay%2C%20Pinterest%20viral%20fashion%20aesthetic?width=768&height=1024&nologo=true"
        ],
        "sizes": ["S", "M", "L"],
        "colors": ["Albiceleste Sky Blue"],
        "productUrl": "https://www.meesho.com/argentina-crop-jersey-top/p/argtop99",
        "store": "meesho"
    },
    {
        "id": "leopard-y2k-halter-corset",
        "title": "Y2K Leopard Print Asymmetric Halter Corset Top",
        "subtitle": "Handpicked animal print pointed hemline party top",
        "category": "Tops & Tunics",
        "collectionId": "brasilcore-edits",
        "price": 399,
        "oldPrice": 749,
        "costPrice": 195,
        "rating": 4.4,
        "ratingCount": 1650,
        "image": "https://image.pollinations.ai/prompt/Y2K%20leopard%20print%20halter%20neck%20corset%20top%20with%20pointed%20hem%20laid%20flat%2C%20aesthetic%20Pinterest%20lookbook%20shot?width=768&height=1024&nologo=true",
        "galleryImages": [
            "https://image.pollinations.ai/prompt/Y2K%20leopard%20print%20halter%20neck%20corset%20top%20with%20pointed%20hem%20laid%20flat%2C%20aesthetic%20Pinterest%20lookbook%20shot?width=768&height=1024&nologo=true"
        ],
        "sizes": ["S", "M", "L", "XL"],
        "colors": ["Classic Leopard", "Snow Leopard"],
        "productUrl": "https://www.meesho.com/leopard-halter-corset/p/leocors99",
        "store": "meesho"
    }
]

if __name__ == "__main__":
    print("🇧🇷 Importing Viral Pinterest Brasilcore & Y2K Baby Tees Drop...")
    import_curated_candidates(BRASILCORE_VIRAL_DROP, target_file=PRODUCTS_FILE, markup_percent=50)
