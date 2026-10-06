from __future__ import annotations

import hashlib
import json
import re
import shutil
import statistics
import subprocess
import uuid
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo
from typing import Any
from urllib.parse import urlparse

from .adapters import distribution_variants
from .config import DATA_DIR, PACKAGES_DIR
from .db import create_job, get_channel, update_job
from .renderer import _ffmpeg_executable, _voiceover

GAME_TITLE = "Grand Theft Auto VI"
GAME_RELEASE_DATE = date(2026, 11, 19)
SOURCE_DIR = DATA_DIR / "gaming_sources"
ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".mov", ".mkv", ".webm", ".m4v"}
MAX_SOURCE_BYTES = 2 * 1024 * 1024 * 1024
MAX_CLIP_SECONDS = 60
GAME_CAPTION_STYLES = {"static_srt", "kinetic_karaoke"}


def _local_today() -> date:
    return datetime.now(ZoneInfo("Asia/Kolkata")).date()


def list_local_sources() -> list[dict[str, Any]]:
    """List local source files only; never fetch or download a remote video."""
    SOURCE_DIR.mkdir(parents=True, exist_ok=True)
    root = SOURCE_DIR.resolve()
    result: list[dict[str, Any]] = []
    for path in sorted(SOURCE_DIR.iterdir(), key=lambda p: p.name.lower()):
        try:
            resolved = path.resolve(strict=True)
            if resolved.parent != root or not resolved.is_file() or resolved.suffix.lower() not in ALLOWED_VIDEO_EXTENSIONS:
                continue
            size = resolved.stat().st_size
            if size <= 0 or size > MAX_SOURCE_BYTES:
                continue
            result.append({"name": path.name, "extension": resolved.suffix.lower(), "size_bytes": size})
        except (OSError, RuntimeError):
            continue
    return result


def _local_source(filename: str) -> Path:
    name = str(filename or "").strip()
    if not name or name in {".", ".."} or Path(name).name != name or "/" in name or "\\" in name:
        raise ValueError("Choose a video file from data/gaming_sources; remote URLs and paths are not accepted.")
    if Path(name).suffix.lower() not in ALLOWED_VIDEO_EXTENSIONS:
        raise ValueError("Use a local MP4, MOV, MKV, WebM or M4V source file.")
    root = SOURCE_DIR.resolve()
    candidate = (SOURCE_DIR / name).resolve()
    if candidate.parent != root or not candidate.is_file():
        raise ValueError("Source file not found. Copy an owned or explicitly licensed clip into data/gaming_sources/.")
    if candidate.stat().st_size > MAX_SOURCE_BYTES:
        raise ValueError("Source file exceeds the 2 GB local-processing limit.")
    return candidate


