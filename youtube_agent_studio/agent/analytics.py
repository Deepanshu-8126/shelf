from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
from typing import Any

from .config import ROOT
from .db import get_channel, save_analytics


def fetch_video_analytics(channel_id: str, video_id: str, start_date: str | None = None, end_date: str | None = None) -> dict[str, Any]:
    channel = get_channel(channel_id)
    if not channel:
        raise ValueError("Unknown channel")
    token_path = ROOT / "secrets" / "tokens" / f"{channel_id}.json"
    if not token_path.exists():
        raise RuntimeError(f"No YouTube OAuth token found for {channel['name']}")
    try:
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build
    except ImportError as exc:
        raise RuntimeError("Install YouTube API libraries from requirements.txt") from exc
    credentials = Credentials.from_authorized_user_file(str(token_path))
    if credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
        token_path.write_text(credentials.to_json(), encoding="utf-8")
    end = end_date or (date.today() - timedelta(days=2)).isoformat()
    start = start_date or (date.fromisoformat(end) - timedelta(days=27)).isoformat()
    service = build("youtubeAnalytics", "v2", credentials=credentials, cache_discovery=False)
    report = service.reports().query(
        ids="channel==MINE", startDate=start, endDate=end,
        metrics="views,estimatedRevenue,averageViewDuration,likes,comments",
        dimensions="video", filters=f"video=={video_id}",
    ).execute()
    headers = [h.get("name") for h in report.get("columnHeaders", [])]
    rows = report.get("rows", [])
    values = dict(zip(headers, rows[0])) if rows else {}
    views = int(values.get("views", 0))
    average_duration = values.get("averageViewDuration")
    average_percentage = values.get("averageViewPercentage")
    try:
        watch_minutes = (views * float(average_duration) / 60) if average_duration is not None else 0.0
    except (TypeError, ValueError):
        watch_minutes = 0.0
    result = {
        "video_id": video_id, "start_date": start, "end_date": end,
        "views": views, "estimated_revenue": values.get("estimatedRevenue"),
        "average_view_duration_seconds": average_duration,
        "average_view_percentage": average_percentage,
        "watch_minutes": round(watch_minutes, 2),
        "likes": int(values.get("likes", 0)), "comments": int(values.get("comments", 0)),
        "note": "YouTube Analytics owner-only data; revenue can be delayed and is an estimate.",
    }
    save_analytics(channel_id, video_id, {**result, "date": end})
    return result
