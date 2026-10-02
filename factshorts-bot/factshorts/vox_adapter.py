"""
Vox Studio Adapter for FactShorts Bot (Channel 1 Upgrade).
Upgrades standard fact generation to 2.5D Vox Motion Graphics with:
- Real authentic NASA / Historical photographs & video stream slicing
- ElevenLabs Brian cinematic voiceover with dramatic breath pauses
- 3D paper fold / coordinate map overlays
- Spring-physics glowing pop-up karaoke captions
- Auto High-CTR YouTube Shorts thumbnail generation
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


class VoxFactshortsEngine:
    """Seamless bridge that executes the 5-Agent Vox Studio for FactShorts channel."""

    def __init__(self):
        self.director = StudioDirector()

    def render_fact_short(self, topic: str) -> dict[str, Any]:
        """Renders a 1080x1920 60fps Vox-grade short with real evidence and Brian narration."""
        print(f"\n🚀 [VoxFactshortsEngine] Upgrading Channel 1 generation for: '{topic}'...")
        master_mp4 = self.director.create_video(topic)
        slug = topic.strip().lower().replace(" ", "_")
        thumb_path = WORKSPACE_ROOT / "vox_studio" / "output" / f"THUMB_{slug.upper()}.jpg"

        return {
            "status": "success",
            "video_path": str(master_mp4),
            "thumbnail_path": str(thumb_path) if thumb_path.exists() else None,
            "topic": topic,
            "resolution": "1080x1920 @ 60fps",
            "engine": "Vox Studio 2.5D HyperFrames",
        }
