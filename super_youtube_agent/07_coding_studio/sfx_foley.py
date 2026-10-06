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
import os
import sys
import wave
from pathlib import Path
import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

SAMPLE_RATE = 44100


SFX_DIR = Path(__file__).resolve().parent / "assets" / "sfx"


def get_real_click() -> np.ndarray:
    """Loads studio recording of Cherry MX Blue switch click if available, else synthetic fallback."""
    click_path = SFX_DIR / "keyboard_click.wav"
    if click_path.exists():
        try:
            with wave.open(str(click_path), 'rb') as wf:
                raw = wf.readframes(wf.getnframes())
                return (np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0) * 0.72
        except Exception:
            pass
    return create_mechanical_click()


def get_real_enter() -> np.ndarray:
    """Loads studio recording of Cherry MX heavy Enter key with stabilizer thud."""
    enter_path = SFX_DIR / "keyboard_enter.wav"
    if enter_path.exists():
        try:
            with wave.open(str(enter_path), 'rb') as wf:
                raw = wf.readframes(wf.getnframes())
                return (np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0) * 0.85
        except Exception:
            pass
    return create_enter_key()


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


def overlay_keystroke_sequence(
    master: np.ndarray,
    start_time: float,
    duration: float,
    volume: float = 0.36
):
    """Generates humanized Cherry MX mechanical keyboard typing sounds with tactile cadence."""
    rng = np.random.RandomState(42)
    t = start_time
    end_time = min(len(master) / SAMPLE_RATE, start_time + duration)
    click = get_real_click()
    enter = get_real_enter()

    while t < end_time:
        is_newline = rng.rand() < 0.14
        if is_newline:
            overlay_audio_stem(master, enter, t, volume=volume * 1.25)
            t += rng.uniform(0.11, 0.18)
        else:
            overlay_audio_stem(master, click, t, volume=volume * rng.uniform(0.85, 1.15))
            t += rng.uniform(0.048, 0.088)


def overlay_precise_keystrokes(
    master: np.ndarray,
    code_text: str,
    start_sec: float,
    duration_sec: float,
    volume: float = 0.38,
    ease_exponent: float = 1.6
):
    """
    Overlays exact keystrokes corresponding to each character typed in code_text
    over duration_sec, with Cherry MX Blue click per char and enter thud for newlines.
    """
    if not code_text or duration_sec <= 0:
        return
    click = get_real_click()
    enter = get_real_enter()
    chars = list(code_text)
    total_chars = len(chars)
    if total_chars == 0:
        return

    for idx, ch in enumerate(chars):
        progress = (idx / total_chars) ** (1.0 / ease_exponent)
        t = start_sec + progress * duration_sec
        if t * SAMPLE_RATE >= len(master):
            break
        if ch == '\n':
            overlay_audio_stem(master, enter, t, volume=volume * 1.25)
        elif ch in (' ', '\t'):
            overlay_audio_stem(master, click, t, volume=volume * 0.65)
        else:
            overlay_audio_stem(master, click, t, volume=volume)


