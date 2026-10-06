"""
Dhruv Rathee & Mohak Mangal Style High-Retention Documentary Engine.
Features:
1. 5-Stage Script Architecture:
   - HOOK (0-30s): Shocking paradox / question without generic "hello dosto" intros.
   - CONTEXT: Simplified historical foundation from Wikipedia & research.
   - DEEP DIVE: 3-4 analytical chapters (Why & How).
   - DATA & PROOF: Empirical numbers, dates, geographical maps.
   - CONCLUSION: Neutral, balanced summary + 1 thought-provoking comment hook.
2. Embedded [VISUAL CUE] Extraction:
   - Automatically parses `[VISUAL CUE: ...]` tokens and generates matching motion graphic prompts.
3. Multi-Channel Signature Color Palettes:
   - Channel 1 (Facts): Cyan/Gold Neon (#00F0FF, #FFD700)
   - Channel 3 (Dark Sutra): Blood Crimson/Ash (#E63946, #F1FAEE)
   - Channel 5 (The Global Ledger): Emerald/Amber Geopolitical (#06D6A0, #F77F00)
"""
from __future__ import annotations

import json
import os
import re
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


CHANNEL_COLOR_PALETTES = {
    "channel_1_facts": {
        "primary": "#00F0FF",      # Electric Cyan
        "accent": "#FFD700",       # Cyber Gold
        "background": "#050B14",   # Deep Space Black
        "theme_name": "Cyber Science & Cosmos"
    },
    "channel_3_dark_sutra": {
        "primary": "#E63946",      # Blood Crimson
        "accent": "#D62828",       # Deep Amber/Red
        "background": "#0A0A0C",   # Forensic Charcoal
        "theme_name": "True Crime & Redacted Archive"
    },
    "channel_5_global_ledger": {
        "primary": "#06D6A0",      # Geopolitical Emerald
        "accent": "#F77F00",       # Naval Amber
        "background": "#080C14",   # Diplomatic Navy
        "theme_name": "Johnny Harris Global Affairs & Maps"
    },
    "channel_4_lofi": {
        "primary": "#B5179E",      # Sunset Magenta
        "accent": "#7209B7",       # Dream Indigo
        "background": "#0D0B18",   # Midnight Velvet
        "theme_name": "Ambient Anime Lo-Fi"
    }
}


