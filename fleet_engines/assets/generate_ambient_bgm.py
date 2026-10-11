import sys
import math
import numpy as np
from pathlib import Path
import scipy.signal as signal
import subprocess

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SR = 44100
DUR = 65.0  # 65 seconds, ample length for any Short

OUT_DIR = Path(__file__).resolve().parent / "bgm"
OUT_DIR.mkdir(parents=True, exist_ok=True)

def apply_soft_clip(audio, drive=1.2):
    return np.tanh(audio * drive) / drive

def apply_reverb_stereo(left, right, delay_ms=85, feedback=0.45):
    delay_samples = int((delay_ms / 1000.0) * SR)
    out_l = np.copy(left)
    out_r = np.copy(right)
    for i in range(delay_samples, len(left)):
        out_l[i] += out_r[i - delay_samples] * feedback
        out_r[i] += out_l[i - delay_samples] * feedback
    return out_l, out_r

def butter_lowpass(data, cutoff, order=3):
    sos = signal.butter(order, cutoff, btype='low', fs=SR, output='sos')
    return signal.sosfilt(sos, data)

def butter_bandpass(data, lowcut, highcut, order=3):
    sos = signal.butter(order, [lowcut, highcut], btype='band', fs=SR, output='sos')
    return signal.sosfilt(sos, data)

