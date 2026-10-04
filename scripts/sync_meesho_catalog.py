#!/usr/bin/env python3
"""Sync Meesho catalog prices from a trusted, user-supplied CSV.

This script never requests or scrapes Meesho. Affiliate links identify a listing;
they are not a reliable price feed. Provide a current approved export/CSV before
building if you want prices refreshed.

Existing product update columns:
  product_url (or ext_id), price
Optional: old_price, clear_old_price, price_checked_at, affiliate_url.

A new listing can be upserted when the row also includes title, image (a local
/public image path that already exists), and category. Products are de-duplicated
by the Meesho ext_id parsed from the product URL, not by the card title.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
import sys
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlsplit

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover - older Python fallback
    ZoneInfo = None  # type: ignore[assignment,misc]

ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATHS = [ROOT / "src/meesho-products.json", ROOT / "src/meesho-dresses.json"]
PRICE_OVERRIDES_PATH = ROOT / "src/meesho-price-overrides.json"
CATALOG_CSV_PATH = ROOT / "scripts/meesho-products.csv"
LINKS_CSV_PATH = ROOT / "scripts/meesho-products-with-links.csv"
LINK_GENERATOR_PATH = ROOT / "scripts/generate_meesho_affiliate_links.py"
DEFAULT_UPDATES_PATH = ROOT / "scripts/meesho-price-updates.csv"
DEFAULT_FIELDS = [
    "id", "product_url", "affiliate_url", "price", "rating", "rating_count",
    "image_url", "category", "subtitle", "price_checked_at", "ext_id", "old_price",
]


def today_in_india() -> str:
    if ZoneInfo is not None:
        try:
            return datetime.now(ZoneInfo("Asia/Kolkata")).date().isoformat()
        except Exception:
            pass
    return date.today().isoformat()


def extract_ext_id(url: str) -> str:
    """Extract a Meesho product's stable ext_id from a product or invite URL."""
    value = (url or "").strip()
    if not value:
        return ""
    if not value.startswith(("https://", "http://")):
        value = "https://www.meesho.com/" + value.lstrip("/")
    parsed = urlsplit(value)
    host = (parsed.hostname or "").lower()
    if host != "meesho.com" and not host.endswith(".meesho.com"):
        return ""
    query_id = (parse_qs(parsed.query).get("ext_id") or [""])[0]
    if query_id:
        return query_id.strip().lower()
    short = re.fullmatch(r"/s/p/([^/]+)/?", parsed.path, re.IGNORECASE)
    if short:
        return short.group(1).strip().lower()
    match = re.search(r"/p/([^/]+)/?$", parsed.path, re.IGNORECASE)
    return match.group(1).strip().lower() if match else ""


def parse_money(value: Any, *, required: bool = False) -> int | float | None:
    text = str(value or "").strip().replace("₹", "").replace(",", "").replace(" ", "")
    if not text:
        if required:
            raise ValueError("price is required")
        return None
    try:
        amount = Decimal(text)
    except InvalidOperation as error:
        raise ValueError(f"invalid amount: {value!r}") from error
    if not amount.is_finite() or amount < 0 or (required and amount == 0):
        raise ValueError(f"amount must be {'greater than ' if required else ''}zero: {value!r}")
    if amount == amount.to_integral_value():
        return int(amount)
    return float(amount)


def parse_int(value: Any, field: str) -> int | None:
    text = str(value or "").strip().replace(",", "")
    if not text:
        return None
    try:
        result = int(text)
    except ValueError as error:
        raise ValueError(f"invalid {field}: {value!r}") from error
    if result < 0:
        raise ValueError(f"{field} cannot be negative")
    return result


def truthy(value: Any) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "y"}


def is_blank(value: Any) -> bool:
    return value is None or value == "" or value == [] or value == {}


