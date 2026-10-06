"""SQLite storage: topics (anti-repeat), videos, clip cache, runtime settings."""
from __future__ import annotations

import json
import sqlite3
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable

from .config import get_config
from .utils import module_logger

log = module_logger("db")
_lock = threading.RLock()

SCHEMA = """
CREATE TABLE IF NOT EXISTS topics (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    niche        TEXT NOT NULL,
    topic        TEXT NOT NULL,
    fact         TEXT,
    fingerprint  TEXT NOT NULL,
    verified     INTEGER DEFAULT 0,
    source       TEXT,
    source_url   TEXT,
    created_at   TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_topics_niche ON topics(niche, id DESC);

CREATE TABLE IF NOT EXISTS videos (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    niche         TEXT,
    topic         TEXT,
    hook          TEXT,
    script        TEXT,
    title         TEXT,
    description   TEXT,
    tags          TEXT,
    pinned_comment TEXT,
    video_path    TEXT,
    duration      REAL,
    status        TEXT NOT NULL DEFAULT 'rendering',
    yt_video_id   TEXT,
    ig_media_id   TEXT,
    source_url    TEXT,
    source_name   TEXT,
    platforms     TEXT,
    publish_at    TEXT,
    error         TEXT,
    meta          TEXT,
    created_at    TEXT NOT NULL,
    updated_at    TEXT NOT NULL,
    uploaded_at   TEXT
);
CREATE INDEX IF NOT EXISTS idx_videos_status ON videos(status, id DESC);

CREATE TABLE IF NOT EXISTS clip_cache (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    source      TEXT NOT NULL,
    source_id   TEXT NOT NULL,
    path        TEXT NOT NULL,
    page_url    TEXT,
    author      TEXT,
    license     TEXT,
    query       TEXT,
    duration    REAL,
    width       INTEGER,
    height      INTEGER,
    used_count  INTEGER DEFAULT 0,
    created_at  TEXT NOT NULL,
    UNIQUE(source, source_id)
);

CREATE TABLE IF NOT EXISTS settings (
    key   TEXT PRIMARY KEY,
    value TEXT
);
"""

VIDEO_FIELDS = {
    "niche", "topic", "hook", "script", "title", "description", "tags", "pinned_comment",
    "video_path", "duration", "status", "yt_video_id", "ig_media_id", "source_url",
    "source_name", "platforms", "publish_at", "error", "meta", "uploaded_at",
}

