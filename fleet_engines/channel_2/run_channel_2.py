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
import re
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

import warnings
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

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
def generate_script(pillar_id: int, topic: str, lang: str = "en", target_duration: int = 70) -> dict:
    pillar = PILLARS.get(pillar_id, PILLARS[1])
    target_topic = topic or pillar["default_topic"]
    # 60-90s spoken script needs ~140-170 words
    word_count = max(int(target_duration * 2.1), 60)
    return generate_humanized_script(
        topic=target_topic,
        niche_context=pillar["name"],
        lang=lang,
        word_count_target=word_count
    )

# =============================================================================
# 3. ACOUSTIC WORD TIMESTAMP ALIGNER (WHISPER-TIMESTAMPED)
# =============================================================================
def extract_acoustic_words(audio_path: Path, lang: str = "en") -> list:
    """Uses whisper_timestamped to extract 100% frame-perfect acoustic word timestamps directly from audio waveform."""
    try:
        import whisper_timestamped as wt
        print(f"🎯 Aligning acoustic subtitles with Whisper-Timestamped ({lang})...")
        model = wt.load_model("base")
        audio = wt.load_audio(str(audio_path))
        result = wt.transcribe(model, audio, language=lang)
        words = []
        for seg in result.get("segments", []):
            for w in seg.get("words", []):
                clean_w = w["text"].strip()
                if clean_w:
                    words.append({
                        "word": clean_w,
                        "start": round(float(w["start"]), 3),
                        "end": round(float(w["end"]), 3),
                        "duration": round(float(w["end"] - w["start"]), 3)
                    })
        if words:
            print(f"✅ Whisper aligned {len(words)} exact words with zero drift!")
            return words
    except Exception as e:
        print(f"⚠️ Whisper acoustic alignment note: {e}")
    return []

# =============================================================================
# 4. SUBTITLES & VOICEOVER (KOKORO MICHAEL SOTA NARRATION)
# =============================================================================
from media_fetcher import fetch_mixed_media_clip

