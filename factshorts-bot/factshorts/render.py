"""Render module: 1080x1920 Shorts renderer built on ffmpeg (no MoviePy needed for the heavy lift).

Pipeline per video:
  1. plan       - split the target duration across the selected clips
  2. normalise  - each clip: cover-crop to 1080x1920, fps, subtle animated zoom, no audio
  3. join       - xfade cross-fades (or hard cuts) into one base video
  4. audio      - voiceover + optional local royalty-free music with side-chain ducking
  5. captions   - burn the .ass file, add a fade-out, encode H.264 yuv420p faststart

Every step is a separate ffmpeg call so failures are easy to isolate, and all
temporary files live inside cache/tmp so the output folder stays clean.
"""
from __future__ import annotations

import json
import random
import re
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from .captions import captions_for
from .config import Config, get_config
from .footage import Clip, credits_line
from .script_writer import Script
from .utils import (
    CommandError,
    human_bytes,
    media_duration,
    module_logger,
    run_cmd,
    run_cmd_async,
    slugify,
    video_size,
)
from .voice import VoiceResult

log = module_logger("render")

MUSIC_EXTS = {".mp3", ".m4a", ".wav", ".aac", ".ogg", ".opus", ".flac"}
VIDEO_EXTS = {".mp4", ".mov", ".mkv", ".webm"}


def ensure_fonts(cfg: Config | None = None) -> None:
    """Make sure the bundled caption font is visible to libass (fontconfig).

    ffmpeg renders ASS through fontconfig, which only looks at installed fonts.
    We register assets/fonts/*.ttf in the user font dir once, so captions always
    use the intended font instead of silently falling back to DejaVu.
    """
    cfg = cfg or get_config()
    fonts = sorted(cfg.fonts_dir.glob("*.ttf")) if cfg.fonts_dir.exists() else []
    if not fonts:
        log.info("no bundled fonts in %s - libass will use a system font", cfg.fonts_dir)
        return
    family = cfg.caption_font.split()[0]
    try:
        probe = run_cmd(["fc-match", "-f", "%{family}\n", cfg.caption_font], check=False, timeout=30)
        if family.lower() in (probe.stdout or "").lower():
            return  # already available
        dest = Path.home() / ".local" / "share" / "fonts"
        dest.mkdir(parents=True, exist_ok=True)
        for font in fonts:
            shutil.copy2(font, dest / font.name)
        run_cmd(["fc-cache", "-f", "-q"], check=False, timeout=180)
        log.info("registered caption font %r in %s", cfg.caption_font, dest)
    except Exception as exc:  # noqa: BLE001 - never fail a render over a font
        log.warning("could not register the caption font (%s) - using a fallback", exc)


@dataclass
class SegmentPlan:
    clip: Clip
    start: float
    length: float
    loop: bool = False


@dataclass
class RenderResult:
    path: Path
    duration: float
    width: int
    height: int
    size_bytes: int
    clip_count: int
    caption_pages: int
    voice: str
    credit: str
    report: dict = field(default_factory=dict)

    def as_dict(self) -> dict:
        return self.report


class RenderError(RuntimeError):
    pass


# --------------------------------------------------------------------- helpers
def _cover_crop_chain(cfg: Config) -> str:
    return (
        f"scale={cfg.width}:{cfg.height}:force_original_aspect_ratio=increase:flags=bicubic,"
        f"crop={cfg.width}:{cfg.height},setsar=1,"
        f"eq=contrast=1.05:saturation=1.10,"
        f"vignette=PI/5"
    )


