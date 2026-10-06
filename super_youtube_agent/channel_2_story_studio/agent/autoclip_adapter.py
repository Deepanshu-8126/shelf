from __future__ import annotations

import importlib
import json
import os
import subprocess
import sys
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
WORKSPACE = ROOT.parent
_clipper_base = (WORKSPACE / "ai_clipper_best") if (WORKSPACE / "ai_clipper_best").is_dir() else (WORKSPACE / "ai clipper best")
AUTOCLIP_DIR = (_clipper_base / "autoclip").resolve()
SHORTS_DIR = (_clipper_base / "Shorts").resolve()
INSTAPOST_DIR = (_clipper_base / "instapost").resolve()
_fs_candidates = [
    WORKSPACE / "channel_1_facts_shorts",
    WORKSPACE / "factshorts-bot",
    WORKSPACE.parent / "channel_1_facts_shorts",
]
FACTSHORTS_DIR = next((p for p in _fs_candidates if p.is_dir()), WORKSPACE / "channel_1_facts_shorts").resolve()


# Tasks storage for background renders
AUTOCLIP_TASKS: dict[str, dict[str, Any]] = {}


def _ensure_paths() -> None:
    for d in (AUTOCLIP_DIR, INSTAPOST_DIR, FACTSHORTS_DIR):
        if str(d) not in sys.path and d.is_dir():
            sys.path.insert(0, str(d))


def get_autoclip_status() -> dict[str, Any]:
    _ensure_paths()
    SHORTS_DIR.mkdir(parents=True, exist_ok=True)
    clip_files = list(SHORTS_DIR.rglob("*.mp4"))

    # Telegram check
    tg_ready = False
    try:
        from factshorts.telegram_notify import TelegramNotifier
        n = TelegramNotifier()
        tg_ready = n.enabled
    except Exception:
        pass

    # Instagram check
    ig_status = {"configured": False, "driver": "none", "today_count": 0, "cap": 8}
    try:
        from instapost.private import PrivateInstagram
        p = PrivateInstagram()
        if p.configured():
            count, cap = p.quota()
            ig_status = {"configured": True, "driver": "private (direct upload)", "today_count": count, "cap": cap}
    except Exception:
        pass

    groq_ready = bool(os.getenv("GROQ_API_KEY"))

    return {
        "ok": True,
        "available": AUTOCLIP_DIR.is_dir(),
        "total_clips": len(clip_files),
        "telegram_ready": tg_ready,
        "instagram": ig_status,
        "groq_ready": groq_ready,
        "genres": ["vlog", "gaming", "reality", "news"],
        "caption_styles": ["hormozi", "karaoke", "bounce", "glow", "plain"],
    }


def ensure_clip_thumbnail(mp4: Path) -> str:
    """Extracts a high quality 9:16 vertical hook thumbnail at 2.5s if not already generated."""
    try:
        thumb_path = mp4.with_suffix(".jpg")
        if not thumb_path.is_file() or thumb_path.stat().st_size == 0:
            cmd = [
                "ffmpeg", "-y", "-ss", "00:00:02.5",
                "-i", str(mp4),
                "-vframes", "1",
                "-q:v", "2",
                str(thumb_path),
            ]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10)

        if thumb_path.is_file():
            try:
                rel_subpath = thumb_path.relative_to(SHORTS_DIR).as_posix()
                return f"/video/autoclip/{rel_subpath}"
            except ValueError:
                return f"/video/autoclip/{thumb_path.name}"
    except Exception:
        pass
    return ""


def get_autoclip_clips() -> list[dict[str, Any]]:
    SHORTS_DIR.mkdir(parents=True, exist_ok=True)
    clips: list[dict[str, Any]] = []

    # Check for clips.json in all subdirectories of Shorts
    for cj in sorted(SHORTS_DIR.rglob("clips.json"), reverse=True):
        try:
            data = json.loads(cj.read_text(encoding="utf-8"))
            src_info = data.get("source", {})
            clip_list = data.get("clips", [])
            for c in clip_list:
                mp4 = Path(c.get("out") or c.get("mp4") or "")
                if not mp4.is_file():
                    candidate = cj.parent / f"{c.get('name')}.mp4"
                    if candidate.is_file():
                        mp4 = candidate
                if not mp4.is_file():
                    continue

                try:
                    rel_subpath = mp4.relative_to(SHORTS_DIR).as_posix()
                    rel_url = f"/video/autoclip/{rel_subpath}"
                except ValueError:
                    rel_url = f"/video/autoclip/{mp4.name}"

                thumb_url = ensure_clip_thumbnail(mp4)

                clips.append({
                    "name": c.get("name", mp4.stem),
                    "title": c.get("title") or c.get("name", ""),
                    "hook": c.get("hook", ""),
                    "duration": round(float(c.get("duration", 0)), 1),
                    "size_mb": round(mp4.stat().st_size / (1024 * 1024), 2),
                    "path": str(mp4.resolve()),
                    "stream_url": rel_url,
                    "thumb_url": thumb_url,
                    "source_title": src_info.get("title", ""),
                    "source_url": src_info.get("webpage_url") or src_info.get("url", ""),
                    "created_at": datetime.fromtimestamp(mp4.stat().st_mtime, tz=timezone.utc).isoformat(),
                })
        except Exception:
            continue

    # Also include standalone MP4s if any are in Shorts directly
    seen_paths = {c["path"] for c in clips}
    for mp4 in sorted(SHORTS_DIR.glob("*.mp4"), reverse=True):
        if str(mp4.resolve()) not in seen_paths:
            try:
                rel_subpath = mp4.relative_to(SHORTS_DIR).as_posix()
                rel_url = f"/video/autoclip/{rel_subpath}"
            except ValueError:
                rel_url = f"/video/autoclip/{mp4.name}"
            thumb_url = ensure_clip_thumbnail(mp4)
            clips.append({
                "name": mp4.stem,
                "title": mp4.stem.replace("_", " "),
                "hook": "Standalone render",
                "duration": 0,
                "size_mb": round(mp4.stat().st_size / (1024 * 1024), 2),
                "path": str(mp4.resolve()),
                "stream_url": rel_url,
                "thumb_url": thumb_url,
                "source_title": "",
                "source_url": "",
                "created_at": datetime.fromtimestamp(mp4.stat().st_mtime, tz=timezone.utc).isoformat(),
            })

    return clips


