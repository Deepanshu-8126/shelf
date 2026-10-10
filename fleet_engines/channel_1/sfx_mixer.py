"""
SFX Mixer - Layers subtle sound effects at exact word timestamps.
Non-intrusive audio mixing so voiceover remains 100% clear.
AUTO-GENERATES procedural SFX if files missing (no manual download needed).
"""
import os
from pathlib import Path
from typing import List, Dict, Optional
from moviepy import AudioFileClip, CompositeAudioClip, AudioClip
import numpy as np

SFX_DIR = Path(__file__).resolve().parent.parent / "assets" / "sfx"
SFX_DIR.mkdir(parents=True, exist_ok=True)

# SFX files with their volumes (0.0 to 1.0)
SFX_CONFIG = {
    "whoosh": {"file": "whoosh.mp3", "volume": 0.18},
    "cash": {"file": "cash.mp3", "volume": 0.20},
    "boom": {"file": "boom.mp3", "volume": 0.15},
    "click": {"file": "click.mp3", "volume": 0.18},
}

# Pre-load SFX clips for performance
_sfx_cache = {}


def get_sfx_clip(sfx_type: str) -> Optional[AudioFileClip]:
    """Get cached SFX clip or load it. Auto-generates procedural SFX if missing."""
    if sfx_type in _sfx_cache:
        return _sfx_cache[sfx_type]

    config = SFX_CONFIG.get(sfx_type)
    if not config:
        return None

    path = (SFX_DIR / config["file"]).resolve()
    if path.exists():
        try:
            clip = AudioFileClip(str(path))
            _sfx_cache[sfx_type] = clip
            return clip
        except Exception as e:
            print(f"WARNING: Failed to load SFX {sfx_type}: {e}", flush=True)

    # Auto-generate procedural SFX
    print(f"   AUTO-GENERATING procedural SFX: {sfx_type}")
    clip = generate_procedural_sfx(sfx_type, config["volume"])
    if clip:
        _sfx_cache[sfx_type] = clip
    return clip


def generate_procedural_sfx(sfx_type: str, volume: float) -> Optional[AudioClip]:
    """Generate synthetic SFX using numpy - no external files needed."""
    # Duration per SFX type
    durations = {
        "whoosh": 0.6,
        "cash": 0.4,
        "boom": 0.5,
        "click": 0.15,
    }
    duration = durations.get(sfx_type, 0.5)
    sample_rate = 44100
    t = np.linspace(0, duration, int(sample_rate * duration), dtype=np.float32)

    if sfx_type == "whoosh":
        # Rising/falling pitch noise - wind whoosh
        freq_start, freq_end = 200, 2000
        freq = freq_start + (freq_end - freq_start) * t / duration
        signal = np.sin(2 * np.pi * freq * t) * np.exp(-t * 3)  # Decay
        # Add filtered noise for airiness
        noise = np.random.normal(0, 0.3, len(t))
        # Simple high-pass filter effect
        signal = signal * 0.6 + noise * 0.4

    elif sfx_type == "cash":
        # Cha-ching: two quick metallic tones
        signal = np.sin(2 * np.pi * 800 * t) * np.exp(-t * 15)
        signal += 0.5 * np.sin(2 * np.pi * 1200 * t) * np.exp(-(t - 0.1) * 15) * (t > 0.1)
        signal += 0.3 * np.sin(2 * np.pi * 600 * t) * np.exp(-t * 10)

    elif sfx_type == "boom":
        # Low frequency impact with decay
        signal = np.sin(2 * np.pi * 60 * t) * np.exp(-t * 8)
        signal += 0.5 * np.sin(2 * np.pi * 120 * t) * np.exp(-t * 12)
        # Add noise burst for impact
        noise = np.random.normal(0, 0.4, len(t)) * np.exp(-t * 20)
        signal = signal * 0.7 + noise * 0.3

    elif sfx_type == "click":
        # Sharp click - very short transient
        signal = np.exp(-t * 100) * np.sin(2 * np.pi * 3000 * t)
        signal += 0.3 * np.random.normal(0, 0.2, len(t)) * np.exp(-t * 50)

    else:
        return None

    # Normalize and apply volume
    signal = signal / (np.max(np.abs(signal)) + 1e-6)
    signal = signal * volume

    # Convert to stereo
    stereo = np.column_stack([signal, signal])

    def make_frame(frame_t):
        idx = int(frame_t * sample_rate)
        if idx >= len(stereo):
            return np.zeros(2, dtype=np.float32)
        return stereo[idx]

    return AudioClip(make_frame, duration=duration, fps=sample_rate)


def create_sfx_at_timestamp(sfx_type: str, timestamp: float, video_duration: float) -> Optional[AudioClip]:
    """
    Create an SFX audio clip positioned at exact timestamp.
    Returns an AudioClip that can be composited.
    """
    config = SFX_CONFIG.get(sfx_type)
    if not config:
        return None

    sfx_clip = get_sfx_clip(sfx_type)
    if sfx_clip is None:
        return None

    # Set the clip to start at the exact timestamp
    sfx_clip = sfx_clip.with_start(timestamp)
    sfx_clip = sfx_clip.with_volume_scaled(config["volume"])

    return sfx_clip


def mix_sfx_with_voiceover(
    voiceover_clip: AudioFileClip,
    sfx_events: List[Dict],
    video_duration: float
) -> CompositeAudioClip:
    """
    Mix SFX events with the main voiceover audio.
    voiceover_clip: Main TTS audio clip
    sfx_events: List of {sfx_type, timestamp} dicts
    video_duration: Total video duration for clipping
    """
    audio_clips = [voiceover_clip]

    for event in sfx_events:
        sfx_type = event.get("sfx_type", "whoosh")
        timestamp = event.get("timestamp", 0)

        sfx_clip = create_sfx_at_timestamp(sfx_type, timestamp, video_duration)
        if sfx_clip:
            audio_clips.append(sfx_clip)

    # Composite all audio
    mixed = CompositeAudioClip(audio_clips)

    # Ensure duration matches video
    mixed = mixed.subclipped(0, video_duration)

    return mixed


def extract_sfx_events_from_popups(popups: List[Dict]) -> List[Dict]:
    """Extract SFX events from popup data."""
    events = []
    for popup in popups:
        events.append({
            "sfx_type": popup.get("sfx_type", "whoosh"),
            "timestamp": popup.get("timestamp", 0)
        })
    return events


def create_silent_audio(duration: float) -> AudioClip:
    """Create a silent audio clip of given duration."""
    def make_frame(t):
        return np.zeros((int(t * 44100), 2), dtype=np.float32)

    return AudioClip(make_frame, duration=duration, fps=44100)