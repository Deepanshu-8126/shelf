#!/usr/bin/env python3
"""Turn pasted Meesho listing text into a categorized review/import file.

This script only parses content you paste or provide in files. It does not crawl
Meesho pages. Product links/IDs are required to identify a listing and generate
its af_invite route; a title and price alone are not enough.

Quick start:
  python3 scripts/import_meesho_paste.py
  # paste copied page text, finish with Ctrl+D (Linux/macOS) or Ctrl+Z then Enter (Windows)

For a page-copy that omits links/images, supply one product URL and (for new
products) one Meesho image-CDN URL per extracted item in --links-file and
--images-file, in the same order as the listing cards. Then add --apply to
upsert matched prices/products into the app catalog.
"""
from __future__ import annotations

import argparse
import csv
import re
import subprocess
import sys
import tempfile
from collections import OrderedDict
from datetime import date, datetime
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen
from urllib.parse import parse_qs, urlsplit

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover - older Python fallback
    ZoneInfo = None  # type: ignore[assignment,misc]

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "scripts"
DEFAULT_OUTPUT = SCRIPT_DIR / "meesho-paste-review.csv"
CATALOG_CSV = SCRIPT_DIR / "meesho-products.csv"
SYNC_SCRIPT = SCRIPT_DIR / "sync_meesho_catalog.py"

sys.path.insert(0, str(SCRIPT_DIR))
from generate_meesho_affiliate_links import generate_link  # noqa: E402

RAW_URL_RE = re.compile(r"https?://[^\s<>\"'()]+", re.IGNORECASE)
IMAGE_URL_RE = re.compile(r"https?://images\.meesho\.com/[^\s<>\"']+", re.IGNORECASE)
PRICE_BLOCK_RE = re.compile(
    r"₹\s*(?P<price>[\d,]+)"
    r"(?:\s+₹\s*(?P<old_price>[\d,]+))?"
    r"(?:\s+(?P<discount>\d+(?:\.\d+)?\s*%\s*off))?"
    r"(?:\s*(?P<rating>[0-5](?:\.\d+)?)\s*Star\s*(?P<rating_count>[\d,]+)\s*Reviews?)?",
    re.IGNORECASE,
)
DETAIL_PAGE_MARKER_RE = re.compile(
    r"(?i)\b(?:Select\s+Size|Product\s+Highlights|Product\s+Ratings\s*(?:&(?:amp;)?\s*)?Reviews|Sold\s+By)\b"
)
RELATED_SECTION_RE = re.compile(r"(?im)^\s*people\s+also\s+viewed\s*$")
OUTPUT_FIELDS = [
    "title", "price", "old_price", "discount", "rating", "rating_count", "review_count",
    "category", "subcategories", "color", "fabric", "fit_shape", "length", "sizes", "seller_name",
    "product_url", "ext_id", "image_url", "gallery_image_urls",
    "affiliate_url", "generated_affiliate_url", "status",
]


def india_date() -> str:
    if ZoneInfo is not None:
        try:
            return datetime.now(ZoneInfo("Asia/Kolkata")).date().isoformat()
        except Exception:
            pass
    return date.today().isoformat()


def clean_url_token(value: str) -> str:
    return value.rstrip(".,;:!?)]}>")


def extract_ext_id(url: str) -> str:
    candidate = clean_url_token(url.strip())
    if not candidate:
        return ""
    try:
        parsed = urlsplit(candidate)
    except ValueError:
        return ""
    host = (parsed.hostname or "").lower()
    if host != "meesho.com" and not host.endswith(".meesho.com"):
        return ""
    query_id = (parse_qs(parsed.query).get("ext_id") or [""])[0]
    if query_id:
        return query_id.strip().lower()
    segments = [segment for segment in parsed.path.split("/") if segment]
    if len(segments) >= 3 and segments[0].lower() == "s" and segments[1].lower() == "p":
        return segments[2].lower()
    if len(segments) >= 2 and segments[-2].lower() == "p":
        return segments[-1].lower()
    return ""


def is_affiliate_url(url: str) -> bool:
    try:
        return "/af_invite/" in urlsplit(url).path.lower()
    except ValueError:
        return False


