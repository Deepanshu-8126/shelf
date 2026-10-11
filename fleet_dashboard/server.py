import os
import sys
import json
import time
import asyncio
import subprocess
from pathlib import Path
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.responses import HTMLResponse, StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
FLEET_DIR = WORKSPACE_ROOT / "fleet_engines"
DASHBOARD_DIR = Path(__file__).resolve().parent
STATIC_DIR = DASHBOARD_DIR / "static"
STATIC_DIR.mkdir(parents=True, exist_ok=True)

# Add fleet_engines to Python path
sys.path.insert(0, str(WORKSPACE_ROOT))
sys.path.insert(0, str(FLEET_DIR))
sys.path.insert(0, str(FLEET_DIR / "channel_1"))
sys.path.insert(0, str(FLEET_DIR / "channel_2"))
sys.path.insert(0, str(FLEET_DIR / "channel_3"))

load_dotenv(WORKSPACE_ROOT / ".env")

app = FastAPI(title="Triple-Channel Master Studio", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory job tracking & event queues for real-time SSE logs
JOBS: Dict[str, Dict[str, Any]] = {}
JOB_QUEUES: Dict[str, List[asyncio.Queue]] = {}

class RenderRequest(BaseModel):
    channel: int  # 1, 2, or 3
    mode: str     # "manual" or "autopilot"
    title: Optional[str] = ""
    script: Optional[str] = ""
    script_url: Optional[str] = ""
    pillar: Optional[int] = 1
    topic: Optional[str] = ""
    lang: Optional[str] = "hi"
    voice: Optional[str] = "swara"
    bg_music: Optional[str] = "auto"
    bg_volume: Optional[float] = 0.52

def emit_log(job_id: str, message: str, step: str = "INFO", progress: int = None, video_url: str = None):
    event_data = {
        "job_id": job_id,
        "step": step,
        "message": message,
        "progress": progress,
        "video_url": video_url,
        "timestamp": time.strftime("%H:%M:%S")
    }
    if job_id in JOBS:
        JOBS[job_id]["logs"].append(event_data)
        if progress is not None:
            JOBS[job_id]["progress"] = progress
        if video_url is not None:
            JOBS[job_id]["video_url"] = video_url
            JOBS[job_id]["status"] = "COMPLETED"

    # Push to SSE queues
    for q in JOB_QUEUES.get(job_id, []):
        try:
            q.put_nowait(event_data)
        except Exception:
            pass

def run_render_worker(job_id: str, req: RenderRequest):
    try:
        emit_log(job_id, f"🚀 Job initialized for Channel {req.channel} in {req.mode.upper()} mode", "INIT", progress=5)
        out_video_path = None
        
        if req.channel == 1:
            emit_log(job_id, "📱 Loading Channel 1 (Reddit Drama & Storytime Engine)...", "CHANNEL_1", progress=15)
            from channel_1.run_reddit_pipeline import run as run_ch1
            bg_theme = "Subway Surfers"
            title = req.title if req.title else "Crazy Reddit Story"
            emit_log(job_id, f"🎬 Rendering Reddit Short: '{title}'", "RENDERING", progress=30)
            vid = run_ch1(bg_theme=bg_theme, custom_title=title, custom_script=req.script if req.mode == "manual" else "")
            out_video_path = Path(vid)
            
        elif req.channel == 2:
            emit_log(job_id, f"🕵️ Loading Channel 2 (Vox Noir / Crime & Psychology Pillar #{req.pillar})...", "CHANNEL_2", progress=15)
            from channel_2.run_channel_2 import render_short as run_ch2
            vid = run_ch2(
                pillar_id=req.pillar,
                topic=req.topic if req.mode == "autopilot" else "",
                lang=req.lang,
                custom_script=req.script if req.mode == "manual" else "",
                custom_title=req.title if req.mode == "manual" else ""
            )
            out_video_path = Path(vid)
            
        elif req.channel == 3:
            emit_log(job_id, f"🌌 Loading Channel 3 (Cosmic What-If / Sci-Fi Pillar #{req.pillar})...", "CHANNEL_3", progress=15)
            from channel_3.run_channel_3 import render_channel_3_short as run_ch3
            voice_choice = "madhur" if "madhur" in str(req.lang).lower() or "madhur" in str(req.voice).lower() else "swara"
            vid = run_ch3(
                pillar_id=req.pillar,
                topic=req.topic if req.mode == "autopilot" else "",
                lang="hi",
                custom_script=req.script if req.mode == "manual" else "",
                custom_title=req.title if req.mode == "manual" else "",
                script_url=req.script_url or "",
                voice_name=voice_choice
            )
            out_video_path = Path(vid)
        else:
            raise ValueError(f"Unknown channel: {req.channel}")

        if out_video_path and out_video_path.exists():
            # Create a web-accessible relative URL
            rel_name = out_video_path.name
            web_url = f"/api/video_file/{out_video_path.parent.name}/{rel_name}"
            emit_log(job_id, f"🎉 100% 4K Video Render Complete: {rel_name}", "SUCCESS", progress=90, video_url=web_url)
            
            # Direct Phone Telegram Delivery
            emit_log(job_id, "📱 Dispatching video directly to user Telegram phone...", "TELEGRAM", progress=95)
            try:
                from telegram_dispatcher import send_fleet_video_to_telegram
                title_clean = req.title if req.title else (req.topic if req.topic else f"Channel {req.channel} Viral Short")
                desc_clean = req.script if req.script else f"Autonomous AI Viral Short for Channel {req.channel}."
                send_fleet_video_to_telegram(
                    video_path=out_video_path,
                    channel=req.channel,
                    title=title_clean,
                    description=desc_clean,
                    tags=["shorts", "viral", "facts", "mystery"]
                )
                emit_log(job_id, "✅ Delivered to Telegram phone with Optimal Viral Upload Times!", "TELEGRAM", progress=100)
            except Exception as t_err:
                emit_log(job_id, f"⚠️ Telegram delivery note: {t_err}", "TELEGRAM", progress=100)
        else:
            emit_log(job_id, "❌ Error: Video file was not created", "ERROR", progress=100)
            if job_id in JOBS:
                JOBS[job_id]["status"] = "FAILED"
    except Exception as e:
        emit_log(job_id, f"❌ Crash in rendering worker: {str(e)}", "ERROR", progress=100)
        if job_id in JOBS:
            JOBS[job_id]["status"] = "FAILED"

@app.get("/api/status")
def get_status():
    pexels_key = os.getenv("PEXELS_API_KEY", "")
    groq_key = os.getenv("GROQ_API_KEY", "")
    gemini_key = os.getenv("GEMINI_API_KEY", "")
    return {
        "status": "online",
        "keys": {
            "pexels": bool(pexels_key and not pexels_key.startswith("sk-proj")),
            "groq": bool(groq_key),
            "gemini": bool(gemini_key)
        },
        "bgm_tracks_count": len(list((FLEET_DIR / "assets" / "bgm").glob("*.mp3"))),
        "total_jobs": len(JOBS)
    }

@app.get("/api/videos")
def list_videos():
    videos = []
    output_root = FLEET_DIR / "output"
    if output_root.exists():
        for f in output_root.rglob("*.mp4"):
            try:
                stat = f.stat()
                folder_name = f.parent.name
                channel = 1 if "reddit" in folder_name.lower() or "channel_1" in folder_name.lower() else (2 if "vox" in folder_name.lower() or "channel_2" in folder_name.lower() else 3)
                videos.append({
                    "name": f.name,
                    "channel": channel,
                    "folder": folder_name,
                    "size_mb": round(stat.st_size / (1024 * 1024), 2),
                    "modified": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(stat.st_mtime)),
                    "url": f"/api/video_file/{folder_name}/{f.name}"
                })
            except Exception:
                pass
    videos.sort(key=lambda x: x["modified"], reverse=True)
    return videos

