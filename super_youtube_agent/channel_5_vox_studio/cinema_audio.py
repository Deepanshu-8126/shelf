"""
Cinema-Grade Multi-Track Foley & Diegetic Soundscape Synthesizer for Vox Studio.
Synthesizes professional acoustic layers without external audio dependencies:
1. 50Hz Sub-bass tension drone with analog tape flutter
2. Heavy stamp impact with metallic reverberation
3. Realistic archival paper rustle
4. Highlighter friction squeak
5. Sub-drop cinematic riser & climax boom
"""
from __future__ import annotations

import math
import random
import struct
import wave
from pathlib import Path

SAMPLE_RATE = 44100


class CinemaAudioEngine:
    """Procedurally synthesizes Hollywood-grade documentary sound effects."""

    @classmethod
    def generate_full_soundscape(cls, output_dir: Path, duration_sec: float = 16.0) -> dict[str, Path]:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        drone_p = output_dir / "foley_drone.wav"
        slam_p = output_dir / "foley_slam.wav"
        paper_p = output_dir / "foley_paper.wav"
        marker_p = output_dir / "foley_marker.wav"
        subdrop_p = output_dir / "foley_subdrop.wav"

        cls._make_drone(drone_p, duration_sec)
        cls._make_slam(slam_p)
        cls._make_paper_rustle(paper_p)
        cls._make_marker(marker_p)
        cls._make_subdrop(subdrop_p)

        return {
            "drone": drone_p,
            "slam": slam_p,
            "paper": paper_p,
            "marker": marker_p,
            "subdrop": subdrop_p,
        }

    @staticmethod
    def _make_drone(path: Path, dur: float):
        n = int(SAMPLE_RATE * dur)
        with wave.open(str(path), 'w') as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(SAMPLE_RATE)
            for i in range(n):
                t = i / SAMPLE_RATE
                # 50Hz fundamental + 52.5Hz binaural beat
                s1 = math.sin(2 * math.pi * 50.0 * t)
                s2 = math.sin(2 * math.pi * 52.8 * t) * 0.75
                h1 = math.sin(2 * math.pi * 100.0 * t) * 0.25
                env = min(1.0, t / 1.2) * (0.85 + 0.15 * math.sin(2 * math.pi * 0.15 * t))
                noise = (random.random() * 2.0 - 1.0) * 0.015
                val = int(max(-32767, min(32767, (s1 + s2 + h1 + noise) * 0.35 * env * 32767)))
                w.writeframes(struct.pack('<h', val))

    @staticmethod
    def _make_slam(path: Path):
        dur = 2.0
        n = int(SAMPLE_RATE * dur)
        with wave.open(str(path), 'w') as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(SAMPLE_RATE)
            for i in range(n):
                t = i / SAMPLE_RATE
                env = math.exp(-t * 4.5)
                freq = 120.0 * math.exp(-t * 9.0) + 38.0
                impact = math.sin(2 * math.pi * freq * t) * env
                metal = math.sin(2 * math.pi * 840.0 * t) * math.exp(-t * 18.0) * 0.25
                val = int(max(-32767, min(32767, (impact + metal) * 0.95 * 32767)))
                w.writeframes(struct.pack('<h', val))

    @staticmethod
    def _make_paper_rustle(path: Path):
        dur = 1.0
        n = int(SAMPLE_RATE * dur)
        with wave.open(str(path), 'w') as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(SAMPLE_RATE)
            for i in range(n):
                t = i / SAMPLE_RATE
                env = math.sin(math.pi * (t / dur)) ** 1.5
                noise = (random.random() * 2.0 - 1.0) * 0.7
                # High frequency paper friction
                squeak = math.sin(2 * math.pi * (2200 + 300 * math.sin(20 * t)) * t) * 0.15
                val = int(max(-32767, min(32767, (noise + squeak) * env * 0.45 * 32767)))
                w.writeframes(struct.pack('<h', val))

    @staticmethod
    def _make_marker(path: Path):
        dur = 1.4
        n = int(SAMPLE_RATE * dur)
        with wave.open(str(path), 'w') as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(SAMPLE_RATE)
            for i in range(n):
                t = i / SAMPLE_RATE
                env = math.sin(math.pi * (t / dur)) ** 0.8
                friction_f = 1750.0 + 350.0 * math.sin(2 * math.pi * 14.0 * t)
                squeak = math.sin(2 * math.pi * friction_f * t) * 0.35
                noise = (random.random() * 2.0 - 1.0) * 0.65
                val = int(max(-32767, min(32767, (noise + squeak) * env * 0.45 * 32767)))
                w.writeframes(struct.pack('<h', val))

    @staticmethod
    def _make_subdrop(path: Path):
        dur = 2.5
        n = int(SAMPLE_RATE * dur)
        with wave.open(str(path), 'w') as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(SAMPLE_RATE)
            for i in range(n):
                t = i / SAMPLE_RATE
                env = math.exp(-t * 2.2)
                freq = 90.0 * math.exp(-t * 4.0) + 30.0
                sub = math.sin(2 * math.pi * freq * t) * env
                val = int(max(-32767, min(32767, sub * 0.95 * 32767)))
                w.writeframes(struct.pack('<h', val))
