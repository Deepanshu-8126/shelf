from __future__ import annotations

import asyncio
import json
import shutil
import subprocess
import urllib.request
from pathlib import Path
from typing import Any

from .config import ROOT, env
from .db import get_job, update_job

PALETTE = [(12, 25, 52), (18, 35, 70), (15, 48, 72), (24, 39, 73)]
SHORT_FORMATS = {"short", "shorts", "youtube shorts"}


def _voice_provider() -> str:
    if env("ELEVENLABS_API_KEY") and env("ELEVENLABS_VOICE_ID"):
        return "ElevenLabs"
    if env("EDGE_TTS_VOICE"):
        return "Edge TTS · network service"
    return "not configured"


def _voiceover(text: str, target: Path) -> bool:
    key, voice = env("ELEVENLABS_API_KEY"), env("ELEVENLABS_VOICE_ID")
    if key and voice:
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice}?output_format=mp3_44100_128"
        body = json.dumps({"text": text, "model_id": env("ELEVENLABS_MODEL", "eleven_multilingual_v2"),
                           "voice_settings": {"stability": 0.48, "similarity_boost": 0.75}}).encode()
        request = urllib.request.Request(url, data=body, headers={
            "Content-Type": "application/json", "xi-api-key": key, "Accept": "audio/mpeg"
        }, method="POST")
        with urllib.request.urlopen(request, timeout=120) as response:
            target.write_bytes(response.read())
        return target.exists() and target.stat().st_size > 1000

    edge_voice = env("EDGE_TTS_VOICE")
    if edge_voice:
        try:
            import edge_tts
        except ImportError as exc:
            raise RuntimeError("EDGE_TTS_VOICE is set, but edge-tts is not installed; run pip install -r requirements.txt") from exc

        async def generate() -> None:
            communicator = edge_tts.Communicate(text, edge_voice)
            await communicator.save(str(target))

        asyncio.run(generate())
        return target.exists() and target.stat().st_size > 1000
    return False


def _ffmpeg_executable() -> str | None:
    override = env("FFMPEG_BINARY")
    if override:
        found = shutil.which(override)
        if found:
            return found
        if Path(override).is_file():
            return override
    found = shutil.which("ffmpeg")
    if found:
        return found
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return None


def _wrap(draw, text: str, font, max_width: int) -> list[str]:
    words, lines, current = str(text).split(), [], ""
    for word in words:
        candidate = (current + " " + word).strip()
        if draw.textbbox((0, 0), candidate, font=font)[2] <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def _build_silent_storyboard(job: dict, output: Path) -> dict[str, Any]:
    import cv2
    import numpy as np
    from PIL import Image, ImageDraw, ImageFont

    package_dir = (ROOT / job["package_path"]).resolve()
    content = json.loads((package_dir / "content.json").read_text(encoding="utf-8"))
    scenes = content.get("scenes", []) or [{"narration": content.get("script", ""), "visual_brief": "Original scene"}]
    is_short = str(job.get("format", "")).lower() in SHORT_FORMATS
    width, height, fps = (720, 1280, 12) if is_short else (1280, 720, 12)
    writer = cv2.VideoWriter(str(output), cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height))
    if not writer.isOpened():
        raise RuntimeError("OpenCV could not initialize an MP4 writer. Install a build with FFmpeg support.")
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    try:
        if is_short:
            font_big = ImageFont.truetype(font_path, 56)
            font_body = ImageFont.truetype(font_path, 32)
            font_small = ImageFont.truetype(font_path, 21)
        else:
            font_big = ImageFont.truetype(font_path, 48)
            font_body = ImageFont.truetype(font_path, 27)
            font_small = ImageFont.truetype(font_path, 18)
    except OSError:
        font_big, font_body, font_small = ImageFont.load_default(), ImageFont.load_default(), ImageFont.load_default()

    total_words = sum(max(1, len(str(s.get("narration", "")).split())) for s in scenes)
    estimated_seconds = max(18, int(total_words / 2.5))
    if is_short:
        total_seconds = min(70, estimated_seconds)
    else:
        total_seconds = min(360, max(30, estimated_seconds))
    scene_weights = [max(1, len(str(s.get("narration", "")).split())) for s in scenes]
    weight_total = sum(scene_weights) or 1
    durations = [max(3, round(total_seconds * weight / weight_total)) for weight in scene_weights]
    durations[-1] = max(3, total_seconds - sum(durations[:-1]))

    headline = str(content.get("title", job.get("title", "New idea")))
    for idx, (scene, seconds) in enumerate(zip(scenes, durations)):
        narration = str(scene.get("narration", "")).strip()
        visual = str(scene.get("visual_brief", "Original graphic scene")).strip()
        base = PALETTE[idx % len(PALETTE)]
        for frame_idx in range(seconds * fps):
            progress = frame_idx / max(1, seconds * fps - 1)
            image = Image.new("RGB", (width, height), base)
            draw = ImageDraw.Draw(image)
            circle_size = 105 if is_short else 75
            circle_y = 230 if is_short else 120
            circle_x = int(width * (0.88 - 0.16 * progress))
            draw.ellipse((circle_x - circle_size, circle_y - circle_size, circle_x + circle_size, circle_y + circle_size), fill=(35, 174, 184))
            inner = int(circle_size * 0.54)
            draw.ellipse((circle_x - inner, circle_y - inner, circle_x + inner, circle_y + inner), fill=(12, 25, 52))
            badge_y = 56 if is_short else 30
            draw.rounded_rectangle((42, badge_y, 240, badge_y + 42), radius=17, fill=(31, 54, 92))
            draw.text((58, badge_y + 10), "ORIGINAL DRAFT", font=font_small, fill=(172, 220, 229))
            label_y = 465 if is_short else 152
            draw.text((52, label_y), f"{idx + 1:02d}  /  {len(scenes):02d}", font=font_small, fill=(127, 209, 214))
            title_y = 520 if is_short else 200
            lines = _wrap(draw, headline, font_big, width - 104)[:3]
            y = title_y
            for line in lines:
                draw.text((52, y), line, font=font_big, fill=(250, 252, 255))
                y += 66 if is_short else 58

            caption_top = 890 if is_short else 430
            caption_bottom = height - (100 if is_short else 70)
            caption_lines = _wrap(draw, narration, font_body, width - 112)[:4]
            cap_h = min(caption_bottom - caption_top, max(110, 46 * len(caption_lines) + 38))
            draw.rounded_rectangle((36, caption_top, width - 36, caption_top + cap_h), radius=20,
                                   fill=(5, 13, 28), outline=(35, 174, 184), width=2)
            cy = caption_top + 18
            for line in caption_lines:
                draw.text((58, cy), line, font=font_body, fill=(250, 252, 255))
                cy += 38 if is_short else 32
            footer = visual[:82] + ("…" if len(visual) > 82 else "")
            draw.text((48, height - 48), footer, font=font_small, fill=(166, 183, 205))
            frame = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            writer.write(frame)
    writer.release()
    return {"width": width, "height": height, "fps": fps, "estimated_duration_seconds": sum(durations),
            "aspect_ratio": "9:16" if is_short else "16:9", "scene_count": len(scenes)}


