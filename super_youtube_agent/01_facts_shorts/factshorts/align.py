"""Word-level timing for captions when the voice does not provide timestamps.

Local engines (Kokoro, Piper) return no word boundaries, so captions need a timing
source. Two are implemented here, in order of accuracy:

1. ``whisper_words`` - run faster-whisper (free, MIT, fully local) over the generated
   narration and align its word timestamps onto the *script* words. ~20x realtime on a
   CPU for tiny.en, so a 60-second story costs ~3 seconds. This is the default for
   local voices.
2. ``estimate_words`` - no extra dependency. Sentence-level anchors are exact (we
   synthesise sentence by sentence, so we know where each one starts), and inside a
   sentence the duration is shared out by syllable weight with punctuation pauses.
   Measured against real word boundaries this lands within ~150-250 ms, which is fine
   for 3-word caption pages but clearly step two.

Both paths produce ``WordTiming``-compatible tuples so ``captions.py`` stays simple.
"""
from __future__ import annotations

import re
import subprocess
import difflib
from pathlib import Path

from .config import Config, get_config
from .utils import module_logger, have_binary

log = module_logger("align")

VOWELS = "aeiouy"
# Extra silence that a punctuation mark adds *after* the word it is attached to.
PAUSE_AFTER = {",": 0.16, ";": 0.20, ":": 0.18, ".": 0.30, "!": 0.30, "?": 0.30, "\u2014": 0.22, "-": 0.08}
ACRONYM_RE = re.compile(r"^[A-Z0-9]{2,}$")


def syllables(word: str) -> int:
    w = re.sub(r"[^a-z]", "", (word or "").lower())
    if not w:
        return 1
    count = len(re.findall(r"[aeiouy]+", w))
    if w.endswith("e") and count > 1 and not w.endswith(("le", "ee", "ye")):
        count -= 1
    return max(1, count)


