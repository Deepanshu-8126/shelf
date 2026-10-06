"""
Master Director & Multi-Layer Cinema Engine (OpenMontage + HyperFrames + MoneyPrinter Hybrid).
Builds Blender/After Effects grade automated documentaries purely through code:
- Scene 1 (0-3s): Tactical Radar Recon Hook (3D/Canvas HUD with rotating sweep & target lock)
- Scene 2 (3-8s): Vox / Johnny Harris Declassified Newspaper Highlighter sweep with SFX
- Scene 3 (8-16s): Ken Burns 2.5D Archival Photo Motion with evidence badges & dark vignette
- Scene 4 (16-24s): Tactical Map / Coordinate Escalation
- Scene 5 (24-30s): Climax Mystery Reveal
- Sound Design: Procedural 50Hz sub-bass suspense drone + felt-tip marker squeak + transition booms
- Captions: High-retention word-by-word kinetic captions in universal safe zones (above 300px dead zone)
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Ensure UTF-8 output on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from wiki_archival_scraper import fetch_case_dossier
from sfx_generator import generate_tension_drone, generate_marker_scratch, generate_cinematic_boom
from voice_engine import generate_voiceover
from kenburns_engine import render_kenburns_clip
from document_highlighter import render_highlighter_video
from map_engine import render_map_locator_clip
from timeline_assembler import assemble_documentary_video


STUDIO_DIR = Path(__file__).resolve().parent
ASSETS_DIR = STUDIO_DIR / "assets"
OUTPUT_DIR = STUDIO_DIR / "output"


def ensure_sound_design() -> None:
    sfx_dir = ASSETS_DIR / "sfx"
    sfx_dir.mkdir(parents=True, exist_ok=True)
    drone = sfx_dir / "drone_suspense.wav"
    marker = sfx_dir / "marker_sweep.wav"
    boom = sfx_dir / "transition_boom.wav"

    if not drone.exists():
        generate_tension_drone(drone, duration_sec=60.0)
    if not marker.exists():
        generate_marker_scratch(marker, duration_sec=2.0)
    if not boom.exists():
        generate_cinematic_boom(boom, duration_sec=2.5)


def produce_cinematic_short(
    topic: str = "The Lost City of Atlantis",
    coordinates: str = "31°12'N 24°00'W // MID-ATLANTIC RIDGE",
    headline: str = "ATLANTIS: ADVANCED SUBMERGED CIVILIZATION",
    key_quote: str = "SANK BENEATH THE OCEAN IN A SINGLE DAY.",
    custom_script: str | None = None,
) -> Path:
    print("=" * 70)
    print(f">> [OPENMONTAGE + HYPERFRAMES MASTER DIRECTOR]")
    print(f">> Producing Blender-Grade Cinema Short for: {topic.upper()}")
    print("=" * 70)

    ensure_sound_design()
    slug = topic.strip().replace(" ", "_").replace("'", "")
    aspect_ratio = "vertical"  # 1080x1920 Universal 9:16

    # 1. Fetch Real Archival Media
    print("\n[Layer 1/5: Archival Intelligence] Querying Wikimedia & Public Domain Dossier...")
    dossier = None
    try:
        dossier = fetch_case_dossier(topic)
    except Exception as e:
        print(f">> Fallback to investigative dossier: {e}")
        dossier = {"extract": "Classified oceanographic expedition records confirm underwater geometric structures.", "images": []}

    images = dossier.get("images", [])

    # 2. OpenMontage Narrative Architecture (Psychological 4-Part Hook)
    print("\n[Layer 2/5: Psychological Scripting & Voice Narration]...")
    if not custom_script:
        custom_script = (
            f"Over eleven thousand years ago, an advanced civilization vanished without a trace: {topic}. "
            "Plato's ancient declassified records describe a metropolis powered by unknown energy. "
            f"Official texts confirm the disaster: {key_quote} "
            "Modern deep-sea satellite telemetry reveals massive concentric ring structures buried beneath kilometers of ocean sediment. "
            "Was it just a myth, or the world's greatest cover-up?"
        )

    voice_audio = OUTPUT_DIR / f"{slug}_voice.mp3"
    voice_audio, cues = generate_voiceover(custom_script, voice_audio, voice_key="deep_narrator")

    # 3. Code-Generated Motion Graphics & 3D Radar (HyperFrames Standard)
    print("\n[Layer 3/5: Rendering Code-Based Motion Graphics (Blender Alternative)]...")
    scenes = []

    # Scene 1: Tactical Satellite Radar Hook (0.0s - 3.5s)
    scene1_radar = OUTPUT_DIR / f"{slug}_scene1_radar.mp4"
    render_map_locator_clip(
        location_name=topic,
        coordinates=coordinates,
        output_path=scene1_radar,
        aspect_ratio=aspect_ratio,
        duration_sec=3.5,
    )
    scenes.append(scene1_radar)

    # Scene 2: Vox Declassified Document Highlighter (3.5s - 8.5s)
    scene2_newspaper = OUTPUT_DIR / f"{slug}_scene2_newspaper.mp4"
    render_highlighter_video(
        headline=headline,
        dateline="ARCHIVAL DOSSIER // DEEP SEA EXPEDITION",
        lead_paragraph=dossier.get("extract", "Oceanographic sonar readings indicate artificial anomalies.")[:200],
        key_quote=key_quote,
        output_path=scene2_newspaper,
        aspect_ratio=aspect_ratio,
        duration_sec=5.0,
    )
    scenes.append(scene2_newspaper)

    # Scene 3: Archival Photo Ken Burns Drift (8.5s - 15.0s)
    lead_img = None
    if images:
        lead_img = Path(images[0]["path"])

    if lead_img and lead_img.exists():
        scene3_photo = OUTPUT_DIR / f"{slug}_scene3_archive.mp4"
        render_kenburns_clip(
            image_path=lead_img,
            output_path=scene3_photo,
            duration_sec=6.5,
            aspect_ratio=aspect_ratio,
            badge_text=f"EVIDENCE DOSSIER: {topic[:16].upper()}",
            zoom_direction="in",
        )
        scenes.append(scene3_photo)
    else:
        # Fallback to secondary radar scan zoom
        scene3_photo = OUTPUT_DIR / f"{slug}_scene3_radar_zoom.mp4"
        render_map_locator_clip(
            location_name="AZORES SEAMOUNT ANOMALY",
            coordinates="36°58'N 25°02'W // DEPTH: 3,200M",
            output_path=scene3_photo,
            aspect_ratio=aspect_ratio,
            duration_sec=6.5,
        )
        scenes.append(scene3_photo)

    # Scene 4: Climax Ken Burns or Final Telemetry (15.0s - end)
    second_img = None
    if len(images) > 1:
        second_img = Path(images[1]["path"])
    elif lead_img:
        second_img = lead_img

    if second_img and second_img.exists():
        scene4_climax = OUTPUT_DIR / f"{slug}_scene4_climax.mp4"
        render_kenburns_clip(
            image_path=second_img,
            output_path=scene4_climax,
            duration_sec=8.0,
            aspect_ratio=aspect_ratio,
            badge_text="CONFIDENTIAL CLASSIFIED RECORD",
            zoom_direction="out",
        )
        scenes.append(scene4_climax)
    else:
        scene4_climax = OUTPUT_DIR / f"{slug}_scene4_climax_radar.mp4"
        render_map_locator_clip(
            location_name="BURIED CONCENTRIC ANOMALY",
            coordinates="STATUS: UNEXPLAINED // RESTRICTED",
            output_path=scene4_climax,
            aspect_ratio=aspect_ratio,
            duration_sec=8.0,
        )
        scenes.append(scene4_climax)

    # 4. Master Timeline Assembly, Kinetic Subtitles & Sound Design
    print("\n[Layer 4/5: Timeline Assembly & Kinetic Subtitle Burning]...")
    master_output = OUTPUT_DIR / f"{slug}_CINEMA_MASTER.mp4"
    assemble_documentary_video(
        scene_clips=scenes,
        voice_audio=voice_audio,
        cues=cues,
        output_master_video=master_output,
        aspect_ratio=aspect_ratio,
    )

    print("\n" + "=" * 70)
    print(f">> [SUCCESS] Master Cinema Video Rendered!")
    print(f">> Output File: {master_output}")
    print("=" * 70)
    return master_output


if __name__ == "__main__":
    produce_cinematic_short(
        topic="The Lost City of Atlantis",
        coordinates="31°12'N 24°00'W // MID-ATLANTIC RIDGE",
        headline="ATLANTIS: SUBMERGED METROPOLIS CONFIRMED",
        key_quote="SANK BENEATH THE OCEAN IN A SINGLE DAY.",
    )
