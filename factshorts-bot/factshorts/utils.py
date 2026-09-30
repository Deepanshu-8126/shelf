"""Shared helpers: logging, subprocess/ffmpeg wrappers, ffprobe, retries, text utils."""
from __future__ import annotations

import asyncio
import functools
import json
import logging
import logging.handlers
import os
import random
import re
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any, Awaitable, Callable, Iterable, Sequence

from .config import get_config

log = logging.getLogger("factshorts")


# --------------------------------------------------------------------- logging
def setup_logging(level: str | None = None) -> logging.Logger:
    cfg = get_config()
    lvl = getattr(logging, (level or cfg.log_level).upper(), logging.INFO)
    root = logging.getLogger("factshorts")
    if root.handlers:  # already configured
        return root
    root.setLevel(lvl)
    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-7s | %(name)-22s | %(message)s", "%Y-%m-%d %H:%M:%S"
    )

    console = logging.StreamHandler()
    console.setFormatter(fmt)
    root.addHandler(console)

    try:
        cfg.log_dir.mkdir(parents=True, exist_ok=True)
        fh = logging.handlers.RotatingFileHandler(
            cfg.log_dir / "factshorts.log", maxBytes=2_000_000, backupCount=3, encoding="utf-8"
        )
        fh.setFormatter(fmt)
        root.addHandler(fh)
    except Exception as exc:  # pragma: no cover - logging must never break the app
        root.warning("file logging disabled: %s", exc)

    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("apscheduler").setLevel(logging.WARNING)
    logging.getLogger("telegram").setLevel(logging.WARNING)
    return root


def module_logger(name: str) -> logging.Logger:
    return logging.getLogger(f"factshorts.{name}")


# ------------------------------------------------------------------ subprocess
class CommandError(RuntimeError):
    def __init__(self, cmd: Sequence[str], code: int, stderr: str):
        self.cmd = list(cmd)
        self.code = code
        self.stderr = stderr
        super().__init__(f"command failed ({code}): {' '.join(str(c) for c in cmd[:6])}...\n{stderr[-1500:]}")


def run_cmd(cmd: Sequence[str], timeout: int = 600, check: bool = True) -> subprocess.CompletedProcess:
    """Run a blocking subprocess (used for short ffprobe/ffmpeg helper calls)."""
    t0 = time.time()
    proc = subprocess.run(
        [str(c) for c in cmd], capture_output=True, text=True, timeout=timeout, errors="replace"
    )
    log.debug("cmd %.1fs: %s", time.time() - t0, " ".join(str(c) for c in cmd[:8]))
    if check and proc.returncode != 0:
        raise CommandError(cmd, proc.returncode, proc.stderr or proc.stdout or "")
    return proc


async def run_cmd_async(
    cmd: Sequence[str],
    timeout: int = 900,
    check: bool = True,
    cwd: str | Path | None = None,
) -> tuple[int, str, str]:
    """Run ffmpeg/ffprobe without blocking the event loop."""
    proc = await asyncio.create_subprocess_exec(
        *[str(c) for c in cmd],
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=str(cwd) if cwd else None,
    )
    try:
        out, err = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        proc.kill()
        raise CommandError(cmd, -1, f"timeout after {timeout}s")
    stdout = out.decode("utf-8", "replace")
    stderr = err.decode("utf-8", "replace")
    if check and proc.returncode != 0:
        raise CommandError(cmd, proc.returncode or -1, stderr)
    return proc.returncode or 0, stdout, stderr


def _ensure_ffmpeg_path() -> None:
    if shutil.which("ffmpeg") and shutil.which("ffprobe"):
        return
    local_app_data = os.getenv("LOCALAPPDATA")
    if local_app_data:
        winget_pkgs = Path(local_app_data) / "Microsoft" / "WinGet" / "Packages"
        if winget_pkgs.is_dir():
            for p in winget_pkgs.glob("**/ffmpeg.exe"):
                bin_dir = str(p.parent)
                if bin_dir not in os.environ.get("PATH", ""):
                    os.environ["PATH"] = bin_dir + os.pathsep + os.environ.get("PATH", "")
                break

_ensure_ffmpeg_path()


def have_binary(name: str) -> bool:
    _ensure_ffmpeg_path()
    return shutil.which(name) is not None


def ffprobe_json(path: str | Path) -> dict[str, Any]:
    proc = run_cmd(
        ["ffprobe", "-v", "error", "-print_format", "json", "-show_format", "-show_streams", str(path)],
        timeout=120,
        check=False,
    )
    if proc.returncode != 0 or not proc.stdout.strip():
        return {}
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError:
        return {}


def media_duration(path: str | Path) -> float:
    info = ffprobe_json(path)
    try:
        return float(info.get("format", {}).get("duration") or 0.0)
    except (TypeError, ValueError):
        return 0.0


def video_size(path: str | Path) -> tuple[int, int]:
    info = ffprobe_json(path)
    for stream in info.get("streams", []):
        if stream.get("codec_type") == "video":
            return int(stream.get("width") or 0), int(stream.get("height") or 0)
    return 0, 0


