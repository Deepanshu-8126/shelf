"""
Anchored Timeline Scheduler for Channel 7.
Synchronizes code typing speed, per-line Kokoro audio,
spotlight pauses, and Cherry MX Foley cues with zero drift.
"""
from __future__ import annotations
from dataclasses import dataclass
import math
import subprocess
import wave
from pathlib import Path
from typing import List, Tuple, Dict, Any
import numpy as np
import soundfile as sf

from videosynx_schema import AnchoredLesson, AnchoredLine
from kokoro_tts import generate_kokoro_narration
from sfx_foley import get_real_click, get_real_enter, create_success_ding, create_whoosh, SAMPLE_RATE, overlay_audio_stem


@dataclass
class LineTimeSchedule:
    line_idx: int
    code_text: str
    narration_text: str
    type_start_sec: float
    type_end_sec: float
    explain_start_sec: float
    explain_end_sec: float
    highlight: bool
    state_label: str
    tip: str


class AnchoredTimeline:
    def __init__(self, lesson: AnchoredLesson, output_dir: Path):
        self.lesson = lesson
        self.output_dir = output_dir
        self.schedules: List[LineTimeSchedule] = []
        self.total_duration: float = 0.0
        self.intro_duration: float = 0.0
        self.outro_duration: float = 0.0
        self.exec_start_sec: float = 0.0
        self.exec_end_sec: float = 0.0

    def build_timeline_and_audio(self, lang: str = "hi", voice: str = "hm_omega") -> Tuple[Path, Path]:
        """
        Synthesizes Kokoro audio for intro, each line, sandbox execution, and outro.
        Constructs master voice WAV and master mixed SFX soundtrack WAV.
        """
        self.output_dir.mkdir(parents=True, exist_ok=True)
        audios: List[np.ndarray] = []
        current_time = 0.0

        # 1. Intro Hook
        intro_wav = self.output_dir / f"{self.lesson.id}_intro.wav"
        if self.lesson.intro_narration.strip():
            _, self.intro_duration = generate_kokoro_narration(
                self.lesson.intro_narration, intro_wav, lang=lang, voice=voice, speed=0.96
            )
            data, _ = sf.read(str(intro_wav))
            audios.append(data)
            current_time += self.intro_duration
        else:
            self.intro_duration = 0.5
            current_time += 0.5
            audios.append(np.zeros(int(0.5 * 24000), dtype=np.float32))

        # 2. Per-Line Anchored Timing
        for idx, line in enumerate(self.lesson.lines):
            # Typing phase (char by char)
            # ~20-25 chars per second for natural code typing
            code_len = max(len(line.code.strip()), 8)
            type_duration = max(0.45, code_len * 0.024)
            type_start = current_time
            type_end = type_start + type_duration
            
            # Line explanation phase (Kokoro audio)
            explain_start = type_end
            line_wav = self.output_dir / f"{self.lesson.id}_line_{idx}.wav"
            _, explain_duration = generate_kokoro_narration(
                line.narration, line_wav, lang=lang, voice=voice, speed=0.96
            )
            explain_end = explain_start + explain_duration
            data, _ = sf.read(str(line_wav))
            
            # Add silence padding for typing phase in the voice track
            silence_samples = int(type_duration * 24000)
            if silence_samples > 0:
                audios.append(np.zeros(silence_samples, dtype=np.float32))
            audios.append(data)

            self.schedules.append(LineTimeSchedule(
                line_idx=idx,
                code_text=line.code,
                narration_text=line.narration,
                type_start_sec=type_start,
                type_end_sec=type_end,
                explain_start_sec=explain_start,
                explain_end_sec=explain_end,
                highlight=line.highlight,
                state_label=line.state_label,
                tip=line.tip
            ))
            current_time = explain_end

        # 3. Sandbox Execution Phase
        self.exec_start_sec = current_time
        exec_pause_duration = 2.8  # Time for terminal dry run & test passing animation
        audios.append(np.zeros(int(exec_pause_duration * 24000), dtype=np.float32))
        current_time += exec_pause_duration
        self.exec_end_sec = current_time

        # 4. Outro Takeaway
        outro_wav = self.output_dir / f"{self.lesson.id}_outro.wav"
        if self.lesson.outro_narration.strip():
            _, self.outro_duration = generate_kokoro_narration(
                self.lesson.outro_narration, outro_wav, lang=lang, voice=voice, speed=0.96
            )
            data, _ = sf.read(str(outro_wav))
            audios.append(data)
            current_time += self.outro_duration
        else:
            self.outro_duration = 1.0
            current_time += 1.0

        self.total_duration = current_time

        # Save concatenated 24kHz raw voice
        full_audio_24k = np.concatenate(audios)
        raw_voice_path = self.output_dir / f"{self.lesson.id}_voice_24k.wav"
        sf.write(str(raw_voice_path), full_audio_24k, 24000)

        # Resample to 44.1kHz stereo
        master_voice_44k = self.output_dir / f"{self.lesson.id}_voice_44k.wav"
        subprocess.run([
            "ffmpeg", "-y", "-i", str(raw_voice_path),
            "-ar", "44100", "-ac", "1", str(master_voice_44k)
        ], check=True, capture_output=True)

        # 5. Synthesize Foley SFX & Keyboard Clicks
        master_soundtrack = self.mix_foley(master_voice_44k)
        return master_voice_44k, master_soundtrack

    def mix_foley(self, voice_path: Path) -> Path:
        """Overlays Cherry MX Blue clicks, Enter thuds, whooshes, and chimes."""
        with wave.open(str(voice_path), "rb") as vf:
            n_frames = vf.getnframes()
            raw_bytes = vf.readframes(n_frames)
            voice_data = np.frombuffer(raw_bytes, dtype=np.int16).astype(np.float32) / 32768.0

        master = np.copy(voice_data)
        click_stem = get_real_click()
        enter_stem = get_real_enter()
        ding_stem = create_success_ding()
        whoosh_stem = create_whoosh()

        # Humanized Cherry MX mechanical keystroke clicks for each line
        rng = np.random.RandomState(42)
        for sched in self.schedules:
            chars = list(sched.code_text)
            total_chars = len(chars)
            dur = sched.type_end_sec - sched.type_start_sec
            
            # Step in organic human typing cadence (~10-14 keys/sec max, not harsh machine-gun)
            step = max(1, total_chars // 14) if total_chars > 14 else 1
            for c_i in range(0, total_chars, step):
                ch = chars[c_i]
                jitter = float(rng.uniform(-0.012, 0.012))
                t = max(0.0, sched.type_start_sec + (c_i / max(1, total_chars)) * dur + jitter)
                if ch in (' ', '\t'):
                    overlay_audio_stem(master, click_stem, t, volume=0.12)
                else:
                    vol = float(rng.uniform(0.13, 0.17))
                    overlay_audio_stem(master, click_stem, t, volume=vol)

            # Crisp Enter key clack at the end of every line (subtle thud)
            overlay_audio_stem(master, enter_stem, sched.type_end_sec, volume=0.22)

        # Transition whoosh into execution phase
        overlay_audio_stem(master, whoosh_stem, self.exec_start_sec, volume=0.45)
        # Success chime when tests pass in terminal
        overlay_audio_stem(master, ding_stem, self.exec_start_sec + 1.2, volume=0.55)

        # Save to 16-bit PCM WAV
        master_sfx_path = self.output_dir / f"{self.lesson.id}_master_soundtrack.wav"
        peak = np.max(np.abs(master))
        if peak > 0.98:
            master = master * (0.95 / peak)
        int16_data = (master * 32767).astype(np.int16)

        with wave.open(str(master_sfx_path), "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(SAMPLE_RATE)
            wf.writeframes(int16_data.tobytes())

        return master_sfx_path