def _weight(token: str) -> tuple[int, float]:
    core = token.strip('.,;:!?"\u201c\u201d()[]')
    weight = syllables(core)
    if core.isdigit():
        weight = max(1, len(core) // 2)       # "1907" is spoken digit by digit
    elif ACRONYM_RE.match(core):
        weight = len(core)                    # NASA, DNA
    pause = sum(PAUSE_AFTER.get(ch, 0) for ch in token if ch in PAUSE_AFTER)
    return weight, pause


def estimate_span(text: str, duration: float) -> list[tuple[str, float, float]]:
    """Word timings for one utterance of known duration, relative to its start."""
    tokens = re.findall(r"\S+", text or "")
    if not tokens or duration <= 0:
        return []
    weighted = [(tok,) + _weight(tok) for tok in tokens]
    pause_total = sum(w[2] for w in weighted)
    speech = max(0.05, duration - pause_total)
    total_weight = sum(w[1] for w in weighted) or 1
    out: list[tuple[str, float, float]] = []
    t = 0.0
    for token, weight, pause in weighted:
        span = speech * weight / total_weight
        out.append((token, t, t + span))
        t += span + pause
    return out


def estimate_words(segments: list[tuple[str, float, float]]) -> list[tuple[str, float, float]]:
    """Absolute word timings from ``(sentence, start, duration)`` anchors."""
    out: list[tuple[str, float, float]] = []
    for text, start, duration in segments or []:
        for token, s, e in estimate_span(text, duration):
            out.append((token, start + s, start + e))
    return out


def proportional_words(text: str, duration: float) -> list[tuple[str, float, float]]:
    """Last resort: spread the words evenly (used when nothing else is available)."""
    tokens = re.findall(r"\S+", text or "")
    if not tokens:
        return []
    per = max(0.05, duration / len(tokens))
    return [(tok, i * per, (i + 1) * per) for i, tok in enumerate(tokens)]


# ------------------------------------------------------------------- whisper
def _decode_to_float32(audio_path: str | Path, cfg: Config):
    """Decode any audio file to 16 kHz mono float32 using ffmpeg.

    faster-whisper's own loader goes through PyAV, and a version mismatch there raises
    ``TypeError: open() got an unexpected keyword argument 'metadata_errors'``. Feeding
    it a numpy array sidesteps PyAV entirely.
    """
    import numpy as np
    import wave

    src = Path(audio_path)
    tmp = src.with_name(src.stem + ".asr16.wav")
    cmd = ["ffmpeg", "-y", "-v", "error", "-i", str(src), "-ac", "1", "-ar", "16000",
           "-f", "wav", str(tmp)]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg could not decode {src.name}: {proc.stderr[:200]}")
    with wave.open(str(tmp), "rb") as fh:
        frames = fh.readframes(fh.getnframes())
    try:
        tmp.unlink()
    except OSError:
        pass
    return np.frombuffer(frames, dtype="<i2").astype("float32") / 32768.0


_WHISPER_CACHE: dict[tuple[str, str, str], object] = {}


def load_whisper(cfg: Config):
    """Cached WhisperModel per (model, device, compute_type) - loading costs seconds."""
    key = (cfg.whisper_model, cfg.whisper_device, cfg.whisper_compute_type)
    model = _WHISPER_CACHE.get(key)
    if model is None:
        from faster_whisper import WhisperModel  # type: ignore

        log.info("loading whisper model %s (%s/%s)", cfg.whisper_model, cfg.whisper_device, cfg.whisper_compute_type)
        model = WhisperModel(cfg.whisper_model, device=cfg.whisper_device, compute_type=cfg.whisper_compute_type)
        _WHISPER_CACHE[key] = model
    return model


def release_whisper() -> None:
    """Free the model between renders (small hosts)."""
    _WHISPER_CACHE.clear()


def whisper_words(audio_path: str | Path, text: str = "", cfg: Config | None = None) -> list[tuple[str, float, float]]:
    """Word timings via faster-whisper, with the model's obvious lapses patched up."""
    cfg = cfg or get_config()
    if not have_binary("ffmpeg"):
        raise RuntimeError("ffmpeg is required to decode audio for whisper")

    audio = _decode_to_float32(audio_path, cfg)
    if audio.size == 0:
        raise RuntimeError("decoded audio is empty")

    model = load_whisper(cfg)
    segments, _info = model.transcribe(
        audio, language="en", word_timestamps=True, vad_filter=False, beam_size=1
    )
    heard: list[tuple[str, float, float]] = []
    for seg in segments:
        for word in seg.words or []:
            token = (word.word or "").strip()
            if token:
                heard.append((token, float(word.start), float(word.end)))
    if not heard:
        raise RuntimeError("whisper returned no words")
    log.info("whisper heard %d words", len(heard))

    snapped = snap_to_script(heard, text) if text else heard
    if snapped:
        return snapped
    return heard


def _norm(token: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (token or "").lower())


def snap_to_script(
    heard: list[tuple[str, float, float]], text: str
) -> list[tuple[str, float, float]]:
    """Give every script word the timing of the word whisper actually heard.

    Whisper sometimes writes "peroxide." as "peroxide", splits "three thousand" into
    "three" + "thousand", or drops a repeated article. Captions must still show the
    exact script text, so we align the two token streams (difflib) and copy timings
    across; unmatched script words are interpolated between their neighbours.
    """
    script = re.findall(r"\S+", text or "")
    if not script or not heard:
        return []
    a = [_norm(t) for t in script]
    b = [_norm(t[0]) for t in heard]
    matcher = difflib.SequenceMatcher(a=a, b=b, autojunk=False)

    starts: list[float | None] = [None] * len(script)
    ends: list[float | None] = [None] * len(script)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            for k in range(i2 - i1):
                starts[i1 + k] = heard[j1 + k][1]
                ends[i1 + k] = heard[j1 + k][2]
        elif tag == "replace" and (i2 - i1) == (j2 - j1):
            for k in range(i2 - i1):
                starts[i1 + k] = heard[j1 + k][1]
                ends[i1 + k] = heard[j1 + k][2]
        elif tag == "replace" and (i2 - i1) > 0 and (j2 - j1) > 0:
            # different lengths (e.g. "12,000" vs "twelve thousand"): share the window
            window_start = heard[j1][1]
            window_end = heard[j2 - 1][2]
            share = (window_end - window_start) / max(1, i2 - i1)
            for k in range(i2 - i1):
                starts[i1 + k] = window_start + k * share
                ends[i1 + k] = starts[i1 + k] + share

    # interpolate anything whisper missed entirely
    known = [i for i, s in enumerate(starts) if s is not None]
    if not known:
        return []
    for i in range(len(script)):
        if starts[i] is not None:
            continue
        prev = next((j for j in reversed(known) if j < i), None)
        nxt = next((j for j in known if j > i), None)
        if prev is not None and nxt is not None:
            gap_start = float(ends[prev] or starts[prev] or 0.0)
            gap_end = float(starts[nxt] or gap_start + 0.2)
            span = max(0.05, gap_end - gap_start) / (nxt - prev)
            starts[i] = gap_start + (i - prev - 1) * span
            ends[i] = starts[i] + span
        elif prev is not None:
            starts[i] = float(ends[prev] or starts[prev] or 0.0)
            ends[i] = starts[i] + 0.18
        else:
            edge = float(ends[known[0]] or starts[known[0]] or 0.0)
            starts[i] = max(0.0, float(starts[known[0]] or 0.0) - 0.18 * (known[0] - i))
            ends[i] = starts[i] + 0.18 if i < known[0] else edge

    out: list[tuple[str, float, float]] = []
    for token, start, end in zip(script, starts, ends):
        s = max(0.0, float(start or 0.0))
        e = max(s + 0.04, float(end or s + 0.12))
        if out and s < out[-1][2] - 0.15:      # keep timings monotonic
            s = out[-1][2]
            e = max(s + 0.04, e)
        out.append((token, s, e))
    return out


def check_accuracy(estimated: list[tuple[str, float, float]],
                   truth: list[tuple[str, float, float]]) -> tuple[float, float, int]:
    """Mean/max absolute start-time error (seconds) between two timing lists."""
    n = min(len(estimated), len(truth))
    if not n:
        return 0.0, 0.0, 0
    errs = [abs(estimated[i][1] - truth[i][1]) for i in range(n)]
    return sum(errs) / n, max(errs), n
