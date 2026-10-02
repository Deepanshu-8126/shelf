"""
Vox Studio Adapter for YouTube Agent Studio (Channel 2 Upgrade).
Upgrades Dark Case / Mystery storytelling to 2.5D Vox Motion Graphics:
- 1945 Declassified military logs & archival crime/mystery footage
- Full-screen nautical/topographic map tracking with glowing coordinate vectors
- ElevenLabs Brian cinematic true-crime narration
- 3D paper fold with synchronized yellow marker wipe
- High-CTR Declassified Dossier thumbnail generator
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from vox_studio.director import StudioDirector
from vox_studio.story_intelligence import StoryIntelligence
from vox_studio.thumbnail_engine import ThumbnailEngine


class VoxDarkCaseEngine:
    """Seamless bridge for Channel 2 to produce Vox-style documentary shorts."""

    def __init__(self):
        self.director = StudioDirector()

    def produce_dark_case_short(self, case_topic: str) -> dict[str, Any]:
        """Produces a 1080x1920 60fps declassified case documentary short."""
        print(f"\n🕵️ [VoxDarkCaseEngine] Producing Channel 2 Vox Master for: '{case_topic}'...")
        master_mp4 = self.director.create_video(case_topic)
        slug = case_topic.strip().lower().replace(" ", "_")
        thumb_path = WORKSPACE_ROOT / "vox_studio" / "output" / f"THUMB_{slug.upper()}.jpg"

        return {
            "status": "success",
            "video_path": str(master_mp4),
            "thumbnail_path": str(thumb_path) if thumb_path.exists() else None,
            "case_topic": case_topic,
            "resolution": "1080x1920 @ 60fps",
            "engine": "Vox Studio 2.5D Declassified Engine",
        }
