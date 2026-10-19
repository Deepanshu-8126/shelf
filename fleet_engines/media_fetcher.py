"""
=============================================================================
UNIFIED MEDIA FETCHER & VISUAL DIRECTOR (COMPACT & ULTRA-FAST)
=============================================================================
Features:
1. Multi-Source Footage Mixup: Pexels & Pixabay Videos + 4K Ken-Burns Photos.
2. Fast HTTP Session with Keep-Alive for 2x faster downloads.
3. Word-Level Hindi Semantic Visual Planner (1.5 - 2.2s Cuts for High Retention).
4. Strict Anti-Duplication & Multi-Directional Cinematic Drift (Down/Up/Zoom).
=============================================================================
"""
import os
import re
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import json
import random
import requests
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Tuple
from dotenv import load_dotenv

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(WORKSPACE_ROOT / ".env")

PEXELS_KEY = os.getenv("PEXELS_API_KEY") or "Ng530LMnrpm85zReE4lMhjCD7wm5Pc6h8rTE8NfSsuS7be57Qe7C1AGT"
PIXABAY_KEY = os.getenv("PIXABAY_API_KEY") or "57841834-fccecee02edcc2dfb5cf90fc0"

SESSION = requests.Session()


# ---------------------------------------------------------------------------
# 1. CORE STREAMING DOWNLOAD & KEN-BURNS RENDERER
# ---------------------------------------------------------------------------
def _download_stream(url: str, out_path: Path, min_bytes: int = 15000, headers: dict = None) -> bool:
    try:
        r = SESSION.get(url, headers=headers or {}, stream=True, timeout=16)
        if r.status_code == 200:
            with open(out_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=1024 * 512):
                    if chunk: f.write(chunk)
            return out_path.exists() and out_path.stat().st_size >= min_bytes
    except Exception:
        pass
    return False


def convert_image_to_kenburns(img_path: Path, out_path: Path, duration: float, direction: str = "down") -> bool:
    """Converts high-res photo into animated 1080x1920 vertical video clip."""
    dur = max(duration, 1.0)
    crop = (f"crop=1080:1920:x='(in_w-out_w)/2':y='(in_h-out_h)*(t/{dur:.2f})'" if direction == "down"
            else f"crop=1080:1920:x='(in_w-out_w)/2':y='(in_h-out_h)*(1-t/{dur:.2f})'" if direction == "up"
            else "crop=1080:1920:x='(in_w-out_w)/2':y='(in_h-out_h)/2'")
    vf = f"scale=1242:2208:force_original_aspect_ratio=increase,{crop},eq=contrast=1.12:saturation=1.05:brightness=-0.02,vignette=PI/4.5"
    cmd = ["ffmpeg", "-y", "-loop", "1", "-i", str(img_path), "-vf", vf, "-t", f"{dur:.2f}", "-r", "30",
           "-c:v", "libx264", "-preset", "fast", "-crf", "19", "-pix_fmt", "yuv420p", "-an", str(out_path)]
    return subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0 and out_path.exists()


def _render_video_segment(src: Path, dst: Path, dur: float, direction: str = "down"):
    """Crops landscape/portrait video into 1080x1920 with high-contrast grading."""
    crop = (f"crop=1080:1920:x='(in_w-out_w)/2':y='(in_h-out_h)*(t/{dur:.2f})'" if direction == "down"
            else f"crop=1080:1920:x='(in_w-out_w)/2':y='(in_h-out_h)*(1-t/{dur:.2f})'")
    vf = f"scale=1188:2112:force_original_aspect_ratio=increase,{crop},eq=contrast=1.18:brightness=-0.03:saturation=0.98,vignette=PI/4.2"
    cmd = ["ffmpeg", "-y", "-stream_loop", "-1", "-i", str(src), "-vf", vf, "-t", f"{dur:.2f}", "-r", "30",
           "-c:v", "libx264", "-preset", "fast", "-crf", "19", "-pix_fmt", "yuv420p", "-an", str(dst)]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)