def start_autoclip_generation(payload: dict[str, Any]) -> str:
    _ensure_paths()
    url = str(payload.get("url", "")).strip()
    if not url:
        raise ValueError("YouTube video URL is required.")

    genre = str(payload.get("genre", "vlog")).strip().lower()
    clips_count = int(payload.get("clips", 1))
    caption_style = str(payload.get("caption_style", "hormozi")).strip().lower()
    caption_box = bool(payload.get("caption_box", False))
    safe_level = int(payload.get("safe_level", 1))
    send_telegram = bool(payload.get("telegram", True))
    send_instagram = bool(payload.get("instagram", False))

    task_id = uuid.uuid4().hex[:12]
    task = {
        "id": task_id,
        "status": "running",
        "url": url,
        "genre": genre,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "logs": [f"Task {task_id} queued: target={url}, genre={genre}, clips={clips_count}"],
        "result": None,
        "error": None,
    }
    AUTOCLIP_TASKS[task_id] = task

    def _worker():
        try:
            from autoclip.pipeline import run as run_pipeline
            task["logs"].append("Step 1/5: Expanding and checking source metadata...")
            
            # Run pipeline
            res = run_pipeline(
                url,
                clips=clips_count,
                genre=genre,
                caption_style=caption_style,
                caption_box=caption_box,
                safe_level=safe_level,
                outdir=str(SHORTS_DIR)
            )
            task["status"] = "completed"
            task["result"] = res
            task["logs"].append(f"✓ Success! Generated {len(res)} viral short(s).")

            if send_telegram:
                for r in res:
                    mp4_path = r.get("out")
                    if mp4_path and Path(mp4_path).is_file():
                        publish_clip_now(mp4_path, "telegram")
                task["logs"].append("✓ Telegram notification dispatched to phone!")

            if send_instagram:
                for r in res:
                    mp4_path = r.get("out")
                    if mp4_path and Path(mp4_path).is_file():
                        publish_clip_now(mp4_path, "instagram")
                task["logs"].append("✓ Instagram Reel upload dispatched!")
        except Exception as exc:
            task["status"] = "failed"
            task["error"] = str(exc)
            task["logs"].append(f"✗ Failed: {exc}")

    thread = threading.Thread(target=_worker, daemon=True)
    thread.start()
    return task_id


def get_autoclip_task(task_id: str) -> dict[str, Any] | None:
    return AUTOCLIP_TASKS.get(task_id)


def publish_clip_now(video_path: str, platform: str) -> dict[str, Any]:
    _ensure_paths()
    p = Path(video_path)
    if not p.is_file():
        return {"ok": False, "error": f"File not found: {video_path}"}

    platform = platform.lower().strip()
    if platform == "telegram":
        try:
            from factshorts.telegram_notify import TelegramNotifier
            notifier = TelegramNotifier()
            if not notifier.is_enabled():
                return {"ok": False, "error": "Telegram not configured in .env"}
            caption = f"✂️ *Viral Short Ready!*\n\n📌 *{p.stem}*\n#autoclip #shorts\n\n📺 Channel: chan6 (AI Clipper)"
            ok = notifier.send_video(p, caption=caption)
            return {"ok": ok, "platform": "telegram"}
        except Exception as exc:
            return {"ok": False, "error": str(exc), "platform": "telegram"}
    elif platform == "instagram":
        try:
            from instapost.private import PrivateInstagram
            driver = PrivateInstagram.from_env()
            reel_id = driver.post_reel(p, caption=f"{p.stem} #shorts #reels")
            return {"ok": True, "reel_id": reel_id, "platform": "instagram"}
        except Exception as exc:
            return {"ok": False, "error": str(exc), "platform": "instagram"}
    else:
        return {"ok": False, "error": f"Unknown platform: {platform}"}


def delete_autoclip_clip(clip_path: str) -> bool:
    _ensure_paths()
    if not clip_path:
        return False
    p = Path(clip_path).resolve()
    # Security: ensure file is inside SHORTS_DIR
    try:
        p.relative_to(SHORTS_DIR)
    except ValueError:
        return False

    if not p.is_file():
        return False

    try:
        p.unlink(missing_ok=True)
        p.with_suffix(".jpg").unlink(missing_ok=True)
        p.with_suffix(".ass").unlink(missing_ok=True)
        p.with_suffix(".srt").unlink(missing_ok=True)

        cj = p.parent / "clips.json"
        if cj.is_file():
            try:
                data = json.loads(cj.read_text(encoding="utf-8"))
                original_clips = data.get("clips", [])
                updated = [c for c in original_clips if Path(c.get("out") or c.get("mp4") or "").name != p.name and c.get("name") != p.stem]
                data["clips"] = updated
                cj.write_text(json.dumps(data, indent=2), encoding="utf-8")
            except Exception:
                pass
        return True
    except Exception:
        return False

