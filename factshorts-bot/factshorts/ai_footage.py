"""100% Free AI Video & Visual Footage Engine (September 2026).

Zero Paid APIs. 100% Free / Apache 2.0 / MIT Open-Source Stack:
1. REAL VIDEO (PRIMARY):
   - Wan 2.2 (Alibaba, Apache 2.0, 5s 720p, Kaggle T4 / Local GPU)
   - LTX-2.3 (Lightricks, Free Community, 20s 4K, Kaggle T4 / Local GPU)
2. AI IMAGERY (FALLBACK):
   - PRIMARY: Z-Image-Turbo (Apache 2.0, 1024x1024, local/Kaggle GPU)
   - FALLBACK: Gemini 3.1 Flash Image (gemini-3.1-flash-image, 500/day FREE)
3. CINEMATIC CAMERA MOTION (EMERGENCY FALLBACK):
   - FFmpeg Ken-Burns zoom/pan/drift only when real video generator is offline.
"""
from __future__ import annotations

import asyncio
import base64
import random
import re
from pathlib import Path
from typing import Any

import httpx

from .ai_video import generate_remote_image_z_turbo, generate_remote_video
from .config import Config, get_config
from .utils import media_duration, module_logger, run_cmd, slugify, video_size

log = module_logger("ai_footage")

# Gemini 3.1 Flash Image endpoint (Free tier: 500 requests/day, NO paid Imagen)
GEMINI_GENERATE = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

# Cinematic prompt enhancers per niche
NICHE_STYLE: dict[str, str] = {
    "space": "cinematic 8K photograph, deep space, volumetric nebula lighting, NASA telescope style, ultra realistic, dark cosmic background, lens flare, photorealistic",
    "psychology": "cinematic 8K photograph, dramatic studio lighting, human brain visualization, neural network glow, dark moody atmosphere, photorealistic, depth of field",
    "history": "cinematic 8K photograph, dramatic golden hour lighting, ancient civilization, epic wide angle, atmospheric haze, photorealistic, film grain",
    "science": "cinematic 8K photograph, laboratory macro shot, quantum visualization, bioluminescent glow, dark background, photorealistic, scientific illustration",
    "animals": "cinematic 8K photograph, National Geographic style, wildlife close-up, dramatic rim lighting, shallow depth of field, photorealistic",
    "facts": "cinematic 8K photograph, dramatic lighting, surreal visualization, dark moody atmosphere, ultra detailed, photorealistic, epic composition",
}
DEFAULT_STYLE = "cinematic 8K photograph, dramatic lighting, ultra realistic, dark moody atmosphere, photorealistic, epic wide angle composition"
NEGATIVE = "text, watermark, logo, signature, blurry, low quality, cartoon, anime, illustration, drawing, painting, sketch, CGI render, 3D render"


def _enhance_prompt(scene_description: str, niche: str) -> str:
    """Turn a plain scene description into a cinematic visual prompt."""
    style = NICHE_STYLE.get(niche, DEFAULT_STYLE)
    desc = re.sub(r"[^\w\s,.:;!?'-]", "", scene_description).strip()
    return f"{desc}, {style}. Avoid: {NEGATIVE}"


# -----------------------------------------------------------------------------
# 1. AI Image Generation: Z-Image-Turbo (Primary) -> Gemini 3.1 Flash Image (Fallback)
# -----------------------------------------------------------------------------
_GEMINI_IMAGE_UNAVAILABLE = False