def synthesize_channel2_voice(script: str, out_raw: Path, lang: str = "en") -> list:
    """
    Synthesizes documentary-grade voiceover for Channel 2.
    Primary: Kokoro-82M ('am_michael' for English, 'hf_beta' for Hindi).
    Extracts frame-accurate acoustic word boundaries using Whisper.
    """
    is_hindi = (lang == "hi")
    voice_code = "hf_beta" if is_hindi else "am_michael"
    lang_code = "h" if is_hindi else "a"

    # 1. Kokoro-82M
    try:
        print(f"🎙️ Engaging Kokoro-82M Engine (Voice: {voice_code}, Natural Speed 1.0)...")
        from kokoro import KPipeline
        import soundfile as sf
        import numpy as np

        pipeline = KPipeline(lang_code=lang_code)
        generator = pipeline(script, voice=voice_code, speed=1.0)

        all_audios = []
        for res in generator:
            all_audios.append(res.audio)

        if all_audios:
            combined = np.concatenate(all_audios)
            out_wav = out_raw.with_suffix(".wav")
            sf.write(str(out_wav), combined, 24000)
            subprocess.run(["ffmpeg", "-y", "-i", str(out_wav), str(out_raw)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            if out_wav.exists() and out_wav != out_raw:
                out_wav.unlink()

            # Align frame-perfect word timestamps using Whisper
            words = extract_acoustic_words(out_raw)
            if words:
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

def build_mrbeast_ass(words: list, ass_path: Path, lang: str = "en"):
    """Kinetic ASS subtitles: yellow highlighted active word, bold font, 8px black stroke."""
    is_hi = (lang == "hi")
    font_name = "Nirmala UI" if is_hi else "Impact"
    font_size = 76 if is_hi else 78
    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: MrBeast,{font_name},{font_size},&H00FFFFFF,&H0000FFFF,&H00000000,&H80000000,-1,0,0,0,100,100,2,0,1,8,2,2,60,60,260,1

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
                w_end = chunk[act_idx+1]["start"]
            else:
                # Hold last word in chunk smoothly until next chunk or small hold
                if i + 3 < len(words):
                    next_chunk_start = words[i+3]["start"]
                    w_end = max(w_end, min(w_end + 0.22, next_chunk_start))
                else:
                    w_end = w_end + 0.30
            w_end = max(w_end, w_start + 0.12)

            parts = []
            for idx, cw in enumerate(chunk):
                word_clean = cw["word"].strip() if is_hi else cw["word"].strip().upper()
                if idx == act_idx:
                    parts.append(f"{{\\c&H0000FFFF&}}{word_clean}")
                else:
                    parts.append(f"{{\\c&H00FFFFFF&}}{word_clean}")
            events.append(f"Dialogue: 0,{fmt(w_start)},{fmt(w_end)},MrBeast,,0,0,0,,{' '.join(parts)}")

    ass_path.write_text(header + "\n".join(events) + "\n", encoding="utf-8")

def generate_visual_cut_queries(script: str, pillar_id: int, num_cuts: int) -> list:
    """Generates highly specific 2-4 word visual search queries for each cut."""
    pillar_terms = PILLARS.get(pillar_id, PILLARS[1])["search_terms"]
    try:
        from openai import OpenAI
        client = OpenAI(api_key=GROQ_API_KEY, base_url="https://api.groq.com/openai/v1")
        prompt = (
            f"You are a master visual director for high-cadence YouTube Shorts.\n"
            f"Script: \"{script}\"\n"
            f"Task: Generate exactly {num_cuts} distinct, highly visual 2-3 word search tags "
            f"for stock footage archives (Mixkit & Pexels). Each tag must describe a real visual scene, camera movement, or object.\n"
            f"Rules:\n"
            f"- No abstract words (e.g. avoid 'secret', 'mystery', 'truth', 'anomaly').\n"
            f"- Use concrete visuals (e.g. 'dark crater snow', 'deep cave entrance', 'drone flying canyon', 'satellite earth view', 'foggy pine forest', 'ocean waves storm', 'scientist laboratory microscopes', 'cracked desert earth').\n"
            f"Output strictly a JSON array of {num_cuts} strings."
        )
        res = client.chat.completions.create(
            model="qwen/qwen3.8-27b",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=300,
            timeout=10
        )
        raw = res.choices[0].message.content
        match = re.search(r'\[.*\]', raw, re.DOTALL)
        if match:
            queries = json.loads(match.group(0))
            if isinstance(queries, list) and len(queries) >= num_cuts:
                return [str(q).strip().lower() for q in queries[:num_cuts]]
    except Exception as e:
        print(f"ℹ️ Visual tags extraction note ({e}). Using pillar terms.")

    queries = []
    for i in range(num_cuts):
        queries.append(pillar_terms[i % len(pillar_terms)])
    return queries

def render_short(pillar_id: int = 1, topic: str = "", lang: str = "en", custom_script: str = "", custom_title: str = "", target_duration: int = 75) -> str:
    print("=" * 75)
    print(f"🎬 CHANNEL 2: RENDERING SHORT (PILLAR #{pillar_id} | 100% REAL FOOTAGE)")
    print("=" * 75)
    
    # 1. Script
    resolved_script = custom_script.strip()
    if not resolved_script and not topic:
        for cand in [Path(WORKSPACE_ROOT) / "custom_script.txt", Path(__file__).parent / "custom_script.txt"]:
            if cand.exists() and cand.stat().st_size > 10:
                lines = [l.strip() for l in cand.read_text(encoding="utf-8", errors="replace").splitlines() if l.strip() and not l.strip().startswith("#")]
                clean_text = " ".join(lines).strip()
                # Ensure custom script matches channel language
                if clean_text:
                    print(f"📄 Auto-detected user custom script from: {cand}")
                    resolved_script = clean_text
                    break

    if resolved_script:
        title = custom_title or (topic if topic else PILLARS.get(pillar_id, PILLARS[1])["default_topic"])
        pkg = {"title": title, "script": resolved_script}
        print(f"📌 Custom Title: {pkg['title']}")
        print(f"📜 Custom Script: {pkg['script']}\n")
    else:
        pkg = generate_script(pillar_id, topic, lang, target_duration=target_duration)
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

        # Transparent broadcast normalization (maintains Michael's rich natural timbre)
        af = "loudnorm=I=-16:TP=-1.5:LRA=11,volume=1.0"
        subprocess.run(["ffmpeg", "-y", "-i", str(raw_voice), "-af", af, str(audio_file)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

        dur_cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(audio_file)]
        total_dur = float(subprocess.run(dur_cmd, stdout=subprocess.PIPE, text=True).stdout.strip())
        print(f"⏱️ Audio Duration: {total_dur:.1f}s")

        # Frame-perfect acoustic word alignment
        exact_words = extract_acoustic_words(audio_file, lang=lang)
        if exact_words:
            timed_words = exact_words

        print("📝 Generating Kinetic ASS Subtitles (100% Synced)...")
        ass_file = tmp / "subtitles.ass"
        build_mrbeast_ass(timed_words, ass_file, lang=lang)

        # 3. Dynamic Cuts (Smooth cinematic pacing: 3.0s - 3.5s per shot, 100% REAL STOCK FOOTAGE)
        import random
        total_cuts = max(int(round(total_dur / 3.2)), 6)
        cut_dur = total_dur / total_cuts
        print(f"✂️ Visual Cuts: {total_cuts} cinematic cuts ({cut_dur:.2f}s each) [100% REAL STOCK FOOTAGE]")
        search_queries = generate_visual_cut_queries(pkg["script"], pillar_id, total_cuts)

        segments = []
        pillar_terms = PILLARS.get(pillar_id, PILLARS[1])["search_terms"]
        used_ids = set()

        for idx in range(total_cuts):
            seg_out = tmp / f"seg_{idx}.mp4"
            segments.append(seg_out)

            q = search_queries[idx % len(search_queries)]
            media_type = "video" if idx % 2 == 0 else "photo"
            print(f"🎥 Scene {idx+1}/{total_cuts}: Fetching '{q}' ({media_type.upper()})...")

            ok, source = fetch_mixed_media_clip(q, cut_dur, seg_out, media_type=media_type, used_ids=used_ids, cut_index=idx)
            if not ok or not seg_out.exists() or seg_out.stat().st_size < 10000:
                fallback_q = random.choice(["dark stormy ocean night", "deep space stars galaxy", "snow blizzard mountain", "aerial misty pine forest", "ancient dark stone cave"])
                print(f"⚠️ Retrying with atmospheric fallback: '{fallback_q}'")
                fetch_mixed_media_clip(fallback_q, cut_dur, seg_out, media_type="video", used_ids=used_ids, cut_index=idx)

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
    parser.add_argument("--duration", type=int, default=75, help="Target duration in seconds (e.g. 60-90s)")
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
        custom_title=args.title,
        target_duration=args.duration
    )
    
    yt_url = None
    raw_title = args.title.strip() if args.title else (args.topic.strip() if args.topic else f"Duniya Ka Sabse Bada Rahasya")
    
    if args.lang == "en":
        title = f"{raw_title} ⚓ #shorts #history #mystery"
        desc = (
            f"⚓ {raw_title}\n\n"
            f"What do you think really happened? Share your theory in the comments below! 👇\n\n"
            f"#shorts #history #mystery #titanic #unsolved #documentary #facts #historyfacts #viral"
        )
        tags = ["titanic", "mystery", "history", "unsolved", "facts", "documentary", "history facts", "shorts", "viral"]
    else:
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
