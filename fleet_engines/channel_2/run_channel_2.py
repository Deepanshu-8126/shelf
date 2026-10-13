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

GROQ_API_KEY = os.getenv("GROQ_API_KEY") or "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"
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY") or "Ng530LMnrpm85zReE4lMhjCD7wm5Pc6h8rTE8NfSsuS7be57Qe7C1AGT"
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
        word_count_target=55
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
    tmp_h264 = output_path.with_name(f"h264_{output_path.name}")
    subprocess.run(["ffmpeg", "-y", "-i", str(output_path), "-c:v", "libx264", "-preset", "fast", "-pix_fmt", "yuv420p", "-r", "30", str(tmp_h264)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    if tmp_h264.exists():
        tmp_h264.replace(output_path)

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
    tmp_h264 = output_path.with_name(f"h264_hl_{output_path.name}")
    subprocess.run(["ffmpeg", "-y", "-i", str(output_path), "-c:v", "libx264", "-preset", "fast", "-pix_fmt", "yuv420p", "-r", "30", str(tmp_h264)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    if tmp_h264.exists():
        tmp_h264.replace(output_path)

# =============================================================================
# 4. SUBTITLES & VOICEOVER
# =============================================================================
from media_fetcher import fetch_mixed_media_clip

# =============================================================================
# 4. SUBTITLES & VOICEOVER (KOKORO MICHAEL SOTA NARRATION)
# =============================================================================
def synthesize_channel2_voice(script: str, out_raw: Path, lang: str = "en") -> list:
    """
    Synthesizes documentary-grade voiceover for Channel 2.
    Primary: Kokoro-82M ('am_michael' for English, 'hf_beta' for Hindi).
    Secondary: Edge-TTS ('en-US-ChristopherNeural' for English, 'hi-IN-MadhurNeural' for Hindi).
    Tertiary: Google TTS.
    Returns word timestamps list: [{'word': ..., 'start': ..., 'end': ...}]
    """
    is_hindi = (lang == "hi")
    voice_code = "hf_beta" if is_hindi else "am_michael"
    lang_code = "h" if is_hindi else "a"

    # 1. Kokoro-82M
    try:
        print(f"🎙️ Engaging Kokoro-82M Engine (Voice: {voice_code})...")
        import re
        from kokoro import KPipeline
        import soundfile as sf
        import numpy as np

        pipeline = KPipeline(lang_code=lang_code)
        generator = pipeline(script, voice=voice_code, speed=1.05)

        all_audios = []
        words = []
        curr_time = 0.0

        for res in generator:
            chunk_audio = res.audio
            chunk_dur = len(chunk_audio) / 24000.0
            all_audios.append(chunk_audio)

            cwords = [w for w in re.split(r'\s+', res.graphemes) if w.strip()]
            if not cwords:
                curr_time += chunk_dur
                continue

            total_chars = sum(len(w) for w in cwords)
            chunk_t = curr_time
            for w in cwords:
                w_dur = max(0.12, (len(w) / max(total_chars, 1)) * chunk_dur)
                words.append({
                    "start": round(chunk_t, 3),
                    "end": round(chunk_t + w_dur, 3),
                    "duration": round(w_dur, 3),
                    "word": w
                })
                chunk_t += w_dur
            curr_time += chunk_dur

        if all_audios and words:
            combined = np.concatenate(all_audios)
            out_wav = out_raw.with_suffix(".wav")
            sf.write(str(out_wav), combined, 24000)
            subprocess.run(["ffmpeg", "-y", "-i", str(out_wav), str(out_raw)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            if out_wav.exists() and out_wav != out_raw:
                out_wav.unlink()
            print(f"✅ Kokoro-82M ({voice_code}) synthesized {len(words)} words ({curr_time:.1f}s audio)")
            return words
    except Exception as e:
        print(f"⚠️ Kokoro engine note: {e}. Falling back to Edge-TTS...")

    # 2. Edge-TTS Fallback
    edge_voice = "hi-IN-MadhurNeural" if is_hindi else "en-US-ChristopherNeural"
    try:
        import edge_tts
        print(f"🎙️ Engaging Edge-TTS Engine ({edge_voice})...")
        c = edge_tts.Communicate(script, edge_voice, rate="+2%", boundary="WordBoundary")
        words = []
        async def _run_edge():
            with open(out_raw, "wb") as f:
                async for chunk in c.stream():
                    if chunk["type"] == "audio":
                        f.write(chunk["data"])
                    elif chunk["type"] == "WordBoundary":
                        st_s = chunk["offset"] / 10_000_000.0
                        dur_s = chunk["duration"] / 10_000_000.0
                        words.append({
                            "start": st_s,
                            "end": st_s + dur_s,
                            "duration": dur_s,
                            "word": chunk.get("text", "").strip()
                        })
        asyncio.run(_run_edge())
        if out_raw.exists() and out_raw.stat().st_size > 10000 and words:
            return words
    except Exception as e:
        print(f"⚠️ Edge-TTS unavailable ({e}). Engaging Google TTS fallback...")

    # 3. Google TTS Fallback
    import urllib.parse
    clean_words = [w for w in re.split(r'\s+', script) if w.strip()]
    u = f"https://translate.google.com/translate_tts?ie=UTF-8&q={urllib.parse.quote(script[:180])}&tl={'hi' if is_hindi else 'en'}&client=tw-ob"
    r = requests.get(u, headers={"User-Agent": "Mozilla/5.0"}, timeout=12)
    with open(out_raw, "wb") as f: f.write(r.content)
    total_dur = 25.0
    curr_t = 0.0
    words = []
    for w in clean_words:
        w_dur = 0.35
        words.append({"start": curr_t, "end": curr_t + w_dur, "duration": w_dur, "word": w})
        curr_t += w_dur
    return words

def build_mrbeast_ass(words: list, ass_path: Path):
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
    def fmt(t):
        return f"{int(t//3600):01d}:{int((t%3600)//60):02d}:{t%60:05.2f}"

    for i in range(0, len(words), 3):
        chunk = words[i:i+3]
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
        
        # 2. Voiceover (Kokoro Michael for English, Kokoro Beta for Hindi) & Studio Mastering
        raw_voice = tmp / "raw_voice.mp3"
        audio_file = tmp / "voice.mp3"
        timed_words = synthesize_channel2_voice(pkg["script"], raw_voice, lang=lang)

        # Studio audio mastering chain: Warmth + Presence + Broadcast Compressor
        af = (
            "highpass=f=75,"
            "equalizer=f=120:width_type=h:width=80:g=2.2,"
            "equalizer=f=3400:width_type=h:width=600:g=2.5,"
            "acompressor=threshold=-16dB:ratio=2.8:attack=10:release=90,"
            "volume=1.05"
        )
        subprocess.run(["ffmpeg", "-y", "-i", str(raw_voice), "-af", af, str(audio_file)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

        dur_cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(audio_file)]
        total_dur = float(subprocess.run(dur_cmd, stdout=subprocess.PIPE, text=True).stdout.strip())
        print(f"⏱️ Duration: {total_dur:.1f}s")

        print("📝 Generating Kinetic ASS Subtitles...")
        ass_file = tmp / "subtitles.ass"
        build_mrbeast_ass(timed_words, ass_file)

        # 3. Dynamic Cuts (Cut every 2.0s for high retention)
        total_cuts = max(int(total_dur / 2.0), 6)
        cut_dur = total_dur / total_cuts
        print(f"✂️ Visual Cuts: {total_cuts} rapid cuts ({cut_dur:.2f}s each)")

        segments = []
        pillar_terms = PILLARS.get(pillar_id, PILLARS[1])["search_terms"]
        used_ids = set()

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
                print(f"🎥 Scene {idx+1}: Mixed 4K Footage ('{q}')...")
                clip_path = tmp / f"stock_{idx}.mp4"
                ok, source = fetch_mixed_media_clip(q, cut_dur, clip_path, used_ids=used_ids, cut_index=idx)
                if not ok:
                    make_animated_map(clip_path, cut_dur)
                shutil.copyfile(clip_path, seg_out)

        # 4. Concat
        concat_txt = tmp / "concat.txt"
        with open(concat_txt, "w") as f:
            for s in segments: f.write(f"file '{s.name}'\n")
        concat_mp4 = tmp / "concat.mp4"
        subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_txt), "-c", "copy", str(concat_mp4)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

        # 5. Smart BGM with Dynamic Synced Slicer
        bgm_file = tmp / "bgm.mp3"
        bgm_dir = WORKSPACE_ROOT / "fleet_engines/assets/bgm"
        available_bgms = sorted(list(bgm_dir.glob("*.mp3"))) if bgm_dir.exists() else []
        chosen_bgm = None
        if available_bgms:
            pillar_bgm = {1: "03_mystery", 2: "01_forensic", 3: "06_cosmic", 4: "02_psychology"}.get(pillar_id, "03_mystery")
            for b in available_bgms:
                if pillar_bgm in b.name:
                    chosen_bgm = b
                    break
            if not chosen_bgm:
                chosen_bgm = available_bgms[0]

        from dynamic_bgm_slicer import prepare_synced_bgm
        bgm_file, bgm_volume = prepare_synced_bgm(chosen_bgm, total_dur, bgm_file)

        # 5b. Smart Cinematic SFX Layering (Boom on hook, Paper on doc, Whoosh on cut)
        sfx_dir = WORKSPACE_ROOT / "fleet_engines/assets/sfx"
        boom_sfx = sfx_dir / "boom.wav"
        whoosh_sfx = sfx_dir / "whoosh.wav"
        paper_sfx = sfx_dir / "paper.wav"

        sfx_inputs = []
        sfx_filters = []
        if boom_sfx.exists() and whoosh_sfx.exists() and paper_sfx.exists():
            sfx_inputs.extend(["-i", str(boom_sfx), "-i", str(paper_sfx), "-i", str(whoosh_sfx)])
            c1_ms = int(cut_dur * 1000)
            c2_ms = int(cut_dur * 2 * 1000)
            sfx_filters.append("[3:a]volume=0.22[sfx0];")
            sfx_filters.append(f"[4:a]adelay={c1_ms}|{c1_ms},volume=0.25[sfx1];")
            sfx_filters.append(f"[5:a]adelay={c2_ms}|{c2_ms},volume=0.18[sfx2];")
            amix_str = "[1:a][drone][sfx0][sfx1][sfx2]amix=inputs=5:duration=first:dropout_transition=2[aout]"
        else:
            amix_str = "[1:a][drone]amix=inputs=2:duration=first[aout]"

        # 6. Burn ASS Subtitles & Mix Audio
        sub_escaped = str(ass_file).replace("\\", "/").replace(":", "\\:")
        filt = f"[0:v]ass='{sub_escaped}'[vout];[2:a]volume={bgm_volume:.2f}[drone];" + "".join(sfx_filters) + amix_str
        final_cmd = [
            "ffmpeg", "-y",
            "-i", str(concat_mp4), "-i", str(audio_file), "-i", str(bgm_file),
            *sfx_inputs,
            "-filter_complex", filt,
            "-map", "[vout]", "-map", "[aout]",
            "-c:v", "libx264", "-preset", "fast", "-c:a", "aac", "-threads", "2", str(final_video)
        ]
            
        print("⚡ Final Assembly...")
        try:
            subprocess.run(final_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        except subprocess.CalledProcessError as e:
            print(f"❌ FFmpeg error (code {e.returncode}):\n{e.stderr[-1500:]}")
            raise
        
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
        try:
            from channel_2.youtube_uploader import upload_short_to_youtube
        except ImportError:
            from fleet_engines.channel_2.youtube_uploader import upload_short_to_youtube
        video_p = Path(rendered_path)
        res = upload_short_to_youtube(video_p, title, desc, channel=2, privacy_status=args.privacy)
        if res:
            yt_url = res.get("video_url")
            
    if args.telegram and rendered_path:
        try:
            from telegram_dispatcher import send_fleet_video_to_telegram
        except ImportError:
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
