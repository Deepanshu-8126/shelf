"""Crawl inputs: a single URL, a playlist, a whole channel, or a search query.

    autoclip run "https://youtu.be/xxxx"
    autoclip run "https://www.youtube.com/@BiggBoss/videos" --limit 5
    autoclip run "ytsearch10:bigg boss fight 2026"
"""
from __future__ import annotations

import json
import re
from pathlib import Path

def _ffmpeg_dir() -> str | None:
    try:
        from .ffmpeg import shim_dir
        return shim_dir()
    except Exception:
        return None


CHANNEL_RE = re.compile(r"youtube\.com/(@[\w.-]+|c/[\w.-]+|channel/[\w-]+)/?$", re.I)


def expand(target: str, limit: int = 1) -> list[dict]:
    """Return [{id,title,url,duration,uploader}] without downloading media."""
    import yt_dlp

    if CHANNEL_RE.search(target):
        target = target.rstrip("/") + "/videos"

    opts = {"quiet": True, "no_warnings": True, "extract_flat": "in_playlist",
            "skip_download": True, "playlistend": limit,
            "extractor_args": {"youtube": {"player_client": ["ios", "android", "mweb"]}}}
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(target, download=False)

    entries = info.get("entries") if isinstance(info, dict) else None
    items = entries if entries else [info]
    out = []
    for e in items[:limit]:
        if not e:
            continue
        vid = e.get("id")
        out.append({
            "id": vid,
            "title": e.get("title") or "",
            "url": e.get("url") if (e.get("url") or "").startswith("http")
                   else f"https://www.youtube.com/watch?v={vid}",
            "duration": e.get("duration") or 0,
            "uploader": e.get("uploader") or e.get("channel") or "",
        })
    return out


# Rough megabytes of mp4 per minute of runtime, measured on real YouTube sources
# (1280x720 ~2.1, 1920x1080 ~4.3). Used only to pick a height that will fit.
_MB_PER_MIN = {480: 1.1, 720: 2.1, 1080: 4.3, 1440: 9.0, 2160: 20.0}


def _probe_mb(info: dict) -> float:
    """Actual download size yt-dlp predicts for the selected formats, in MB.

    Far better than a bitrate guess: the same 69-minute episode is 4 MB/min on
    one channel and 7 MB/min on another. Returns 0.0 when yt-dlp will not say.
    """
    reqs = info.get("requested_formats") or ([info] if info.get("url") else [])
    dur = info.get("duration") or 0
    total = 0.0
    for f in reqs:
        sz = f.get("filesize") or f.get("filesize_approx") or 0
        if not sz:
            # DASH formats usually report no size but do report a bitrate.
            tbr = f.get("tbr") or 0          # kbit/s
            if not (tbr and dur):
                return 0.0
            sz = tbr * 1000 / 8 * dur
        total += sz
    return total / 1e6


def fit_height(duration_s: float, workdir: Path, height: int,
               known_mb: float = 0.0) -> int:
    """Step `height` down until the download plausibly fits on disk.

    A 69-minute episode at 1080p is over a gigabyte. On a small tmpfs yt-dlp
    does not fail loudly when it runs out of room -- it stalls and the whole
    run dies with an empty log. Better to drop to 720p and say so.
    """
    import shutil

    workdir.mkdir(parents=True, exist_ok=True)
    free_mb = shutil.disk_usage(workdir).free / 1e6
    budget = free_mb * 0.80          # leave room for the muxed copy and renders
    mins = max(duration_s, 0) / 60.0
    if known_mb and known_mb <= budget:
        return height
    if known_mb:
        # Scale the measured size by area ratio to estimate the lower rungs.
        for h in sorted((x for x in _MB_PER_MIN if x <= height), reverse=True):
            est = known_mb * (h / height) ** 2
            if est <= budget:
                if h != height:
                    print(f"  disk: {free_mb:.0f} MB free, source is "
                          f"{known_mb:.0f} MB at {height}p -> using {h}p "
                          f"(~{est:.0f} MB)")
                return h
        # Measured and nothing fits. Do not fall through to the guess table.
        return 0
    for h in sorted(_MB_PER_MIN, reverse=True):
        if h > height:
            continue
        if mins * _MB_PER_MIN[h] <= budget:
            if h != height:
                print(f"  disk: {free_mb:.0f} MB free, {mins:.0f} min source -> "
                      f"{height}p would not fit, using {h}p")
            return h
    low = min(_MB_PER_MIN)
    print(f"  disk: only {free_mb:.0f} MB free for a {mins:.0f} min source; "
          f"trying {low}p anyway")
    return low


