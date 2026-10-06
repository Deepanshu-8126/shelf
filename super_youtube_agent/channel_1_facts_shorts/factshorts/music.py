"""Commercial-safe background music generation and auto-selection.

LICENSING POLICY:
- MusicGen is STRICTLY BANNED (weights are CC-BY-NC 4.0 -> copyright strike risk).
- Supported Safe Providers:
  1. Mubert API (royalty-free tier for commercial use)
  2. Pixabay Audio (free commercial license, no attribution needed)
  3. Freesound CC0 / Public Domain
  4. Local Procedural Harmonic Bed (100% offline, ₹0, pure mathematical synthesis)
  5. ACE-Step / DiffRhythm 2 (MIT / Apache-2.0 local GPU if available)
"""
from __future__ import annotations

import math
import os
import random
import struct
import wave
from pathlib import Path
from typing import Any

import httpx
import numpy as np

from .config import Config, get_config
from .utils import module_logger

log = module_logger("music")

MUSIC_EXTS = {".mp3", ".m4a", ".wav", ".aac", ".ogg", ".opus", ".flac"}

MOOD_MAP: dict[str, dict[str, Any]] = {
    "space": {
        "mood": "space",
        "genre": "ambient",
        "bpm": 70,
        "prompt": "epic, orchestral, ambient, 70 BPM",
        "keywords": "space ambient cinematic galaxy",
        "base_freq": 130.81,  # C3
        "chords": [(130.81, 155.56, 196.00), (116.54, 138.59, 174.61), (103.83, 130.81, 155.56)],  # Cm, Bbm, Ab
    },
    "space_fact": {
        "mood": "space",
        "genre": "ambient",
        "bpm": 70,
        "prompt": "epic, orchestral, ambient, 70 BPM",
        "keywords": "space ambient cinematic galaxy",
        "base_freq": 130.81,
        "chords": [(130.81, 155.56, 196.00), (116.54, 138.59, 174.61), (103.83, 130.81, 155.56)],
    },
    "fun_fact": {
        "mood": "lofi",
        "genre": "chillhop",
        "bpm": 120,
        "prompt": "upbeat, happy, lo-fi, 120 BPM",
        "keywords": "upbeat happy lofi hip hop beats",
        "base_freq": 146.83,  # D3
        "chords": [(146.83, 174.61, 220.00), (164.81, 196.00, 246.94), (130.81, 164.81, 196.00)],
    },
    "scary_fact": {
        "mood": "dark",
        "genre": "cinematic",
        "bpm": 80,
        "prompt": "dramatic, dark, cinematic, 80 BPM",
        "keywords": "dramatic dark horror cinematic suspense",
        "base_freq": 103.83,  # Ab2
        "chords": [(103.83, 123.47, 155.56), (98.00, 116.54, 146.83), (87.31, 103.83, 130.81)],
    },
    "tech_fact": {
        "mood": "tech",
        "genre": "electronic",
        "bpm": 130,
        "prompt": "electronic, futuristic, 130 BPM",
        "keywords": "futuristic electronic technology synth",
        "base_freq": 138.59,  # C#3
        "chords": [(138.59, 164.81, 207.65), (123.47, 146.83, 185.00), (110.00, 138.59, 164.81)],
    },
    "history_fact": {
        "mood": "classical",
        "genre": "cinematic",
        "bpm": 60,
        "prompt": "classical, piano, emotional, 60 BPM",
        "keywords": "classical piano emotional historical",
        "base_freq": 110.00,  # A2
        "chords": [(110.00, 130.81, 164.81), (130.81, 164.81, 196.00), (98.00, 123.47, 146.83)],
    },
    "psychology": {
        "mood": "lofi",
        "genre": "chillhop",
        "bpm": 120,
        "prompt": "upbeat, happy, lo-fi, 120 BPM",
        "keywords": "lofi hip hop chill beats study",
        "base_freq": 146.83,
        "chords": [(146.83, 174.61, 220.00), (164.81, 196.00, 246.94), (130.81, 164.81, 196.00)],
    },
    "history": {
        "mood": "classical",
        "genre": "cinematic",
        "bpm": 60,
        "prompt": "classical, piano, emotional, 60 BPM",
        "keywords": "cinematic piano emotional dramatic historical",
        "base_freq": 110.00,
        "chords": [(110.00, 130.81, 164.81), (130.81, 164.81, 196.00), (98.00, 123.47, 146.83)],
    },
    "science": {
        "mood": "tech",
        "genre": "electronic",
        "bpm": 130,
        "prompt": "electronic, futuristic, 130 BPM",
        "keywords": "futuristic electronic technology synth",
        "base_freq": 138.59,
        "chords": [(138.59, 164.81, 207.65), (123.47, 146.83, 185.00), (110.00, 138.59, 164.81)],
    },
    "animals": {
        "mood": "acoustic",
        "genre": "acoustic",
        "bpm": 90,
        "prompt": "acoustic, playful, warm, nature, 90 BPM",
        "keywords": "acoustic guitar playful nature bright",
        "base_freq": 146.83,
        "chords": [(146.83, 185.00, 220.00), (164.81, 196.00, 246.94), (174.61, 220.00, 261.63)],
    },
}


