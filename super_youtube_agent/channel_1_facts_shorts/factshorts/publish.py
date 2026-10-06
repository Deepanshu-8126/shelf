"""Multi-platform publishing: YouTube Shorts + Instagram Reels (and room for more).

A single call publishes a finished render everywhere it is configured to go, records
per-platform results in SQLite, and reports exactly what succeeded or failed so the
Telegram message can say something useful instead of "error".
"""
from __future__ import annotations

from datetime import datetime, timezone

from . import db
from .config import Config, get_config
from .instagram import InstagramError, is_configured as ig_configured, publishing_limit, upload_reel
from .uploader import UploadError, is_authenticated, upload_video
import os
import httpx
from .utils import module_logger

log = module_logger("publish")

ALL_PLATFORMS = ("youtube", "instagram", "telegram", "discord", "webhook")


def platforms_from_setting(cfg: Config | None = None) -> list[str]:
    cfg = cfg or get_config()
    stored = db.get_setting("platforms")
    raw = stored.split(",") if stored else cfg.platforms
    out = [p.strip().lower() for p in raw if p.strip()]
    return [p for p in out if p in ALL_PLATFORMS] or ["youtube"]


def platform_health(cfg: Config | None = None) -> dict[str, str]:
    """Human readable readiness of each platform (used by /status and --check)."""
    cfg = cfg or get_config()
    return {
        "youtube": "ready" if is_authenticated(cfg) else "not authorised (run: python main.py --auth)",
        "instagram": "ready" if ig_configured(cfg) else "not configured (IG_USER_ID / IG_ACCESS_TOKEN)",
        "telegram": "ready" if cfg.telegram_token and cfg.telegram_chat_id else "optional (TELEGRAM_BOT_TOKEN)",
        "discord": "ready" if os.getenv("DISCORD_WEBHOOK_URL") else "optional (DISCORD_WEBHOOK_URL)",
        "webhook": "ready" if os.getenv("PUBLISH_WEBHOOK_URL") else "optional (PUBLISH_WEBHOOK_URL)",
    }


async def publish_video(
    video_id: int,
    platforms: list[str] | None = None,
    cfg: Config | None = None,
    privacy: str | None = None,
    dry_run: bool = False,
    publish_at: datetime | None = None,
) -> dict:
    """Publish one video to every requested platform. Never raises for a single platform
    failure - each result is reported back separately."""
    cfg = cfg or get_config()
    targets = platforms or platforms_from_setting(cfg)
    results: dict[str, dict] = {}
    record = db.get_video(video_id) or {}
    meta = record.get("meta") or {}

    for platform in targets:
        try:
            if platform == "youtube":
                results["youtube"] = await upload_video(
                    video_id, cfg=cfg, privacy=privacy, publish_at=publish_at, dry_run=dry_run
                )
            elif platform == "instagram":
                results["instagram"] = await upload_reel(video_id, cfg=cfg, dry_run=dry_run)
            elif platform == "discord":
                webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
                if not webhook_url:
                    results["discord"] = {"error": "DISCORD_WEBHOOK_URL not set in .env"}
                elif dry_run:
                    results["discord"] = {"dry_run": True}
                else:
                    async with httpx.AsyncClient(timeout=15.0) as client:
                        title = meta.get("title") or record.get("topic") or "New Short"
                        payload = {
                            "content": f"🎬 **{title}**\n{meta.get('description', '')[:300]}...\n\nTags: {meta.get('tags', '')[:100]}"
                        }
                        resp = await client.post(webhook_url, json=payload)
                        results["discord"] = {"status": "posted", "code": resp.status_code}
            elif platform == "webhook":
                webhook_url = os.getenv("PUBLISH_WEBHOOK_URL")
                if not webhook_url:
                    results["webhook"] = {"error": "PUBLISH_WEBHOOK_URL not set in .env"}
                elif dry_run:
                    results["webhook"] = {"dry_run": True}
                else:
                    async with httpx.AsyncClient(timeout=15.0) as client:
                        resp = await client.post(webhook_url, json={"video_id": video_id, "meta": meta})
                        results["webhook"] = {"status": "delivered", "code": resp.status_code}
            elif platform == "telegram":
                if not (cfg.telegram_token and cfg.telegram_chat_id):
                    results["telegram"] = {"error": "TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID missing"}
                elif dry_run:
                    results["telegram"] = {"dry_run": True}
                else:
                    from .telegram_notify import send_telegram_video
                    sent = await send_telegram_video(video_id, cfg)
                    results["telegram"] = {"status": "broadcasted" if sent else "failed"}
            else:
                results[platform] = {"error": f"unknown platform {platform}"}
        except (UploadError, InstagramError) as exc:
            log.error("%s publish failed for #%s: %s", platform, video_id, exc)
            results[platform] = {"error": str(exc)}
        except Exception as exc:  # noqa: BLE001 - one platform must not kill the other
            log.exception("%s publish crashed for #%s", platform, video_id)
            results[platform] = {"error": f"{type(exc).__name__}: {exc}"}

    dry = all(r.get("dry_run") for r in results.values()) and bool(results)
    if dry:
        # a dry run must not touch the queue/statistics - nothing was actually published
        log.info("#%s dry-run finished for %s (status untouched)", video_id, ", ".join(targets))
        return results

    ok = [p for p, r in results.items() if not r.get("error")]
    failed = [p for p, r in results.items() if r.get("error")]
    if ok:
        db.update_video(
            video_id,
            platforms=",".join(ok),
            status="uploaded",
            uploaded_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
            error=("; ".join(f"{p}: {results[p]['error'][:200]}" for p in failed) or None),
        )
    else:
        db.update_video(
            video_id,
            platforms=",".join(targets),
            status="upload_failed",
            error="; ".join(f"{p}: {results[p]['error'][:200]}" for p in failed),
        )
    log.info("#%s publish done: ok=%s failed=%s", video_id, ok or "-", failed or "-")
    return results


def summary_text(results: dict) -> str:
    """Telegram-ready multi-platform result block."""
    lines = []
    for platform, info in results.items():
        if info.get("error"):
            lines.append(f"❌ {platform}: {info['error'][:300]}")
        elif info.get("dry_run"):
            lines.append(f"🧪 {platform}: dry-run only")
        else:
            url = info.get("url") or ""
            extra = ""
            if platform == "youtube":
                extra = (f"\n   privacy: {info.get('privacy')} · A/S disclosure: "
                         f"{info.get('synthetic_disclosure')} · uploads left today: {info.get('quota_left')}")
            elif platform == "instagram":
                extra = f"\n   mode: {info.get('mode')} · caption {info.get('caption_chars')} chars"
            lines.append(f"✅ {platform}: {url or 'published'}{extra}")
    return "\n".join(lines)


async def instagram_status(cfg: Config | None = None) -> str:
    """Quota line for /status ('' when Instagram is not set up)."""
    cfg = cfg or get_config()
    if not ig_configured(cfg):
        return ""
    try:
        limit = await publishing_limit(cfg)
        usage = limit.get("quota_usage")
        total = (limit.get("config") or {}).get("quota_total")
        return f"Instagram quota: {usage}/{total} posts in the last 24h"
    except Exception as exc:  # noqa: BLE001
        return f"Instagram quota check failed: {exc}"