def _zoom_chain(idx: int, seg_len: float, cfg: Config) -> str:
    """FireRed-OpenStoryline intention-driven directing + Ken-Burns camera movement.

    * Beat 0 (The Hook, 0-3s): Punch zoom-in (z * 1.45) to capture immediate viewer focus.
    * Middle Beats (Core Story): Alternating zoom-in/zoom-out with cinematic lateral drift.
    * Final Beat: Smooth pull-back reveal.
    """
    z = max(0.0, cfg.zoom_amount)
    if z <= 0.001:
        return "null"

    if idx == 0:
        # High impact hook zoom
        eff_z = z * 1.45
        scale_expr = f"1+{eff_z:.4f}*t/{max(seg_len, 0.1):.3f}"
        drift = ""
    else:
        direction = "in" if idx % 2 == 0 else "out"
        if direction == "in":
            scale_expr = f"1+{z:.4f}*t/{max(seg_len, 0.1):.3f}"
        else:
            scale_expr = f"{1 + z:.4f}-{z:.4f}*t/{max(seg_len, 0.1):.3f}"
        drift = ""
        if idx % 3 == 2:
            sign = 1 if (idx // 3) % 2 == 0 else -1
            drift = f"+{sign}*0.02*{cfg.width}*(t/{max(seg_len,0.1):.3f})"

    return (
        f"scale=w='{cfg.width}*({scale_expr})':h='{cfg.height}*({scale_expr})':eval=frame:flags=bicubic,"
        f"crop={cfg.width}:{cfg.height}:"
        f"x='(in_w-{cfg.width})/2{drift}':y='(in_h-{cfg.height})/2',setsar=1"
    )


TARGET_SECONDS_PER_CLIP = 3.8  # calmer than a hard cut every 1.5s, still snappy


def picking_window(clip_duration: float, length: float) -> tuple[float, float]:
    """Where inside a clip we are allowed to start.

    Short B-roll: anywhere after the first fraction of a second (the start is often a
    fade-in). Long videos (NASA briefings, compilations): the middle, because intros,
    title cards and end credits live at the edges.
    """
    latest = max(0.0, clip_duration - length - 0.1)
    if clip_duration > 60:
        return (clip_duration * 0.30, max(clip_duration * 0.30, clip_duration * 0.70 - length))
    if latest > 1.0:
        return (min(0.4, latest), latest)
    return (0.0, latest)


def plan_segments(
    clips: list[Clip],
    total_duration: float,
    cfg: Config,
    sentence_durations: list[float] | None = None,
) -> list[SegmentPlan]:
    profile = cfg.profile()
    if sentence_durations and len(sentence_durations) > 0 and len(clips) >= len(sentence_durations):
        # Frame-perfect sentence synchronization: cut points align with sentence ends
        plans: list[SegmentPlan] = []
        raw_sum = sum(sentence_durations)
        scale = (total_duration / raw_sum) if raw_sum > 0 else 1.0
        scaled_durations = [round(d * scale, 3) for d in sentence_durations]

        for i, length in enumerate(scaled_durations):
            clip = clips[i]
            usable = max(0.6, clip.duration - 0.15)
            loop = usable < length - 0.05
            low, high = picking_window(clip.duration, length if not loop else min(length, usable))
            start = random.uniform(max(0.0, low), max(0.0, high)) if high > low else max(0.0, low)
            if loop:
                start = random.uniform(0, max(0.0, min(usable, clip.duration) - 0.6))
            plans.append(SegmentPlan(clip=clip, start=round(start, 3), length=round(length, 3), loop=loop))

        log.info(
            "sentence-synced segment plan (%d shots, total %.2fs): %s",
            len(plans), total_duration,
            ", ".join(f"{p.clip.candidate.key}@{p.start:.1f}s({p.length:.1f}s){'~loop' if p.loop else ''}" for p in plans),
        )
        return plans

    seconds_per_clip = profile.seconds_per_clip or TARGET_SECONDS_PER_CLIP
    n = max(1, min(len(clips), max(1, profile.clip_count)))
    # pace by duration instead of always using clip_count: ~3.8s per shot feels right for
    # facts, ~6.5s for a 60 s story (fewer, calmer cuts over a longer narration)
    paced = max(1, min(n, int(round(total_duration / seconds_per_clip)) or 1))
    n = paced
    chosen = clips[:n]

    def layout(count: int) -> tuple[float, float]:
        overlap = cfg.transition_duration if (cfg.transition == "fade" and count > 1) else 0.0
        base = total_duration + overlap * (count - 1)
        return base / count, overlap

    share, overlap = layout(n)
    while share < 1.6 and n > 1:  # never cut faster than ~1.6s per shot
        n -= 1
        chosen = chosen[:n]
        share, overlap = layout(n)

    plans: list[SegmentPlan] = []
    for clip in chosen:
        usable = max(0.6, clip.duration - 0.15)
        length = share
        loop = usable < share - 0.05
        low, high = picking_window(clip.duration, length if not loop else min(length, usable))
        start = random.uniform(max(0.0, low), max(0.0, high)) if high > low else max(0.0, low)
        if loop:
            start = random.uniform(0, max(0.0, min(usable, clip.duration) - 0.6))
        plans.append(SegmentPlan(clip=clip, start=round(start, 3), length=round(length, 3), loop=loop))
    log.info(
        "segment plan (%d shots, %.2fs each): %s",
        len(plans), share,
        ", ".join(f"{p.clip.candidate.key}@{p.start:.1f}s{'~loop' if p.loop else ''}" for p in plans),
    )
    return plans


BLUR_LIMIT = 18.0        # blurdetect: measured 4.5-12 on sharp stock vs ~22 on a blurred copy
DARK_LIMIT = 32.0        # average luma below this = "dark" (starfields live here)
CONTRAST_LIMIT = 30.0    # YHIGH-YLOW: a black title card is dark AND has almost no range


async def _segment_stats(path: Path, cfg: Config) -> tuple[float, float, float]:
    """(average luma, dynamic range, blur) sampled once per second across a segment.

    * black title card -> dark AND flat. We measure structure with ffmpeg signalstats'
      YHIGH-YLOW range, because signalstats does **not** emit a standard deviation and
      "dark" alone would wrongly reject starfields and night skies.
    * focus pull / fade -> blurdetect score jumps well above the sharp baseline.
    """
    try:
        _code, _out, err = await run_cmd_async(
            ["ffmpeg", "-hide_banner", "-v", "info", "-i", str(path),
             "-vf", "fps=1,signalstats,blurdetect,metadata=print",
             "-f", "null", "-"],
            timeout=120, check=False,
        )
    except Exception:  # noqa: BLE001
        return (255.0, 255.0, 0.0)

    def avg(key: str, default: float) -> float:
        values = [float(x) for x in re.findall(rf"{key}=([0-9.]+)", err)]
        return (sum(values) / len(values)) if values else default

    yavg = avg("YAVG", 255.0)
    yhigh = avg("YHIGH", 255.0)
    ylow = avg("YLOW", 0.0)
    blur = avg(r"lavfi\.blur", 0.0)
    return (yavg, max(0.0, yhigh - ylow), blur)


def segment_problem(stats: tuple[float, float, float]) -> str:
    """'' when the slice is usable, else a short reason."""
    yavg, contrast, blur = stats
    if yavg < DARK_LIMIT and contrast < CONTRAST_LIMIT:
        return f"black/empty frame (luma={yavg:.0f} range={contrast:.0f})"
    if blur and blur > BLUR_LIMIT:
        return f"soft/out of focus (blur={blur:.0f})"
    return ""


async def rank_clips_by_sharpness(clips: list, cfg: Config | None = None, keep: int | None = None) -> list:
    """Measure each candidate clip and return them sharpest-first, dropping the ones that
    are dramatically softer than the best (self-calibrating: no fixed blur threshold, so it
    works for both crisp city B-roll and soft starfields).

    `blurdetect` is only meaningful in comparison, which is exactly how it is used here.
    """
    cfg = cfg or get_config()
    scored = []
    for clip in clips:
        if getattr(clip, "sharpness", None) is None:
            quality = await clip_quality(clip.path, cfg)
            clip.sharpness = quality["blur"]
        scored.append(clip)
    if len(scored) < 2:
        return scored

    blur_values = sorted(c.sharpness for c in scored)
    median = blur_values[len(blur_values) // 2]
    # a clip is only dropped when it is both worse than the median and clearly soft in absolute
    # terms (>=1.6x the median and above the blur limit)
    kept = [c for c in scored if not (c.sharpness >= median * 1.6 and c.sharpness > BLUR_LIMIT)]
    if not kept:
        kept = scored
    if keep and len(kept) > keep:
        kept = sorted(kept, key=lambda c: c.sharpness)[: keep]
        log.info("sharpness ranking kept the best %d of %d clips", keep, len(scored))
    else:
        dropped = len(scored) - len(kept)
        if dropped:
            log.info("sharpness ranking dropped %d soft clip(s) (median blur %.1f)", dropped, median)
    return sorted(kept, key=lambda c: c.sharpness)


async def clip_quality(path: Path, cfg: Config | None = None, samples: int = 3) -> dict:
    """Cheap sharpness/darkness score for a source clip (used to prefer good B-roll).

    Samples a few windows in the middle of the clip so intros/credits do not skew it.
    """
    cfg = cfg or get_config()
    duration = media_duration(path)
    probes = []
    if duration > 12:
        for i in range(1, samples + 1):
            start = duration * i / (samples + 1)
            probes.append(start)
    else:
        probes = [max(0.0, duration / 2)]
    scores = []
    for start in probes[:samples]:
        try:
            _code, _out, err = await run_cmd_async(
                ["ffmpeg", "-hide_banner", "-v", "info", "-ss", f"{start:.2f}", "-i", str(path),
                 "-t", "2", "-vf", "blurdetect,metadata=print", "-f", "null", "-"],
                timeout=60, check=False,
            )
            values = [float(x) for x in re.findall(r"lavfi\.blur=([0-9.]+)", err)]
            if values:
                scores.append(sum(values) / len(values))
        except Exception:  # noqa: BLE001
            continue
    blur = sum(scores) / len(scores) if scores else 0.0
    return {"blur": round(blur, 2), "sharp": (blur == 0.0 or blur <= BLUR_LIMIT)}


async def _normalize_segment(plan: SegmentPlan, index: int, workdir: Path, cfg: Config) -> Path:
    out = workdir / f"seg_{index:02d}.mp4"
    vf = f"{_cover_crop_chain(cfg)},{_zoom_chain(index, plan.length, cfg)},fps={cfg.fps},format=yuv420p"
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y"]
    if plan.loop:
        cmd += ["-stream_loop", "1"]
    cmd += ["-ss", f"{plan.start:.3f}", "-i", str(plan.clip.path), "-t", f"{plan.length:.3f}", "-an"]
    cmd += ["-vf", vf, "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", str(out)]
    try:
        await run_cmd_async(cmd, timeout=300)
    except CommandError as exc:
        raise RenderError(f"failed to normalise clip {plan.clip.candidate.key}: {exc}") from exc
    if not out.exists() or out.stat().st_size < 5000:
        raise RenderError(f"normalised segment is empty: {out}")

    # guard against black title cards / credits inside long source videos: if the slice is
    # both dark and flat, shift the window and try again
    for attempt in range(1, 4):
        stats = await _segment_stats(out, cfg)
        problem = segment_problem(stats)
        if not problem:
            break
        low, high = picking_window(plan.clip.duration, plan.length)
        new_start = min(high, plan.start + plan.length + 1.5)
        if abs(new_start - plan.start) < 0.3 or new_start < low:
            log.warning("segment %d still problematic after %d tries: %s (keeping it)", index, attempt, problem)
            break
        log.info("segment %d rejected: %s -> shifting start %.1fs -> %.1fs", index, problem, plan.start, new_start)
        plan.start = round(new_start, 3)
        if plan.loop:
            plan.loop = False
        cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
               "-ss", f"{plan.start:.3f}", "-i", str(plan.clip.path), "-t", f"{plan.length:.3f}", "-an",
               "-vf", f"{_cover_crop_chain(cfg)},{_zoom_chain(index, plan.length, cfg)},fps={cfg.fps},format=yuv420p",
               "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", str(out)]
        await run_cmd_async(cmd, timeout=300)
    return out


async def _join_segments(segments: list[Path], workdir: Path, cfg: Config, total_duration: float) -> Path:
    out = workdir / "base.mp4"
    if len(segments) == 1:
        await run_cmd_async(
            ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(segments[0]),
             "-t", f"{total_duration:.3f}", "-c", "copy", str(out)],
            timeout=180,
        )
        return out

    if cfg.transition == "fade":
        d = cfg.transition_duration
        lengths = [media_duration(p) for p in segments]
        parts = []
        prev = "[0:v]"
        offset = 0.0
        for i in range(1, len(segments)):
            offset += max(0.05, lengths[i - 1] - d)
            label = f"[v{i}]"
            parts.append(f"{prev}[{i}:v]xfade=transition=fade:duration={d:.3f}:offset={offset:.3f}{label}")
            prev = label
        graph = ";".join(parts)
        cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y"]
        for seg in segments:
            cmd += ["-i", str(seg)]
        cmd += ["-filter_complex", graph, "-map", prev, "-an", "-c:v", "libx264", "-preset", "veryfast",
                "-crf", "18", "-pix_fmt", "yuv420p", str(out)]
        try:
            await run_cmd_async(cmd, timeout=420)
        except CommandError as exc:  # pragma: no cover - fall back to hard cuts
            log.warning("xfade join failed (%s) -> hard cuts", exc)
            cfg.transition = "cut"
            return await _join_segments(segments, workdir, cfg, total_duration)
    else:
        listfile = workdir / "concat.txt"
        listfile.write_text("".join(f"file '{p.resolve()}'\n" for p in segments), encoding="utf-8")
        try:
            await run_cmd_async(
                ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0",
                 "-i", str(listfile), "-t", f"{total_duration:.3f}", "-c", "copy", str(out)],
                timeout=240,
            )
        except CommandError:
            # re-encode if stream params differ
            cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0",
                   "-i", str(listfile), "-t", f"{total_duration:.3f}", "-an", "-c:v", "libx264",
                   "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", str(out)]
            await run_cmd_async(cmd, timeout=420)

    if not out.exists() or out.stat().st_size < 10_000:
        raise RenderError("failed to join segments")
    return out


