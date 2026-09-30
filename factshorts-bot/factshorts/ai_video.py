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
