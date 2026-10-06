"""
Unified Configuration for Vox Production Studio.
Consolidates all paths, API keys, and production standards.
"""
from pathlib import Path
import os

STUDIO_ROOT = Path(__file__).resolve().parent
WORKSPACE_ROOT = STUDIO_ROOT.parent

# Directories
ASSETS_DIR = STUDIO_ROOT / "assets"
IMAGES_DIR = ASSETS_DIR / "real_images"
VIDEOS_DIR = ASSETS_DIR / "video_clips"
SFX_DIR = ASSETS_DIR / "sfx"
TEMPLATES_DIR = STUDIO_ROOT / "templates"
OUTPUT_DIR = STUDIO_ROOT / "output"

for d in [ASSETS_DIR, IMAGES_DIR, VIDEOS_DIR, SFX_DIR, TEMPLATES_DIR, OUTPUT_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# Environment Configuration
def _load_root_env():
    candidates = [
        STUDIO_ROOT / ".env",
        STUDIO_ROOT.parent / ".env",
        STUDIO_ROOT.parent.parent / ".env",
        Path("d:/facts_yt/.env"),
    ]
    for env_file in candidates:
        if env_file.exists():
            for line in env_file.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, val = line.split("=", 1)
                key = key.strip()
                val = val.strip().strip('"').strip("'")
                if key and key not in os.environ:
                    os.environ[key] = val

_load_root_env()


ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "sk_f27562b3dda4dd4c2b6bda43c7205548e5a35bc966403310")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY", "")
PIXABAY_API_KEY = os.getenv("PIXABAY_API_KEY", "")

VOICE_ID = "nPczCjzI2devNBz1zQrb"  # Brian - Deep Cinematic Vox/Johnny Harris Narrator
MODEL_ID = "eleven_multilingual_v2"  # More expressive, human breathing & dynamic inflection
VOICE_STABILITY = 0.32  # Low stability for natural human vocal emotion & suspense
VOICE_STYLE = 0.45      # High narrative weight
VOICE_SIMILARITY = 0.82


# Video Standards
VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920
VIDEO_FPS = 60
VIDEO_DURATION = 15.0  # Seconds per short
