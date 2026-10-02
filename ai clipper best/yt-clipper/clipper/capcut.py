"""Step 7 - emit an editable CapCut / Jianying draft instead of (or next to) an mp4.

Writes <drafts>/<name>/draft_content.json + draft_meta_info.json. Drop the folder in
CapCut's draft dir and it shows up in the app, fully editable:
  Windows : %LOCALAPPDATA%\\CapCut\\User Data\\Projects\\com.lveditor.draft
  macOS   : ~/Movies/CapCut/User Data/Projects/com.lveditor.draft
Timings in CapCut are MICROSECONDS. This writes the subset CapCut needs
(video + audio + text tracks); the app fills in defaults on open.
"""
from __future__ import annotations

import json
import time
import uuid
from pathlib import Path

from .config import settings

US = 1_000_000


def _id() -> str:
    return str(uuid.uuid4()).upper()


def _seg(material_id: str, start_us: int, dur_us: int, src_start_us: int = 0) -> dict:
    return {
        "id": _id(),
        "material_id": material_id,
        "target_timerange": {"start": int(start_us), "duration": int(dur_us)},
        "source_timerange": {"start": int(src_start_us), "duration": int(dur_us)},
        "speed": 1.0,
        "volume": 1.0,
        "visible": True,
        "clip": {"alpha": 1.0, "rotation": 0.0,
                 "scale": {"x": 1.0, "y": 1.0}, "transform": {"x": 0.0, "y": 0.0},
                 "flip": {"horizontal": False, "vertical": False}},
        "extra_material_refs": [],
        "enable_adjust": True,
    }


def _text_material(content: str, color=(1.0, 1.0, 1.0)) -> dict:
    return {
        "id": _id(),
        "type": "text",
        "content": json.dumps({
            "text": content,
            "styles": [{"fill": {"content": {"solid": {"color": list(color)}}},
                        "size": 12, "bold": True, "range": [0, len(content)]}],
        }, ensure_ascii=False),
        "font_size": 12.0,
        "text_color": "#FFFFFF",
        "border_color": "#000000",
        "has_shadow": True,
        "alignment": 1,
        "line_spacing": 0.02,
    }


def build_draft(clip_video: str | Path, duration_s: float, name: str,
                words: list[dict] | None = None, voice_audio: str | Path | None = None,
                drafts_dir: str | Path | None = None, group_words: int = 4) -> Path:
    """Create one CapCut draft folder for a single clip. Returns the folder path."""
    from .captions import chunk_words

    drafts_dir = Path(drafts_dir or settings.work_dir / "capcut")
    folder = drafts_dir / name
    folder.mkdir(parents=True, exist_ok=True)
    dur_us = int(duration_s * US)

    vid = {"id": _id(), "type": "video", "path": str(Path(clip_video).resolve()),
           "material_name": Path(clip_video).name, "duration": dur_us,
           "width": settings.width, "height": settings.height, "has_audio": True}
    materials = {"videos": [vid], "audios": [], "texts": [], "stickers": [],
                 "effects": [], "transitions": [], "canvases": [], "speeds": []}
    tracks = [{"id": _id(), "type": "video", "attribute": 0, "flag": 0,
               "segments": [_seg(vid["id"], 0, dur_us)]}]

    if voice_audio:
        aud = {"id": _id(), "type": "extract_music",
               "path": str(Path(voice_audio).resolve()),
               "name": Path(voice_audio).name, "duration": dur_us}
        materials["audios"].append(aud)
        tracks.append({"id": _id(), "type": "audio", "attribute": 0, "flag": 0,
                       "segments": [_seg(aud["id"], 0, dur_us)]})

    if words:
        text_segs = []
        for group in chunk_words(words, group_words):
            m = _text_material(" ".join(w["word"].upper() for w in group))
            materials["texts"].append(m)
            s = int(group[0]["start"] * US)
            d = max(int((group[-1]["end"] - group[0]["start"]) * US), 200_000)
            seg = _seg(m["id"], s, d, 0)
            seg["clip"]["transform"] = {"x": 0.0, "y": -0.28}  # lower third
            text_segs.append(seg)
        tracks.append({"id": _id(), "type": "text", "attribute": 0, "flag": 0,
                       "segments": text_segs})

    draft = {
        "id": _id(),
        "version": 360000,
        "new_version": "110.0.0",
        "duration": dur_us,
        "fps": float(settings.fps),
        "canvas_config": {"width": settings.width, "height": settings.height, "ratio": "9:16"},
        "materials": materials,
        "tracks": tracks,
        "platform": {"app_source": "cc", "app_version": "5.9.0", "os": "windows"},
        "config": {"adjust_max_index": 1, "maintrack_adsorb": True, "record_audio_last_index": 1},
        "keyframes": {"adjusts": [], "audios": [], "texts": [], "videos": []},
        "extra_info": None,
    }
    now = int(time.time() * US)
    meta = {"draft_id": draft["id"], "draft_name": name, "draft_fold_path": str(folder.resolve()),
            "tm_draft_create": now, "tm_draft_modified": now,
            "draft_timeline_materials_size_": 0, "draft_removable_storage_device": "",
            "draft_root_path": str(drafts_dir.resolve())}

    (folder / "draft_content.json").write_text(json.dumps(draft, ensure_ascii=False, indent=1))
    (folder / "draft_meta_info.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1))
    return folder