def download(url: str, workdir: Path, height: int = 720, cookies: str | None = None) -> dict:
    """Fetch the media once; reused by every clip from that video."""
    import yt_dlp

    workdir.mkdir(parents=True, exist_ok=True)
    opts = {
        # Prefer plain avc1: YouTube's "Premium" vp09 rung is 3 GB for a
        # 70-minute episode where avc1 is 1.3 GB, decodes faster, and the
        # difference vanishes after our re-encode.
        "format": f"bv*[height<={height}][vcodec^=avc1]+ba[ext=m4a]/"
                  f"bv*[height<={height}][ext=mp4]+ba[ext=m4a]/"
                  f"b[height<={height}]/b",
        "merge_output_format": "mp4",
        "outtmpl": str(workdir / "%(id)s.%(ext)s"),
        "quiet": True, "no_warnings": True, "noplaylist": True, "noprogress": True,
        "retries": 5, "concurrent_fragment_downloads": 4,
        "cookiefile": cookies,
        # yt-dlp needs ffmpeg to merge bestvideo+bestaudio. When it is not on PATH the
        # merge silently never happens and you are left with .fXXX fragments.
        "ffmpeg_location": _ffmpeg_dir(),
        "extractor_args": {"youtube": {"player_client": ["ios", "android", "mweb"]}},
    }
    with yt_dlp.YoutubeDL({**opts, "skip_download": True}) as ydl:
        probe = ydl.extract_info(url, download=False)
    fitted = fit_height(probe.get("duration") or 0, workdir, height,
                        known_mb=_probe_mb(probe))
    if fitted != height:
        opts["format"] = (f"bv*[height<={fitted}][ext=mp4]+ba[ext=m4a]/"
                          f"b[height<={fitted}]/b")
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
    path = workdir / f"{info['id']}.mp4"
    meta = {"id": info["id"], "title": info.get("title", ""),
            "duration": info.get("duration", 0),
            "uploader": info.get("uploader", ""), "path": str(path),
            "url": url}
    (workdir / f"{info['id']}.meta.json").write_text(json.dumps(meta, indent=2,
                                                                ensure_ascii=False))
    return meta


def download_audio(url: str, workdir: Path, cookies: str | None = None) -> dict:
    """Audio only, for transcription.

    A 70-minute episode is ~3 GB of 1080p video but ~65 MB of m4a, and the
    transcriber never looks at the pixels. Returns the same meta dict shape as
    `download`, plus the source width/height read from yt-dlp metadata so the
    caller can still do placement maths without the video on disk.
    """
    import yt_dlp

    workdir.mkdir(parents=True, exist_ok=True)
    opts = {
        "format": "ba[ext=m4a]/ba/b",
        "outtmpl": str(workdir / "%(id)s.audio.%(ext)s"),
        "quiet": True, "no_warnings": True, "noplaylist": True, "noprogress": True,
        "retries": 5, "concurrent_fragment_downloads": 4,
        "cookiefile": cookies,
        "ffmpeg_location": _ffmpeg_dir(),
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
    path = next(workdir.glob(f"{info['id']}.audio.*"))
    vf = [f for f in (info.get("formats") or []) if f.get("height")]
    best = max(vf, key=lambda f: f["height"]) if vf else {}
    return {"id": info["id"], "title": info.get("title", ""),
            "duration": info.get("duration", 0),
            "uploader": info.get("uploader", ""), "path": str(path),
            "width": best.get("width", 1280), "height": best.get("height", 720),
            "audio_only": True, "url": url}


def download_section(url: str, workdir: Path, start: float, end: float,
                     height: int = 1080, cookies: str | None = None,
                     pad: float = 1.0) -> Path:
    """Download only `start`-`end` of the video, via ffmpeg range requests.

    yt-dlp's own `download_ranges` hands the job to ffmpeg as an *external
    downloader*, which segfaults (exit -11) on this box. So we ask yt-dlp only
    for the direct media URLs and do the ranged pull ourselves: `-ss` before
    `-i` makes ffmpeg issue an HTTP range request instead of reading from the
    start, so a 15-second cut out of a 70-minute episode costs a few MB.
    """
    import subprocess
    import yt_dlp
    from .ffmpeg import binary

    workdir.mkdir(parents=True, exist_ok=True)
    a, b = max(0.0, start - pad), end + pad
    out = workdir / f"sec_{int(a)}_{int(b)}.mp4"
    if out.exists():
        return out

    opts = {
        "format": f"bv*[height<={height}][ext=mp4]+ba[ext=m4a]/b[height<={height}]/b",
        "quiet": True, "no_warnings": True, "noplaylist": True,
        "skip_download": True, "cookiefile": cookies,
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)
    streams = info.get("requested_formats") or [info]
    urls = [f["url"] for f in streams]

    cmd = [binary("ffmpeg"), "-y", "-loglevel", "error"]
    for u in urls:
        cmd += ["-ss", f"{a:.3f}", "-i", u]
    cmd += ["-t", f"{b - a:.3f}"]
    for n in range(len(urls)):
        cmd += ["-map", f"{n}:v:0?" if n == 0 and len(urls) > 1 else f"{n}:a:0?"]
    if len(urls) == 1:
        cmd = [c for c in cmd if not c.startswith("-map")]
        cmd = [binary("ffmpeg"), "-y", "-loglevel", "error",
               "-ss", f"{a:.3f}", "-i", urls[0], "-t", f"{b - a:.3f}"]
    cmd += ["-c", "copy", "-avoid_negative_ts", "make_zero", str(out)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0 or not out.exists():
        raise RuntimeError(f"section download failed: {r.stderr[-400:]}")
    return out
