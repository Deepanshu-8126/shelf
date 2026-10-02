"""Central config. Override anything with env vars or CLI flags."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORK = Path(os.getenv("CLIPPER_WORK", ROOT / "out"))

# Edge-TTS neural voices (free, no API key). Full list: `edge-tts --list-voices`
VOICES = {
    "en": "en-US-ChristopherNeural",
    "en-f": "en-US-AriaNeural",
    "es": "es-ES-AlvaroNeural",
    "es-mx": "es-MX-JorgeNeural",
    "es-f": "es-ES-ElviraNeural",
}


@dataclass
class Settings:
    # --- transcription ---
    whisper_model: str = os.getenv("WHISPER_MODEL", "base")  # tiny|base|small|medium|large-v3
    whisper_backend: str = os.getenv("WHISPER_BACKEND", "faster")  # faster|openai

    # --- clip selection ---
    min_clip_s: float = 18.0
    max_clip_s: float = 58.0
    clips_per_video: int = 3
    llm_model: str = os.getenv("LLM_MODEL", "gpt-4o-mini")
    llm_api_key: str | None = os.getenv("OPENAI_API_KEY")

    # --- languages / voice ---
    languages: list[str] = field(default_factory=lambda: ["en", "es"])
    dub: bool = True          # generate TTS voiceover track
    keep_original_audio: float = 0.08  # duck original under the dub (0 = mute)

    # --- render ---
    width: int = 1080
    height: int = 1920
    fps: int = 30
    crf: int = 20
    font: str = os.getenv("CLIPPER_FONT", "Arial")
    caption_style: str = "karaoke"  # karaoke|block|none

    # --- output ---
    emit_capcut_draft: bool = True
    work_dir: Path = WORK


settings = Settings()