def _source_duration_seconds(source: Path) -> float:
    try:
        import cv2
    except ImportError as exc:
        raise RuntimeError("Gaming clip processing needs OpenCV; install requirements.txt.") from exc
    capture = cv2.VideoCapture(str(source))
    if not capture.isOpened():
        capture.release()
        raise ValueError("OpenCV could not read this local video. Try an MP4/MOV file with a supported codec.")
    fps = float(capture.get(cv2.CAP_PROP_FPS) or 0)
    frames = float(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    capture.release()
    duration = frames / fps if fps > 0 and frames > 0 else 0.0
    if duration <= 0:
        raise ValueError("Could not read source duration from this local video.")
    return duration


def suggest_local_moments(filename: str) -> dict[str, Any]:
    """Rank abrupt visual-change windows in a local owned/authorized video; not semantic event detection."""
    source = _local_source(filename)
    try:
        import cv2
    except ImportError as exc:
        raise RuntimeError("Local moment suggestions need OpenCV; install requirements.txt.") from exc
    capture = cv2.VideoCapture(str(source))
    if not capture.isOpened():
        capture.release()
        raise ValueError("OpenCV could not read this local video. Try an MP4/MOV file with a supported codec.")
    fps = float(capture.get(cv2.CAP_PROP_FPS) or 0)
    frame_count = float(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    duration = frame_count / fps if fps > 0 and frame_count > 0 else 0.0
    if duration <= 0:
        capture.release()
        raise ValueError("Could not read source duration; moment suggestions are unavailable for this file.")
    scan_duration = min(duration, 900.0)
    step = 0.75
    previous = None
    changes: list[tuple[float, float]] = []
    position = 0.0
    while position < scan_duration:
        capture.set(cv2.CAP_PROP_POS_MSEC, position * 1000.0)
        ok, frame = capture.read()
        if ok:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            small = cv2.resize(gray, (64, 36), interpolation=cv2.INTER_AREA)
            if previous is not None:
                score = float(cv2.absdiff(previous, small).mean()) / 255.0
                changes.append((position, score))
            previous = small
        position += step
    capture.release()
    if not changes:
        return {"source_file": source.name, "duration_seconds": round(duration, 2), "scanned_seconds": round(scan_duration, 2), "candidates": [],
                "note": "No readable frame changes found. This detector does not recognize kills, explosions or other game events."}
    scores = [score for _, score in changes]
    threshold = max(0.04, statistics.mean(scores) + 0.8 * statistics.pstdev(scores), statistics.mean(scores) * 1.5)
    local_peaks = []
    for index, (at, score) in enumerate(changes):
        before = changes[index - 1][1] if index else -1
        after = changes[index + 1][1] if index + 1 < len(changes) else -1
        if score >= threshold and score >= before and score >= after:
            local_peaks.append((at, score))
    chosen: list[tuple[float, float]] = []
    for at, score in sorted(local_peaks, key=lambda item: item[1], reverse=True):
        if all(abs(at - existing_at) >= 5 for existing_at, _ in chosen):
            chosen.append((at, score))
        if len(chosen) >= 10:
            break
    candidates = []
    for at, score in sorted(chosen):
        start = max(0.0, at - 4.0)
        end = min(duration, start + 12.0)
        candidates.append({"start_seconds": round(start, 1), "end_seconds": round(end, 1),
                           "change_score": round(score, 3), "cue": "abrupt visual change · human review required"})
    note = "Candidates come only from local frame-change scores. This does not detect kills, explosions, chat spikes, or copyrighted-content permissions; watch the source and choose manually."
    if duration > scan_duration:
        note += " Only the first 15 minutes were scanned."
    return {"source_file": source.name, "duration_seconds": round(duration, 2),
            "scanned_seconds": round(scan_duration, 2), "candidates": candidates, "note": note}


def _srt_timestamp(seconds: float) -> str:
    milliseconds = max(0, int(round(float(seconds) * 1000)))
    hours, remainder = divmod(milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    whole_seconds, millis = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{whole_seconds:02d},{millis:03d}"


def clean_caption_lines(raw: list[str] | str) -> list[str]:
    if isinstance(raw, str):
        values = raw.splitlines()
    elif isinstance(raw, list):
        values = raw
    else:
        values = []
    lines: list[str] = []
    for value in values:
        line = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", str(value))
        line = re.sub(r"\s+", " ", line).strip().replace("-->", "→")
        if not line:
            continue
        if len(line) > 180:
            raise ValueError("Keep each Hinglish caption line under 180 characters.")
        lines.append(line)
        if len(lines) > 20:
            raise ValueError("Use at most 20 caption lines per clip.")
    return lines


def captions_to_srt(lines: list[str] | str, duration_seconds: float) -> str:
    clean = clean_caption_lines(lines)
    if not clean:
        raise ValueError("Add at least one manually reviewed Hinglish caption line.")
    duration = float(duration_seconds)
    if duration <= 0 or duration > MAX_CLIP_SECONDS:
        raise ValueError("Caption duration must be between 0 and 60 seconds.")
    interval = duration / len(clean)
    blocks = []
    for index, line in enumerate(clean, start=1):
        start = (index - 1) * interval
        end = duration if index == len(clean) else index * interval
        blocks.append(f"{index}\n{_srt_timestamp(start)} --> {_srt_timestamp(end)}\n{line}\n")
    return "\n".join(blocks)


def _ass_timestamp(centiseconds: int) -> str:
    value = max(0, int(centiseconds))
    hours, remainder = divmod(value, 360_000)
    minutes, remainder = divmod(remainder, 6_000)
    seconds, fraction = divmod(remainder, 100)
    return f"{hours}:{minutes:02d}:{seconds:02d}.{fraction:02d}"


def _ass_safe_word(word: str) -> str:
    # Prevent user-entered ASS override syntax from changing style or timing.
    return word.replace("\\", "／").replace("{", "｛").replace("}", "｝")


def captions_to_ass(lines: list[str] | str, duration_seconds: float) -> str:
    """Create a draft ASS karaoke sidecar with per-word highlight timing.

    Word durations are divided evenly within each manually supplied caption line;
    this is a visual draft, not ASR or speech alignment.
    """
    clean = clean_caption_lines(lines)
    if not clean:
        raise ValueError("Add at least one manually reviewed Hinglish caption line.")
    duration = float(duration_seconds)
    if duration <= 0 or duration > MAX_CLIP_SECONDS:
        raise ValueError("Caption duration must be between 0 and 60 seconds.")
    total_cs = int(round(duration * 100))
    if total_cs < len(clean):
        raise ValueError("Kinetic captions need at least 0.01 seconds per caption line.")

    events: list[str] = []
    for index, line in enumerate(clean):
        words = line.split()
        start_cs = int(round(index * total_cs / len(clean)))
        end_cs = total_cs if index == len(clean) - 1 else int(round((index + 1) * total_cs / len(clean)))
        line_cs = end_cs - start_cs
        if line_cs < len(words):
            raise ValueError("Kinetic caption timing is too short for the number of words in a line. Use fewer words or standard SRT.")
        base_cs, remainder = divmod(line_cs, len(words))
        timed_words = []
        for word_index, word in enumerate(words):
            word_cs = base_cs + (1 if word_index < remainder else 0)
            timed_words.append(f"{{\\kf{word_cs}}}{_ass_safe_word(word)}")
        events.append(
            f"Dialogue: 0,{_ass_timestamp(start_cs)},{_ass_timestamp(end_cs)},Kinetic,,0,0,0,,{' '.join(timed_words)}"
        )

    return "\n".join([
        "[Script Info]",
        "ScriptType: v4.00+",
        "PlayResX: 1080",
        "PlayResY: 1920",
        "ScaledBorderAndShadow: yes",
        "WrapStyle: 0",
        "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
        "Style: Kinetic,DejaVu Sans,64,&H0000D7FF,&H00FFFFFF,&H00101010,&H9905091C,-1,0,0,0,100,100,0,0,1,4,2,2,72,72,220,1",
        "",
        "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
        *events,
        "",
    ])


def _valid_url(value: str) -> str:
    url = str(value or "").strip()
    if not url:
        return ""
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc or parsed.username or parsed.password:
        raise ValueError("Source link must be a normal http(s) URL; it is stored only as provenance and is never downloaded.")
    return url[:1000]


def _probe_has_audio(ffmpeg: str, path: Path) -> bool:
    # ffmpeg prints stream details to stderr and exits nonzero when invoked without an output target.
    result = subprocess.run([ffmpeg, "-hide_banner", "-i", str(path)], capture_output=True,
                           text=True, timeout=45)
    return bool(re.search(r"Stream #\d+:\d+.*Audio:", result.stderr, flags=re.IGNORECASE))


def _ffmpeg_supports_ass(ffmpeg: str) -> bool:
    result = subprocess.run([ffmpeg, "-hide_banner", "-filters"], capture_output=True,
                           text=True, timeout=30)
    if result.returncode != 0:
        return False
    output = (result.stdout or "") + "\n" + (result.stderr or "")
    return any(len(fields := line.split()) >= 2 and fields[1] == "ass" for line in output.splitlines())


def _escape_filter_path(path: Path) -> str:
    value = str(path.resolve())
    value = value.replace("\\", "\\\\")
    for character in (":", "'", ",", "[", "]"):
        value = value.replace(character, "\\" + character)
    return f"'{value}'"


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _run(command: list[str], timeout: int = 900) -> None:
    result = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
    if result.returncode != 0:
        details = (result.stderr or result.stdout or "FFmpeg failed").strip().splitlines()
        tail = "\n".join(details[-8:])[:1800]
        raise RuntimeError(f"FFmpeg could not render the authorized local clip. {tail}")


def _render_vertical_clip(source: Path, target: Path, ffmpeg: str, start: float,
                          duration: float, source_has_audio: bool,
                          captions_ass: Path | None = None) -> None:
    # Preserve the full game frame in the foreground; fill 9:16 with a blurred, enlarged background.
    video_filters = "setsar=1,fps=30"
    if captions_ass is not None:
        video_filters += f",ass=filename={_escape_filter_path(captions_ass)}"
    graph = (
        "[0:v:0]split=2[bg][fg];"
        "[bg]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=22:10[bg2];"
        "[fg]scale=1080:1920:force_original_aspect_ratio=decrease[fg2];"
        f"[bg2][fg2]overlay=(W-w)/2:(H-h)/2,{video_filters}[v]"
    )
    command = [ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-ss", f"{start:.3f}",
               "-i", str(source), "-t", f"{duration:.3f}", "-filter_complex", graph,
               "-map", "[v]"]
    if source_has_audio:
        command.extend(["-map", "0:a:0?"])
    command.extend(["-c:v", "libx264", "-preset", "veryfast", "-crf", "22",
                    "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k",
                    "-movflags", "+faststart", str(target)])
    _run(command)
    if not target.is_file() or target.stat().st_size < 10_000:
        raise RuntimeError("FFmpeg returned without a usable clip file.")


def _mix_voiceover(ffmpeg: str, clip_path: Path, voice_path: Path, target: Path,
                   duration: float, source_has_audio: bool) -> None:
    command = [ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-i", str(clip_path), "-i", str(voice_path)]
    if source_has_audio:
        graph = (
            f"[0:a:0]volume=0.22[game];[1:a:0]volume=1.0[voice];"
            f"[game][voice]amix=inputs=2:duration=longest:dropout_transition=0,atrim=0:{duration:.3f}[a]"
        )
        command.extend(["-filter_complex", graph, "-map", "0:v:0", "-map", "[a]"])
    else:
        command.extend(["-map", "0:v:0", "-map", "1:a:0"])
    command.extend(["-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-t", f"{duration:.3f}",
                    "-movflags", "+faststart", str(target)])
    _run(command)
    if not target.is_file() or target.stat().st_size < 10_000:
        raise RuntimeError("Voiceover mux did not produce a usable video.")


def create_game_clip_job(payload: dict[str, Any]) -> dict[str, Any]:
    channel_id = str(payload.get("channel_id", "ch-2")).strip()
    channel = get_channel(channel_id)
    if not channel:
        raise ValueError("Unknown channel slot.")
    if channel.get("audience_country") != "IN" or not str(channel.get("language", "")).lower().startswith("hi"):
        raise ValueError("Use a separate India/Hindi channel slot (country IN, language hi-IN). The existing US plan is unchanged.")

    source = _local_source(str(payload.get("source_file", "")))
    source_kind = str(payload.get("source_kind", "owned_gameplay"))
    if source_kind not in {"owned_gameplay", "licensed_creator_clip"}:
        raise ValueError("Source must be your own local gameplay or an explicitly licensed creator submission.")
    source_note = str(payload.get("source_rights_note", "")).strip()[:2000]
    if len(source_note) < 30:
        raise ValueError("Add a source-rights note of at least 30 characters.")
    creator_permission_reference = str(payload.get("creator_permission_reference", "")).strip()[:500]
    attribution = str(payload.get("attribution", "")).strip()[:300]
    if source_kind == "licensed_creator_clip":
        if len(creator_permission_reference) < 8:
            raise ValueError("Creator footage needs a written permission/license reference, not just attribution.")
        if not attribution:
            raise ValueError("Add the creator's name/handle for attribution; attribution does not replace permission.")

    source_url = _valid_url(str(payload.get("source_url", "")))
    pre_release_reference = str(payload.get("pre_release_authorization_reference", "")).strip()[:500]
    if _local_today() < GAME_RELEASE_DATE and len(pre_release_reference) < 8:
        raise ValueError("Before the announced release, GTA VI footage requires a written pre-release authorization reference. Leaked footage is prohibited and must not be used.")
    title = str(payload.get("title", "")).strip()
    hook = str(payload.get("hook", "")).strip()[:600]
    commentary = str(payload.get("commentary", "")).strip()[:6000]
    if not title or len(title) > 100:
        raise ValueError("Add a YouTube title from 1 to 100 characters.")
    if len(hook) < 8:
        raise ValueError("Add a specific Hindi/Hinglish hook (at least 8 characters).")
    if len(commentary) < 30:
        raise ValueError("Add an original Hindi/Hinglish commentary or analysis script (at least 30 characters).")

    try:
        start = float(payload.get("start_seconds", 0))
        end = float(payload.get("end_seconds", 0))
    except (TypeError, ValueError) as exc:
        raise ValueError("Start and end timecodes must be numbers in seconds.") from exc
    duration = end - start
    if start < 0 or duration < 5 or duration > MAX_CLIP_SECONDS:
        raise ValueError("Choose a 5–60 second segment. Longer edits need a separate reviewed workflow.")
    source_duration = _source_duration_seconds(source)
    if end > source_duration + 0.05:
        raise ValueError(f"End time exceeds this source's duration ({source_duration:.1f} seconds).")
    caption_style = str(payload.get("caption_style", "static_srt")).strip()
    if caption_style not in GAME_CAPTION_STYLES:
        raise ValueError("Choose Standard SRT or Kinetic word-highlight captions.")
    caption_lines = clean_caption_lines(payload.get("caption_lines", []))
    srt_text = captions_to_srt(caption_lines, duration)
    ass_text = captions_to_ass(caption_lines, duration) if caption_style == "kinetic_karaoke" else ""

    ffmpeg = _ffmpeg_executable()
    if not ffmpeg:
        raise RuntimeError("FFmpeg is not installed. Install FFmpeg or imageio-ffmpeg before rendering gaming clips.")
    if caption_style == "kinetic_karaoke" and not _ffmpeg_supports_ass(ffmpeg):
        raise RuntimeError("Kinetic captions need FFmpeg built with the ASS/libass filter. Choose Standard SRT or configure a supported FFmpeg build.")
    source_has_audio = _probe_has_audio(ffmpeg, source)
    job_id = uuid.uuid4().hex[:12]
    package_dir = PACKAGES_DIR / job_id
    package_dir.mkdir(parents=True, exist_ok=False)
    temp_clip = package_dir / "gaming_clip_source_audio.mp4"
    output = package_dir / "gaming_clip.mp4"
    caption_path = package_dir / "captions.srt"
    caption_ass_path = package_dir / "captions.ass"
    voiceover_enabled = bool(payload.get("generate_voiceover", False))
    voice_path = package_dir / "hindi_voiceover.mp3"
    try:
        caption_path.write_text(srt_text, encoding="utf-8")
        if caption_style == "kinetic_karaoke":
            caption_ass_path.write_text(ass_text, encoding="utf-8")
        _render_vertical_clip(source, temp_clip, ffmpeg, start, duration, source_has_audio,
                              captions_ass=caption_ass_path if caption_style == "kinetic_karaoke" else None)
        if voiceover_enabled:
            if not _voiceover(commentary, voice_path):
                raise RuntimeError("Hindi voiceover was requested but no configured provider returned audio. Configure a Hindi-capable voice, or turn off VO and finish it in an editor.")
            _mix_voiceover(ffmpeg, temp_clip, voice_path, output, duration, source_has_audio)
            temp_clip.unlink(missing_ok=True)
        else:
            temp_clip.replace(output)
        has_audio = _probe_has_audio(ffmpeg, output)
        source_digest = _sha256_file(source)

        release_days = (GAME_RELEASE_DATE - _local_today()).days
        content = {
            "title": title,
            "hook": hook,
            "script": commentary,
            "description": f"{hook}\n\nOriginal commentary script prepared; confirm it is present in the final edit. Verify all rights, game-policy requirements, spoilers and audio before upload.",
            "tags": ["GTA6", "GTAVI", "HindiGaming", "Hinglish", "Shorts"],
            "scenes": [{"narration": commentary, "visual_brief": f"Authorized local gameplay · {start:.1f}s–{end:.1f}s", "seconds": round(duration)}],
            "factual_claims": [],
            "research_questions": ["Confirm the source permission covers commercial YouTube use and every audio element.",
                                   "Review game-policy restrictions, spoilers, and current platform rules."],
            "source_urls": [source_url] if source_url else [],
            "verification_required": True,
            "caption_lines": caption_lines,
        }
        clip_policy = {
            "game": GAME_TITLE,
            "audience_country": "IN",
            "audience_language": "hi-IN",
            "audience_age_hypothesis": "18–35 (working persona; not a reach or targeting guarantee)",
            "official_release_date": GAME_RELEASE_DATE.isoformat(),
            "days_until_release_at_creation": release_days,
            "source_file": source.name,
            "source_sha256": source_digest,
            "source_kind": source_kind,
            "source_url": source_url,
            "pre_release_authorization_reference": pre_release_reference,
            "attribution": attribution,
            "source_rights_note": source_note,
            "creator_permission_reference": creator_permission_reference,
            "start_seconds": start,
            "end_seconds": end,
            "source_duration_seconds": round(source_duration, 3),
            "duration_seconds": round(duration, 3),
            "vertical_render": "1080x1920; full frame fitted over blurred background; 30 fps",
            "caption_style": caption_style,
            "captions_burned_in": caption_style == "kinetic_karaoke",
            "captions_timing": "manual lines split evenly by line and word; not ASR/alignment; manually sync before upload",
            "voiceover_generated": voiceover_enabled,
            "voiceover_path": str(voice_path) if voiceover_enabled else "",
            "commercial_rights_required": True,
            "commercial_license_reference": "",
            "original_commentary_in_render_confirmed": False,
            "game_audio_rights_confirmed": False,
            "no_leaked_or_prohibited_content_confirmed": False,
            "policy_note": "Rockstar's general fan-video policy describes allowed fan use as non-commercial; this monetization-oriented workflow requires case-specific written commercial permission before publication.",
        }
        rights_manifest = {
            "job_id": job_id,
            "rights_status": "uncleared",
            "rights_evidence": "",
            "commercial_game_ip_permission_required": True,
            "commercial_license_reference": "",
            "source_rights": {
                "kind": source_kind,
                "note": source_note,
                "creator_permission_reference": creator_permission_reference,
                "attribution": attribution,
                "source_url": source_url,
                "pre_release_authorization_reference": pre_release_reference,
                "sha256": source_digest,
            },
            "publish_allowed": False,
            "note": "A source-owner permission does not grant the right to exploit Rockstar/Take-Two game IP. No commercial publication until a written commercial authorization is documented and separately reviewed.",
        }
        metadata = {
            "title": title,
            "description": content["description"],
            "tags": content["tags"],
            "language": "hi-IN",
            "target_country": "IN",
            "format": "YouTube Short · Game Clip",
            "source_urls": content["source_urls"],
            "cross_platform_status": "copy variants only; no non-YouTube publisher",
        }
        distribution = distribution_variants(content, "YouTube Short · Game Clip")
        distribution["delivery_mode"] = "YouTube-first; other platform variants are copy-only drafts, not uploads."
        data = {
            "content": content,
            "llm_mode": "manual/editor-supplied gaming brief",
            "format": "Game Clip",
            "fact_check_status": "needs_review",
            "renderer": {
                "video_path": str(output),
                "has_audio": has_audio,
                "visual_mode": ("authorized local footage · blurred background · kinetic word-highlight captions burned in"
                                if caption_style == "kinetic_karaoke" else "authorized local footage · blurred background vertical conversion"),
                "is_publish_ready": False,
                "visual_reviewed": False,
            },
            "gaming_clip": clip_policy,
        }
        (package_dir / "content.json").write_text(json.dumps(content, ensure_ascii=False, indent=2), encoding="utf-8")
        (package_dir / "script.md").write_text(
            f"# {title}\n\n## Hinglish hook\n{hook}\n\n## Original Hindi/Hinglish commentary\n{commentary}\n\n"
            "## Caption timing\nDraft cues are evenly divided across the chosen clip. Re-time and proofread in an editor.\n",
            encoding="utf-8")
        (package_dir / "metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
        (package_dir / "gaming_clip_manifest.json").write_text(json.dumps({
            "job_id": job_id, "video_path": str(output), "width": 1080, "height": 1920, "fps": 30,
            "duration_seconds": round(duration, 3), "has_audio": has_audio,
            "source_file": source.name, "source_sha256": source_digest, "source_kind": source_kind,
            "source_url": source_url, "pre_release_authorization_reference": pre_release_reference,
            "attribution": attribution, "start_seconds": start, "end_seconds": end,
            "source_duration_seconds": round(source_duration, 3),
            "official_release_date": GAME_RELEASE_DATE.isoformat(),
            "voiceover_generated": voiceover_enabled,
            "caption_style": caption_style,
            "captions_burned_in": caption_style == "kinetic_karaoke",
            "captions_sidecar": "captions.srt" + ("; captions.ass" if caption_style == "kinetic_karaoke" else ""),
            "caption_timing_note": "Manual caption lines are split evenly by line and word; proofread and resync before upload.",
            "publish_ready": False,
            "review_note": "Preview/package only. Add and review original commentary, verify every right and check current platform/game policies.",
        }, ensure_ascii=False, indent=2), encoding="utf-8")
        (package_dir / "rights_manifest.json").write_text(json.dumps(rights_manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        (package_dir / "distribution.json").write_text(json.dumps(distribution, ensure_ascii=False, indent=2), encoding="utf-8")
        (package_dir / "review_checklist.md").write_text(
            "# GTA VI clip — human review checklist\n\n"
            "- [ ] Written permission covers commercial use of the source recording and creator stream, if any.\n"
            "- [ ] Case-specific written commercial permission for Rockstar/Take-Two game IP is documented; source credit alone is not permission.\n"
            "- [ ] No leaked/pre-release footage, prohibited story reveals, isolated cutscenes or prohibited in-game entertainment.\n"
            "- [ ] Music, game audio, voice, fonts and every other asset are cleared for commercial use.\n"
            "- [ ] The final edit adds meaningful original Hindi/Hinglish commentary or analysis; captions are proofread and timed.\n"
            "- [ ] No unsupported claims, cheating promotion, misleading title, or repetitive/template-only mass production.\n"
            "- [ ] Final 9:16 MP4 is watched end-to-end, meets current platform rules, and has an audio track.\n"
            "- [ ] YouTube-first metadata is reviewed. Other social variants are copy-only, not automatically published.\n",
            encoding="utf-8")
        job = create_job({
            "id": job_id,
            "channel_id": channel_id,
            "title": title,
            "topic": f"{GAME_TITLE} authorized gaming clip",
            "niche": channel["niche"],
            "format": "Game Clip",
            "status": "needs_review",
            "stage": "gaming_clip_rendered",
            "package_path": str(package_dir.relative_to(PACKAGES_DIR.parent.parent)),
            "rights_status": "uncleared",
            "data": data,
        })
        updated = update_job(job_id, video_path=str(output), has_audio=has_audio, data=data)
        return updated or job
    except Exception:
        shutil.rmtree(package_dir, ignore_errors=True)
        raise