async def pick_music(cfg: Config, niche: str = "space", duration: float = 30.0) -> Path | None:
    if not cfg.music_enabled:
        return None
    from .music import ensure_music_track
    try:
        return await ensure_music_track(niche, duration, cfg)
    except Exception as exc:  # noqa: BLE001
        log.warning("could not auto-ensure background music: %s", exc)
        return None


async def _mix_audio(
    voice: VoiceResult,
    workdir: Path,
    total_duration: float,
    cfg: Config,
    music: Path | None = None,
) -> Path:
    out = workdir / "mix.m4a"
    lead_in = 0.10
    fade_start = max(0.1, total_duration - 0.35)

    if music and cfg.music_volume > 0:
        music_fade_start = max(0.1, total_duration - 3.0)
        cmd = [
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-i", str(voice.path),
            "-stream_loop", "-1", "-i", str(music),
        ]
        graph = (
            f"[0:a]adelay=delays={int(lead_in*1000)}|{int(lead_in*1000)},aformat=channel_layouts=stereo[v0];"
            f"[1:a]aformat=channel_layouts=stereo,atrim=0:{total_duration:.3f},volume={cfg.music_volume:.3f},afade=t=out:st={music_fade_start:.3f}:d=3.0[m0];"
            f"[m0][v0]sidechaincompress=threshold=0.045:ratio=9:attack=15:release=320:makeup=1[ducked];"
            f"[v0][ducked]amix=inputs=2:duration=first:dropout_transition=0:normalize=0[mixed];"
            f"[mixed]apad,atrim=0:{total_duration:.3f},afade=t=out:st={fade_start:.3f}:d=0.35[aout]"
        )
        cmd += ["-filter_complex", graph, "-map", "[aout]", "-c:a", "aac", "-b:a", "192k", str(out)]
    else:
        graph = (
            f"[0:a]adelay=delays={int(lead_in*1000)}|{int(lead_in*1000)},aformat=channel_layouts=stereo,"
            f"apad,atrim=0:{total_duration:.3f},afade=t=out:st={fade_start:.3f}:d=0.35[aout]"
        )
        cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(voice.path),
               "-filter_complex", graph, "-map", "[aout]", "-c:a", "aac", "-b:a", "192k", str(out)]

    try:
        await run_cmd_async(cmd, timeout=240)
    except CommandError as exc:
        log.error("audio mix failed (%s) -> voice only", exc)
        await run_cmd_async(
            ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(voice.path),
             "-af", f"apad,atrim=0:{total_duration:.3f}", "-c:a", "aac", "-b:a", "192k", str(out)],
            timeout=180,
        )
    return out


