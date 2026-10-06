from __future__ import annotations

from pathlib import Path
from typing import Any

from .config import ROOT, env
from .db import get_channel, get_job, update_job
from .policy import publish_blockers, safe_privacy


class PublishBlocked(RuntimeError):
    def __init__(self, blockers: list[str]):
        self.blockers = blockers
        super().__init__("Publication blocked: " + "; ".join(blockers))


def publish_job(job_id: str, requested_privacy: str | None = None, automated: bool = False) -> dict[str, Any]:
    job = get_job(job_id)
    if not job:
        raise ValueError("Unknown job")
    blockers = publish_blockers(job, automated=automated)
    if blockers:
        raise PublishBlocked(blockers)
    channel = get_channel(job["channel_id"])
    token_path = ROOT / "secrets" / "tokens" / f"{channel['id']}.json"
    video_path = Path(job["video_path"])
    if ROOT not in video_path.resolve().parents:
        raise PublishBlocked(["Video path is outside the local project output folder."])
    try:
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload
    except ImportError as exc:
        raise PublishBlocked(["Install the optional YouTube API dependencies with: pip install -r requirements.txt"])
    try:
        credentials = Credentials.from_authorized_user_file(str(token_path))
        if credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
            token_path.write_text(credentials.to_json(), encoding="utf-8")
        youtube = build("youtube", "v3", credentials=credentials, cache_discovery=False)
        # Verify which signed-in channel the OAuth token can upload to.
        mine = youtube.channels().list(part="id,snippet", mine=True, maxResults=5).execute()
        owned_ids = [item.get("id") for item in mine.get("items", [])]
        expected_id = env(f"YOUTUBE_CHANNEL_ID_{channel['id'].upper().replace('-', '_')}")
        if expected_id and expected_id not in owned_ids:
            raise PublishBlocked([f"OAuth token is not authorized for expected channel {expected_id}."])
        privacy = safe_privacy(requested_privacy)
        content = job.get("data", {}).get("content", {})
        package_dir = (ROOT / job["package_path"]).resolve()
        metadata_file = package_dir / "metadata.json"
        import json
        metadata = json.loads(metadata_file.read_text(encoding="utf-8"))
        body = {
            "snippet": {
                "title": metadata.get("title", job["title"])[:100],
                "description": metadata.get("description", "")[:5000],
                "tags": metadata.get("tags", [])[:500],
                "categoryId": env("YOUTUBE_CATEGORY_ID", "27"),
                "defaultLanguage": channel["language"],
            },
            "status": {
                "privacyStatus": privacy,
                "selfDeclaredMadeForKids": False,
            },
        }
        if job.get("scheduled_at") and privacy == "private":
            body["status"]["publishAt"] = job["scheduled_at"]
        request = youtube.videos().insert(
            part="snippet,status",
            body=body,
            media_body=MediaFileUpload(str(video_path), chunksize=8 * 1024 * 1024, resumable=True),
        )
        response = None
        while response is None:
            _, response = request.next_chunk()
        video_id = response.get("id", "")
        update_job(job_id, status="published" if privacy == "public" else "uploaded_private",
                   stage="uploaded", youtube_video_id=video_id, error="")
        return {"id": video_id, "url": f"https://www.youtube.com/watch?v={video_id}", "privacy": privacy,
                "channel_ids_seen": owned_ids}
    except PublishBlocked:
        raise
    except Exception as exc:
        update_job(job_id, status="upload_failed", stage="publish_error", error=f"{type(exc).__name__}: {exc}")
        raise RuntimeError(f"YouTube upload failed: {type(exc).__name__}: {exc}") from exc