# ---------------------------------------------------------------------------
# 2. PEXELS & PIXABAY MULTI-SOURCE INGESTION
# ---------------------------------------------------------------------------
def _fetch_pexels(query: str, is_video: bool, out_path: Path, used_ids: set) -> bool:
    if not PEXELS_KEY: return False
    headers = {"Authorization": PEXELS_KEY}
    try:
        if is_video:
            for url in [f"https://api.pexels.com/videos/search?query={requests.utils.quote(query)}&orientation=portrait&per_page=10",
                        f"https://api.pexels.com/videos/search?query={requests.utils.quote(query)}&per_page=10"]:
                r = SESSION.get(url, headers=headers, timeout=10)
                if r.status_code != 200: continue
                for v in r.json().get("videos", []):
                    vid_id = f"pex_v_{v.get('id')}"
                    if vid_id in used_ids: continue
                    for f in v.get("video_files", []):
                        if (f.get("height", 0) > f.get("width", 0) or f.get("width", 0) >= 720) and f.get("link"):
                            if _download_stream(f["link"], out_path, min_bytes=40000):
                                used_ids.add(vid_id)
                                return True
        else:
            r = SESSION.get("https://api.pexels.com/v1/search", headers=headers, params={"query": query, "per_page": 8, "orientation": "portrait"}, timeout=10)
            if r.status_code != 200:
                r = SESSION.get("https://api.pexels.com/v1/search", headers=headers, params={"query": query, "per_page": 8}, timeout=10)
            if r.status_code == 200:
                for p in r.json().get("photos", []):
                    p_id = f"pex_p_{p.get('id')}"
                    if p_id in used_ids: continue
                    src = p.get("src", {})
                    # Prefer true 4K uncompressed original camera resolution
                    link = src.get("original") or src.get("large2x") or src.get("large")
                    if link and _download_stream(link, out_path, min_bytes=10000):
                        used_ids.add(p_id)
                        return True
    except Exception:
        pass
    return False


def _fetch_pixabay(query: str, is_video: bool, out_path: Path, used_ids: set) -> bool:
    if not PIXABAY_KEY: return False
    try:
        if is_video:
            r = SESSION.get("https://pixabay.com/api/videos/", params={"key": PIXABAY_KEY, "q": query, "per_page": 8}, timeout=10)
            if r.status_code == 200:
                for h in r.json().get("hits", []):
                    vid_id = f"pix_v_{h.get('id')}"
                    if vid_id in used_ids: continue
                    streams = h.get("videos", {})
                    # Prefer crisp large/HD streams first
                    stream = streams.get("large") or streams.get("medium") or streams.get("small")
                    if stream and stream.get("url") and _download_stream(stream["url"], out_path, min_bytes=40000):
                        used_ids.add(vid_id)
                        return True
        else:
            r = SESSION.get("https://pixabay.com/api/", params={"key": PIXABAY_KEY, "q": query, "image_type": "photo", "per_page": 8}, timeout=10)
            if r.status_code == 200:
                for h in r.json().get("hits", []):
                    p_id = f"pix_p_{h.get('id')}"
                    if p_id in used_ids: continue
                    # Prefer fullHD / original photo resolution
                    link = h.get("fullHDURL") or h.get("imageURL") or h.get("largeImageURL") or h.get("webformatURL")
                    if link and _download_stream(link, out_path, min_bytes=10000):
                        used_ids.add(p_id)
                        return True
    except Exception:
        pass
    return False


