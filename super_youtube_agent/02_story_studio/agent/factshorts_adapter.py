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
_fs_candidates = [
    WORKSPACE / "channel_1_facts_shorts",
    WORKSPACE / "factshorts-bot",
    WORKSPACE.parent / "channel_1_facts_shorts",
]
FACTSHORTS_DIR = next((p for p in _fs_candidates if p.is_dir()), WORKSPACE / "channel_1_facts_shorts").resolve()
OUTPUT_DIR = (FACTSHORTS_DIR / "output").resolve()
FACTSHORTS_OUTPUT = OUTPUT_DIR
PYTHON_EXE = (FACTSHORTS_DIR / "venv" / "Scripts" / "python.exe").resolve()
if not PYTHON_EXE.exists():
    PYTHON_EXE = Path(sys.executable)


TASKS_CACHE_FILE = FACTSHORTS_DIR / "cache" / "tasks_state.json"
TASKS: dict[str, dict[str, Any]] = {}


def _save_tasks():
    try:
        TASKS_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        sub = dict(list(TASKS.items())[-15:])
        TASKS_CACHE_FILE.write_text(json.dumps(sub, default=str), encoding="utf-8")
    except Exception:
        pass


def _load_tasks():
    global TASKS
    if TASKS_CACHE_FILE.is_file():
        try:
            data = json.loads(TASKS_CACHE_FILE.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                TASKS.update(data)
        except Exception:
            pass


_load_tasks()


def get_active_task() -> dict[str, Any] | None:
    # 1. Any task currently running
    for t_id, task in reversed(list(TASKS.items())):
        if task.get("status") == "running":
            return task
    # 2. Or the latest task
    if TASKS:
        return list(TASKS.values())[-1]
    return None


def _load_factshorts_module(name: str) -> Any:
    if str(FACTSHORTS_DIR) not in sys.path:
        sys.path.insert(0, str(FACTSHORTS_DIR))
    return importlib.import_module(name)


def get_factshorts_status() -> dict[str, Any]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    video_count = len(list(OUTPUT_DIR.glob("*.mp4")))
    
    # Try reading autonomous memory telemetry
    auto_info: dict[str, Any] = {
        "connected": False,
        "current_pillar": "space",
        "saturation": "0%",
        "proposal": "Cosmic Frontiers & Space Mysteries"
    }
    try:
        autopilot_mod = _load_factshorts_module("factshorts.autopilot")
        AutonomousStudio = getattr(autopilot_mod, "AutonomousStudio")
        studio = AutonomousStudio()
        proposal = studio.memory.propose_next_move()
        auto_info = {
            "connected": True,
            "current_pillar": proposal.get("current_pillar", "space"),
            "saturation": proposal.get("saturation_level", "0%"),
            "recommended_next_pillar": proposal.get("recommended_next_pillar", "space"),
            "recommended_hook_style": proposal.get("recommended_hook_style", "question"),
            "reasoning": proposal.get("reasoning", "")
        }
    except Exception as exc:
        auto_info["error"] = str(exc)

    return {
        "ok": True,
        "active_task": get_active_task(),
        "available": FACTSHORTS_DIR.exists(),
        "video_count": video_count,
        "models": [
            {
                "id": "ltx-2.3",
                "name": "LTX-2.3 (Lightricks)",
                "role": "Primary Video Engine (FactShorts & Influencer)",
                "specs": "20 sec, 4K, 50fps, Native Audio in 1 step",
                "hardware": "16GB VRAM (Kaggle T4 Q4_K_M GGUF)",
                "license": "LTX Community (<$10M ARR)"
            },
            {
                "id": "wan-2.2",
                "name": "Wan 2.2 (Alibaba)",
                "role": "Cinematic B-Roll & Transitions",
                "specs": "5 sec, 720p, T2V / I2V / FLF2V",
                "hardware": "14-16GB VRAM (Kaggle T4)",
                "license": "Apache 2.0"
            },
            {
                "id": "hunyuan-1.5",
                "name": "HunyuanVideo 1.5 (Tencent)",
                "role": "Long-Form Documentary Engine",
                "specs": "75 sec continuous, 8.3B params",
                "hardware": "16GB VRAM",
                "license": "Apache 2.0"
            },
            {
                "id": "z-image-turbo",
                "name": "Z-Image-Turbo",
                "role": "Thumbnails & Visuals",
                "specs": "Instant 1024x1024, ultra-fast",
                "hardware": "8GB / CPU",
                "license": "Apache 2.0"
            }
        ],
        "caption_styles": [
            {"id": "hormozi", "name": "Hormozi Kinetic Pop", "desc": "Word-level bounce with bold punch words & high retention"},
            {"id": "mrbeast", "name": "MrBeast Explosive", "desc": "Rapid word reveal with alert banner header"},
            {"id": "karaoke", "name": "Karaoke Glow Sweep", "desc": "Smooth active word color sweep highlight"},
            {"id": "pop_bounce", "name": "Elastic Pop-Bounce", "desc": "Playful elastic scale overshoot per word"},
            {"id": "neon_glow", "name": "Cyberpunk Neon Glow", "desc": "High contrast luminous border with dark shadow"}
        ],
        "niches": [
            {"id": "space", "name": "Space & Cosmic Mysteries", "icon": "🚀"},
            {"id": "science", "name": "Science Wonders & Quantum", "icon": "🔬"},
            {"id": "history", "name": "Historical Secrets & Empires", "icon": "🏛️"},
            {"id": "facts", "name": "Mindblowing Unbelievable Facts", "icon": "🤯"},
            {"id": "psychology", "name": "Human Mind & Psychology", "icon": "🧠"},
            {"id": "mystery", "name": "Haunted & Dark Mysteries", "icon": "👻"}
        ],
        "autonomous": auto_info
    }


def get_factshorts_videos() -> list[dict[str, Any]]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    videos: list[dict[str, Any]] = []

    # Get DB lookup helper if possible
    db_lookup = {}
    try:
        db_mod = _load_factshorts_module("factshorts.db")
        list_videos_fn = getattr(db_mod, "list_videos")
        for row in list_videos_fn(limit=100):
            db_lookup[row["id"]] = row
    except Exception:
        pass

    for mp4_file in sorted(OUTPUT_DIR.glob("*.mp4"), key=lambda p: p.stat().st_mtime, reverse=True):
        json_file = mp4_file.with_suffix(".json")
        meta: dict[str, Any] = {}
        if json_file.exists():
            try:
                meta = json.loads(json_file.read_text(encoding="utf-8"))
            except Exception:
                meta = {}

        video_id = meta.get("video_id")
        db_row = db_lookup.get(video_id) if video_id else None

        title = (db_row.get("title") if db_row else None) or mp4_file.stem.replace("-", " ").capitalize()
        duration = meta.get("duration") or (db_row.get("duration") if db_row else 15.0)
        size_bytes = mp4_file.stat().st_size
        size_human = f"{size_bytes / (1024 * 1024):.1f} MB"
        mtime = datetime.fromtimestamp(mp4_file.stat().st_mtime, tz=timezone.utc).isoformat()

        videos.append({
            "id": video_id or mp4_file.stem,
            "filename": mp4_file.name,
            "title": title,
            "topic": (db_row.get("topic") if db_row else "") or meta.get("query", ""),
            "duration": round(float(duration), 1),
            "size_bytes": size_bytes,
            "size_human": meta.get("size_human", size_human),
            "created_at": meta.get("rendered_at", mtime),
            "video_url": f"/output/factshorts/{mp4_file.name}",
            "json_url": f"/output/factshorts/{json_file.name}" if json_file.exists() else None,
            "clips_count": len(meta.get("clips", [])),
            "voice": meta.get("voice", "bm_george"),
            "caption_pages": meta.get("caption_pages", 0)
        })

    return videos


def start_factshorts_generation(options: dict[str, Any]) -> str:
    task_id = uuid.uuid4().hex[:12]
    mode = str(options.get("mode", "demo")).strip().lower()
    niche = str(options.get("niche", "space")).strip().lower()
    topic = str(options.get("topic", "")).strip()
    voice = str(options.get("voice", "")).strip()
    caption_style = str(options.get("caption_style", "hormozi")).strip()
    upload = bool(options.get("upload", False))

    model = str(options.get("model", "wan-2.2")).strip().lower()

    task: dict[str, Any] = {
        "task_id": task_id,
        "mode": mode,
        "niche": niche,
        "topic": topic,
        "voice": voice,
        "caption_style": caption_style,
        "model": model,
        "status": "running",
        "progress": ["Initializing FactShorts Bot..."],
        "logs": [],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "video": None,
        "error": None
    }
    TASKS[task_id] = task
    _save_tasks()

    def _worker():
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        if caption_style:
            env["CAPTION_STYLE"] = caption_style
        if voice:
            env["VOICE"] = voice
        if model:
            env["VIDEO_GEN_MODEL"] = model

        cmd = [str(PYTHON_EXE), "main.py"]
        if mode == "autonomous":
            cmd.extend(["--autonomous"])
            if upload:
                cmd.append("--upload")
        elif mode == "demo":
            cmd.append("--demo")
            if niche and niche != "auto":
                cmd.extend(["--niche", niche])
            if topic:
                cmd.extend(["--topic", topic])
        else:
            # LIVE ONLINE MODE: Google Trends + Wikipedia + Gemini LLM Script Writer
            cmd.append("--generate")
            if niche and niche != "auto":
                cmd.extend(["--niche", niche])
            if topic:
                cmd.extend(["--topic", topic])
            if options.get("offline") is True:
                cmd.append("--offline")

        try:
            task["progress"].append(f"Starting execution: {' '.join(cmd[1:])}")
            _save_tasks()
            process = subprocess.Popen(
                cmd,
                cwd=str(FACTSHORTS_DIR),
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace"
            )

            lines_count = 0
            for line in iter(process.stdout.readline, ""):
                line_str = line.strip()
                if line_str:
                    task["logs"].append(line_str)
                    if any(term in line_str.lower() for term in ["step", "stage", "rendering", "audio", "captions", "complete", "scout", "video", "topic", "script", "voice"]):
                        task["progress"].append(line_str)
                    if len(task["logs"]) > 200:
                        task["logs"].pop(0)
                    lines_count += 1
                    if lines_count % 5 == 0:
                        _save_tasks()

            process.wait()
            if process.returncode == 0:
                task["status"] = "completed"
                task["progress"].append("Video generated and OpenMontage QA verified successfully!")
                # Get the newest video
                videos = get_factshorts_videos()
                if videos:
                    task["video"] = videos[0]
            else:
                task["status"] = "failed"
                task["error"] = f"Process exited with code {process.returncode}"
                task["progress"].append(f"Error: Process failed with code {process.returncode}")
        except Exception as exc:
            task["status"] = "failed"
            task["error"] = str(exc)
            task["progress"].append(f"Error: {exc}")
        finally:
            _save_tasks()

    thread = threading.Thread(target=_worker, daemon=True)
    thread.start()
    return task_id


def get_task_status(task_id: str) -> dict[str, Any] | None:
    return TASKS.get(task_id)


def delete_factshorts_video(filename: str) -> bool:
    safe_name = Path(filename).name
    target = FACTSHORTS_OUTPUT / safe_name
    if target.is_file() and FACTSHORTS_OUTPUT in target.parents:
        try:
            target.unlink()
            json_target = target.with_suffix(".json")
            if json_target.is_file():
                json_target.unlink()
            return True
        except Exception:
            return False
    return False

