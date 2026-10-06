from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any

from .config import DATA_DIR, DB_PATH


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def connect() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=15)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


@contextmanager
def get_db():
    conn = connect()
    try:
        with conn:
            yield conn
    finally:
        conn.close()


def init_db() -> None:
    with get_db() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS channels (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            niche TEXT NOT NULL DEFAULT 'Awaiting market scan',
            audience_country TEXT NOT NULL DEFAULT 'US',
            language TEXT NOT NULL DEFAULT 'en-US',
            format TEXT NOT NULL DEFAULT 'Shorts + long-form tests',
            active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS scans (
            id TEXT PRIMARY KEY,
            mode TEXT NOT NULL,
            created_at TEXT NOT NULL,
            notes TEXT NOT NULL,
            candidates_json TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS jobs (
            id TEXT PRIMARY KEY,
            channel_id TEXT NOT NULL,
            title TEXT NOT NULL,
            topic TEXT NOT NULL,
            niche TEXT NOT NULL,
            format TEXT NOT NULL,
            status TEXT NOT NULL,
            stage TEXT NOT NULL,
            package_path TEXT NOT NULL,
            video_path TEXT NOT NULL DEFAULT '',
            has_audio INTEGER NOT NULL DEFAULT 0,
            rights_status TEXT NOT NULL DEFAULT 'uncleared',
            rights_evidence TEXT NOT NULL DEFAULT '',
            human_approved INTEGER NOT NULL DEFAULT 0,
            scheduled_at TEXT NOT NULL DEFAULT '',
            youtube_video_id TEXT NOT NULL DEFAULT '',
            error TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            data_json TEXT NOT NULL DEFAULT '{}',
            FOREIGN KEY(channel_id) REFERENCES channels(id)
        );
        CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status, scheduled_at);
        CREATE TABLE IF NOT EXISTS analytics_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel_id TEXT NOT NULL,
            video_id TEXT NOT NULL,
            snapshot_date TEXT NOT NULL,
            views INTEGER NOT NULL DEFAULT 0,
            likes INTEGER NOT NULL DEFAULT 0,
            comments INTEGER NOT NULL DEFAULT 0,
            watch_minutes REAL NOT NULL DEFAULT 0,
            estimated_revenue REAL,
            average_view_duration_seconds REAL,
            average_view_percentage REAL,
            country_json TEXT NOT NULL DEFAULT '{}',
            FOREIGN KEY(channel_id) REFERENCES channels(id)
        );
        CREATE TABLE IF NOT EXISTS strategy_plans (
            id TEXT PRIMARY KEY,
            channel_id TEXT NOT NULL,
            created_at TEXT NOT NULL,
            plan_json TEXT NOT NULL,
            FOREIGN KEY(channel_id) REFERENCES channels(id)
        );
        CREATE INDEX IF NOT EXISTS idx_strategy_channel_created ON strategy_plans(channel_id, created_at);
        """)
        # Small in-place migrations keep existing local MVP databases usable.
        analytics_columns = {row["name"] for row in c.execute("PRAGMA table_info(analytics_snapshots)")}
        if "average_view_duration_seconds" not in analytics_columns:
            c.execute("ALTER TABLE analytics_snapshots ADD COLUMN average_view_duration_seconds REAL")
        if "average_view_percentage" not in analytics_columns:
            c.execute("ALTER TABLE analytics_snapshots ADD COLUMN average_view_percentage REAL")
        existing = c.execute("SELECT COUNT(*) FROM channels").fetchone()[0]
        if not existing:
            # Keep the U.S. pilot intact; reserve the unused second slot for the distinct India/hi-IN gaming workflow.
            defaults = [
                ("Pilot Channel", "Selected by the Market Scout", "US", "en-US", "Shorts + long-form tests"),
                ("GTA VI Hinglish Clips · draft", "GTA VI gameplay clips with original Hindi/Hinglish commentary", "IN", "hi-IN", "YouTube Shorts"),
                ("Channel Slot 03", "Not selected yet", "US", "en-US", "Shorts + long-form tests"),
            ]
            for idx, (name, niche, country, language, format_name) in enumerate(defaults, start=1):
                c.execute(
                    "INSERT INTO channels(id,name,niche,audience_country,language,format,active,created_at) VALUES(?,?,?,?,?,?,?,?)",
                    (f"ch-{idx}", name, niche, country, language, format_name, 1, now_iso()),
                )


def list_channels() -> list[dict[str, Any]]:
    with get_db() as c:
        return [dict(r) for r in c.execute("SELECT * FROM channels ORDER BY id")]


def get_channel(channel_id: str) -> dict[str, Any] | None:
    with get_db() as c:
        row = c.execute("SELECT * FROM channels WHERE id=?", (channel_id,)).fetchone()
        return dict(row) if row else None


def update_channel(channel_id: str, values: dict[str, Any]) -> dict[str, Any] | None:
    allowed = {"name", "niche", "audience_country", "language", "format", "active"}
    fields = [(k, v) for k, v in values.items() if k in allowed]
    if not fields:
        return get_channel(channel_id)
    assignments = ",".join(f"{k}=?" for k, _ in fields)
    with get_db() as c:
        c.execute(f"UPDATE channels SET {assignments} WHERE id=?", [v for _, v in fields] + [channel_id])
    return get_channel(channel_id)


def save_scan(mode: str, candidates: list[dict], notes: str) -> dict:
    import uuid
    scan_id = uuid.uuid4().hex[:12]
    created = now_iso()
    with get_db() as c:
        c.execute("INSERT INTO scans(id,mode,created_at,notes,candidates_json) VALUES(?,?,?,?,?)",
                  (scan_id, mode, created, notes, json.dumps(candidates)))
    return {"id": scan_id, "mode": mode, "created_at": created, "notes": notes, "candidates": candidates}


def latest_scan() -> dict | None:
    with get_db() as c:
        row = c.execute("SELECT * FROM scans ORDER BY created_at DESC LIMIT 1").fetchone()
    if not row:
        return None
    return {"id": row["id"], "mode": row["mode"], "created_at": row["created_at"],
            "notes": row["notes"], "candidates": json.loads(row["candidates_json"])}


def create_job(job: dict[str, Any]) -> dict[str, Any]:
    created = now_iso()
    with get_db() as c:
        c.execute("""INSERT INTO jobs(id,channel_id,title,topic,niche,format,status,stage,package_path,
                  rights_status,created_at,updated_at,data_json)
                  VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                  (job["id"], job["channel_id"], job["title"], job["topic"], job["niche"],
                   job["format"], job.get("status", "draft"), job.get("stage", "scripted"),
                   job["package_path"], job.get("rights_status", "uncleared"), created, created,
                   json.dumps(job.get("data", {}))))
    return get_job(job["id"])


