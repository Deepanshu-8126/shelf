"""Voiceover: free local engines by default, optional ElevenLabs for "human" narration.

Providers
---------
* ``kokoro``     - Kokoro-82M (Apache-2.0), runs on your CPU, no key, no billing.
                   ~325 MB model downloaded once into ``TTS_MODEL_DIR``; 54 voices;
                   ~1.3x realtime. Word timings come from faster-whisper (see align.py).
* ``piper``      - Piper (MIT), one small ONNX file per voice (~63 MB), ~8x realtime -
                   the lightest way to get a free voice on a 1 GB host.
* ``local``      - picks kokoro when installed, otherwise piper.
* ``edge``       - Microsoft neural voices over edge-tts. Free, no key, unlimited,
                   returns word-level timings that feed the captions directly.
* ``elevenlabs`` - ElevenLabs API with character-level timestamps, so captions stay
                   word accurate. Needs ``ELEVENLABS_API_KEY`` (+ ``ELEVENLABS_VOICE_ID``).
                   **Licensing:** the ElevenLabs FREE plan is non-commercial and requires
                   attribution - for a monetized channel you need their paid Starter tier
                   or above. The bot prints a warning when it detects a free-tier key.
* ``espeak``     - offline last resort (robotic). Only used if nothing else runs.

``VOICE_PROVIDER=auto`` (default) picks a free local engine when one is installed,
otherwise edge-tts. ElevenLabs only runs when you ask for it *and* set a key.
Monthly character usage is tracked in SQLite so you can see how much of a paid/free
quota you have burned: ``/status`` shows it, the log warns at 80% and 100%.
"""
from __future__ import annotations

import asyncio
import base64
import random
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import httpx

from . import db
from .config import Config, get_config
from .tts_local import available_engines, pick_local_voice, synthesize_local
from .utils import have_binary, media_duration, module_logger, run_cmd

LOCAL_ENGINES = {"kokoro", "piper"}

log = module_logger("voice")

# Curated natural-sounding edge-tts voices per niche (variety = less "mass produced").
VOICES: dict[str, list[str]] = {
    "space": ["en-US-ChristopherNeural", "en-GB-RyanNeural", "en-US-EricNeural"],
    "psychology": ["en-US-AriaNeural", "en-GB-SoniaNeural", "en-US-MichelleNeural"],
    "history": ["en-GB-ThomasNeural", "en-US-GuyNeural", "en-AU-WilliamNeural"],
    "science": ["en-US-JennyNeural", "en-US-BrandonNeural", "en-GB-LibbyNeural"],
    "animals": ["en-US-AnaNeural", "en-US-SteffanNeural", "en-AU-NatashaNeural"],
}
DEFAULT_VOICES = ["en-US-AriaNeural", "en-US-GuyNeural", "en-GB-SoniaNeural"]

# ElevenLabs pre-made voices available on every account (paste your own ID to override)
ELEVENLABS_VOICES: dict[str, str] = {
    "Rachel": "21m00Tcm4TlvDq8ikWAM",
    "Adam": "pNInz6obpgDQGcFmaJgB",
    "Bella": "EXAVITQu4vr4xnSDxMaL",
    "Antoni": "ErXwobaYiN019PkySvjV",
    "Josh": "TxGEqnHWrfWFTfGW9XjX",
    "Elli": "MF3mGyEYCl7XYWbV9V6O",
    "Sam": "yoZ06aMxZJJ28mfd3POQ",
    "Charlotte": "XB0fDUnXU5powFXDhCwa",
}
ELEVENLABS_TTS = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/with-timestamps"
ELEVENLABS_VOICES_API = "https://api.elevenlabs.io/v1/voices"
ELEVENLABS_BASE = "https://api.elevenlabs.io"


@dataclass
class WordTiming:
    word: str
    start: float
    end: float


@dataclass
class VoiceResult:
    path: Path
    duration: float
    words: list[WordTiming] = field(default_factory=list)
    voice: str = ""
    provider: str = ""
    characters: int = 0
    # local engines return no word timings, but they do return exact sentence anchors:
    # [(sentence_text, start_seconds, duration_seconds), ...] - used by align.py
    segments: list[tuple[str, float, float]] = field(default_factory=list)
    speed: float = 1.0

    @property
    def has_timings(self) -> bool:
        return len(self.words) > 0


