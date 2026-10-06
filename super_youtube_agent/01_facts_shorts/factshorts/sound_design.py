"""Dynamic Rhythmic Sound Design & SFX Engine.

Generates beat-synchronized cinematic sound effects (Hook sub-booms, transition whooshes,
and reveal impact hits) aligned to spoken sentence timestamps.
"""
from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

from .config import Config, get_config
from .utils import module_logger, run_cmd_async

log = module_logger("sound_design")


async def ensure_sfx_samples(sfx_dir: Path) -> dict[str, Path]:
    """Ensure standard CC0 sound effect samples exist; synthesizes them via FFmpeg if missing."""
    sfx_dir.mkdir(parents=True, exist_ok=True)
    samples: dict[str, Path] = {
        "boom": sfx_dir / "sub_boom.wav",
        "whoosh": sfx_dir / "whoosh.wav",
        "impact": sfx_dir / "impact_hit.wav",
    }

    # 1. Sub-Bass Boom (48Hz deep cinematic sub-impact with quick punch & decay)
    if not samples["boom"].exists() or samples["boom"].stat().st_size < 1000:
        cmd = [
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-f", "lavfi",
            "-i", "sine=frequency=52:duration=1.4",
            "-af", "volume=1.8,afade=t=in:ss=0:d=0.03,afade=t=out:st=0.1:d=1.3",
            "-c:a", "pcm_s16le", str(samples["boom"]),
        ]
        try:
            await run_cmd_async(cmd, timeout=30)
        except Exception as exc:  # noqa: BLE001
            log.warning("could not synthesize sub_boom.wav: %s", exc)

    # 2. Transition Whoosh (bandpass filtered white noise sweep)
    if not samples["whoosh"].exists() or samples["whoosh"].stat().st_size < 1000:
        cmd = [
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-f", "lavfi",
            "-i", "anoisesrc=d=0.42:c=white:r=48000",
            "-af", "bandpass=f=1100:w=700,volume=1.2,afade=t=in:ss=0:d=0.15,afade=t=out:st=0.15:d=0.27",
            "-c:a", "pcm_s16le", str(samples["whoosh"]),
        ]
        try:
            await run_cmd_async(cmd, timeout=30)
        except Exception as exc:  # noqa: BLE001
            log.warning("could not synthesize whoosh.wav: %s", exc)

    # 3. Climax Impact Hit (dual-layer punch)
    if not samples["impact"].exists() or samples["impact"].stat().st_size < 1000:
        cmd = [
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-f", "lavfi",
            "-i", "sine=frequency=75:duration=1.2",
            "-af", "volume=2.0,afade=t=in:ss=0:d=0.02,afade=t=out:st=0.08:d=1.12",
            "-c:a", "pcm_s16le", str(samples["impact"]),
        ]
        try:
            await run_cmd_async(cmd, timeout=30)
        except Exception as exc:  # noqa: BLE001
            log.warning("could not synthesize impact_hit.wav: %s", exc)

    return samples


async def build_sfx_track(
    sentence_timings: list[tuple[float, float, str]],
    total_duration: float,
    workdir: Path,
    cfg: Config | None = None,
) -> Path | None:
    """Build a complete, synchronized SFX audio track for the video duration."""
    cfg = cfg or get_config()
    sfx_dir = cfg.cache_dir / "sfx"
    samples = await ensure_sfx_samples(sfx_dir)

    valid_samples = {k: v for k, v in samples.items() if v.exists() and v.stat().st_size > 1000}
    if not valid_samples:
        log.warning("no valid SFX samples available, skipping sound design track")
        return None

    # Determine SFX placement cue points
    cues: list[tuple[float, str]] = []

    # Cue 1: Hook opening impact at t=0.05s
    if "boom" in valid_samples:
        cues.append((0.05, "boom"))

    # Cue 2: Scene transitions between sentences
    climax_index = max(1, int(len(sentence_timings) * 0.70))  # 70% into the video
    for idx, seg in enumerate(sentence_timings):
        start_t = seg[1]
        if idx == 0:
            continue
        if idx == climax_index and "impact" in valid_samples:
            cues.append((round(start_t, 3), "impact"))
        elif "whoosh" in valid_samples:
            # Place whoosh 0.15s before cut point for leading transition
            whoosh_t = max(0.1, start_t - 0.15)
            cues.append((round(whoosh_t, 3), "whoosh"))

    if not cues:
        return None
 
    workdir.mkdir(parents=True, exist_ok=True)
    out_sfx = workdir / "sfx_track.wav"
    inputs = []
    filter_parts = []

    for i, (t_offset, sfx_key) in enumerate(cues):
        sfx_path = valid_samples[sfx_key].resolve()
        inputs.extend(["-i", str(sfx_path)])
        delay_ms = int(t_offset * 1000)
        # Apply adelay and volume balance
        vol = 0.55 if sfx_key == "whoosh" else 0.85
        filter_parts.append(f"[{i}:a]adelay={delay_ms}|{delay_ms},volume={vol}[sfx{i}]")

    mix_inputs = "".join(f"[sfx{i}]" for i in range(len(cues)))
    filter_graph = f"{';'.join(filter_parts)};{mix_inputs}amix=inputs={len(cues)}:normalize=0[out]"

    cmd = [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        *inputs,
        "-filter_complex", filter_graph,
        "-map", "[out]",
        "-t", f"{total_duration:.3f}",
        "-c:a", "pcm_s16le",
        str(out_sfx.resolve()),
    ]

    try:
        await run_cmd_async(cmd, timeout=60)
        if out_sfx.exists() and out_sfx.stat().st_size > 2000:
            log.info("rhythmic SFX track built (%d sound design cues) -> %s", len(cues), out_sfx.name)
            return out_sfx
    except Exception as exc:  # noqa: BLE001
        log.warning("failed to compile SFX track: %s", exc)

    return None
