"""
Full Vox-Style AI Production Pipeline Orchestrator.
Orchestrates:
1. ElevenLabs Hollywood Narration (Adam Voice + Studio Mastering)
2. HyperFrames 2.5D Motion Graphics Rendering (Chromium GPU 60fps)
3. Procedural Diegetic Foley & SFX (Marker scratch, stamp slam, drone)
4. Master Audio-Visual Compositing with Sidechain Ducking
"""
import json
import os
import subprocess
import time
from pathlib import Path
from dark_case_studio.voice_engine import generate_voiceover
from dark_case_studio.sfx_generator import (
    generate_tension_drone,
    generate_marker_scratch,
    generate_cinematic_boom,
)

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"
TEMPLATE_DIR = BASE_DIR / "hf_templates" / "vox_master"


import sys

# Ensure UTF-8 output on Windows terminal
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def build_vox_production():
    print("=" * 70)
    print(">> STARTING VOX-STYLE AI PRODUCTION PIPELINE")
    print("=" * 70)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # -------------------------------------------------------------
    # STEP 1: ELEVENLABS ADAM NARRATION
    # -------------------------------------------------------------
    print("\n[Step 1/4] Synthesizing ElevenLabs Adam Voiceover...")
    script_text = (
        "Deep inside the Sahara desert, satellite recon detected something impossible. "
        "Declassified documents confirm the circular structure matches Plato's original dimensions of Atlantis. "
        "Spanning forty kilometers with three concentric rings. "
        "Was Atlantis never in the ocean, but buried beneath the sand?"
    )
    
    raw_voice = OUTPUT_DIR / "vox_voice_adam_raw.mp3"
    mastered_voice = OUTPUT_DIR / "vox_voice_adam_mastered.mp3"
    
    res_path, cues = generate_voiceover(
        script_text=script_text,
        output_audio=raw_voice,
        provider="elevenlabs",
        voice_name="adam"
    )
    print(f">> Voiceover generated: {res_path} ({res_path.stat().st_size} bytes)")

    # Master voice with broadcast EQ and compand
    eq_cmd = [
        "ffmpeg", "-y", "-i", str(raw_voice),
        "-af", "highpass=f=80,equalizer=f=3500:width_type=q:width=1.5:g=3.5,compand=attacks=0.02:decays=0.15:points=-60/-60|-24/-12|0/-2:gain=2",
        "-b:a", "192k", str(mastered_voice)
    ]
    subprocess.run(eq_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f">> Voice mastered with broadcast vocal chain: {mastered_voice.name}")

    # -------------------------------------------------------------
    # STEP 2: GENERATE DIEGETIC FOLEY SFX & TENSION DRONE
    # -------------------------------------------------------------
    print("\n[Step 2/4] Generating Procedural Sound Design & Foley...")
    drone_wav = OUTPUT_DIR / "vox_drone.wav"
    marker_wav = OUTPUT_DIR / "vox_marker.wav"
    slam_wav = OUTPUT_DIR / "vox_slam.wav"

    generate_tension_drone(drone_wav, duration_sec=16.0)
    generate_marker_scratch(marker_wav, duration_sec=1.4)
    generate_cinematic_boom(slam_wav, duration_sec=2.0)

    # -------------------------------------------------------------
    # STEP 3: HYPERFRAMES GPU MOTION GRAPHICS RENDER
    # -------------------------------------------------------------
    print("\n[Step 3/4] >> Rendering HyperFrames 2.5D Motion Graphics (1080x1920 60fps)...")
    raw_video = OUTPUT_DIR / "vox_master_visuals.mp4"
    
    render_cmd = f"npx -y hyperframes render {TEMPLATE_DIR} -o {raw_video}"
    t0 = time.time()
    res = subprocess.run(render_cmd, shell=True, capture_output=True, text=True)
    render_time = time.time() - t0
    
    if res.returncode != 0:
        print(f"[ERROR] HyperFrames Render failed:\n{res.stderr}")
        raise RuntimeError("HyperFrames render failed")
    print(f">> HyperFrames GPU render completed in {render_time:.1f}s -> {raw_video.name}")

    # -------------------------------------------------------------
    # STEP 4: MASTER AUDIO-VISUAL COMPOSITING (FFMPEG)
    # -------------------------------------------------------------
    print("\n[Step 4/4] >> Master Compositing Audio Multi-Tracks onto Video...")
    final_output = OUTPUT_DIR / "VOX_STYLE_ATLANTIS_MASTER.mp4"

    # Multi-input filter graph:
    # 0: Video (15s)
    # 1: Mastered Voice (starts at 0.2s)
    # 2: Ambient Drone (volume 0.16)
    # 3: Stamp Slam SFX (delayed to 0.6s, volume 0.65)
    # 4: Marker Scratch SFX (delayed to 4.8s, volume 0.75)
    
    filter_complex = (
        "[1:a]adelay=200|200,volume=1.0[voice];"
        "[2:a]volume=0.16[drone];"
        "[3:a]adelay=600|600,volume=0.65[slam];"
        "[4:a]adelay=4800|4800,volume=0.75[marker];"
        "[voice][drone][slam][marker]amix=inputs=4:duration=first:dropout_transition=2[aout]"
    )

    composite_cmd = [
        "ffmpeg", "-y",
        "-i", str(raw_video),
        "-i", str(mastered_voice),
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
        str(final_output)
    ]
    
    subprocess.run(composite_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"\n>> SUCCESS! Broadcast-Ready Vox Short Rendered:")
    print(f">> Output Path: {final_output}")
    print(f">> File Size: {final_output.stat().st_size / (1024*1024):.2f} MB")
    return final_output


if __name__ == "__main__":
    build_vox_production()
