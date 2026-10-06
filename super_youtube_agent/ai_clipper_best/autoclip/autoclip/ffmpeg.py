"""Locate ffmpeg/ffprobe robustly.

Sandboxes and fresh machines lose the exec bit or the whole package, so resolve in
this order: $AUTOCLIP_FFMPEG -> PATH -> imageio-ffmpeg's bundled static binary.
"""
from __future__ import annotations

import os
import shutil
import stat
import subprocess
from functools import lru_cache
from pathlib import Path


@lru_cache(maxsize=2)
def binary(name: str = "ffmpeg") -> str:
    env = os.getenv(f"AUTOCLIP_{name.upper()}")
    if env and os.path.exists(env):
        _ensure_exec(env)
        return env
    found = shutil.which(name)
    if found:
        return found
    if name in ("ffmpeg", "ffprobe"):
        try:
            import imageio_ffmpeg

            p = imageio_ffmpeg.get_ffmpeg_exe()
            if name == "ffprobe":
                # imageio-ffmpeg ships ffmpeg only. Some builds drop an
                # ffprobe next to it; use that when present.
                cand = os.path.join(os.path.dirname(p), "ffprobe")
                if os.path.exists(cand):
                    _ensure_exec(cand)
                    return cand
                raise FileNotFoundError("no ffprobe beside imageio ffmpeg")
            _ensure_exec(p)
            return p
        except Exception:
            pass
    raise RuntimeError(
        f"{name} not found. Install it (apt install ffmpeg / brew install ffmpeg) "
        f"or `pip install imageio-ffmpeg`."
    )


def _ensure_exec(path: str) -> None:
    try:
        st = os.stat(path)
        if not st.st_mode & stat.S_IXUSR:
            os.chmod(path, st.st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    except OSError:
        pass


def run(args: list[str], quiet: bool = True) -> subprocess.CompletedProcess:
    cmd = [binary("ffmpeg"), "-y"] + (["-v", "error"] if quiet else []) + args
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode:
        raise RuntimeError("ffmpeg failed:\n" + p.stderr[-2500:])
    return p


def duration(path: str) -> float:
    try:
        out = subprocess.run([binary("ffprobe"), "-v", "quiet", "-show_entries",
                              "format=duration", "-of", "csv=p=0", path],
                             capture_output=True, text=True).stdout.strip()
        return float(out)
    except Exception:
        return 0.0


def shim_dir() -> str:
    """Directory containing a binary literally named `ffmpeg`.

    yt-dlp searches `ffmpeg_location` for a file called `ffmpeg`; imageio-ffmpeg's
    binary is named `ffmpeg-linux-x86_64-v7.0.2`, so merging bestvideo+bestaudio fails
    with "ffmpeg is not installed" even though it is right there. Symlink fixes it.
    """
    real = binary("ffmpeg")
    d = Path.home() / ".cache" / "autoclip" / "bin"
    d.mkdir(parents=True, exist_ok=True)
    link = d / "ffmpeg"
    try:
        if link.is_symlink() or link.exists():
            if os.path.realpath(link) == os.path.realpath(real):
                return str(d)
            link.unlink()
        link.symlink_to(real)
    except OSError:
        shutil.copy2(real, link)
        _ensure_exec(str(link))
    return str(d)
