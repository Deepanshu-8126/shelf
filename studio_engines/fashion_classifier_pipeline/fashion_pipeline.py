#!/usr/bin/env python3
"""
Fashion Intelligence Pipeline & Auto-Tagger
===========================================
Integrates:
- Gemini Multimodal Vision AI
- 300+ Item Kaggle & Atlas Fashion Taxonomy
- Indian Festivals & Gen Z Aesthetics
- Batch CSV Enrichment & Real-Time Classification
"""

import os
import sys
import csv
import json
import argparse
from pathlib import Path
from typing import Any, Dict, List, Optional

# Ensure UTF-8 output
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

PIPELINE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(PIPELINE_DIR))

from gemini_vision_classifier import GeminiVisionClassifier

AFFILIATE_CREATOR_ID = "374453404"
CAMPAIGN_ID = "12492338"
SOURCE_PARAM = "youtube_long_form"

def generate_verified_affiliate_url(raw_url: str) -> str:
    if not raw_url:
        return ""
    import re
    from urllib.parse import quote
    ext_match = re.search(r"/p/([a-zA-Z0-9]+)", raw_url)
    ext_id = ext_match.group(1) if ext_match else "item"
    pid_match = re.search(r"p_id=(\d+)", raw_url)
    p_id = pid_match.group(1) if pid_match else "542355935"
    encoded = quote(raw_url)
    return f"https://www.meesho.com/af_invite/{AFFILIATE_CREATOR_ID}:{SOURCE_PARAM}:{CAMPAIGN_ID}?p_id={p_id}&ext_id={ext_id}&utm_source={SOURCE_PARAM}&url={encoded}"


