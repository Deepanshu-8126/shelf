"""Free, open-source, fully local text-to-speech engines (no API keys, no billing).

Engines
-------
``kokoro`` - Kokoro-82M (Apache-2.0). ~325 MB ONNX model + 28 MB voice pack, 24 kHz,
             ~1.3x realtime on a CPU core, 54 voices. Best quality-per-byte of the
             free options and safe for monetised channels.
``piper``  - Piper (MIT). One small ONNX file per voice (~20-65 MB), fastest of the
             two, 22.05 kHz, very steady delivery.

Both run entirely offline after the first download, so a hosted bot does not need
any paid key anywhere in the voice path. Models are cached under ``TTS_MODEL_DIR``
(default ``cache/tts``) and downloaded on first use.

Why sentence-by-sentence?
-------------------------
Neither engine returns word-level timestamps (Kokoro's ``create_timed`` and Piper's
``include_alignments`` both come back empty on the standard exports). Synthesising
one sentence at a time gives us *exact* sentence boundaries, and those boundaries
are what the caption aligner uses as anchors; the rest comes from faster-whisper
(see ``factshorts/align.py``). It also keeps memory flat on long 60-second stories.
"""
from __future__ import annotations

import asyncio
import re
import wave
from dataclasses import dataclass, field
from pathlib import Path

import httpx

from .config import Config, get_config
from .utils import module_logger, run_cmd

log = module_logger("tts_local")


@dataclass(frozen=True)
class ModelFile:
    name: str
    urls: tuple[str, ...]
    min_bytes: int


# Mirrors are tried in order; the second one is a plain HTTPS mirror for hosts where
# GitHub release downloads are slow or blocked.
KOKORO_FILES: tuple[ModelFile, ...] = (
    ModelFile(
        "kokoro-v1.0.onnx",
        (
            "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx",
            "https://hf-mirror.com/hexgrad/Kokoro-82M/resolve/main/kokoro-v1.0.onnx",
        ),
        300_000_000,
    ),
    ModelFile(
        "voices-v1.0.bin",
        (
            "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin",
            "https://hf-mirror.com/hexgrad/Kokoro-82M/resolve/main/voices-v1.0.bin",
        ),
        20_000_000,
    ),
)

PIPER_BASE = "https://huggingface.co/rhasspy/piper-voices/resolve/main"

# voice name -> relative path under rhasspy/piper-voices (name:lang-region-speaker-quality)
PIPER_VOICES: dict[str, tuple[str, int]] = {
    "en_US-lessac-medium": ("en/en_US/lessac/medium/en_US-lessac-medium", 55_000_000),
    "en_US-amy-medium": ("en/en_US/amy/medium/en_US-amy-medium", 55_000_000),
    "en_US-ryan-high": ("en/en_US/ryan/high/en_US-ryan-high", 100_000_000),
    "en_GB-alan-medium": ("en/en_GB/alan/medium/en_GB-alan-medium", 55_000_000),
    "en_GB-jenny_dioco-medium": ("en/en_GB/jenny_dioco/medium/en_GB-jenny_dioco-medium", 55_000_000),
}
DEFAULT_PIPER_VOICE = "en_US-lessac-medium"

# Kokoro voice ids often used for narration (any of the 54 in voices-v1.0.bin works).
KOKORO_VOICES = {
    "space": ["am_michael", "bm_george", "am_adam"],
    "psychology": ["af_heart", "af_bella", "bf_emma"],
    "history": ["bm_george", "am_michael", "bm_lewis"],
    "science": ["af_bella", "af_nicole", "bf_isabella"],
    "animals": ["af_nova", "af_sarah", "bf_alice"],
}
DEFAULT_KOKORO_VOICES = ["af_heart", "am_michael", "af_bella"]