def load_json_list(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError(f"Expected a JSON list in {path}")
    return data


def merge_duplicate(target: dict[str, Any], duplicate: dict[str, Any]) -> None:
    """Fill missing metadata, preferring the more recently checked price fields."""
    target_date = str(target.get("priceCheckedAt") or "")
    duplicate_date = str(duplicate.get("priceCheckedAt") or "")
    if duplicate_date and duplicate_date > target_date:
        for key in ("price", "oldPrice", "priceCheckedAt"):
            if key in duplicate:
                target[key] = duplicate[key]
    for key, value in duplicate.items():
        if key in {"price", "oldPrice", "priceCheckedAt"} and duplicate_date > target_date:
            continue
        if is_blank(target.get(key)) and not is_blank(value):
            target[key] = value
    if is_blank(target.get("affiliateUrl")) and not is_blank(duplicate.get("affiliateUrl")):
        target["affiliateUrl"] = duplicate["affiliateUrl"]


def dedupe_catalogs(catalogs: dict[Path, list[dict[str, Any]]]) -> tuple[int, dict[str, tuple[Path, dict[str, Any]]]]:
    by_ext_id: dict[str, tuple[Path, dict[str, Any]]] = {}
    duplicate_count = 0
    for path in CATALOG_PATHS:
        products = catalogs.setdefault(path, [])
        unique: list[dict[str, Any]] = []
        for product in products:
            ext_id = extract_ext_id(str(product.get("productUrl") or ""))
            if not ext_id or ext_id not in by_ext_id:
                unique.append(product)
                if ext_id:
                    by_ext_id[ext_id] = (path, product)
                continue
            target_path, target = by_ext_id[ext_id]
            merge_duplicate(target, product)
            duplicate_count += 1
            # If the duplicate was found later in a file already visited, its
            # original entry is removed there by the second pass below.
        catalogs[path] = unique
    # A duplicate can be in a later file but point to an earlier target; unique
    # above omits it from the current file. Re-index after all files are settled.
    return duplicate_count, by_ext_id


def load_catalogs() -> tuple[dict[Path, list[dict[str, Any]]], int, dict[str, tuple[Path, dict[str, Any]]]]:
    catalogs = {path: load_json_list(path) for path in CATALOG_PATHS}
    duplicate_count, _ = dedupe_catalogs(catalogs)
    index: dict[str, tuple[Path, dict[str, Any]]] = {}
    for path in CATALOG_PATHS:
        for product in catalogs[path]:
            ext_id = extract_ext_id(str(product.get("productUrl") or ""))
            if ext_id:
                index[ext_id] = (path, product)
    return catalogs, duplicate_count, index


def load_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    if not path.exists():
        return DEFAULT_FIELDS.copy(), []
    with path.open("r", encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        if not reader.fieldnames:
            return DEFAULT_FIELDS.copy(), []
        fields = list(reader.fieldnames)
        rows = [{key: (value or "") for key, value in row.items() if key is not None} for row in reader]
    for field in ("ext_id", "old_price", "subtitle"):
        if field not in fields:
            fields.append(field)
    return fields, rows


def row_ext_id(row: dict[str, Any]) -> str:
    explicit = str(row.get("ext_id") or row.get("product_id") or "").strip().lower()
    from_url = extract_ext_id(str(row.get("product_url") or ""))
    return explicit or from_url


def dedupe_csv_rows(rows: list[dict[str, str]]) -> tuple[list[dict[str, str]], int]:
    unique: list[dict[str, str]] = []
    indexes: dict[str, int] = {}
    duplicates = 0
    for row in rows:
        ext_id = row_ext_id(row)
        if not ext_id:
            unique.append(row)
            continue
        row["ext_id"] = ext_id
        if ext_id not in indexes:
            indexes[ext_id] = len(unique)
            unique.append(row)
            continue
        previous = unique[indexes[ext_id]]
        # Keep the newest price snapshot; fill any other empty fields from the duplicate.
        if str(row.get("price_checked_at") or "") >= str(previous.get("price_checked_at") or ""):
            for key in ("price", "old_price", "price_checked_at"):
                if row.get(key, "") != "":
                    previous[key] = row[key]
        for key, value in row.items():
            if value and not previous.get(key):
                previous[key] = value
        duplicates += 1
    return unique, duplicates


def current_old_price(product: dict[str, Any] | None, row: dict[str, str] | None) -> int | float | None:
    if product is not None:
        value = product.get("oldPrice")
        if value not in (None, ""):
            return parse_money(value)
    if row is not None:
        value = row.get("old_price") or row.get("oldPrice") or ""
        if value:
            return parse_money(value)
    return None


def local_image_path(value: str) -> str:
    path = value.strip()
    if path.startswith("public/"):
        path = "/" + path[len("public/"):]
    if not path.startswith("/"):
        path = "/" + path
    return path


def create_product_from_row(row: dict[str, str], ext_id: str, price: int | float, checked_at: str) -> tuple[Path, dict[str, Any]]:
    title = (row.get("title") or "").strip()
    category = (row.get("category") or "").strip()
    image = local_image_path(row.get("image") or row.get("image_path") or "")
    product_url = (row.get("product_url") or "").strip()
    if not all((title, category, product_url, image != "/")):
        raise ValueError(
            "new listing needs product_url, title, category, and image (an existing local /public image path)"
        )
    if "/af_invite/" in urlsplit(product_url).path.lower():
        raise ValueError("new listing product_url must be the public product page, not an af_invite route")
    image_file = ROOT / "public" / image.lstrip("/")
    if not image_file.is_file():
        raise ValueError(f"local product image does not exist: {image_file.relative_to(ROOT)}")
    if extract_ext_id(product_url) != ext_id:
        raise ValueError("product_url does not match ext_id")

    price_checked_at = (row.get("price_checked_at") or checked_at).strip()
    old_price = parse_money(row.get("old_price"))
    product_id = f"p-meesho-{ext_id}"
    collection_id = (row.get("collection_id") or "").strip()
    if not collection_id:
        category_key = category.lower()
        if category_key in {"women dresses", "dresses"}:
            collection_id = "meesho-dresses-2026"
        elif category_key == "kurtis":
            collection_id = "meesho-kurtis-2026"
        elif category_key == "tops & tunics":
            collection_id = "meesho-western-2026"
        elif category_key == "winter":
            collection_id = "winter-2026"
        else:
            collection_id = "everyday-style"

    product: dict[str, Any] = {
        "id": product_id,
        "title": title,
        "subtitle": (row.get("subtitle") or "").strip(),
        "brand": (row.get("brand") or "Meesho listing").strip(),
        "store": "Meesho",
        "category": category,
        "collectionId": collection_id,
        "image": image,
        "imagePosition": (row.get("image_position") or "50% 38%").strip(),
        "imageFit": "cover",
        "tint": (row.get("tint") or "peach").strip(),
        "price": price,
        "oldPrice": old_price,
        "clicks": 0,
        "commission": "",
        "saved": False,
        "affiliateUrl": (row.get("affiliate_url") or "").strip(),
        "productUrl": product_url,
        "isRealListing": True,
        "priceCheckedAt": price_checked_at,
        "priceSyncManaged": True,
    }
    rating_text = (row.get("rating") or "").strip()
    rating_count = parse_int(row.get("rating_count"), "rating_count")
    if rating_text:
        try:
            rating = float(rating_text)
        except ValueError as error:
            raise ValueError(f"invalid rating: {rating_text!r}") from error
        if rating < 0 or rating > 5:
            raise ValueError("rating must be between 0 and 5")
        product["rating"] = rating
    if rating_count is not None:
        product["ratingCount"] = rating_count
    target_path = CATALOG_PATHS[1] if category.lower() in {"women dresses", "dresses"} else CATALOG_PATHS[0]
    return target_path, product


def update_catalog_product(
    product: dict[str, Any],
    row: dict[str, str],
    ext_id: str,
    price: int | float,
    old_price: int | float | None,
    checked_at: str,
) -> None:
    product["price"] = price
    product["oldPrice"] = old_price
    product["priceCheckedAt"] = checked_at
    product["priceSyncManaged"] = True
    new_url = (row.get("product_url") or "").strip()
    if new_url:
        if extract_ext_id(new_url) != ext_id:
            raise ValueError("product_url does not match the resolved ext_id")
        product["productUrl"] = new_url
    new_affiliate = (row.get("affiliate_url") or "").strip()
    if new_affiliate:
        product["affiliateUrl"] = new_affiliate
    new_category = (row.get("category") or "").strip()
    if new_category:
        product["category"] = new_category
    new_subtitle = (row.get("subtitle") or "").strip()
    if new_subtitle:
        product["subtitle"] = new_subtitle
    collection_id = (row.get("collection_id") or "").strip()
    if collection_id:
        product["collectionId"] = collection_id


def update_csv_row(
    csv_row: dict[str, str], row: dict[str, str], ext_id: str,
    price: int | float, old_price: int | float | None, checked_at: str,
) -> None:
    csv_row["ext_id"] = ext_id
    csv_row["price"] = str(price)
    csv_row["old_price"] = "" if old_price is None else str(old_price)
    csv_row["price_checked_at"] = checked_at
    if row.get("product_url", "").strip():
        csv_row["product_url"] = row["product_url"].strip()
    if row.get("affiliate_url", "").strip():
        csv_row["affiliate_url"] = row["affiliate_url"].strip()
    if row.get("title", "").strip() and not csv_row.get("title"):
        csv_row["title"] = row["title"].strip()
    if row.get("category", "").strip():
        csv_row["category"] = row["category"].strip()
    if row.get("subtitle", "").strip():
        csv_row["subtitle"] = row["subtitle"].strip()
    if row.get("image_url", "").strip() and not csv_row.get("image_url"): 
        csv_row["image_url"] = row["image_url"].strip()


def sync_csv_from_catalog(
    rows: list[dict[str, str]], fields: list[str], index: dict[str, tuple[Path, dict[str, Any]]]
) -> list[dict[str, str]]:
    by_id = {row_ext_id(row): row for row in rows if row_ext_id(row)}
    for ext_id, (_path, product) in index.items():
        row = by_id.get(ext_id)
        if row is None:
            row = {field: "" for field in fields}
            row["ext_id"] = ext_id
            rows.append(row)
            by_id[ext_id] = row
        row["ext_id"] = ext_id
        mapping = {
            "id": product.get("id", ""),
            "title": product.get("title", ""),
            "product_url": product.get("productUrl", ""),
            "price": product.get("price", ""),
            "old_price": product.get("oldPrice") or "",
            "category": product.get("category", ""),
            "subtitle": product.get("subtitle", ""),
            "price_checked_at": product.get("priceCheckedAt", ""),
            "affiliate_url": product.get("affiliateUrl", ""),
        }
        if "rating" in product:
            mapping["rating"] = product["rating"]
        else:
            mapping["rating"] = ""
        if "ratingCount" in product:
            mapping["rating_count"] = product["ratingCount"]
        else:
            mapping["rating_count"] = ""
        for key, value in mapping.items():
            # Existing custom affiliate URLs are preserved if the JSON seed is blank.
            if key == "affiliate_url" and not value and row.get(key):
                continue
            row[key] = "" if value is None else str(value)
        if not row.get("image_url"):
            row["image_url"] = str(product.get("imageUrl") or product.get("image") or "")
    return rows


def write_json_atomic(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(path.suffix + ".tmp")
    temp_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp_path.replace(path)


def write_csv_atomic(path: Path, fields: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(path.suffix + ".tmp")
    with temp_path.open("w", encoding="utf-8", newline="") as destination:
        writer = csv.DictWriter(destination, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    temp_path.replace(path)


def load_price_updates(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        if not reader.fieldnames:
            return []
        fields = set(reader.fieldnames)
        if "price" not in fields:
            raise ValueError("price update CSV must include a 'price' column")
        if not ({"product_url", "ext_id", "product_id"} & fields):
            raise ValueError("price update CSV must include 'product_url' or 'ext_id'")
        return [{key: (value or "") for key, value in row.items() if key is not None} for row in reader]


def dedupe_updates(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    merged: dict[str, dict[str, str]] = {}
    order: list[str] = []
    for row in rows:
        if not any(str(value or "").strip() for value in row.values()):
            continue
        ext_id = row_ext_id(row)
        if not ext_id:
            raise ValueError("each non-empty update row needs a valid Meesho product_url or ext_id")
        if row.get("product_url", "").strip():
            parsed_id = extract_ext_id(row["product_url"])
            if parsed_id and parsed_id != ext_id:
                raise ValueError(f"product_url and ext_id disagree for {ext_id}")
        if ext_id not in merged:
            merged[ext_id] = dict(row)
            order.append(ext_id)
        else:
            prior = merged[ext_id]
            # Last row wins for current price; non-empty optional metadata is retained.
            for key, value in row.items():
                if str(value or "").strip():
                    prior[key] = value
    return [merged[ext_id] for ext_id in order]


def load_overrides() -> dict[str, dict[str, Any]]:
    if not PRICE_OVERRIDES_PATH.exists():
        return {}
    value = json.loads(PRICE_OVERRIDES_PATH.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object in {PRICE_OVERRIDES_PATH}")
    return {str(key).lower(): item for key, item in value.items() if isinstance(item, dict)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input", "-i", type=Path, default=DEFAULT_UPDATES_PATH,
        help="approved price-update CSV (default: scripts/meesho-price-updates.csv)",
    )
    parser.add_argument("--dry-run", action="store_true", help="validate and report without writing files")
    parser.add_argument("--require-feed", action="store_true", help="fail if the price-update CSV is missing")
    args = parser.parse_args()
    updates_path = args.input if args.input.is_absolute() else (ROOT / args.input).resolve()

    try:
        catalogs, json_duplicates, catalog_index = load_catalogs()
        fields, csv_rows = load_csv(CATALOG_CSV_PATH)
        if "ext_id" not in fields:
            fields.append("ext_id")
        if "old_price" not in fields:
            fields.append("old_price")
        csv_rows, csv_duplicates = dedupe_csv_rows(csv_rows)
        csv_index = {row_ext_id(row): row for row in csv_rows if row_ext_id(row)}
        overrides = load_overrides()
        updates: list[dict[str, str]] = []
        if updates_path.exists():
            updates = dedupe_updates(load_price_updates(updates_path))
        elif args.require_feed:
            parser.error(f"No approved price CSV found: {updates_path}")
        else:
            print(f"No price update CSV found at {updates_path}; prices will remain unchanged.")

        update_count = 0
        errors: list[str] = []
        checked_at_default = today_in_india()
        for row in updates:
            ext_id = row_ext_id(row)
            try:
                price = parse_money(row.get("price"), required=True)
                if price is None:
                    raise ValueError("price is required")
                checked_at = (row.get("price_checked_at") or checked_at_default).strip()
                catalog_entry = catalog_index.get(ext_id)
                csv_row = csv_index.get(ext_id)
                product = catalog_entry[1] if catalog_entry else None

                if product is None and csv_row is None:
                    target_path, product = create_product_from_row(row, ext_id, price, checked_at)
                    catalogs.setdefault(target_path, []).append(product)
                    catalog_index[ext_id] = (target_path, product)
                    fields.extend(field for field in ("id", "title", "product_url", "affiliate_url", "rating", "rating_count", "image_url", "category", "price_checked_at") if field not in fields)
                    csv_row = {field: "" for field in fields}
                    csv_row.update({
                        "id": product["id"],
                        "ext_id": ext_id,
                        "title": product["title"],
                        "product_url": product["productUrl"],
                        "affiliate_url": product.get("affiliateUrl", ""),
                        "price": str(price),
                        "old_price": "" if product.get("oldPrice") is None else str(product["oldPrice"]),
                        "rating": str(product.get("rating", "")),
                        "rating_count": str(product.get("ratingCount", "")),
                        "image_url": row.get("image_url") or product["image"],
                        "category": product["category"],
                        "price_checked_at": checked_at,
                    })
                    csv_rows.append(csv_row)
                    csv_index[ext_id] = csv_row
                elif product is None:
                    if row.get("product_url", "").strip() and extract_ext_id(row["product_url"]) != ext_id:
                        raise ValueError("product_url does not match the resolved ext_id")
                    if row.get("product_url", "").strip():
                        csv_row["product_url"] = row["product_url"].strip()
                    new_affiliate = row.get("affiliate_url", "").strip()
                    if new_affiliate:
                        csv_row["affiliate_url"] = new_affiliate
                else:
                    prior_old = current_old_price(product, csv_row)
                    if str(row.get("old_price") or "").strip():
                        prior_old = parse_money(row.get("old_price"))
                    elif truthy(row.get("clear_old_price")):
                        prior_old = None
                    update_catalog_product(product, row, ext_id, price, prior_old, checked_at)
                    if catalog_entry:
                        catalog_entry[1].update(product)
                    if csv_row is None:
                        csv_row = {field: "" for field in fields}
                        csv_index[ext_id] = csv_row
                        csv_rows.append(csv_row)

                if csv_row is None:
                    csv_row = {field: "" for field in fields}
                    csv_rows.append(csv_row)
                    csv_index[ext_id] = csv_row
                old_price_value = current_old_price(product, csv_row)
                if str(row.get("old_price") or "").strip():
                    old_price_value = parse_money(row.get("old_price"))
                elif truthy(row.get("clear_old_price")):
                    old_price_value = None
                update_csv_row(csv_row, row, ext_id, price, old_price_value, checked_at)

                overrides[ext_id] = {
                    "price": price,
                    "oldPrice": old_price_value,
                    "priceCheckedAt": checked_at,
                }
                affiliate_override = (
                    row.get("affiliate_url", "").strip()
                    or (str(product.get("affiliateUrl") or "").strip() if product is not None else "")
                    or str(csv_row.get("affiliate_url") or "").strip()
                )
                if affiliate_override:
                    overrides[ext_id]["affiliateUrl"] = affiliate_override
                if row.get("category", "").strip():
                    overrides[ext_id]["category"] = row["category"].strip()
                if row.get("subtitle", "").strip():
                    overrides[ext_id]["subtitle"] = row["subtitle"].strip()
                if product is not None:
                    product["price"] = price
                    product["oldPrice"] = old_price_value
                    product["priceCheckedAt"] = checked_at
                    product["priceSyncManaged"] = True
                update_count += 1
            except (ValueError, InvalidOperation) as error:
                errors.append(f"{ext_id}: {error}")

        if errors:
            print("Price sync cancelled; fix these rows first:", file=sys.stderr)
            for error in errors:
                print(f"  - {error}", file=sys.stderr)
            return 1

        csv_rows = sync_csv_from_catalog(csv_rows, fields, catalog_index)
        csv_rows, final_csv_duplicates = dedupe_csv_rows(csv_rows)
        final_index = {row_ext_id(row): row for row in csv_rows if row_ext_id(row)}
        for row in csv_rows:
            if row_ext_id(row):
                row["ext_id"] = row_ext_id(row)
        # Keep the original image references for catalog CSV rows when available.
        if args.dry_run:
            print(
                f"Dry run OK: {len(updates)} price rows, {len(catalog_index)} catalog JSON products, "
                f"{len(final_index)} unique CSV IDs; {json_duplicates} JSON and "
                f"{csv_duplicates + final_csv_duplicates} CSV duplicates would be removed."
            )
            return 0

        for path in CATALOG_PATHS:
            write_json_atomic(path, catalogs.get(path, []))
        write_json_atomic(PRICE_OVERRIDES_PATH, overrides)
        write_csv_atomic(CATALOG_CSV_PATH, fields, csv_rows)
        subprocess.run(
            [sys.executable, str(LINK_GENERATOR_PATH), str(CATALOG_CSV_PATH), str(LINKS_CSV_PATH)],
            cwd=ROOT,
            check=True,
        )
        print(
            f"Meesho sync complete: {update_count} prices refreshed, {len(catalog_index)} imported JSON products, "
            f"{len(final_index)} unique Meesho IDs in CSV. Removed {json_duplicates} JSON and "
            f"{csv_duplicates + final_csv_duplicates} duplicate CSV rows."
        )
        if not updates:
            print("No live price lookup was performed; prices change only when a trusted CSV/feed is supplied.")
        return 0
    except (OSError, json.JSONDecodeError, csv.Error, ValueError, subprocess.CalledProcessError) as error:
        print(f"Meesho sync failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
