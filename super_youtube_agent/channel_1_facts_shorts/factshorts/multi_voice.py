"""Multi-Voice Story Engine: synthesizes scripts using 2-3 distinct voices
(e.g., Hook Narrator -> Storyteller -> Climax Specialist) and generates
synchronized audio and multi-color word timings for Option 1 Animated Captions.
"""
from __future__ import annotations

import asyncio
import json
import re
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Tuple

import edge_tts

from .config import Config, get_config
from .utils import media_duration, module_logger

log = module_logger("multi_voice")

@dataclass
class SpeakerVoice:
    name: str
    voice_id: str
    provider: str = "edge"  # edge, kokoro, svara, elevenlabs
    caption_color: str = "#FFE600"  # Hex color for word highlight

DEFAULT_MULTI_VOICES = {
    "hindi": [
        SpeakerVoice("Deep Narrator", "hi-IN-MadhurNeural", "edge", "#FFE600"),    # Cyber Yellow
        SpeakerVoice("Expressive Story", "hi-IN-SwaraNeural", "edge", "#00FF88"),  # Neon Green
        SpeakerVoice("Serious Climax", "hi-IN-MadhurNeural", "edge", "#FF3300"),   # Fiery Red
    ],
    "english": [
        SpeakerVoice("Christopher", "en-US-ChristopherNeural", "edge", "#00E5FF"), # Electric Cyan
        SpeakerVoice("Jenny", "en-US-JennyNeural", "edge", "#FFE600"),             # Cyber Yellow
        SpeakerVoice("Guy", "en-US-GuyNeural", "edge", "#FF3300"),                 # Fiery Orange
    ]
}

@dataclass
class VoiceWord:
    word: str
    start: float
    end: float
    speaker_index: int = 0
    color: str = "#FFE600"

async def synthesize_speaker_segment(
    text: str,
    voice_id: str,
    out_path: Path,
) -> Tuple[List[dict], float]:
    """Synthesize a single speaker segment via edge-tts with word timestamps."""
    comm = edge_tts.Communicate(text, voice_id)
    sub_words: List[dict] = []
    
    with open(out_path, "wb") as f:
        async for chunk in comm.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                sub_words.append({
                    "word": chunk["text"],
                    "start": chunk["offset"] / 10_000_000,
                    "end": (chunk["offset"] + chunk["duration"]) / 10_000_000,
                })
                
    dur = media_duration(out_path)
    if not sub_words:
        from .align import estimate_span
        estimated = estimate_span(text, dur)
        sub_words = [{"word": w, "start": s, "end": e} for (w, s, e) in estimated]
    return sub_words, dur

async def render_multi_voice(
    segments: List[Tuple[int, str]],  # List of (speaker_index, text)
    output_audio: Path,
    language: str = "hindi",
    custom_voices: List[SpeakerVoice] | None = None,
) -> Tuple[Path, float, List[VoiceWord]]:
    """Synthesize 2-3 voices into a unified audio file with stitched word timestamps."""
    voices = custom_voices or DEFAULT_MULTI_VOICES.get(language, DEFAULT_MULTI_VOICES["english"])
    workdir = output_audio.parent / "multi_voice_tmp"
    workdir.mkdir(parents=True, exist_ok=True)
    
    audio_files: List[Path] = []
    all_words: List[VoiceWord] = []
    current_time_offset = 0.0
    
    for i, (speaker_idx, text) in enumerate(segments):
        speaker = voices[speaker_idx % len(voices)]
        seg_audio = workdir / f"seg_{i:02d}.mp3"
        log.info("Multi-Voice [%d]: %s (%s) -> %r", i, speaker.name, speaker.voice_id, text[:40])
        
        words, dur = await synthesize_speaker_segment(text, speaker.voice_id, seg_audio)
        audio_files.append(seg_audio)
        
        for w in words:
            all_words.append(VoiceWord(
                word=w["word"],
                start=round(w["start"] + current_time_offset, 3),
                end=round(w["end"] + current_time_offset, 3),
                speaker_index=speaker_idx,
                color=speaker.caption_color,
            ))
            
        current_time_offset += dur
        
    # Stitch audio files with ffmpeg concat demuxer
    concat_list = workdir / "concat.txt"
    with open(concat_list, "w", encoding="utf-8") as f:
        for a in audio_files:
            f.write(f"file '{a.resolve().as_posix()}'\n")
            
    cmd = [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-f", "concat", "-safe", "0", "-i", str(concat_list),
        "-c:a", "libmp3lame", "-q:a", "2", str(output_audio)
    ]
    subprocess.run(cmd, check=True)
    total_dur = media_duration(output_audio)
    log.info("Multi-Voice complete: %.2fs audio stitched from %d segments (%d words)", total_dur, len(segments), len(all_words))
    
    # Cleanup temp segment files
    shutil.rmtree(workdir, ignore_errors=True)
    return output_audio, total_dur, all_words