def synthesize_harmonic_bed(niche: str, duration: float, out_path: Path) -> Path:
    """Synthesizes a 100% royalty-free, warm harmonic ambient drone pad locally.

    Zero external API, zero GPU, zero licensing ambiguity. Uses multi-oscillator
    additive synthesis with warm second-harmonic saturation and gentle low-frequency
    modulation.
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sample_rate = 44100
    total_samples = int(duration * sample_rate)
    t = np.linspace(0, duration, total_samples, endpoint=False)

    spec = MOOD_MAP.get(niche, MOOD_MAP["space"])
    chord_list = spec.get("chords") or [(130.81, 155.56, 196.00)]

    audio = np.zeros(total_samples, dtype=np.float32)

    # Crossfade through 3 chord inversions
    chord_duration = duration / len(chord_list)
    for idx, chord in enumerate(chord_list):
        t_start = idx * chord_duration
        t_end = (idx + 1) * chord_duration

        # Soft window for chord transition
        chord_env = np.sin(np.clip((t - t_start) / max(0.01, chord_duration), 0, 1) * np.pi) ** 2

        for f in chord:
            # Fundamental + soft octave + gentle detuned shimmer
            osc1 = np.sin(2 * np.pi * f * t)
            osc2 = 0.45 * np.sin(2 * np.pi * (f * 1.998) * t)
            osc3 = 0.25 * np.sin(2 * np.pi * (f * 0.5) * t)
            sub = 0.30 * np.sin(2 * np.pi * (f * 0.25) * t)

            # LFO movement (slow 0.15 Hz breathing)
            lfo = 0.85 + 0.15 * np.sin(2 * np.pi * 0.15 * t)
            audio += (osc1 + osc2 + osc3 + sub) * chord_env * lfo

    # Overall master fade in (2s) and fade out (3s)
    fade_in_len = int(min(2.0, duration * 0.2) * sample_rate)
    fade_out_len = int(min(3.0, duration * 0.25) * sample_rate)
    master_env = np.ones(total_samples, dtype=np.float32)
    if fade_in_len > 0:
        master_env[:fade_in_len] = np.linspace(0, 1, fade_in_len)
    if fade_out_len > 0:
        master_env[-fade_out_len:] = np.linspace(1, 0, fade_out_len)

    audio *= master_env

    # Soft tape-style saturation to prevent clipping and add warmth
    audio = np.tanh(audio * 0.35)

    # Normalize to -3dB
    peak = np.max(np.abs(audio)) or 1.0
    audio = (audio / peak) * 0.70

    # Write 16-bit PCM stereo WAV
    int_audio = (audio * 32767).astype(np.int16)
    stereo_audio = np.column_stack((int_audio, int_audio))

    with wave.open(str(out_path), "w") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(stereo_audio.tobytes())

    log.info("synthesized %s harmonic ambient bed (%.1fs) -> %s", niche, duration, out_path.name)
    return out_path


async def fetch_pixabay_music(query: str, cfg: Config) -> Path | None:
    """Download a commercial royalty-free track from Pixabay Audio API."""
    key = cfg.pixabay_api_key or os.getenv("PIXABAY_API_KEY")
    if not key:
        return None
    url = "https://pixabay.com/api/"
    params = {
        "key": key,
        "q": query,
        "safesearch": "true",
        "per_page": 5,
    }
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.get(url, params=params)
            if resp.status_code != 200:
                return None
            data = resp.json()
            hits = data.get("hits") or []
            if not hits:
                return None
            # pick top matching track
            track = hits[0]
            audio_url = track.get("audio") or track.get("audio_download")
            if not audio_url:
                return None
            dl_resp = await client.get(audio_url)
            if dl_resp.status_code == 200:
                out_path = cfg.music_dir / f"pixabay_{track.get('id', 'track')}.mp3"
                out_path.write_bytes(dl_resp.content)
                log.info("downloaded royalty-free Pixabay music: %s", out_path.name)
                return out_path
    except Exception as exc:  # noqa: BLE001
        log.warning("pixabay music fetch failed: %s", exc)
    return None


async def fetch_mubert_music(mood: str, duration: int, cfg: Config) -> Path | None:
    """Fetch 30-60s royalty-free track from Mubert API (free tier 50/month)."""
    api_key = os.getenv("MUBERT_API_KEY")
    if not api_key:
        return None
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            payload = {
                "method": "TTMRecordTrack",
                "params": {
                    "text": mood,
                    "duration": duration,
                    "bitrate": "192",
                    "format": "mp3",
                },
            }
            resp = await client.post("https://api-b2b.mubert.com/v2/TTMRecordTrack", json=payload, headers={"Authorization": f"Bearer {api_key}"})
            if resp.status_code == 200:
                data = resp.json()
                dl_url = ((data.get("data") or {}).get("tasks") or [{}])[0].get("download_link")
                if dl_url:
                    dl = await client.get(dl_url)
                    out = cfg.music_dir / f"mubert_{int(duration)}s.mp3"
                    out.write_bytes(dl.content)
                    log.info("generated Mubert track: %s", out.name)
                    return out
    except Exception as exc:  # noqa: BLE001
        log.warning("mubert API call failed: %s", exc)
    return None


def generate_ace_step(prompt: str, duration: int, out_path: Path) -> Path | None:
    """Run local ACE-Step 1.5 generation (MIT license, local GPU)."""
    ace_step_dir = os.getenv("ACE_STEP_PATH", "ace_step")
    ace_script = Path(ace_step_dir) / "generate.py"
    if not ace_script.exists():
        return None
    try:
        import subprocess

        out_path.parent.mkdir(parents=True, exist_ok=True)
        res = subprocess.run(
            ["python", str(ace_script), "--prompt", prompt, "--duration", str(duration), "--output", str(out_path)],
            capture_output=True,
            text=True,
            timeout=180,
        )
        if res.returncode == 0 and out_path.exists():
            log.info("ACE-Step generated music: %s", out_path.name)
            return out_path
    except Exception as exc:  # noqa: BLE001
        log.warning("ACE-Step generation failed: %s", exc)
    return None


async def search_freesound_cc0(keywords: str, cfg: Config) -> Path | None:
    """VibeMatch-AI style: Search Freesound API for CC0 / Public Domain audio."""
    api_key = os.getenv("FREESOUND_API_KEY")
    if not api_key:
        return None
    try:
        url = "https://freesound.org/apiv2/search/text/"
        params = {
            "query": keywords,
            "filter": 'license:"Creative Commons 0"',
            "fields": "id,name,previews,duration",
            "token": api_key,
            "page_size": 5,
        }
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.get(url, params=params)
            if resp.status_code == 200:
                results = resp.json().get("results", [])
                for r in results:
                    preview_url = r.get("previews", {}).get("preview-hq-mp3")
                    if preview_url:
                        dl = await client.get(preview_url)
                        if dl.status_code == 200:
                            out = cfg.music_dir / f"freesound_cc0_{r.get('id')}.mp3"
                            out.write_bytes(dl.content)
                            log.info("downloaded CC0 Freesound track: %s", out.name)
                            return out
    except Exception as exc:  # noqa: BLE001
        log.warning("freesound CC0 fetch failed: %s", exc)
    return None


async def ensure_music_track(niche: str, duration: float = 30.0, cfg: Config | None = None) -> Path | None:
    """Guarantees a 100% commercial-safe, royalty-free background track exists.

    Order of resolution:
    1. Existing matching track in `assets/music/{niche}*`
    2. Any existing royalty-free track in `assets/music/`
    3. ACE-Step local model (if GPU & repo installed)
    4. Mubert API (if MUBERT_API_KEY configured)
    5. Pixabay Audio (if PIXABAY_API_KEY configured)
    6. Freesound CC0 / VibeMatch (if FREESOUND_API_KEY configured)
    7. Local procedural harmonic bed synthesis (100% offline fallback)
    """
    cfg = cfg or get_config()
    if not cfg.music_enabled:
        return None

    music_dir = cfg.music_dir
    music_dir.mkdir(parents=True, exist_ok=True)

    # 1. Search local folder for existing files matching this niche
    existing = [p for p in sorted(music_dir.iterdir()) if p.suffix.lower() in MUSIC_EXTS]
    niche_tracks = [p for p in existing if niche.lower() in p.stem.lower()]
    if niche_tracks:
        return random.choice(niche_tracks)

    spec = MOOD_MAP.get(niche, MOOD_MAP["space"])

    # 2. Local ACE-Step if available
    ace_out = music_dir / f"ace_{niche}_{int(duration)}s.mp3"
    ace_res = generate_ace_step(spec["prompt"], int(duration), ace_out)
    if ace_res:
        return ace_res

    # 3. Try Mubert API if key present
    mubert_track = await fetch_mubert_music(spec["prompt"], int(duration), cfg)
    if mubert_track:
        return mubert_track

    # 4. Try Pixabay Audio API if key present
    pixabay_track = await fetch_pixabay_music(spec["keywords"], cfg)
    if pixabay_track:
        return pixabay_track

    # 5. YouTube Free Audio Library API (ThibaultJanBeyer, official YouTube library, zero key, 100% monetized safe)
    yt_track = await fetch_youtube_audio_library(spec["keywords"], cfg)
    if yt_track:
        return yt_track

    # 6. Freesound CC0 / VibeMatch
    freesound_track = await search_freesound_cc0(spec["keywords"], cfg)
    if freesound_track:
        return freesound_track

    # 7. Generate harmonic ambient bed locally (instant, zero cost, completely safe)
    out_synth = music_dir / f"{niche}_ambient_bed.wav"
    return synthesize_harmonic_bed(niche, max(duration, 30.0), out_synth)


async def fetch_youtube_audio_library(keywords: str, cfg: Config) -> Path | None:
    """Download official free music from YouTube Free Audio Library API.

    Repo: ThibaultJanBeyer/YouTube-Free-Audio-Library-API
    100% YouTube monetization cleared, zero copyright strike risk, zero API keys required.
    """
    url = "https://thibaultjanbeyer.github.io/YouTube-Free-Audio-Library-API/api.json"
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url)
            if resp.status_code != 200:
                return None
            data = resp.json()
            tracks = data.get("all") or data.get("arr") or []
            if not tracks:
                return None

            kw_terms = [k.strip().lower() for k in keywords.split() if len(k) > 3]
            matches = []
            for t in tracks:
                name = str(t.get("name", "")).lower()
                if any(kw in name for kw in kw_terms):
                    matches.append(t)

            pick = random.choice(matches) if matches else random.choice(tracks[:50])
            drive_id = pick.get("id")
            track_name = pick.get("name", "yt_track.mp3")
            if not drive_id:
                return None

            dl_url = f"https://drive.google.com/uc?export=download&id={drive_id}"
            dl_resp = await client.get(dl_url, follow_redirects=True, timeout=30.0)
            if dl_resp.status_code == 200 and len(dl_resp.content) > 10000:
                safe_name = track_name.replace(" ", "_")
                out_path = cfg.music_dir / f"ytlib_{safe_name}"
                out_path.write_bytes(dl_resp.content)
                log.info("downloaded YouTube Audio Library track: %s", out_path.name)
                return out_path
    except Exception as exc:  # noqa: BLE001
        log.warning("youtube audio library fetch failed: %s", exc)
    return None


def generate_music(mood: str, duration: int = 30) -> str:
    """Direct API helper matching FactShorts automation workflow.

    mood: "upbeat", "dramatic", "cinematic", "lofi", "epic"
    duration: seconds (30-60 for shorts)
    Returns: path string to generated or matched .mp3 / .wav
    """
    import asyncio
    import concurrent.futures

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        with concurrent.futures.ThreadPoolExecutor() as pool:
            p = pool.submit(asyncio.run, ensure_music_track(mood, float(duration))).result()
    else:
        p = asyncio.run(ensure_music_track(mood, float(duration)))

    return str(p) if p else ""


def get_music(mood: str, duration: int = 30) -> str:
    """Direct alias for generate_music matching updated 2026 guidelines."""
    return generate_music(mood, duration)


def auto_select_music(video_mood: str) -> str:
    """Video ke mood ke hisaab se music select/generate karo."""
    return generate_music(video_mood, 30)


