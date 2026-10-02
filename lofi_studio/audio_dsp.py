"""LoFi Audio DSP Engine: High-grade Slowed + Reverb + Vintage LoFi + Ambient Mixer.

Transforms standard tracks into copyright-immune, ultra-soothing LoFi audio.
"""
from __future__ import annotations

import asyncio
import os
import subprocess
from pathlib import Path


def generate_ambient_track(duration: float, output_path: Path) -> Path:
    """Generates synthetic gentle rain + vinyl noise using ffmpeg audio noise generators."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Generate rain simulation using bandpassed pink noise + soft vinyl crackle
    filtergraph = (
        f"anoisesrc=d={duration:.2f}:c=pink:r=44100:a=0.035,lowpass=f=2400,highpass=f=200[rain];"
        f"anoisesrc=d={duration:.2f}:c=brown:r=44100:a=0.015,bandpass=f=1200:w=800[vinyl];"
        f"[rain][vinyl]amix=inputs=2:duration=first[ambient]"
    )
    cmd = [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-filter_complex", filtergraph,
        "-map", "[ambient]",
        "-c:a", "aac", "-b:a", "192k",
        str(output_path)
    ]
    subprocess.run(cmd, check=True)
    return output_path


def apply_lofi_dsp(
    input_audio: Path,
    output_audio: Path,
    speed: float = 0.86,
    pitch_factor: float = 0.88,
    lowpass_freq: int = 3600,
    bass_boost_db: int = 5,
    reverb_mix: float = 0.35,
    add_ambience: bool = True
) -> Path:
    """Processes audio through an advanced multi-stage LoFi DSP filter chain.
    
    1. Slowed + Pitch Shift (Changes acoustic signature)
    2. Lo-Fi Warm Vintage Curve (Lowpass filter + Sub-bass presence)
    3. Multi-tap stereo reverb (Expands acoustic field)
    4. Layered gentle rain & vinyl crackle (Alters acoustic waveform to prevent Content-ID match)
    """
    input_audio = Path(input_audio)
    output_audio = Path(output_audio)
    output_audio.parent.mkdir(parents=True, exist_ok=True)
    
    # Calculate sample rate shift for pitch modulation
    orig_sr = 44100
    shifted_sr = int(orig_sr * pitch_factor)
    tempo_adj = speed / pitch_factor

    # Master LoFi Filtergraph
    # aecho: in_gain:out_gain:delays:decays
    dsp_graph = (
        f"[0:a]asetrate={shifted_sr},aresample={orig_sr},"
        f"atempo={tempo_adj:.4f},"
        f"lowpass=f={lowpass_freq},"
        f"bass=g={bass_boost_db}:f=90,"
        f"aecho=0.85:0.75:50|75:0.35|0.25,"
        f"aformat=channel_layouts=stereo[processed];"
    )
    
    if add_ambience:
        dsp_graph += (
            f"anoisesrc=c=pink:r=44100:a=0.03,lowpass=f=2200,highpass=f=250[rain];"
            f"anoisesrc=c=brown:r=44100:a=0.012,bandpass=f=1100:w=700[vinyl];"
            f"[rain][vinyl]amix=inputs=2:duration=first[amb];"
            f"[processed][amb]amix=inputs=2:duration=first:weights=1.0 0.08:dropout_transition=2[aout]"
        )
    else:
        dsp_graph += "[processed]aformat=channel_layouts=stereo[aout]"

    cmd = [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-i", str(input_audio),
        "-filter_complex", dsp_graph,
        "-map", "[aout]",
        "-c:a", "aac", "-b:a", "256k",
        str(output_audio)
    ]
    
    subprocess.run(cmd, check=True)
    return output_audio
