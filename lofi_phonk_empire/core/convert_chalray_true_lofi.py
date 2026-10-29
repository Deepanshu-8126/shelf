import os
import sys
import subprocess as sp
import numpy as np
import soundfile as sf
from pathlib import Path
from pedalboard import Pedalboard, Reverb, LowpassFilter, PitchShift, Chorus

sys.stdout.reconfigure(encoding='utf-8')

base_dir = Path(r"d:\facts_yt\lofi_phonk_empire")
raw_audio = base_dir / "raw_stems" / "chalray.mp3"
output_dir = base_dir / "output"
output_dir.mkdir(parents=True, exist_ok=True)

out_mp3 = output_dir / "chalray_true_lofi_master.mp3"
out_wav = output_dir / "chalray_true_lofi_master.wav"
tmp_slice = output_dir / "tmp_chalray_slice.wav"

rain_path = base_dir / "lofi-music-generator" / "app" / "data" / "effects" / "rain_thunder.wav"

sr = 44100
start_sec = 0.0
dur_sec = 135.65 # Exactly matches verified LRC duration (02:15.65)

print(f"[1/4] Extracting {dur_sec}s slice from {raw_audio.name}...", flush=True)
cmd = f'ffmpeg -y -ss {start_sec} -t {dur_sec} -i "{raw_audio}" -ar {sr} -ac 2 "{tmp_slice}"'
sp.run(cmd, shell=True, check=True, stdout=sp.DEVNULL, stderr=sp.DEVNULL)

data, _ = sf.read(tmp_slice)
tmp_slice.unlink(missing_ok=True)

print("[2/4] Applying True Indian Lo-Fi DSP Engine (Pedalboard: Pitch -1.75st, Lowpass 7200Hz, Chorus, Warm Reverb)...", flush=True)
dsp = Pedalboard([
    PitchShift(semitones=-1.75),
    LowpassFilter(cutoff_frequency_hz=7200),
    Chorus(rate_hz=0.5, depth=0.15, mix=0.10),
    Reverb(room_size=0.65, damping=0.50, wet_level=0.18, dry_level=0.86, width=1.0)
])
lofi_audio = dsp(data, sr)

# Smooth 0.8s fade in and 2.5s fade out
fade_in = np.linspace(0, 1, int(0.8 * sr))[:, np.newaxis]
fade_out = np.linspace(1, 0, int(2.5 * sr))[:, np.newaxis]
lofi_audio[:len(fade_in)] *= fade_in
lofi_audio[-len(fade_out):] *= fade_out

print("[3/4] Layering gentle ambient rain texture...", flush=True)
if rain_path.exists():
    rain_raw, _ = sf.read(rain_path)
    reps = int(np.ceil(len(lofi_audio) / len(rain_raw)))
    rain_layer = np.tile(rain_raw, (reps, 1))[:len(lofi_audio)] * 0.06
    final_mix = lofi_audio + rain_layer
else:
    final_mix = lofi_audio

# Peak normalize to 0.94
peak = np.max(np.abs(final_mix))
if peak > 0:
    final_mix = (final_mix / peak) * 0.94

# Save intermediate master wav
sf.write(out_wav, final_mix, sr)

# Export high quality 320kbps MP3
cmd_mp3 = f'ffmpeg -y -i "{out_wav}" -b:a 320k "{out_mp3}"'
sp.run(cmd_mp3, shell=True, check=True, stdout=sp.DEVNULL, stderr=sp.DEVNULL)

print(f"[OK] Master True Lo-Fi Audio Exported successfully:")
print(f"  MP3: {out_mp3} ({dur_sec:.2f}s)")
print(f"  WAV: {out_wav} ({dur_sec:.2f}s)")