def save_stereo_mp3(left, right, out_path: Path):
    # Normalize peak to -1 dB (0.89)
    peak = max(np.max(np.abs(left)), np.max(np.abs(right)), 1e-6)
    norm_l = (left / peak) * 0.88
    norm_r = (right / peak) * 0.88
    
    # Linear fade in/out
    fade_len = int(SR * 2.0)
    fade_in = np.linspace(0, 1, fade_len)
    fade_out = np.linspace(1, 0, fade_len)
    
    norm_l[:fade_len] *= fade_in
    norm_l[-fade_len:] *= fade_out
    norm_r[:fade_len] *= fade_in
    norm_r[-fade_len:] *= fade_out
    
    # Interleave 16-bit PCM
    stereo = np.empty((len(norm_l), 2), dtype=np.int16)
    stereo[:, 0] = (norm_l * 32767).astype(np.int16)
    stereo[:, 1] = (norm_r * 32767).astype(np.int16)
    
    raw_wav = out_path.with_suffix(".raw.wav")
    import scipy.io.wavfile as wavfile
    wavfile.write(str(raw_wav), SR, stereo)
    
    # Encode with FFmpeg to pristine 320k MP3
    cmd = [
        "ffmpeg", "-y", "-i", str(raw_wav),
        "-codec:a", "libmp3lame", "-b:a", "320k",
        str(out_path)
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    if raw_wav.exists():
        raw_wav.unlink()
    print(f"✅ Generated: {out_path.name} ({out_path.stat().st_size // 1024} KB)")

# ==============================================================================
# TRACK 1: 01_forensic_interrogation.mp3 (FBI Silence & Interrogation Pressure)
# ==============================================================================
def make_forensic_interrogation():
    t = np.linspace(0, DUR, int(SR * DUR), endpoint=False)
    
    # Sub-bass root (40 Hz) + slight detune (40.3 Hz) for slow acoustic beating
    sub = np.sin(2 * np.pi * 40.0 * t) * 0.45
    sub_l = sub + np.sin(2 * np.pi * 40.25 * t) * 0.25
    sub_r = sub + np.sin(2 * np.pi * 39.75 * t) * 0.25
    
    # Minor second dissonance (Tritone drone at 56.6 Hz - F#1)
    tritone_l = np.sin(2 * np.pi * 56.6 * t) * 0.18 * (0.8 + 0.2 * np.sin(2 * np.pi * 0.08 * t))
    tritone_r = np.sin(2 * np.pi * 56.4 * t) * 0.18 * (0.8 + 0.2 * np.cos(2 * np.pi * 0.08 * t))
    
    # Cold AC / HVAC Room rumble (Filtered brownian noise)
    noise = np.cumsum(np.random.normal(0, 0.03, len(t)))
    noise = butter_bandpass(noise, 35, 120, order=3) * 0.25
    
    # Subsonic dread throb (0.6 Hz breathing cycle)
    throb = np.sin(2 * np.pi * 0.6 * t)**4 * np.sin(2 * np.pi * 50 * t) * 0.22
    
    left = sub_l + tritone_l + noise + throb
    right = sub_r + tritone_r + noise + throb
    
    left = butter_lowpass(left, 240)
    right = butter_lowpass(right, 240)
    
    save_stereo_mp3(apply_soft_clip(left), apply_soft_clip(right), OUT_DIR / "01_forensic_interrogation.mp3")

# ==============================================================================
# TRACK 2: 02_dark_mindhunter_dread.mp3 (Psychological Tension, Bowed Resonance)
# ==============================================================================
def make_mindhunter_dread():
    t = np.linspace(0, DUR, int(SR * DUR), endpoint=False)
    
    # Low C1 (32.7 Hz) fundamental
    sub_l = np.sin(2 * np.pi * 32.7 * t) * 0.50
    sub_r = np.sin(2 * np.pi * 32.7 * t + 0.3) * 0.50
    
    # Eerie bowed harmonics (65.4 Hz, 98.1 Hz, 130.8 Hz)
    bow_l = (
        np.sin(2 * np.pi * 65.4 * t) * 0.22 +
        np.sin(2 * np.pi * 98.1 * t + 0.4) * 0.16 +
        np.sin(2 * np.pi * 130.8 * t) * 0.10
    ) * (0.85 + 0.15 * np.sin(2 * np.pi * 0.05 * t))
    
    bow_r = (
        np.sin(2 * np.pi * 65.7 * t) * 0.22 +
        np.sin(2 * np.pi * 97.8 * t - 0.4) * 0.16 +
        np.sin(2 * np.pi * 131.2 * t) * 0.10
    ) * (0.85 + 0.15 * np.cos(2 * np.pi * 0.05 * t))
    
    # High-tension eerie metallic shimmer (Dissonant high frequency filtered low)
    shimmer = np.sin(2 * np.pi * 370.0 * t) * 0.04 * (1 + np.sin(2 * np.pi * 0.15 * t))
    shimmer = butter_bandpass(shimmer, 250, 450)
    
    left = sub_l + bow_l + shimmer
    right = sub_r + bow_r + shimmer * 0.8
    
    left = butter_lowpass(left, 350)
    right = butter_lowpass(right, 350)
    
    save_stereo_mp3(apply_soft_clip(left), apply_soft_clip(right), OUT_DIR / "02_dark_mindhunter_dread.mp3")

# ==============================================================================
# TRACK 3: 03_forbidden_coordinates_void.mp3 (Desolate Abyss, Cave/Coordinates)
# ==============================================================================
def make_forbidden_coordinates():
    t = np.linspace(0, DUR, int(SR * DUR), endpoint=False)
    
    # Seismic subterranean rumble (28 Hz - 55 Hz)
    noise_raw = np.cumsum(np.random.normal(0, 0.05, len(t)))
    deep_rumble = butter_lowpass(noise_raw, 55) * 0.45
    
    # Wind cavern resonance (Slow bandpass sweep)
    wind_noise = np.random.normal(0, 0.1, len(t))
    sweep_fc = 220 + 80 * np.sin(2 * np.pi * 0.04 * t)
    # Simple dynamic bandpass approximation
    wind_l = butter_bandpass(wind_noise, 150, 320) * (0.7 + 0.3 * np.sin(2 * np.pi * 0.07 * t))
    wind_r = butter_bandpass(wind_noise, 160, 340) * (0.7 + 0.3 * np.cos(2 * np.pi * 0.07 * t))
    
    # Sub harmonic drone (45 Hz)
    sub = np.sin(2 * np.pi * 45.0 * t) * 0.35
    
    left = deep_rumble + wind_l * 0.35 + sub
    right = deep_rumble + wind_r * 0.35 + sub
    
    left, right = apply_reverb_stereo(left, right, delay_ms=120, feedback=0.35)
    save_stereo_mp3(apply_soft_clip(left), apply_soft_clip(right), OUT_DIR / "03_forbidden_coordinates_void.mp3")

# ==============================================================================
# TRACK 4: 04_cosmic_singularity_deepspace.mp3 (Interstellar Nebula, Black Hole)
# ==============================================================================
def make_cosmic_singularity():
    t = np.linspace(0, DUR, int(SR * DUR), endpoint=False)
    
    # Cosmic gravitational drone cluster (43.6 Hz + 65.4 Hz + 87.3 Hz)
    f0 = 43.65  # F1
    drone_1 = np.sin(2 * np.pi * f0 * t) * 0.40
    drone_2 = np.sin(2 * np.pi * (f0 * 1.5) * t) * 0.25  # C2
    drone_3 = np.sin(2 * np.pi * (f0 * 2.01) * t) * 0.18 # F2 detuned
    
    # Slow phased stellar sweep
    phase_l = np.sin(2 * np.pi * 0.03 * t)
    phase_r = np.cos(2 * np.pi * 0.03 * t)
    
    # Cosmic radiation pink noise bed
    pink = np.cumsum(np.random.normal(0, 0.02, len(t)))
    pink = butter_bandpass(pink, 60, 220) * 0.30
    
    left = (drone_1 + drone_2 * (1 + 0.3 * phase_l) + drone_3 + pink)
    right = (drone_1 + drone_2 * (1 + 0.3 * phase_r) + drone_3 * 1.1 + pink)
    
    left = butter_lowpass(left, 280)
    right = butter_lowpass(right, 280)
    
    save_stereo_mp3(apply_soft_clip(left), apply_soft_clip(right), OUT_DIR / "04_cosmic_singularity_deepspace.mp3")

# ==============================================================================
# TRACK 5: 05_unsolved_dossier_tension.mp3 (True Crime Cold Case Atmosphere)
# ==============================================================================
def make_unsolved_dossier():
    t = np.linspace(0, DUR, int(SR * DUR), endpoint=False)
    
    # Cold drone in A (55 Hz) with flat 5th dissonance (77.8 Hz)
    root = np.sin(2 * np.pi * 55.0 * t) * 0.40
    dim5 = np.sin(2 * np.pi * 77.78 * t) * 0.16 * (0.8 + 0.2 * np.sin(2 * np.pi * 0.06 * t))
    octave = np.sin(2 * np.pi * 110.0 * t) * 0.12 * (0.8 + 0.2 * np.cos(2 * np.pi * 0.06 * t))
    
    # Very slow pulse (tension swelling without any drum beat)
    swell = (np.sin(2 * np.pi * 0.12 * t)**2) * 0.20
    
    # Low room air ambience
    air = butter_bandpass(np.random.normal(0, 0.04, len(t)), 40, 150)
    
    left = root + dim5 + octave + air + swell * np.sin(2 * np.pi * 55.0 * t)
    right = root + dim5 * 0.9 + octave * 1.1 + air + swell * np.sin(2 * np.pi * 55.3 * t)
    
    save_stereo_mp3(apply_soft_clip(left), apply_soft_clip(right), OUT_DIR / "05_unsolved_dossier_tension.mp3")

# ==============================================================================
# TRACK 6: 06_abyssal_deep_ocean_blackout.mp3 (Mariana Trench / Pitch Black Void)
# ==============================================================================
def make_deep_ocean_abyss():
    t = np.linspace(0, DUR, int(SR * DUR), endpoint=False)
    
    # Extreme sub-bass pressure (33 Hz)
    sub = np.sin(2 * np.pi * 33.0 * t) * 0.50
    
    # Underwater pressure resonance (slow oceanic drift)
    ocean_noise = np.cumsum(np.cumsum(np.random.normal(0, 0.005, len(t))))
    ocean_noise = butter_bandpass(ocean_noise, 25, 90) * 0.40
    
    # Distant eerie hydrophone whale/metal echo
    echo_tone = np.sin(2 * np.pi * 185.0 * t) * 0.06 * (0.5 + 0.5 * np.sin(2 * np.pi * 0.02 * t))
    echo_tone = butter_bandpass(echo_tone, 150, 220)
    
    left = sub + ocean_noise + echo_tone
    right = sub + ocean_noise + echo_tone * 0.7
    
    left, right = apply_reverb_stereo(left, right, delay_ms=150, feedback=0.40)
    save_stereo_mp3(apply_soft_clip(left), apply_soft_clip(right), OUT_DIR / "06_abyssal_deep_ocean_blackout.mp3")

if __name__ == "__main__":
    print(f"🎵 Synthesizing 6 Master Studio-Grade Beatless Drones into: {OUT_DIR}...")
    make_forensic_interrogation()
    make_mindhunter_dread()
    make_forbidden_coordinates()
    make_cosmic_singularity()
    make_unsolved_dossier()
    make_deep_ocean_abyss()
    print("🎉 All 6 Master Ambient Drones Synthesized Successfully!")