# columns added after the first release - applied automatically to existing databases
MIGRATIONS = {
    "ig_media_id": "TEXT",
    "source_url": "TEXT",
    "source_name": "TEXT",
    "platforms": "TEXT",
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def connect() -> sqlite3.Connection:
    cfg = get_config()
    Path(cfg.db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(cfg.db_path), timeout=30, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=10000")
    return conn


def init_db() -> None:
    with _lock, connect() as conn:
        conn.executescript(SCHEMA)
        _migrate(conn)
    log.info("database ready at %s", get_config().db_path)


def _migrate(conn: sqlite3.Connection) -> None:
    """Add columns that older databases are missing (no destructive changes)."""
    try:
        existing = {row["name"] for row in conn.execute("PRAGMA table_info(videos)").fetchall()}
    except sqlite3.Error:
        return
    for column, sqltype in MIGRATIONS.items():
        if column not in existing:
            conn.execute(f"ALTER TABLE videos ADD COLUMN {column} {sqltype}")
            log.info("db migration: added videos.%s", column)
    try:
        topic_cols = {row["name"] for row in conn.execute("PRAGMA table_info(topics)").fetchall()}
        if topic_cols and "source_url" not in topic_cols:
            conn.execute("ALTER TABLE topics ADD COLUMN source_url TEXT")
            log.info("db migration: added topics.source_url")
    except sqlite3.Error:
        pass


def _rows(sql: str, params: Iterable[Any] = ()) -> list[dict[str, Any]]:
    with _lock, connect() as conn:
        return [dict(r) for r in conn.execute(sql, tuple(params)).fetchall()]


def _one(sql: str, params: Iterable[Any] = ()) -> dict[str, Any] | None:
    rows = _rows(sql, params)
    return rows[0] if rows else None


def _exec(sql: str, params: Iterable[Any] = ()) -> int:
    with _lock, connect() as conn:
        cur = conn.execute(sql, tuple(params))
        return cur.lastrowid or cur.rowcount


# --------------------------------------------------------------------- settings
def get_setting(key: str, default: str | None = None) -> str | None:
    row = _one("SELECT value FROM settings WHERE key = ?", (key,))
    return row["value"] if row else default


def set_setting(key: str, value: Any) -> None:
    with _lock, connect() as conn:
        conn.execute(
            "INSERT INTO settings(key, value) VALUES(?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, str(value)),
        )


def get_bool_setting(key: str, default: bool = False) -> bool:
    raw = get_setting(key)
    if raw is None:
        return default
    return str(raw).lower() in {"1", "true", "yes", "on"}


def get_float_setting(key: str, default: float) -> float:
    raw = get_setting(key)
    try:
        return float(raw) if raw is not None else default
    except ValueError:
        return default


# ----------------------------------------------------------------------- topics
def topic_fingerprints(limit: int = 400) -> list[str]:
    return [r["fingerprint"] for r in _rows("SELECT fingerprint FROM topics ORDER BY id DESC LIMIT ?", (limit,))]


def add_topic(niche: str, topic: str, fact: str, fingerprint: str, verified: bool,
              source: str | None = None, source_url: str = "") -> int:
    return _exec(
        "INSERT INTO topics(niche, topic, fact, fingerprint, verified, source, source_url, created_at) "
        "VALUES(?,?,?,?,?,?,?,?)",
        (niche, topic, fact, fingerprint, int(bool(verified)), source, source_url or "", _now()),
    )


def recent_topics(limit: int = 60) -> list[dict[str, Any]]:
    return _rows("SELECT * FROM topics ORDER BY id DESC LIMIT ?", (limit,))


# ----------------------------------------------------------------------- videos
def create_video(
    niche: str,
    topic: str = "",
    status: str = "rendering",
    hook: str = "",
    script: str = "",
    meta: dict[str, Any] | None = None,
) -> int:
    now = _now()
    return _exec(
        "INSERT INTO videos(niche, topic, status, hook, script, meta, created_at, updated_at) "
        "VALUES(?,?,?,?,?,?,?,?)",
        (niche, topic, status, hook, script, json.dumps(meta or {}), now, now),
    )


def update_video(video_id: int, **fields: Any) -> None:
    fields = {k: v for k, v in fields.items() if k in VIDEO_FIELDS}
    if not fields:
        return
    for key in ("tags", "meta"):
        if key in fields and not isinstance(fields[key], str):
            fields[key] = json.dumps(fields[key], ensure_ascii=False)
    sets = ", ".join(f"{k} = ?" for k in fields)
    params = list(fields.values()) + [_now(), video_id]
    with _lock, connect() as conn:
        conn.execute(f"UPDATE videos SET {sets}, updated_at = ? WHERE id = ?", params)


def update_meta(video_id: int, patch: dict[str, Any]) -> None:
    """Merge keys into videos.meta instead of replacing the whole JSON blob."""
    row = get_video(video_id)
    if not row:
        return
    try:
        meta = json.loads(row.get("meta") or "{}")
    except Exception:  # noqa: BLE001
        meta = {}
    meta.update(patch or {})
    update_video(video_id, meta=meta)


def get_video(video_id: int) -> dict[str, Any] | None:
    return _one("SELECT * FROM videos WHERE id = ?", (video_id,))


def list_videos(status: str | None = None, limit: int = 20) -> list[dict[str, Any]]:
    if status:
        statuses = [s.strip() for s in status.split(",") if s.strip()]
        marks = ",".join("?" for _ in statuses)
        return _rows(f"SELECT * FROM videos WHERE status IN ({marks}) ORDER BY id DESC LIMIT ?", (*statuses, limit))
    return _rows("SELECT * FROM videos ORDER BY id DESC LIMIT ?", (limit,))


def count_videos_since(statuses: list[str], hours: int = 24) -> int:
    since = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat(timespec="seconds")
    marks = ",".join("?" for _ in statuses)
    row = _one(
        f"SELECT COUNT(*) AS c FROM videos WHERE status IN ({marks}) AND created_at >= ?",
        (*statuses, since),
    )
    return int(row["c"]) if row else 0


def stats() -> dict[str, Any]:
    rows = _rows("SELECT status, COUNT(*) AS c FROM videos GROUP BY status")
    by_status = {r["status"]: r["c"] for r in rows}
    total = sum(by_status.values())
    last = _one(
        "SELECT title, yt_video_id, uploaded_at FROM videos WHERE status = 'uploaded' "
        "ORDER BY id DESC LIMIT 1"
    )
    return {"by_status": by_status, "total": total, "last_upload": last}


def next_pending() -> dict[str, Any] | None:
    return _one("SELECT * FROM videos WHERE status IN ('pending','approved','failed') ORDER BY id ASC LIMIT 1")


# ------------------------------------------------------------------ clip cache
def clip_get(source: str, source_id: str) -> dict[str, Any] | None:
    return _one("SELECT * FROM clip_cache WHERE source = ? AND source_id = ?", (source, source_id))


def clip_add(
    source: str,
    source_id: str,
    path: str,
    page_url: str = "",
    author: str = "",
    license_: str = "",
    query: str = "",
    duration: float = 0.0,
    width: int = 0,
    height: int = 0,
) -> int:
    return _exec(
        "INSERT OR IGNORE INTO clip_cache(source, source_id, path, page_url, author, license, query,"
        " duration, width, height, created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
        (source, source_id, path, page_url, author, license_, query, duration, width, height, _now()),
    )


def clip_mark_used(source: str, source_id: str) -> None:
    with _lock, connect() as conn:
        conn.execute(
            "UPDATE clip_cache SET used_count = used_count + 1 WHERE source = ? AND source_id = ?",
            (source, source_id),
        )


def clip_pick_cached(source: str, query: str, min_duration: float = 3.0) -> dict[str, Any] | None:
    """Return a previously downloaded, least-used clip matching a keyword."""
    rows = _rows(
        "SELECT * FROM clip_cache WHERE source = ? AND duration >= ? AND query LIKE ? "
        "ORDER BY used_count ASC, RANDOM() LIMIT 1",
        (source, min_duration, f"%{query}%"),
    )
    return rows[0] if rows else None


def clip_unused_count(source: str) -> int:
    row = _one("SELECT COUNT(*) AS c FROM clip_cache WHERE source = ? AND used_count = 0", (source,))
    return int(row["c"]) if row else 0
