"""
Generates production-grade procedural cinematic SFX files for Fleet Engines (Channel 1, 2, and 3).
Zero external dependencies required besides numpy and soundfile/scipy.
"""
import os
import math
import numpy as np
import soundfile as sf
from pathlib import Path

SFX_DIR = Path(__file__).resolve().parent / "sfx"
SFX_DIR.mkdir(parents=True, exist_ok=True)
SAMPLE_RATE = 44100

def make_whoosh(filename="whoosh.mp3", duration=0.65, volume=0.75):
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), dtype=np.float32)
    # Pitch rises from 250Hz to 1600Hz and falls back to 350Hz
    mid = duration / 2.0
    freq = 250 + 1350 * np.exp(-((t - mid) ** 2) / 0.04)
    phase = 2 * np.pi * np.cumsum(freq) / SAMPLE_RATE
    carrier = np.sin(phase)
    # Add filtered noise
    noise = np.random.normal(0, 0.5, len(t)).astype(np.float32)
    env = np.sin(np.pi * (t / duration)) ** 2
    signal = (carrier * 0.5 + noise * 0.5) * env * volume
    out_p = SFX_DIR / filename
    sf.write(str(out_p), signal, SAMPLE_RATE)
    print(f"Generated {out_p.name} ({out_p.stat().st_size} bytes)")

def make_impact_boom(filename="boom.mp3", duration=1.2, volume=0.85):
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), dtype=np.float32)
    # Deep sub-bass drop from 90Hz to 35Hz
    freq = 90 * np.exp(-t * 2.8) + 35
    phase = 2 * np.pi * np.cumsum(freq) / SAMPLE_RATE
    sub = np.sin(phase) * np.exp(-t * 3.5)
    # Transient punch
    punch = np.sin(2 * np.pi * 140 * t) * np.exp(-t * 22)
    # Low frequency rumble noise
    noise = np.random.normal(0, 0.4, len(t)).astype(np.float32) * np.exp(-t * 8.0)
    signal = (sub * 0.65 + punch * 0.35 + noise * 0.2) * volume
    # Normalize
    signal = signal / (np.max(np.abs(signal)) + 1e-6) * volume
    out_p = SFX_DIR / filename
    sf.write(str(out_p), signal, SAMPLE_RATE)
    print(f"Generated {out_p.name} ({out_p.stat().st_size} bytes)")

def make_paper_rustle(filename="paper.mp3", duration=0.7, volume=0.7):
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), dtype=np.float32)
    noise = np.random.normal(0, 0.4, len(t)).astype(np.float32)
    # Modulation envelopes for flutter
    flutter = (np.sin(2 * np.pi * 18 * t) + 1.2) * (np.sin(2 * np.pi * 6 * t) + 1.0)
    env = np.sin(np.pi * (t / duration)) ** 1.5
    signal = noise * flutter * env * volume
    signal = signal / (np.max(np.abs(signal)) + 1e-6) * volume
    out_p = SFX_DIR / filename
    sf.write(str(out_p), signal, SAMPLE_RATE)
    print(f"Generated {out_p.name} ({out_p.stat().st_size} bytes)")

def make_cash(filename="cash.mp3", duration=0.55, volume=0.75):
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), dtype=np.float32)
    tone1 = np.sin(2 * np.pi * 987.77 * t) * np.exp(-t * 12)  # B5
    tone2 = np.sin(2 * np.pi * 1318.51 * t) * np.exp(-(t - 0.08) * 14) * (t > 0.08)  # E6
    tone3 = np.sin(2 * np.pi * 1975.53 * t) * np.exp(-(t - 0.15) * 16) * (t > 0.15)  # B6
    signal = (tone1 * 0.4 + tone2 * 0.4 + tone3 * 0.3) * volume
    out_p = SFX_DIR / filename
    sf.write(str(out_p), signal, SAMPLE_RATE)
    print(f"Generated {out_p.name} ({out_p.stat().st_size} bytes)")

def make_click(filename="click.mp3", duration=0.18, volume=0.8):
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), dtype=np.float32)
    tick = np.sin(2 * np.pi * 3200 * t) * np.exp(-t * 70)
    noise = np.random.normal(0, 0.3, len(t)).astype(np.float32) * np.exp(-t * 90)
    signal = (tick * 0.6 + noise * 0.4) * volume
    out_p = SFX_DIR / filename
    sf.write(str(out_p), signal, SAMPLE_RATE)
    print(f"Generated {out_p.name} ({out_p.stat().st_size} bytes)")

if __name__ == "__main__":
    print(f"Creating SFX in: {SFX_DIR}")
    make_whoosh("whoosh.mp3")
    make_impact_boom("boom.mp3")
    make_paper_rustle("paper.mp3")
    make_cash("cash.mp3")
    make_click("click.mp3")
    # Also save as .wav aliases for ffmpeg zero-transcode mixing
    make_whoosh("whoosh.wav")
    make_impact_boom("boom.wav")
    make_paper_rustle("paper.wav")
    print("All SFX assets generated successfully!")
