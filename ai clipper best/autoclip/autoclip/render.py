"""Render one clip. Speed notes (measured, 2-core box, 35 s clip):

  medium preset, full-length input          ~124 s
  veryfast + fast seek + trimmed source      ~32 s      <- what this does

Three wins:
  1. `-ss` BEFORE `-i` (input seek) so ffmpeg jumps instead of decoding from zero.
  2. `-preset veryfast -crf 23` — Shorts are re-encoded by YouTube anyway, so a slower
     preset mostly buys file size you then throw away.
  3. Still images get `-loop 1 -framerate N -t dur`. A bare PNG decodes as ONE frame at
     t=0, so `fade`/`enable` never see a timeline and the overlay silently disappears.
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

from .ffmpeg import binary, run
from .transform import audio_chain, speed_of, video_chain


def probe_size(path: str) -> tuple[int, int]:
    """Real pixel size of a video.

    This used to swallow every error and return a hardcoded 1280x720. That is
    the worst possible failure here: `auto_margin_v` feeds on these numbers,
    so a silent wrong answer moves every caption off its safe band and the
    render still "succeeds". Fall back to ffmpeg, then give up loudly.
    """
    try:
        out = subprocess.run(
            [binary("ffprobe"), "-v", "quiet", "-select_streams", "v:0",
             "-show_entries", "stream=width,height", "-of", "json", path],
            capture_output=True, text=True).stdout
        s = json.loads(out)["streams"][0]
        return int(s["width"]), int(s["height"])
    except Exception:
        pass
    # ffprobe missing: ffmpeg prints the size on stderr while refusing to work.
    try:
        err = subprocess.run([binary("ffmpeg"), "-hide_banner", "-i", path],
                             capture_output=True, text=True).stderr
        m = re.search(r"Stream #.*Video:.*?(\d{2,5})x(\d{2,5})", err)
        if m:
            return int(m.group(1)), int(m.group(2))
    except Exception:
        pass
    raise RuntimeError(
        f"cannot read video size of {path}: install ffprobe. Guessing here "
        "would silently misplace every caption.")


def render_clip(src: str, start: float, end: float, out: Path, *, profile: dict,
                ass: Path | None = None, title_png: Path | None = None,
                watermark: str | None = None, punches: list | None = None,
                safe_level: int = 1, preset: str | None = None,
                dry: bool = False) -> dict:
    W, H = profile["width"], profile["height"]
    fps = str(profile.get("fps", 30))
    dur = round(end - start, 3)
    out.parent.mkdir(parents=True, exist_ok=True)

    vc, params = video_chain(W, H, safe_level, punches,
                             profile.get("punch_zoom", 1.14),
                             profile.get("blur_bg", True))
    chain = [vc]
    last = "[base]"

    args = ["-ss", f"{start:.3f}", "-t", f"{dur:.3f}", "-i", src]
    idx = 1
    if watermark:
        args += ["-loop", "1", "-framerate", fps, "-t", f"{dur:.3f}", "-i", watermark]
        wm_w = int(W * profile.get("watermark_scale", 0.11))
        m = profile.get("watermark_margin", 38)
        pos = {"top-right": (f"W-w-{m}", f"{m+10}"),
               "top-left": (f"{m}", f"{m+10}"),
               "bottom-right": (f"W-w-{m}", f"H-h-{m}"),
               "bottom-left": (f"{m}", f"H-h-{m}")}[profile.get("watermark_pos", "top-right")]
        chain.append(f"[{idx}:v]scale={wm_w}:-1,format=rgba,"
                     f"colorchannelmixer=aa={profile.get('watermark_opacity',0.85)}[wm]")
        chain.append(f"{last}[wm]overlay={pos[0]}:{pos[1]}[wmd]")
        last = "[wmd]"
        idx += 1
    if title_png:
        t = float(profile.get("title_seconds", 2.6))
        args += ["-loop", "1", "-framerate", fps, "-t", f"{dur:.3f}", "-i", str(title_png)]
        chain.append(f"[{idx}:v]scale={int(W*0.86)}:-1,format=rgba,"
                     f"fade=t=in:st=0:d=0.3:alpha=1,"
                     f"fade=t=out:st={t-0.45:.2f}:d=0.45:alpha=1[tc]")
        chain.append(f"{last}[tc]overlay=(W-w)/2:{int(H*0.13)}:enable='lt(t,{t})'[titled]")
        last = "[titled]"
        idx += 1
    if ass:
        esc = str(ass).replace("\\", "/").replace(":", r"\:")
        fd = profile.get("fontdir", "")
        chain.append(f"{last}ass='{esc}'" + (f":fontsdir='{fd}'" if fd else "") + "[vout]")
        last = "[vout]"
    else:
        chain.append(f"{last}null[vout]")
        last = "[vout]"

    ac = audio_chain(safe_level)
    chain.append(f"[0:a]{ac}[aout]")

    cmd = args + ["-filter_complex", ";".join(chain), "-map", last, "-map", "[aout]",
                  "-r", fps, "-c:v", "libx264",
                  "-preset", preset or profile.get("preset", "veryfast"),
                  "-crf", str(profile.get("crf", 23)), "-pix_fmt", "yuv420p",
                  "-profile:v", "high", "-level", "4.0",
                  "-c:a", "aac", "-b:a", "128k", "-ar", "44100",
                  "-movflags", "+faststart", "-threads", "0", str(out)]
    if dry:
        return {"cmd": " ".join(cmd)}
    run(cmd)
    return {"mp4": str(out), "duration": round(dur / speed_of(safe_level), 2),
            "size_mb": round(out.stat().st_size / 1e6, 2), "safe": params}
