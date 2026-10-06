"""
Cinematic Ken Burns Motion Engine & Assembly (OpenReels / Lemmino Architecture).
Applies frame-accurate zoom/pan transformations and dark documentary color grading to still images.
"""
from __future__ import annotations

import os
import random
import subprocess
from pathlib import Path

# 7 Distinct OpenReels Camera Motions
MOTIONS: dict[str, str] = {
    "slow_zoom_in":   "z='min(zoom+0.0015,1.5)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'",
    "slow_zoom_out":  "z='if(lte(zoom,1.0),1.5,max(zoom-0.0015,1.0))':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'",
    "pan_left":       "z='1.3':x='(iw-iw/zoom)/2*(1-on/total)':y='ih/2-(ih/zoom/2)'",
    "pan_right":      "z='1.3':x='(iw-iw/zoom)/2*(on/total)':y='ih/2-(ih/zoom/2)'",
    "pan_up":         "z='1.3':x='iw/2-(iw/zoom/2)':y='(ih-ih/zoom)/2*(1-on/total)'",
    "pan_down":       "z='1.3':x='iw/2-(iw/zoom/2)':y='(ih-ih/zoom)/2*(on/total)'",
    "drift":          "z='min(zoom+0.001,1.4)':x='iw/3':y='ih/3'",
}

DARK_COLOR_GRADE = "eq=contrast=1.2:saturation=0.7:brightness=-0.05,colorbalance=rs=-0.05:bs=0.1"


def create_ken_burns_clip(
    image_path: Path | str,
    output_path: Path | str,
    duration: float = 4.0,
    fps: int = 30,
    motion_type: str | None = None,
) -> Path:
    """Creates a 1080x1920 9:16 vertical Ken Burns clip with dark noir color grading."""
    img_p = Path(image_path)
    out_p = Path(output_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)

    motion = motion_type if motion_type in MOTIONS else random.choice(list(MOTIONS.keys()))
    frames = int(duration * fps)
    m_expr = MOTIONS[motion]

    vf = (
        f"scale=3840:2160:force_original_aspect_ratio=increase,"
        f"crop=3840:2160,"
        f"zoompan={m_expr}:d={frames}:s=1080x1920:fps={fps},"
        f"{DARK_COLOR_GRADE},"
        f"format=yuv420p"
    )

    cmd = [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-loop", "1", "-i", str(img_p),
        "-vf", vf,
        "-t", f"{duration:.3f}",
        "-c:v", "libx264", "-preset", "fast", "-crf", "18",
        "-pix_fmt", "yuv420p",
        str(out_p)
    ]

    subprocess.run(cmd, check=True)
    return out_p


def assemble_video(
    clips: list[Path | str],
    audio_path: Path | str,
    output_path: Path | str,
    captions_path: Path | str | None = None,
    workdir: Path | None = None,
) -> Path:
    """Assembles all clips, background audio, and subtitles into a publish-ready 9:16 Short."""
    out_p = Path(output_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    temp_dir = workdir or out_p.parent
    temp_dir.mkdir(parents=True, exist_ok=True)

    concat_file = temp_dir / "concat_list.txt"
    with open(concat_file, "w", encoding="utf-8") as f:
        for c in clips:
            c_str = str(Path(c).resolve()).replace("\\", "/")
            f.write(f"file '{c_str}'\n")

    cmd = [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-f", "concat", "-safe", "0", "-i", str(concat_file),
        "-i", str(audio_path),
    ]

    filters = []
    if captions_path and Path(captions_path).exists():
        c_path_clean = str(Path(captions_path).resolve()).replace("\\", "/").replace(":", r"\:")
        filters.append(f"ass='{c_path_clean}'")

    if filters:
        cmd += ["-vf", ",".join(filters)]

    cmd += [
        "-c:v", "libx264", "-crf", "18", "-preset", "fast",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        str(out_p)
    ]

    subprocess.run(cmd, check=True)
    return out_p