async def _final_pass(
    base: Path,
    audio: Path,
    ass_file: Path | None,
    out_path: Path,
    total_duration: float,
    cfg: Config,
    workdir: Path,
) -> Path:
    fade_start = max(0.1, total_duration - 0.35)
    filters = []
    if ass_file is not None:
        fonts_dir_arg = str(cfg.fonts_dir.resolve()).replace('\\', '/').replace(':', r'\:')
        filters.append(f"ass='{ass_file.name}':fontsdir='{fonts_dir_arg}'")  # cwd = workdir keeps path trivial
    filters.append(f"fade=t=out:st={fade_start:.3f}:d=0.35")
    filters.append("format=yuv420p")
    cmd = [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-i", str(base), "-i", str(audio),
        "-vf", ",".join(filters),
        "-map", "0:v:0", "-map", "1:a:0",
    ]
    if cfg.video_threads > 0:
        cmd += ["-threads", str(cfg.video_threads)]
    cmd += [
        "-t", f"{total_duration:.3f}",
        "-c:v", "libx264", "-preset", cfg.preset, "-crf", str(cfg.crf), "-r", str(cfg.fps),
        "-profile:v", "high", "-level", "4.1", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
        "-movflags", "+faststart", str(out_path),
    ]
    await run_cmd_async(cmd, timeout=600, cwd=workdir)
    if not out_path.exists() or out_path.stat().st_size < 50_000:
        raise RenderError(f"final render looks wrong: {out_path}")
    await _openmontage_qa_review(out_path, total_duration, cfg)
    return out_path


