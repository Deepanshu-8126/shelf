"""
Timeline Assembler & Master Documentary Video Renderer.
Orchestrates:
- Archival photo Ken Burns clips
- Animated Vox-style Newspaper Highlighter clips
- Sub-bass tension audio drone + marker scratch SFX + transition booms
- Kinetic documentary subtitles (ASS with drop shadow & margin protection)
- Outputs broadcast-grade 1080p MP4 (Vertical 9:16 or Horizontal 16:9)
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any


def generate_ass_subtitles(cues: list[dict[str, Any]], output_ass: Path, is_vertical: bool = True) -> Path:
    """
    Generates high-retention documentary ASS subtitles.
    Safe margins for YouTube Shorts / Reels UI (MarginV=260).
    """
    output_ass = Path(output_ass)
    output_ass.parent.mkdir(parents=True, exist_ok=True)

    play_res_x = 1080 if is_vertical else 1920
    play_res_y = 1920 if is_vertical else 1080
    font_size = 54 if is_vertical else 42
    margin_v = 300 if is_vertical else 100

    header = f"""[Script Info]
Title: Dark Case Files Subtitles
ScriptType: v4.00+
WrapStyle: 0
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.601
PlayResX: {play_res_x}
PlayResY: {play_res_y}

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: DocStyle,Arial,{font_size},&H00FFFFFF,&H0000FFFF,&H00000000,&H90000000,-1,0,0,0,100,100,1,0,1,3.5,2.0,2,60,60,{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    events = []
    for c in cues:
        # Format time to 0:00:00.00
        def fmt_time(sec: float) -> str:
            h = int(sec // 3600)
            m = int((sec % 3600) // 60)
            s = sec % 60
            return f"{h}:{m:02d}:{s:05.2f}"

        start_str = fmt_time(c["start"])
        end_str = fmt_time(c["end"])
        raw_text = c["text"].strip().upper()
        # Highlight first or key word with yellow tag \c&H00FFFF&
        words = raw_text.split(" ")
        if len(words) >= 3:
            # Highlight middle/key word
            mid = len(words) // 2
            words[mid] = f"{{\\c&H00FFFF&}}{words[mid]}{{\\c&HFFFFFF&}}"
            line = " ".join(words)
        else:
            line = raw_text

        events.append(f"Dialogue: 0,{start_str},{end_str},DocStyle,,0,0,0,,{line}")

    content = header + "\n".join(events) + "\n"
    output_ass.write_text(content, encoding="utf-8")
    print(f">> Generated ASS subtitles: {output_ass}")
    return output_ass


def assemble_documentary_video(
    scene_clips: list[Path],
    voice_audio: Path,
    cues: list[dict[str, Any]],
    output_master_video: Path,
    aspect_ratio: str = "vertical",
    sfx_assets_dir: Path | None = None,
) -> Path:
    """
    Concatenates visual scenes, mixes voice + background suspense drone + SFX,
    burns kinetic subtitles, and outputs master MP4.
    """
    output_master_video = Path(output_master_video)
    output_master_video.parent.mkdir(parents=True, exist_ok=True)
    temp_dir = output_master_video.parent / "temp"
    temp_dir.mkdir(parents=True, exist_ok=True)

    # 1. Create ffmpeg concat file for video clips
    concat_txt = temp_dir / "concat_list.txt"
    lines = [f"file '{clip.resolve().as_posix()}'" for clip in scene_clips]
    concat_txt.write_text("\n".join(lines), encoding="utf-8")

    # Probe voice audio duration
    probe_cmd = [
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(voice_audio)
    ]
    res = subprocess.run(probe_cmd, capture_output=True, text=True)
    total_voice_duration = float(res.stdout.strip() or "15.0")
    print(f">> Total Voiceover Duration: {total_voice_duration:.2f}s")

    # 2. Generate ASS Subtitles
    ass_path = temp_dir / "subtitles.ass"
    generate_ass_subtitles(cues, ass_path, is_vertical=(aspect_ratio == "vertical"))

    # 3. Concatenate video scenes without audio first
    raw_video_concat = temp_dir / "raw_visuals.mp4"
    cmd_concat = [
        "ffmpeg", "-hide_banner", "-loglevel", "warning", "-y",
        "-f", "concat", "-safe", "0", "-i", str(concat_txt),
        "-c", "copy",
        str(raw_video_concat)
    ]
    subprocess.run(cmd_concat, check=True)
    print(f">> Concatenated visual scenes: {raw_video_concat}")

    # 4. Sound Mixing: Voice (1.0) + Tension Drone (0.20) + Subtitles burned
    # Audio mixing filtergraph
    drone_path = (Path(__file__).resolve().parent / "assets/sfx/drone_suspense.wav")
    marker_path = (Path(__file__).resolve().parent / "assets/sfx/marker_sweep.wav")
    
    # Check available SFX
    has_drone = drone_path.exists()
    
    # We burn subtitles via ass filter
    # Note: On Windows paths in ffmpeg filters, colons must be escaped or use relative/forward slash
    ass_filter_path = ass_path.resolve().as_posix().replace(":", "\\:")

    if has_drone:
        # Inputs:
        # 0: video (raw_visuals)
        # 1: voiceover
        # 2: tension drone
        ffmpeg_mix_cmd = [
            "ffmpeg", "-hide_banner", "-loglevel", "warning", "-y",
            "-i", str(raw_video_concat),
            "-i", str(voice_audio),
            "-stream_loop", "-1", "-i", str(drone_path),
            "-filter_complex",
            f"[0:v]subtitles='{ass_filter_path}'[v];"
            f"[1:a]volume=1.0[a_voice];"
            f"[2:a]volume=0.22[a_drone];"
            f"[a_voice][a_drone]amix=inputs=2:duration=first:dropout_transition=2[a]",
            "-map", "[v]",
            "-map", "[a]",
            "-t", f"{total_voice_duration + 0.5:.2f}",
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "18",
            "-c:a", "aac",
            "-b:a", "192k",
            str(output_master_video)
        ]
    else:
        ffmpeg_mix_cmd = [
            "ffmpeg", "-hide_banner", "-loglevel", "warning", "-y",
            "-i", str(raw_video_concat),
            "-i", str(voice_audio),
            "-filter_complex",
            f"[0:v]subtitles='{ass_filter_path}'[v]",
            "-map", "[v]",
            "-map", "1:a",
            "-t", f"{total_voice_duration + 0.5:.2f}",
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "18",
            "-c:a", "aac",
            "-b:a", "192k",
            str(output_master_video)
        ]

    subprocess.run(ffmpeg_mix_cmd, check=True)
    print(f">> Master Documentary Video Rendered: {output_master_video}")
    return output_master_video