def render_job(job_id: str, generate_voice: bool = True) -> dict[str, Any]:
    job = get_job(job_id)
    if not job:
        raise ValueError("Unknown job")
    if job.get("format") == "Game Clip":
        raise ValueError("Game Clips are rendered from an authorized local source; use the Gaming Clips section rather than the storyboard renderer.")
    package_dir = (ROOT / job["package_path"]).resolve()
    if ROOT not in package_dir.parents:
        raise ValueError("Invalid package path")
    output = package_dir / "storyboard_preview.mp4"
    try:
        render_info = _build_silent_storyboard(job, output)
    except ImportError as exc:
        raise RuntimeError("Video preview needs Pillow, OpenCV and NumPy. Install requirements.txt.") from exc
    content = json.loads((package_dir / "content.json").read_text(encoding="utf-8"))
    narration = str(content.get("script", ""))
    voice_path = package_dir / "voiceover.mp3"
    voice_ready, final_path, has_audio = False, output, False
    voice_provider = _voice_provider() if generate_voice else "not requested"
    voice_error = ""
    if generate_voice and voice_provider != "not configured":
        try:
            voice_ready = _voiceover(narration, voice_path)
        except Exception as exc:
            voice_error = f"{type(exc).__name__}: {exc}"
            (package_dir / "voiceover_error.txt").write_text(f"Voice provider error: {voice_error}\n", encoding="utf-8")
    ffmpeg = _ffmpeg_executable()
    if voice_ready and ffmpeg:
        mixed = package_dir / "final_with_voice.mp4"
        process = subprocess.run([
            ffmpeg, "-y", "-i", str(output), "-i", str(voice_path), "-c:v", "copy",
            "-c:a", "aac", "-b:a", "160k", "-shortest", str(mixed),
        ], capture_output=True, text=True, timeout=600)
        if process.returncode == 0 and mixed.exists() and mixed.stat().st_size > 10000:
            final_path, has_audio = mixed, True
        else:
            voice_error = "FFmpeg could not mux the voiceover into the preview. Inspect local FFmpeg setup."
    elif voice_ready and not ffmpeg:
        voice_error = "Voiceover was created but FFmpeg is unavailable to mux it into the video."

    if voice_error and not (package_dir / "voiceover_error.txt").exists():
        (package_dir / "voiceover_error.txt").write_text(voice_error + "\n", encoding="utf-8")
    manifest = {
        "video_path": str(final_path), "preview_path": str(output), "voiceover_path": str(voice_path) if voice_ready else "",
        "has_audio": has_audio, "voiceover_ready": voice_ready, "voiceover_provider": voice_provider,
        "ffmpeg_available": bool(ffmpeg), "visual_mode": "generated text-and-shape storyboard animatic",
        "render_info": render_info, "is_publish_ready": False,
        "warning": "Preview only. Replace/add licensed, audience-fit visuals, verify every claim and review timing/audio. Documentary scene cards are not a finished documentary.",
        "voice_error": voice_error,
    }
    (package_dir / "render_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    media_manifest_path = package_dir / "media_manifest.json"
    try:
        media_manifest = json.loads(media_manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        media_manifest = {}
    media_manifest.update({"render": manifest, "status": "preview rendered · human review required"})
    media_manifest_path.write_text(json.dumps(media_manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    update_job(job_id, video_path=str(final_path), has_audio=has_audio, status="needs_review", stage="storyboard_rendered",
               data={**job.get("data", {}), "renderer": manifest})
    return manifest
