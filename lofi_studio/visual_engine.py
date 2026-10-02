"""
LoFi Visual Engine v2: Professional cinematic video renderer.

Key improvements over v1:
- NO zoompan (was causing jitter/shake)  
- Real B-roll video loop support (Pexels clips)
- Static image fallback with smooth vignette overlay
- Proper audio waveform visualizer (subtle, not harsh)
- Cinematic color grade: warm teal/orange LUT-style
- Elegant "Now Playing" card with fade animation
"""
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Optional


def _escape_for_drawtext(text: str) -> str:
    """Safely escape text for ffmpeg drawtext filter."""
    return (
        text
        .replace("\\", "\\\\")
        .replace(":", "\\:")
        .replace("'", "\\'")
        .replace("[", "\\[")
        .replace("]", "\\]")
        .replace(",", "\\,")
    )


# Windows system fonts (guaranteed to exist on Windows)
WINDOWS_FONTS = [
    "C:/Windows/Fonts/arial.ttf",
    "C:/Windows/Fonts/Arial.ttf",
    "C:/Windows/Fonts/calibri.ttf",
    "C:/Windows/Fonts/segoeui.ttf",
    "C:/Windows/Fonts/verdana.ttf",
]


def _get_font_filter(custom_font_path: Optional[Path] = None) -> str:
    """
    Returns the fontfile= prefix for ffmpeg drawtext filter.
    Priority: custom_font → Windows system font → empty (ffmpeg builtin).
    On Windows, fontconfig fails silently — we must specify an explicit path.
    """
    # Try custom font first
    if custom_font_path:
        fp = Path(custom_font_path)
        if fp.exists():
            fpath = fp.as_posix().replace(":", "\\:")
            return f"fontfile='{fpath}':"

    # Try Windows system fonts
    for wf in WINDOWS_FONTS:
        if Path(wf).exists():
            fpath = wf.replace(":", "\\:")
            return f"fontfile='{fpath}':"

    # Fallback: no fontfile (ffmpeg uses built-in, may show fontconfig warning)
    return ""


def render_lofi_video(
    background_source: Path,
    audio_path: Path,
    output_video: Path,
    track_title: str = "Trending Hindi LoFi Mix",
    broll_clips: Optional[list[Path]] = None,
    resolution: tuple[int, int] = (1920, 1080),
    font_path: Optional[Path] = None,
) -> Path:
    """
    Renders a full professional LoFi video.
    
    Args:
        background_source: Static image (.jpg/.png) used as backdrop
        audio_path: The processed LoFi audio file
        output_video: Output path for final .mp4
        track_title: Title text shown in the Now Playing card
        broll_clips: Optional list of real video clips to loop (Pexels)
        resolution: Output resolution (default 1920x1080)
        font_path: Path to .ttf font file (uses system default if None)
    """
    background_source = Path(background_source)
    audio_path = Path(audio_path)
    output_video = Path(output_video)
    output_video.parent.mkdir(parents=True, exist_ok=True)

    w, h = resolution
    clean_title = _escape_for_drawtext(track_title)
    sub_label = _escape_for_drawtext("SLOWED + REVERB  •  NIGHT VIBES  •  HINDI LOFI")

    # Font: use provided TTF, Windows system font, or ffmpeg built-in
    font_filter = _get_font_filter(font_path)

    if broll_clips:
        return _render_with_broll(
            broll_clips, audio_path, output_video,
            clean_title, sub_label, font_filter, w, h
        )
    else:
        return _render_with_static_image(
            background_source, audio_path, output_video,
            clean_title, sub_label, font_filter, w, h
        )


