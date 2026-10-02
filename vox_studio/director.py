"""
Master Autonomous Director for Vox Production Studio.
Orchestrates the complete 5-Agent pipeline:
1. Media Crawler Agent (Real maps, historical documents, archival photos)
2. Storyboard & Script Agent (4-Beat Vox narrative with kinetic subtitle beats)
3. Audio Engineer Agent (ElevenLabs broadcast voiceover + Foley sound effects)
4. Motion Director Agent (HyperFrames 2.5D GSAP/WebGL 1080x1920 60fps GPU render)
5. Master Compositor Agent (FFmpeg multi-track audio mixing)
"""
from __future__ import annotations

import json
import re
import subprocess
import time
from pathlib import Path
from typing import Any

from vox_studio.config import (
    OUTPUT_DIR,
    TEMPLATES_DIR,
    VIDEO_DURATION,
    VIDEO_FPS,
    VIDEO_HEIGHT,
    VIDEO_WIDTH,
)
from vox_studio.media_crawler import MediaCrawler
from vox_studio.motion_templates import generate_vox_html
from vox_studio.sfx_engine import (
    generate_cinematic_boom,
    generate_marker_scratch,
    generate_tension_drone,
)
from vox_studio.voice_engine import VoiceEngine
from vox_studio.gemini_rag_scriptwriter import GeminiRAGScriptWriter
from vox_studio.thumbnail_engine import ThumbnailEngine