# --------------------------------------------------------------------- selection
def provider_for(cfg: Config) -> str:
    """Runtime choice: SQLite setting wins over .env, so /voiceprovider works live."""
    try:
        stored = db.get_setting("voice_provider")
    except Exception:  # noqa: BLE001 - e.g. before init_db()
        stored = None
    want = (stored or cfg.voice_provider or "auto").lower()
    if want == "auto":
        # the promise of v3: a free, open-source, key-less voice whenever possible
        installed = available_engines()
        if "kokoro" in installed:
            return "kokoro"
        if "piper" in installed:
            return "piper"
        return "edge"
    if want == "local":
        installed = available_engines()
        if "kokoro" in installed:
            return "kokoro"
        if "piper" in installed:
            return "piper"
        log.warning("VOICE_PROVIDER=local but neither kokoro-onnx nor piper-tts is installed -> edge-tts")
        return "edge"
    if want == "elevenlabs" and not cfg.elevenlabs_api_key:
        # asked for ElevenLabs without a key: report what will actually be used
        return provider_for_local_or_edge(cfg)
    return want


def provider_for_local_or_edge(cfg: Config) -> str:
    installed = available_engines()
    if "kokoro" in installed:
        return "kokoro"
    if "piper" in installed:
        return "piper"
    return "edge"


def pick_voice(niche: str, cfg: Config | None = None) -> str:
    cfg = cfg or get_config()
    if cfg.voice:
        return cfg.voice
    provider = provider_for(cfg)
    if provider == "elevenlabs":
        return cfg.elevenlabs_voice_id or random.choice(list(ELEVENLABS_VOICES.values()))
    if provider in LOCAL_ENGINES:
        return pick_local_voice(niche, provider, cfg)
    return random.choice(VOICES.get(niche, DEFAULT_VOICES))


def elevenlabs_voice_name(voice_id: str) -> str:
    for name, vid in ELEVENLABS_VOICES.items():
        if vid == voice_id:
            return name
    return voice_id or "custom"


# --------------------------------------------------------------------- edge-tts
async def _edge_tts(text: str, out_path: Path, voice: str, cfg: Config) -> tuple[list[WordTiming], float]:
    import edge_tts  # imported lazily so the module works without it installed
    import re

    out_path.parent.mkdir(parents=True, exist_ok=True)
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]

    # If only 1 sentence or fallback, use single-pass communicate
    if len(sentences) < 2:
        communicate = edge_tts.Communicate(
            text, voice, rate=cfg.voice_rate, volume=cfg.voice_volume, boundary="WordBoundary"
        )
        words: list[WordTiming] = []
        with open(out_path, "wb") as fh:
            async for chunk in communicate.stream():
                ctype = chunk.get("type")
                if ctype == "audio":
                    fh.write(chunk["data"])
                elif ctype == "WordBoundary":
                    start = float(chunk["offset"]) / 10_000_000
                    dur = float(chunk.get("duration") or 0) / 10_000_000
                    words.append(WordTiming(str(chunk["text"]), start, start + max(dur, 0.05)))
        return words, media_duration(out_path)

    # 3-Tier Vocal Energy Modulation:
    # Tier 1 (Hook 0-3s): High Pitch & Energetic Rate to stop the scroll (+5Hz, +7%)
    # Tier 2 (Body 3-25s): Deep Baritone / Mystery Tone (-2Hz, +0%)
    # Tier 3 (Payoff): Punchy Drop (+1Hz, -3%)
    chunks: list[tuple[str, str, str]] = []
    chunks.append((sentences[0], "+5Hz", "+7%"))
    if len(sentences) == 2:
        chunks.append((sentences[1], "+0Hz", "-2%"))
    else:
        body = " ".join(sentences[1:-1])
        chunks.append((body, "-2Hz", "+0%"))
        chunks.append((sentences[-1], "+1Hz", "-3%"))

    all_words: list[WordTiming] = []
    current_offset = 0.0
    with open(out_path, "wb") as master_fh:
        for chunk_text, pitch, rate in chunks:
            comm = edge_tts.Communicate(
                chunk_text, voice, pitch=pitch, rate=rate, volume=cfg.voice_volume, boundary="WordBoundary"
            )
            chunk_audio = bytearray()
            max_s = 0.0
            async for ch in comm.stream():
                if ch.get("type") == "audio":
                    chunk_audio.extend(ch["data"])
                elif ch.get("type") == "WordBoundary":
                    s = float(ch["offset"]) / 10_000_000
                    dur = float(ch.get("duration") or 0) / 10_000_000
                    end = s + max(dur, 0.05)
                    max_s = max(max_s, end)
                    all_words.append(WordTiming(str(ch["text"]), current_offset + s, current_offset + end))
            master_fh.write(chunk_audio)
            current_offset += max_s + 0.12  # natural conversational pause between beats

    return all_words, media_duration(out_path)