def collect_product_refs(text: str) -> list[dict[str, str]]:
    """Collect unique product IDs in first-seen order, preserving direct/custom URLs."""
    grouped: OrderedDict[str, dict[str, str]] = OrderedDict()
    for raw_url in RAW_URL_RE.findall(text):
        url = clean_url_token(raw_url)
        ext_id = extract_ext_id(url)
        if not ext_id:
            continue
        entry = grouped.setdefault(ext_id, {"ext_id": ext_id, "product_url": "", "affiliate_url": ""})
        if is_affiliate_url(url):
            if not entry["affiliate_url"]:
                entry["affiliate_url"] = url
        elif not entry["product_url"]:
            entry["product_url"] = url
    for ext_id, entry in grouped.items():
        if not entry["product_url"]:
            # A known ext_id can form Meesho's stable public short-product alias.
            entry["product_url"] = f"https://www.meesho.com/s/p/{ext_id}"
    return list(grouped.values())


def collect_image_urls(text: str) -> list[str]:
    urls: list[str] = []
    seen: set[str] = set()
    for raw in IMAGE_URL_RE.findall(text):
        url = clean_url_token(raw)
        try:
            parsed = urlsplit(url)
        except ValueError:
            continue
        if "/images/products/" not in parsed.path.lower() or url in seen:
            continue
        seen.add(url)
        urls.append(url)
    return urls


GARMENT_NOUNS = [
    'Midi Dress', 'Maxi Dress', 'Mini Dress', 'Bodycon Dress', 'Dress',
    'Kurti Set', 'Anarkali Kurti', 'Kurti', 'Top', 'Co-ord Set', 'Trousers',
    'Palazzo', 'Skirt', 'Jacket', 'Sweater', 'Cardigan', 'Saree', 'Lehenga', 'Jumpsuit', 'Blouse'
]


def clean_editorial_title(raw: str) -> tuple[str, str, list[str]]:
    text = str(raw or '').strip()
    if not text:
        return 'Curated Style Piece', 'Thoughtful fashion find', []

    all_words = re.findall(r'[a-zA-Z0-9]+', text.lower())
    stop_words = {'the', 'and', 'for', 'with', 'from', 'women', 'womens', 'girls', 'girl', 'one', 'piece'}
    seo_tags = list(dict.fromkeys(w for w in all_words if len(w) > 2 and w not in stop_words))

    # Split chunks by | or ;
    chunks = [c.strip() for c in re.split(r'[|;]+', text) if c.strip()]
    first_chunk = chunks[0] if chunks else text

    # Strip brand caps at start (e.g. SHRASTHA, DHRUVI, ZARA, etc.)
    first_chunk = re.sub(r'^[A-Z0-9]{3,}\s+(?:Fashion|Creation|Enterprises|Textile|Collection|Brand|Studio)?\s*', '', first_chunk)

    # Strip marketing fluff
    first_chunk = re.sub(r'(?i)\b(premium|exclusive|trending|stylish|designer|latest|heavy|pure|original|casual|formal|professional|western|daily wear|office & party|party wear|for office & party|one piece for women|one piece|combo pack|pack of \d+)\b', ' ', first_chunk)
    first_chunk = re.sub(r'(?i)\b(women\'s|womens|girls|for women|for girls|female)\b', ' ', first_chunk)
    first_chunk = re.sub(r'(?i)\b(\d+\s*gsm|\d+\s*count|\d+\s*meter|\d+\s*m)\b', ' ', first_chunk)

    clean_name = re.sub(r'\s+', ' ', first_chunk).strip(' -_,;.|')

    detected_noun = ''
    for noun in GARMENT_NOUNS:
        if re.search(rf'(?i)\b{re.escape(noun)}\b', text):
            detected_noun = noun
            break

    words = clean_name.split()
    if len(words) > 6 or len(clean_name) > 40:
        clean_name = ' '.join(words[:5])
        if detected_noun and detected_noun.lower() not in clean_name.lower():
            clean_name += f' {detected_noun}'

    display_title = clean_name.title()
    display_title = re.sub(r'\bAnd\b', '&', display_title)

    sub_parts = []
    for c in chunks[1:3]:
        sub_c = re.sub(r'(?i)\b(for women|for girls|buy online|best price|2026)\b', '', c).strip(' -_,;.|')
        if sub_c:
            sub_parts.append(sub_c.title())
    subtitle = ' · '.join(sub_parts) if sub_parts else 'Curated fashion piece'
    if len(subtitle) > 55:
        subtitle = subtitle[:52] + '...'

    return display_title, subtitle, seo_tags