async def _try_gemini_flash_image(
    prompt: str, output_path: Path, api_key: str
) -> Path | None:
    """Free Gemini 3.1 Flash Image generator (500 free requests/day).

    NEVER uses paid Imagen. Uses the standard generative language v1beta endpoint.
    """
    global _GEMINI_IMAGE_UNAVAILABLE
    if _GEMINI_IMAGE_UNAVAILABLE:
        return None

    # Free tier models supporting multimodal image output
    free_image_models = ["gemini-3.1-flash-image", "gemini-2.5-flash-image", "gemini-3.1-flash"]

    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": (
                            f"Generate a stunning cinematic vertical image (9:16 aspect ratio) for a YouTube Short. "
                            f"Scene: {prompt}. "
                            f"The image must look like a high-budget film frame. No text, no watermarks."
                        )
                    }
                ]
            }
        ],
        "generationConfig": {
            "responseModalities": ["IMAGE"],
        },
    }

    for model in free_image_models:
        url = GEMINI_GENERATE.format(model=model) + f"?key={api_key}"
        for attempt in range(1, 2):
            try:
                async with httpx.AsyncClient(timeout=httpx.Timeout(4.0)) as client:
                    resp = await client.post(url, json=payload)

                if resp.status_code in (503, 429):
                    log.debug("Gemini free image %s: HTTP %d (rate limit / unavailable)", model, resp.status_code)
                    break

                if resp.status_code >= 400:
                    log.debug("Gemini free image %s HTTP %d: %s", model, resp.status_code, resp.text[:120])
                    _GEMINI_IMAGE_UNAVAILABLE = True
                    return None

                data = resp.json()
                for candidate in data.get("candidates", []):
                    for part in candidate.get("content", {}).get("parts", []):
                        inline_data = part.get("inlineData")
                        if inline_data and inline_data.get("mimeType", "").startswith("image/"):
                            image_bytes = base64.b64decode(inline_data["data"])
                            output_path.parent.mkdir(parents=True, exist_ok=True)
                            output_path.write_bytes(image_bytes)
                            log.info("AI image generated (%s FREE): %s (%d KB)",
                                     model, output_path.name, len(image_bytes) // 1024)
                            return output_path
                break  # Next model
            except Exception as exc:
                log.debug("Gemini free image error: %s", exc)
                break

    return None


async def generate_ai_image(
    scene_description: str,
    output_path: Path,
    niche: str = "space",
    cfg: Config | None = None,
) -> Path | None:
    """Generate a single AI image for a scene:

    Priority 1: Z-Image-Turbo (Apache 2.0, FREE, local or remote worker)
    Priority 2: Gemini 3.1 Flash Image (500/day FREE, zero paid Imagen)
    """
    cfg = cfg or get_config()
    prompt = _enhance_prompt(scene_description, niche)

    # 1. PRIMARY: Z-Image-Turbo (Apache 2.0, 100% Free)
    res = await generate_remote_image_z_turbo(prompt, output_path, cfg)
    if res and res.exists():
        return res

    # 2. FALLBACK: Gemini 3.1 Flash Image (Free tier)
    if cfg.gemini_api_key:
        res = await _try_gemini_flash_image(prompt, output_path, cfg.gemini_api_key)
        if res and res.exists():
            return res

    log.debug("Free AI image generation unavailable for: %s", scene_description[:50])
    return None


# -----------------------------------------------------------------------------
# 2. Emergency Fallback: FFmpeg Ken-Burns Camera Motion (Only if Real Video fails)
# -----------------------------------------------------------------------------
async def animate_image_to_video(
    image_path: Path,
    output_path: Path,
    duration: float = 4.0,
    width: int = 1080,
    height: int = 1920,
    fps: int = 30,
    effect_index: int = 0,
) -> Path | None:
    """Convert static AI image into cinematic clip using FFmpeg.

    Used strictly as fallback when real Wan 2.2 / LTX-2.3 video generation is offline.
    """
    effects = [
        # Zoom in
        (
            f"scale=w='if(gte(t,0),{width}*(1+0.12*t/{duration}),{width})':"
            f"h='if(gte(t,0),{height}*(1+0.12*t/{duration}),{height})':"
            f"eval=frame:flags=bicubic,"
            f"crop={width}:{height}"
        ),
        # Zoom out
        (
            f"scale=w='{int(width * 1.15)}':h='{int(height * 1.15)}':flags=bicubic,"
            f"crop={width}:{height}:"
            f"x='(in_w-{width})/2-((in_w-{width})/2)*(t/{duration})':"
            f"y='(in_h-{height})/2-((in_h-{height})/2)*(t/{duration})'"
        ),
        # Left-to-right pan
        (
            f"scale=w='{int(width * 1.2)}':h='{int(height * 1.2)}':flags=bicubic,"
            f"crop={width}:{height}:"
            f"x='(in_w-{width})*(t/{duration})':"
            f"y='(in_h-{height})/2'"
        ),
        # Top-down drift
        (
            f"scale=w='{int(width * 1.15)}':h='{int(height * 1.15)}':flags=bicubic,"
            f"crop={width}:{height}:"
            f"x='(in_w-{width})/2':"
            f"y='(in_h-{height})*(t/{duration})'"
        ),
        # Diagonal drift
        (
            f"scale=w='if(gte(t,0),{width}*(1+0.08*t/{duration}),{width})':"
            f"h='if(gte(t,0),{height}*(1+0.08*t/{duration}),{height})':"
            f"eval=frame:flags=bicubic,"
            f"crop={width}:{height}:"
            f"x='(in_w-{width})/2+30*(t/{duration})':"
            f"y='(in_h-{height})/2+20*(t/{duration})'"
        ),
    ]

    effect = effects[effect_index % len(effects)]
    color_grade = "eq=contrast=1.05:saturation=1.10,vignette=PI/5"
    vf = f"{effect},{color_grade},fps={fps},format=yuv420p"

    cmd = [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-loop", "1", "-i", str(image_path),
        "-t", f"{duration:.3f}",
        "-vf", vf,
        "-c:v", "libx264", "-preset", "fast", "-crf", "19",
        "-pix_fmt", "yuv420p",
        str(output_path),
    ]

    try:
        code, out, err = run_cmd(cmd, timeout=90)
        if code == 0 and output_path.exists() and output_path.stat().st_size > 5000:
            log.info("Fallback animated clip created: %s (%.1fs)", output_path.name, duration)
            return output_path
        return None
    except Exception as exc:
        log.warning("FFmpeg animation error: %s", exc)
        return None


# -----------------------------------------------------------------------------
# 3. Main Scene Clip Pipeline (Real Video Primary -> Image+Pan Fallback)
# -----------------------------------------------------------------------------
async def generate_ai_clip(
    scene_description: str,
    output_dir: Path,
    clip_index: int = 0,
    duration: float = 4.0,
    niche: str = "space",
    cfg: Config | None = None,
) -> dict[str, Any] | None:
    """Generates an individual scene clip:

    STEP 1: Real AI Video Generation via Wan 2.2 / LTX-2.3 (Kaggle GPU / remote worker).
    STEP 2: (Fallback) Z-Image-Turbo / Gemini 3.1 Flash Image + FFmpeg camera movement.
    """
    cfg = cfg or get_config()
    output_dir.mkdir(parents=True, exist_ok=True)
    slug = slugify(scene_description[:40], 30)

    video_path = output_dir / f"ai_video_{clip_index:02d}_{slug}.mp4"
    image_path = output_dir / f"ai_image_{clip_index:02d}_{slug}.png"
    prompt = _enhance_prompt(scene_description, niche)

    # -------------------------------------------------------------------------
    # STEP 1: REAL AI VIDEO (Wan 2.2 / LTX-2.3 on Kaggle GPU)
    # -------------------------------------------------------------------------
    preferred_model = getattr(cfg, "video_gen_model", "wan-2.2")
    real_video = await generate_remote_video(
        prompt=prompt,
        output_path=video_path,
        model=preferred_model,
        duration=duration,
        cfg=cfg,
    )

    if real_video and real_video.exists() and real_video.stat().st_size > 20_000:
        dur = media_duration(real_video) or duration
        w, h = video_size(real_video)
        log.info("Generated REAL AI VIDEO clip (%s): %s (%.1fs)", preferred_model, real_video.name, dur)
        return {
            "source": f"ai_video_{preferred_model}",
            "source_id": f"{preferred_model}-{clip_index:02d}-{slug}",
            "path": str(real_video),
            "image_path": "",
            "duration": dur,
            "width": w or 1080,
            "height": h or 1920,
            "prompt": scene_description,
            "niche": niche,
            "license": f"AI Video ({preferred_model}) — 100% Free, Commercial Safe",
            "author": f"{preferred_model.upper()} AI",
        }

    # -------------------------------------------------------------------------
    # STEP 2: FALLBACK (Z-Image-Turbo / Gemini 3.1 Flash Image + FFmpeg Zoom/Pan)
    # -------------------------------------------------------------------------
    img = await generate_ai_image(scene_description, image_path, niche=niche, cfg=cfg)
    if img and img.exists():
        anim = await animate_image_to_video(
            image_path=img,
            output_path=video_path,
            duration=duration,
            width=cfg.width if cfg else 1080,
            height=cfg.height if cfg else 1920,
            fps=cfg.fps if cfg else 30,
            effect_index=clip_index,
        )
        if anim and anim.exists():
            return {
                "source": "ai_image_animated",
                "source_id": f"ai-img-{clip_index:02d}-{slug}",
                "path": str(anim),
                "image_path": str(img),
                "duration": duration,
                "width": cfg.width if cfg else 1080,
                "height": cfg.height if cfg else 1920,
                "prompt": scene_description,
                "niche": niche,
                "license": "AI Visuals (Z-Image/Gemini 3.1 Free) — Commercial Safe",
                "author": "AI Generated",
            }

    return None


async def generate_scene_clips(
    script_text: str,
    output_dir: Path,
    total_duration: float,
    clip_count: int = 4,
    niche: str = "space",
    cfg: Config | None = None,
    sentence_timings: list[tuple[str, float, float]] | None = None,
) -> list[dict[str, Any]]:
    """Generate multiple AI clips from a script using the 100% free AI stack.
    
    If sentence_timings is provided [(sentence_text, start_sec, duration_sec), ...],
    each video clip is explicitly generated and timed to match that exact spoken sentence!
    """
    cfg = cfg or get_config()
    if sentence_timings and len(sentence_timings) > 0:
        scenes = [st[0] for st in sentence_timings]
        durations = [max(1.8, st[2]) for st in sentence_timings]
    else:
        scenes = _extract_scenes(script_text, clip_count, niche)
        duration_per_clip = total_duration / max(1, len(scenes))
        durations = [duration_per_clip] * len(scenes)

    clips: list[dict[str, Any]] = []
    for i, scene in enumerate(scenes):
        target_dur = durations[i] if i < len(durations) else (total_duration / max(1, len(scenes)))
        clip = await generate_ai_clip(
            scene_description=scene,
            output_dir=output_dir,
            clip_index=i,
            duration=target_dur,
            niche=niche,
            cfg=cfg,
        )
        if clip:
            clips.append(clip)
        else:
            log.debug("AI clip %d skipped for scene: %s", i, scene[:50])

    log.info("AI footage engine: generated %d/%d clips (Sentence Synced to Spoken Beats)", len(clips), len(scenes))
    return clips


def _extract_scenes(script_text: str, count: int, niche: str) -> list[str]:
    """Break a narration script into visual scene descriptions."""
    sentences = re.split(r'[.!?]+', script_text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 10]

    if not sentences:
        return [f"Dramatic {niche} visualization, epic cinematic shot"]

    if len(sentences) > count:
        step = len(sentences) / count
        picked = [sentences[int(i * step)] for i in range(count)]
    else:
        picked = sentences
        while len(picked) < count:
            picked.append(f"Epic cinematic {niche} scene, dramatic wide shot")

    enhanced: list[str] = []
    visual_styles = [
        "extreme close-up macro shot",
        "epic wide angle establishing shot",
        "dramatic low angle hero shot",
        "bird's eye aerial view",
        "intimate medium shot with bokeh",
    ]
    for i, sentence in enumerate(picked):
        style = visual_styles[i % len(visual_styles)]
        enhanced.append(f"{sentence} — {style}")

    return enhanced
