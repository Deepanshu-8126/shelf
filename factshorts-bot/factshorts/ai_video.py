"""Verified Open-Source AI Video Generation Models (September 2026).

Registry of 100% Free (₹0), Commercial-Safe, Verified Open-Weight Video Models:
1. PRIMARY: LTX-2.3 (Lightricks)
   - 20s, 4K, 50fps, Native Audio
   - Q4_K_M GGUF: 16GB VRAM (Kaggle T4 compatible)
   - LoRA Fine-tuning supported (character consistency)
   - HuggingFace: Lightricks/LTX-2.3 | License: LTX Community (<$10M ARR)
2. SECONDARY: Wan 2.2 (Alibaba)
   - 5s, 720p, Apache 2.0
   - T2V (Wan-AI/Wan2.2-T2V-A14B), I2V (Wan-AI/Wan2.2-I2V-A14B), FLF2V (Wan-AI/Wan2.2-FLF2V-14B)
   - 14-16GB VRAM (Kaggle T4 compatible)
3. LONG-FORM: HunyuanVideo 1.5 (Tencent)
   - 75s, 8.3B params, Apache 2.0
   - 16GB VRAM (Kaggle T4 compatible)
4. WEBSITE IMAGERY: Z-Image-Turbo (Image only)

BLACKLISTED / CLOSED / FAKE MODELS (DO NOT USE):
- Wan 3.0 (API-only, PAID, no weights)
- Wan 2.7 (API-only, no weights)
- HappyHorse (no weights, no code)
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .config import Config, get_config
from .utils import module_logger

log = module_logger("ai_video")


@dataclass
class VideoModelSpec:
    name: str
    provider: str
    repo_id: str
    license: str
    commercial_safe: bool
    vram_gb: int
    duration_sec: int
    resolution: str
    native_audio: bool
    lora_support: bool
    use_case: str
    is_verified: bool = True
    hardware_target: str = "16GB VRAM (Kaggle T4 / Local GPU)"


# Verified 2026 Model Catalog
VERIFIED_MODELS: dict[str, VideoModelSpec] = {
    "ltx-2.3": VideoModelSpec(
        name="LTX-2.3",
        provider="Lightricks",
        repo_id="Lightricks/LTX-2.3",
        license="LTX Community (Free under $10M ARR)",
        commercial_safe=True,
        vram_gb=16,
        duration_sec=20,
        resolution="4K @ 50fps",
        native_audio=True,
        lora_support=True,
        use_case="FactShorts (20s + audio in 1 step) & AI Influencer Character Videos",
        is_verified=True,
    ),
    "wan-2.2": VideoModelSpec(
        name="Wan 2.2",
        provider="Alibaba",
        repo_id="Wan-AI/Wan2.2-T2V-A14B",
        license="Apache 2.0",
        commercial_safe=True,
        vram_gb=14,
        duration_sec=5,
        resolution="720p",
        native_audio=False,
        lora_support=True,
        use_case="Cinematic 5s B-roll & First/Last Frame Transitions (FLF2V)",
        is_verified=True,
    ),
    "hunyuan-1.5": VideoModelSpec(
        name="HunyuanVideo 1.5",
        provider="Tencent",
        repo_id="Tencent/HunyuanVideo-1.5",
        license="Apache 2.0",
        commercial_safe=True,
        vram_gb=16,
        duration_sec=75,
        resolution="1080p",
        native_audio=False,
        lora_support=False,
        use_case="Long-form YouTube Documentary & Deep-Dive Explainer Scenes",
        is_verified=True,
    ),
    "z-image-turbo": VideoModelSpec(
        name="Z-Image-Turbo",
        provider="Open-Community",
        repo_id="Z-Image/Turbo",
        license="Apache 2.0",
        commercial_safe=True,
        vram_gb=8,
        duration_sec=0,
        resolution="1024x1024",
        native_audio=False,
        lora_support=True,
        use_case="Website Hero Imagery & YouTube Thumbnails (Image Only)",
        is_verified=True,
    ),
}

# Blacklist of API-only / Paid / Fake models
UNVERIFIED_BLACKLIST = {
    "wan-3.0": "API-only, PAID, no weights released",
    "wan-2.7": "API-only, no weights released",
    "happyhorse": "Fake announcement, no weights, no open-source code",
    "musicgen": "Weights are CC-BY-NC 4.0 (Non-commercial, copyright strike risk)",
}


def is_model_verified(model_name: str) -> tuple[bool, str]:
    """Checks whether a video generation model is verified free and open-source."""
    key = model_name.strip().lower().replace(" ", "-")
    if key in UNVERIFIED_BLACKLIST:
        return False, f"BANNED: {UNVERIFIED_BLACKLIST[key]}"
    if key in VERIFIED_MODELS:
        return True, "VERIFIED: 100% Free, Open-Weight, Commercial-Safe"
    return False, "UNKNOWN: Model not in verified September 2026 registry"


def get_recommended_model(use_case: str) -> VideoModelSpec:
    """Returns the optimal verified model for a given use-case."""
    u = use_case.lower()
    if "short" in u or "fact" in u or "influencer" in u:
        return VERIFIED_MODELS["ltx-2.3"]
    if "long" in u or "documentary" in u or "youtube" in u:
        return VERIFIED_MODELS["hunyuan-1.5"]
    if "b-roll" in u or "clip" in u or "transition" in u:
        return VERIFIED_MODELS["wan-2.2"]
    if "web" in u or "thumb" in u or "image" in u:
        return VERIFIED_MODELS["z-image-turbo"]
    return VERIFIED_MODELS["ltx-2.3"]


def get_model_specs_summary() -> list[dict[str, Any]]:
    """Returns a clean serializable list of all verified model specs."""
    return [
        {
            "name": m.name,
            "provider": m.provider,
            "license": m.license,
            "vram": f"{m.vram_gb}GB",
            "duration": f"{m.duration_sec}s" if m.duration_sec > 0 else "Image",
            "resolution": m.resolution,
            "native_audio": "✅ Yes" if m.native_audio else "❌ No",
            "lora": "✅ Yes" if m.lora_support else "❌ No",
            "use_case": m.use_case,
            "hardware": m.hardware_target,
        }
        for m in VERIFIED_MODELS.values()
    ]


# -----------------------------------------------------------------------------
# Remote Kaggle / Local GPU Worker Client (Wan 2.2 / LTX-2.3 / Z-Image-Turbo)
# -----------------------------------------------------------------------------
async def check_gpu_worker_health(cfg: Config | None = None) -> dict[str, Any]:
    """Check connectivity and loaded models on the remote GPU worker (Kaggle/Colab/Local)."""
    import httpx
    cfg = cfg or get_config()
    worker_url = getattr(cfg, "gpu_worker_url", "")
    if not worker_url:
        return {"online": False, "reason": "No GPU_WORKER_URL configured in .env"}

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(4.0)) as client:
            resp = await client.get(f"{worker_url.rstrip('/')}/health")
            if resp.status_code == 200:
                data = resp.json()
                return {"online": True, **data}
            return {"online": False, "status_code": resp.status_code}
    except Exception as exc:
        return {"online": False, "reason": str(exc)}


async def generate_remote_video(
    prompt: str,
    output_path: Path,
    model: str = "wan-2.2",
    duration: float = 5.0,
    cfg: Config | None = None,
) -> Path | None:
    """Generate real AI video clip using Wan 2.2 or LTX-2.3 running on Kaggle GPU / remote worker.

    100% Free, Apache 2.0 / LTX Community license, NO paid API.
    Returns path to downloaded MP4 clip, or None if worker is unavailable.
    """
    import httpx
    cfg = cfg or get_config()
    worker_url = getattr(cfg, "gpu_worker_url", "")
    if not worker_url:
        log.debug("No GPU_WORKER_URL set — skipping remote Wan/LTX video generation")
        return None

    norm_model = model.strip().lower()
    endpoint = f"{worker_url.rstrip('/')}/generate_video"
    payload = {
        "prompt": prompt,
        "model": norm_model,
        "duration": duration,
        "aspect_ratio": "9:16",
        "width": 720,
        "height": 1280,
    }

    log.info("Requesting AI video from GPU worker: model=%s (%.1fs) -> %s", norm_model, duration, endpoint)
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(300.0)) as client:
            resp = await client.post(endpoint, json=payload)

        if resp.status_code != 200:
            log.warning("GPU worker video generation failed HTTP %d: %s", resp.status_code, resp.text[:200])
            return None

        # Check if response is raw MP4 bytes or JSON with download URL / base64
        content_type = resp.headers.get("content-type", "")
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if "video" in content_type or "octet-stream" in content_type:
            output_path.write_bytes(resp.content)
            log.info("Real AI video generated (%s): %s (%.1f MB)",
                     norm_model, output_path.name, len(resp.content) / (1024 * 1024))
            return output_path

        data = resp.json()
        if "video_base64" in data:
            import base64
            video_bytes = base64.b64decode(data["video_base64"])
            output_path.write_bytes(video_bytes)
            log.info("Real AI video generated from b64 (%s): %s", norm_model, output_path.name)
            return output_path

        if "video_url" in data:
            video_url = data["video_url"]
            async with httpx.AsyncClient(timeout=httpx.Timeout(120.0)) as dl_client:
                dl_resp = await dl_client.get(video_url)
                if dl_resp.status_code == 200:
                    output_path.write_bytes(dl_resp.content)
                    log.info("Real AI video downloaded (%s): %s", norm_model, output_path.name)
                    return output_path

        log.warning("Worker returned JSON without usable video data: %s", list(data.keys()))
        return None

    except Exception as exc:
        log.warning("GPU worker video generation exception: %s", exc)
        return None


async def generate_remote_image_z_turbo(
    prompt: str,
    output_path: Path,
    cfg: Config | None = None,
) -> Path | None:
    """Generate image via Z-Image-Turbo (Apache 2.0, FREE) on Kaggle/local worker.

    Returns path to PNG image, or None if unavailable.
    """
    import base64
    import httpx
    cfg = cfg or get_config()
    worker_url = getattr(cfg, "gpu_worker_url", "")
    if not worker_url:
        return None

    endpoint = f"{worker_url.rstrip('/')}/generate_image"
    payload = {
        "prompt": prompt,
        "model": "z-image-turbo",
        "aspect_ratio": "9:16",
        "width": 1024,
        "height": 1792,
    }

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(120.0)) as client:
            resp = await client.post(endpoint, json=payload)

        if resp.status_code != 200:
            log.warning("Z-Image-Turbo worker failed HTTP %d: %s", resp.status_code, resp.text[:200])
            return None

        content_type = resp.headers.get("content-type", "")
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if "image" in content_type:
            output_path.write_bytes(resp.content)
            log.info("Z-Image-Turbo generated image: %s (%d KB)", output_path.name, len(resp.content) // 1024)
            return output_path

        data = resp.json()
        if "image_base64" in data:
            image_bytes = base64.b64decode(data["image_base64"])
            output_path.write_bytes(image_bytes)
            log.info("Z-Image-Turbo decoded b64 image: %s", output_path.name)
            return output_path

        return None
    except Exception as exc:
        log.debug("Z-Image worker error: %s", exc)
        return None

