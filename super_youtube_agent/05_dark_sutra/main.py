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

try:
    from .wiki_archival_scraper import fetch_case_dossier
    from .sfx_generator import generate_tension_drone, generate_marker_scratch, generate_cinematic_boom
    from .voice_engine import generate_voiceover
    from .kenburns_engine import render_kenburns_clip
    from .document_highlighter import render_highlighter_video
    from .timeline_assembler import assemble_documentary_video
    from .dark_sutra_brain import generate_dark_sutra_script
    from .image_fetcher import RealImageFetcher
    from .comfyui_api import is_comfyui_online, generate_crime_scene, ComfyUIClient
    from .dark_crime_prompts import get_visual_prompt, CRIME_PROMPTS
except ImportError:
    from wiki_archival_scraper import fetch_case_dossier
    from sfx_generator import generate_tension_drone, generate_marker_scratch, generate_cinematic_boom
    from voice_engine import generate_voiceover
    from kenburns_engine import render_kenburns_clip
    from document_highlighter import render_highlighter_video
    from timeline_assembler import assemble_documentary_video
    from dark_sutra_brain import generate_dark_sutra_script
    from image_fetcher import RealImageFetcher
    from comfyui_api import is_comfyui_online, generate_crime_scene, ComfyUIClient
    from dark_crime_prompts import get_visual_prompt, CRIME_PROMPTS

try:
    from super_youtube_agent.engines.enhancer_engine import enhance_video_4k, build_ass_subtitle_file
    from super_youtube_agent.engines.seo_schema_generator import build_video_schema, export_schema_json_ld
except ImportError:
    try:
        from engines.enhancer_engine import enhance_video_4k, build_ass_subtitle_file
        from engines.seo_schema_generator import build_video_schema, export_schema_json_ld
    except ImportError:
        enhance_video_4k = None
        build_ass_subtitle_file = None
        build_video_schema = None
        export_schema_json_ld = None


