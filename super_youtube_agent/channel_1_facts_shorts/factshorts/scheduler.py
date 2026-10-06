"""Daily scheduler (APScheduler) with a crash-proof job wrapper.

Jobs
----
* daily_generate  - at the configured time: full pipeline, then preview (or auto-upload)
* retry_uploads   - every 30 min: retry videos stuck in approved/upload_failed
* cleanup         - 03:30 daily: delete temp render folders older than 2 days

The scheduler itself never raises out of a job: every job is wrapped and any
failure is pushed to Telegram.
"""
from __future__ import annotations

import asyncio
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from . import db
from .config import NICHES, get_config
from .pipeline import generate_and_render, pipeline_summary
from .publish import platform_health, platforms_from_setting, publish_video, summary_text
from .telegram_notify import TelegramNotifier

from .utils import module_logger, setup_logging

log = module_logger("scheduler")

_scheduler: AsyncIOScheduler | None = None

DAILY_JOB_PREFIX = "daily_generate"
RETRY_JOB_ID = "retry_uploads"
CLEANUP_JOB_ID = "cleanup"


def current_niche() -> str:
    cfg = get_config()
    return (db.get_setting("niche") or cfg.niche or "space").lower()


def current_times() -> list[str]:
    """All daily posting slots, e.g. ["08:30", "19:30"] (morning + night)."""
    cfg = get_config()
    stored = db.get_setting("schedule_times")
    if stored:
        times = [t.strip() for t in stored.split(",") if t.strip()]
        if times:
            return times
    return list(cfg.schedule_times)


def current_time() -> str:
    """Backwards compatible single-slot accessor (first slot)."""
    return current_times()[0]


def auto_mode() -> bool:
    cfg = get_config()
    return db.get_bool_setting("auto_mode", cfg.auto_mode)


def _normalise_time(value: str) -> str | None:
    try:
        hh, mm = value.strip().split(":")
        if 0 <= int(hh) <= 23 and 0 <= int(mm) <= 59:
            return f"{int(hh):02d}:{int(mm):02d}"
    except Exception:  # noqa: BLE001
        return None
    return None


def _cron_for(hhmm: str) -> CronTrigger:
    cfg = get_config()
    try:
        hh, mm = hhmm.split(":")
        return CronTrigger(hour=int(hh), minute=int(mm), timezone=cfg.timezone)
    except Exception:  # noqa: BLE001
        log.warning("invalid schedule %r -> using 19:30", hhmm)
        return CronTrigger(hour=19, minute=30, timezone=cfg.timezone)


# ----------------------------------------------------------------------- jobs
def _niche_for_slot(slot_index: int) -> str:
    """Either the fixed niche, or the next one in the rotation list."""
    cfg = get_config()
    base = current_niche()
    if not cfg.niche_rotate:
        return base
    rotation = [n for n in NICHES if n != base]
    # rotate but keep the configured niche first in the cycle
    cycle = [base] + rotation
    return cycle[slot_index % len(cycle)]


async def job_daily_generate(slot_index: int = 0) -> None:
    cfg = get_config()
    notifier = TelegramNotifier(cfg)
    niche = _niche_for_slot(slot_index)
    log.info("daily job (slot %d): niche=%s auto=%s", slot_index, niche, auto_mode())
    try:
        if notifier.enabled:
            await notifier.send_message(f"⏰ Daily run starting (niche: {niche})…")

        async def progress(stage: str) -> None:
            log.info("daily progress: %s", stage)

        result = await generate_and_render(niche=niche, progress=progress)

        if auto_mode():
            results = await publish_video(result.video_id, cfg=cfg)
            if all(r.get("error") for r in results.values()):
                db.update_video(result.video_id, status="pending")
                await notifier.send_message(
                    "⚠️ Auto-publish failed on every platform - the video is waiting for approval:\n"
                    + summary_text(results)
                )
                await notifier.send_video(result.path, pipeline_summary(result)[:1000])
            else:
                await notifier.send_message(
                    f"🤖 Auto-published #{result.video_id}\n{summary_text(results)}"
                )
                await notifier.send_video(result.path, f"✅ {result.seo['title']}")
        else:
            await notifier.send_video(result.path, pipeline_summary(result)[:1000])
            await notifier.send_message(
                f"👆 #{result.video_id} ready. Reply /approve {result.video_id} to upload, "
                f"/regenerate {result.video_id} for a new version, /reject {result.video_id} to drop it."
            )
    except Exception as exc:  # noqa: BLE001 - the scheduler must survive anything
        log.exception("daily job failed")
        await notifier.send_message(f"❌ Daily run failed: {type(exc).__name__}: {exc}")
    finally:
        await notifier.aclose()