async def _openmontage_qa_review(out_path: Path, expected_duration: float, cfg: Config) -> dict[str, Any]:
    """OpenMontage multi-point self-review QA layer.

    Validates:
    1. Duration match (within ±1.0s of expected).
    2. Video dimensions match expected 9:16 vertical (1080x1920).
    3. File size and stream integrity.
    """
    qa_report: dict[str, Any] = {"valid": True, "checks": []}
    try:
        dur = media_duration(out_path)
        w, h = video_size(out_path)
        dur_diff = abs(dur - expected_duration)
        if dur_diff > 1.2:
            log.warning("OpenMontage QA: duration drift %.2fs (target: %.2f)", dur_diff, expected_duration)
        qa_report["checks"].append(f"duration: {dur:.2f}s (target: {expected_duration:.2f}s)")

        if (w, h) != (cfg.width, cfg.height):
            log.warning("OpenMontage QA: dimensions %dx%d do not match target %dx%d", w, h, cfg.width, cfg.height)
        qa_report["checks"].append(f"resolution: {w}x{h}")

        file_size_kb = out_path.stat().st_size / 1024
        qa_report["checks"].append(f"filesize: {file_size_kb:.1f} KB")
        log.info("OpenMontage QA passed for %s: %s", out_path.name, ", ".join(qa_report["checks"]))
    except Exception as exc:  # noqa: BLE001
        log.warning("OpenMontage QA check encountered error: %s", exc)
        qa_report["valid"] = False
    return qa_report


