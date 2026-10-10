"""
=============================================================================
CHANNEL 2: VOX DOCUMENTARY ENGINE (SINGLE UNIFIED SCRIPT)
=============================================================================
Usage:
  python run_channel_2.py                 (Pillar 1: Forbidden Places, English)
  python run_channel_2.py --pillar 2      (Pillar 2: Forensic Interrogation)
  python run_channel_2.py --lang hi       (Hindi Voiceover & Script)
  python run_channel_2.py --topic "Custom Topic"
=============================================================================
"""
import os
import sys
import json
import time
import math
import shutil
import asyncio
import argparse
import requests
import subprocess
import numpy as np
import cv2
from pathlib import Path
from tempfile import TemporaryDirectory
from PIL import Image, ImageDraw, ImageFont

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)

import edge_tts
import whisper
from openai import OpenAI
from dotenv import load_dotenv

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(WORKSPACE_ROOT / ".env")

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")
OUTPUT_DIR = WORKSPACE_ROOT / "fleet_engines/output/channel_2_vox_mystery"

# =============================================================================
# 1. THE 4 MASTER VIRAL PILLARS
# =============================================================================
PILLARS = {
    1: {
        "name": "Forbidden Places & Coordinates",
        "default_topic": "The Siberian Door to the Underworld crater expanding yearly",
        "search_terms": ["stormy ocean dark fog", "dark misty rainforest aerial", "ancient cave entrance"]
    },
    2: {
        "name": "Forensic & Interrogation Psychology",
        "default_topic": "The FBI 4-second silence rule that exposes lies",
        "search_terms": ["dark interrogation room", "clock ticking dramatic", "close up eye pupil"]
    },
    3: {
        "name": "Space & Cosmic Anomalies",
        "default_topic": "The James Webb deep void discovery that shouldn't exist",
        "search_terms": ["deep space telescope nebula", "satellite earth night", "spinning galaxy cosmic"]
    },
    4: {
        "name": "Dark Mind Hacks & Subconscious Glitches",
        "default_topic": "How looking at someone's forehead triggers anxiety",
        "search_terms": ["mysterious shadow portrait", "chess pieces dramatic", "macro eye dilation"]
    }
}

# Import Universal Anti-AI-Slop Humanized Script & CTA Writer
sys.path.insert(0, str(WORKSPACE_ROOT / "fleet_engines"))
from universal_humanized_writer import generate_humanized_script

# =============================================================================
# 2. SCRIPT GENERATOR (UNIVERSAL HUMANIZED STORYTELLER)
# =============================================================================
def generate_script(pillar_id: int, topic: str, lang: str = "en") -> dict:
    pillar = PILLARS.get(pillar_id, PILLARS[1])
    target_topic = topic or pillar["default_topic"]
    return generate_humanized_script(
        topic=target_topic,
        niche_context=pillar["name"],
        lang=lang,
        word_count_target=85
    )