def has_audio_stream(path: str | Path) -> bool:
    info = ffprobe_json(path)
    return any(s.get("codec_type") == "audio" for s in info.get("streams", []))


# ---------------------------------------------------------------------- retries
async def retry_async(
    fn: Callable[[], Awaitable[Any]],
    attempts: int = 3,
    base_delay: float = 2.0,
    label: str = "task",
    exceptions: tuple[type[BaseException], ...] = (Exception,),
) -> Any:
    last: BaseException | None = None
    for i in range(1, attempts + 1):
        try:
            return await fn()
        except exceptions as exc:  # noqa: PERF203
            last = exc
            if i == attempts:
                break
            delay = base_delay * (2 ** (i - 1)) + random.uniform(0, 0.5)
            log.warning("%s failed (attempt %d/%d): %s -> retry in %.1fs", label, i, attempts, exc, delay)
            await asyncio.sleep(delay)
    assert last is not None
    raise last


def retry_sync(
    attempts: int = 3,
    base_delay: float = 2.0,
    label: str = "task",
    exceptions: tuple[type[BaseException], ...] = (Exception,),
):
    def deco(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            last = None
            for i in range(1, attempts + 1):
                try:
                    return fn(*args, **kwargs)
                except exceptions as exc:  # noqa: PERF203
                    last = exc
                    if i == attempts:
                        break
                    delay = base_delay * (2 ** (i - 1)) + random.uniform(0, 0.5)
                    log.warning("%s failed (attempt %d/%d): %s", label, i, attempts, exc)
                    time.sleep(delay)
            raise last  # type: ignore[misc]

        return wrapper

    return deco


# ------------------------------------------------------------------------ text
_SLUG_RE = re.compile(r"[^a-z0-9]+")
_WORD_RE = re.compile(r"[a-z0-9']+")
STOPWORDS = {
    "the", "a", "an", "of", "to", "and", "in", "is", "it", "that", "this", "for", "on", "with",
    "as", "at", "by", "from", "are", "was", "were", "be", "been", "you", "your", "we", "our",
    "their", "they", "its", "has", "have", "had", "but", "not", "no", "so", "if", "or", "than",
    "then", "when", "while", "into", "about", "over", "more", "most", "can", "will", "just",
}


def slugify(text: str, max_len: int = 60) -> str:
    s = _SLUG_RE.sub("-", (text or "").lower()).strip("-")
    return s[:max_len].strip("-") or "clip"


def words_of(text: str) -> list[str]:
    return _WORD_RE.findall((text or "").lower())


def content_tokens(text: str) -> set[str]:
    return {w for w in words_of(text) if w not in STOPWORDS and len(w) > 2}


def jaccard(a: Iterable[str], b: Iterable[str]) -> float:
    sa, sb = set(a), set(b)
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def is_similar(text_a: str, text_b: str, threshold: float = 0.55) -> bool:
    """Cheap near-duplicate check for short texts.

    Word overlap alone misses synonym swaps ("Venus spins backwards" vs "Venus rotates
    backwards"), so we also compare the raw strings character-wise and take the better
    score. Over-rejecting a topic only costs one extra LLM call, under-rejecting means
    posting a video the channel already published - so we lean strict.
    """
    from difflib import SequenceMatcher

    a = re.sub(r"\s+", " ", (text_a or "").strip().lower())
    b = re.sub(r"\s+", " ", (text_b or "").strip().lower())
    if not a or not b:
        return False
    word_score = jaccard(content_tokens(a), content_tokens(b))
    char_score = SequenceMatcher(None, a, b).ratio()
    return max(word_score, char_score) >= threshold


def clean_text(text: str, max_len: int | None = None) -> str:
    """Collapse whitespace, strip smart quotes and dashes for TTS/ASS safety."""
    t = (text or "").strip()
    # dashes first, then collapse whitespace, then fix the spacing the replacement created
    t = t.replace("—", ", ").replace("–", ", ").replace("“", '"').replace("”", '"')
    t = re.sub(r"\s+", " ", t)
    t = re.sub(r"\s+([,.;:!?])", r"\1", t)
    if max_len and len(t) > max_len:
        t = t[: max_len - 1].rstrip() + "…"
    return t


def human_bytes(num: float) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if abs(num) < 1024:
            return f"{num:.1f}{unit}"
        num /= 1024
    return f"{num:.1f}TB"


def human_time(seconds: float) -> str:
    seconds = max(0, int(round(seconds)))
    return f"{seconds // 60}:{seconds % 60:02d}"


def fmt_ts_ass(seconds: float) -> str:
    """ASS timestamp: H:MM:SS.cc"""
    seconds = max(0.0, float(seconds))
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def esc_ass(text: str) -> str:
    """Escape text for an ASS dialogue line."""
    return (
        (text or "")
        .replace("\\", "\\\\")
        .replace("{", "(")
        .replace("}", ")")
        .replace("\n", "\\N")
    )


def chunked(seq: Sequence[Any], size: int) -> list[list[Any]]:
    return [list(seq[i : i + size]) for i in range(0, len(seq), size)]
