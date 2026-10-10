"""
HyperFrames Vox Studio Engine for Fleet Channels.
Provides programmatic, reusable Vox-style motion graphic rendering.
Uses official HeyGen HyperFrames components (vox-annotate, yt-circle-pointer, etc.)
"""
from __future__ import annotations
import os
import sys
import json
import shutil
import tempfile
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional

STUDIO_DIR = Path(__file__).resolve().parent
WORKSPACE_ROOT = STUDIO_DIR.parent.parent


def render_vox_scene(
    text: str,
    keyword: str,
    note: str = "",
    style: str = "circle",      # "circle" | "highlight" | "underline" | "scribble"
    accent: str = "green",      # "green" | "blue" | "violet" | "red" | "yellow"
    duration: float = 4.0,
    output_path: Optional[Path] = None
) -> Path:
    """
    Renders a single Vox-style annotated scene into 1080x1920 60fps MP4.
    """
    if output_path is None:
        output_path = STUDIO_DIR / f"vox_scene_{int(duration)}s.mp4"
    else:
        output_path = Path(output_path).resolve()

    output_path.parent.mkdir(parents=True, exist_ok=True)

    vars_payload = {
        "text": text.strip(),
        "keyword": keyword.strip(),
        "note": note.strip(),
        "style": style,
        "accent": accent,
        "draw_at": 0.8
    }

    vars_file = STUDIO_DIR / "current_vars.json"
    with open(vars_file, "w", encoding="utf-8") as f:
        json.dump(vars_payload, f, indent=2, ensure_ascii=False)

    cmd = [
        "npx", "-y", "hyperframes", "render", ".",
        f"--variables-file={vars_file.name}",
        "--experimental-fast-capture=false",
        "-o", str(output_path)
    ]

    print(f"🎬 [HYPERFRAMES] Rendering Vox Scene: '{keyword}' ({style})...", flush=True)
    res = subprocess.run(
        cmd,
        cwd=str(STUDIO_DIR),
        capture_output=True,
        text=True,
        shell=True
    )

    if res.returncode != 0:
        print(f"⚠️ HyperFrames render error:\n{res.stderr}\n{res.stdout}", flush=True)
        raise RuntimeError(f"HyperFrames render failed: {res.stderr[:200]}")

    print(f"✅ Vox Scene ready: {output_path} ({output_path.stat().st_size / 1024:.1f} KB)", flush=True)
    return output_path


def render_vox_full_short(
    scenes: List[Dict[str, Any]],
    audio_path: Optional[Path] = None,
    final_output_path: Optional[Path] = None
) -> Path:
    """
    Renders multiple Vox scenes sequentially and stitches them with audio.
    scenes format:
    [
        {"text": "...", "keyword": "...", "note": "...", "style": "circle", "accent": "green"},
        {"text": "...", "keyword": "...", "note": "...", "style": "highlight", "accent": "yellow"},
    ]
    """
    if final_output_path is None:
        final_output_path = STUDIO_DIR / "final_vox_short.mp4"
    else:
        final_output_path = Path(final_output_path).resolve()

    temp_vids: List[Path] = []
    
    try:
        for idx, sc in enumerate(scenes):
            sc_out = STUDIO_DIR / f"temp_scene_{idx}.mp4"
            rendered = render_vox_scene(
                text=sc.get("text", ""),
                keyword=sc.get("keyword", ""),
                note=sc.get("note", ""),
                style=sc.get("style", "circle"),
                accent=sc.get("accent", "green"),
                duration=sc.get("duration", 4.0),
                output_path=sc_out
            )
            temp_vids.append(rendered)

        # Concatenate using FFmpeg concat demuxer
        concat_txt = STUDIO_DIR / "concat_list.txt"
        with open(concat_txt, "w", encoding="utf-8") as f:
            for tv in temp_vids:
                # FFmpeg file path format
                safe_path = str(tv).replace("\\", "/")
                f.write(f"file '{safe_path}'\n")

        concat_mp4 = STUDIO_DIR / "merged_visuals.mp4"
        ffmpeg_cmd = [
            "ffmpeg", "-y", "-f", "concat", "-safe", "0",
            "-i", str(concat_txt),
            "-c", "copy",
            str(concat_mp4)
        ]
        subprocess.run(ffmpeg_cmd, check=True, capture_output=True)

        if audio_path and Path(audio_path).exists():
            print(f"🎵 [HYPERFRAMES] Muxing Voiceover Audio: {audio_path.name}...", flush=True)
            mux_cmd = [
                "ffmpeg", "-y",
                "-i", str(concat_mp4),
                "-i", str(audio_path),
                "-c:v", "copy",
                "-c:a", "aac",
                "-shortest",
                str(final_output_path)
            ]
            subprocess.run(mux_cmd, check=True, capture_output=True)
        else:
            shutil.copy(concat_mp4, final_output_path)

        print(f"🚀 [HYPERFRAMES] Final Vox Short Rendered: {final_output_path}", flush=True)
        return final_output_path

    finally:
        # Cleanup temp clips
        for tv in temp_vids:
            if tv.exists():
                try:
                    tv.unlink()
                except Exception:
                    pass
        for temp_f in [STUDIO_DIR / "concat_list.txt", STUDIO_DIR / "merged_visuals.mp4"]:
            if temp_f.exists():
                try:
                    temp_f.unlink()
                except Exception:
                    pass


if __name__ == "__main__":
    test_scene = render_vox_scene(
        text="1962: FBI Top Secret Document Unsealed",
        keyword="Top Secret",
        note="CLASSIFIED",
        style="circle",
        accent="green"
    )
    print("Standalone test successful:", test_scene)