def clean_title(value: str) -> str:
    text = RAW_URL_RE.sub(" ", value)
    text = IMAGE_URL_RE.sub(" ", text)
    text = re.sub(r"(?i)people\s+also\s+viewed", " ", text)
    text = re.sub(r"(?i)meesho\s+trusted", " ", text)
    text = re.sub(r"(?i)\+\s*\d+\s*more", " ", text)
    text = re.sub(r"(?i)\b[0-5](?:\.\d+)?\s*star\s*(?:[\d,]+\s*reviews?|supplier)\b", " ", text)
    text = re.sub(r"(?i)\bstar\s*supplier\b", " ", text)
    text = re.sub(r"(?i)\b\d+(?:\.\d+)?\s*%\s*off\b", " ", text)
    text = re.sub(r"\s+", " ", text).strip(" \t\r\n|·-,:;")
    words = text.split()
    # Meesho's copied listing text commonly repeats the card title back-to-back.
    if len(words) % 2 == 0 and words[: len(words) // 2] == words[len(words) // 2 :]:
        words = words[: len(words) // 2]
    raw_clean = " ".join(words).strip()
    editorial_title, _, _ = clean_editorial_title(raw_clean)
    return editorial_title or raw_clean



DETAIL_LABELS = {
    "color", "fabric", "fit shape", "length", "sleeve length", "sleeve type",
    "pattern", "sold by", "select size", "product highlights", "additional details",
    "product ratings reviews", "check delivery date", "lowest price", "cash on delivery",
}


def _normalise_label(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def _detail_field_value(text: str, labels: set[str]) -> str:
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if _normalise_label(line) not in labels:
            continue
        for candidate in lines[index + 1 :]:
            candidate = candidate.strip()
            if not candidate:
                continue
            if _normalise_label(candidate) in DETAIL_LABELS:
                break
            return candidate
    return ""


def _detail_seller(text: str) -> str:
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if _normalise_label(line) != "sold by":
            continue
        for candidate in lines[index + 1 : index + 10]:
            candidate = candidate.strip()
            normalized = _normalise_label(candidate)
            if not candidate or normalized in {"shop profile icon", "view shop", "products", "ratings"}:
                continue
            if re.fullmatch(r"[\d,.]+(?:\s+ratings?)?", candidate, re.IGNORECASE):
                continue
            if re.fullmatch(r"[0-5](?:\.\d)?", candidate):
                continue
            if _normalise_label(candidate) in DETAIL_LABELS:
                break
            return candidate
    return ""


def _detail_sizes(text: str) -> str:
    match = re.search(r"(?is)select\s+size(.*?)(?:product\s+highlights|$)", text)
    if not match:
        return ""
    found = re.findall(r"(?i)\b(XXXL|XXL|XXS|XL|XS|S|M|L|ONE\s+SIZE|FREE\s+SIZE)\b", match.group(1))
    return " | ".join(dict.fromkeys(re.sub(r"\s+", " ", size.upper()) for size in found))


def classify(title: str) -> tuple[str, list[str]]:
    text = title.lower()
    tags: list[str] = []

    if any(word in text for word in ("bra", "panty", "panties", "lingerie", "innerwear")):
        category = "Innerwear"
        if "bra" in text:
            tags.append("Bras")
        if any(word in text for word in ("panty", "panties")):
            tags.append("Panties")
    elif any(word in text for word in ("skirt", "palazzo", "plazo", "trouser", "pants", "leggings", "jeggings", "shorts")):
        category = "Bottomwear"
        if "skirt" in text:
            tags.append("Skirts")
        if "palazzo" in text or "plazo" in text:
            tags.append("Palazzos")
        if any(word in text for word in ("trouser", "pants")):
            tags.append("Trousers & pants")
        if "leggings" in text or "jeggings" in text:
            tags.append("Leggings")
        if "shorts" in text:
            tags.append("Shorts")
    elif "kurti" in text or "kurta" in text or "anarkali" in text:
        category = "Kurtis"
    elif any(word in text for word in ("saree", "lehenga", "salwar", "ethnic", "suit set")):
        category = "Ethnic Wear"
        if "saree" in text:
            tags.append("Sarees")
        if "lehenga" in text:
            tags.append("Lehengas")
        if "salwar" in text or "suit set" in text:
            tags.append("Suits")
    elif any(re.search(pattern, text) for pattern in (r"\bdress\b", r"\bbodycon\b", r"\bgown\b", r"\bone-piece\b", r"\bone piece\b", r"\bmaxi\b", r"\bmidi\b")):
        category = "Women Dresses"
        for pattern, label in ((r"\bbodycon\b", "Bodycon"), (r"\bmaxi\b", "Maxi"), (r"\bmidi\b", "Midi"), (r"\bmini\b", "Mini")):
            if re.search(pattern, text):
                tags.append(label)
    elif any(word in text for word in ("top", "tunic", "shirt", "crop top", "blouse")):
        category = "Tops & Tunics"
    elif any(word in text for word in ("sweater", "sweatshirt", "jacket", "puffer", "cardigan", "shawl")):
        category = "Winter"
    else:
        category = "Fashion"

    if any(phrase in text for phrase in ("full sleeve", "full sleeves", "long sleeve", "long sleeves")):
        tags.append("Full sleeves")
    if "sleeveless" in text:
        tags.append("Sleeveless")
    if "partywear" in text or "party wear" in text:
        tags.append("Partywear")
    if "floral" in text:
        tags.append("Floral")
    # De-duplicate tags while preserving order.
    tags = list(dict.fromkeys(tags))
    return category, tags


def read_lines_file(path: Path | None) -> list[str]:
    if path is None:
        return []
    if not path.is_file():
        raise FileNotFoundError(f"Input list not found: {path}")
    return [line.strip() for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]


def parse_paste(text: str, links: list[str] | None = None, image_urls: list[str] | None = None) -> list[dict[str, str]]:
    detail_mode = bool(DETAIL_PAGE_MARKER_RE.search(text))
    source_text = text
    if detail_mode:
        related_section = RELATED_SECTION_RE.search(source_text)
        if related_section:
            source_text = source_text[: related_section.start()]

    matches = list(PRICE_BLOCK_RE.finditer(source_text))
    if detail_mode:
        # A copied detail page contains many recommended cards; treat only the
        # primary listing as this entry and never mistake recommendations for it.
        matches = matches[:1]
    if not matches:
        return []

    records: list[dict[str, Any]] = []
    cursor = 0
    for match in matches:
        title = clean_title(source_text[cursor:match.start()])
        cursor = match.end()
        color = _detail_field_value(source_text, {"color"}) if detail_mode else ""
        fabric = _detail_field_value(source_text, {"fabric"}) if detail_mode else ""
        fit_shape = _detail_field_value(source_text, {"fit shape"}) if detail_mode else ""
        length = _detail_field_value(source_text, {"length"}) if detail_mode else ""
        sizes = _detail_sizes(source_text) if detail_mode else ""
        seller_name = _detail_seller(source_text) if detail_mode else ""
        category, tags = classify(" ".join(part for part in (title, fit_shape) if part))
        rating = match.group("rating") or ""
        rating_count = (match.group("rating_count") or "").replace(",", "")
        review_count = ""
        if detail_mode:
            rating_match = re.search(
                r"(?is)(?<![\d.])(?P<rating>[0-5](?:\.\d)?)\s+(?P<count>[\d,]+)\s+Ratings?\b",
                source_text[match.end() :],
            )
            if rating_match:
                rating = rating_match.group("rating")
                rating_count = rating_match.group("count").replace(",", "")
                review_match = re.search(
                    r"(?is)^\s*,?\s*(?P<count>[\d,]+)\s+Reviews?\b",
                    source_text[match.end() + rating_match.end() :],
                )
                if review_match:
                    review_count = review_match.group("count").replace(",", "")
        record = {
            "title": title,
            "price": match.group("price").replace(",", ""),
            "old_price": (match.group("old_price") or "").replace(",", ""),
            "discount": re.sub(r"\s+", "", match.group("discount") or ""),
            "rating": rating,
            "rating_count": rating_count,
            "review_count": review_count,
            "category": category,
            "subcategories": " | ".join(tags),
            "color": color,
            "fabric": fabric,
            "fit_shape": fit_shape,
            "length": length,
            "sizes": sizes,
            "seller_name": seller_name,
            "product_url": "",
            "ext_id": "",
            "image_url": "",
            "gallery_image_urls": "",
            "affiliate_url": "",
            "generated_affiliate_url": "",
            "status": "needs_product_url_or_ext_id",
        }
        records.append(record)

    raw_refs = collect_product_refs(source_text)
    if links:
        # Explicit lists are paired by order only when every card has one; no guessing.
        parsed_refs = collect_product_refs("\n".join(links))
        if len(parsed_refs) == len(records):
            raw_refs = parsed_refs
        elif len(links) == len(records):
            raw_refs = []
            for link in links:
                ext_id = extract_ext_id(link)
                raw_refs.append({
                    "ext_id": ext_id,
                    "product_url": "" if is_affiliate_url(link) else clean_url_token(link),
                    "affiliate_url": clean_url_token(link) if is_affiliate_url(link) else "",
                })

    if len(raw_refs) == len(records):
        for record, ref in zip(records, raw_refs):
            record["ext_id"] = ref["ext_id"]
            record["product_url"] = ref["product_url"]
            record["affiliate_url"] = ref["affiliate_url"]
            if not record["product_url"] and record["ext_id"]:
                record["product_url"] = f"https://www.meesho.com/s/p/{record['ext_id']}"
    elif raw_refs:
        for record in records:
            record["status"] = f"link_count_mismatch_{len(raw_refs)}_for_{len(records)}_cards"

    found_images = image_urls if image_urls else collect_image_urls(source_text)
    if detail_mode and records and found_images:
        records[0]["image_url"] = found_images[0]
        records[0]["gallery_image_urls"] = "|".join(found_images[1:9])
    elif len(found_images) == len(records):
        for record, image_url in zip(records, found_images):
            record["image_url"] = image_url

    existing_ids = load_existing_ids()
    for record in records:
        if record["ext_id"]:
            if record["ext_id"] in existing_ids:
                record["status"] = "ready_update_existing"
            elif record["product_url"] and record["image_url"]:
                record["status"] = "ready_add_new"
            elif not record["product_url"]:
                record["status"] = "needs_direct_product_url"
            else:
                record["status"] = "needs_image_url_for_new_listing"
            if record["product_url"]:
                try:
                    generated, _status = generate_link(record["product_url"], record["affiliate_url"])
                    record["generated_affiliate_url"] = generated
                except ValueError:
                    record["status"] = "needs_valid_product_url"
    return records


def load_existing_ids() -> set[str]:
    if not CATALOG_CSV.is_file():
        return set()
    with CATALOG_CSV.open("r", encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        return {
            str(row.get("ext_id") or extract_ext_id(str(row.get("product_url") or ""))).strip().lower()
            for row in reader
            if row.get("ext_id") or row.get("product_url")
        }


def download_image(image_url: str, ext_id: str, image_index: int = 0) -> str:
    parsed = urlsplit(image_url)
    if (parsed.hostname or "").lower() != "images.meesho.com" or "/images/products/" not in parsed.path.lower():
        raise ValueError("new-product image must be a supplied images.meesho.com product-image URL")
    request = Request(image_url, headers={"User-Agent": "Mozilla/5.0 (compatible; shelf-import/1.0)"})
    with urlopen(request, timeout=25) as response:
        content_type = (response.headers.get("Content-Type") or "").split(";", 1)[0].lower()
        data = response.read(6 * 1024 * 1024 + 1)
    if content_type not in {"image/webp", "image/jpeg", "image/png"} or len(data) > 6 * 1024 * 1024:
        raise ValueError("image response was not a supported product image (webp/jpeg/png, up to 6 MB)")
    extension = {"image/webp": ".webp", "image/jpeg": ".jpg", "image/png": ".png"}[content_type]
    safe_id = re.sub(r"[^a-z0-9_-]", "", ext_id.lower()) or "item"
    suffix = f"-{image_index:02d}" if image_index > 0 else ""
    filename = f"meesho-import-{safe_id}{suffix}{extension}"
    destination = ROOT / "public" / "images" / filename
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(data)
    return f"/images/{filename}"


def write_review(path: Path, records: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as destination:
        writer = csv.DictWriter(destination, fieldnames=OUTPUT_FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(records)


def apply_records(records: list[dict[str, str]]) -> tuple[int, int]:
    existing_ids = load_existing_ids()
    rows: list[dict[str, str]] = []
    skipped = 0
    checked_at = india_date()
    for record in records:
        ext_id = record["ext_id"].strip().lower()
        if not ext_id:
            record["status"] = "not_applied_missing_product_id"
            skipped += 1
            continue
        update: dict[str, str] = {
            "ext_id": ext_id,
            "price": record["price"],
            "price_checked_at": checked_at,
            "category": record["category"],
            "subtitle": record["subcategories"],
        }
        if record["old_price"]:
            update["old_price"] = record["old_price"]
        else:
            update["clear_old_price"] = "true"
        if record["image_url"]:
            update["image_url"] = record["image_url"]
        if record["product_url"]:
            update["product_url"] = record["product_url"]
        if record["affiliate_url"] and is_affiliate_url(record["affiliate_url"]):
            update["affiliate_url"] = record["affiliate_url"]
        if record["rating"]:
            update["rating"] = record["rating"]
        if record["rating_count"]:
            update["rating_count"] = record["rating_count"]

        if ext_id not in existing_ids:
            if not record["product_url"] or not record["image_url"]:
                record["status"] = "not_applied_new_listing_needs_url_and_image"
                skipped += 1
                continue
            try:
                update["image"] = download_image(record["image_url"], ext_id)
            except Exception as error:  # keep other complete listings importable
                record["status"] = f"not_applied_image_error: {error}"
                skipped += 1
                continue
            update["title"] = record["title"]
            update["category"] = record["category"]
        else:
            record["status"] = "applied_price_update"
        rows.append(update)

    if not rows:
        return 0, skipped

    fields = sorted({key for row in rows for key in row})
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", newline="", suffix=".csv", dir=SCRIPT_DIR, delete=False) as temp:
        temp_path = Path(temp.name)
        writer = csv.DictWriter(temp, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    try:
        subprocess.run(
            [sys.executable, str(SYNC_SCRIPT), "--input", str(temp_path)],
            cwd=ROOT,
            check=True,
        )
    finally:
        temp_path.unlink(missing_ok=True)
    return len(rows), skipped


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", "-i", type=Path, help="text file with copied Meesho listing content; omit to paste in terminal")
    parser.add_argument("--links-file", type=Path, help="optional one-product-URL-per-line file, in card order")
    parser.add_argument("--images-file", type=Path, help="optional one images.meesho.com URL per line, in card order")
    parser.add_argument("--output", "-o", type=Path, default=DEFAULT_OUTPUT, help=f"review CSV (default: {DEFAULT_OUTPUT})")
    parser.add_argument("--apply", action="store_true", help="upsert rows with IDs; new products also require a product URL and matching image URL")
    args = parser.parse_args()

    try:
        if args.input:
            input_path = args.input if args.input.is_absolute() else (ROOT / args.input).resolve()
            text = input_path.read_text(encoding="utf-8-sig")
        else:
            print("Paste the copied Meesho listing text below; finish with Ctrl+D (Linux/macOS) or Ctrl+Z then Enter (Windows).")
            text = sys.stdin.read()
        records = parse_paste(text, read_lines_file(args.links_file), read_lines_file(args.images_file))
        if not records:
            print("No ₹ price cards were found. Save the copied page text to a file and inspect its formatting.", file=sys.stderr)
            return 2

        output_path = args.output if args.output.is_absolute() else (ROOT / args.output).resolve()
        write_review(output_path, records)
        print(f"Parsed {len(records)} card(s); review file: {output_path}")
        for record in records:
            title = record["title"] or "(title not detected)"
            rating = f" · ★ {record['rating']} / {record['rating_count']}" if record["rating"] and record["rating_count"] else ""
            tags = f" · {record['subcategories']}" if record["subcategories"] else ""
            print(f"  ₹{record['price']} · {record['category']}{tags} · {title}{rating} · {record['status']}")

        if args.apply:
            applied, skipped = apply_records(records)
            write_review(output_path, records)
            print(f"Import complete: {applied} row(s) sent to catalog sync; {skipped} skipped for missing ID/link/image or invalid image.")
            if skipped:
                print("Skipped entries remain in the review CSV. The pasted text cannot create product-specific links without ext_id/product URLs.")
        else:
            print("Review only: no catalog changes made. Add product URLs/IDs (and image URLs for new listings), then rerun with --apply.")
        return 0
    except (OSError, UnicodeError, csv.Error, subprocess.CalledProcessError, ValueError) as error:
        print(f"Paste import failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
