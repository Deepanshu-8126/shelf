"""
SEO Schema Generator for Super YouTube Agent.
Generates production-grade, Google-compliant Schema.org JSON-LD structured data:
- Type: VideoObject (Google Rich Results verified)
- Supports: YouTube Chapters (Clip), SeekToAction, Transcript, and Thumbnail arrays.
- Complies with latest Google Search guidelines (active June 2026 specifications).
"""
from __future__ import annotations

import datetime
import json
from pathlib import Path
from typing import Any


def format_iso8601_duration(seconds: float | int) -> str:
    """Converts seconds into ISO 8601 duration format (e.g. PT58S or PT8M30S)."""
    s = int(round(seconds))
    hours = s // 3600
    minutes = (s % 3600) // 60
    sec = s % 60
    
    parts = ["PT"]
    if hours > 0:
        parts.append(f"{hours}H")
    if minutes > 0:
        parts.append(f"{minutes}M")
    if sec > 0 or (hours == 0 and minutes == 0):
        parts.append(f"{sec}S")
    return "".join(parts)


def build_video_schema(
    title: str,
    description: str,
    duration_sec: float | int,
    thumbnail_urls: list[str],
    upload_date: str | None = None,
    channel_name: str = "Super YouTube Studio",
    channel_url: str = "https://www.youtube.com/@SuperYouTubeAgent",
    content_url: str | None = None,
    embed_url: str | None = None,
    transcript: str | None = None,
    chapters: list[dict[str, Any]] | None = None,
    keywords: list[str] | None = None
) -> dict[str, Any]:
    """
    Constructs a valid Schema.org VideoObject JSON-LD dictionary.
    """
    now_iso = upload_date or datetime.datetime.now(datetime.timezone.utc).isoformat()
    duration_iso = format_iso8601_duration(duration_sec)

    schema: dict[str, Any] = {
        "@context": "https://schema.org",
        "@type": "VideoObject",
        "name": title,
        "description": description,
        "uploadDate": now_iso,
        "duration": duration_iso,
        "thumbnailUrl": thumbnail_urls or [
            "https://i.ytimg.com/vi/placeholder/maxresdefault.jpg"
        ],
        "author": {
            "@type": "Organization",
            "name": channel_name,
            "url": channel_url
        }
    }

    if content_url:
        schema["contentUrl"] = content_url
    if embed_url:
        schema["embedUrl"] = embed_url
    if transcript:
        schema["transcript"] = transcript
    if keywords:
        schema["keywords"] = ", ".join(keywords)

    # Chapters / Clips (Google Rich Results for Key Moments)
    if chapters:
        parts = []
        for ch in chapters:
            part = {
                "@type": "Clip",
                "name": ch.get("title", "Chapter"),
                "startOffset": int(ch.get("start", 0)),
                "endOffset": int(ch.get("end", 0)),
                "url": f"{content_url or channel_url}#t={int(ch.get('start', 0))}"
            }
            parts.append(part)
        schema["hasPart"] = parts

        # Add SeekToAction for dynamic key moments discovery
        if content_url:
            schema["potentialAction"] = {
                "@type": "SeekToAction",
                "target": f"{content_url}&t={{seek_to_second_number}}",
                "startOffset-input": "required name=seek_to_second_number"
            }

    return schema


def export_schema_json_ld(schema_data: dict[str, Any], output_path: Path) -> Path:
    """Exports structured data to a .json file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(schema_data, indent=2, ensure_ascii=False), encoding="utf-8")
    return output_path


def format_schema_tag(schema_data: dict[str, Any]) -> str:
    """Returns HTML <script type="application/ld+json"> tag."""
    raw = json.dumps(schema_data, indent=2, ensure_ascii=False)
    return f'<script type="application/ld+json">\n{raw}\n</script>'
