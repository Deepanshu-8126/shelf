from __future__ import annotations

import time
from datetime import datetime, timezone

from .config import env
from .db import get_channel, latest_scan, list_channels, list_jobs, save_scan, update_channel, update_job
from .llm import suggest_topic
from .pipeline import create_package
from .publisher import PublishBlocked, publish_job
from .research import scan_market


def _today() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def _daily_scan() -> dict | None:
    if not env("YOUTUBE_DATA_API_KEY"):
        return None
    latest = latest_scan()
    if latest and latest.get("mode") == "live" and str(latest.get("created_at", ""))[:10] == _today():
        return latest
    result = scan_market()
    return save_scan(result["mode"], result["candidates"], result["notes"])


def _daily_drafts(scan: dict | None) -> list[dict]:
    if env("AUTO_DRAFT_ENABLED", "false").lower() != "true":
        return []
    if not scan or scan.get("mode") != "live" or not scan.get("candidates"):
        return [{"status": "stopped", "reason": "Daily drafting needs a successful live market scan."}]
    raw_channels = env("DAILY_DRAFT_CHANNELS", env("DAILY_DRAFT_CHANNEL", "ch-1"))
    channel_ids = [x.strip() for x in raw_channels.split(",") if x.strip()]
    if not channel_ids:
        channel_ids = ["ch-1"]
    jobs = list_jobs(300)
    results = []
    slots = {c["id"]: c for c in list_channels()}
    for index, channel_id in enumerate(channel_ids[:3]):
        existing = [j for j in jobs if j.get("channel_id") == channel_id
                    and j.get("data", {}).get("auto_generated")
                    and str(j.get("created_at", ""))[:10] == _today()]
        if existing:
            results.append({"status": "already_created_today", "channel_id": channel_id, "job_id": existing[0]["id"]})
            continue
        channel = slots.get(channel_id) or get_channel(channel_id)
        if not channel:
            results.append({"status": "stopped", "channel_id": channel_id, "reason": "Unknown channel slot"})
            continue
        placeholder = channel.get("niche") in {"Awaiting market scan", "Selected by the Market Scout", "Not selected yet"}
        selected = scan["candidates"][min(index, len(scan["candidates"]) - 1)]
        if placeholder:
            update_channel(channel_id, {"niche": selected.get("name", "Scout-selected niche")})
            channel = get_channel(channel_id)
        else:
            match = next((c for c in scan["candidates"] if c.get("name", "").lower() == channel["niche"].lower()), None)
            if match:
                selected = match
            else:
                results.append({"status": "stopped", "channel_id": channel_id,
                                "reason": f"Configured niche '{channel['niche']}' is not in today's scanned candidates. Add it to the research seed list first."})
                continue
        selected_scan = {"id": scan.get("id", ""), "mode": scan.get("mode"), "candidates": [selected]}
        recent = [j.get("topic", "") for j in jobs if j.get("channel_id") == channel_id]
        plan = suggest_topic(selected_scan, recent)
        job = create_package(channel_id, plan["topic"], env("DAILY_DRAFT_FORMAT", "Shorts"), plan["angle"],
                             auto_generated=True,
                             scan={"id": scan.get("id", ""), "why_now": plan.get("why_now", ""),
                                   "market_signals": selected})
        jobs.append(job)
        results.append({"status": "draft_created", "channel_id": channel_id, "job_id": job["id"],
                        "topic": plan["topic"], "niche": selected.get("name")})
    return results


def run_once() -> list[dict]:
    results: list[dict] = []
    scan = latest_scan()
    if env("YOUTUBE_DATA_API_KEY"):
        try:
            scan = _daily_scan()
            if scan:
                results.append({"status": "research_ready", "mode": scan.get("mode"), "scan_id": scan.get("id")})
        except Exception as exc:
            results.append({"status": "research_error", "error": f"{type(exc).__name__}: {exc}"})
    results.extend(_daily_drafts(scan))
    if env("AUTO_PUBLISH_ENABLED", "false").lower() != "true":
        results.append({"status": "stopped", "reason": "AUTO_PUBLISH_ENABLED is false; worker will not upload."})
        return results
    now = datetime.now(timezone.utc)
    for job in list_jobs(200):
        if job.get("status") not in {"approved", "scheduled"}:
            continue
        if not job.get("scheduled_at"):
            continue
        try:
            due = datetime.fromisoformat(job["scheduled_at"].replace("Z", "+00:00"))
        except ValueError:
            update_job(job["id"], status="schedule_error", error="scheduled_at must be an ISO-8601 timestamp")
            continue
        if due > now:
            continue
        try:
            result = publish_job(job["id"], automated=True)
            results.append({"job_id": job["id"], "status": "uploaded", **result})
        except PublishBlocked as exc:
            update_job(job["id"], status="blocked", error="; ".join(exc.blockers))
            results.append({"job_id": job["id"], "status": "blocked", "blockers": exc.blockers})
        except Exception as exc:
            results.append({"job_id": job["id"], "status": "error", "error": str(exc)})
    return results


def main() -> None:
    interval = max(60, int(env("WORKER_POLL_SECONDS", "300")))
    print(f"CreatorOps worker running; poll={interval}s. Auto-draft={env('AUTO_DRAFT_ENABLED','false')} Auto-publish={env('AUTO_PUBLISH_ENABLED','false')}")
    while True:
        for result in run_once():
            print(result)
        time.sleep(interval)


if __name__ == "__main__":
    main()
