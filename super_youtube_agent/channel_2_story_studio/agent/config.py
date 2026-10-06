from __future__ import annotations

import os
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
PACKAGES_DIR = DATA_DIR / "packages"
SECRETS_DIR = ROOT / "secrets"
DB_PATH = DATA_DIR / "creatorops.sqlite3"
WEB_DIR = ROOT / "web"


def load_local_env() -> None:
    """Load root workspace .env then local .env without overriding real environment vars."""
    paths = [Path("d:/facts_yt/.env"), ROOT.parent.parent / ".env", ROOT.parent / ".env", ROOT / ".env"]
    for env_path in paths:

        if not env_path.exists():
            continue
        for raw in env_path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key:
                os.environ.setdefault(key, value)


load_local_env()


def env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


def readiness() -> dict:
    yt_data_key = bool(env("YOUTUBE_DATA_API_KEY"))
    gemini_key = bool(env("GEMINI_API_KEY"))
    llm_compat = bool(env("LLM_API_KEY") and env("LLM_BASE_URL"))
    elevenlabs = bool(env("ELEVENLABS_API_KEY") and env("ELEVENLABS_VOICE_ID"))
    edge_voice = bool(env("EDGE_TTS_VOICE"))
    try:
        import edge_tts  # noqa: F401
        edge_installed = True
    except Exception:
        edge_installed = False
    voice_connected = elevenlabs or (edge_voice and edge_installed)
    voice_provider = "ElevenLabs" if elevenlabs else ("Edge TTS · network service" if edge_voice and edge_installed else "Not configured")
    ffmpeg_binary = env("FFMPEG_BINARY")
    ffmpeg_available = bool(shutil.which(ffmpeg_binary) if ffmpeg_binary else shutil.which("ffmpeg"))
    if not ffmpeg_available:
        try:
            import imageio_ffmpeg  # noqa: F401
            ffmpeg_available = True
        except Exception:
            pass
    client_file = env("YOUTUBE_OAUTH_CLIENT_FILE", "secrets/client_secret.json")
    client_path = (ROOT / client_file).resolve() if not Path(client_file).is_absolute() else Path(client_file)
    token_dir = SECRETS_DIR / "tokens"
    tokens = sorted(p.stem for p in token_dir.glob("*.json")) if token_dir.exists() else []
    try:
        import cv2  # noqa: F401
        import PIL  # noqa: F401
        renderer = True
    except Exception:
        renderer = False
    return {
        "mode": "live" if yt_data_key else "demo",
        "research_connected": yt_data_key,
        "llm_connected": gemini_key or llm_compat,
        "llm_provider": "Gemini" if gemini_key else ("OpenAI-compatible" if llm_compat else "Template fallback"),
        "voice_connected": voice_connected,
        "voice_provider": voice_provider,
        "edge_tts_available": edge_installed,
        "ffmpeg_available": ffmpeg_available,
        "youtube_oauth_client_ready": client_path.exists(),
        "authorized_channels": tokens,
        "renderer_available": renderer,
        "auto_draft_enabled": env("AUTO_DRAFT_ENABLED", "false").lower() == "true",
        "auto_publish_enabled": env("AUTO_PUBLISH_ENABLED", "false").lower() == "true",
        "default_privacy": env("DEFAULT_PRIVACY", "private").lower(),
        "secrets_are_never_returned": True,
    }
