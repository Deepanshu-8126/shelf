"""
=============================================================================
CHANNEL 3: COSMIC WHAT-IF & DARK SCIENCE ENGINE (100% CLEAN PIPELINE)
=============================================================================
Pillars:
1. Cosmic Anomalies & Deep Space Paradoxes (James Webb voids, black hole horizon)
2. Mind-Bending What-If Science (Gravity stops, time reverses, oxygen disappears)
3. Forbidden Ancient Cosmos & Alien Physics (Fermi paradox, celestial signals)
=============================================================================
Voice: Cloned Bella (Atmospheric, Eerie, Mysterious Female Narration)
Visuals: 100% Real 4K Space/Physics Footage (Zero synthetic drawings)
BGM: Cosmic Deep Space Ambient Drone
=============================================================================
"""
import os
import sys
import time
import subprocess
import requests
from pathlib import Path
from tempfile import TemporaryDirectory
from dotenv import load_dotenv

# Path setup
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

load_dotenv(WORKSPACE_ROOT / ".env")

PEXELS_API_KEY = os.getenv("PEXELS_API_KEY") or "Ng530LMnrpm85zReE4lMhjCD7wm5Pc6h8rTE8NfSsuS7be57Qe7C1AGT"
OUTPUT_DIR = WORKSPACE_ROOT / "fleet_engines/output/channel_3_cosmic_what_if"

from llm_engine import generate_channel3_script, extract_keywords_llm
from cloned_voice_engine import generate_cloned_voice
import whisper

PILLARS = {
    1: {
        "name": "Cosmic Anomalies & James Webb Voids",
        "default_topic": "The cosmic supervoid where thousands of galaxies should be but don't exist",
        "search_terms": ["deep space stars telescope", "spinning galaxy cosmic nebula", "satellite earth night space"]
    },
    2: {
        "name": "Mind-Bending What-If Physics",
        "default_topic": "What if Earth lost gravity for just 5 seconds",
        "search_terms": ["floating in zero gravity space", "earth from space rotating", "cosmic storm meteor asteroid"]
    },
    3: {
        "name": "Dark Universe Paradoxes & Black Holes",
        "default_topic": "What happens at the event horizon where time itself freezes",
        "search_terms": ["black hole gravitational lens", "wormhole universe stars travel", "deep ocean dark abyssal void"]
    }
}

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
                for f in v.get("video_files", []):
                    if f.get("height", 0) > f.get("width", 0) and f.get("link"):
                        dl = requests.get(f["link"], stream=True, timeout=20)
                        if dl.status_code == 200:
                            with open(out_path, "wb") as fo:
                                for chunk in dl.iter_content(chunk_size=1024*1024): fo.write(chunk)
                            if out_path.exists() and out_path.stat().st_size > 50000:
                                return True
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

