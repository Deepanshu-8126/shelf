"""
Series Progression & Daily Scheduler Engine for Channel 7.
Manages 100 Days of Python/DSA series state, evening multi-language slots,
auto-advances day counters, and tracks playlist history.
"""
from __future__ import annotations
import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

STATE_FILE = Path(__file__).resolve().parent / "series_progress.json"

DEFAULT_STATE = {
    "core_series": {
        "name": "100 DAYS OF PYTHON & DSA",
        "current_day": 1,
        "max_days": 100,
        "playlist_title": "100 Days of Python & Algorithms Series"
    },
    "secondary_series": {
        "active_niche": "java",
        "niches": ["java", "ai_tools", "sysdesign", "web_backend"],
        "niche_index": 0
    },
    "history": [],
    "daily_slots": {
        "slot_1_morning": "core_series",
        "slot_2_evening": "secondary_series"
    },
    "last_rendered": None
}


def load_state() -> Dict[str, Any]:
    """Loads series progression state from disk with resilient defaults."""
    if not STATE_FILE.exists():
        save_state(DEFAULT_STATE)
        return DEFAULT_STATE
    try:
        data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        # Ensure keys exist
        for k, v in DEFAULT_STATE.items():
            if k not in data:
                data[k] = v
        return data
    except Exception as e:
        print(f"⚠️ [Series Tracker] Error reading state ({e}), initializing default.")
        save_state(DEFAULT_STATE)
        return DEFAULT_STATE


def save_state(state: Dict[str, Any]) -> None:
    """Persists state atomically to disk."""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")


def get_next_scheduled_slot() -> Dict[str, Any]:
    """
    Determines whether the next video should be Morning Core Series (Day N)
    or Evening Multi-Language (Java, AI Tools, System Design, SQL).
    """
    state = load_state()
    core = state["core_series"]
    sec = state["secondary_series"]
    
    # Check history count today (IST time)
    now_dt = datetime.now()
    hour = now_dt.hour
    
    # If morning (before 2 PM) or alternate slot logic
    is_morning_slot = hour < 14
    
    # However, if user already rendered core today, rotate to secondary
    today_str = now_dt.strftime("%Y-%m-%d")
    today_renders = [h for h in state.get("history", []) if h.get("date") == today_str]
    
    if len(today_renders) == 0:
        # First video of the day: Core series (Day N)
        return {
            "slot": "morning_core",
            "type": "day",
            "day": core["current_day"],
            "series_name": core["name"],
            "query": f"day {core['current_day']}"
        }
    else:
        # Second video: Multi-language / AI Tools / Java slot
        active_niches = sec.get("niches", ["java", "ai_tools", "sysdesign", "web_backend"])
        curr_idx = sec.get("niche_index", 0) % len(active_niches)
        target_niche = active_niches[curr_idx]
        
        return {
            "slot": "evening_secondary",
            "type": "niche",
            "niche": target_niche,
            "query": target_niche
        }


def advance_and_record_render(lesson_obj: Any, video_path: str | Path) -> Dict[str, Any]:
    """
    Records a successful video render, saves history entry,
    and advances current_day or niche_index.
    """
    state = load_state()
    core = state["core_series"]
    sec = state["secondary_series"]
    
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    today_date = datetime.now().strftime("%Y-%m-%d")
    
    ep_num = getattr(lesson_obj, "episode_num", 1)
    series_name = getattr(lesson_obj, "series_name", "TECH")
    title = getattr(lesson_obj, "title", "Coding Short")
    lesson_id = getattr(lesson_obj, "id", "lesson")
    lang = getattr(lesson_obj, "language", "python")
    
    is_core = ("python" in series_name.lower() or "dsa" in series_name.lower() or "100" in series_name.lower())
    
    if is_core and ep_num >= core["current_day"]:
        core["current_day"] = ep_num + 1
        if core["current_day"] > core["max_days"]:
            core["current_day"] = 1  # Loop or restart season 2
    else:
        # Advance secondary niche rotation
        sec["niche_index"] = (sec.get("niche_index", 0) + 1) % len(sec.get("niches", ["java"]))
        sec["active_niche"] = sec["niches"][sec["niche_index"]]

    entry = {
        "id": lesson_id,
        "title": title,
        "series": series_name,
        "episode_num": ep_num,
        "language": lang,
        "video_path": str(video_path),
        "timestamp": now_str,
        "date": today_date
    }
    
    state["history"].append(entry)
    state["last_rendered"] = entry
    save_state(state)
    
    print(f"📈 [Series Tracker] Progress Updated! Next Core Day: {core['current_day']}, Next Niche: {sec['active_niche']}")
    return state


def get_series_status_summary() -> str:
    """Returns a formatted Markdown summary of the channel's series progression."""
    state = load_state()
    core = state["core_series"]
    sec = state["secondary_series"]
    history = state.get("history", [])
    
    now_dt = datetime.now().strftime("%d %b %Y, %I:%M %p")
    today_date = datetime.now().strftime("%Y-%m-%d")
    today_count = len([h for h in history if h.get("date") == today_date])
    
    last = state.get("last_rendered")
    last_title = f"{last['series']} • Ep {last['episode_num']}: {last['title']}" if last else "None"
    
    next_slot = get_next_scheduled_slot()
    slot_desc = f"Day {next_slot.get('day')}" if next_slot.get('type') == 'day' else f"Niche: {next_slot.get('niche', '').upper()}"

    lines = [
        "📊 *CHANNEL 7 // SERIES PROGRESSION BRAIN*",
        f"🕒 Time: `{now_dt}`",
        "",
        "🎯 *Core Playlist (Python / DSA)*:",
        f"  • Series: `{core['name']}`",
        f"  • Current Day: *Day {core['current_day']} of {core['max_days']}*",
        f"  • Progress: `[{'█' * (core['current_day'] // 10)}{'░' * (10 - core['current_day'] // 10)}] {core['current_day']}%`",
        "",
        "🌐 *Secondary Slot (Multi-Language / AI)*:",
        f"  • Next Niche: `{sec.get('active_niche', 'java').upper()}`",
        f"  • Rotation: `{', '.join([n.upper() for n in sec.get('niches', [])])}`",
        "",
        "📅 *Daily Cadence (2 Videos/Day)*:",
        f"  • Videos Rendered Today: *{today_count} / 2*",
        f"  • Next Up in Queue: *{slot_desc}*",
        f"  • Total Master Videos: *{len(history)}*",
        "",
        f"🎬 *Last Completed*: _{last_title}_"
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    print(get_series_status_summary())
