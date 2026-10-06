"""
ElevenLabs Broadcast Voiceover Engine for Vox Studio.
Generates authoritative documentary voiceover using Adam voice and applies broadcast mastering EQ.
"""
from pathlib import Path
import os
import requests
import subprocess
from channel_5_vox_studio.config import ELEVENLABS_API_KEY, VOICE_ID, MODEL_ID, VOICE_STABILITY, VOICE_STYLE, VOICE_SIMILARITY


class VoiceEngine:
    def __init__(self, api_key: str = ELEVENLABS_API_KEY, voice_id: str = VOICE_ID):
        self.api_key = api_key
        self.voice_id = voice_id

    def generate_narration(self, script_text: str, raw_output_path: Path, mastered_output_path: Path) -> Path:
        """Calls ElevenLabs API to generate deep narration and applies broadcast EQ filter."""
        raw_output_path = Path(raw_output_path)
        mastered_output_path = Path(mastered_output_path)
        raw_output_path.parent.mkdir(parents=True, exist_ok=True)
        mastered_output_path.parent.mkdir(parents=True, exist_ok=True)

        url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}"
        headers = {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
        }
        payload = {
            "text": script_text,
            "model_id": MODEL_ID,
            "voice_settings": {
                "stability": VOICE_STABILITY,
                "similarity_boost": VOICE_SIMILARITY,
                "style": VOICE_STYLE,
                "use_speaker_boost": True,
            },
        }

        print(f">> [VoiceEngine] Generating ElevenLabs narration ({len(script_text.split())} words)...")
        res = requests.post(url, headers=headers, json=payload, timeout=30)
        if res.status_code != 200:
            raise RuntimeError(f"ElevenLabs TTS failed: {res.status_code} - {res.text}")

        with open(raw_output_path, "wb") as f:
            f.write(res.content)

        # Broadcast Mastering EQ (Highpass 80Hz, +3.5dB presence at 3.5kHz, broadcast multi-band compression)
        eq_cmd = [
            "ffmpeg", "-y", "-i", str(raw_output_path),
            "-af", "highpass=f=80,equalizer=f=3500:width_type=q:width=1.5:g=3.5,compand=attacks=0.02:decays=0.15:points=-60/-60|-24/-12|0/-2:gain=2",
            "-b:a", "192k", str(mastered_output_path),
        ]
        subprocess.run(eq_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return mastered_output_path
