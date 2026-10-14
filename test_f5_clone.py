import os
import sys
import torch
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import soundfile as sf
import torchaudio

# Monkeypatch torchaudio with soundfile to avoid Windows torchcodec DLL crash
def _sf_load(uri, *args, **kwargs):
    data, sr = sf.read(uri, dtype="float32")
    t = torch.from_numpy(data)
    if t.ndim == 1:
        t = t.unsqueeze(0)
    else:
        t = t.t()
    return t, sr

def _sf_save(uri, src, sample_rate, channels_first=True, **kwargs):
    if isinstance(src, torch.Tensor):
        src = src.detach().cpu().numpy()
    if channels_first and src.ndim > 1:
        src = src.T
    sf.write(uri, src, sample_rate)

torchaudio.load = _sf_load
torchaudio.save = _sf_save

from f5_tts.api import F5TTS

ref_audio = "d:/facts_yt/fleet_engines/output/elevenlabs_bella_sample.mp3"
ref_text = "ब्रह्मांड का सबसे बड़ा रहस्य हमारी समझ से परे है"
gen_text = "क्या आपको पता है कि समंदर के 11 किलोमीटर नीचे वैज्ञानिकों को क्या मिला?"
out_wav = "d:/facts_yt/fleet_engines/output/f5_bella_test.wav"

print("Initializing GitHub SOTA Cloner F5-TTS...")
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Device: {device}")

f5tts = F5TTS(device=device)

print(f"Cloning voice from '{Path(ref_audio).name}'...")
wav, sr, _ = f5tts.infer(
    ref_file=ref_audio,
    ref_text=ref_text,
    gen_text=gen_text,
    file_wave=out_wav,
    nfe_step=32,
    speed=1.0
)

print(f"Generated Cloned Voice at: {out_wav}")
if os.path.exists(out_wav):
    print(f"Success! File size: {os.path.getsize(out_wav)} bytes")
