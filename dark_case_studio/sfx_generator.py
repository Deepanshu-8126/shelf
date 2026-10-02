"""
Sound Design & SFX Generator for Dark Case Documentaries.
Synthesizes procedural cinematic audio using NumPy & Wave:
- Sub-bass tension drone (ambient suspense layer)
- Marker / highlighter friction scratch SFX
- Deep cinematic sub-boom / impact transition
- Vintage camera shutter click
"""
from __future__ import annotations

import math
import struct
import wave
from pathlib import Path
import numpy as np


def generate_tension_drone(output_path: Path, duration_sec: float = 60.0, sample_rate: int = 44100) -> Path:
    """Generates an ominous deep sub-bass ambient tension drone."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    num_samples = int(duration_sec * sample_rate)
    t = np.linspace(0, duration_sec, num_samples, endpoint=False)
    
    # Fundamental low frequencies: 48Hz, 55Hz, 65Hz with slow amplitude modulation
    lfo1 = 0.5 + 0.5 * np.sin(2 * np.pi * 0.15 * t)  # Slow 0.15Hz swell
    lfo2 = 0.5 + 0.5 * np.sin(2 * np.pi * 0.08 * t + 1.0)
    
    wave_data = (
        0.55 * np.sin(2 * np.pi * 50.0 * t) * lfo1 +
        0.30 * np.sin(2 * np.pi * 55.0 * t) * lfo2 +
        0.20 * np.sin(2 * np.pi * 100.0 * t) * (0.8 + 0.2 * lfo1) +
        0.08 * np.sin(2 * np.pi * 150.0 * t)
    )
    
    # Add subtle lowpass filtered white noise for room air / suspense rumble
    noise = np.random.normal(0, 0.03, num_samples)
    # Simple moving average filter for noise
    window_size = 50
    smooth_noise = np.convolve(noise, np.ones(window_size) / window_size, mode='same')
    
    drone = wave_data + smooth_noise
    # Normalize and scale to 16-bit PCM
    drone = drone / (np.max(np.abs(drone)) + 1e-6) * 0.75
    int_samples = (drone * 32767).astype(np.int16)
    
    with wave.open(str(output_path), 'wb') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)   # 16-bit
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(int_samples.tobytes())
        
    print(f">> Tension drone created: {output_path} ({duration_sec}s)")
    return output_path


def generate_marker_scratch(output_path: Path, duration_sec: float = 1.8, sample_rate: int = 44100) -> Path:
    """Generates an authentic highlighter marker felt-tip squeak / friction sound."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    num_samples = int(duration_sec * sample_rate)
    t = np.linspace(0, duration_sec, num_samples, endpoint=False)
    
    # High-mid friction frequencies (800Hz - 2400Hz) with rapid jitter
    noise = np.random.uniform(-1, 1, num_samples)
    
    # Envelope: gentle ramp-up, sustained friction, smooth ramp-down
    fade_len = int(0.1 * sample_rate)
    envelope = np.ones(num_samples)
    envelope[:fade_len] = np.linspace(0, 1, fade_len)
    envelope[-fade_len:] = np.linspace(1, 0, fade_len)
    
    # Subtle resonance frequency around 1400Hz (felt tip vibrating on paper)
    squeak = np.sin(2 * np.pi * 1350 * t + 0.1 * np.sin(2 * np.pi * 18 * t)) * 0.35
    
    scratch = (noise * 0.65 + squeak) * envelope
    # Simple band-limited smoothing
    kernel = np.array([0.1, 0.2, 0.4, 0.2, 0.1])
    scratch_filtered = np.convolve(scratch, kernel, mode='same')
    
    scratch_filtered = scratch_filtered / (np.max(np.abs(scratch_filtered)) + 1e-6) * 0.65
    int_samples = (scratch_filtered * 32767).astype(np.int16)
    
    with wave.open(str(output_path), 'wb') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(int_samples.tobytes())
        
    print(f">> Marker scratch SFX created: {output_path}")
    return output_path


def generate_cinematic_boom(output_path: Path, duration_sec: float = 2.5, sample_rate: int = 44100) -> Path:
    """Generates a deep sub-bass cinematic impact/boom for scene transitions."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    num_samples = int(duration_sec * sample_rate)
    t = np.linspace(0, duration_sec, num_samples, endpoint=False)
    
    # Pitch drop from 120Hz down to 35Hz
    freq = 35 + 85 * np.exp(-4.5 * t)
    phase = 2 * np.pi * np.cumsum(freq) / sample_rate
    
    # Exponential decay envelope
    envelope = np.exp(-2.2 * t)
    
    # Impact transient (initial attack thump)
    transient = np.exp(-35 * t) * np.random.uniform(-0.5, 0.5, num_samples)
    
    boom = (np.sin(phase) + 0.3 * np.sin(2 * phase) + transient) * envelope
    boom = boom / (np.max(np.abs(boom)) + 1e-6) * 0.85
    int_samples = (boom * 32767).astype(np.int16)
    
    with wave.open(str(output_path), 'wb') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(int_samples.tobytes())
        
    print(f">> Cinematic boom SFX created: {output_path}")
    return output_path


if __name__ == "__main__":
    assets_dir = Path("d:/facts_yt/dark_case_studio/assets/sfx")
    assets_dir.mkdir(parents=True, exist_ok=True)
    generate_tension_drone(assets_dir / "drone_suspense.wav", duration_sec=30.0)
    generate_marker_scratch(assets_dir / "marker_sweep.wav", duration_sec=2.0)
    generate_cinematic_boom(assets_dir / "transition_boom.wav", duration_sec=2.5)
