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

# Ensure project root is in sys.path
CHANNEL_DIR = Path(__file__).resolve().parent
FLEET_DIR = CHANNEL_DIR.parent
WORKSPACE_ROOT = FLEET_DIR.parent
for p in [str(CHANNEL_DIR), str(FLEET_DIR), str(WORKSPACE_ROOT)]:
    if p not in sys.path:
        sys.path.insert(0, p)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)

import thermal_guard
thermal_guard.apply_cool_mode()

import edge_tts
import whisper
from openai import OpenAI
from dotenv import load_dotenv

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(WORKSPACE_ROOT / ".env")

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY", "")
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

# Import from centralized LLM engine (single source of truth)
_FLEET_DIR = str(WORKSPACE_ROOT / "fleet_engines")
if _FLEET_DIR not in sys.path:
    sys.path.insert(0, _FLEET_DIR)
from llm_engine import generate_channel2_script as generate_humanized_script, extract_keywords_llm

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
    api_key = os.getenv("PEXELS_API_KEY") or "Ng530LMnrpm85zReE4lMhjCD7wm5Pc6h8rTE8NfSsuS7be57Qe7C1AGT"
    if not api_key: return False
    try:
        urls = [
            f"https://api.pexels.com/videos/search?query={requests.utils.quote(query)}&orientation=portrait&per_page=5",
            f"https://api.pexels.com/videos/search?query={requests.utils.quote(query)}&per_page=5"
        ]
        for url in urls:
            r = requests.get(url, headers={"Authorization": api_key}, timeout=12)
            if r.status_code != 200:
                continue
            videos = r.json().get("videos", [])
            if not videos:
                continue
            for v in videos:
                # 1. Prefer portrait files
                for f in v.get("video_files", []):
                    if f.get("height", 0) > f.get("width", 0) and f.get("link"):
                        dl = requests.get(f["link"], stream=True, timeout=20)
                        if dl.status_code == 200:
                            with open(out_path, "wb") as fo:
                                for chunk in dl.iter_content(chunk_size=1024*1024): fo.write(chunk)
                            if out_path.exists() and out_path.stat().st_size > 50000:
                                return True
                # 2. Accept HD landscape (ffmpeg auto crops to 9:16)
                for f in v.get("video_files", []):
                    if f.get("link") and (f.get("width", 0) >= 720 or f.get("height", 0) >= 720):
                        dl = requests.get(f["link"], stream=True, timeout=20)
                        if dl.status_code == 200:
                            with open(out_path, "wb") as fo:
                                for chunk in dl.iter_content(chunk_size=1024*1024): fo.write(chunk)
                            if out_path.exists() and out_path.stat().st_size > 50000:
                                return True
    except Exception as e:
        print(f"Pexels fetch warning for '{query}': {e}")
    return False

