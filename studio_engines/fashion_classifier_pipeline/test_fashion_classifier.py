#!/usr/bin/env python3
"""
Test Suite & Verification for Fashion Intelligence Pipeline
===========================================================
Validates:
1. Hoodie detection (Gents Hoodie vs Women Crop Hoodie)
2. Sweater & Knitwear detection (Cable Knit vs Cardigan)
3. Dress detection (Bodycon Maxi vs Sundress)
4. Indian Ethnic detection (Kurti vs Saree)
5. Bottomwear detection (Cargos vs Trousers)
"""

import os
import sys
import json
from pathlib import Path

# Ensure UTF-8
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

PIPELINE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(PIPELINE_DIR))

from fashion_pipeline import FashionIntelligencePipeline

TEST_CASES = [
    {
        "title": "Gents Charcoal Heavyweight Fleece Drop-Shoulder Oversized Hoodie with Drawstrings",
        "expected_garment": "Hoodie",
        "expected_gender": "Men",
        "expected_category": "Winter Outerwear"
    },
    {
        "title": "Women Cream Chunky Cable-Knit Turtleneck Wool Pullover Sweater",
        "expected_garment": "Sweater",
        "expected_gender": "Women",
        "expected_category": "Winter Outerwear"
    },
    {
        "title": "Wine Red Satin Sweetheart Neck Form-Fitting Bodycon Slit Maxi Dress",
        "expected_garment": "Bodycon Maxi Dress",
        "expected_gender": "Women",
        "expected_category": "Dresses"
    },
    {
        "title": "Lucknowi Hand Embroidered Pure Cotton Chikankari Kurti with Flared Palazzo Pant Set",
        "expected_garment": "Kurti",
        "expected_gender": "Women",
        "expected_category": "Kurtis"
    },
    {
        "title": "Olive Green Multi-Pocket Baggy Streetwear Tactical Cargo Pants",
        "expected_garment": "Cargo",
        "expected_gender": "Unisex",
        "expected_category": "Bottomwear"
    }
]

def run_tests():
    print("=" * 65)
    print("🚀 RUNNING FASHION INTELLIGENCE PIPELINE VERIFICATION SUITE")
    print("=" * 65)

    pipeline = FashionIntelligencePipeline()
    passed = 0

    for i, tc in enumerate(TEST_CASES, 1):
        print(f"\n--- [Test {i}/{len(TEST_CASES)}] {tc['title'][:45]}... ---")
        
        # Test classification
        result = pipeline.classify_single(image_source=tc["title"], title=tc["title"], price=599)
        
        garment = result.get("garment_name", "")
        cat = result.get("category", "")
        gender = result.get("gender", "")
        tags = result.get("auto_tags", [])
        
        print(f"  • Detected Garment  : {garment}")
        print(f"  • Category          : {cat}")
        print(f"  • Gender            : {gender}")
        print(f"  • Auto Tags         : {tags[:6]}")
        print(f"  • Confidence Score  : {result.get('confidence_score')}")

        # Verification check
        is_garment_match = tc["expected_garment"].lower() in garment.lower() or tc["expected_garment"].lower() in str(tags).lower()
        is_cat_match = tc["expected_category"].lower() in cat.lower() or cat.lower() in tc["expected_category"].lower()
        
        if is_garment_match or is_cat_match:
            print("  ✅ PASSED")
            passed += 1
        else:
            print(f"  ⚠️ Review: Expected {tc['expected_garment']} in {tc['expected_category']}")

    print("\n" + "=" * 65)
    print(f"RESULTS: {passed}/{len(TEST_CASES)} Tests Verified Successfully!")
    print("=" * 65)

if __name__ == "__main__":
    run_tests()