# --------------------------------------------------------------------- helpers
def model_dir(cfg: Config | None = None) -> Path:
    cfg = cfg or get_config()
    path = Path(cfg.tts_model_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def split_sentences(text: str, max_chars: int = 220) -> list[str]:
    """Split narration into TTS-sized sentences.

    Short fragments are glued to the previous sentence so the model never has to
    voice a two-word line in isolation (that is where prosody gets choppy).
    """
    parts = [p.strip() for p in re.split(r"(?<=[.!?])\s+", (text or "").strip()) if p.strip()]
    if not parts:
        return []
    out: list[str] = []
    absorbed = False
    for part in parts:
        # a two-word sentence voiced alone sounds choppy - glue it to the previous one,
        # but never cascade (otherwise a run of short lines collapses into one blob)
        if out and not absorbed and len(part) <= 8 and len(part.split()) <= 2:
            out[-1] = f"{out[-1]} {part}"
            absorbed = True
        else:
            out.append(part)
            absorbed = False
    # very long sentences: split on the last comma before the limit
    final: list[str] = []
    for sent in out:
        while len(sent) > max_chars:
            cut = sent.rfind(",", 0, max_chars)
            if cut < max_chars * 0.4:
                cut = sent.rfind(" ", 0, max_chars)
            if cut <= 0:
                break
            final.append(sent[:cut].strip())
            sent = sent[cut + 1:].strip() if sent[cut] == "," else sent[cut:].strip()
        if sent:
            final.append(sent)
    return final


def _write_wav(path: Path, samples, sample_rate: int) -> None:
    """Write 16-bit PCM mono WAV without needing soundfile installed."""
    import numpy as np

    data = np.asarray(samples, dtype="float32")
    if data.ndim > 1:
        data = data.mean(axis=1)
    peak = float(abs(data).max()) if data.size else 0.0
    if peak > 1.0:                      # Kokoro can overshoot slightly on loud voices
        data = data / peak
    pcm = (np.clip(data, -1.0, 1.0) * 32767.0).astype("<i2")
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as fh:
        fh.setnchannels(1)
        fh.setsampwidth(2)
        fh.setframerate(int(sample_rate))
        fh.writeframes(pcm.tobytes())


def _silence(sample_rate: int, seconds: float):
    import numpy as np

    return np.zeros(max(1, int(sample_rate * seconds)), dtype="float32")


def _resample(samples, src_rate: int, dst_rate: int):
    """Linear resample (good enough for speech; avoids a scipy/librosa dependency)."""
    if src_rate == dst_rate or len(samples) == 0:
        return samples, src_rate
    import numpy as np

    src = np.asarray(samples, dtype="float32")
    dst_len = int(round(len(src) * dst_rate / src_rate))
    if dst_len <= 1:
        return src, src_rate
    x_old = np.linspace(0.0, 1.0, num=len(src), endpoint=False)
    x_new = np.linspace(0.0, 1.0, num=dst_len, endpoint=False)
    return np.interp(x_new, x_old, src).astype("float32"), dst_rate


# ------------------------------------------------------------------- downloads
def _local_file(name: str, cfg: Config) -> Path:
    return model_dir(cfg) / name


def model_ready(engine: str, voice: str, cfg: Config | None = None) -> bool:
    cfg = cfg or get_config()
    if engine == "kokoro":
        return all(_local_file(f.name, cfg).is_file() and _local_file(f.name, cfg).stat().st_size > f.min_bytes
                   for f in KOKORO_FILES)
    if engine == "piper":
        rel, min_bytes = PIPER_VOICES.get(voice, PIPER_VOICES[DEFAULT_PIPER_VOICE])
        stem = Path(rel).name
        model = _local_file(f"{stem}.onnx", cfg)
        conf = _local_file(f"{stem}.onnx.json", cfg)
        return (model.is_file() and model.stat().st_size > min_bytes * 0.5
                and conf.is_file() and conf.stat().st_size > 500)
    return False


async def _download(url: str, dest: Path, min_bytes: int, timeout: float = 900.0) -> None:
    tmp = dest.with_suffix(dest.suffix + ".part")
    tmp.parent.mkdir(parents=True, exist_ok=True)
    log.info("downloading %s -> %s", url, dest.name)
    async with httpx.AsyncClient(follow_redirects=True, timeout=httpx.Timeout(timeout)) as client:
        async with client.stream("GET", url) as resp:
            if resp.status_code >= 400:
                raise RuntimeError(f"HTTP {resp.status_code} for {url}")
            total = int(resp.headers.get("content-length") or 0)
            done = 0
            with open(tmp, "wb") as fh:
                async for chunk in resp.aiter_bytes(1 << 20):
                    fh.write(chunk)
                    done += len(chunk)
                    if total and done % (25 << 20) < (1 << 20):
                        log.info("  %s %d%% (%d MB)", dest.name, int(done * 100 / total), done >> 20)
    size = tmp.stat().st_size
    if size < min_bytes:
        tmp.unlink(missing_ok=True)
        raise RuntimeError(f"{dest.name} looks truncated ({size} bytes < {min_bytes})")
    tmp.replace(dest)
    log.info("saved %s (%.1f MB)", dest.name, size / 1e6)


async def ensure_models(engine: str, voice: str, cfg: Config | None = None) -> None:
    """Download whatever is missing for this engine/voice. Safe to call every run."""
    cfg = cfg or get_config()
    if model_ready(engine, voice, cfg):
        return
    if engine == "kokoro":
        for spec in KOKORO_FILES:
            target = _local_file(spec.name, cfg)
            if target.is_file() and target.stat().st_size > spec.min_bytes:
                continue
            errors: list[str] = []
            urls = (cfg.tts_kokoro_model_url,) if (spec.name.endswith(".onnx") and cfg.tts_kokoro_model_url) else spec.urls
            for url in urls:
                try:
                    await _download(url, target, spec.min_bytes)
                    break
                except Exception as exc:  # noqa: BLE001 - try the next mirror
                    errors.append(f"{url}: {exc}")
                    log.warning("download failed (%s), trying next mirror", exc)
            else:
                raise RuntimeError(
                    "could not download the Kokoro model files. Tried:\n  " + "\n  ".join(errors)
                    + "\nSet TTS_MODEL_DIR to a folder that already has kokoro-v1.0.onnx + voices-v1.0.bin,"
                      " or use VOICE_PROVIDER=piper (much smaller download)."
                )
    elif engine == "piper":
        rel, min_bytes = PIPER_VOICES.get(voice, PIPER_VOICES[DEFAULT_PIPER_VOICE])
        stem = Path(rel).name
        model = _local_file(f"{stem}.onnx", cfg)
        conf = _local_file(f"{stem}.onnx.json", cfg)
        base = cfg.tts_piper_base_url or PIPER_BASE
        if not (model.is_file() and model.stat().st_size > min_bytes * 0.5):
            await _download(f"{base}/{rel}.onnx", model, min_bytes // 2)
        if not (conf.is_file() and conf.stat().st_size > 500):
            await _download(f"{base}/{rel}.onnx.json", conf, 200)


# ------------------------------------------------------------------ synthesis
@dataclass
class LocalTtsResult:
    path: Path
    duration: float
    sample_rate: int
    voice: str
    engine: str
    segments: list[tuple[str, float, float]] = field(default_factory=list)  # (text, start, dur)
    speed: float = 1.0
    words_per_second: float = 0.0


def _synth_kokoro(sentences: list[str], voice: str, speed: float, cfg: Config) -> tuple[list, int]:
    from kokoro_onnx import Kokoro  # type: ignore

    model = _local_file(KOKORO_FILES[0].name, cfg)
    voices = _local_file(KOKORO_FILES[1].name, cfg)
    engine = Kokoro(str(model), str(voices))
    chunks: list = []
    rate = 24000
    for sentence in sentences:
        audio, rate = engine.create(sentence, voice=voice, speed=speed)
        chunks.append(audio)
    return chunks, int(rate)


def _synth_piper(sentences: list[str], voice: str, speed: float, cfg: Config) -> tuple[list, int]:
    import numpy as np
    from piper import PiperVoice  # type: ignore

    rel, _ = PIPER_VOICES.get(voice, PIPER_VOICES[DEFAULT_PIPER_VOICE])
    stem = Path(rel).name
    engine = PiperVoice.load(str(_local_file(f"{stem}.onnx", cfg)))
    length_scale = max(0.5, min(2.0, 1.0 / max(0.5, speed)))
    chunks: list = []
    rate = 22050
    for sentence in sentences:
        try:
            from piper import SynthesisConfig  # type: ignore

            syn = SynthesisConfig(length_scale=length_scale, normalize_audio=True)
            stream = engine.synthesize(sentence, syn_config=syn)
        except Exception:  # noqa: BLE001 - older piper builds
            stream = engine.synthesize(sentence) if hasattr(engine, "synthesize") else engine.synthesize_stream_raw(sentence)
        for chunk in stream:
            raw = getattr(chunk, "audio_int16_bytes", None)
            if raw is not None:
                rate = int(getattr(chunk, "sample_rate", rate) or rate)
                chunks.append(np.frombuffer(raw, dtype="<i2").astype("float32") / 32768.0)
            elif isinstance(chunk, (bytes, bytearray)):
                chunks.append(np.frombuffer(chunk, dtype="<i2").astype("float32") / 32768.0)
    return chunks, int(rate)


def _synthesize_blocking(
    text: str, out_wav: Path, engine: str, voice: str, speed: float, cfg: Config
) -> LocalTtsResult:
    import numpy as np

    sentences = split_sentences(text)
    if not sentences:
        raise RuntimeError("nothing to speak")

    if engine == "kokoro":
        chunks, rate = _synth_kokoro(sentences, voice, speed, cfg)
    elif engine == "piper":
        chunks, rate = _synth_piper(sentences, voice, speed, cfg)
    else:
        raise RuntimeError(f"unknown local TTS engine {engine!r}")

    lead_in = max(0.0, cfg.tts_lead_in)
    pause = max(0.0, cfg.tts_sentence_pause)
    tail = max(0.0, cfg.tts_tail)

    pieces: list = [_silence(rate, lead_in)]
    segments: list[tuple[str, float, float]] = []
    t = lead_in
    for i, (sentence, audio) in enumerate(zip(sentences, chunks)):
        if audio is None or len(audio) == 0:
            continue
        dur = len(audio) / rate
        pieces.append(audio)
        segments.append((sentence, round(t, 3), round(dur, 3)))
        t += dur
        gap = pause if i < len(chunks) - 1 else tail
        pieces.append(_silence(rate, gap))
        t += gap

    samples = np.concatenate(pieces) if pieces else np.zeros(1, dtype="float32")
    out_rate = int(cfg.tts_sample_rate or 0)
    if out_rate and out_rate != rate:
        samples, rate = _resample(samples, rate, out_rate)
    _write_wav(out_wav, samples, rate)
    duration = len(samples) / rate
    spoken_words = len(re.findall(r"\S+", text))
    return LocalTtsResult(
        path=out_wav,
        duration=duration,
        sample_rate=rate,
        voice=voice,
        engine=engine,
        segments=segments,
        speed=speed,
        words_per_second=spoken_words / duration if duration else 0.0,
    )


def _payload(text: str, out_path: Path, engine: str, voice: str, cfg: Config, speed: float) -> dict:
    return {
        "text": text, "out_path": str(out_path), "engine": engine, "voice": voice,
        "speed": speed, "sample_rate": cfg.tts_sample_rate, "sentence_pause": cfg.tts_sentence_pause,
        "lead_in": cfg.tts_lead_in, "tail": cfg.tts_tail, "model_dir": str(cfg.tts_model_dir),
        "mp3_quality": cfg.voice_mp3_quality,
    }


def _run_isolated(payload: dict) -> dict:
    """Run one synthesis in a child process (module __main__) and return the result as JSON."""
    import json
    import subprocess
    import sys

    proc = subprocess.run(
        [sys.executable, "-m", "factshorts.tts_local", "--worker"],
        input=json.dumps(payload), capture_output=True, text=True, timeout=1800,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"local TTS worker failed: {(proc.stderr or proc.stdout)[-400:]}")
    line = [ln for ln in proc.stdout.splitlines() if ln.startswith("{")]
    if not line:
        raise RuntimeError(f"local TTS worker produced no result: {proc.stdout[-300:]}")
    return json.loads(line[-1])


async def synthesize_local(
    text: str,
    out_path: Path,
    engine: str,
    voice: str,
    cfg: Config | None = None,
    speed: float = 1.0,
    isolate: bool | None = None,
) -> LocalTtsResult:
    """Render `text` with a local engine and mux the WAV to mp3 at `out_path`."""
    cfg = cfg or get_config()
    await ensure_models(engine, voice, cfg)
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    isolate = cfg.tts_isolate if isolate is None else isolate
    if isolate:
        data = await asyncio.to_thread(_run_isolated, _payload(text, out_path, engine, voice, cfg, speed))
        wav = Path(data["wav_path"])
        mp3 = Path(data["path"])
        return LocalTtsResult(
            path=mp3, duration=float(data["duration"]), sample_rate=int(data["sample_rate"]),
            voice=voice, engine=engine, segments=[tuple(x) for x in data["segments"]],
            speed=speed, words_per_second=float(data["words_per_second"]),
        )
    wav = out_path.with_suffix(".wav")
    result = await asyncio.to_thread(_synthesize_blocking, text, wav, engine, voice, speed, cfg)
    mp3 = out_path.with_suffix(".mp3")
    await asyncio.to_thread(
        run_cmd,
        ["ffmpeg", "-y", "-v", "error", "-i", str(wav), "-c:a", "libmp3lame",
         "-q:a", str(cfg.voice_mp3_quality), "-ar", "44100", str(mp3)],
        300,
    )
    result.path = mp3
    log.info(
        "%s voice done: %.2fs audio, %d sentences, %.2f words/s, speed=%.2f, voice=%s",
        engine, result.duration, len(result.segments), result.words_per_second, speed, voice,
    )
    return result


def pick_local_voice(niche: str, engine: str, cfg: Config | None = None) -> str:
    cfg = cfg or get_config()
    import random

    if cfg.voice:
        return cfg.voice
    if engine == "kokoro":
        return random.choice(KOKORO_VOICES.get(niche, DEFAULT_KOKORO_VOICES))
    return cfg.piper_voice or DEFAULT_PIPER_VOICE


def available_engines() -> list[str]:
    """Which engines can actually run in this environment."""
    import importlib.util

    out: list[str] = []
    if importlib.util.find_spec("kokoro_onnx"):
        out.append("kokoro")
    if importlib.util.find_spec("piper"):
        out.append("piper")
    return out


# ------------------------------------------------------------------- worker CLI
def _worker_main() -> int:
    """`python -m factshorts.tts_local --worker` - reads one JSON job on stdin.

    Isolating the engine keeps peak memory low on small hosts: onnxruntime does not
    hand the Kokoro weights back to the OS, and faster-whisper + ffmpeg still have to
    run afterwards in the parent process.
    """
    import json
    import sys

    from .config import Config

    payload = json.loads(sys.stdin.read() or "{}")
    cfg = Config()
    cfg.tts_sample_rate = int(payload.get("sample_rate") or 0)
    cfg.tts_sentence_pause = float(payload.get("sentence_pause", cfg.tts_sentence_pause))
    cfg.tts_lead_in = float(payload.get("lead_in", cfg.tts_lead_in))
    cfg.tts_tail = float(payload.get("tail", cfg.tts_tail))
    cfg.voice_mp3_quality = int(payload.get("mp3_quality", cfg.voice_mp3_quality))
    if payload.get("model_dir"):
        cfg.tts_model_dir = Path(payload["model_dir"])

    text = str(payload.get("text") or "")
    engine = str(payload.get("engine") or "kokoro")
    voice = str(payload.get("voice") or "")
    speed = float(payload.get("speed") or 1.0)
    out_path = Path(str(payload.get("out_path")))
    wav = out_path.with_suffix(".wav")

    result = _synthesize_blocking(text, wav, engine, voice, speed, cfg)
    mp3 = out_path.with_suffix(".mp3")
    run_cmd(["ffmpeg", "-y", "-v", "error", "-i", str(wav), "-c:a", "libmp3lame",
             "-q:a", str(cfg.voice_mp3_quality), "-ar", "44100", str(mp3)], 300)
    print(json.dumps({
        "path": str(mp3), "wav_path": str(wav), "duration": result.duration,
        "sample_rate": result.sample_rate, "segments": result.segments,
        "words_per_second": result.words_per_second,
    }))
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    import sys as _sys

    if "--worker" in _sys.argv:
        raise SystemExit(_worker_main())
    print(__doc__ or "factshorts.tts_local")