# =============================================================================
# 3. PROCEDURAL MOTION GRAPHICS (MAPS & HIGHLIGHTERS)
# =============================================================================
def make_animated_map(output_path: Path, duration: float = 2.5):
    """Renders dark Vox cartography map with curved trajectory."""
    w, h, fps = 1080, 1920, 30
    total_frames = int(duration * fps)
    out = cv2.VideoWriter(str(output_path), cv2.VideoWriter_fourcc(*'mp4v'), fps, (w, h))
    p1, p2, ctrl = np.array([280, 1100]), np.array([820, 820]), np.array([520, 680])
    
    for f in range(total_frames):
        prog = f / max(total_frames - 1, 1)
        canvas = np.zeros((h, w, 3), dtype=np.uint8)
        canvas[:, :] = [22, 16, 12]  # Dark oceanic
        
        # Grid
        for gy in range(0, h, 140): cv2.line(canvas, (0, gy), (w, gy), (40, 32, 24), 1)
        for gx in range(0, w, 140): cv2.line(canvas, (gx, 0), (gx, h), (40, 32, 24), 1)
        
        # Curve
        t_vals = np.linspace(0, prog, int(prog * 50) + 2)
        curve_pts = [(1-t)**2 * p1 + 2*(1-t)*t * ctrl + t**2 * p2 for t in t_vals]
        if len(curve_pts) > 1:
            pts_arr = np.array(curve_pts, np.int32)
            cv2.polylines(canvas, [pts_arr], False, (0, 180, 255), 4, cv2.LINE_AA)
            cv2.polylines(canvas, [pts_arr], False, (180, 230, 255), 2, cv2.LINE_AA)
            
        cv2.circle(canvas, (int(p1[0]), int(p1[1])), 8, (0, 200, 255), -1)
        if len(curve_pts) > 0:
            head = curve_pts[-1]
            cv2.circle(canvas, (int(head[0]), int(head[1])), int(12 + 6*math.sin(f*0.4)), (0, 160, 255), 2)
            
        pil = Image.fromarray(cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(pil)
        draw.rectangle([60, 220, 480, 280], fill=(0, 0, 0, 190), outline=(0, 180, 255), width=2)
        draw.text((80, 238), "SATELLITE TELEMETRY // ROUTE", fill=(0, 210, 255))
        draw.text((80, 1680), "ATLANTIC EXPEDITION SECTOR 04", fill=(120, 120, 120))
        out.write(cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR))
    out.release()

