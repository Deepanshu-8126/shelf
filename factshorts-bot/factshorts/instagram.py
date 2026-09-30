"""Instagram Reels publishing (official Instagram Content Publishing API).

Flow (all official, no browser automation):
  1. POST {host}/{ig-user-id}/media           -> container id (media_type=REELS)
     * mode "resumable": upload_type=resumable, then push the mp4 bytes to
       rupload.facebook.com (needs an app set up with *Facebook Login for Business*)
     * mode "url":       video_url=<public https url>  (works with Instagram Login apps,
       but you must host the mp4 somewhere public - see docs/INSTAGRAM_SETUP.md)
  2. poll GET /{container-id}?fields=status_code until FINISHED
  3. POST /{ig-user-id}/media_publish?creation_id=<container-id>

Requirements you must set up once (documented in docs/INSTAGRAM_SETUP.md):
  * Instagram **Business or Creator** account (personal accounts cannot publish via API)
  * a Meta app with the instagram_content_publish permission (or instagram_business_content_publish)
  * IG_USER_ID + IG_ACCESS_TOKEN in .env, token refreshed every ~60 days

Reel specs enforced by Instagram (our renders are already inside them):
  3 s - 15 min, 9:16 recommended, H.264, AAC <= 48 kHz, <= 300 MB, VBR <= 25 Mbps.
"""
from __future__ import annotations

import asyncio
import json
import time
from pathlib import Path

import httpx

from . import db
from .config import Config, get_config
from .utils import module_logger

log = module_logger("instagram")

GRAPH_FACEBOOK = "https://graph.facebook.com"
GRAPH_INSTAGRAM = "https://graph.instagram.com"
RUPLOAD = "https://rupload.facebook.com/ig-api-upload/{version}/{container}"

STATUS_OK = {"FINISHED", "PUBLISHED"}
STATUS_BAD = {"ERROR", "EXPIRED"}


class InstagramError(RuntimeError):
    pass


def is_configured(cfg: Config | None = None) -> bool:
    cfg = cfg or get_config()
    return bool(cfg.ig_user_id and cfg.ig_access_token)


def _host(cfg: Config) -> str:
    return GRAPH_INSTAGRAM if cfg.ig_graph_host == "graph.instagram.com" else GRAPH_FACEBOOK


def _url(cfg: Config, path: str) -> str:
    return f"{_host(cfg)}/{cfg.ig_graph_version}/{path.lstrip('/')}"


def _error(resp: httpx.Response) -> str:
    try:
        payload = resp.json()
        err = payload.get("error") or {}
        msg = err.get("message") or resp.text[:200]
        code = err.get("code")
        sub = err.get("error_subcode")
        hint = ""
        if "publish" in str(msg).lower() and "permission" in str(msg).lower():
            hint = " (check the instagram_content_publish permission and that the account is Business/Creator)"
        return f"Instagram API HTTP {resp.status_code}: {msg} [code={code} subcode={sub}]{hint}"
    except Exception:  # noqa: BLE001
        return f"Instagram API HTTP {resp.status_code}: {resp.text[:200]}"


# ---------------------------------------------------------------- API building blocks
async def create_container(
    cfg: Config,
    caption: str,
    video_url: str | None = None,
    resumable: bool = False,
) -> dict:
    params = {
        "media_type": "REELS",
        "caption": caption[:2200],
        "share_to_feed": "true" if cfg.ig_share_to_feed else "false",
        "access_token": cfg.ig_access_token,
    }
    if resumable:
        params["upload_type"] = "resumable"
    elif video_url:
        params["video_url"] = video_url
    else:
        raise InstagramError("either video_url or resumable=True is required")
    async with httpx.AsyncClient(timeout=httpx.Timeout(90.0)) as client:
        resp = await client.post(_url(cfg, f"{cfg.ig_user_id}/media"), params=params)
        if resp.status_code >= 400:
            raise InstagramError(_error(resp))
        data = resp.json()
    if not data.get("id"):
        raise InstagramError(f"container creation returned no id: {data}")
    log.info("IG container created: %s (resumable=%s)", data["id"], resumable)
    return data