class FashionIntelligencePipeline:
    def __init__(self, api_key: Optional[str] = None):
        self.classifier = GeminiVisionClassifier(api_key=api_key)
        self.taxonomy = self._load_taxonomy()

    def _load_taxonomy(self) -> Dict[str, Any]:
        tax_path = PIPELINE_DIR / "fashion_taxonomy.json"
        if tax_path.exists():
            with open(tax_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def classify_single(self, image_source: Any, title: str = "", price: Optional[float] = None) -> Dict[str, Any]:
        """Classifies one product image or listing."""
        result = self.classifier.classify_image(image_source, additional_context=title)
        
        # Enrich with pricing guidelines if price is known
        if price:
            result["price"] = float(price)
            result["wholesale_cost"] = max(149, int(price - 100))
            result["estimated_profit"] = max(80, int(price * 0.35))
        
        # Build clean tags array
        tags = []
        if result.get("category"):
            tags.append(result["category"].lower())
        if result.get("gender"):
            tags.append(result["gender"].lower())
        if result.get("silhouette_fit"):
            tags.append(result["silhouette_fit"].lower())
        if result.get("fabric"):
            tags.append(result["fabric"].lower())
        if result.get("aesthetic"):
            tags.append(result["aesthetic"].lower())
        if result.get("is_hoodie"):
            tags.extend(["hoodie", "sweatshirt", "winter"])
        if result.get("is_sweater"):
            tags.extend(["sweater", "knitwear", "winter"])

        result["auto_tags"] = list(set(tags))
        return result

    def process_csv(self, input_csv_path: str, output_csv_path: str, limit: int = 50) -> Dict[str, Any]:
        """
        Reads an input product CSV, runs multimodal classification on each row's image and title,
        and saves an enriched CSV with standardized categories, exact garment types, and tags.
        """
        inp = Path(input_csv_path)
        out = Path(output_csv_path)

        if not inp.exists():
            raise FileNotFoundError(f"Input CSV not found: {inp}")

        rows = []
        with open(inp, "r", encoding="utf-8", errors="ignore") as f:
            reader = csv.DictReader(f)
            fieldnames = list(reader.fieldnames or [])
            for row in reader:
                rows.append(row)

        print(f"\n[FashionPipeline] Loaded {len(rows)} products from {inp.name} (Processing up to {limit})...")
        
        # Ensure enriched fields exist in output
        new_fields = ["ai_garment_type", "ai_category", "ai_gender", "ai_fabric", "ai_tags", "verified_affiliate_url"]
        for nf in new_fields:
            if nf not in fieldnames:
                fieldnames.append(nf)

        processed_rows = []
        for idx, row in enumerate(rows[:limit]):
            title = (
                row.get("title", "") or
                row.get("product_title", "") or
                row.get("name", "") or
                row.get("notes", "") or
                row.get("description", "")
            ).strip()
            
            img_url = (
                row.get("image", "") or
                row.get("image_url", "") or
                row.get("primary_image", "") or
                row.get("img", "")
            ).strip()
            
            raw_url = (
                row.get("productUrl", "") or
                row.get("url", "") or
                row.get("link", "") or
                row.get("product_url", "")
            ).strip()

            # If title is still missing, infer from URL slug
            if not title and raw_url:
                import urllib.parse
                clean_u = urllib.parse.unquote(raw_url)
                m_slug = re.search(r"meesho\.com/([^/?#]+)/p/", clean_u)
                if m_slug:
                    title = m_slug.group(1).replace("-", " ").title()
                elif "q=" in clean_u:
                    m_q = re.search(r"q=([^&#]+)", clean_u)
                    if m_q:
                        title = m_q.group(1).replace("+", " ").title()

            price_val = 0.0
            for pk in ["price", "discountedPrice", "finalPrice", "cost"]:
                if row.get(pk):
                    try:
                        price_val = float(re.sub(r"[^\d.]", "", str(row[pk])))
                        break
                    except Exception:
                        pass

            display_name = title or img_url or "Item"
            print(f"[{idx+1}/{min(len(rows), limit)}] Analyzing: {display_name[:45]}...")
            
            # Analyze image with Gemini Vision (or title context)
            analysis = self.classify_single(img_url or title, title=title, price=price_val)
            
            row["ai_garment_type"] = analysis.get("garment_name", "Curated Fashion")
            row["ai_category"] = analysis.get("category", "Tops & Tunics")
            row["ai_gender"] = analysis.get("gender", "Women")
            row["ai_fabric"] = analysis.get("fabric", "Cotton")
            row["ai_tags"] = ", ".join(analysis.get("auto_tags", []))
            
            # Ensure verified affiliate URL
            if raw_url and not row.get("affiliateUrl"):
                row["verified_affiliate_url"] = generate_verified_affiliate_url(raw_url)
            else:
                row["verified_affiliate_url"] = row.get("affiliateUrl", "")

            processed_rows.append(row)

        # Write output CSV
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(processed_rows)

        print(f"[FashionPipeline] Finished! Enriched dataset saved to: {out}")
        return {
            "total_processed": len(processed_rows),
            "output_file": str(out)
        }


def main():
    parser = argparse.ArgumentParser(description="Fashion Intelligence Classification Pipeline")
    parser.add_argument("--image", type=str, help="Image URL or local file path to classify")
    parser.add_argument("--title", type=str, default="", help="Optional title or context")
    parser.add_argument("--csv", type=str, help="Input CSV path for batch enrichment")
    parser.add_argument("--out", type=str, default="enriched_fashion_catalog.csv", help="Output CSV path")
    parser.add_argument("--limit", type=int, default=25, help="Batch limit")

    args = parser.parse_args()
    pipeline = FashionIntelligencePipeline()

    if args.image:
        print(f"\n[CLI] Classifying Image: {args.image}...")
        res = pipeline.classify_single(args.image, title=args.title)
        print("\n=== CLASSIFICATION RESULT ===")
        print(json.dumps(res, indent=2, ensure_ascii=False))

    elif args.csv:
        pipeline.process_csv(args.csv, args.out, limit=args.limit)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
