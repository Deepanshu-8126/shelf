"""YouTube upload with OAuth (YouTube Data API v3).

Highlights
----------
* Resumable upload with retry + exponential backoff.
* Honest `status.containsSyntheticMedia = true` (the narration is synthetic TTS).
* Optional scheduled publishing via `status.publishAt` (requires privacyStatus=private).
* Daily upload cap so the default 10,000 units/day quota is never blown
  (videos.insert costs ~1600 units -> ~6 uploads/day).
* Posts the "pinned comment" text (the API cannot pin; Telegram preview tells you to pin it).
* Clear error messages for the two classic blockers: quota exceeded, and the
  "unverified API project -> uploads locked to private" audit requirement.

Run `python main.py --auth` once to complete the OAuth consent and cache token.json.
"""
from __future__ import annotations

import asyncio
import socket
from datetime import datetime, timedelta, timezone
from pathlib import Path

from . import db
from .config import Config, get_config
from .utils import module_logger

log = module_logger("uploader")

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.force-ssl",  # needed to post the first comment
]


class UploadError(RuntimeError):
    pass


GOOGLE_MODULES = (
    "google.auth.transport.requests",
    "google.oauth2.credentials",
    "google_auth_oauthlib.flow",
    "googleapiclient.discovery",
    "googleapiclient.errors",
    "googleapiclient.http",
)


def _import_google() -> None:
    """Fail early with a copy-pasteable fix when the Google libs are missing."""
    import importlib.util

    missing: list[str] = []
    for module in GOOGLE_MODULES:
        try:
            if importlib.util.find_spec(module) is None:
                missing.append(module)
        except ModuleNotFoundError:
            missing.append(module)
    if missing:
        raise UploadError(
            "Google API libraries are missing (" + ", ".join(missing) + "). Install them with:\n"
            "  pip install google-api-python-client google-auth-oauthlib google-auth-httplib2"
        )


def credentials_present(cfg: Config | None = None) -> bool:
    cfg = cfg or get_config()
    return cfg.yt_client_secrets.exists()


def is_authenticated(cfg: Config | None = None) -> bool:
    cfg = cfg or get_config()
    return cfg.yt_token_file.exists()


def run_oauth_flow(cfg: Config | None = None, port: int = 0) -> Path:
    """Interactive OAuth. Runs a local server on a free port; falls back to console."""
    cfg = cfg or get_config()
    _import_google()
    from google_auth_oauthlib.flow import InstalledAppFlow

    if not cfg.yt_client_secrets.exists():
        raise UploadError(
            f"YouTube client secrets not found at {cfg.yt_client_secrets}.\n"
            "Create an OAuth 'Desktop app' client in Google Cloud Console and save the JSON there."
        )
    flow = InstalledAppFlow.from_client_secrets_file(str(cfg.yt_client_secrets), SCOPES)

    def free_port() -> int:
        with socket.socket() as s:
            s.bind(("127.0.0.1", 0))
            return s.getsockname()[1]

    try:
        creds = flow.run_local_server(port=port or free_port(), prompt="consent", open_browser=True)
    except Exception as exc:  # noqa: BLE001 - headless servers
        log.warning("local server OAuth failed (%s) - falling back to console flow", exc)
        creds = flow.run_console()
    cfg.yt_token_file.parent.mkdir(parents=True, exist_ok=True)
    cfg.yt_token_file.write_text(creds.to_json(), encoding="utf-8")
    log.info("OAuth token saved to %s", cfg.yt_token_file)
    return cfg.yt_token_file