async def list_edge_voices(language: str = "en") -> list[dict]:
    import edge_tts

    voices = await edge_tts.list_voices()
    return [v for v in voices if v.get("Locale", "").startswith(language)]


# ------------------------------------------------------------------ ElevenLabs
def _alignment_to_words(alignment: dict) -> list[WordTiming]:
    """Turn ElevenLabs character timestamps into word timings for the caption engine.

    Uses ``normalized_alignment`` when available (it matches the *spoken* text, so
    numbers like "3.8" line up with "three point eight"), otherwise the raw alignment.
    """
    if not alignment:
        return []
    chars = alignment.get("characters") or []
    starts = alignment.get("character_start_times_seconds") or []
    ends = alignment.get("character_end_times_seconds") or []
    if not chars or len(chars) != len(starts) or len(starts) != len(ends):
        return []

    words: list[WordTiming] = []
    current = ""
    word_start: float | None = None
    word_end: float = 0.0
    for ch, start, end in zip(chars, starts, ends):
        if ch.isspace():
            if current and word_start is not None:
                words.append(WordTiming(current, float(word_start), max(float(word_end), float(word_start))))
                current, word_start = "", None
            continue
        if word_start is None:
            word_start = float(start)
        current += ch
        word_end = float(end)
    if current and word_start is not None:
        words.append(WordTiming(current, float(word_start), max(float(word_end), float(word_start))))
    return words


async def _elevenlabs_tts(text: str, out_path: Path, voice: str, cfg: Config) -> tuple[list[WordTiming], float]:
    payload = {
        "text": text,
        "model_id": cfg.elevenlabs_model,
        "output_format": cfg.elevenlabs_output_format,
        "voice_settings": {
            "stability": cfg.elevenlabs_stability,
            "similarity_boost": cfg.elevenlabs_similarity,
            "style": cfg.elevenlabs_style,
            "use_speaker_boost": True,
        },
    }
    headers = {"xi-api-key": cfg.elevenlabs_api_key, "Content-Type": "application/json"}
    async with httpx.AsyncClient(timeout=httpx.Timeout(180.0)) as client:
        resp = await client.post(
            ELEVENLABS_TTS.format(voice_id=voice), json=payload, headers=headers
        )
        if resp.status_code == 401:
            raise RuntimeError("ElevenLabs rejected the API key (401). Check ELEVENLABS_API_KEY.")
        if resp.status_code == 402:
            raise RuntimeError("ElevenLabs credits exhausted (402). Check your plan/usage.")
        if resp.status_code == 429:
            raise RuntimeError("ElevenLabs rate limit / concurrency limit (429). Try again shortly.")
        if resp.status_code >= 400:
            raise RuntimeError(f"ElevenLabs HTTP {resp.status_code}: {resp.text[:240]}")

        data = resp.json()

    audio_b64 = data.get("audio_base64") or ""
    if not audio_b64:
        raise RuntimeError("ElevenLabs returned no audio")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(base64.b64decode(audio_b64))

    alignment = data.get("normalized_alignment") or data.get("alignment") or {}
    words = _alignment_to_words(alignment)
    return words, media_duration(out_path)


async def elevenlabs_voices(cfg: Config | None = None) -> list[dict]:
    """Your account's voices (needs a key)."""
    cfg = cfg or get_config()
    if not cfg.elevenlabs_api_key:
        return []
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(ELEVENLABS_VOICES_API, headers={"xi-api-key": cfg.elevenlabs_api_key})
        if resp.status_code >= 400:
            raise RuntimeError(f"ElevenLabs voices HTTP {resp.status_code}: {resp.text[:200]}")
        return resp.json().get("voices", [])


async def elevenlabs_usage(cfg: Config | None = None) -> dict:
    """Quota info from the account (character_count / character_limit)."""
    cfg = cfg or get_config()
    if not cfg.elevenlabs_api_key:
        return {}
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(
            f"{ELEVENLABS_BASE}/v1/user/subscription",
            headers={"xi-api-key": cfg.elevenlabs_api_key},
        )
        if resp.status_code >= 400:
            return {}
        data = resp.json()
        return {
            "tier": data.get("tier"),
            "character_count": data.get("character_count"),
            "character_limit": data.get("character_limit"),
            "can_extend_character_limit": data.get("can_extend_character_limit"),
        }