def make_highlighter_document(output_path: Path, duration: float = 2.5):
    """Renders vintage archival report with animated yellow highlighter."""
    w, h, fps = 1080, 1920, 30
    total_frames = int(duration * fps)
    out = cv2.VideoWriter(str(output_path), cv2.VideoWriter_fourcc(*'mp4v'), fps, (w, h))
    paper_bg = np.full((h, w, 3), [210, 225, 238], dtype=np.uint8)
    
    for f in range(total_frames):
        prog = f / max(total_frames - 1, 1)
        pil = Image.fromarray(cv2.cvtColor(paper_bg, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(pil, "RGBA")
        cx1, cy1, cx2, cy2 = 80, 420, 1000, 1460
        draw.rectangle([cx1, cy1, cx2, cy2], fill=(245, 238, 222, 255), outline=(120, 100, 80, 255), width=3)
        draw.text((cx1 + 40, cy1 + 50), "OFFICIAL INVESTIGATION REPORT", fill=(20, 15, 10))
        draw.line([cx1 + 40, cy1 + 100, cx2 - 40, cy1 + 100], fill=(60, 50, 40), width=2)
        
        # Highlight wipe
        hl_prog = min(max((prog - 0.15) / 0.65, 0.0), 1.0)
        cur_w = int(800 * hl_prog)
        if cur_w > 0:
            draw.rectangle([cx1 + 35, cy1 + 220, cx1 + 35 + cur_w, cy1 + 270], fill=(255, 240, 20, 180))
        draw.text((cx1 + 40, cy1 + 230), "TARGET ANOMALY CONFIRMED BEYOND PERIMETER", fill=(10, 8, 5))
        draw.rectangle([cx2 - 320, cy2 - 140, cx2 - 40, cy2 - 50], outline=(190, 30, 30, 230), width=3)
        draw.text((cx2 - 300, cy2 - 120), "CLASSIFIED FILE", fill=(190, 30, 30, 230))
        out.write(cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR))
    out.release()

# =============================================================================
# 4. SUBTITLES & VOICEOVER
# =============================================================================
async def create_voiceover(text: str, out_path: str, lang: str):
    voice = "hi-IN-MadhurNeural" if lang == "hi" else "en-US-ChristopherNeural"
    communicate = edge_tts.Communicate(text, voice, rate="+0%")
    await communicate.save(out_path)

def build_mrbeast_ass(whisper_segments: list, ass_path: Path):
    """Kinetic ASS subtitles: yellow highlighted active word, bold font, 8px black stroke."""
    header = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: MrBeast,Impact,78,&H00FFFFFF,&H0000FFFF,&H00000000,&H80000000,-1,0,0,0,100,100,2,0,1,8,2,2,60,60,260,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    events = []
    all_words = [w for s in whisper_segments for w in s.get("words", [])]
    
    def fmt(t):
        return f"{int(t//3600):01d}:{int((t%3600)//60):02d}:{t%60:05.2f}"
        
    for i in range(0, len(all_words), 3):
        chunk = all_words[i:i+3]
        if not chunk: continue
        for act_idx, w in enumerate(chunk):
            w_start, w_end = w["start"], w["end"]
            if act_idx < len(chunk) - 1:
                next_st = chunk[act_idx+1]["start"]
                if next_st > w_end and next_st - w_end < 0.25:
                    w_end = next_st
            parts = []
            for idx, cw in enumerate(chunk):
                word_clean = cw["word"].strip().upper()
                if idx == act_idx:
                    parts.append(f"{{\\c&H0000FFFF&}}{word_clean}")
                else:
                    parts.append(f"{{\\c&H00FFFFFF&}}{word_clean}")
            events.append(f"Dialogue: 0,{fmt(w_start)},{fmt(w_end)},MrBeast,,0,0,0,,{' '.join(parts)}")
            
    ass_path.write_text(header + "\n".join(events) + "\n", encoding="utf-8")

# =============================================================================
# 5. MASTER VIDEO COMPOSITING (ZERO SLOP, RAPID CUTS)
# =============================================================================
def download_pexels_clip(query: str, out_path: Path) -> bool:
    if not PEXELS_API_KEY: return False
    try:
        url = f"https://api.pexels.com/videos/search?query={requests.utils.quote(query)}&orientation=portrait&per_page=3"
        r = requests.get(url, headers={"Authorization": PEXELS_API_KEY}, timeout=12).json()
        for v in r.get("videos", []):
            for f in v.get("video_files", []):
                if f.get("height", 0) > f.get("width", 0) and f.get("link"):
                    dl = requests.get(f["link"], stream=True, timeout=20)
                    with open(out_path, "wb") as fo:
                        for chunk in dl.iter_content(chunk_size=1024*1024): fo.write(chunk)
                    return True
    except Exception:
        pass
    return False

def render_short(pillar_id: int = 1, topic: str = "", lang: str = "en") -> str:
    print("=" * 75)
    print(f"🎬 CHANNEL 2: RENDERING VOX SHORT (PILLAR #{pillar_id})")
    print("=" * 75)
    
    # 1. Script
    pkg = generate_script(pillar_id, topic, lang)
    print(f"📌 Title: {pkg['title']}")
    print(f"📜 Script: {pkg['script']}\n")
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    final_video = OUTPUT_DIR / f"vox_pillar_{pillar_id}_{lang}_{int(time.time())}.mp4"
    
    with TemporaryDirectory() as tmp_str:
        tmp = Path(tmp_str)
        
        # 2. Voiceover & Whisper
        audio_file = tmp / "voice.mp3"
        print("🎙️ Generating EdgeTTS voiceover...")
        asyncio.run(create_voiceover(pkg["script"], str(audio_file), lang))
        
        dur_cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(audio_file)]
        total_dur = float(subprocess.run(dur_cmd, stdout=subprocess.PIPE, text=True).stdout.strip())
        print(f"⏱️ Duration: {total_dur:.1f}s")
        
        print("🧠 Transcribing with Whisper for word captions...")
        whisper_data = whisper.load_model("tiny").transcribe(str(audio_file), word_timestamps=True)
        ass_file = tmp / "subtitles.ass"
        build_mrbeast_ass(whisper_data["segments"], ass_file)
        
        # 3. Dynamic Cuts (Cut every 2.5s)
        total_cuts = max(int(total_dur / 2.5), 4)
        cut_dur = total_dur / total_cuts
        print(f"✂️ Visual Cuts: {total_cuts} rapid cuts ({cut_dur:.2f}s each)")
        
        segments = []
        pillar_terms = PILLARS.get(pillar_id, PILLARS[1])["search_terms"]
        
        for idx in range(total_cuts):
            seg_out = tmp / f"seg_{idx}.mp4"
            segments.append(seg_out)
            
            if idx == 0:
                print(f"🗺️ Scene {idx+1}: Animated Vox Map...")
                make_animated_map(seg_out, cut_dur)
            elif idx == 1:
                print(f"📰 Scene {idx+1}: Archival Highlighter...")
                make_highlighter_document(seg_out, cut_dur)
            else:
                q = pillar_terms[(idx - 2) % len(pillar_terms)]
                print(f"🎥 Scene {idx+1}: 4K Pexels Video ('{q}')...")
                b_path = tmp / f"stock_{idx}.mp4"
                if not download_pexels_clip(q, b_path):
                    b_path = WORKSPACE_ROOT / "fleet_engines/assets/background_videos/subway_surfers/subway_surfers.mp4"
                cmd = [
                    "ffmpeg", "-y", "-stream_loop", "-1", "-i", str(b_path),
                    "-filter_complex", "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920[v]",
                    "-map", "[v]", "-t", f"{cut_dur:.2f}",
                    "-c:v", "libx264", "-preset", "fast", "-threads", "2", str(seg_out)
                ]
                subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
                
        # 4. Concat
        concat_txt = tmp / "concat.txt"
        with open(concat_txt, "w") as f:
            for s in segments: f.write(f"file '{s.name}'\n")
        concat_mp4 = tmp / "concat.mp4"
        subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_txt), "-c", "copy", str(concat_mp4)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        
        # 5. Burn ASS Subtitles & Mix Audio
        sub_escaped = str(ass_file).replace("\\", "/").replace(":", "\\:")
        ambient = WORKSPACE_ROOT / "fleet_engines/ShortGPT/public/audio/ambient_drone.mp3"
        
        if ambient.exists():
            final_cmd = [
                "ffmpeg", "-y",
                "-i", str(concat_mp4), "-i", str(audio_file), "-stream_loop", "-1", "-i", str(ambient),
                "-filter_complex", f"[0:v]ass='{sub_escaped}'[vout];[2:a]volume=0.08[drone];[1:a][drone]amix=inputs=2:duration=first[aout]",
                "-map", "[vout]", "-map", "[aout]",
                "-c:v", "libx264", "-preset", "fast", "-c:a", "aac", "-threads", "2", str(final_video)
            ]
        else:
            final_cmd = [
                "ffmpeg", "-y",
                "-i", str(concat_mp4), "-i", str(audio_file),
                "-filter_complex", f"[0:v]ass='{sub_escaped}'[vout]",
                "-map", "[vout]", "-map", "1:a",
                "-c:v", "libx264", "-preset", "fast", "-c:a", "aac", "-threads", "2", str(final_video)
            ]
            
        print("⚡ Final Assembly...")
        subprocess.run(final_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        
    print("=" * 75)
    print("🎉 [VOX SHORT RENDERED SUCCESSFULLY]")
    print(f"📁 Video: {final_video}")
    print("=" * 75)
    return str(final_video)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Unified Channel 2 Engine")
    parser.add_argument("--pillar", type=int, default=1, choices=[1, 2, 3, 4])
    parser.add_argument("--topic", type=str, default="")
    parser.add_argument("--lang", type=str, default="en", choices=["en", "hi"])
    parser.add_argument("--upload", action="store_true", help="Auto upload to YouTube after rendering (unlisted)")
    parser.add_argument("--privacy", type=str, default="unlisted", choices=["public", "unlisted", "private"])
    args = parser.parse_args()
    
    rendered_path = render_short(pillar_id=args.pillar, topic=args.topic, lang=args.lang)
    
    if args.upload and rendered_path:
        from fleet_engines.channel_2.youtube_uploader import upload_short_to_youtube
        video_p = Path(rendered_path)
        topic_title = args.topic or f"Mystery Shorts #{args.pillar}"
        upload_short_to_youtube(video_p, f"{topic_title} #shorts", "Story by Channel 2 Mystery Engine", privacy_status=args.privacy)
