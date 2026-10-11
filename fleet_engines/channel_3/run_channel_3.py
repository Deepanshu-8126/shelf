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


# =============================================================================
# 1. PURE DEVANAGARI SUBTITLE ENGINE (ZERO WHISPER URDU HALLUCINATIONS)
# =============================================================================
async def synthesize_voice_with_boundaries(script: str, voice: str, out_raw: Path):
    """Generates studio voice and simultaneously extracts exact sentence timestamps."""
    import edge_tts
    # Punchy +3% pacing for retention
    c = edge_tts.Communicate(script, voice, rate="+3%")
    sentences = []
    with open(out_raw, "wb") as f:
        async for chunk in c.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] == "SentenceBoundary":
                st_s = chunk["offset"] / 10_000_000.0
                dur_s = chunk["duration"] / 10_000_000.0
                sentences.append({
                    "start": st_s,
                    "end": st_s + dur_s,
                    "duration": dur_s,
                    "text": chunk.get("text", "").strip()
                })
    return sentences


def build_pure_hindi_ass(sentences: list, ass_file: Path):
    """
    Creates kinetic ASS subtitles using 100% clean Devanagari Hindi text.
    Active word is bold bright yellow (&H0000FFFF&), inactive words white with heavy black stroke.
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
    events = []
    def fmt(t): return f"{int(t//3600):01d}:{int((t%3600)//60):02d}:{t%60:05.2f}"

    all_timed_words = []
    for s in sentences:
        words = [w for w in re.split(r"\s+", s["text"]) if w.strip()]
        if not words: continue
        total_chars = sum(len(w) for w in words)
        curr_t = s["start"]
        for w in words:
            w_dur = max(0.18, (len(w) / max(total_chars, 1)) * s["duration"])
            w_start = curr_t
            w_end = min(curr_t + w_dur, s["end"])
            all_timed_words.append({
                "word": w,
                "start": w_start,
                "end": w_end
            })
            curr_t = w_end

    # Group into punchy 2-3 word chunks
    for i in range(0, len(all_timed_words), 3):
        chunk = all_timed_words[i:i+3]
        if not chunk: continue
        for act_idx, w in enumerate(chunk):
            w_start, w_end = w["start"], w["end"]
            parts = []
            for idx_c, cw in enumerate(chunk):
                clean_w = cw["word"]
                if idx_c == act_idx:
                    parts.append(f"{{\\c&H0000FFFF&}}{clean_w}")
                else:
                    parts.append(f"{{\\c&H00FFFFFF&}}{clean_w}")
            events.append(f"Dialogue: 0,{fmt(w_start)},{fmt(w_end)},CosmicHindi,,0,0,0,,{' '.join(parts)}")

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

    return script_text.strip()


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
            word_count_target=75,
        )
        if custom_title: pkg["title"] = custom_title

    print(f"📌 Title: {pkg['title']}")
    print(f"📜 Script: {pkg['script']}\n")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    final_video = OUTPUT_DIR / f"channel3_cosmic_{pillar_id}_{int(time.time())}.mp4"

    # Select Edge-TTS voice
    edge_voice = "hi-IN-SwaraNeural" if voice_name.lower() in ["swara", "female", "hi_female"] else "hi-IN-MadhurNeural"
    voice_label = "Swara (Natural Documentary Female)" if "Swara" in edge_voice else "Madhur (Documentary Male)"

    with TemporaryDirectory() as tmp_str:
        tmp = Path(tmp_str)

        # 1. Voice Synthesis & Sentence Boundary Extraction
        print(f"🎙️ Generating High-Fidelity Voiceover ({voice_label})...")
        raw_tmp = tmp / "raw_edge.mp3"
        audio_file = tmp / "voice.mp3"

        sentences = asyncio.run(
            synthesize_voice_with_boundaries(pkg["script"], edge_voice, raw_tmp)
        )

        # Studio mastering chain: High pass + chest warmth + clarity + smooth broadcast compressor
        af = (
            "highpass=f=75,"
            "equalizer=f=120:width_type=h:width=80:g=2.2,"
            "equalizer=f=3400:width_type=h:width=600:g=2.5,"
            "acompressor=threshold=-16dB:ratio=2.8:attack=10:release=90,"
            "volume=1.05"
        )
        subprocess.run(["ffmpeg", "-y", "-i", str(raw_tmp), "-af", af, str(audio_file)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        print("✅ Native Hindi Voiceover Mastered Successfully!")

        dur_cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(audio_file)]
        total_dur = float(subprocess.run(dur_cmd, stdout=subprocess.PIPE, text=True).stdout.strip())
        print(f"⏱️ Audio Duration: {total_dur:.1f}s")

        # 2. Build Clean Devanagari Kinetic Subtitles
        print("📝 Generating Pure Devanagari Hindi Kinetic Subtitles...")
        ass_file = tmp / "subtitles.ass"
        build_pure_hindi_ass(sentences, ass_file)

        # 3. Rapid Beat Visual Planning (1.5 - 2.2s cuts)
        print("⚡ Planning Rapid 1.5 - 2.2s Visual Beats with Word-Level Semantic Sync...")
        beats = plan_beat_visuals(total_dur, sentences, pkg["script"], target_cut_dur=1.9)
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

        bgm_volume = 0.50
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
    parser.add_argument("--pillar", type=int, default=1, choices=[1, 2, 3])
    parser.add_argument("--topic", type=str, default="")
    parser.add_argument("--title", type=str, default="")
    parser.add_argument("--script", type=str, default="")
    parser.add_argument("--script_file", type=str, default="")
    parser.add_argument("--script_url", type=str, default="")
    parser.add_argument("--voice", type=str, default="swara", choices=["swara", "madhur"])
    parser.add_argument("--lang", type=str, default="hi", choices=["hi", "en"])
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
        from telegram_dispatcher import send_fleet_video_to_telegram
        p_info = PILLARS.get(args.pillar, PILLARS[1])
        raw_title = args.title.strip() if args.title else (args.topic.strip() if args.topic else p_info["default_topic"])
        clean_title = f"{raw_title} 🌌 #shorts #spacefacts"
        desc = (
            f"🚀 {raw_title}\n\n"
            f"Kya aapko brahmand ke is sach ke baare mein pata tha? Apni raye comment me batayein! 👇\n\n"
            f"#shorts #space #cosmic #science #whatif #spacefacts #hindifacts #viral #trending"
        )
        tags = ["space", "cosmic", "whatif", "space facts", "universe", "science", "shorts", "hindi facts", "viral"]
        print("📱 Dispatching Channel 3 Short to Telegram...")
        send_fleet_video_to_telegram(
            video_path=Path(rendered_path),
            channel=3,
            title=clean_title,
            description=desc,
            tags=tags
        )
