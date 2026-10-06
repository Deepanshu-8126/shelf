from __future__ import annotations

import json
import mimetypes
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

from agent.adapters import platform_matrix
from agent.config import ROOT, WEB_DIR, readiness, env
from agent.db import (init_db, latest_scan, latest_strategy_plan, list_channels, list_jobs, get_job,
                      update_job, save_scan, save_strategy_plan, update_channel, recent_analytics, now_iso)
from agent.analytics import fetch_video_analytics
from agent.pipeline import create_package, package_contents
from agent.llm import suggest_topic
from agent.policy import publish_blockers
from agent.publisher import PublishBlocked, publish_job
from agent.research import demo_candidates, scan_market
from agent.renderer import render_job
from agent.game_clips import create_game_clip_job, list_local_sources, suggest_local_moments
from agent.strategy import build_strategy
from agent.factshorts_adapter import (
    FACTSHORTS_OUTPUT,
    get_factshorts_status,
    get_factshorts_videos,
    get_task_status,
    get_active_task,
    start_factshorts_generation,
    delete_factshorts_video,
)
from agent.autoclip_adapter import (
    SHORTS_DIR,
    get_autoclip_status,
    get_autoclip_clips,
    start_autoclip_generation,
    get_autoclip_task,
    publish_clip_now,
    delete_autoclip_clip,
)
from agent.kaggle_adapter import (
    get_kaggle_telemetry,
    push_and_start_kaggle_gpu,
    stop_kaggle_gpu,
    save_worker_url,
)


init_db()


def dashboard() -> dict:
    scan = latest_scan()
    if not scan:
        scan = {"id": None, "mode": "demo", "created_at": None,
                "notes": "Run a scan. Without a YouTube Data API key, sample scores are illustrative only.",
                "candidates": demo_candidates()}
    jobs = list_jobs(20)
    ready = readiness()
    fs_status = get_factshorts_status()
    ac_status = get_autoclip_status()
    ac_clips = get_autoclip_clips()
    return {
        "ok": True,
        "channels": list_channels(),
        "jobs": jobs,
        "scan": scan,
        "analytics": recent_analytics(20),
        "platforms": platform_matrix(ready.get("authorized_channels", [])),
        "readiness": ready,
        "factshorts": {
            "video_count": fs_status.get("video_count", 0),
            "autonomous": fs_status.get("autonomous", {})
        },
        "autoclip": {
            "clip_count": len(ac_clips),
            "telegram_ready": ac_status.get("telegram_ready", False),
            "instagram": ac_status.get("instagram", {})
        },
        "summary": {
            "active_channels": sum(1 for c in list_channels() if c.get("active")),
            "jobs_total": len(list_jobs(200)),
            "factshorts_total": fs_status.get("video_count", 0),
            "autoclip_total": len(ac_clips),
            "needs_review": sum(1 for j in jobs if j.get("status") in {"draft", "needs_review"}),
            "ready_to_publish": sum(1 for j in jobs if j.get("status") == "approved"),
        },
    }


def get_engines_telemetry() -> dict:
    fs_status = get_factshorts_status()
    ac_status = get_autoclip_status()
    ac_clips = get_autoclip_clips()
    return {
        "ok": True,
        "engines": [
            {
                "id": "factshorts",
                "folder_name": "factshorts-bot",
                "name": "FactShorts AI",
                "path": str(FACTSHORTS_OUTPUT.parent.resolve()),
                "status": "online",
                "badge": "FACTS ENGINE",
                "output_dir": str(FACTSHORTS_OUTPUT.resolve()),
                "item_count": fs_status.get("video_count", 0),
                "features": ["Edge-TTS Hindi/Eng", "Whisper Subtitles", "Audio Ducking", "Pexels B-Roll", "Telegram Bot Control"],
                "autonomous": fs_status.get("autonomous", {})
            },
            {
                "id": "autoclip",
                "folder_name": "ai clipper best",
                "name": "Auto Clipper Pro",
                "path": str(SHORTS_DIR.parent.resolve()),
                "status": "online",
                "badge": "VIRAL CLIPPER",
                "output_dir": str(SHORTS_DIR.resolve()),
                "item_count": len(ac_clips),
                "features": ["YouTube Ingestion", "Drama Hook AI", "9:16 Face Crop", "Hormozi Kinetic Captions", "Direct Telegram / Instagram", "CapCut Sync"],
                "telegram": ac_status.get("telegram_ready", False),
                "instagram": ac_status.get("instagram", {})
            },
            {
                "id": "studio",
                "folder_name": "youtube_agent_studio",
                "name": "Studio Operations & Fleet",
                "path": str(ROOT.resolve()),
                "status": "online",
                "badge": "FLEET COMMAND",
                "output_dir": str((ROOT / "data").resolve()),
                "item_count": len(list_channels()),
                "features": ["4 Channel Personas", "Market Scout (US/IN)", "14-Day Playbook", "GTA VI Clips Lab", "SQLite Ledger"]
            }
        ]
    }


