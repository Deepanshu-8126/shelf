"""Database layer for trend-engine: topics, performance metrics, and bandit states."""
from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path
from typing import Any


def get_db(db_path: str = "data/trendengine.db") -> sqlite3.Connection:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: str = "data/trendengine.db") -> None:
    conn = get_db(db_path)
    cur = conn.cursor()
    cur.executescript("""
    CREATE TABLE IF NOT EXISTS discovered_topics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        summary TEXT DEFAULT '',
        source TEXT NOT NULL,
        source_url TEXT DEFAULT '',
        niche TEXT DEFAULT 'science',
        score REAL DEFAULT 0.0,
        velocity REAL DEFAULT 0.0,
        fingerprint TEXT UNIQUE,
        status TEXT DEFAULT 'discovered',
        created_at REAL NOT NULL
    );

    CREATE TABLE IF NOT EXISTS scripts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        topic_id INTEGER,
        hook TEXT NOT NULL,
        body TEXT NOT NULL,
        closing TEXT NOT NULL,
        full_text TEXT NOT NULL,
        hook_style TEXT DEFAULT 'pattern_interrupt',
        cta_style TEXT DEFAULT 'loop_curiosity',
        quality_score REAL DEFAULT 0.0,
        critique_reason TEXT DEFAULT '',
        visual_keywords TEXT DEFAULT '[]',
        titles TEXT DEFAULT '[]',
        tags TEXT DEFAULT '[]',
        description TEXT DEFAULT '',
        created_at REAL NOT NULL,
        FOREIGN KEY(topic_id) REFERENCES discovered_topics(id)
    );

    CREATE TABLE IF NOT EXISTS video_metrics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        script_id INTEGER,
        youtube_video_id TEXT UNIQUE,
        views INTEGER DEFAULT 0,
        likes INTEGER DEFAULT 0,
        comments INTEGER DEFAULT 0,
        ctr REAL DEFAULT 0.0,
        retention_pct REAL DEFAULT 0.0,
        reward REAL DEFAULT 0.0,
        updated_at REAL NOT NULL,
        FOREIGN KEY(script_id) REFERENCES scripts(id)
    );

    CREATE TABLE IF NOT EXISTS bandit_arms (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        arm_type TEXT NOT NULL,
        arm_value TEXT NOT NULL,
        alpha REAL DEFAULT 1.0,
        beta REAL DEFAULT 1.0,
        UNIQUE(arm_type, arm_value)
    );

    CREATE TABLE IF NOT EXISTS scoring_weights (
        feature_name TEXT PRIMARY KEY,
        weight REAL NOT NULL,
        updated_at REAL NOT NULL
    );
    """)
    conn.commit()
    conn.close()


def save_discovered_topics(topics: list[dict[str, Any]], db_path: str = "data/trendengine.db") -> int:
    conn = get_db(db_path)
    cur = conn.cursor()
    saved = 0
    now = time.time()
    for t in topics:
        try:
            cur.execute("""
                INSERT OR IGNORE INTO discovered_topics 
                (title, summary, source, source_url, niche, score, velocity, fingerprint, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'discovered', ?)
            """, (
                t.get("title", ""),
                t.get("summary", ""),
                t.get("source", "trend"),
                t.get("source_url", ""),
                t.get("niche", "science"),
                float(t.get("score", 0.0)),
                float(t.get("velocity", 0.0)),
                t.get("fingerprint", t.get("title", "")),
                now
            ))
            if cur.rowcount > 0:
                saved += 1
        except Exception:
            continue
    conn.commit()
    conn.close()
    return saved


def get_top_topics(limit: int = 5, db_path: str = "data/trendengine.db") -> list[dict[str, Any]]:
    conn = get_db(db_path)
    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM discovered_topics 
        WHERE status = 'discovered'
        ORDER BY score DESC, created_at DESC 
        LIMIT ?
    """, (limit,))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def mark_topic_status(topic_id: int, status: str, db_path: str = "data/trendengine.db") -> None:
    conn = get_db(db_path)
    cur = conn.cursor()
    cur.execute("UPDATE discovered_topics SET status = ? WHERE id = ?", (status, topic_id))
    conn.commit()
    conn.close()