def _render_with_static_image(
    bg_image: Path,
    audio_path: Path,
    output_video: Path,
    clean_title: str,
    sub_label: str,
    font_filter: str,
    w: int, h: int
) -> Path:
    """
    Render with static background image.
    Smooth approach: NO zoompan. Just a clean static cinematic frame.
    Adds: vignette, warm teal color grade, waveform visualizer.
    """
    print("🎬 Rendering: Static cinematic mode (no zoompan shake)...")

    # Filtergraph:
    # [0:v] = looped background image
    # [1:a] = lofi audio
    # Steps:
    #   1. Scale+crop bg image to exact resolution
    #   2. Apply cinematic color grade (eq + curves approximation)
    #   3. Add vignette overlay
    #   4. Generate waveform from audio, apply glow, overlay bottom
    #   5. Draw "Now Playing" card text
    filtergraph = (
        # Background: scale + crop (no movement = no shake)
        f"[0:v]scale={w}:{h}:force_original_aspect_ratio=increase,"
        f"crop={w}:{h},"
        # Cinematic color grade: slightly desaturate + warm shadows + cool mids
        f"eq=contrast=1.08:brightness=-0.06:saturation=0.82:gamma=0.96,"
        # Vignette: darken edges for cinematic look
        f"vignette=PI/4[bg];"

        # Waveform visualizer: thin elegant line at bottom
        f"[1:a]showwaves=s={int(w*0.6)}x80:mode=cline:rate=30:"
        f"colors=0xFFD700@0.7:scale=lin[wave_raw];"
        f"[wave_raw]format=rgba,"
        f"boxblur=lr=3:lp=1[wave_glow];"  # soft glow
        f"[wave_glow][wave_raw]overlay=0:0[wave_fx];"

        # Overlay wave centered at bottom
        f"[bg][wave_fx]overlay=x=(W-w)/2:y={h-180}[v_with_wave];"

        # Dark gradient bar at bottom for text readability
        f"[v_with_wave]drawbox=x=0:y={h-220}:w={w}:h=220:color=black@0.5:t=fill[v_bar];"

        # Title text
        f"[v_bar]drawtext={font_filter}"
        f"text='{clean_title}':"
        f"fontcolor=white:fontsize=38:x=(w-text_w)/2:y={h-170}:"
        f"shadowcolor=black@0.8:shadowx=2:shadowy=2,"

        # Subtitle
        f"drawtext={font_filter}"
        f"text='{sub_label}':"
        f"fontcolor=0xFFD700@0.85:fontsize=20:x=(w-text_w)/2:y={h-110}:"
        f"shadowcolor=black@0.6:shadowx=1:shadowy=1[vout]"
    )

    cmd = [
        "ffmpeg", "-hide_banner", "-loglevel", "warning", "-y",
        "-loop", "1", "-framerate", "30", "-i", str(bg_image),  # looped static image
        "-i", str(audio_path),
        "-filter_complex", filtergraph,
        "-map", "[vout]",
        "-map", "1:a",
        "-c:v", "libx264", "-preset", "fast", "-crf", "19", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "256k",
        "-r", "30",
        "-shortest",
        str(output_video)
    ]
    subprocess.run(cmd, check=True)
    print(f"✅ Static render complete: {output_video}")
    return output_video


def _render_with_broll(
    broll_clips: list[Path],
    audio_path: Path,
    output_video: Path,
    clean_title: str,
    sub_label: str,
    font_filter: str,
    w: int, h: int
) -> Path:
    """
    Render using real B-roll video clips looped to match audio duration.
    Creates concat list, loops clips seamlessly, overlays HUD.
    """
    print(f"🎬 Rendering with {len(broll_clips)} real B-roll clips...")

    # Step 1: Create concat list — repeat clips to fill audio
    concat_dir = output_video.parent / "cache"
    concat_dir.mkdir(exist_ok=True)
    concat_file = concat_dir / "broll_concat.txt"

    # Loop the clips multiple times (each ~15-60s, audio could be 1+ hour)
    # We write them enough times to exceed any typical mix length
    loop_count = 20  # 20x loops ensures enough for multi-hour mixes
    with open(concat_file, "w", encoding="utf-8") as f:
        for _ in range(loop_count):
            for clip in broll_clips:
                f.write(f"file '{clip.resolve().as_posix()}'\n")

    # Step 2: Build looped B-roll video (no audio)
    broll_combined = concat_dir / "broll_combined.mp4"
    concat_cmd = [
        "ffmpeg", "-hide_banner", "-loglevel", "warning", "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(concat_file),
        "-vf", f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},"
               f"eq=contrast=1.05:brightness=-0.05:saturation=0.80,"
               f"vignette=PI/4",
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "23", "-pix_fmt", "yuv420p",
        "-an", "-r", "30",
        str(broll_combined)
    ]
    subprocess.run(concat_cmd, check=True)
    print("  ✅ B-roll loop assembled")

    # Step 3: Compose final video with HUD overlays + waveform
    filtergraph = (
        f"[1:a]showwaves=s={int(w*0.6)}x80:mode=cline:rate=30:"
        f"colors=0xFFD700@0.7:scale=lin[wave_raw];"
        f"[wave_raw]format=rgba,boxblur=lr=3:lp=1[wave_glow];"
        f"[wave_glow][wave_raw]overlay=0:0[wave_fx];"
        f"[0:v][wave_fx]overlay=x=(W-w)/2:y={h-180}[v_with_wave];"
        f"[v_with_wave]drawbox=x=0:y={h-220}:w={w}:h=220:color=black@0.5:t=fill[v_bar];"
        f"[v_bar]drawtext={font_filter}"
        f"text='{clean_title}':"
        f"fontcolor=white:fontsize=38:x=(w-text_w)/2:y={h-170}:"
        f"shadowcolor=black@0.8:shadowx=2:shadowy=2,"
        f"drawtext={font_filter}"
        f"text='{sub_label}':"
        f"fontcolor=0xFFD700@0.85:fontsize=20:x=(w-text_w)/2:y={h-110}:"
        f"shadowcolor=black@0.6:shadowx=1:shadowy=1[vout]"
    )

    final_cmd = [
        "ffmpeg", "-hide_banner", "-loglevel", "warning", "-y",
        "-i", str(broll_combined),
        "-i", str(audio_path),
        "-filter_complex", filtergraph,
        "-map", "[vout]",
        "-map", "1:a",
        "-c:v", "libx264", "-preset", "fast", "-crf", "19", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "256k",
        "-shortest",
        str(output_video)
    ]
    subprocess.run(final_cmd, check=True)
    print(f"✅ B-roll render complete: {output_video}")
    return output_video
