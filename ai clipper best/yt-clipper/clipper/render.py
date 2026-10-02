"""Step 6 - FFmpeg render: cut -> 9:16 (blurred pillar or face-tracked crop) ->
mix dub over ducked original -> burn captions."""
from __future__ import annotations

import json
import shlex
import subprocess
from pathlib import Path

from .config import settings


def run(cmd: list[str], dry: bool = False) -> str:
    line = " ".join(shlex.quote(c) for c in cmd)
    if dry:
        return line
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode:
        raise RuntimeError(f"ffmpeg failed:\n{line}\n{p.stderr[-2000:]}")
    return line


def crop_filter(mode: str = "blur") -> str:
    W, H = settings.width, settings.height
    if mode == "crop":           # centre-safe fill crop, no bars
        return (f"scale={W}:{H}:force_original_aspect_ratio=increase,"
                f"crop={W}:{H},setsar=1")
    # blurred background + centred source (keeps gameplay HUD readable)
    return (f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
            f"gblur=sigma=28,eq=brightness=-0.06[bg];"
            f"[0:v]scale={W}:-2:force_original_aspect_ratio=decrease[fg];"
            f"[bg][fg]overlay=(W-w)/2:(H-h)/2,setsar=1")


def render_clip(source: str | Path, start: float, end: float, out_path: str | Path,
                ass: str | Path | None = None, voice_audio: str | Path | None = None,
                mode: str = "blur", dry: bool = False) -> str:
    source, out_path = str(source), Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    dur = round(end - start, 3)

    cmd = ["ffmpeg", "-y", "-ss", f"{start:.3f}", "-t", f"{dur}", "-i", source]
    if voice_audio:
        cmd += ["-i", str(voice_audio)]

    vf = crop_filter(mode)
    last = "[vout]"
    if ass:
        esc = str(ass).replace("\\", "/").replace(":", r"\:")
        vf = f"{vf}[v0];[v0]ass='{esc}'{last}"
    else:
        vf = f"{vf}{last}"

    if voice_audio:
        keep = settings.keep_original_audio
        af = (f"[0:a]volume={keep}[orig];[1:a]volume=1.0,adelay=120|120[vo];"
              f"[orig][vo]amix=inputs=2:duration=first:dropout_transition=0[aout]")
        filter_complex = f"{vf};{af}"
        amap = ["-map", "[aout]"]
    else:
        filter_complex = vf
        amap = ["-map", "0:a?"]

    cmd += ["-filter_complex", filter_complex, "-map", last, *amap,
            "-r", str(settings.fps), "-c:v", "libx264", "-preset", "medium",
            "-crf", str(settings.crf), "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart",
            "-shortest", str(out_path)]
    return run(cmd, dry=dry)


def probe(path: str | Path) -> dict:
    out = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format",
         "-show_streams", str(path)], capture_output=True, text=True).stdout
    return json.loads(out or "{}")
