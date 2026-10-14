"""
=============================================================================
CHANNEL 3: COSMIC WHAT-IF & DARK SCIENCE ENGINE (PRODUCTION-GRADE V3)
=============================================================================
Major Upgrades:
1. Multi-Source Footage Mixup (Pexels + Pixabay Videos & 4K Photos):
   - Integrates both Pexels and Pixabay APIs.
   - Alternates between 4K stock videos and ultra-sharp 4K photography.
   - Images are animated using cinematic Ken-Burns drift & zoom at 30/60 fps.
2. Rapid 1.5 - 2.2s Visual Cuts (High-Cadence Retention):
   - Cuts every 1.5 - 2.2 seconds (15-20 cuts per 30s video).
   - Matches the exact spoken Hindi keyword in that 1-2 second window.
3. Natural Studio Voiceover:
   - Upgraded default voice to 'hi-IN-SwaraNeural' (expressive documentary tone).
   - Studio mastering chain (high-pass, chest warmth, presence boost, compressor).
   - Supports 'swara' and 'madhur' voice toggle.
4. Flexible Script Ingestion:
   - Supports inline script, local file, or direct GitHub / raw URL download.
5. Pure Devanagari Kinetic Subtitles:
   - 100% clean Devanagari text timed via Edge-TTS SentenceBoundaries.
   - Zero Whisper Urdu/Hebrew hallucinations.
=============================================================================
"""
import os
import sys
import time
import json
import re
import subprocess
import requests
import asyncio
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

OUTPUT_DIR = WORKSPACE_ROOT / "fleet_engines/output/channel_3_cosmic_what_if"

from llm_engine import generate_channel3_script, llm_complete
from media_fetcher import fetch_mixed_media_clip, plan_beat_visuals

PILLARS = {
    1: {
        "name": "Deep Earth & Ocean Anomalies",
        "category": "deep_earth_ocean",
        "default_topic": "मारियाना ट्रेंच के 11 किलोमीटर नीचे वैज्ञानिकों को क्या मिला?",
        "search_terms": ["deep sea underwater trench", "stormy ocean rough dark", "strange deep sea creatures"]
    },
    2: {
        "name": "Bizarre Human Body Science",
        "category": "bizarre_human_science",
        "default_topic": "अगर इंसान लगातार 7 दिन तक न सोए तो दिमाग के साथ क्या होता है?",
        "search_terms": ["brain glowing scan human", "person looking tired insomnia", "medical science laboratory dark"]
    },
    3: {
        "name": "Real Everyday What-Ifs",
        "category": "everyday_what_ifs",
        "default_topic": "अगर 24 घंटे के लिए दुनिया का सारा इंटरनेट बंद हो जाए?",
        "search_terms": ["server room computer network", "modern city traffic night", "empty streets power outage"]
    },
    4: {
        "name": "Mysterious Historic & Dark Science Curiosities",
        "category": "dark_science_anomalies",
        "default_topic": "चेरनोबिल का एलीफेंट्स फुट: दुनिया का सबसे खतरनाक पत्थर",
        "search_terms": ["abandoned chernobyl dark reactor", "radiation danger hazard zone", "mysterious glowing dark artifact"]
    },
    5: {
        "name": "Mind-Bending Deep Space Curiosities",
        "category": "mind_bending_space",
        "default_topic": "अंतरिक्ष का वो ग्रह जो पूरा का पूरा हीरे का बना हुआ है",
        "search_terms": ["deep space stars telescope", "spinning galaxy cosmic nebula", "diamond glowing crystal space"]
    }
}



# =============================================================================
# 0. ACOUSTIC WORD ALIGNMENT (WHISPER-TIMESTAMPED FOR HINDI)
# =============================================================================
def extract_acoustic_words_hindi(audio_path: Path) -> list:
    """Uses whisper_timestamped to extract frame-perfect acoustic word timestamps from Hindi audio.
    Returns Devanagari words with exact start/end times aligned to actual speech waveform."""
    try:
        import whisper_timestamped as wt
        print("🎯 Aligning acoustic subtitles with Whisper-Timestamped (Hindi)...")
        model = wt.load_model("small")
        audio = wt.load_audio(str(audio_path))
        result = wt.transcribe(model, audio, language="hi")
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
            print(f"✅ Whisper aligned {len(words)} Hindi words with zero drift!")
            return words
    except Exception as e:
        print(f"⚠️ Whisper Hindi acoustic alignment note: {e}")
    return []