def get_service(cfg: Config | None = None, interactive: bool = False):
    """Return an authenticated YouTube client, refreshing the token when possible."""
    cfg = cfg or get_config()
    _import_google()
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build

    creds = None
    if cfg.yt_token_file.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(cfg.yt_token_file), SCOPES)
        except Exception as exc:  # noqa: BLE001
            log.warning("could not read token (%s)", exc)
    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            cfg.yt_token_file.write_text(creds.to_json(), encoding="utf-8")
        except Exception as exc:  # noqa: BLE001
            log.warning("token refresh failed: %s", exc)
            creds = None
    if (not creds or not creds.valid) and interactive:
        run_oauth_flow(cfg)
        creds = Credentials.from_authorized_user_file(str(cfg.yt_token_file), SCOPES)
    if not creds or not creds.valid:
        raise UploadError(
            "Not authenticated with YouTube. Run once:  python main.py --auth"
        )
    return build("youtube", "v3", credentials=creds, cache_discovery=False)


def uploads_today(cfg: Config | None = None) -> int:
    cfg = cfg or get_config()
    return db.count_videos_since(["uploaded", "scheduled"], hours=24)


def quota_left(cfg: Config | None = None) -> int:
    cfg = cfg or get_config()
    return max(0, cfg.yt_max_uploads_per_day - uploads_today(cfg))


def _friendly_error(exc: Exception) -> str:
    text = str(exc)
    if "quotaExceeded" in text or "uploadLimitExceeded" in text:
        return ("YouTube API quota exceeded for today. The default project quota allows about "
                "6 uploads/day (1600 units each). Try again after midnight Pacific Time.")
    if "insufficientPermissions" in text or "insufficient authentication scopes" in text:
        return "Token is missing scopes. Delete credentials/token.json and run: python main.py --auth"
    if "invalid_grant" in text:
        return "OAuth token expired/revoked. Delete credentials/token.json and run: python main.py --auth"
    if "forbidden" in text.lower():
        return f"YouTube refused the request (403): {text[:300]}"
    return text[:600]


