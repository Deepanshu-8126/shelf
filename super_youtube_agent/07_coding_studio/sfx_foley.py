"""
Procedural SFX & Foley Audio Synthesizer for Coding Studio.
Generates 100% copyright-free, procedural sound design:
- Mechanical keyboard clacks & typing bursts
- Enter key heavy press / spacebar thud
- Highlighter marker friction sweep
- Camera zoom whoosh / transition swell
- Success chime / benchmark ding
"""
from __future__ import annotations
import math
import wave
from pathlib import Path
import numpy as np

SAMPLE_RATE = 44100


def create_mechanical_click(duration_sec: float = 0.025) -> np.ndarray:
    """Crisp mechanical switch click (Cherry MX Blue/Brown tactile click)."""
    n = int(duration_sec * SAMPLE_RATE)
    t = np.linspace(0, duration_sec, n, endpoint=False)
    
    # Fast attack, exponential decay
    decay = np.exp(-t * 280)
    # Click resonance at 2800Hz + 4200Hz
    click = (np.sin(2 * np.pi * 2800 * t) * 0.6 + np.sin(2 * np.pi * 4200 * t) * 0.4) * decay
    # Add subtle snap transient
    noise = np.random.uniform(-0.3, 0.3, n) * np.exp(-t * 600)
    out = (click + noise) * 0.45
    return out.astype(np.float32)


def create_enter_key(duration_sec: float = 0.08) -> np.ndarray:
    """Heavy mechanical Enter key thud with stabilizer bar click."""
    n = int(duration_sec * SAMPLE_RATE)
    t = np.linspace(0, duration_sec, n, endpoint=False)
    
    # Bottom-out thud around 320Hz
    thud = np.sin(2 * np.pi * 320 * t) * np.exp(-t * 80) * 0.7
    # Metallic stabilizer ring
    ring = np.sin(2 * np.pi * 2400 * t) * np.exp(-t * 220) * 0.35
    # Initial snap
    snap = np.random.uniform(-0.5, 0.5, n) * np.exp(-t * 800) * 0.4
    
    out = (thud + ring + snap) * 0.55
    return out.astype(np.float32)


def create_marker_sweep(duration_sec: float = 0.65) -> np.ndarray:
    """Felt-tip highlighter marker friction sweep on clean paper."""
    n = int(duration_sec * SAMPLE_RATE)
    t = np.linspace(0, duration_sec, n, endpoint=False)
    
    # Smooth attack and decay envelope
    env = np.sin(np.pi * np.linspace(0, 1, n)) ** 0.8
    # High-mid friction noise
    noise = np.random.uniform(-1, 1, n)
    # Felt vibration resonance around 1250Hz with micro flutter
    flutter = np.sin(2 * np.pi * 1250 * t + 0.15 * np.sin(2 * np.pi * 24 * t)) * 0.3
    
    # Simple smoothing
    raw = (noise * 0.7 + flutter) * env * 0.35
    kernel = np.array([0.1, 0.25, 0.3, 0.25, 0.1])
    smoothed = np.convolve(raw, kernel, mode='same')
    return smoothed.astype(np.float32)


def create_whoosh(duration_sec: float = 0.42) -> np.ndarray:
    """Airy transition swoosh / camera zoom whoosh."""
    n = int(duration_sec * SAMPLE_RATE)
    t = np.linspace(0, duration_sec, n, endpoint=False)
    
    # Bell-shaped swell envelope
    env = np.sin(np.pi * np.linspace(0, 1, n)) ** 2.2
    # Pink-ish noise
    noise = np.random.normal(0, 0.5, n)
    # Low frequency sweep: 180Hz rising to 550Hz then falling
    pitch = 220 + 380 * env
    phase = 2 * np.pi * np.cumsum(pitch) / SAMPLE_RATE
    swoosh = (np.sin(phase) * 0.3 + noise * 0.7) * env * 0.4
    
    kernel = np.ones(12) / 12
    smoothed = np.convolve(swoosh, kernel, mode='same')
    return smoothed.astype(np.float32)


def create_success_ding(duration_sec: float = 0.7) -> np.ndarray:
    """Clean UI success chime / benchmark pass ding."""
    n = int(duration_sec * SAMPLE_RATE)
    t = np.linspace(0, duration_sec, n, endpoint=False)
    
    # Harmonic frequencies: C6 (1046.5Hz) and E6 (1318.5Hz)
    decay = np.exp(-t * 7.5)
    ding = (
        np.sin(2 * np.pi * 1046.5 * t) * 0.6 +
        np.sin(2 * np.pi * 1568.0 * t) * 0.3 +
        np.sin(2 * np.pi * 2093.0 * t) * 0.1
    ) * decay * 0.35
    return ding.astype(np.float32)