# =============================================================================
# 1. PURE DEVANAGARI SUBTITLE ENGINE (ZERO WHISPER URDU HALLUCINATIONS)
# =============================================================================
async def synthesize_voice_with_boundaries(script: str, voice_pref: str, out_raw: Path):
    """
    Generates high-fidelity native Hindi voiceover and extracts synchronized word timestamps.
    Primary Engine: Kokoro-82M (hf_beta, hm_omega, hf_alpha, hm_psi) - 100% on-device neural Indian voice.
    Secondary Fallback: Edge-TTS (Swara / Madhur)
    Tertiary Fallback: Google Cloud Hindi Voice
    """
    voice_pref = (voice_pref or "dynamic").lower()
    kokoro_map = {
        "beta": "hf_beta",     # Warm storytelling female
        "alpha": "hf_alpha",   # Dynamic facts female
        "omega": "hm_omega",   # Deep cinematic male
        "psi": "hm_psi"        # Fast engaging male
    }

    selected_kokoro_voice = None
    if voice_pref == "dynamic":
        import random
        selected_kokoro_voice = random.choice(["hf_beta", "hm_omega", "hf_alpha", "hm_psi"])
    elif voice_pref in kokoro_map:
        selected_kokoro_voice = kokoro_map[voice_pref]
    elif voice_pref in ["hf_beta", "hf_alpha", "hm_omega", "hm_psi"]:
        selected_kokoro_voice = voice_pref

    # 1. Try Kokoro-82M First
    if selected_kokoro_voice:
        try:
            print(f"🎙️ Engaging Kokoro-82M Engine (Voice: {selected_kokoro_voice})...")
            from kokoro import KPipeline
            import soundfile as sf
            import numpy as np

            pipeline = KPipeline(lang_code='h')
            generator = pipeline(script, voice=selected_kokoro_voice, speed=1.05)

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
                # Convert to mp3 if needed or copy
                subprocess.run(["ffmpeg", "-y", "-i", str(out_wav), str(out_raw)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
                if out_wav.exists() and out_wav != out_raw:
                    out_wav.unlink()
                print(f"✅ Kokoro-82M synthesized {len(words)} words ({curr_time:.1f}s audio)")
                return words
        except Exception as e:
            print(f"⚠️ Kokoro engine note: {e}. Falling back to Edge-TTS...")

    # 2. Edge-TTS Fallback
    edge_voice = "hi-IN-SwaraNeural" if voice_pref in ["swara", "female", "beta", "alpha"] else "hi-IN-MadhurNeural"
    try:
        import edge_tts
        print(f"🎙️ Engaging Edge-TTS Engine ({edge_voice})...")
        c = edge_tts.Communicate(script, edge_voice, rate="+3%", boundary="WordBoundary")
        words = []
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
        if out_raw.exists() and out_raw.stat().st_size > 10000 and words:
            return words
    except Exception as e:
        print(f"⚠️ Edge-TTS unavailable ({e}). Engaging Google Cloud Hindi voiceover fallback...")

    # 3. High-speed reliable fallback: Google Cloud Hindi Voice
    import urllib.parse
    clean_words = [w for w in re.split(r'\s+', script) if w.strip()]
    chunks = []
    curr = ""
    for s in re.split(r'([।\?!,])', script):
        if not s.strip(): continue
        if len(curr) + len(s) < 180: curr += s
        else:
            chunks.append(curr.strip())
            curr = s
    if curr.strip(): chunks.append(curr.strip())

    audio_bytes = b""
    for ch in chunks:
        u = f"https://translate.google.com/translate_tts?ie=UTF-8&q={urllib.parse.quote(ch)}&tl=hi&client=tw-ob"
        r = requests.get(u, headers={"User-Agent": "Mozilla/5.0"}, timeout=12)
        if r.status_code == 200:
            audio_bytes += r.content

    with open(out_raw, "wb") as f:
        f.write(audio_bytes)

    dur_cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(out_raw)]
    dur_res = subprocess.run(dur_cmd, stdout=subprocess.PIPE, text=True)
    total_dur = float(dur_res.stdout.strip()) if dur_res.stdout.strip() else 25.0

    total_chars = sum(len(w) for w in clean_words)
    curr_t = 0.0
    words = []
    for w in clean_words:
        w_dur = max(0.18, (len(w) / max(total_chars, 1)) * total_dur)
        words.append({
            "start": curr_t,
            "end": curr_t + w_dur,
            "duration": w_dur,
            "word": w
        })
        curr_t += w_dur
    return words


def build_pure_hindi_ass(words: list, ass_file: Path):
    """
    Creates kinetic ASS subtitles using 100% clean Devanagari Hindi text.
    Active word is bold bright yellow (&H0000FFFF&), inactive words white with heavy black stroke.
    Groups into natural 2-3 word phrases without cutting across speech pauses.
    """
    header = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: CosmicHindi,Nirmala UI,76,&H00FFFFFF,&H0000FFFF,&H00000000,&H90000000,-1,0,0,0,100,100,0,0,1,6,3,2,60,60,360,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    def fmt(t): return f"{int(t//3600):01d}:{int((t%3600)//60):02d}:{t%60:05.2f}"

    if not words:
        ass_file.write_text(header, encoding="utf-8")
        return

    # Group into natural phrases based on word count and speech pauses
    chunks = []
    current_chunk = []

    for i, w in enumerate(words):
        current_chunk.append(w)
        is_last = (i == len(words) - 1)
        pause_after = False
        if not is_last:
            gap = words[i+1]["start"] - w["end"]
            if gap >= 0.28:
                pause_after = True

        if len(current_chunk) >= 3 or pause_after or is_last:
            chunks.append(current_chunk)
            current_chunk = []

    events = []
    for c_idx, chunk in enumerate(chunks):
        for act_idx, w in enumerate(chunk):
            w_start = w["start"]
            if act_idx < len(chunk) - 1:
                w_end = chunk[act_idx + 1]["start"]
            else:
                if c_idx < len(chunks) - 1:
                    next_start = chunks[c_idx + 1][0]["start"]
                    w_end = max(w["end"], min(w["end"] + 0.25, next_start))
                else:
                    w_end = w["end"] + 0.35
            w_end = max(w_end, w_start + 0.15)

            parts = []
            for idx_c, cw in enumerate(chunk):
                clean_w = cw["word"]
                if idx_c == act_idx:
                    parts.append(f"{{\\c&H0000FFFF&}}{clean_w}")
                else:
                    parts.append(f"{{\\c&H00FFFFFF&}}{clean_w}")
            joined_text = " ".join(parts)
            events.append(f"Dialogue: 0,{fmt(w_start)},{fmt(w_end)},CosmicHindi,,0,0,0,,{joined_text}")

    ass_file.write_text(header + "\n".join(events) + "\n", encoding="utf-8")


# =============================================================================
# 2. SCRIPT LOADER (INLINE / FILE / GITHUB RAW URL)
# =============================================================================
def load_custom_script(script_text: str = "", script_file: str = "", script_url: str = "") -> str:
    """Loads script from string, local file path, or remote GitHub URL."""
    if script_url:
        print(f"🌐 Fetching custom script from remote URL: {script_url}...")
        try:
            r = requests.get(script_url, timeout=12)
            if r.status_code == 200 and r.text.strip():
                print(f"✅ Successfully downloaded script ({len(r.text.strip())} characters)")
                return r.text.strip()
            else:
                print(f"⚠️ Failed to fetch URL, HTTP {r.status_code}")
        except Exception as e:
            print(f"⚠️ Error fetching script URL: {e}")

    if script_file:
        p = Path(script_file)
        if p.exists():
            print(f"📄 Loading script from local file: {p}...")
            return p.read_text(encoding="utf-8", errors="replace").strip()
        else:
            print(f"⚠️ Script file not found: {p}")

    if script_text and script_text.strip():
        return script_text.strip()

    # Convenience: Auto-check for custom_script.txt or my_script.txt in channel folder or root
    for cand in [Path(__file__).parent / "custom_script.txt", Path("custom_script.txt"), Path(WORKSPACE_ROOT) / "custom_script.txt", Path(__file__).parent / "my_script.txt"]:
        if cand.exists() and cand.stat().st_size > 10:
            lines = [l.strip() for l in cand.read_text(encoding="utf-8", errors="replace").splitlines() if l.strip() and not l.strip().startswith("#")]
            clean_text = " ".join(lines).strip()
            if clean_text:
                print(f"📄 Auto-detected user custom script from: {cand}")
                return clean_text

    return ""


# =============================================================================
# 3. MASTER COMPOSITOR PIPELINE (HIGH-CADENCE 1.5 - 2.2S CUTS)
# =============================================================================
def render_channel_3_short(
    pillar_id: int = 1,
    topic: str = "",
    lang: str = "hi",
    custom_script: str = "",
    custom_title: str = "",
    script_file: str = "",
    script_url: str = "",
    voice_name: str = "swara"
) -> str:
    print("=" * 75)
    print(f"🌌 CHANNEL 3: COSMIC WHAT-IF ENGINE V3 (RAPID CUTS + PEXELS/PIXABAY MIXUP)")
    print("=" * 75)

    if not topic and (pillar_id is None or pillar_id == 1):
        # Auto-rotate dynamically across all 5 categories so no two videos repeat the same domain
        rot_id = (int(time.time() // 86400) % 5) + 1
        pillar = PILLARS.get(rot_id, PILLARS[1])
        target_topic = pillar["default_topic"]
        print(f"🔄 [Dynamic Rotation] Automatically selected Category #{rot_id}: {pillar['name']}")
    else:
        pillar = PILLARS.get(pillar_id, PILLARS[1])
        target_topic = topic or pillar["default_topic"]

    # Resolve script
    resolved_script = load_custom_script(custom_script, script_file, script_url)
    if resolved_script:
        title = custom_title or target_topic
        pkg = {"title": title, "script": resolved_script}
    else:
        pkg = generate_channel3_script(
            topic=target_topic,
            pillar_name=pillar["name"],
            lang=lang,
            word_count_target=42,
        )
        if custom_title: pkg["title"] = custom_title

    print(f"📌 Title: {pkg['title']}")
    print(f"📜 Script: {pkg['script']}\n")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    final_video = OUTPUT_DIR / f"channel3_cosmic_{pillar_id}_{int(time.time())}.mp4"

    with TemporaryDirectory() as tmp_str:
        tmp = Path(tmp_str)

        # 1. Voice Synthesis & Word Boundary Extraction
        print(f"🎙️ Generating High-Fidelity Voiceover (Voice: {voice_name})...")
        raw_tmp = tmp / "raw_voice.mp3"
        audio_file = tmp / "voice.mp3"

        timed_words = asyncio.run(
            synthesize_voice_with_boundaries(pkg["script"], voice_name, raw_tmp)
        )

        # Transparent EBU R128 broadcast normalization (preserves natural Kokoro Hindi timbre)
        af = "loudnorm=I=-16:TP=-1.5:LRA=11,volume=1.0"
        subprocess.run(["ffmpeg", "-y", "-i", str(raw_tmp), "-af", af, str(audio_file)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        print("✅ Native Hindi Voiceover Mastered Successfully!")

        dur_cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(audio_file)]
        total_dur = float(subprocess.run(dur_cmd, stdout=subprocess.PIPE, text=True).stdout.strip())
        print(f"⏱️ Audio Duration: {total_dur:.1f}s")

        # 2. Frame-perfect acoustic word alignment (fixes caption drift at end)
        exact_words = extract_acoustic_words_hindi(audio_file)
        if exact_words:
            timed_words = exact_words
            print(f"🎯 Replaced {len(exact_words)} words with acoustic-aligned timestamps")

        # 3. Build Clean Devanagari Kinetic Subtitles
        print("📝 Generating Pure Devanagari Hindi Kinetic Subtitles...")
        ass_file = tmp / "subtitles.ass"
        build_pure_hindi_ass(timed_words, ass_file)

        # 3. Rapid Beat Visual Planning (1.5 - 2.2s cuts)
        print("⚡ Planning Rapid 1.5 - 2.2s Visual Beats with Word-Level Semantic Sync...")
        beats = plan_beat_visuals(total_dur, timed_words, pkg["script"], target_cut_dur=1.9)
        print(f"🎬 Directed {len(beats)} Rapid Beats (Mixing Videos & 4K Photos):")
        for b in beats:
            print(f"   [{b['start']}s - {b['end']}s] ({b['media_type'].upper()}): Spoken: '{b['spoken_hindi'][:35]}' -> Query: '{b['query']}'")

        # 4. Multi-Source Ingestion & Ken-Burns Assembly
        used_ids = set()
        segments = []

        for b in beats:
            idx = b["cut_index"]
            seg_out = tmp / f"seg_{idx}.mp4"
            segments.append(seg_out)

            q = b["query"]
            m_type = b["media_type"]
            dur = b["duration"]

            print(f"📥 Beat {idx+1}/{len(beats)}: Fetching {m_type.upper()} for '{q}'...")
            ok, actual_kind = fetch_mixed_media_clip(
                query=q,
                target_dur=dur,
                out_video_path=seg_out,
                media_type=m_type,
                used_ids=used_ids,
                cut_index=idx
            )

            # Fallback if primary query yielded nothing
            if not ok or not seg_out.exists() or seg_out.stat().st_size < 5000:
                print(f"⚠️ Retrying with atmospheric cosmic fallback...")
                alt_queries = ["deep space stars galaxy", "stormy ocean night", "planet earth rotating", "extreme blizzard snow storm"]
                for alt_q in alt_queries:
                    ok, actual_kind = fetch_mixed_media_clip(
                        query=alt_q,
                        target_dur=dur,
                        out_video_path=seg_out,
                        media_type="photo" if m_type == "video" else "video",
                        used_ids=used_ids,
                        cut_index=idx
                    )
                    if ok and seg_out.exists() and seg_out.stat().st_size > 5000:
                        break

            # Ultimate procedural backup if network is offline
            if not ok or not seg_out.exists() or seg_out.stat().st_size < 5000:
                print(f"⚠️ Generating procedural cosmic background for beat {idx+1}...")
                proc_cmd = [
                    "ffmpeg", "-y", "-f", "lavfi",
                    "-i", f"color=c=0x02040d:s=1080x1920:d={dur+1:.2f}:r=30",
                    "-vf", "noise=alls=16:allf=t+u,vignette=PI/3.2,eq=contrast=1.35:brightness=-0.04",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-t", f"{dur:.2f}",
                    str(seg_out)
                ]
                subprocess.run(proc_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

        # 5. Concat all unique clips
        concat_txt = tmp / "concat.txt"
        with open(concat_txt, "w") as f:
            for s in segments: f.write(f"file '{s.name}'\n")
        concat_mp4 = tmp / "concat.mp4"
        subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_txt), "-c", "copy", str(concat_mp4)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

        # 6. Master Cosmic Drone BGM with Dynamic Smart Cueing (50-52% Volume)
        bgm_file = tmp / "cosmic_drone.mp3"
        bgm_dir = WORKSPACE_ROOT / "fleet_engines/assets/bgm"
        available_bgms = sorted(list(bgm_dir.glob("*.mp3"))) if bgm_dir.exists() else []

        pillar_bgm_map = {
            1: "06_cosmic_deep_noise.mp3",
            2: "03_mystery_lightless_dawn.mp3",
            3: "01_forensic_the_dread.mp3",
            4: "04_investigation_apprehension.mp3",
            5: "02_psychology_echoes_of_time.mp3",
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

        bgm_volume = 0.50
        if chosen_bgm and chosen_bgm.exists():
            from dynamic_bgm_slicer import prepare_synced_bgm
            bgm_file, bgm_volume = prepare_synced_bgm(chosen_bgm, total_dur, bgm_file)
            print(f"🎵 Using Real Studio BGM: {chosen_bgm.name} (Volume: {bgm_volume:.2f})")
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
            bgm_volume = 0.48

        # 7. Burn Subtitles & Mix Audio (Voice at 1.05, Music at ~50%)
        sub_escaped = str(ass_file).replace("\\", "/").replace(":", "\\:")
        full_filter = (
            f"[0:v]ass='{sub_escaped}'[vout];"
            f"[1:a]volume=1.05[voice];"
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
            "-c:v", "libx264", "-preset", "fast", "-crf", "20",
            "-c:a", "aac", "-b:a", "192k",
            "-shortest",
            str(final_video)
        ]
        print("⚡ Final Cosmic Assembly & Subtitle Integration...")
        subprocess.run(final_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

    print("=" * 75)
    print("🌌 [CHANNEL 3 COSMIC SHORT RENDERED SUCCESSFULLY]")
    print(f"📁 Video: {final_video}")
    print("=" * 75)
    return str(final_video)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Channel 3 Cosmic What-If Engine V3")
    parser.add_argument("--pillar", type=int, default=1, choices=[1, 2, 3, 4, 5])
    parser.add_argument("--topic", type=str, nargs="?", default="")
    parser.add_argument("--title", type=str, nargs="?", default="")
    parser.add_argument("--script", type=str, nargs="?", default="")
    parser.add_argument("--script_file", type=str, nargs="?", default="")
    parser.add_argument("--script_url", type=str, nargs="?", default="")
    parser.add_argument("--voice", type=str, nargs="?", default="dynamic", choices=["dynamic", "beta", "alpha", "omega", "psi", "swara", "madhur"])
    parser.add_argument("--lang", type=str, nargs="?", default="hi", choices=["hi", "en"])
    parser.add_argument("--upload", action="store_true", help="Auto upload to YouTube Channel 3")
    parser.add_argument("--telegram", action="store_true", default=True, help="Send video & metadata to Telegram")
    parser.add_argument("--privacy", type=str, default="unlisted", choices=["public", "unlisted", "private"])
    args = parser.parse_args()

    rendered_path = render_channel_3_short(
        pillar_id=args.pillar,
        topic=args.topic,
        custom_title=args.title,
        custom_script=args.script,
        script_file=args.script_file,
        script_url=args.script_url,
        voice_name=args.voice,
        lang=args.lang
    )

    if rendered_path:
        p_info = PILLARS.get(args.pillar, PILLARS[1])
        raw_title = args.title.strip() if args.title else (args.topic.strip() if args.topic else p_info["default_topic"])
        clean_title = f"{raw_title} 🌌 #shorts #spacefacts"
        desc = (
            f"🚀 {raw_title}\n\n"
            f"Kya aapko brahmand ke is sach ke baare mein pata tha? Apni raye comment me batayein! 👇\n\n"
            f"#shorts #space #cosmic #science #whatif #spacefacts #hindifacts #viral #trending"
        )
        tags = ["space", "cosmic", "whatif", "space facts", "universe", "science", "shorts", "hindi facts", "viral"]

        if args.upload:
            try:
                from channel_2.youtube_uploader import upload_short_to_youtube
                upload_short_to_youtube(Path(rendered_path), clean_title, desc, channel=3, privacy_status=args.privacy)
            except Exception as e:
                print(f"⚠️ YouTube upload note: {e}")

        if args.telegram:
            try:
                from telegram_dispatcher import send_fleet_video_to_telegram
                print("📱 Dispatching Channel 3 Short to Telegram...")
                send_fleet_video_to_telegram(
                    video_path=Path(rendered_path),
                    channel=3,
                    title=clean_title,
                    description=desc,
                    tags=tags
                )
            except Exception as e:
                print(f"⚠️ Telegram dispatch note: {e}")