def _get_api_key(name: str) -> str:
    val = os.getenv(name, "")
    if val:
        return val
    env_file = Path("d:/facts_yt/.env")
    if env_file.is_file():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith(f"{name}="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return ""


def generate_dhruv_rathee_script(
    topic: str,
    channel_key: str = "channel_5_global_ledger",
    wiki_context: str = "",
    target_duration: str = "5-8 minutes (700-1000 words)"
) -> dict[str, Any]:
    """
    Generates a high-retention Dhruv Rathee / Mohak Mangal style documentary script
    with explicit [VISUAL CUE: ...] tags and chapter breakdowns.
    """
    palette = CHANNEL_COLOR_PALETTES.get(channel_key, CHANNEL_COLOR_PALETTES["channel_5_global_ledger"])
    gemini_key = _get_api_key("GEMINI_API_KEY")
    groq_key = _get_api_key("GROQ_API_KEY")

    prompt = f"""
You are the lead investigative documentary scriptwriter and director, working in the exact storytelling style of DHRUV RATHEE and MOHAK MANGAL.

TOPIC: "{topic}"
TARGET LENGTH: {target_duration}
LANGUAGE: Conversational Hindi / Hinglish (natural, lucid, intellectually engaging, zero robotic jargon).
CHANNEL SIGNATURE THEME: {palette['theme_name']} (Primary: {palette['primary']}, Accent: {palette['accent']})
RESEARCH CONTEXT:
\"\"\"{wiki_context[:2000]}\"\"\"

MANDATORY 5-STAGE SCRIPT STRUCTURE:
1. HOOK (0-30s): Start directly with a shocking paradox, counter-intuitive statistic, or unsolved dilemma. NO "Hello dosto" or generic introductions.
2. CONTEXT: Explain the foundational history/origin in simple everyday terms so even a 15-year-old understands the stakes.
3. DEEP DIVE (3-4 Chapters): Break the story into logical chapters. Explain WHY this happened and HOW the dominoes fell.
4. DATA & PROOF: Cite specific years, official treaty names, financial billions, satellite coordinates, and legal statutes.
5. CONCLUSION: Provide a neutral, objective synthesis + 1 provocative, thought-provoking question for the audience.

CRITICAL RULES:
- Keep sentences concise, punchy, and voiceover-friendly.
- Insert explicit [VISUAL CUE: ...] markers every 30-45 seconds indicating what graphic, dotted map, archival newspaper, or satellite fly-through must appear on screen.
- Example: [VISUAL CUE: Animated 2.5D dotted world map zooming into Strait of Hormuz with glowing red shipping choke-point line]

OUTPUT FORMAT: Output ONLY valid JSON with this exact schema:
{{
  "title": "Engaging High-CTR YouTube Title",
  "topic": "{topic}",
  "channel_theme": "{channel_key}",
  "estimated_duration": "6 minutes",
  "chapters": [
    {{"title": "Hook & The Shocking Paradox", "time_range": "00:00 - 00:45"}},
    {{"title": "The Hidden History", "time_range": "00:45 - 02:15"}},
    {{"title": "The Strategic Domino Effect", "time_range": "02:15 - 04:30"}},
    {{"title": "The Unresolved Conclusion", "time_range": "04:30 - 05:45"}}
  ],
  "script_text": "The full spoken voiceover script containing embedded [VISUAL CUE: ...] tags throughout.",
  "conclusion_question": "The final thought-provoking open question for the comments."
}}
"""

    import requests

    # 1. Try Groq REST API (Fastest and reliable)
    if groq_key:
        try:
            g_url = "https://api.groq.com/openai/v1/chat/completions"
            payload = {
                "model": "qwen/qwen3.8-27b",
                "messages": [
                    {"role": "system", "content": "You are a senior documentary scriptwriter in the style of Dhruv Rathee. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                "response_format": {"type": "json_object"},
                "temperature": 0.35
            }
            res = requests.post(g_url, json=payload, headers={"Authorization": f"Bearer {groq_key}"}, timeout=25)
            if res.status_code == 200:
                data = res.json()
                raw_content = data["choices"][0]["message"]["content"]
                parsed = json.loads(raw_content)
                print(f">> [Dhruv Rathee Engine] Generated {len(parsed.get('script_text', '').split())} words script via Groq!")
                return parsed
        except Exception as e:
            print(f"[Dhruv Rathee Engine] Groq error: {e}")

    # 2. Try Gemini REST API
    if gemini_key:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={gemini_key}"
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.35, "responseMimeType": "application/json"}
            }
            res = requests.post(url, json=payload, timeout=25)
            if res.status_code == 200:
                data = res.json()
                text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                parsed = json.loads(text)
                print(f">> [Dhruv Rathee Engine] Generated {len(parsed.get('script_text', '').split())} words script via Gemini!")
                return parsed
        except Exception as e:
            print(f"[Dhruv Rathee Engine] Gemini error: {e}")

    # 3. Authentic Fallback
    return {
        "title": f"The Untold Truth of {topic} | Explained",
        "topic": topic,
        "channel_theme": channel_key,
        "estimated_duration": "5 minutes",
        "chapters": [
            {"title": "The Shocking Incident", "time_range": "00:00 - 01:00"},
            {"title": "Historical Background", "time_range": "01:00 - 02:30"},
            {"title": "The Real Reason Behind It", "time_range": "02:30 - 04:30"},
            {"title": "What Does This Mean For The Future?", "time_range": "04:30 - 05:30"}
        ],
        "script_text": (
            f"[VISUAL CUE: Dramatic satellite zoom-in to {topic} with glowing red alert coordinates] "
            f"Kya aapko pata hai ki {topic} ke baare me jo baatein official reports me kahi gayi hain, "
            "asliyat usse bilkul alag hai? "
            "[VISUAL CUE: Declassified archive dossier stamp slam reading TOP SECRET] "
            "Saal ke sabse bade declassified investigation ne ye saaf kar diya hai ki is ghatna ke peechhe "
            "ek aisa pattern tha jise saalon tak public se chhipaya gaya. "
            "[VISUAL CUE: 2.5D Animated dotted map showing tactical trade choke-points] "
            "Is video me hum decode karenge is poore case ke 3 sabse bade facts jo modern history ko badal kar rakh dete hain."
        ),
        "conclusion_question": f"Aapke mutabiq, kya {topic} ek accidental ghatna thi ya ek calculated strategy?"
    }


def extract_visual_cues(script_text: str) -> list[dict[str, Any]]:
    """
    Parses all [VISUAL CUE: ...] tags from the script and constructs
    corresponding motion graphic prompts and keywords.
    """
    pattern = r"\[VISUAL CUE:\s*(.*?)\]"
    matches = re.findall(pattern, script_text, flags=re.IGNORECASE)
    cues = []
    for idx, cue_text in enumerate(matches):
        cue_clean = cue_text.strip()
        motion_prompt = (
            f"Create a premium documentary-style motion infographic, 16:9, clean vector style. "
            f"Topic: {cue_clean}. "
            f"Style: Dark theme, smooth zoom-in animation, dotted world map, glowing data points, "
            f"minimal text, cinematic color grading like Netflix documentary. "
            f"Avoid: cartoonish, cluttered, low-res."
        )
        cues.append({
            "cue_index": idx + 1,
            "raw_cue": cue_clean,
            "motion_prompt": motion_prompt,
            "search_keywords": cue_clean[:40].replace("Animated", "").replace("map of", "").strip()
        })
    return cues