class Handler(BaseHTTPRequestHandler):
    server_version = "CreatorOps/0.1"

    def log_message(self, fmt: str, *args) -> None:
        # Never log request bodies: they may contain content notes or OAuth-related values.
        print("%s - %s" % (self.address_string(), fmt % args))

    def _json(self, status: int, data: dict) -> None:
        if isinstance(data, dict):
            if status >= 400:
                data.setdefault("success", False)
                if "error" not in data:
                    data["error"] = "Request failed"
            else:
                data.setdefault("success", True)
                data.setdefault("error", None)
        raw = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(raw)

    def _body(self) -> dict:
        size = int(self.headers.get("Content-Length", "0") or "0")
        if size > 1_000_000:
            raise ValueError("Request body is too large")
        if not size:
            return {}
        data = json.loads(self.rfile.read(size).decode("utf-8"))
        if not isinstance(data, dict):
            raise ValueError("Expected a JSON object")
        return data

    def _file(self, path: Path) -> None:
        if not path.is_file():
            self._json(404, {"error": "File not found"})
            return
        mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        size = path.stat().st_size
        self.send_response(200)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(size))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        with path.open("rb") as stream:
            while chunk := stream.read(1024 * 1024):
                self.wfile.write(chunk)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = unquote(parsed.path)
        if path == "/" or path == "/index.html":
            return self._file(WEB_DIR / "index.html")
        if path == "/api/health":
            return self._json(200, {"ok": True, "name": "CreatorOps", "readiness": readiness()})
        if path == "/api/engines":
            return self._json(200, get_engines_telemetry())
        if path == "/api/dashboard":
            return self._json(200, dashboard())
        if path == "/api/platforms":
            ready = readiness()
            return self._json(200, {"platforms": platform_matrix(ready.get("authorized_channels", []))})
        if path == "/api/strategy/latest":
            params = parse_qs(parsed.query)
            channel_id = str((params.get("channel_id") or ["ch-1"])[0])
            return self._json(200, {"strategy": latest_strategy_plan(channel_id)})
        if path == "/api/channels":
            return self._json(200, {"channels": list_channels()})
        if path == "/api/gaming/sources":
            return self._json(200, {"sources": list_local_sources(), "source_directory": "data/gaming_sources"})
        if path == "/api/jobs":
            return self._json(200, {"jobs": list_jobs(100)})
        match = re.fullmatch(r"/api/jobs/([a-f0-9]+)/?", path)
        if match:
            job = get_job(match.group(1))
            if not job:
                return self._json(404, {"error": "Job not found"})
            job["package"] = package_contents(job)
            job["publish_blockers"] = publish_blockers(job)
            return self._json(200, {"job": job})
        match = re.fullmatch(r"/packages/([a-f0-9]+)/([A-Za-z0-9_.-]+)", path)
        if match:
            job = get_job(match.group(1))
            if not job:
                return self._json(404, {"error": "Package not found"})
            package_dir = (ROOT / job["package_path"]).resolve()
            candidate = (package_dir / match.group(2)).resolve()
            if ROOT not in candidate.parents or package_dir not in candidate.parents:
                return self._json(403, {"error": "Invalid file path"})
            return self._file(candidate)
        if path == "/api/factshorts/status":
            return self._json(200, get_factshorts_status())
        if path == "/api/factshorts/videos":
            return self._json(200, {"videos": get_factshorts_videos()})
        if path == "/api/factshorts/active-task":
            return self._json(200, {"task": get_active_task()})
        match = re.fullmatch(r"/api/factshorts/task/([a-f0-9]+)", path)
        if match:
            task = get_task_status(match.group(1))
            if not task:
                return self._json(404, {"error": "Task not found"})
            return self._json(200, task)
        match = re.fullmatch(r"/output/factshorts/([A-Za-z0-9_.-]+)", path)
        if match:
            candidate = (FACTSHORTS_OUTPUT / match.group(1)).resolve()
            if FACTSHORTS_OUTPUT not in candidate.parents or not candidate.is_file():
                return self._json(404, {"error": "Video file not found"})
            return self._file(candidate)

        # AutoClip endpoints
        if path == "/api/autoclip/status":
            return self._json(200, get_autoclip_status())
        if path == "/api/autoclip/clips":
            return self._json(200, {"clips": get_autoclip_clips()})
        match = re.fullmatch(r"/api/autoclip/task/([a-f0-9]+)", path)
        if match:
            task = get_autoclip_task(match.group(1))
            if not task:
                return self._json(404, {"error": "Task not found"})
            return self._json(200, task)
        match = re.fullmatch(r"/video/autoclip/(.+)", path)
        if match:
            rel = match.group(1).lstrip("/")
            candidate = (SHORTS_DIR / rel).resolve()
            if SHORTS_DIR not in candidate.parents or not candidate.is_file():
                return self._json(404, {"error": "Video file not found"})
            return self._file(candidate)

        # Kaggle GPU endpoints
        if path == "/api/kaggle/status":
            return self._json(200, get_kaggle_telemetry())

        self._json(404, {"error": "Not found"})

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        path = unquote(parsed.path)
        try:
            body = self._body()
            if path == "/api/autoclip/generate":
                task_id = start_autoclip_generation(body)
                return self._json(202, {"task_id": task_id, "status": "running"})
            if path == "/api/autoclip/publish":
                res = publish_clip_now(str(body.get("video_path", "")), str(body.get("platform", "telegram")))
                return self._json(200 if res.get("ok") else 400, res)
            if path == "/api/autoclip/delete":
                clip_path = str(body.get("clip_path", "")).strip()
                ok = delete_autoclip_clip(clip_path)
                return self._json(200 if ok else 400, {"ok": ok, "clip_path": clip_path})
            if path == "/api/factshorts/generate":
                task_id = start_factshorts_generation(body)
                return self._json(202, {"task_id": task_id, "status": "running"})
            if path == "/api/factshorts/delete":
                filename = str(body.get("filename", "")).strip()
                ok = delete_factshorts_video(filename)
                return self._json(200 if ok else 400, {"ok": ok, "filename": filename})
            if path == "/api/kaggle/push":
                res = push_and_start_kaggle_gpu()
                return self._json(200 if res.get("ok") else 500, res)
            if path == "/api/kaggle/stop":
                res = stop_kaggle_gpu()
                return self._json(200 if res.get("ok") else 500, res)
            if path == "/api/kaggle/save-url":
                url = str(body.get("url", "")).strip()
                model = str(body.get("model", "wan-2.2")).strip()
                res = save_worker_url(url, model)
                return self._json(200, res)
            if path == "/api/research/run":
                result = scan_market()
                saved = save_scan(result["mode"], result["candidates"], result["notes"])
                return self._json(200 if result["mode"] != "error" else 502, {"scan": saved})
            if path == "/api/pipeline/generate":
                job = create_package(str(body.get("channel_id", "ch-1")), str(body.get("topic", "")),
                                     str(body.get("format", "Shorts")), str(body.get("angle", "")),
                                     research_notes=str(body.get("research_notes", "")),
                                     source_urls=body.get("source_urls", []))
                return self._json(201, {"job": job, "package": package_contents(job)})
            if path == "/api/gaming/highlights":
                suggestions = suggest_local_moments(str(body.get("source_file", "")))
                return self._json(200, {"suggestions": suggestions})
            if path == "/api/gaming/clips":
                job = create_game_clip_job(body)
                return self._json(201, {"job": job, "package": package_contents(job)})
            if path == "/api/pipeline/run":
                job = create_package(str(body.get("channel_id", "ch-1")), str(body.get("topic", "")),
                                     str(body.get("format", "Shorts")), str(body.get("angle", "")),
                                     research_notes=str(body.get("research_notes", "")),
                                     source_urls=body.get("source_urls", []))
                render = None
                render_error = ""
                try:
                    render = render_job(job["id"], generate_voice=bool(body.get("generate_voice", False)))
                    job = get_job(job["id"])
                except Exception as exc:
                    render_error = f"{type(exc).__name__}: {exc}"
                return self._json(201, {"job": job, "package": package_contents(job),
                                        "render": render, "render_error": render_error})
            if path == "/api/strategy/build":
                channel_id = str(body.get("channel_id", "ch-1"))
                scan = latest_scan() or {"mode": "demo", "candidates": demo_candidates()}
                plan = build_strategy(channel_id, scan, recent_analytics(200))
                saved = save_strategy_plan(channel_id, plan)
                return self._json(201, {"strategy": saved})
            if path == "/api/pipeline/from-scout":
                scan = latest_scan()
                if not scan:
                    raw_scan = scan_market()
                    scan = save_scan(raw_scan["mode"], raw_scan["candidates"], raw_scan["notes"])
                if not scan.get("candidates"):
                    return self._json(409, {"error": "No market candidates. Check research connection and run a scan."})
                channel_id = str(body.get("channel_id", "ch-1"))
                recent = [j.get("topic", "") for j in list_jobs(100) if j.get("channel_id") == channel_id]
                plan = suggest_topic(scan, recent)
                top = scan["candidates"][0]
                channel = next((c for c in list_channels() if c["id"] == channel_id), None)
                if channel and channel.get("niche") in {"Awaiting market scan", "Selected by the Market Scout", "Not selected yet"}:
                    update_channel(channel_id, {"niche": top.get("name", "Market Scout recommendation")})
                job = create_package(channel_id, plan["topic"], str(body.get("format", "Shorts")),
                                     plan["angle"], auto_generated=True,
                                     scan={"id": scan.get("id", ""), "why_now": plan.get("why_now", ""),
                                           "market_signals": top},
                                     research_notes=str(body.get("research_notes", "")),
                                     source_urls=body.get("source_urls", []))
                return self._json(201, {"job": job, "topic_plan": plan, "package": package_contents(job)})
            match = re.fullmatch(r"/api/jobs/([a-f0-9]+)/render", path)
            if match:
                manifest = render_job(match.group(1), generate_voice=bool(body.get("generate_voice", True)))
                return self._json(200, {"render": manifest, "job": get_job(match.group(1))})
            match = re.fullmatch(r"/api/jobs/([a-f0-9]+)/rights", path)
            if match:
                job = get_job(match.group(1))
                if not job:
                    return self._json(404, {"error": "Job not found"})
                status = str(body.get("status", ""))
                evidence = str(body.get("evidence", "")).strip()
                game_clip = job.get("data", {}).get("gaming_clip")
                commercial_reference = str(body.get("commercial_license_reference", "")).strip()[:500]
                if status not in {"owned", "licensed"} or len(evidence) < 12:
                    return self._json(400, {"error": "Choose owned/licensed and add a meaningful rights note (at least 12 characters)."})
                if isinstance(game_clip, dict):
                    if status != "licensed" or len(commercial_reference) < 8:
                        return self._json(409, {"error": "GTA VI monetization requires case-specific written commercial permission from Rockstar/Take-Two. Choose LICENSED and record the agreement/license reference; owning or crediting the recording is not sufficient."})
                    game_clip["commercial_license_reference"] = commercial_reference
                    game_clip["commercial_permission_attested_at"] = now_iso()
                    job_data = job.get("data", {})
                    job_data["gaming_clip"] = game_clip
                else:
                    job_data = job.get("data", {})
                manifest_path = (ROOT / job["package_path"] / "rights_manifest.json").resolve()
                if ROOT not in manifest_path.parents:
                    return self._json(403, {"error": "Invalid package path"})
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                manifest["rights_status"] = status
                manifest["rights_evidence"] = evidence
                if isinstance(game_clip, dict):
                    manifest["commercial_license_reference"] = commercial_reference
                    manifest["commercial_permission_attested_at"] = game_clip["commercial_permission_attested_at"]
                manifest["publish_allowed"] = False
                manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
                updated = update_job(job["id"], rights_status=status, rights_evidence=evidence, data=job_data)
                return self._json(200, {"job": updated})
            match = re.fullmatch(r"/api/jobs/([a-f0-9]+)/render-review", path)
            if match:
                job = get_job(match.group(1))
                if not job:
                    return self._json(404, {"error": "Job not found"})
                note = str(body.get("note", "")).strip()
                video_path = Path(job.get("video_path", ""))
                if len(note) < 25:
                    return self._json(400, {"error": "Add a meaningful final-render QA note (at least 25 characters)."})
                if not video_path.is_file() or not job.get("has_audio"):
                    return self._json(409, {"error": "A final video with an audio track is required before render QA can be recorded."})
                data = job.get("data", {})
                game_clip = data.get("gaming_clip")
                if isinstance(game_clip, dict):
                    review_fields = {
                        "original_commentary_in_render_confirmed": body.get("original_commentary_confirmed") is True,
                        "game_audio_rights_confirmed": body.get("game_audio_rights_confirmed") is True,
                        "no_leaked_or_prohibited_content_confirmed": body.get("no_leaked_or_prohibited_content_confirmed") is True,
                    }
                    if not all(review_fields.values()):
                        return self._json(400, {"error": "For a GTA VI clip, confirm original Hindi/Hinglish commentary is in the final render, all game/music/audio rights are cleared, and no leaked or prohibited content appears."})
                    game_clip.update(review_fields)
                    data["gaming_clip"] = game_clip
                renderer = data.get("renderer", {})
                renderer["visual_reviewed"] = True
                renderer["visual_review_note"] = note
                renderer["is_publish_ready"] = True
                data["renderer"] = renderer
                manifest_path = (ROOT / job["package_path"] / "render_manifest.json").resolve()
                if ROOT in manifest_path.parents and manifest_path.exists():
                    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                    manifest.update({"visual_reviewed": True, "visual_review_note": note, "is_publish_ready": True})
                    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
                if isinstance(game_clip, dict):
                    game_manifest_path = (ROOT / job["package_path"] / "gaming_clip_manifest.json").resolve()
                    if ROOT in game_manifest_path.parents and game_manifest_path.exists():
                        game_manifest = json.loads(game_manifest_path.read_text(encoding="utf-8"))
                        game_manifest.update({"visual_reviewed": True, "visual_review_note": note,
                                              "commercial_license_reference": game_clip.get("commercial_license_reference", ""),
                                              "original_commentary_in_render_confirmed": True,
                                              "game_audio_rights_confirmed": True,
                                              "no_leaked_or_prohibited_content_confirmed": True})
                        game_manifest_path.write_text(json.dumps(game_manifest, indent=2), encoding="utf-8")
                updated = update_job(job["id"], data=data)
                return self._json(200, {"job": updated, "note": "Final-render review recorded as a human attestation."})
            match = re.fullmatch(r"/api/jobs/([a-f0-9]+)/factcheck", path)
            if match:
                job = get_job(match.group(1))
                if not job:
                    return self._json(404, {"error": "Job not found"})
                note = str(body.get("note", "")).strip()
                sources = body.get("sources", [])
                if not isinstance(sources, list):
                    sources = []
                if len(note) < 20:
                    return self._json(400, {"error": "Add a fact-check note of at least 20 characters. This is a human attestation, not an automated fact-check."})
                data = job.get("data", {})
                data["fact_check_status"] = "verified_by_human"
                data["fact_check_note"] = note
                data["reviewed_source_urls"] = [str(s).strip() for s in sources if str(s).strip()][:20]
                updated = update_job(job["id"], data=data)
                return self._json(200, {"job": updated, "note": "Human review recorded. The system does not independently certify the sources."})
            match = re.fullmatch(r"/api/jobs/([a-f0-9]+)/approve", path)
            if match:
                job = get_job(match.group(1))
                if not job:
                    return self._json(404, {"error": "Job not found"})
                if job.get("rights_status") not in {"owned", "licensed"} or not job.get("rights_evidence"):
                    return self._json(409, {"error": "Clear and document the rights first."})
                if job.get("data", {}).get("fact_check_status") != "verified_by_human":
                    return self._json(409, {"error": "Complete the human fact-check first."})
                game_clip = job.get("data", {}).get("gaming_clip")
                if job.get("format") == "Game Clip" and not isinstance(game_clip, dict):
                    return self._json(409, {"error": "Build game clips through the rights-gated Gaming Clips workflow; required metadata is missing."})
                if isinstance(game_clip, dict):
                    if job.get("rights_status") != "licensed" or len(str(game_clip.get("commercial_license_reference", "")).strip()) < 8:
                        return self._json(409, {"error": "GTA VI approval is blocked until case-specific commercial permission from Take-Two/Rockstar is documented."})
                    required_checks = ("original_commentary_in_render_confirmed", "game_audio_rights_confirmed", "no_leaked_or_prohibited_content_confirmed")
                    if not all(game_clip.get(key) for key in required_checks):
                        return self._json(409, {"error": "Complete all GTA VI commentary, audio-rights, and no-leak/spoiler render checks first."})
                    renderer = job.get("data", {}).get("renderer", {})
                    video_path = Path(job.get("video_path", ""))
                    if not renderer.get("visual_reviewed") or not job.get("has_audio") or not video_path.is_file():
                        return self._json(409, {"error": "Review the final GTA VI MP4 with audio before approval."})
                updated = update_job(job["id"], human_approved=True, status="approved", stage="human_approved", error="")
                return self._json(200, {"job": updated, "publish_blockers": publish_blockers(updated)})
            match = re.fullmatch(r"/api/jobs/([a-f0-9]+)/schedule", path)
            if match:
                job = get_job(match.group(1))
                if not job:
                    return self._json(404, {"error": "Job not found"})
                if not job.get("human_approved"):
                    return self._json(409, {"error": "Approve the reviewed package first."})
                scheduled_at = str(body.get("scheduled_at", "")).strip()
                if not scheduled_at:
                    return self._json(400, {"error": "Provide an ISO timestamp for the scheduled upload."})
                updated = update_job(job["id"], scheduled_at=scheduled_at, status="scheduled", stage="queued", error="")
                return self._json(200, {"job": updated})
            match = re.fullmatch(r"/api/jobs/([a-f0-9]+)/publish", path)
            if match:
                result = publish_job(match.group(1), str(body.get("privacy", "private")), automated=False)
                return self._json(200, {"upload": result, "job": get_job(match.group(1))})
            if path == "/api/analytics/pull":
                result = fetch_video_analytics(str(body.get("channel_id", "")), str(body.get("video_id", "")),
                                               body.get("start_date"), body.get("end_date"))
                return self._json(200, {"analytics": result})
            match = re.fullmatch(r"/api/channels/(ch-[1-3])", path)
            if match:
                updated = update_channel(match.group(1), body)
                if not updated:
                    return self._json(404, {"error": "Channel slot not found"})
                return self._json(200, {"channel": updated})
            self._json(404, {"error": "Not found"})
        except PublishBlocked as exc:
            self._json(409, {"error": str(exc), "blockers": exc.blockers})
        except ValueError as exc:
            self._json(400, {"error": str(exc)})
        except Exception as exc:
            self._json(500, {"error": f"{type(exc).__name__}: {exc}"})

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.send_header("Allow", "GET, POST, OPTIONS")
        self.end_headers()


def main() -> None:
    host = env("HOST", "0.0.0.0")
    port = int(env("PORT", "8787"))
    server = ThreadingHTTPServer((host, port), Handler)
    print(f"CreatorOps running on http://{host}:{port}")
    print(f"Mode: {'LIVE RESEARCH' if readiness()['research_connected'] else 'DEMO'} · Auto-publish: {readiness()['auto_publish_enabled']}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