async def upload_video(
    video_id: int,
    cfg: Config | None = None,
    privacy: str | None = None,
    publish_at: datetime | None = None,
    dry_run: bool = False,
) -> dict:
    """Upload a rendered video by DB id. Returns {yt_video_id, url, privacy, status}."""
    cfg = cfg or get_config()
    row = db.get_video(video_id)
    if not row:
        raise UploadError(f"video #{video_id} not found in the database")
    path = Path(row.get("video_path") or "")
    if not path.exists():
        raise UploadError(f"file missing on disk: {path}")

    if dry_run or cfg.dry_run:
        log.info("[dry-run] would upload #%s (%s)", video_id, path.name)
        return {"yt_video_id": "dry-run", "url": "", "privacy": "unset", "dry_run": True}

    left = quota_left(cfg)
    if left <= 0:
        raise UploadError(
            f"daily upload limit reached ({cfg.yt_max_uploads_per_day}). "
            "Increase MAX_UPLOADS_PER_DAY only if your quota really allows it."
        )

    title = (row.get("title") or "Amazing fact").strip()[:100]
    description = (row.get("description") or "").strip()[:4900]
    tags = []
    try:
        import json

        tags = json.loads(row.get("tags") or "[]")
    except Exception:  # noqa: BLE001
        tags = []

    privacy = privacy or cfg.yt_privacy
    if publish_at is not None:
        privacy = "private"  # required by the API when publishAt is set

    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags[:15],
            "categoryId": cfg.yt_category_id,
            "defaultLanguage": "en",
        },
        "status": {
            "privacyStatus": privacy,
            "selfDeclaredMadeForKids": cfg.yt_made_for_kids,
            "license": "youtube",
            "embeddable": True,
        },
    }
    if cfg.yt_synthetic_disclosure:
        # The voice is synthetic TTS; disclosing is required by YouTube's A/S policy
        body["status"]["containsSyntheticMedia"] = True
    if publish_at is not None:
        body["status"]["publishAt"] = publish_at.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    def _do_upload() -> dict:
        from googleapiclient.errors import HttpError
        from googleapiclient.http import MediaFileUpload

        service = get_service(cfg)
        media = MediaFileUpload(str(path), chunksize=4 * 1024 * 1024, resumable=True, mimetype="video/mp4")
        request = service.videos().insert(part="snippet,status", body=body, media_body=media)
        response = None
        retries = 0
        while response is None:
            try:
                status, response = request.next_chunk()
                if status:
                    log.info("#%s upload progress: %d%%", video_id, int(status.progress() * 100))
            except HttpError as exc:  # retryable?
                code = getattr(exc.resp, "status", 0)
                retries += 1
                if code in (500, 502, 503, 504, 429) and retries <= cfg.yt_upload_retries:
                    import time as _time

                    wait = min(60, 2 ** retries)
                    log.warning("upload chunk failed (%s), retrying in %ss", code, wait)
                    _time.sleep(wait)
                    continue
                raise
            except Exception as exc:  # noqa: BLE001
                retries += 1
                if retries <= cfg.yt_upload_retries:
                    import time as _time

                    log.warning("upload error: %s - retrying", exc)
                    _time.sleep(3 * retries)
                    continue
                raise
        return response

    try:
        response = await asyncio.to_thread(_do_upload)
    except Exception as exc:  # noqa: BLE001
        msg = _friendly_error(exc)
        log.error("#%s upload failed: %s", video_id, msg)
        db.update_video(video_id, status="upload_failed", error=msg)
        raise UploadError(msg) from exc

    yt_id = response.get("id", "")
    url = f"https://youtube.com/shorts/{yt_id}" if yt_id else ""
    status = "scheduled" if publish_at is not None else "uploaded"
    db.update_video(
        video_id,
        status=status,
        yt_video_id=yt_id,
        publish_at=publish_at.isoformat() if publish_at else None,
        uploaded_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        error=None,
    )
    log.info("#%s uploaded -> %s (%s)", video_id, url, privacy)

    # first comment (the API cannot pin; the Telegram message reminds you to pin it)
    if row.get("pinned_comment") and yt_id:
        try:
            await asyncio.to_thread(_post_comment, cfg, yt_id, row["pinned_comment"])
        except Exception as exc:  # noqa: BLE001
            log.warning("could not post the first comment: %s", exc)

    return {
        "yt_video_id": yt_id,
        "url": url,
        "privacy": privacy,
        "publish_at": body["status"].get("publishAt"),
        "status": status,
        "synthetic_disclosure": bool(body["status"].get("containsSyntheticMedia")),
        "quota_left": quota_left(cfg),
    }


def _post_comment(cfg: Config, yt_video_id: str, text: str) -> None:
    service = get_service(cfg)
    service.commentThreads().insert(
        part="snippet",
        body={
            "snippet": {
                "videoId": yt_video_id,
                "topLevelComment": {"snippet": {"textOriginal": text[:9000]}},
            }
        },
    ).execute()
    log.info("first comment posted on %s", yt_video_id)


def schedule_next_slot(cfg: Config | None = None, minutes_ahead: int = 5) -> datetime:
    """Small helper: publish time a few minutes from now (YouTube needs a future time)."""
    cfg = cfg or get_config()
    return datetime.now(timezone.utc) + timedelta(minutes=minutes_ahead)


if __name__ == "__main__":  # tiny CLI: python -m factshorts.uploader --auth
    import argparse

    parser = argparse.ArgumentParser(description="FactShorts YouTube auth helper")
    parser.add_argument("--auth", action="store_true", help="run the OAuth consent flow")
    parser.add_argument("--status", action="store_true", help="show auth/quota status")
    args = parser.parse_args()
    cfg = get_config()
    if args.auth:
        run_oauth_flow(cfg)
        print("Token saved:", cfg.yt_token_file)
    elif args.status:
        print("client_secret.json:", "found" if credentials_present(cfg) else "MISSING")
        print("token.json       :", "found" if is_authenticated(cfg) else "MISSING")
        print("uploads in 24h   :", uploads_today(cfg), f"(cap {cfg.yt_max_uploads_per_day})")
    else:
        parser.print_help()
