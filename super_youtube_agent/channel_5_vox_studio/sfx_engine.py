"""
Procedural Diegetic SFX Generator for Vox Studio.
Generates Foley sound design without external dependencies:
- Paper rustle & document handling
- Marker squeak / highlight swipe
- 50Hz deep ocean tension drone
- Cinematic impact / declassified stamp slam
"""
from pathlib import Path
import math
import wave
import struct
import random

SAMPLE_RATE = 44100


def generate_tension_drone(output_path: Path, duration_sec: float = 60.0):
    """Deep 50Hz sub-bass drone with pulsing dark dissonance."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    num_samples = int(SAMPLE_RATE * duration_sec)
    
    with wave.open(str(output_path), 'w') as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(SAMPLE_RATE)
        
        for i in range(num_samples):
            t = i / SAMPLE_RATE
            # 50Hz fundamental + 52Hz beat frequency (creates unsettling slow pulse)
            sub1 = math.sin(2 * math.pi * 50.0 * t)
            sub2 = math.sin(2 * math.pi * 52.5 * t) * 0.7
            harm = math.sin(2 * math.pi * 100.0 * t) * 0.3
            
            # Slow volume swell
            env = min(1.0, t / 1.5) * (0.8 + 0.2 * math.sin(2 * math.pi * 0.2 * t))
            sample = (sub1 + sub2 + harm) * 0.35 * env
            
            # Subtle tape flutter noise
            flutter = (random.random() * 2.0 - 1.0) * 0.015
            sample += flutter
            
            val = int(max(-32767, min(32767, sample * 32767)))
            wav.writeframes(struct.pack('<h', val))


def generate_marker_scratch(output_path: Path, duration_sec: float = 1.2):
    """Procedural squeak of a highlighter marker sliding across rough archival paper."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    num_samples = int(SAMPLE_RATE * duration_sec)
    
    with wave.open(str(output_path), 'w') as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(SAMPLE_RATE)
        
        for i in range(num_samples):
            t = i / SAMPLE_RATE
            env = math.sin(math.pi * (t / duration_sec)) ** 0.5
            friction_freq = 1800 + 400 * math.sin(2 * math.pi * 12.0 * t)
            squeak = math.sin(2 * math.pi * friction_freq * t) * 0.2
            noise = (random.random() * 2.0 - 1.0) * 0.8
            sample = (noise + squeak) * env * 0.45
            
            val = int(max(-32767, min(32767, sample * 32767)))
            wav.writeframes(struct.pack('<h', val))


def generate_cinematic_boom(output_path: Path, duration_sec: float = 2.0):
    """Heavy low-frequency stamp impact / boom."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    num_samples = int(SAMPLE_RATE * duration_sec)
    
    with wave.open(str(output_path), 'w') as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(SAMPLE_RATE)
        
        for i in range(num_samples):
            t = i / SAMPLE_RATE
            env = math.exp(-t * 3.5)
            freq = 110.0 * math.exp(-t * 8.0) + 40.0
            sample = math.sin(2 * math.pi * freq * t) * env * 0.95
            
            val = int(max(-32767, min(32767, sample * 32767)))
            wav.writeframes(struct.pack('<h', val))