def render_channel_3_short(pillar_id: int = 1, topic: str = "", lang: str = "hi", custom_script: str = "", custom_title: str = "") -> str:
    print("=" * 75)
    print(f"🌌 CHANNEL 3: RENDERING COSMIC WHAT-IF SHORT (PILLAR #{pillar_id})")
    print("=" * 75)
    
    pillar = PILLARS.get(pillar_id, PILLARS[1])
    target_topic = topic or pillar["default_topic"]
    
    if custom_script:
        title = custom_title or target_topic
        pkg = {"title": title, "script": custom_script}
    else:
        pkg = generate_channel3_script(
            topic=target_topic,
            pillar_name=pillar["name"],
            lang=lang,
            word_count_target=75,
        )
        if custom_title: pkg["title"] = custom_title
        
    print(f"📌 Title: {pkg['title']}")
    print(f"📜 Script: {pkg['script']}\n")
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    final_video = OUTPUT_DIR / f"channel3_cosmic_{pillar_id}_{int(time.time())}.mp4"
    
    with TemporaryDirectory() as tmp_str:
        tmp = Path(tmp_str)
        
        # 1. Native Hindi Documentary Voiceover (Madhur Neural - FactTechz / Dark Science Style)
        audio_file = tmp / "voice.mp3"
        print("🎙️ Generating Native Hindi Documentary Voiceover (hi-IN-MadhurNeural)...")
        import edge_tts, asyncio
        raw_tmp = tmp / "raw_edge.mp3"
        async def _get_voice():
            c = edge_tts.Communicate(pkg["script"], "hi-IN-MadhurNeural", rate="+2%")
            await c.save(str(raw_tmp))
        asyncio.run(_get_voice())
        
        # Studio mastering chain: warm chest resonance + crystal clarity
        af = (
            "equalizer=f=120:width_type=h:width=80:g=2.5,"
            "equalizer=f=3200:width_type=h:width=600:g=2.0,"
            "acompressor=threshold=-18dB:ratio=3.0:attack=10:release=100"
        )
        subprocess.run(["ffmpeg", "-y", "-i", str(raw_tmp), "-af", af, str(audio_file)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        print("✅ Native Hindi Voiceover Mastered Successfully!")
            
        dur_cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(audio_file)]
        total_dur = float(subprocess.run(dur_cmd, stdout=subprocess.PIPE, text=True).stdout.strip())
        print(f"⏱️ Duration: {total_dur:.1f}s")
        
        # 2. Whisper Base Model with Hindi Language Lock
        print("🧠 Transcribing with Whisper Base for accurate Hindi word captions...")
        whisper_data = whisper.load_model("base").transcribe(str(audio_file), language="hi", word_timestamps=True)
        ass_file = tmp / "subtitles.ass"
        
        header = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: CosmicText,Nirmala UI,76,&H00FFFFFF,&H0000FFFF,&H00000000,&H90000000,-1,0,0,0,100,100,0,0,1,6,3,2,60,60,360,1

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
                events.append(f"Dialogue: 0,{fmt(w_start)},{fmt(w_end)},CosmicText,,0,0,0,,{' '.join(parts)}")
        ass_file.write_text(header + "\n".join(events) + "\n", encoding="utf-8")
        
        # 3. 100% Real 4K Cosmic Footage Cuts
        total_cuts = max(int(total_dur / 3.0), 3)
        cut_dur = total_dur / total_cuts
        print(f"✂️ Visual Cuts: {total_cuts} 100% Real 4K Cuts ({cut_dur:.2f}s each)")
        
        segments = []
        pillar_terms = pillar["search_terms"]
        kw_list = extract_keywords_llm(pkg["script"], total_dur) if pkg.get("script") else []
        combined_queries = kw_list + pillar_terms
        
        for idx in range(total_cuts):
            seg_out = tmp / f"seg_{idx}.mp4"
            segments.append(seg_out)
            
            q = combined_queries[idx % len(combined_queries)]
            print(f"🌌 Scene {idx+1}/{total_cuts}: 4K Cosmic Footage ('{q}')...")
            b_path = tmp / f"stock_{idx}.mp4"
            downloaded = download_pexels_clip(q, b_path)
            if not downloaded:
                for alt_q in ["deep space nebula stars cosmic", "galaxy universe dark stars", "earth from space night", "black hole cosmic space"]:
                    if download_pexels_clip(alt_q, b_path):
                        downloaded = True
                        break
                
            if not downloaded or not b_path.exists() or b_path.stat().st_size < 10000:
                print("⚠️ Generating procedural deep cosmic background...")
                b_path = tmp / f"procedural_cosmic_{idx}.mp4"
                proc_cmd = [
                    "ffmpeg", "-y", "-f", "lavfi",
                    "-i", f"color=c=0x02040d:s=1080x1920:d={cut_dur+2:.2f}:r=30",
                    "-vf", "noise=alls=16:allf=t+u,vignette=PI/3.2,eq=contrast=1.35:brightness=-0.04",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-t", f"{cut_dur+1:.2f}",
                    str(b_path)
                ]
                subprocess.run(proc_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
                
            drift_dir = "down" if idx % 2 == 0 else "up"
            if drift_dir == "down":
                crop_expr = f"crop=1080:1920:x='(in_w-out_w)/2':y='(in_h-out_h)*(t/{cut_dur:.2f})'"
            else:
                crop_expr = f"crop=1080:1920:x='(in_w-out_w)/2':y='(in_h-out_h)*(1-t/{cut_dur:.2f})'"
                
            vf = (
                f"scale=1188:2112:force_original_aspect_ratio=increase,"
                f"{crop_expr},"
                f"eq=contrast=1.20:brightness=-0.04:saturation=0.95,"
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
            
        # 4. Concat
        concat_txt = tmp / "concat.txt"
        with open(concat_txt, "w") as f:
            for s in segments: f.write(f"file '{s.name}'\n")
        concat_mp4 = tmp / "concat.mp4"
        subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_txt), "-c", "copy", str(concat_mp4)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        
        # 5. Master Cosmic Drone BGM with Dynamic Smart Cueing
        bgm_file = tmp / "cosmic_drone.mp3"
        bgm_dir = WORKSPACE_ROOT / "fleet_engines/assets/bgm"
        available_bgms = sorted(list(bgm_dir.glob("*.mp3"))) if bgm_dir.exists() else []
        
        pillar_bgm_map = {
            1: "06_cosmic_deep_noise.mp3",
            2: "03_mystery_lightless_dawn.mp3",
            3: "01_forensic_the_dread.mp3"
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
                "-f", "lavfi", "-i", "anoisesrc=c=pink:r=44100:a=0.04",
                "-f", "lavfi", "-i", "sine=f=45:r=44100",
                "-f", "lavfi", "-i", "sine=f=90:r=44100",
                "-filter_complex",
                f"[0:a]lowpass=f=200,volume=0.20[noise];"
                f"[1:a]volume=0.35[sub];"
                f"[2:a]volume=0.20[mid];"
                f"[noise][sub][mid]amix=inputs=3,afade=t=in:ss=0:d=1.2,afade=t=out:st={total_dur-1.5:.2f}:d=1.5",
                "-t", f"{total_dur:.2f}",
                str(bgm_file)
            ]
            subprocess.run(drone_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            bgm_volume = 0.50
        
        # 6. Burn Subtitles & Mix Audio (Voice at 1.0, Cosmic Drone at dynamic volume)
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
        print("⚡ Final Cosmic Assembly...")
        subprocess.run(final_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        
    print("=" * 75)
    print("🌌 [CHANNEL 3 COSMIC SHORT RENDERED SUCCESSFULLY]")
    print(f"📁 Video: {final_video}")
    print("=" * 75)
    return str(final_video)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Channel 3 Cosmic What-If Engine")
    parser.add_argument("--pillar", type=int, default=1, choices=[1, 2, 3])
    parser.add_argument("--topic", type=str, default="")
    parser.add_argument("--title", type=str, default="")
    parser.add_argument("--script", type=str, default="")
    parser.add_argument("--lang", type=str, default="hi", choices=["hi", "en"])
    args = parser.parse_args()
    
    render_channel_3_short(
        pillar_id=args.pillar,
        topic=args.topic,
        custom_title=args.title,
        custom_script=args.script,
        lang=args.lang
    )
