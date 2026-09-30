#!/usr/bin/env python3
"""Populate assets/stock/ with free footage so the bot can render with *no* API keys.

  python scripts/fetch_demo_footage.py                 # all niches, 4 clips each
  python scripts/fetch_demo_footage.py --niche space --count 6
  python scripts/fetch_demo_footage.py --list          # show what is cached already

Downloads CC/PD video from Wikimedia Commons (throttled, ~25 MB per clip max) and
writes assets/stock/manifest.json with author + licence for every file, so you can
credit them in your video description. Pexels/Pixabay keys are still recommended
for the best-looking, portrait-oriented results.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from factshorts.config import get_config                       # noqa: E402
from factshorts.db import init_db                             # noqa: E402
from factshorts.footage import (  # noqa: E402
    COMMONS_EXTRA_QUERIES,
    JUNK_TITLE_RE,
    FootageClient,
)
from factshorts.script_writer import GENERIC_VISUALS          # noqa: E402
from factshorts.topic_engine import TOPIC_KEYWORDS            # noqa: E402
from factshorts.utils import human_bytes, module_logger, setup_logging  # noqa: E402

log = module_logger("fetch_demo")


def queries_for(niche: str, limit: int = 8) -> list[str]:
    specific = [kw for topic, kws in TOPIC_KEYWORDS.items() if kws and _topic_niche(topic) == niche for kw in kws]
    generic = GENERIC_VISUALS.get(niche, [])
    pool = list(dict.fromkeys(specific + generic + COMMONS_EXTRA_QUERIES))
    return pool[:limit]


def _topic_niche(topic: str) -> str:
    from factshorts.topic_engine import FACT_BANK

    for niche, entries in FACT_BANK.items():
        if any(e["topic"] == topic for e in entries):
            return niche
    return ""


PROVIDERS_PER_NICHE = {
    "space": ["nasa", "wikimedia"],       # NASA is fast, public domain and always up
    "science": ["nasa", "wikimedia"],
    "animals": ["wikimedia", "nasa"],
    "history": ["wikimedia", "nasa"],
    "psychology": ["wikimedia", "nasa"],
}


async def fetch(niches: list[str], count: int, max_mb: float) -> None:
    cfg = get_config()
    stock = cfg.assets_dir / "stock"
    stock.mkdir(parents=True, exist_ok=True)
    manifest_path = stock / "manifest.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}

    client = FootageClient(cfg)
    total_bytes = 0
    try:
        for niche in niches:
            got = 0
            providers = PROVIDERS_PER_NICHE.get(niche, ["wikimedia"])
            for query in queries_for(niche):
                if got >= count:
                    break
                cands = []
                for provider in providers:
                    try:
                        if provider == "nasa":
                            found = await client._nasa(query, 6)
                        elif provider == "wikimedia":
                            found = await client._wikimedia(query, 6)
                        else:
                            found = []
                    except Exception as exc:  # noqa: BLE001
                        log.warning("%s search failed for %r: %s", provider, query, exc)
                        continue
                    found = [c for c in found if not (c.title and JUNK_TITLE_RE.search(c.title))]
                    if found:
                        cands = found
                        break
                if not cands:
                    continue
                for cand in cands:
                    if got >= count:
                        break
                    if (cand.filesize or 0) > max_mb * 1024 * 1024:
                        continue
                    clip = await client.download(cand)
                    if not clip:
                        continue
                    dest = stock / f"{niche}-{query.replace(' ', '_')}-{cand.source_id}{clip.path.suffix}"
                    if dest.exists():
                        continue
                    try:
                        dest.write_bytes(clip.path.read_bytes())
                    except OSError as exc:
                        log.warning("could not copy %s: %s", dest.name, exc)
                        continue
                    manifest[dest.name] = {
                        "niche": niche,
                        "title": cand.title,
                        "query": query,
                        "source": cand.source,
                        "source_id": cand.source_id,
                        "page": cand.page_url,
                        "author": cand.author,
                        "license": cand.license,
                        "duration": round(clip.duration, 2),
                        "size": dest.stat().st_size,
                    }
                    total_bytes += dest.stat().st_size
                    got += 1
                    log.info("%s (%s, %.1fs, %s)", dest.name, cand.license, clip.duration, human_bytes(dest.stat().st_size))
            log.info("%s: %d clips", niche, got)
    finally:
        await client.aclose()
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        log.info("manifest updated: %s (%d files, %s total)", manifest_path, len(manifest), human_bytes(total_bytes))


def show() -> None:
    cfg = get_config()
    stock = cfg.assets_dir / "stock"
    manifest_path = stock / "manifest.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    if not manifest:
        print("assets/stock is empty - run: python scripts/fetch_demo_footage.py")
        return
    print(f"{len(manifest)} clips in {stock}\n")
    for name, meta in sorted(manifest.items()):
        print(f"  {name:52s} {meta['duration']:5.1f}s  {meta['license'][:40]:42s} {meta['query']}")


def main() -> int:
    setup_logging("INFO")
    init_db()
    parser = argparse.ArgumentParser(description="Download free demo footage into assets/stock/")
    parser.add_argument("--niche", action="append", dest="niches",
                        choices=["space", "psychology", "history", "science", "animals"],
                        help="repeatable; default = all niches")
    parser.add_argument("--count", type=int, default=4, help="clips per niche (default 4)")
    parser.add_argument("--max-mb", type=float, default=25.0, help="skip clips larger than this")
    parser.add_argument("--list", action="store_true", help="list what is already downloaded")
    args = parser.parse_args()

    if args.list:
        show()
        return 0
    niches = args.niches or ["space", "psychology", "history", "science", "animals"]
    asyncio.run(fetch(niches, args.count, args.max_mb))
    show()
    print("\nTip: these clips also credit the authors at render time (see the render .json report).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
