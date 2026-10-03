"""A tiny append-only log of what was posted, so nothing goes up twice.

Deliberately a JSON file and not a database: this has to survive a wiped
sandbox and be readable by a human at a glance.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

LOG = Path.home() / "Shorts" / "instagram_posted.json"


def _read(path: Path) -> list[dict]:
    if not path.exists():
        return []
    try:
        d = json.loads(path.read_text())
        return d if isinstance(d, list) else []
    except json.JSONDecodeError:
        return []


def already_posted(clip_id: str, kind: str = "reel",
                   path: Path = LOG) -> dict | None:
    for row in _read(path):
        if row.get("clip") == clip_id and row.get("kind") == kind:
            return row
    return None


def record(clip_id: str, kind: str, media_id: str, caption: str = "",
           path: Path = LOG) -> dict:
    rows = _read(path)
    row = {"clip": clip_id, "kind": kind, "media_id": media_id,
           "caption": caption[:300],
           "at": time.strftime("%Y-%m-%d %H:%M:%S")}
    rows.append(row)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(rows, indent=2, ensure_ascii=False))
    return row


def today_count(path: Path = LOG) -> int:
    today = time.strftime("%Y-%m-%d")
    return sum(1 for r in _read(path) if str(r.get("at", "")).startswith(today))