def build_teacher_foley_soundtrack(
    voice_wav_path: Path, 
    output_wav_path: Path, 
    beats: list[float],
    lesson: Any = None,
    is_optimal_phase_func=None,
    get_active_code_func=None,
    get_full_code_raw_func=None,
    get_type_start_func=None,
    get_type_duration_func=None
) -> Path:
    """
    Reads teacher narration, mixes authentic Cherry MX mechanical switch Foley SFX at key pedagogical beats,
    and saves the synchronized master soundtrack.
    
    Optional typing synchronization parameters:
    - lesson: The lesson object containing code snippets
    - is_optimal_phase_func: Function(sec) -> bool indicating if we're in optimal phase
    - get_active_code_func: Function() -> list of (text, token_type) tuples for active code
    - get_full_code_raw_func: Function() -> str of complete code being typed
    - get_type_start_func: Function(sec) -> float when typing starts for current phase
    - get_type_duration_func: Function(sec) -> float how long typing takes for current phase
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
    marker = create_marker_sweep()
    whoosh = create_whoosh()
    ding = create_success_ding()

    # Use precise typing synchronization if lesson data is provided
    if lesson is not None and all([
        is_optimal_phase_func, 
        get_active_code_func, 
        get_full_code_raw_func, 
        get_type_start_func, 
        get_type_duration_func
    ]):
        # Generate precise keyboard clicks for both phases (naive and optimal)
        for phase_name, is_optimal in [("naive", False), ("optimal", True)]:
            # Determine when this phase is active based on lesson-specific timing
            # We need to sample time points to detect when each phase is active
            # For simplicity, we'll use the same timing logic as in the renderer
            
            # Get the code for this phase
            if hasattr(lesson, 'snippet_naive'):  # CodingLesson
                active_code = lesson.snippet_optimal if is_optimal else lesson.snippet_naive
            else:  # TeacherLesson
                active_code = lesson.code_after if is_optimal else lesson.code_before
                
            full_code_raw = "\n".join([line_tuple[0] for line_tuple in active_code[:6]])
            
            if not full_code_raw.strip():
                continue
                
            # For each phase, we need to determine when typing occurs
            # In the renderer, typing occurs during the first part of each phase
            # Let's approximate based on the beats and phase duration
            
            if is_optimal:
                # Optimal phase: typing from beats[1] to beats[1] + type_dur
                type_start = beats[1] if len(beats) > 1 else 2.0
                type_duration = 1.7  # From renderer
            else:
                # Naive phase: typing from 0.5 to 0.5 + type_dur  
                type_start = 0.5
                type_duration = 1.9  # From renderer
                
            # Only add typing sounds if this phase is actually in the video timeline
            phase_end_time = type_start + type_duration
            if type_start < len(master) / SAMPLE_RATE:
                actual_duration = min(type_duration, len(master) / SAMPLE_RATE - type_start)
                if actual_duration > 0:
                    overlay_precise_keystrokes(
                        master, 
                        full_code_raw, 
                        type_start, 
                        actual_duration,
                        volume=0.38,
                        ease_exponent=1.6
                    )
    else:
        # Fallback to original behavior if typing sync not available
        # Foley Cues (Synchronized frame-accurately with visual transitions):
        # 1. Early character-by-character typing keystrokes (0.5s to 2.4s)
        overlay_keystroke_sequence(master, start_time=0.5, duration=2.0, volume=0.38)

        # 2. Highlighter marker sweep on key line (around 2.6s - exactly when visual wipe begins)
        marker_time = 2.6
        if marker_time < len(master) / SAMPLE_RATE:
            overlay_audio_stem(master, marker, marker_time, volume=0.55)

        # 3. Enter key click when Terminal executes (around beats[0] + 0.4s)
        enter_thud = get_real_enter()
        term_enter_time = beats[0] + 0.4 if len(beats) > 0 else 7.0
        if term_enter_time < len(master) / SAMPLE_RATE:
            overlay_audio_stem(master, enter_thud, term_enter_time, volume=0.65)

        # 4. Terminal pass / benchmark ding (around beats[0] + 1.8s)
        term_ding_time = beats[0] + 1.8 if len(beats) > 0 else 8.5
        if term_ding_time < len(master) / SAMPLE_RATE:
            overlay_audio_stem(master, ding, term_ding_time, volume=0.50)

        # 5. Whoosh transition into Clean Code phase (around beats[1])
        if len(beats) > 1 and beats[1] < len(master) / SAMPLE_RATE:
            overlay_audio_stem(master, whoosh, beats[1] - 0.25, volume=0.50)
            # Fast typing clacks for the clean refactor
            overlay_keystroke_sequence(master, start_time=beats[1], duration=1.8, volume=0.38)

        # 6. Climax Whoosh + Ding into the VS Comparison Screen (around beats[2])
        climax_beat = beats[2] if len(beats) > 2 else len(master) / SAMPLE_RATE * 0.75
        if climax_beat < len(master) / SAMPLE_RATE:
            overlay_audio_stem(master, whoosh, climax_beat - 0.25, volume=0.60)
            overlay_audio_stem(master, ding, climax_beat + 0.45, volume=0.65)

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