# ----------------------------------------------------------------- usage meter
def _month_key() -> str:
    return "voice_chars_" + datetime.now(timezone.utc).strftime("%Y-%m")


def month_usage() -> int:
    try:
        return int(db.get_setting(_month_key()) or 0)
    except ValueError:
        return 0


def _add_usage(characters: int, cfg: Config) -> None:
    try:
        total = month_usage() + max(0, int(characters))
        db.set_setting(_month_key(), total)
        limit = cfg.elevenlabs_char_limit
        if limit:
            pct = total / limit
            if total >= limit:
                log.warning("ElevenLabs quota for this month is spent (%d/%d chars)", total, limit)
            elif pct >= 0.8 and not db.get_bool_setting(f"warned_80_{_month_key()}"):
                db.set_setting(f"warned_80_{_month_key()}", "1")
                log.warning("ElevenLabs usage at %.0f%% of the monthly allowance (%d/%d chars)",
                            pct * 100, total, limit)
    except Exception as exc:  # noqa: BLE001 - metering must never break a render
        log.debug("usage meter failed: %s", exc)


# ------------------------------------------------------------------- public API
async def synthesize(
    text: str,
    out_path: Path,
    niche: str = "space",
    cfg: Config | None = None,
    voice: str | None = None,
    retries: int = 3,
    speed_hint: float | None = None,
) -> VoiceResult:
    """Generate the narration and return audio + word timings.

    ``speed_hint`` > 1 asks the engine to speak faster. The pipeline uses it when a
    long story narration overshoots the target duration - re-voicing a bit quicker
    keeps the whole script instead of cutting content.
    """
    cfg = cfg or get_config()
    provider = provider_for(cfg)
    requested_voice = voice or pick_voice(niche, cfg)
    out_path = Path(out_path)
    errors: list[str] = []

    # -------- free local engines (Kokoro / Piper), no key, no network --------
    if provider in LOCAL_ENGINES:
        speed = speed_hint if speed_hint else (cfg.kokoro_speed if provider == "kokoro" else 1.0)
        if provider == "piper" and cfg.piper_voice:
            requested_voice = cfg.piper_voice
        for attempt in range(1, retries + 1):
            try:
                result = await synthesize_local(text, out_path, provider, requested_voice, cfg, speed=speed)
                if result.duration <= 0.2 or result.path.stat().st_size < 4000:
                    raise RuntimeError(f"{provider} produced a suspicious file ({result.duration:.2f}s)")
                log.info(
                    "voiceover: %.2fs, provider=%s voice=%s (%.2f words/s, speed=%.2f, %d sentence anchors)",
                    result.duration, provider, requested_voice, result.words_per_second, speed, len(result.segments),
                )
                return VoiceResult(
                    path=result.path, duration=result.duration, words=[], voice=requested_voice,
                    provider=provider, characters=0, segments=result.segments, speed=speed,
                )
            except Exception as exc:  # noqa: BLE001 - fall through to edge / espeak
                errors.append(f"{provider}[{attempt}]: {exc}")
                log.warning("%s attempt %d/%d failed: %s", provider, attempt, retries, exc)
                await asyncio.sleep(1.0 * attempt)
        log.error("%s unavailable -> edge-tts (%s)", provider, errors[-1] if errors else "?")
        requested_voice = random.choice(VOICES.get(niche, DEFAULT_VOICES))

    if provider == "elevenlabs":
        if not cfg.elevenlabs_api_key:
            log.warning("VOICE_PROVIDER=elevenlabs but no ELEVENLABS_API_KEY -> falling back to edge-tts")
        else:
            if cfg.elevenlabs_voice_id or cfg.voice:
                requested_voice = voice or cfg.elevenlabs_voice_id or cfg.voice
            for attempt in range(1, retries + 1):
                try:
                    words, duration = await _elevenlabs_tts(text, out_path, requested_voice, cfg)
                    if duration <= 0.2 or out_path.stat().st_size < 4000:
                        raise RuntimeError(f"ElevenLabs produced a suspicious file ({duration:.2f}s)")
                    _add_usage(len(text), cfg)
                    name = elevenlabs_voice_name(requested_voice)
                    log.info("voiceover: %.2fs, %d word timings, provider=elevenlabs voice=%s (%d chars this month)",
                             duration, len(words), name, month_usage())
                    return VoiceResult(path=out_path, duration=duration, words=words,
                                       voice=f"elevenlabs:{name}", provider="elevenlabs",
                                       characters=len(text))
                except Exception as exc:  # noqa: BLE001
                    errors.append(f"elevenlabs[{attempt}]: {exc}")
                    log.warning("ElevenLabs attempt %d/%d failed: %s", attempt, retries, exc)
                    await asyncio.sleep(2 * attempt)
            log.error("ElevenLabs failed, falling back to edge-tts (%s)", errors[-1] if errors else "?")

    # -------- edge-tts (free, cloud, needs a network but no key) --------
    if provider in {"edge", "auto", "elevenlabs"} or errors:
        if provider in {"elevenlabs"} or provider in LOCAL_ENGINES:
            # ElevenLabs failed -> a rotating edge voice keeps the pipeline alive
            requested_voice = random.choice(VOICES.get(niche, DEFAULT_VOICES))
        for attempt in range(1, retries + 1):
            try:
                words, duration = await _edge_tts(text, out_path, requested_voice, cfg)
                if duration <= 0.2 or out_path.stat().st_size < 4000:
                    raise RuntimeError(f"edge-tts produced a suspicious file ({duration:.2f}s)")
                log.info("voiceover: %.2fs, %d word timings, provider=edge voice=%s",
                         duration, len(words), requested_voice)
                return VoiceResult(path=out_path, duration=duration, words=words,
                                   voice=requested_voice, provider="edge", characters=len(text))
            except Exception as exc:  # noqa: BLE001
                errors.append(f"edge[{attempt}]: {exc}")
                log.warning("edge-tts attempt %d/%d failed: %s", attempt, retries, exc)
                await asyncio.sleep(1.5 * attempt)

    # -------- espeak (offline last resort) --------
    log.error("all online TTS providers failed (%s) -> offline espeak", "; ".join(errors[-2:]))
    wav = out_path.with_suffix(".wav")
    duration = await asyncio.to_thread(_espeak_fallback, text, wav)
    return VoiceResult(path=wav.with_suffix(".mp3"), duration=duration, words=[],
                       voice="espeak-offline", provider="espeak", characters=len(text))