class StudioDirector:
    """Master orchestrator for automated Vox-style video creation."""

    def __init__(self):
        self.crawler = MediaCrawler()
        self.voice = VoiceEngine()

    def create_video(self, topic: str, niche: str = "dark_mystery") -> Path:
        """Runs the end-to-end 5-Agent automated production pipeline for any topic."""
        t_start = time.time()
        slug = re.sub(r"[^a-zA-Z0-9]+", "_", topic).strip("_").lower()

        print("\n" + "=" * 80)
        print(f"🎬 [VOX PRODUCTION STUDIO] STARTING PRODUCTION: '{topic.upper()}'")
        print("=" * 80)

        # -------------------------------------------------------------
        # STAGE 1: GEMINI RAG STORY INTELLIGENCE & RESEARCH AGENT
        # -------------------------------------------------------------
        print("\n[Stage 1: Gemini RAG Script Agent] Generating trained viral script...")
        story_pkg = GeminiRAGScriptWriter.generate_script_package(topic, niche=niche)

        # -------------------------------------------------------------
        # STAGE 2: MEDIA CRAWLER AGENT (Real Web Video & Archival Maps)
        # -------------------------------------------------------------
        print("\n[Stage 2: Media Crawler Agent] Fetching authentic historical media kit...")
        media_kit = self.crawler.fetch_topic_media(topic)

        # -------------------------------------------------------------
        # STAGE 3: AUDIO ENGINEER AGENT
        # -------------------------------------------------------------
        print("\n[Stage 3: Audio Engineer Agent] Synthesizing ElevenLabs broadcast narration & Foley SFX...")
        voice_raw = OUTPUT_DIR / f"{slug}_voice_raw.mp3"
        voice_mastered = OUTPUT_DIR / f"{slug}_voice_mastered.mp3"
        self.voice.generate_narration(story_pkg["narration_script"], voice_raw, voice_mastered)

        # Synthesize Foley SFX
        drone_wav = OUTPUT_DIR / f"{slug}_drone.wav"
        marker_wav = OUTPUT_DIR / f"{slug}_marker.wav"
        slam_wav = OUTPUT_DIR / f"{slug}_slam.wav"
        generate_tension_drone(drone_wav, duration_sec=16.0)
        generate_marker_scratch(marker_wav, duration_sec=1.4)
        generate_cinematic_boom(slam_wav, duration_sec=2.0)

        # -------------------------------------------------------------
        # STAGE 4: MOTION GRAPHICS AGENT (HyperFrames 2.5D Engine)
        # -------------------------------------------------------------
        print("\n[Stage 4: Motion Graphics Director] Building 2.5D GSAP composition with REAL photos & video...")
        comp_dir = TEMPLATES_DIR / slug
        comp_dir.mkdir(parents=True, exist_ok=True)
        
        has_video = False
        if media_kit.get("videos") and media_kit["videos"][0].exists():
            import shutil
            target_vid = comp_dir / "bg_video.mp4"
            shutil.copy2(media_kit["videos"][0], target_vid)
            has_video = True
            print(f">> [Director] Linked real HD video clip to composition: bg_video.mp4")

        html_content = generate_vox_html(story_pkg, media_kit, has_video=has_video)
        (comp_dir / "index.html").write_text(html_content, encoding="utf-8")

        raw_visuals = OUTPUT_DIR / f"{slug}_visuals.mp4"
        print(f">> Rendering 1080x1920 60fps composition via Chromium GPU...")
        render_cmd = f"npx -y hyperframes render {comp_dir} -o {raw_visuals}"
        t_render = time.time()
        res = subprocess.run(render_cmd, shell=True, capture_output=True, text=True)
        if res.returncode != 0:
            print(f"[ERROR] HyperFrames render error:\n{res.stderr}")
            raise RuntimeError("HyperFrames render failed")
        print(f">> Visuals rendered in {time.time() - t_render:.1f}s")

        # -------------------------------------------------------------
        # STAGE 5: MASTER COMPOSITOR AGENT (FFmpeg Multi-Track Mixing)
        # -------------------------------------------------------------
        print("\n[Stage 5: Master Compositor] Final multi-track audio mixing & master export...")
        master_video = OUTPUT_DIR / f"VOX_{slug.upper()}_MASTER.mp4"

        filter_complex = (
            "[1:a]adelay=200|200,volume=1.0[voice];"
            "[2:a]volume=0.18[drone];"
            "[3:a]adelay=600|600,volume=0.65[slam];"
            "[4:a]adelay=5200|5200,volume=0.75[marker];"
            "[voice][drone][slam][marker]amix=inputs=4:duration=first:dropout_transition=2[aout]"
        )

        composite_cmd = [
            "ffmpeg", "-y",
            "-i", str(raw_visuals),
            "-i", str(voice_mastered),
            "-i", str(drone_wav),
            "-i", str(slam_wav),
            "-i", str(marker_wav),
            "-filter_complex", filter_complex,
            "-map", "0:v",
            "-map", "[aout]",
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "256k",
            "-shortest",
            str(master_video),
        ]
        subprocess.run(composite_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # -------------------------------------------------------------
        # STAGE 6: HIGH-CTR THUMBNAIL AGENT
        # -------------------------------------------------------------
        print("\n[Stage 6: Thumbnail Agent] Generating high-CTR Vox-style thumbnail...")
        thumb_path = OUTPUT_DIR / f"THUMB_{slug.upper()}.jpg"
        bg_img = media_kit["maps"][0] if media_kit["maps"] else (media_kit["photos"][0] if media_kit["photos"] else "")
        ThumbnailEngine.generate_thumbnail(story_pkg, bg_img, thumb_path)

        total_time = time.time() - t_start
        print("\n" + "=" * 80)
        print("🎉 VOX STUDIO MASTER VIDEO & THUMBNAIL GENERATED SUCCESSFULLY!")
        print(f"📁 Output Video:     {master_video}")
        if thumb_path.exists():
            print(f"🖼️ High-CTR Poster:  {thumb_path}")
        print(f"📊 Resolution:       {VIDEO_WIDTH}x{VIDEO_HEIGHT} @ {VIDEO_FPS}fps (9:16 Vertical Shorts)")
        print(f"⏱️ Total Time:       {total_time:.1f}s")
        print("=" * 80)
        return master_video

    def _compose_story_package(self, topic: str) -> dict[str, Any]:
        """Builds topic-tailored Vox documentary story structure and kinetic subtitles."""
        topic_lower = topic.lower()

        if "bermuda" in topic_lower:
            return {
                "headline": "The Bermuda Triangle Mystery",
                "sector": "SECTOR // ATLANTIC 25°00'N 71°00'W",
                "stamp": "TOP SECRET // NAVAL ARCHIVE",
                "badge1": "FLIGHT 19 // DEC 5, 1945",
                "badge2": "5 BOMBERS LOST",
                "climax_q1": "WHERE ARE THE 5 BOMBERS?",
                "climax_q2": "OR WAS IT NEVER AN ACCIDENT?",
                "narration_script": (
                    "Deep inside the Atlantic Ocean... a dark mystery remains. "
                    "On December 5th, 1945... five US Navy bombers vanished into thin air. "
                    "Official naval logs classified it as... swallowed by the sea. "
                    "So what really happened out there?"
                ),
                "subtitles": [
                    "Deep inside the Atlantic Ocean...",
                    "December 5, 1945: 5 Bombers Vanished.",
                    "Classified: Swallowed by the sea.",
                    "So what really happened out there?",
                ],
                "subtitles_json": json.dumps([
                    {"time": 0.3, "text": "Deep inside the Atlantic Ocean..."},
                    {"time": 4.6, "text": "December 5, 1945: 5 Bombers Vanished."},
                    {"time": 8.6, "text": "Classified: Swallowed by the sea."},
                    {"time": 12.1, "text": "So what really happened out there?"},
                ]),
            }
        else:
            return {
                "headline": f"The Mystery of {topic}",
                "sector": f"CASE FILE // {topic.upper()}",
                "stamp": "DECLASSIFIED EVIDENCE",
                "badge1": "PRIMARY EVIDENCE",
                "badge2": "ANOMALY DETECTED",
                "climax_q1": "IS THIS PROOF OF THE UNKNOWN?",
                "climax_q2": "DECIDE FOR YOURSELF.",
                "narration_script": (
                    f"Behind the declassified files of {topic}... an impossible truth was documented. "
                    "Eyewitness reports and military logs were buried for decades. "
                    "Until now."
                ),
                "subtitles": [
                    f"The mystery of {topic}...",
                    "Classified military logs buried.",
                    "Until now.",
                ],
                "subtitles_json": json.dumps([
                    {"time": 0.3, "text": f"The mystery of {topic}..."},
                    {"time": 4.6, "text": "Classified military records."},
                    {"time": 8.6, "text": "Buried for over 50 years."},
                    {"time": 12.1, "text": "What do the files reveal?"},
                ]),
            }