def _job_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if not row:
        return None
    result = dict(row)
    result["has_audio"] = bool(result["has_audio"])
    result["human_approved"] = bool(result["human_approved"])
    try:
        result["data"] = json.loads(result.pop("data_json") or "{}")
    except json.JSONDecodeError:
        result["data"] = {}
    return result


def get_job(job_id: str) -> dict[str, Any] | None:
    with get_db() as c:
        return _job_dict(c.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone())


def list_jobs(limit: int = 50) -> list[dict[str, Any]]:
    with get_db() as c:
        rows = c.execute("SELECT * FROM jobs ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
    return [_job_dict(r) for r in rows]


def update_job(job_id: str, **values: Any) -> dict[str, Any] | None:
    allowed = {"title", "topic", "niche", "format", "status", "stage", "video_path", "has_audio",
               "rights_status", "rights_evidence", "human_approved", "scheduled_at", "youtube_video_id", "error"}
    fields = [(k, int(v) if k in {"has_audio", "human_approved"} else v)
              for k, v in values.items() if k in allowed]
    if "data" in values:
        fields.append(("data_json", json.dumps(values["data"])))
    if not fields:
        return get_job(job_id)
    fields.append(("updated_at", now_iso()))
    assignments = ",".join(f"{k}=?" for k, _ in fields)
    with get_db() as c:
        c.execute(f"UPDATE jobs SET {assignments} WHERE id=?", [v for _, v in fields] + [job_id])
    return get_job(job_id)


def save_analytics(channel_id: str, video_id: str, values: dict[str, Any]) -> None:
    with get_db() as c:
        c.execute("""INSERT INTO analytics_snapshots(channel_id,video_id,snapshot_date,views,likes,comments,
                  watch_minutes,estimated_revenue,average_view_duration_seconds,average_view_percentage,country_json)
                  VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
                  (channel_id, video_id, values.get("date", now_iso()[:10]), int(values.get("views", 0)),
                   int(values.get("likes", 0)), int(values.get("comments", 0)), float(values.get("watch_minutes", 0)),
                   values.get("estimated_revenue"), values.get("average_view_duration_seconds"),
                   values.get("average_view_percentage"), json.dumps(values.get("countries", {}))))


def recent_analytics(limit: int = 30) -> list[dict[str, Any]]:
    with get_db() as c:
        rows = c.execute("SELECT * FROM analytics_snapshots ORDER BY snapshot_date DESC, id DESC LIMIT ?", (limit,)).fetchall()
    return [dict(r) for r in rows]


def save_strategy_plan(channel_id: str, plan: dict[str, Any]) -> dict[str, Any]:
    import uuid
    plan_id = uuid.uuid4().hex[:12]
    created = now_iso()
    with get_db() as c:
        c.execute("INSERT INTO strategy_plans(id,channel_id,created_at,plan_json) VALUES(?,?,?,?)",
                  (plan_id, channel_id, created, json.dumps(plan, ensure_ascii=False)))
    return {"id": plan_id, "channel_id": channel_id, "created_at": created, "plan": plan}


def latest_strategy_plan(channel_id: str) -> dict[str, Any] | None:
    with get_db() as c:
        row = c.execute("SELECT * FROM strategy_plans WHERE channel_id=? ORDER BY created_at DESC LIMIT 1",
                         (channel_id,)).fetchone()
    if not row:
        return None
    try:
        plan = json.loads(row["plan_json"])
    except json.JSONDecodeError:
        plan = {}
    return {"id": row["id"], "channel_id": row["channel_id"], "created_at": row["created_at"], "plan": plan}