def local_voice_status(cfg: Config | None = None) -> str:
    """One-line report about the free local voice stack (used by /status)."""
    cfg = cfg or get_config()
    installed = available_engines()
    if not installed:
        return ("No local TTS installed - `pip install kokoro-onnx onnxruntime` (~325 MB model, best "
                "quality) or `pip install piper-tts` (~63 MB per voice, fastest).")
    from .tts_local import model_ready

    parts = []
    for engine in installed:
        voice = pick_local_voice(cfg.niche, engine, cfg)
        parts.append(f"{engine}({'model cached' if model_ready(engine, voice, cfg) else 'downloads on first run'})")
    return "Free local TTS: " + ", ".join(parts)


def _espeak_fallback(text: str, out_path: Path) -> float:
    if have_binary("espeak-ng"):
        cmd = ["espeak-ng", "-v", "en-us", "-s", "165", "-w", str(out_path)]
    elif have_binary("espeak"):
        cmd = ["espeak", "-v", "en-us", "-s", "165", "-w", str(out_path)]
    else:
        raise RuntimeError("no online TTS available and espeak-ng is not installed")
    run_cmd(cmd + [text], timeout=120)
    mp3 = out_path.with_suffix(".mp3")
    run_cmd(["ffmpeg", "-y", "-v", "error", "-i", str(out_path), "-c:a", "libmp3lame", "-q:a", "4", str(mp3)])
    return media_duration(mp3)


async def usage_report(cfg: Config | None = None) -> str:
    """Human readable voice-quota line for /status."""
    cfg = cfg or get_config()
    provider = provider_for(cfg)
    lines = [f"Voice provider: `{provider}` (VOICE_PROVIDER={cfg.voice_provider})"]
    if provider == "elevenlabs":
        local = month_usage()
        api = await elevenlabs_usage(cfg)
        if api:
            lines.append(
                f"ElevenLabs tier `{api.get('tier')}` · used "
                f"{api.get('character_count', '?')}/{api.get('character_limit', '?')} chars"
            )
        lines.append(f"This bot used {local} characters this month")
        if str(api.get("tier") or "").lower() in {"free", ""} and api:
            lines.append("⚠️ Free tier = non-commercial + attribution required. Monetized channel needs Starter+.")
    elif provider in LOCAL_ENGINES:
        lines.append(local_voice_status(cfg))
        lines.append("100% free and offline after the first download - no key, no quota, no attribution.")
    else:
        lines.append("edge-tts: free, unlimited, no attribution needed")
    return "\n".join(lines)
