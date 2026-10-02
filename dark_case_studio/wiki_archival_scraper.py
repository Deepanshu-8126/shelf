"""
Wikipedia & Wikimedia Commons Archival Scraper (100% Free, Zero API Key).
Pulls historical dossiers, official summaries, and authentic public domain archive photos
for Dark Case Files / True Crime / Mystery documentaries.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any
import requests


USER_AGENT = "DarkCaseStudioDocumentary/1.0 (archival_research@factsyt.org)"


def clean_wikitext(text: str) -> str:
    """Removes citations [1], references, and formatting."""
    text = re.sub(r"\[\d+\]", "", text)
    text = re.sub(r"\[edit\]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def fetch_case_dossier(topic: str, output_dir: Path | None = None) -> dict[str, Any]:
    """
    Fetches full case facts, summary, dates, and archival images for a given topic.
    Example topics: 'Black_Dolphin_Prison', 'Dyatlov_Pass_incident', 'Alcatraz_Federal_Penitentiary'
    """
    topic_slug = topic.strip().replace(" ", "_")
    headers = {"User-Agent": USER_AGENT}

    # 1. Fetch REST API Summary
    summary_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{topic_slug}"
    res = requests.get(summary_url, headers=headers, timeout=12)
    if res.status_code != 200:
        raise ValueError(f"Failed to fetch Wikipedia page for '{topic}'. Status: {res.status_code}")
    summary_data = res.json()

    title = summary_data.get("title", topic)
    description = summary_data.get("description", "Historical Investigation")
    extract = clean_wikitext(summary_data.get("extract", ""))

    # 2. Setup download directory
    if output_dir is None:
        output_dir = Path("d:/facts_yt/dark_case_studio/assets/downloads") / topic_slug
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save summary metadata
    dossier = {
        "topic": topic,
        "title": title,
        "description": description,
        "extract": extract,
        "images": [],
    }

    # 3. Fetch Lead Image if available
    lead_thumb = summary_data.get("thumbnail", {}).get("source")
    lead_original = summary_data.get("originalimage", {}).get("source")
    target_lead = lead_original or lead_thumb

    if target_lead:
        img_name = "lead_archive.jpg"
        save_path = output_dir / img_name
        try:
            r_img = requests.get(target_lead, headers=headers, timeout=15)
            if r_img.status_code == 200:
                save_path.write_bytes(r_img.content)
                dossier["images"].append({
                    "name": "lead_image",
                    "path": str(save_path),
                    "url": target_lead
                })
                print(f">> Downloaded lead archival photo: {save_path.name}")
        except Exception as e:
            print(f">> Could not download lead image: {e}")

    # 4. Fetch additional gallery images via MediaWiki API
    api_url = (
        f"https://en.wikipedia.org/w/api.php?action=query&titles={topic_slug}"
        f"&generator=images&gimlimit=10&prop=imageinfo&iiprop=url|size|mime&format=json"
    )
    try:
        r_media = requests.get(api_url, headers=headers, timeout=12)
        if r_media.status_code == 200:
            pages = r_media.json().get("query", {}).get("pages", {})
            img_idx = 1
            for page_id, pdata in pages.items():
                title_file = pdata.get("title", "").lower()
                # Skip icons, maps with pure SVG, or non-photo files
                if any(skip in title_file for skip in [".svg", "question", "icon", "stub", "logo", "portal"]):
                    continue
                info = pdata.get("imageinfo", [{}])[0]
                img_url = info.get("url")
                width = info.get("width", 0)
                # Only keep substantial resolution images (> 400px)
                if img_url and width >= 400:
                    # Clean extension
                    clean_path = img_url.split("?")[0]
                    ext = clean_path.split(".")[-1].lower()
                    if ext not in ["jpg", "jpeg", "png", "webp"]:
                        ext = "jpg"
                    save_path = output_dir / f"archive_photo_{img_idx}.{ext}"
                    try:
                        r_file = requests.get(img_url, headers=headers, timeout=15)
                        if r_file.status_code == 200:
                            save_path.write_bytes(r_file.content)
                            dossier["images"].append({
                                "name": pdata.get("title"),
                                "path": str(save_path),
                                "url": img_url
                            })
                            print(f">> Downloaded archive photo {img_idx}: {save_path.name} ({width}px)")
                            img_idx += 1
                            if img_idx > 4:  # 4 high-res archive photos is optimal for a 60s short
                                break
                    except Exception as err:
                        pass
    except Exception as e:
        print(f">> Error searching additional Wikimedia photos: {e}")

    # Write dossier JSON to disk
    json_path = output_dir / "case_dossier.json"
    json_path.write_text(json.dumps(dossier, indent=2), encoding="utf-8")
    print(f">> Case dossier saved to: {json_path}")
    return dossier


if __name__ == "__main__":
    dossier = fetch_case_dossier("Black Dolphin Prison")
    print("\nSummary Title:", dossier["title"])
    print("Extract:", dossier["extract"][:200], "...")
    print(f"Total Photos Downloaded: {len(dossier['images'])}")