def _fetch_mixkit(query: str, is_video: bool, out_path: Path, used_ids: set) -> bool:
    """Live crawler for Mixkit free cinematic HD stock footage (Priority #1)."""
    if not is_video:
        return False
    try:
        q_lower = query.lower()
        candidates = []

        # 1. Semantic category shortcuts (Mixkit high-yield slugs)
        category_map = [
            (r"ship|boat|titanic|vessel|submarine|cruise|sail|yacht", "ship"),
            (r"iceberg|glacier|ice|frozen|arctic", "ice"),
            (r"moon|lunar", "moon"),
            (r"earth|globe", "earth"),
            (r"stars|star|nebula|constellation", "stars"),
            (r"space|galaxy|universe|planet|black hole|astronomy|cosmic|mars", "space"),
            (r"sun|solar|sunrise|sunset", "sun"),
            (r"ocean|sea|wave|waves|underwater|beach|marine", "ocean"),
            (r"snow|permafrost|frost|blizzard|winter|cold", "snow"),
            (r"storm|lightning|rain|wind|thunder|tornado|cyclone", "storm"),
            (r"dark|night|shadow|mystery|creepy|fog|mist|black", "night"),
            (r"cave|underground|tunnel|crater|hole", "cave"),
            (r"forest|tree|jungle|wood|rainforest|leaves", "forest"),
            (r"aerial|drone|clouds|sky|airplane|flying", "aerial"),
            (r"city|building|street|traffic|urban|crowd", "city"),
            (r"fire|flame|explosion|lava|volcano|burning", "fire"),
            (r"water|river|lake|waterfall|splash", "water"),
            (r"tech|computer|data|server|screen|cyber", "technology"),
            (r"nature|landscape|mountain|desert", "nature"),
        ]
        for pattern, slug in category_map:
            if re.search(pattern, q_lower):
                candidates.append(slug)
                break

        # 2. Query words
        words = [w.lower().strip() for w in re.findall(r'[a-zA-Z]+', query) if len(w) > 2]
        stopwords = {"dark", "rough", "glowing", "deep", "outer", "fast", "massive", "blazing", "bright", "extreme", "violent", "the", "and"}
        keywords = [w for w in words if w not in stopwords] or words

        if len(keywords) >= 2:
            candidates.append(f"{keywords[0]}-{keywords[1]}")
        for kw in keywords[:3]:
            if kw not in candidates:
                candidates.append(kw)

        # Only search specific keyword slugs, do NOT fallback to generic nature
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        }

        for slug in candidates[:4]:
            url = f"https://mixkit.co/free-stock-video/{slug}/"
            r = SESSION.get(url, headers=headers, timeout=6)
            if r.status_code != 200:
                continue

            vid_matches = re.findall(r'assets\.mixkit\.co/videos/(\d+)/', r.text)
            if not vid_matches:
                continue

            for vid_id in dict.fromkeys(vid_matches):
                uid = f"mix_v_{vid_id}"
                if uid in used_ids:
                    continue

                for res in ["1080", "720", "360"]:
                    cdn_url = f"https://assets.mixkit.co/videos/{vid_id}/{vid_id}-{res}.mp4"
                    if _download_stream(cdn_url, out_path, min_bytes=30000, headers=headers):
                        used_ids.add(uid)
                        return True
    except Exception:
        pass
    return False


