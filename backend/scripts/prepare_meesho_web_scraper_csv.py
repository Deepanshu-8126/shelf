#!/usr/bin/env python3
"""Normalize a user-supplied Web Scraper export into shelf's import CSV.

This works only on the CSV file you provide. It does not fetch pages. For Meesho
product galleries it uses the row's image_4 field (the product-detail gallery),
not recommendation-image lists, and deduplicates resolution variants by path.
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from import_meesho_paste import classify, extract_ext_id, generate_link  # noqa: E402

FIELDS = [
    "title", "price", "old_price", "discount", "rating", "rating_count", "review_count",
    "category", "subcategories", "color", "fabric", "fit_shape", "length", "sizes",
    "sleeve_length", "pattern", "seller_name", "product_url", "ext_id", "image_url",
    "gallery_image_urls", "affiliate_url", "generated_affiliate_url", "link_status",
]
IMAGE_URL_RE = re.compile(r"https?://[^\s\"'<>]+", re.IGNORECASE)
COLORS = ("black", "pink", "white", "maroon", "red", "blue", "green", "yellow", "beige", "cream", "brown", "navy", "purple", "orange", "wine")
SIZE_RE = re.compile(r"\b(XXXL|XXL|XXS|XL|XS|S|M|L|FREE\s*SIZE|ONE\s*SIZE)\b", re.IGNORECASE)


def value(row: dict[str, str], *keys: str) -> str:
    for key in keys:
        item = str(row.get(key) or "").replace("\xa0", " ").strip()
        if item:
            return item
    return ""


def normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "").replace("\xa0", " ")).strip()


def image_urls(value_text: str) -> list[str]:
    urls: list[str] = []
    seen: set[str] = set()
    for raw in IMAGE_URL_RE.findall(value_text or ""):
        raw = raw.rstrip(",.;")
        try:
            parsed = urlsplit(raw)
        except ValueError:
            continue
        if (parsed.hostname or "").lower() != "images.meesho.com" or "/images/products/" not in parsed.path.lower():
            continue
        key = f"{parsed.scheme.lower()}://{(parsed.hostname or '').lower()}{parsed.path}"
        if key in seen:
            continue
        seen.add(key)
        urls.append(raw)
    return urls


def full_size_image(url: str) -> str:
    """Keep the supplied image file/path and request a clear 512px rendition."""
    parsed = urlsplit(url)
    query = [(key, val) for key, val in parse_qsl(parsed.query, keep_blank_values=True) if key.lower() != "width"]
    query.append(("width", "512"))
    return urlunsplit((parsed.scheme, parsed.netloc, parsed.path, urlencode(query), parsed.fragment))


def field_value(raw: str, label: str) -> str:
    text = normalize_space(raw)
    if ":" in text:
        before, after = text.split(":", 1)
        if label.lower() in before.lower():
            return after.strip()
    return ""


def parse_rating(row: dict[str, str]) -> tuple[str, str, str]:
    rating = normalize_space(value(row, "ratingValue"))
    raw = normalize_space(value(row, "reviewCount"))
    match = re.search(r"([\d,]+)\s+Ratings?\s*,?\s*([\d,]+)?\s*Reviews?", raw, re.IGNORECASE)
    rating_count = match.group(1).replace(",", "") if match else ""
    review_count = (match.group(2) or "").replace(",", "") if match else ""
    # Some supplied exports contain only the ratings count in this cell.
    if not match:
        count_only = re.search(r"([\d,]+)\s+Ratings?", raw, re.IGNORECASE)
        if count_only:
            rating_count = count_only.group(1).replace(",", "")
    if not re.fullmatch(r"[0-5](?:\.\d+)?", rating):
        rating = ""
    return rating, rating_count, review_count


def product_tags(title: str, row: dict[str, str]) -> tuple[str, str, str, str, str, str, str]:
    sleeve = field_value(value(row, "product_sleeve_length"), "Sleeve Length")
    pattern = field_value(value(row, "product_pattern"), "Pattern")
    fabric = field_value(value(row, "product_fabric"), "Fabric")
    description = value(row, "product_country_of_origin")
    searchable = " ".join((title, sleeve, pattern, fabric, description))
    _category, tags = classify(searchable)
    low = searchable.lower()
    if "a-line" in low or "a line" in low:
        tags.append("A-line")
    if re.search(r"\bfit\s*(?:and|&)\s*flare\b", low):
        tags.append("Fit & flare")
    if "flared" in low:
        tags.append("Flared")
    if "flower" in low and "floral" not in [tag.lower() for tag in tags]:
        tags.append("Floral")
    if "printed" in pattern.lower() or "printed" in title.lower():
        tags.append("Printed")
    if "solid" in pattern.lower():
        tags.append("Solid")
    if "three-quarter" in sleeve.lower() or "three quarter" in sleeve.lower():
        tags.append("Three-quarter sleeves")
    elif "short" in sleeve.lower():
        tags.append("Short sleeves")
    elif "sleeveless" in sleeve.lower():
        tags.append("Sleeveless")
    elif "long" in sleeve.lower() or "full" in sleeve.lower():
        tags.append("Full sleeves")
    tags = list(dict.fromkeys(tag for tag in tags if tag))

    fit = ""
    if "bodycon" in low:
        fit = "Bodycon"
    elif re.search(r"\bfit\s*(?:and|&)\s*flare\b", low):
        fit = "Fit & flare"
    elif "a-line" in low or "a line" in low:
        fit = "A-line"
    elif "flared" in low:
        fit = "Flared"

    length = "Maxi" if "maxi" in low else "Midi" if "midi" in low else "Calf-length" if "calf-length" in low else ""
    color = next((color.title() for color in COLORS if re.search(rf"\b{re.escape(color)}\b", low)), "")
    return " | ".join(tags), fabric, sleeve, fit, length, color, pattern


def build_record(row: dict[str, str]) -> dict[str, str] | None:
    product_url = value(row, "item_page_link", "product_url", "url", "link")
    ext_id = extract_ext_id(product_url).lower()
    if not product_url or not ext_id:
        return None
    title = normalize_space(value(row, "title_1", "name", "name_3", "title"))
    if not title:
        return None
    price = re.sub(r"[^\d.]", "", value(row, "price_1", "price", "data"))
    try:
        if float(price) <= 0:
            return None
    except ValueError:
        return None

    # image_4 is the scraped product-detail gallery. image_1/2/3 are related
    # product cards and image_5/6 are smaller duplicate renditions of the hero.
    primary = image_urls(value(row, "image"))
    detail_gallery = image_urls(value(row, "image_4"))
    candidates = primary + detail_gallery
    deduped: list[str] = []
    keys: set[str] = set()
    for url in candidates:
        parsed = urlsplit(url)
        key = f"{parsed.scheme.lower()}://{(parsed.hostname or '').lower()}{parsed.path}"
        if key in keys:
            continue
        keys.add(key)
        deduped.append(full_size_image(url))
    if not deduped:
        # Conservative fallback: only use another image column if it shares the
        # same Meesho image-product directory as the supplied hero.
        primary_group = re.search(r"/images/products/(\d+)/", primary[0]) if primary else None
        if primary_group:
            for column in ("image2", "image3"):
                for url in image_urls(value(row, column)):
                    if f"/images/products/{primary_group.group(1)}/" in url:
                        deduped.append(full_size_image(url))
    if not deduped:
        return None

    # The detail-page breadcrumb is the supplied source for the main category.
    breadcrumb = value(row, "name_1")
    category = "Women Dresses" if "women dresses" in breadcrumb.lower() else "Women Dresses"
    tags, fabric, sleeve, fit, length, color, pattern = product_tags(title, row)
    rating, rating_count, review_count = parse_rating(row)
    raw_sizes = value(row, "sizes_available")
    sizes = list(dict.fromkeys(match.group(1).upper().replace(" ", "") for match in SIZE_RE.finditer(raw_sizes)))

    existing_affiliate = value(row, "affiliate_url", "generated_affiliate_url")
    try:
        generated, link_status = generate_link(product_url, existing_affiliate)
    except ValueError:
        return None
    # The converter keeps a supplied creator route; otherwise it makes the exact
    # configured af_invite route for this product ID (default creator ID 374453404).
    affiliate_url = existing_affiliate if "/af_invite/" in existing_affiliate.lower() else generated

    return {
        "title": title,
        "price": price,
        "old_price": "",
        "discount": "",
        "rating": rating,
        "rating_count": rating_count,
        "review_count": review_count,
        "category": category,
        "subcategories": tags,
        "color": color,
        "fabric": fabric,
        "fit_shape": fit,
        "length": length,
        "sizes": " | ".join(sizes),
        "sleeve_length": sleeve,
        "pattern": pattern,
        "seller_name": normalize_space(value(row, "seller_name")),
        "product_url": product_url,
        "ext_id": ext_id,
        "image_url": deduped[0],
        "gallery_image_urls": "|".join(deduped[1:9]),
        "affiliate_url": affiliate_url,
        "generated_affiliate_url": affiliate_url,
        "link_status": "creator-link-preserved" if "/af_invite/" in existing_affiliate.lower() else link_status,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_csv", type=Path)
    parser.add_argument("output_csv", type=Path, nargs="?", help="default: <input>-shelf-ready.csv")
    args = parser.parse_args()
    source_path = args.input_csv if args.input_csv.is_absolute() else (ROOT / args.input_csv).resolve()
    output_path = args.output_csv or source_path.with_name(f"{source_path.stem}-shelf-ready.csv")
    if not output_path.is_absolute():
        output_path = (ROOT / output_path).resolve()
    try:
        with source_path.open("r", encoding="utf-8-sig", newline="") as source:
            raw_rows = list(csv.DictReader(source))
    except (OSError, csv.Error) as error:
        parser.error(str(error))

    records: list[dict[str, str]] = []
    seen_ids: set[str] = set()
    duplicates = 0
    missing = 0
    for raw in raw_rows:
        record = build_record(raw)
        if not record:
            missing += 1
            continue
        ext_id = record["ext_id"].lower()
        if ext_id in seen_ids:
            duplicates += 1
            continue
        seen_ids.add(ext_id)
        records.append(record)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8-sig", newline="") as destination:
        writer = csv.DictWriter(destination, fieldnames=FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(records)
    print(f"Wrote {output_path}: {len(records)} unique products, {duplicates} duplicate IDs skipped, {missing} incomplete rows skipped.")
    print(f"Each product uses its exact item_page_link ID; galleries are deduplicated within product and kept to 1 primary + up to 8 extras.")
    print(f"Generated affiliate links for {sum(row['link_status'] == 'generated-from-supplied-pattern' for row in records)} rows; preserved {sum(row['link_status'] == 'creator-link-preserved' for row in records)} existing creator links.")
    print("Affiliate redirects are not proof of commission attribution; verify test clicks/orders in Meesho Creator.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