def render_short(pillar_id: int = 1, topic: str = "", lang: str = "en", custom_script: str = "", custom_title: str = "") -> str:
    print("=" * 75)
    print(f"🎬 CHANNEL 2: RENDERING VOX SHORT (PILLAR #{pillar_id})")
    print("=" * 75)
    
    # 1. Script
    if custom_script:
        title = custom_title or (topic if topic else PILLARS.get(pillar_id, PILLARS[1])["default_topic"])
        pkg = {"title": title, "script": custom_script}
        print(f"📌 Custom Title: {pkg['title']}")
        print(f"📜 Custom Script: {pkg['script']}\n")
    else:
        pkg = generate_script(pillar_id, topic, lang)
        if custom_title:
            pkg["title"] = custom_title
        print(f"📌 Title: {pkg['title']}")
        print(f"📜 Script: {pkg['script']}\n")
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    final_video = OUTPUT_DIR / f"vox_pillar_{pillar_id}_{lang}_{int(time.time())}.mp4"
    
    with TemporaryDirectory() as tmp_str:
        tmp = Path(tmp_str)
        
        # 2. Cloned Voiceover (Adam Baritone)
        audio_file = tmp / "voice.wav"
        print("🎙️ Generating Cloned Adam Voiceover (Offline/Free)...")
        from cloned_voice_engine import generate_cloned_voice
        generate_cloned_voice(pkg["script"], voice_type="adam", output_path=audio_file, lang=lang)
        
        dur_cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(audio_file)]
        total_dur = float(subprocess.run(dur_cmd, stdout=subprocess.PIPE, text=True).stdout.strip())
        print(f"⏱️ Duration: {total_dur:.1f}s")
        
        print("🧠 Transcribing with Whisper for word captions...")
        whisper_data = whisper.load_model("tiny").transcribe(str(audio_file), word_timestamps=True)
        ass_file = tmp / "subtitles.ass"
        
        # Kinetic Subtitles with Nirmala UI Bold and 380px safe margin
        header = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: CineText,Nirmala UI,72,&H00FFFFFF,&H0000FFFF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,5,3,2,60,60,380,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
        events = []
        all_words = [w for s in whisper_data.get("segments", []) for w in s.get("words", [])]
        def fmt(t): return f"{int(t//3600):01d}:{int((t%3600)//60):02d}:{t%60:05.2f}"
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
                for idx_c, cw in enumerate(chunk):
                    word_clean = cw["word"].strip()
                    if idx_c == act_idx:
                        parts.append(f"{{\\c&H0000FFFF&}}{word_clean}")
                    else:
                        parts.append(f"{{\\c&H00FFFFFF&}}{word_clean}")
                events.append(f"Dialogue: 0,{fmt(w_start)},{fmt(w_end)},CineText,,0,0,0,,{' '.join(parts)}")
        ass_file.write_text(header + "\n".join(events) + "\n", encoding="utf-8")
        
        # 3. 100% Real 4K Visual Cuts (Zero Synthetic Drawings)
        total_cuts = max(int(total_dur / 3.0), 3)
        cut_dur = total_dur / total_cuts
        print(f"✂️ Visual Cuts: {total_cuts} 100% Real 4K Cuts ({cut_dur:.2f}s each)")
        
        segments = []
        pillar_terms = PILLARS.get(pillar_id, PILLARS[1])["search_terms"]
        
        # Extract dynamic semantic queries from title/script
        kw_list = extract_keywords_llm(pkg["script"], total_dur) if pkg.get("script") else []
        combined_queries = kw_list + pillar_terms
        
        for idx in range(total_cuts):
            seg_out = tmp / f"seg_{idx}.mp4"
            segments.append(seg_out)
            
            q = combined_queries[idx % len(combined_queries)]
            print(f"🎥 Scene {idx+1}/{total_cuts}: Real 4K Footage ('{q}')...")
            b_path = tmp / f"stock_{idx}.mp4"
            downloaded = download_pexels_clip(q, b_path)
            if not downloaded:
                for alt_q in ["dark interrogation room", "clock ticking dramatic", "noir mystery smoke", "dark cinematic suspense"]:
                    if download_pexels_clip(alt_q, b_path):
                        downloaded = True
                        break
            
            if not downloaded or not b_path.exists() or b_path.stat().st_size < 10000:
                print("⚠️ Generating procedural cinematic noir background...")
                b_path = tmp / f"procedural_noir_{idx}.mp4"
                proc_cmd = [
                    "ffmpeg", "-y", "-f", "lavfi",
                    "-i", f"color=c=0x07090e:s=1080x1920:d={cut_dur+2:.2f}:r=30",
                    "-vf", "noise=alls=12:allf=t+u,vignette=PI/3.5,eq=contrast=1.3:brightness=-0.05",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-t", f"{cut_dur+1:.2f}",
                    str(b_path)
                ]
                subprocess.run(proc_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
                
            # Apply subtle camera drift + Netflix Noir grading + Vignette
            drift_dir = "down" if idx % 2 == 0 else "up"
            if drift_dir == "down":
                crop_expr = f"crop=1080:1920:x='(in_w-out_w)/2':y='(in_h-out_h)*(t/{cut_dur:.2f})'"
            else:
                crop_expr = f"crop=1080:1920:x='(in_w-out_w)/2':y='(in_h-out_h)*(1-t/{cut_dur:.2f})'"
                
            vf = (
                f"scale=1188:2112:force_original_aspect_ratio=increase,"
                f"{crop_expr},"
                f"eq=contrast=1.18:brightness=-0.03:saturation=0.90,"
                f"vignette=PI/4"
            )
            cmd = [
                "ffmpeg", "-y", "-stream_loop", "-1", "-i", str(b_path),
                "-vf", vf,
                "-t", f"{cut_dur:.2f}",
                "-r", "30",
                "-c:v", "libx264", "-preset", "fast", "-crf", "18",
                "-an", str(seg_out)
            ]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            
        # 4. Concat Real Clips
        concat_txt = tmp / "concat.txt"
        with open(concat_txt, "w") as f:
            for s in segments: f.write(f"file '{s.name}'\n")
        concat_mp4 = tmp / "concat.mp4"
        subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_txt), "-c", "copy", str(concat_mp4)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        
        # 5. Master Tuned BGM with Dynamic Smart Cueing (Skipping dead intros)
        bgm_file = tmp / "ambient_drone.mp3"
        bgm_dir = WORKSPACE_ROOT / "fleet_engines/assets/bgm"
        available_bgms = sorted(list(bgm_dir.glob("*.mp3"))) if bgm_dir.exists() else []
        
        pillar_bgm_map = {
            1: "03_mystery_lightless_dawn.mp3",
            2: "01_forensic_the_dread.mp3",
            3: "06_cosmic_deep_noise.mp3",
            4: "02_psychology_echoes_of_time.mp3"
        }
        chosen_bgm = None
        target_name = pillar_bgm_map.get(pillar_id, "")
        for b in available_bgms:
            if target_name and target_name in b.name:
                chosen_bgm = b
                break
        if not chosen_bgm and available_bgms:
            import random
            chosen_bgm = random.choice(available_bgms)
            
        bgm_volume = 0.52
        if chosen_bgm and chosen_bgm.exists():
            from dynamic_bgm_slicer import prepare_synced_bgm
            bgm_file, bgm_volume = prepare_synced_bgm(chosen_bgm, total_dur, bgm_file)
        else:
            drone_cmd = [
                "ffmpeg", "-y",
                "-f", "lavfi", "-i", "anoisesrc=c=pink:r=44100:a=0.05",
                "-f", "lavfi", "-i", "sine=f=50:r=44100",
                "-f", "lavfi", "-i", "sine=f=75:r=44100",
                "-filter_complex",
                f"[0:a]lowpass=f=180,volume=0.25[noise];"
                f"[1:a]volume=0.35[sub];"
                f"[2:a]volume=0.22[mid];"
                f"[noise][sub][mid]amix=inputs=3,afade=t=in:ss=0:d=1.0,afade=t=out:st={total_dur-1.5:.2f}:d=1.5",
                "-t", f"{total_dur:.2f}",
                str(bgm_file)
            ]
            subprocess.run(drone_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            bgm_volume = 0.50
        
        # 6. Burn Subtitles & Mix Audio (Voice at 1.0, Tuned BGM at dynamic volume)
        sub_escaped = str(ass_file).replace("\\", "/").replace(":", "\\:")
        full_filter = (
            f"[0:v]ass='{sub_escaped}'[vout];"
            f"[1:a]volume=1.0[voice];"
            f"[2:a]volume={bgm_volume:.2f}[drone];"
            f"[voice][drone]amix=inputs=2:duration=first:dropout_transition=2[aout]"
        )
        final_cmd = [
            "ffmpeg", "-y",
            "-i", str(concat_mp4),
            "-i", str(audio_file),
            "-i", str(bgm_file),
            "-filter_complex", full_filter,
            "-map", "[vout]",
            "-map", "[aout]",
            "-c:v", "libx264", "-preset", "fast", "-crf", "18",
            "-c:a", "aac", "-b:a", "192k",
            "-shortest",
            str(final_video)
        ]
        print("⚡ Final 4K Cinematic Assembly...")
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
    parser.add_argument("--title", type=str, default="", help="Custom Title override")
    parser.add_argument("--script", type=str, default="", help="Custom Script text override")
    parser.add_argument("--lang", type=str, default="en", choices=["en", "hi"])
    parser.add_argument("--upload", action="store_true", help="Auto upload to YouTube after rendering (unlisted)")
    parser.add_argument("--telegram", action="store_true", default=True, help="Send video & metadata to Telegram")
    parser.add_argument("--privacy", type=str, default="unlisted", choices=["public", "unlisted", "private"])
    args = parser.parse_args()
    
    rendered_path = render_short(
        pillar_id=args.pillar,
        topic=args.topic,
        lang=args.lang,
        custom_script=args.script,
        custom_title=args.title
    )
    
    yt_url = None
    raw_title = args.title.strip() if args.title else (args.topic.strip() if args.topic else f"Duniya Ka Sabse Bada Rahasya")
    title = f"{raw_title} 😱 #shorts #mystery"
    desc = (
        f"🕵️ {raw_title}\n\n"
        f"Kya aapko is anokhi ghatna ka sach pata tha? Apni raye comment me zaroor batayein! 👇\n\n"
        f"#shorts #mystery #unsolved #facts #amazingfacts #hindifacts #sciencefacts #viral #trending #youtubeshorts"
    )
    tags = ["mystery", "unsolved", "facts", "amazing facts", "hindi facts", "science facts", "shorts", "viral shorts", "trending"]
    
    if args.upload and rendered_path:
        from fleet_engines.channel_2.youtube_uploader import upload_short_to_youtube
        video_p = Path(rendered_path)
        res = upload_short_to_youtube(video_p, title, desc, channel=2, privacy_status=args.privacy)
        if res:
            yt_url = res.get("video_url")
            
    if args.telegram and rendered_path:
        from fleet_engines.telegram_dispatcher import send_fleet_video_to_telegram
        send_fleet_video_to_telegram(
            video_path=Path(rendered_path),
            channel=2,
            title=title,
            description=desc,
            tags=tags,
            youtube_url=yt_url,
            privacy=args.privacy
        )