async def job_retry_uploads() -> None:
    cfg = get_config()
    if not auto_mode():
        return
    targets = platforms_from_setting(cfg)
    if not any(platform_health(cfg).get(p) == "ready" for p in targets):
        return
    notifier = TelegramNotifier(cfg)
    try:
        for row in db.list_videos("approved,upload_failed", 3):
            path = Path(row.get("video_path") or "")
            if not path.exists():
                db.update_video(row["id"], status="failed", error="render file missing on disk")
                continue
            results = await publish_video(row["id"], platforms=targets, cfg=cfg)
            if any(r.get("error") for r in results.values()):
                log.warning("retry publish #%s: %s", row["id"], summary_text(results))
                break  # probably a quota/permission problem: stop hammering the APIs
            await notifier.send_message(f"🔁 Retry publish ok: #{row['id']}\n{summary_text(results)}")
    finally:
        await notifier.aclose()


async def job_cleanup() -> None:
    cfg = get_config()
    cutoff = datetime.now(timezone.utc) - timedelta(days=2)
    removed = 0
    for folder in (cfg.cache_dir / "tmp",):
        if not folder.exists():
            continue
        for child in folder.iterdir():
            try:
                if child.is_dir() and datetime.fromtimestamp(child.stat().st_mtime, tz=timezone.utc) < cutoff:
                    shutil.rmtree(child, ignore_errors=True)
                    removed += 1
                elif child.is_file() and datetime.fromtimestamp(child.stat().st_mtime, tz=timezone.utc) < cutoff:
                    child.unlink(missing_ok=True)
            except Exception as exc:  # noqa: BLE001
                log.debug("cleanup skip %s: %s", child, exc)
    if removed:
        log.info("cleanup removed %d temp folders", removed)


# ------------------------------------------------------------------- lifecycle
def start_scheduler() -> AsyncIOScheduler:
    global _scheduler
    if _scheduler and _scheduler.running:
        return _scheduler
    cfg = get_config()
    _scheduler = AsyncIOScheduler(timezone=cfg.timezone)
    for index, slot in enumerate(current_times()):
        _scheduler.add_job(
            job_daily_generate, _cron_for(slot), args=[index],
            id=f"{DAILY_JOB_PREFIX}_{index}", replace_existing=True,
            misfire_grace_time=3600, coalesce=True, max_instances=1,
        )
    _scheduler.add_job(job_retry_uploads, IntervalTrigger(minutes=30), id=RETRY_JOB_ID,
                       replace_existing=True, max_instances=1)
    _scheduler.add_job(job_cleanup, CronTrigger(hour=3, minute=30, timezone=cfg.timezone), id=CLEANUP_JOB_ID,
                       replace_existing=True, max_instances=1)
    _scheduler.start()
    for job in _scheduler.get_jobs():
        if job.id.startswith(DAILY_JOB_PREFIX):
            log.info("scheduler: %s next run %s", job.id, job.next_run_time)
    log.info("scheduler started: slots %s (%s), auto=%s, platforms=%s",
             ", ".join(current_times()), cfg.timezone, auto_mode(), platforms_from_setting(cfg))
    return _scheduler


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        log.info("scheduler stopped")
    _scheduler = None


def reschedule_jobs() -> None:
    """Called after /schedule so changes apply without a restart."""
    if not _scheduler:
        return
    slots = current_times()
    # drop jobs for slots that no longer exist
    for job in list(_scheduler.get_jobs()):
        if job.id.startswith(DAILY_JOB_PREFIX):
            index = int(job.id.rsplit("_", 1)[-1] or 0)
            if index >= len(slots):
                _scheduler.remove_job(job.id)
                log.info("scheduler: removed slot %s", job.id)
    for index, slot in enumerate(slots):
        job_id = f"{DAILY_JOB_PREFIX}_{index}"
        if _scheduler.get_job(job_id):
            _scheduler.reschedule_job(job_id, trigger=_cron_for(slot))
        else:
            _scheduler.add_job(job_daily_generate, _cron_for(slot), args=[index], id=job_id,
                               replace_existing=True, misfire_grace_time=3600, coalesce=True, max_instances=1)
    log.info("scheduler rescheduled to %s", ", ".join(slots))


def run_forever() -> None:
    """Headless worker mode: `python main.py --daemon` (no Telegram bot polling)."""
    setup_logging()
    db.init_db()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    async def main() -> None:
        start_scheduler()
        log.info("daemon mode: slots %s (%s)", ", ".join(current_times()), get_config().timezone)
        notifier = TelegramNotifier()
        if notifier.enabled:
            await notifier.send_message(
                f"🛠 FactShorts daemon started.\nSlots: `{', '.join(current_times())}` "
                f"({get_config().timezone})\nniche `{current_niche()}` · rotation `{get_config().niche_rotate}` · "
                f"auto `{auto_mode()}` · platforms `{','.join(platforms_from_setting())}`."
            )
            await notifier.aclose()
        try:
            while True:
                await asyncio.sleep(3600)
        except (KeyboardInterrupt, asyncio.CancelledError):
            stop_scheduler()

    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        log.info("daemon stopped by user")


if __name__ == "__main__":
    run_forever()