def fetch_mixed_media_clip(query: str, target_dur: float, out_video_path: Path, media_type: str = "video", used_ids: set = None, cut_index: int = 0) -> Tuple[bool, str]:
    """
    Fetches unique stock assets with strict hierarchy:
    1. PRIORITY #1: Mixkit Free Cinematic HD Video (Always tried first)
    2. FALLBACK #1: Pexels (1080p Video -> 4K RAW Photo with Ken-Burns)
    3. FALLBACK #2: Pixabay (HD Video -> 4K Photo)
    """
    if used_ids is None: used_ids = set()
    raw = out_video_path.parent / f"raw_{cut_index}_{int(random.random()*10000)}"
    direction = "down" if cut_index % 2 == 0 else "up"

    # =========================================================================
    # 1. PRIORITY #1: Mixkit Cinematic HD Stock Video
    # =========================================================================
    target_vid = raw.with_suffix(".mp4")
    if _fetch_mixkit(query, True, target_vid, used_ids):
        print(f"   🎬 [Mixkit Priority #1] Successfully downloaded cinematic HD clip for '{query}'")
        _render_video_segment(target_vid, out_video_path, target_dur, direction)
        try: target_vid.unlink()
        except Exception: pass
        return True, "video:mixkit"

    # =========================================================================
    # 2. FALLBACK: Pexels (Video -> 4K Photo)
    # =========================================================================
    if _fetch_pexels(query, True, target_vid, used_ids):
        print(f"   🎥 [Pexels Fallback] Downloaded HD video for '{query}'")
        _render_video_segment(target_vid, out_video_path, target_dur, direction)
        try: target_vid.unlink()
        except Exception: pass
        return True, "video:pexels"

    target_img = raw.with_suffix(".jpg")
    if _fetch_pexels(query, False, target_img, used_ids):
        print(f"   📸 [Pexels Fallback] Downloaded 4K photo for '{query}' (Ken-Burns dynamic pan)")
        convert_image_to_kenburns(target_img, out_video_path, target_dur, direction)
        try: target_img.unlink()
        except Exception: pass
        return True, "photo:pexels"

    # =========================================================================
    # 3. FALLBACK: Pixabay (Video -> Photo)
    # =========================================================================
    if _fetch_pixabay(query, True, target_vid, used_ids):
        print(f"   🎥 [Pixabay Fallback] Downloaded video for '{query}'")
        _render_video_segment(target_vid, out_video_path, target_dur, direction)
        try: target_vid.unlink()
        except Exception: pass
        return True, "video:pixabay"

    if _fetch_pixabay(query, False, target_img, used_ids):
        print(f"   📸 [Pixabay Fallback] Downloaded photo for '{query}'")
        convert_image_to_kenburns(target_img, out_video_path, target_dur, direction)
        try: target_img.unlink()
        except Exception: pass
        return True, "photo:pixabay"

    return False, "failed"