async def upload_container_bytes(cfg: Config, container: dict, path: Path) -> None:
    """Push the video bytes into a resumable container."""
    uri = container.get("uri") or RUPLOAD.format(version=cfg.ig_graph_version, container=container["id"])
    size = path.stat().st_size
    headers = {
        "Authorization": f"OAuth {cfg.ig_access_token}",
        "offset": "0",
        "file_size": str(size),
        "Content-Type": "application/octet-stream",
    }
    async with httpx.AsyncClient(timeout=httpx.Timeout(600.0, connect=30.0)) as client:
        with open(path, "rb") as fh:
            resp = await client.post(uri, headers=headers, content=fh.read())
        if resp.status_code >= 400:
            raise InstagramError(_error(resp))
    log.info("IG upload finished: %s (%d bytes)", container.get("id"), size)


async def wait_for_container(cfg: Config, container_id: str, timeout: int = 600, interval: float = 5.0) -> str:
    """Poll the container until Instagram finishes processing."""
    deadline = time.monotonic() + timeout
    last = ""
    async with httpx.AsyncClient(timeout=30.0) as client:
        while time.monotonic() < deadline:
            resp = await client.get(
                _url(cfg, container_id),
                params={"fields": "status_code,status", "access_token": cfg.ig_access_token},
            )
            if resp.status_code >= 400:
                raise InstagramError(_error(resp))
            data = resp.json()
            last = str(data.get("status_code") or "")
            if last in STATUS_OK:
                log.info("IG container %s ready (%s)", container_id, last)
                return last
            if last in STATUS_BAD:
                raise InstagramError(f"Instagram could not process the video: {data.get('status') or last}")
            await asyncio.sleep(interval)
    raise InstagramError(f"timed out waiting for Instagram to process the video (last status: {last})")


async def publish_container(cfg: Config, container_id: str) -> str:
    async with httpx.AsyncClient(timeout=httpx.Timeout(120.0)) as client:
        resp = await client.post(
            _url(cfg, f"{cfg.ig_user_id}/media_publish"),
            params={"creation_id": container_id, "access_token": cfg.ig_access_token},
        )
        if resp.status_code >= 400:
            raise InstagramError(_error(resp))
        media_id = (resp.json() or {}).get("id", "")
    if not media_id:
        raise InstagramError("publish returned no media id")
    log.info("IG reel published: %s", media_id)
    return media_id


async def publishing_limit(cfg: Config) -> dict:
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(
            _url(cfg, f"{cfg.ig_user_id}/content_publishing_limit"),
            params={"fields": "quota_usage,config", "access_token": cfg.ig_access_token},
        )
        if resp.status_code >= 400:
            raise InstagramError(_error(resp))
        data = (resp.json() or {}).get("data") or [{}]
    return data[0]


async def account_info(cfg: Config) -> dict:
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(
            _url(cfg, "me"), params={"fields": "id,username,account_type", "access_token": cfg.ig_access_token}
        )
        if resp.status_code >= 400:
            raise InstagramError(_error(resp))
        return resp.json()