@app.get("/api/video_file/{folder}/{filename}")
def serve_video(folder: str, filename: str):
    path = FLEET_DIR / "output" / folder / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="Video file not found")
    return FileResponse(path, media_type="video/mp4")

@app.post("/api/render")
def trigger_render(req: RenderRequest, bg_tasks: BackgroundTasks):
    job_id = f"job_{int(time.time())}_{req.channel}"
    JOBS[job_id] = {
        "id": job_id,
        "req": req.dict(),
        "status": "RUNNING",
        "progress": 0,
        "video_url": None,
        "logs": []
    }
    JOB_QUEUES[job_id] = []
    bg_tasks.add_task(run_render_worker, job_id, req)
    return {"job_id": job_id, "status": "QUEUED"}

@app.get("/api/stream/{job_id}")
async def stream_job(job_id: str, request: Request):
    if job_id not in JOBS:
        raise HTTPException(status_code=404, detail="Job not found")

    queue = asyncio.Queue()
    # replay previous logs
    for log in JOBS[job_id]["logs"]:
        await queue.put(log)

    if job_id not in JOB_QUEUES:
        JOB_QUEUES[job_id] = []
    JOB_QUEUES[job_id].append(queue)

    async def event_generator():
        try:
            while True:
                if await request.is_disconnected():
                    break
                try:
                    data = await asyncio.wait_for(queue.get(), timeout=1.0)
                    yield f"data: {json.dumps(data)}\n\n"
                    if data.get("progress") == 100:
                        break
                except asyncio.TimeoutError:
                    # Keep-alive heartbeat
                    yield f": ping\n\n"
        finally:
            if job_id in JOB_QUEUES and queue in JOB_QUEUES[job_id]:
                JOB_QUEUES[job_id].remove(queue)

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.get("/", response_class=HTMLResponse)
def index():
    html_path = STATIC_DIR / "index.html"
    if html_path.exists():
        return html_path.read_text(encoding="utf-8")
    return "<h1>Fleet Dashboard Studio Initializing...</h1>"

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

if __name__ == "__main__":
    import uvicorn
    print("🚀 Launching Triple-Channel Master Command Dashboard on http://0.0.0.0:8000...")
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=False)