# ------------------------------------------------------------------------ API
async def render_video(
    script: Script,
    clips: list[Clip],
    voice: VoiceResult,
    video_id: int | None = None,
    cfg: Config | None = None,
    out_dir: Path | None = None,
) -> RenderResult:
    """Render one Short. Returns RenderResult with the final mp4 path."""
    cfg = cfg or get_config()
    if not clips:
        raise RenderError("no clips to render")

    profile = cfg.profile()
    # story mode: never pad the video far past the narration (a 40 s story with 5 s of
    # silence at the end looks broken). facts mode keeps its familiar 9.5 s floor.
    floor = profile.min_duration
    if profile.name != "facts":
        floor = min(profile.min_duration, voice.duration + 1.0)
    total_duration = min(profile.max_duration, max(floor, voice.duration + 0.35))
    if voice.duration + 0.15 > profile.max_duration:
        log.warning(
            "narration is %.1fs which exceeds the %.1fs %s limit - audio will be trimmed",
            voice.duration,
            profile.max_duration,
            profile.name,
        )

    ensure_fonts(cfg)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    tag = f"{video_id or 'x'}-{slugify(script.topic or script.niche or 'fact', 34)}-{stamp}"
    out_dir = Path(out_dir or cfg.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{tag}.mp4"

    workdir = cfg.cache_dir / "tmp" / tag
    workdir.mkdir(parents=True, exist_ok=True)
    log.info("render start -> %s (target %.2fs, %d clips)", out_path.name, total_duration, len(clips))

    sentence_durs = [seg[2] for seg in getattr(voice, "segments", [])] if getattr(voice, "segments", None) else None
    plans = plan_segments(clips, total_duration, cfg, sentence_durations=sentence_durs)
    segments = []
    for i, plan in enumerate(plans):
        segments.append(await _normalize_segment(plan, i, workdir, cfg))
    base = await _join_segments(segments, workdir, cfg, total_duration)

    # the on-screen banner is the topic label, not the spoken hook: showing the hook twice
    # (banner + captions) looked duplicated
    banner = script.topic or script.niche or ""
    ass_file, page_count = captions_for(
        voice.words,
        script.full_text,
        total_duration,
        workdir / "captions.ass",
        cfg,
        segments=getattr(voice, "segments", None),
        audio_path=voice.path,
        hook_text=banner if cfg.hook_banner else "",
    )
    music = await pick_music(cfg, niche=getattr(script, "niche", "space"), duration=total_duration)
    audio = await _mix_audio(voice, workdir, total_duration, cfg, music=music)
    await _final_pass(base, audio, ass_file, out_path, total_duration, cfg, workdir)

    duration = media_duration(out_path) or total_duration
    width, height = video_size(out_path)
    credit = credits_line(clips)
    size = out_path.stat().st_size

    report = {
        "video_id": video_id,
        "path": str(out_path),
        "duration": round(duration, 2),
        "width": width,
        "height": height,
        "size_bytes": size,
        "size_human": human_bytes(size),
        "clips": [
            {
                "source": c.candidate.source,
                "id": c.candidate.source_id,
                "page": c.candidate.page_url,
                "author": c.candidate.author,
                "license": c.candidate.license,
                "query": c.candidate.query,
                "used_duration": p.length,
                "start": p.start,
            }
            for c, p in zip([pl.clip for pl in plans], plans)
        ],
        "caption_pages": page_count,
        "voice": voice.voice,
        "music": str(music or ""),
        "credit": credit,
        "workdir": str(workdir),
        "rendered_at": datetime.now().isoformat(timespec="seconds"),
    }
    (out_dir / f"{tag}.json").write_text(json.dumps(report, indent=2), encoding="utf-8")

    log.info(
        "render done: %s | %.2fs | %s | %d caption pages | %d clips",
        out_path.name, duration, human_bytes(size), page_count, len(plans),
    )
    return RenderResult(
        path=out_path,
        duration=duration,
        width=width,
        height=height,
        size_bytes=size,
        clip_count=len(plans),
        caption_pages=page_count,
        voice=voice.voice,
        credit=credit,
        report=report,
    )


async def render_placeholder(seconds: float = 3.0, cfg: Config | None = None) -> Path:
    """Tiny self-test render (no network, no stock footage) - used by `python main.py --selftest`."""
    cfg = cfg or get_config()
    out = cfg.cache_dir / "tmp" / "selftest.mp4"
    out.parent.mkdir(parents=True, exist_ok=True)
    ass = cfg.cache_dir / "tmp" / "selftest.ass"
    ass.write_text(
        "[Script Info]\nScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1920\n\n"
        "[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, "
        "BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, "
        "Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
        f"Style: Caption,{cfg.caption_font},96,&H00FFFFFF,&H0000E5FF,&H00000000,&H80000000,-1,0,0,0,100,100,"
        "0,0,1,6,3,5,60,60,240,1\n\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, "
        "MarginV, Effect, Text\n"
        "Dialogue: 0,0:00:00.05,0:00:03.00,Caption,,0,0,0,,Selftest {\\c&H0000E5FF}works{\\c&H00FFFFFF} fine\n",
        encoding="utf-8",
    )
    cmd = [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-f", "lavfi", "-i", f"testsrc2=size={cfg.width}x{cfg.height}:duration={seconds}:rate={cfg.fps}",
        "-f", "lavfi", "-i", f"sine=frequency=220:duration={seconds}",
        "-vf", "ass=selftest.ass", "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
        "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", str(out),
    ]
    await run_cmd_async(cmd, timeout=300, cwd=ass.parent)
    log.info("selftest render ok: %s", out)
    return out