# ---------------------------------------------------------------------------
# 3. GRANULAR BEAT VISUAL DIRECTOR (WORD-SYNC TIMING)
# ---------------------------------------------------------------------------
HINDI_SEMANTIC_DICTIONARY = [
    (r"चाँद|चन्द्र|moon", "full glowing moon night sky"),
    (r"सूरज|सूर्य|sun", "blazing bright sun rays solar"),
    (r"सितारे|तारे|stars|galaxy", "deep space galaxy stars nebula"),
    (r"अंतरिक्ष|space|cosmos", "deep universe outer space travel"),
    (r"ब्लैक होल|black hole", "black hole cosmic gravitational lens"),
    (r"धरती|पृथ्वी|earth|globe", "planet earth rotating in space"),
    (r"धुरी|घूम|चक्कर|spin|rotate|रफ्तार", "fast spinning planet earth globe"),
    (r"गुरुत्वाकर्षण|gravity", "floating zero gravity space"),
    (r"उल्कापिंड|एस्टेरॉयड|meteor|asteroid", "asteroid meteor crashing burning"),
    (r"सुनामी|tsunami", "massive tsunami wave crashing ocean"),
    (r"समुद्र|समंदर|ocean|sea|लहरें", "dark stormy ocean rough waves"),
    (r"डूब|जलमग्न|flood|submerge", "flooded city buildings underwater"),
    (r"शहर|इमारत|city|building", "city skyscrapers aerial drone"),
    (r"तबाही|विनाश|destroy|ruin", "apocalyptic destruction disaster storm"),
    (r"बर्फीली|blizzard|snow", "extreme blizzard howling snow storm"),
    (r"हवा|आंधी|तूफान|wind|storm|hurricane", "violent storm wind trees blowing"),
    (r"माइनस|तापमान|बर्फ|frost|freeze|arctic", "frozen arctic ice glacier landscape"),
    (r"दिन|रात|घंटे|day|night|timelapse", "rapid sunrise sunset timelapse sky"),
    (r"आग|ज्वालामुखी|lava|fire|volcano", "volcano lava eruption explosion"),
    (r"बिजली|lightning", "dramatic lightning thunderstorm dark sky"),
    (r"इंसान|लोग|human|people", "person looking up shocked fear eyes"),
    (r"जिंदा|जीवन|survive|life|बच", "human eye looking close up drama"),
    (r"डर|खौफ|panic|terror|darr|darawani", "terrified scared person in shock"),
    (r"गायब|vanish|disappear", "dark empty cosmic void silence"),
    (r"आवाज़|awaaz|sound|noise|hum|frequency|hertz", "sound wave glowing audio frequency dark"),
    (r"कान|kaan|sun|hear|listen|ear", "human ear listening in silence eerie"),
    (r"डॉक्टर|doctor|science|research|study", "scientist laboratory microscope dark research"),
    (r"दिमाग|dimaag|brain|amygdala|scan", "glowing human brain scan medical x-ray"),
    (r"कमरा|room|ghar|house|akela|alone", "dark room alone silhouette eerie blue light"),
    (r"सड़क|road|sheher|city|desert|town", "empty desert road night street lights fog cinematic"),
    (r"सिरदर्द|neend|headache|sleep|dard|अनिद्रा|insomnia", "person holding head headache pain darkness"),
    (r"मारियाना|ट्रेंच|गहराई|गड्ढा|trench|abyss|deep ocean", "deep sea underwater ocean abyss"),
    (r"मछली|जीव|creature|fish|shark|दानव", "strange deep sea glowing creature underwater"),
    (r"ड्रिल|बोरहोल|borehole|tunnel|hole|छेद", "deep dark tunnel hole underground cavern"),
    (r"रेबीज|गला|ऐंठन|spasm|hydrophobia|rabies", "person terrified looking glass of water"),
    (r"इंटरनेट|वाई-फाई|कंप्यूटर|सर्वर|network|internet|wifi", "modern server room computer data blue lights"),
    (r"विमान|हवाई जहाज|flight|airplane|airport", "airplane flying sky runway airport"),
    (r"मधुमक्खी|पॉलीनेशन|bee|honeycomb", "honey bee on flower macro nature"),
    (r"चेरनोबिल|परमाणु|रेडिएशन|radiation|reactor|chernobyl", "abandoned chernobyl nuclear reactor plant eerie"),
    (r"हीरा|हीरे|रत्न|diamond|crystal|gem", "sparkling raw diamond crystal mineral dark"),
    (r"समय|घड़ी|सापेक्षता|relativity|clock|seconds", "ticking clock antique watch time passing timelapse")
]


FALLBACK_COSMIC_BEATS = [
    "full glowing moon night sky", "massive tsunami wave crashing ocean", "flooded city buildings storm",
    "planet earth rotating in space", "fast spinning earth globe", "rapid sunrise sunset timelapse",
    "extreme blizzard howling snow storm", "frozen arctic ice glacier landscape", "person looking up shocked fear",
    "deep space stars galaxy nebula", "dark stormy ocean rough waves", "violent storm wind hurricane",
    "black hole cosmic gravitational lens", "asteroid meteor cosmic space", "frost ice crystals freezing"
]


