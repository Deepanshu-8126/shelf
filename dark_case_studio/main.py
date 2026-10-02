"""
Dark Case Studio - Autonomous Documentary Video Production Engine.
Produces Vox / Johnny Harris / Lemmino tier mini-documentaries and viral Shorts:
1. Scrapes real historical facts and public domain archive photos from Wikipedia & Wikimedia API.
2. Generates procedural sound design (sub-bass tension drones, highlighter sweep SFX).
3. Synthesizes deep, authoritative documentary voiceover with sentence cues.
4. Generates animated Ken Burns 2.5D archival motion clips.
5. Generates animated vintage newspaper / declassified document highlighter clips.
6. Composites master 1080p video with kinetic subtitles and audio mixing.

Usage:
  python main.py --topic "Black Dolphin Prison" --format short
  python main.py --topic "Alcatraz" --format doc
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
from timeline_assembler import assemble_documentary_video


STUDIO_DIR = Path("d:/facts_yt/dark_case_studio")
ASSETS_DIR = STUDIO_DIR / "assets"
OUTPUT_DIR = STUDIO_DIR / "output"


def ensure_sfx_assets() -> None:
    """Ensures background tension drones and transition SFX are present."""
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


def produce_documentary(
    topic: str = "Black Dolphin Prison",
    format_type: str = "short",  # "short" (vertical 9:16) or "doc" (horizontal 16:9)
    custom_script: str | None = None,
    key_quote: str = "NOT A SINGLE PRISONER HAS EVER ESCAPED.",
) -> Path:
    print("=" * 65)
    print(f">> DARK CASE STUDIO: Starting Production for [{topic.upper()}]")
    print(f">> Target Format: {format_type.upper()}")
    print("=" * 65)

    ensure_sfx_assets()
    aspect_ratio = "vertical" if format_type == "short" else "horizontal"

    # Step 1: Scrape real archival facts and photos
    print("\n[Step 1/5] Fetching Archival Dossier & Public Domain Photos from Wikipedia...")
    dossier = fetch_case_dossier(topic)
    images = dossier.get("images", [])

    # Step 2: Prepare documentary narrative script
    print("\n[Step 2/5] Formulating Investigative Script & Generating Voiceover...")
    if not custom_script:
        custom_script = (
            f"Deep in the freezing steppes of Russia lies one of the most feared facilities on earth: {topic}. "
            "Within its reinforced steel walls, convicts are kept in twenty-three hour total isolation. "
            f"Government surveillance dossiers confirm a chilling statistic: {key_quote} "
            "Whenever inmates are escorted through the corridors, they are forced bent forward at ninety degrees, blindfolded, completely blind to the world."
        )

    slug = topic.strip().replace(" ", "_")
    voice_audio = OUTPUT_DIR / f"{slug}_voice.mp3"
    voice_audio, cues = generate_voiceover(custom_script, voice_audio, voice_key="deep_narrator")

    # Step 3: Produce Ken Burns Archival Photo Scenes
    print("\n[Step 3/5] Rendering Ken Burns Archival Motion Clips...")
    scenes = []
    
    # Scene 1: Lead Archival Photo (Duration: first ~4.5s)
    lead_img_path = None
    if images:
        lead_img_path = Path(images[0]["path"])

    if lead_img_path and lead_img_path.exists():
        scene1_path = OUTPUT_DIR / f"{slug}_scene1_lead.mp4"
        render_kenburns_clip(
            image_path=lead_img_path,
            output_path=scene1_path,
            duration_sec=4.5,
            aspect_ratio=aspect_ratio,
            badge_text=f"ARCHIVAL DOSSIER: {topic[:16].upper()}",
            zoom_direction="in",
        )
        scenes.append(scene1_path)

    # Scene 2: Animated Newspaper / Declassified Document Highlighter Clip
    print("\n[Step 4/5] Rendering Animated Newspaper Highlighter Evidence Clip...")
    scene2_path = OUTPUT_DIR / f"{slug}_scene2_newspaper.mp4"
    render_highlighter_video(
        headline=f"{topic}: CLASSIFIED PENAL FACILITY",
        dateline="OCTOBER 14, 1999 • SOL-ILETSK, RUSSIA",
        lead_paragraph=dossier.get("extract", "Official classified security records verify continuous isolation.")[:220],
        key_quote=key_quote,
        output_path=scene2_path,
        aspect_ratio=aspect_ratio,
        duration_sec=5.0,
    )
    scenes.append(scene2_path)

    # Scene 3: Second Archival Photo (or zoom-out) for Climax
    photo2_path = None
    if len(images) > 1:
        photo2_path = Path(images[1]["path"])
    elif lead_img_path:
        photo2_path = lead_img_path

    if photo2_path and photo2_path.exists():
        scene3_path = OUTPUT_DIR / f"{slug}_scene3_climax.mp4"
        render_kenburns_clip(
            image_path=photo2_path,
            output_path=scene3_path,
            duration_sec=7.0,
            aspect_ratio=aspect_ratio,
            badge_text="CONFIDENTIAL CLASSIFIED RECORD",
            zoom_direction="out",
        )
        scenes.append(scene3_path)

    # Step 5: Timeline Assembly & Subtitle Burning
    print("\n[Step 5/5] Mixing Sound Design & Burning Master Documentary...")
    master_path = OUTPUT_DIR / f"{slug}_{format_type.upper()}_MASTER.mp4"
    assemble_documentary_video(
        scene_clips=scenes,
        voice_audio=voice_audio,
        cues=cues,
        output_master_video=master_path,
        aspect_ratio=aspect_ratio,
    )

    print("\n" + "=" * 65)
    print(f">> PRODUCTION COMPLETE!")
    print(f">> Master File Ready: {master_path}")
    print("=" * 65)
    return master_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Dark Case Studio Documentary Generator")
    parser.add_argument("--topic", default="Black Dolphin Prison", help="Subject/Crime/Mystery topic")
    parser.add_argument("--format", default="short", choices=["short", "doc"], help="Target video format")
    parser.add_argument("--quote", default="NOT A SINGLE PRISONER HAS EVER ESCAPED.", help="Key quote to highlight")
    args = parser.parse_args()

    produce_documentary(
        topic=args.topic,
        format_type=args.format,
        key_quote=args.quote,
    )