# ------------------------------------------------------------------- public API
def caption_for(video: dict, cfg: Config | None = None) -> str:
    """Instagram caption: hook + fact + soft hashtags + source credit (no links - IG kills them)."""
    cfg = cfg or get_config()
    parts: list[str] = []
    meta = {}
    try:
        meta = json.loads(video.get("meta") or "{}")
    except Exception:  # noqa: BLE001
        meta = {}
    script = (meta.get("script") or {}).get("full_text") or ""
    fact = (meta.get("script") or {}).get("body") or script
    hook = video.get("hook") or ""

    if hook:
        parts.append(hook.strip())
    if fact:
        parts.append(fact.strip())
    if video.get("source_url") and cfg.cite_source:
        parts.append(f"Source: {video.get('source_name') or 'source'} → {video['source_url']}")

    hashtags = []
    try:
        hashtags = json.loads(video.get("tags") or "[]")
    except Exception:  # noqa: BLE001
        hashtags = []
    niche = video.get("niche") or "facts"
    base_tags = [f"#{niche}", "#facts", "#didyouknow", "#reels", "#learnoninstagram"]
    extra = ["#" + t.replace(" ", "").replace("-", "") for t in hashtags[:4] if t]
    tags = base_tags + extra
    seen, clean = set(), []
    for tag in tags:
        if tag.lower() not in seen:
            seen.add(tag.lower())
            clean.append(tag)
    parts.append(" ".join(clean[: cfg.ig_hashtag_limit]))
    if cfg.yt_synthetic_disclosure:
        parts.append("Voice: synthetic narration.")
    return "\n\n".join(p for p in parts if p)[:2200]


async def upload_reel(video_id: int, cfg: Config | None = None, dry_run: bool = False) -> dict:
    """Publish a rendered video to Instagram as a Reel. Returns {ig_media_id, url, mode}."""
    cfg = cfg or get_config()
    row = db.get_video(video_id)
    if not row:
        raise InstagramError(f"video #{video_id} not found")
    path = Path(row.get("video_path") or "")
    if not path.exists():
        raise InstagramError(f"file missing on disk: {path}")

    if dry_run or cfg.dry_run:
        log.info("[dry-run] would publish #%s to Instagram as a Reel", video_id)
        return {"ig_media_id": "dry-run", "url": "", "mode": cfg.ig_upload_mode, "dry_run": True}

    if not is_configured(cfg):
        raise InstagramError(
            "Instagram is not configured. Set IG_USER_ID and IG_ACCESS_TOKEN in .env "
            "(see docs/INSTAGRAM_SETUP.md)."
        )

    caption = caption_for(row, cfg)
    mode = cfg.ig_upload_mode
    video_url = None
    if mode == "url":
        if not cfg.ig_public_base_url:
            raise InstagramError(
                "IG_UPLOAD_MODE=url needs IG_PUBLIC_BASE_URL pointing at a public host for the mp4 "
                "(or switch to IG_UPLOAD_MODE=resumable)."
            )
        video_url = cfg.ig_public_base_url.rstrip("/") + "/" + path.name

    container = await create_container(cfg, caption, video_url=video_url, resumable=(mode != "url"))
    if mode != "url":
        await upload_container_bytes(cfg, container, path)
    await wait_for_container(cfg, container["id"])
    media_id = await publish_container(cfg, container["id"])

    db.update_video(
        video_id,
        ig_media_id=media_id,
        status=row.get("status") if row.get("status") == "uploaded" else "uploaded",
        uploaded_at=row.get("uploaded_at") or None,
    )
    log.info("#%s published to Instagram (%s)", video_id, media_id)
    return {
        "ig_media_id": media_id,
        "url": f"https://www.instagram.com/reel/{media_id}/",
        "mode": mode,
        "caption_chars": len(caption),
    }


if __name__ == "__main__":  # python -m factshorts.instagram --check
    import argparse

    parser = argparse.ArgumentParser(description="Instagram Reels helper")
    parser.add_argument("--check", action="store_true", help="verify token, account type and publish quota")
    args = parser.parse_args()
    cfg = get_config()
    if not is_configured(cfg):
        print("IG_USER_ID / IG_ACCESS_TOKEN missing. See docs/INSTAGRAM_SETUP.md")
        raise SystemExit(1)

    async def main() -> None:
        info = await account_info(cfg)
        print("account:", info)
        print("publish quota:", await publishing_limit(cfg))

    if args.check:
        asyncio.run(main())
    else:
        parser.print_help()