def build_timed_words(sentences: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    timed_words = []
    for s in sentences:
        words = [w for w in re.split(r"\s+", s.get("text", "")) if w.strip()]
        if not words: continue
        total_chars = sum(len(w) for w in words)
        dur = s.get("duration", 0.0)
        curr_t = s.get("start", 0.0)
        for w in words:
            w_dur = max(0.18, (len(w) / max(total_chars, 1)) * dur)
            timed_words.append({"word": w, "start": curr_t, "end": curr_t + w_dur})
            curr_t += w_dur
    return timed_words


def plan_beat_visuals(total_dur: float, timed_data: List[Dict[str, Any]], script: str, target_cut_dur: float = 1.9) -> List[Dict[str, Any]]:
    """Calculates rapid cuts (1.5 - 2.2s for shorts, 2.5 - 3.2s for 2-3 min docs) synchronized with spoken words."""
    if total_dur > 75 and target_cut_dur < 2.5:
        target_cut_dur = 2.8
    num_cuts = max(int(round(total_dur / target_cut_dur)), 6)
    actual_cut_dur = total_dur / num_cuts

    if timed_data and "word" in timed_data[0]:
        timed_words = timed_data
    else:
        timed_words = build_timed_words(timed_data)

    beats = []
    for i in range(num_cuts):
        st = i * actual_cut_dur
        et = (i + 1) * actual_cut_dur if i < num_cuts - 1 else total_dur
        dur = et - st
        active_words = [w["word"] for w in timed_words if max(st, w["start"]) < min(et, w["end"])]
        spoken = " ".join(active_words)
        media_type = "video" if i % 2 == 0 else "photo"
        fallback = FALLBACK_COSMIC_BEATS[i % len(FALLBACK_COSMIC_BEATS)]

        # Map query
        query = fallback
        if spoken:
            spoken_lower = spoken.lower()
            for pattern, q in HINDI_SEMANTIC_DICTIONARY:
                if re.search(pattern, spoken_lower):
                    query = q
                    break

        beats.append({
            "cut_index": i, "start": round(st, 2), "end": round(et, 2),
            "duration": round(dur, 2), "spoken_hindi": spoken, "query": query, "media_type": media_type
        })

    # Optional LLM refinement for Hollywood-grade visual variety
    try:
        from llm_engine import llm_complete
        summary = "\n".join([f"Cut {b['cut_index']} [{b['start']}s-{b['end']}s]: '{b['spoken_hindi']}'" for b in beats])
        prompt = (
            f"Video Context / Full Script: \"{script[:250]}\"\n\n"
            f"Act as elite visual director for a viral 9:16 vertical short. Here are {num_cuts} cuts with spoken text:\n{summary}\n\n"
            "DIRECTIVES FOR DYNAMIC CINEMATIC VISUALS:\n"
            "- For each cut, output an exact 2-4 word English visual search query for high-res stock footage.\n"
            "- DYNAMIC DIVERSITY (DO NOT REPEAT HUMAN FACES!):\n"
            "  * MAXIMUM 2 cuts can show a human face/person. NEVER show people cut after cut.\n"
            "  * The rest of the cuts MUST be dynamic non-human cinematic footage:\n"
            "    1. 3D Microscopic Science: (e.g. 'virus 3d animation', 'neurons firing glow', 'blood cells microscope', 'dna strand rotating')\n"
            "    2. Cinematic Macro B-Roll: (e.g. 'water drop slow motion', 'dark liquid ripple', 'glass breaking macro', 'steaming beaker lab')\n"
            "    3. Medical Telemetry: (e.g. 'brain mri scan', 'holographic skeleton mesh', 'heartbeat monitor wave', 'xray skull diagnostic')\n"
            "    4. Moody Atmospheric Cinematic: (e.g. 'dark hospital corridor', 'shadow silhouette fog', 'abstract science particles')\n"
            "- STRICT PROHIBITION: NEVER use UI terms like 'subscribe button', 'like share', 'waving hand', 'goodbye', 'channel preview'.\n"
            f"Return ONLY a JSON list of exactly {num_cuts} strings."
        )
        res = llm_complete(prompt, temp=0.25, max_tokens=450)
        match = re.search(r"\[.*\]", res, re.DOTALL)
        if match:
            queries = json.loads(match.group(0))
            if isinstance(queries, list) and len(queries) >= len(beats):
                for idx, q in enumerate(queries[:len(beats)]):
                    cl = str(q).strip().lower()
                    if len(cl) >= 3 and not any(ban in cl for ban in ["subscribe", "waving", "goodbye", "button", "youtube"]):
                        beats[idx]["query"] = cl
    except Exception:
        pass

    # Ensure no consecutive identical queries
    last_q = ""
    for idx, b in enumerate(beats):
        if b["query"] == last_q:
            b["query"] = f"{b['query']} cinematic {idx % 3}"
        last_q = b["query"]

    return beats
