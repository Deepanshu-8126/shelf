#!/usr/bin/env python3
"""Generate Meesho af_invite routes using the pattern supplied by the creator.

This script builds redirect URLs; it cannot verify account ownership or commission
attribution. Verify generated links in the Meesho Creator dashboard before publishing.

Input CSV must contain a `product_url` column. An optional `affiliate_url` column
can contain a creator-generated link; that link is preserved rather than wrapped.
Usage: python scripts/generate_meesho_affiliate_links.py products.csv [output.csv]
"""
from __future__ import annotations

import argparse
import csv
import os
import re
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlsplit

MEESHO_AFFILIATE_ID = os.getenv("MEESHO_AFFILIATE_ID", "374453404").strip()
MEESHO_SOURCE = os.getenv("MEESHO_SOURCE", "youtube_long_form").strip()
MEESHO_CAMPAIGN_ID = os.getenv("MEESHO_CAMPAIGN_ID", "12492338").strip()


def generate_link(raw_url: str, creator_link: str = "") -> tuple[str, str]:
    """Return (click URL, status) for a Meesho product URL."""
    candidate = (creator_link or raw_url).strip()
    if not candidate:
        raise ValueError("Missing product_url")
    if not candidate.startswith(("https://", "http://")):
        candidate = "https://www.meesho.com/" + candidate.lstrip("/")

    parsed = urlsplit(candidate)
    host = (parsed.hostname or "").lower()
    if host != "meesho.com" and not host.endswith(".meesho.com"):
        return candidate, "non-meesho-preserved"

    path_lower = parsed.path.lower()
    if "/af_invite/" in path_lower:
        return candidate, "creator-link-preserved"
    short_product = re.fullmatch(r"/s/p/([^/]+)/?", parsed.path, re.IGNORECASE)
    if re.search(r"/s(?:/|$)", path_lower) and not short_product:
        return candidate, "shortlink-preserved"

    query = parse_qs(parsed.query)
    product_id = (query.get("p_id") or [""])[0]
    ext_id = (query.get("ext_id") or [""])[0]
    if not ext_id and short_product:
        ext_id = short_product.group(1)
    if not product_id:
        match = re.search(r"/p/(\d+)(?:/|$)", parsed.path, re.IGNORECASE)
        product_id = match.group(1) if match else ""
    if not ext_id:
        match = re.search(r"/p/([^/]+?)/?$", parsed.path, re.IGNORECASE)
        ext_id = match.group(1) if match else ""

    if not product_id and not ext_id:
        raise ValueError(f"Could not find p_id or ext_id in product URL: {candidate}")

    params: list[tuple[str, str]] = []
    if product_id:
        params.append(("p_id", product_id))
    if ext_id:
        params.append(("ext_id", ext_id))
    params.append(("utm_source", MEESHO_SOURCE))
    route = f"https://www.meesho.com/af_invite/{MEESHO_AFFILIATE_ID}:{MEESHO_SOURCE}:{MEESHO_CAMPAIGN_ID}"
    return f"{route}?{urlencode(params)}", "generated-from-supplied-pattern"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_csv", type=Path, help="CSV containing product_url and optional affiliate_url")
    parser.add_argument("output_csv", type=Path, nargs="?", help="Output CSV (default: <input>-with-links.csv)")
    args = parser.parse_args()
    output = args.output_csv or args.input_csv.with_name(f"{args.input_csv.stem}-with-links.csv")

    if not args.input_csv.exists():
        parser.error(f"Input not found: {args.input_csv}")

    with args.input_csv.open("r", encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        if not reader.fieldnames or "product_url" not in reader.fieldnames:
            parser.error("Input CSV must include a 'product_url' column")
        rows = list(reader)
        fields = list(reader.fieldnames)

    for field in ("generated_affiliate_url", "link_status"):
        if field not in fields:
            fields.append(field)

    generated = preserved = failed = 0
    for row in rows:
        try:
            url, status = generate_link(row.get("product_url", ""), row.get("affiliate_url", ""))
            row["generated_affiliate_url"] = url
            row["link_status"] = status
            if status == "generated-from-supplied-pattern":
                generated += 1
            else:
                preserved += 1
        except ValueError as error:
            row["generated_affiliate_url"] = ""
            row["link_status"] = f"needs-review: {error}"
            failed += 1

    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as destination:
        writer = csv.DictWriter(destination, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {output} | generated {generated}, preserved {preserved}, needs review {failed}")
    print("Note: a redirect is not proof of commission attribution; verify in Meesho Creator.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
