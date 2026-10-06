"""Step 1 - pull the source video with yt-dlp (python API, no shelling out)."""
from __future__ import annotations

import json
from pathlib import Path

from .config import settings


def download(url: str, out_dir: Path | None = None, cookies: str | None = None) -> dict:
    """Download best <=1080p mp4 + m4a. Returns {'path', 'title', 'duration', 'id'}."""
    import yt_dlp

    out_dir = Path(out_dir or settings.work_dir / "source")
    out_dir.mkdir(parents=True, exist_ok=True)

    opts = {
        "format": "bv*[height<=1080][ext=mp4]+ba[ext=m4a]/b[height<=1080]/b",
        "merge_output_format": "mp4",
        "outtmpl": str(out_dir / "%(id)s.%(ext)s"),
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "retries": 5,
        "concurrent_fragment_downloads": 4,
        # YouTube now throttles anonymous clients hard; cookies make long videos reliable.
        "cookiefile": cookies,
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)

    path = out_dir / f"{info['id']}.mp4"
    meta = {
        "id": info["id"],
        "title": info.get("title", ""),
        "duration": info.get("duration", 0),
        "channel": info.get("uploader", ""),
        "path": str(path),
    }
    (out_dir / f"{info['id']}.meta.json").write_text(json.dumps(meta, indent=2))
    return meta