STUDIO_DIR = Path(__file__).resolve().parent
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
    topic: str = "Burari Deaths",
    format_type: str = "short",  # "short" (vertical 9:16) or "doc" (horizontal 16:9)
    custom_script: str | None = None,
    key_quote: str | None = None,
    language: str = "hindi",
    voice_key: str = "hm_omega",
    quality: str = "4k",
    caption_style: str = "dark_dossier",
) -> Path:
    print("=" * 70)
    print(f">> [CHANNEL 5: DARK SUTRA CRIME STUDIO] Starting Production for: [{topic.upper()}]")
    print(f">> Format: {format_type.upper()} | Language: {language.upper()} | Voice: {voice_key}")
    print("=" * 70)

    ensure_sfx_assets()
    aspect_ratio = "vertical" if format_type == "short" else "horizontal"

    # Step 1: Ingest Multi-Source Visual Assets (Wikimedia + Pexels + Pixabay)
    print("\n[Step 1/5] Ingesting Authentic Visuals & Real Wallpapers (Pexels, Pixabay, Wikimedia)...")
    fetcher = RealImageFetcher(cache_dir=ASSETS_DIR / "media_pool")
    pool_images = fetcher.fetch_smart_broll(topic, count=4, orientation=aspect_ratio)
    
    # Also fetch case dossier
    dossier = fetch_case_dossier(topic)
    wiki_images = [Path(img["path"]) for img in dossier.get("images", []) if Path(img["path"]).exists()]
    all_images = pool_images + wiki_images

    # Step 2: Formulate Hindi/Hinglish Documentary Script via Dark Sutra Brain
    print("\n[Step 2/5] Formulating Investigative Script via Dark Sutra AI Brain...")
    intel = generate_dark_sutra_script(topic, format_type=format_type, language=language)
    
    script_text = custom_script or intel.get("script", "")
    quote_text = key_quote or intel.get("key_quote", "NO SURVIVORS WERE FOUND.")
    headline_text = intel.get("headline", f"{topic[:20].upper()}: THE REDACTED DOSSIER")
    dateline_text = intel.get("dateline", "CLASSIFIED POLICE DOSSIER • ARCHIVAL RECORD")

    slug = topic.strip().replace(" ", "_")
    voice_audio = OUTPUT_DIR / f"{slug}_voice.mp3"
    voice_audio, cues = generate_voiceover(script_text, voice_audio, voice_name=voice_key)

    # Step 3: Produce Visual Scenes (Hybrid: ComfyUI Wan 2.2 GPU or OpenReels Ken Burns CPU)
    scenes = []
    use_wan_ai = is_comfyui_online()
    if use_wan_ai:
        print("\n[Step 3/5] 🔥 ComfyUI Active on Local GPU! Generating Cinematic Wan 2.2 Video Clips...")
    else:
        print("\n[Step 3/5] ComfyUI Offline. Generating OpenReels Ken Burns & Archival Motion Clips...")

    # Scene 1: Lead Visual (Wan 2.2 AI Clip or Ken Burns Archival)
    scene1_path = OUTPUT_DIR / f"{slug}_scene1_lead.mp4"
    if use_wan_ai:
        prompt_1 = get_visual_prompt("mystery_location", topic)["sd_prompt"]
        wan_clip1 = generate_crime_scene(prompt_1, scene1_path)
        if wan_clip1 and wan_clip1.exists():
            scenes.append(wan_clip1)

    if not scenes:  # Fallback to Ken Burns archival photo
        lead_img_path = all_images[0] if all_images else None
        if lead_img_path and lead_img_path.exists():
            render_kenburns_clip(
                image_path=lead_img_path,
                output_path=scene1_path,
                duration_sec=4.5,
                aspect_ratio=aspect_ratio,
                badge_text=f"DARK SUTRA: {topic[:16].upper()}",
                zoom_direction="in",
            )
            scenes.append(scene1_path)

    # Scene 2: Animated Newspaper / Declassified Document Highlighter Clip
    print("\n[Step 4/5] Rendering Animated Newspaper Highlighter Evidence Clip...")
    scene2_path = OUTPUT_DIR / f"{slug}_scene2_newspaper.mp4"
    render_highlighter_video(
        headline=headline_text,
        dateline=dateline_text,
        lead_paragraph=dossier.get("extract", script_text)[:220],
        key_quote=quote_text,
        output_path=scene2_path,
        aspect_ratio=aspect_ratio,
        duration_sec=5.0,
    )
    scenes.append(scene2_path)

    # Scene 3: Climax Scene (Wan 2.2 Forensic / Crime Scene Clip or Ken Burns)
    scene3_path = OUTPUT_DIR / f"{slug}_scene3_climax.mp4"
    if use_wan_ai:
        prompt_3 = get_visual_prompt("crime_scene", topic)["sd_prompt"]
        wan_clip3 = generate_crime_scene(prompt_3, scene3_path)
        if wan_clip3 and wan_clip3.exists():
            scenes.append(wan_clip3)

    if len(scenes) < 3:  # Fallback to Ken Burns archival photo2
        photo2_path = all_images[1] if len(all_images) > 1 else (all_images[0] if all_images else None)
        if photo2_path and photo2_path.exists():
            render_kenburns_clip(
                image_path=photo2_path,
                output_path=scene3_path,
                duration_sec=5.0,
                aspect_ratio=aspect_ratio,
                badge_text="CONFIDENTIAL EVIDENCE",
                zoom_direction="out",
            )
            scenes.append(scene3_path)


    # Scene 4: Map Locator & Satellite Telemetry (Cross-Studio Map Engine)
    coords = dossier.get("coordinates") or "28°43'N 77°12'E • CLASSIFIED"
    scene_map_path = OUTPUT_DIR / f"{slug}_scene_map.mp4"
    try:
        from map_engine import render_map_locator_clip
        print("\n[Step 4.5/5] Splicing Vox Tactical Satellite Map Locator Clip...")
        render_map_locator_clip(
            location_name=topic.upper(),
            coordinates=coords,
            output_path=scene_map_path,
            aspect_ratio=aspect_ratio,
            duration_sec=3.5,
        )
        scenes.append(scene_map_path)
    except Exception as e:
        print(f"[Notice] Map scene skipped: {e}")


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

    # Export CapCut / Premiere Pro Subtitles (.ass)
    try:
        capcut_ass = OUTPUT_DIR / f"{slug}_{format_type.upper()}_CAPCUT.ass"
        words_timed = [{"word": c.get("text", ""), "start": c.get("start", 0.0), "end": c.get("end", 0.0)} for c in cues]
        build_ass_subtitle_file(words_timed, capcut_ass, style_name=caption_style, video_width=1080 if aspect_ratio=="vertical" else 1920, video_height=1920 if aspect_ratio=="vertical" else 1080)
        print(f">> [CapCut / NLE] Ready-to-import subtitle track: {capcut_ass.name}")
    except Exception as e:
        print(f"[Notice] Subtitle export skipped: {e}")

    # Export Google-compliant Schema.org VideoObject JSON-LD
    try:
        dur_sec = cues[-1].get("end", 55.0) if cues else 55.0
        seo_schema = build_video_schema(
            title=f"{dossier.get('headline', topic)} | Dark Sutra",
            description=f"Official forensic investigation into {topic}. {dossier.get('dateline', '')}",
            duration_sec=dur_sec,
            thumbnail_urls=[],
            channel_name="Dark Sutra",
            channel_url="https://www.youtube.com/@DarkSutraOfficial",
            transcript=script_text,
            keywords=["Dark Sutra", "True Crime Hindi", "Forensic Dossier", topic]
        )
        schema_path = OUTPUT_DIR / f"{slug}_{format_type.upper()}_SEO_SCHEMA.json"
        export_schema_json_ld(seo_schema, schema_path)
        print(f">> [SEO Schema] Exported Google Rich Results Schema: {schema_path.name}")
    except Exception as e:
        print(f"[Notice] SEO Schema export skipped: {e}")

    # Optional 4K Cinema Enhancement
    final_output = master_path
    if quality == "4k":
        try:
            master_4k = OUTPUT_DIR / f"{slug}_{format_type.upper()}_4K_UHD.mp4"
            enhance_video_4k(master_path, master_4k, is_vertical=(aspect_ratio == "vertical"), fps=60)
            final_output = master_4k
        except Exception as e:
            print(f"[Notice] 4K enhancement fallback to 1080p: {e}")

    print("\n" + "=" * 65)
    print(f">> PRODUCTION COMPLETE!")
    print(f">> Master File Ready: {final_output}")
    print("=" * 65)
    return final_output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Channel 3: Dark Sutra — True Crime & Mystery Documentary Engine")
    parser.add_argument("--topic", default="Burari Deaths", help="Crime, mystery, or forensic topic")
    parser.add_argument("--format", default="short", choices=["short", "doc"], help="Target video format: short (9:16) or doc (16:9)")
    parser.add_argument("--quote", default=None, help="Key quote or evidence phrase to highlight")
    parser.add_argument("--lang", default="hindi", choices=["hindi", "hinglish"], help="Narration language")
    parser.add_argument("--voice", default="hindi_deep", help="Voice profile (hindi_deep, deep_narrator, dramatic_story)")
    parser.add_argument("--quality", default="4k", choices=["1080p", "4k"], help="Output resolution (4k UHD @ 60fps or 1080p)")
    parser.add_argument("--caption-style", default="dark_dossier", choices=["dark_dossier", "hormozi_pop", "vox_minimal"], help="Viral subtitle style")
    args = parser.parse_args()

    produce_documentary(
        topic=args.topic,
        format_type=args.format,
        key_quote=args.quote,
        language=args.lang,
        voice_key=args.voice,
        quality=args.quality,
        caption_style=args.caption_style,
    )