def overlay_audio_stem(master: np.ndarray, stem: np.ndarray, start_sec: float, volume: float = 1.0):
    """Overlays a stem onto the master audio track at specified second offset."""
    start_sample = int(start_sec * SAMPLE_RATE)
    end_sample = min(len(master), start_sample + len(stem))
    stem_len = end_sample - start_sample
    if stem_len > 0:
        master[start_sample:end_sample] += stem[:stem_len] * volume


def build_teacher_foley_soundtrack(voice_wav_path: Path, output_wav_path: Path, beats: list[float]) -> Path:
    """
    Reads Edge TTS narration, mixes diegetic coding Foley SFX at key pedagogical beats,
    and saves the synchronized master soundtrack.
    """
    # 1. Load voice wav
    with wave.open(str(voice_wav_path), 'rb') as vf:
        n_channels = vf.getnchannels()
        sampwidth = vf.getsampwidth()
        framerate = vf.getframerate()
        n_frames = vf.getnframes()
        raw_bytes = vf.readframes(n_frames)

    # Convert to float numpy array
    if sampwidth == 2:
        voice_data = np.frombuffer(raw_bytes, dtype=np.int16).astype(np.float32) / 32768.0
    else:
        voice_data = np.frombuffer(raw_bytes, dtype=np.uint8).astype(np.float32) / 128.0 - 1.0

    # If framerate differs, resample simple linear
    if framerate != SAMPLE_RATE:
        new_len = int(len(voice_data) * (SAMPLE_RATE / framerate))
        voice_data = np.interp(np.linspace(0, len(voice_data), new_len), np.arange(len(voice_data)), voice_data)

    master = np.copy(voice_data)

    # Prepare SFX stems
    click = create_mechanical_click()
    enter = create_enter_key()
    marker = create_marker_sweep()
    whoosh = create_whoosh()
    ding = create_success_ding()

    # Foley Cues:
    # 1. Early typing clicks (0.5s to 2.2s)
    typing_times = [0.6, 0.75, 0.9, 1.1, 1.25, 1.45, 1.7, 1.9, 2.15]
    for tt in typing_times:
        if tt < len(master) / SAMPLE_RATE:
            overlay_audio_stem(master, click, tt, volume=0.35)

    # 2. Highlighter marker sweep on Line 3 (around 3.0s)
    marker_time = 3.0
    if marker_time < len(master) / SAMPLE_RATE:
        overlay_audio_stem(master, marker, marker_time, volume=0.55)

    # 3. Enter key click when Terminal executes (around beats[0] + 0.4s)
    term_enter_time = beats[0] + 0.4 if len(beats) > 0 else 7.0
    if term_enter_time < len(master) / SAMPLE_RATE:
        overlay_audio_stem(master, enter, term_enter_time, volume=0.65)

    # 4. Terminal pass / benchmark ding (around beats[0] + 1.8s)
    term_ding_time = beats[0] + 1.8 if len(beats) > 0 else 8.5
    if term_ding_time < len(master) / SAMPLE_RATE:
        overlay_audio_stem(master, ding, term_ding_time, volume=0.50)

    # 5. Whoosh transition into Generator phase (around beats[1])
    if len(beats) > 1 and beats[1] < len(master) / SAMPLE_RATE:
        overlay_audio_stem(master, whoosh, beats[1] - 0.2, volume=0.45)
        gen_typing = [beats[1] + 0.3, beats[1] + 0.45, beats[1] + 0.6, beats[1] + 0.75]
        for gt in gen_typing:
            if gt < len(master) / SAMPLE_RATE:
                overlay_audio_stem(master, click, gt, volume=0.35)

    # 6. Climax Whoosh + Ding into the VS Comparison Screen (around beats[2])
    if len(beats) > 2 and beats[2] < len(master) / SAMPLE_RATE:
        overlay_audio_stem(master, whoosh, beats[2] - 0.3, volume=0.60)
        overlay_audio_stem(master, ding, beats[2] + 0.5, volume=0.65)

    # Normalize to prevent clipping
    peak = np.max(np.abs(master))
    if peak > 0.98:
        master = master * (0.95 / peak)

    # Save to 16-bit PCM WAV
    int16_data = (master * 32767).astype(np.int16)
    with wave.open(str(output_wav_path), 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(int16_data.tobytes())

    print(f"🎵 Foley & SFX Mixed Soundtrack created: {output_wav_path}")
    return output_wav_path
