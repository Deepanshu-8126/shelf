"""
Gemini Neural RAG & Deep Story Script Engine for Vox Studio (50-60s Format).
Generates full-length, high-retention documentary shorts (~130-150 words) with deep investigative storytelling:
1. Beat 1 (0-8s): The Shock Hook & Precise Time/Place
2. Beat 2 (8-20s): The Declassified Records & Initial Incident
3. Beat 3 (20-35s): The Forensic Evidence & What Experts Found
4. Beat 4 (35-48s): The Impossible Escalation / Dark Twist
5. Beat 5 (48-58s): The Chilling Conclusion & Mind-Bending Question
"""
from __future__ import annotations

import json
import re
import os
from typing import Any
import requests
from channel_5_vox_studio.config import GEMINI_API_KEY

API_KEY = GEMINI_API_KEY if GEMINI_API_KEY else "AQ.Ab8RN6LBizkxzkhNouoGq2mhkkGqVLD_LBpME4A5ope3wB-pPQ"

NICHE_PROMPTS = {
    "dark_mystery": """
You are a senior investigative documentary director for Vox and Lemmino.
YOUR FORMULA FOR A MASTER 50-60 SECOND DOCUMENTARY SHORT:
- Total word count: 120-145 words (Strictly ~50-55 seconds spoken pace).
- Tone: Deep, serious, investigative, cinematic, human. Never robotic.
- Beat 1 (0-8s): Shock Hook. Immediate year, coordinates, or chilling physical evidence. No generic intros like "Have you ever wondered...".
- Beat 2 (8-20s): The Incident & First Responder Logs. Concrete details, official names, audio transcript quotes.
- Beat 3 (20-35s): The Forensic Evidence. What investigators found when they examined the wreckage, radar, or files.
- Beat 4 (35-48s): The Dark Contradiction. The impossible detail that defied physics or human explanation.
- Beat 5 (48-58s): The Lingering Question. A chilling open loop that compels the viewer to think and comment.
""",
    "space_science": """
You are a lead astrophysicist & science documentary director for Kurzgesagt and Veritasium.
YOUR FORMULA FOR A MASTER 50-60 SECOND DOCUMENTARY SHORT:
- Total word count: 120-145 words (Strictly ~50-55 seconds spoken pace).
- Tone: Awe-inspiring, mind-bending, existential, scientifically accurate.
- Beat 1 (0-8s): Mind-Bending Paradox. Challenge basic assumptions about time, gravity, or the universe.
- Beat 2 (8-20s): The Discovery. How telescopes or space probes uncovered this anomaly.
- Beat 3 (20-35s): The Physics Mechanism. Explain the phenomenon in visceral, concrete visual terms.
- Beat 4 (35-48s): The Cosmic Threat or Implication. What this means for Earth and human reality.
- Beat 5 (48-58s): The Existential Question. A powerful closing thought that lingers in the mind.
""",
    "global_ledger": """
You are the senior investigative geopolitical director for the YouTube channel 'THE GLOBAL LEDGER'.
Your style matches Johnny Harris, Vox, and CaspianReport:
- Focus: Strategic choke-points, maritime trade routes (Strait of Malacca, Bab-el-Mandeb, Taiwan Strait), rare earth minerals, and classified boundary treaties.
- Language: High-IQ conversational Hindi/Hinglish that sounds authoritative, urgent, and gripping when read aloud.
- Total word count: 120-145 words for Shorts (~50-55s spoken pace).
- Beat 1 (0-8s): Geopolitical Choke-Point / Shocking Map Statistic.
- Beat 2 (8-20s): The Strategic Trigger & Global Stakes.
- Beat 3 (20-35s): The Real Satellite & Trade Map Evidence.
- Beat 4 (35-48s): The Hidden Power Play & Resource Control.
- Beat 5 (48-58s): The Unresolved Global Shift.
"""
}



class GeminiRAGScriptWriter:
    """Generates deep, 50-60 second documentary scripts via Gemini RAG pipeline."""

    @classmethod
    def generate_script_package(cls, topic: str, niche: str = "dark_mystery", research_context: str = "") -> dict[str, Any]:
        print(f"\n[GeminiRAGScriptWriter] Generating deep 55s cinematic script for '{topic}' (Niche: {niche})...")
        
        system_rules = NICHE_PROMPTS.get(niche, NICHE_PROMPTS["dark_mystery"])
        
        prompt = f"""
{system_rules}

TOPIC TO PRODUCE: "{topic}"
ADDITIONAL RESEARCH CONTEXT: "{research_context}"

Generate a complete, production-ready 50-60 second documentary script package formatted as a valid JSON object:
{{
  "topic": "{topic}",
  "headline": "Short punchy 4-word title",
  "sector": "SECTOR // RELEVANT COORDINATES OR ARCHIVE",
  "stamp": "DECLASSIFIED // OFFICIAL ARCHIVE",
  "badge1": "KEY FACT 1 (UPPERCASE)",
  "badge2": "KEY FACT 2 (UPPERCASE)",
  "climax_q1": "PROVOCATIVE QUESTION LINE 1",
  "climax_q2": "PROVOCATIVE QUESTION LINE 2",
  "narration_script": "The full spoken voiceover script (125-140 words). Written for 50-55 seconds of natural human speech with dramatic pauses (...) and natural cadence. Highly compelling, storytelling-driven, zero cliches.",
  "subtitles": [
    "Sentence 1 (0-10s)",
    "Sentence 2 (10-22s)",
    "Sentence 3 (22-35s)",
    "Sentence 4 (35-47s)",
    "Sentence 5 (47-56s)"
  ],
  "subtitles_json": "[{{\\"time\\": 0.5, \\"text\\": \\"Sentence 1 text\\"}}, {{\\"time\\": 11.0, \\"text\\": \\"Sentence 2 text\\"}}, {{\\"time\\": 23.0, \\"text\\": \\"Sentence 3 text\\"}}, {{\\"time\\": 36.0, \\"text\\": \\"Sentence 4 text\\"}}, {{\\"time\\": 48.0, \\"text\\": \\"Sentence 5 text\\"}}]",
  "thumbnail_title": "BOLD HIGH-CTR PHRASE\\nSECOND LINE",
  "thumbnail_tag": "CLASSIFIED // DOSSIER"
}}

OUTPUT ONLY RAW JSON. NO MARKDOWN TICKS, NO EXTRA TEXT.
"""

        # 1. Try Gemini REST API
        gemini_api_key = os.getenv("GEMINI_API_KEY", API_KEY)
        if gemini_api_key:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_api_key}"
                payload = {
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"temperature": 0.3, "responseMimeType": "application/json"}
                }
                res = requests.post(url, json=payload, timeout=20)
                if res.status_code == 200:
                    data = res.json()
                    raw_text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                    raw_text = re.sub(r"^```json\s*", "", raw_text)
                    raw_text = re.sub(r"^```\s*", "", raw_text)
                    raw_text = re.sub(r"\s*```$", "", raw_text).strip()
                    parsed = json.loads(raw_text)
                    print(f">> [The Global Ledger AI] Generated {len(parsed.get('narration_script', '').split())} words script via Gemini!")
                    return parsed
            except Exception as e:
                print(f"[The Global Ledger AI] Gemini REST error: {e}")

        # 2. Try Groq REST API
        groq_key = os.getenv("GROQ_API_KEY", "")
        if not groq_key:
            env_file = Path("d:/facts_yt/.env") if "Path" in globals() else None
            if not groq_key and os.path.exists("d:/facts_yt/.env"):
                for line in open("d:/facts_yt/.env", encoding="utf-8").read().splitlines():
                    if line.startswith("GROQ_API_KEY="):
                        groq_key = line.split("=", 1)[1].strip().strip('"').strip("'")
        if groq_key:
            try:
                g_url = "https://api.groq.com/openai/v1/chat/completions"
                payload = {
                    "model": "qwen/qwen3.8-27b",
                    "messages": [
                        {"role": "system", "content": "You are a professional documentary scriptwriter. Respond only with JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    "response_format": {"type": "json_object"},
                    "temperature": 0.3
                }
                res = requests.post(g_url, json=payload, headers={"Authorization": f"Bearer {groq_key}"}, timeout=20)
                if res.status_code == 200:
                    data = res.json()
                    parsed = json.loads(data["choices"][0]["message"]["content"])
                    print(f">> [The Global Ledger AI] Generated {len(parsed.get('narration_script', '').split())} words script via Groq!")
                    return parsed
            except Exception as e:
                print(f"[The Global Ledger AI] Groq REST error: {e}")

        # Fallback rich 50s script template if API is offline
        return {
            "topic": topic,
            "headline": f"The Secret of {topic}",
            "sector": "ARCHIVE // SPECIAL ACCESS REQUIRED",
            "stamp": "DECLASSIFIED // TOP SECRET",
            "badge1": "UNEXPLAINED ANOMALY",
            "badge2": "OFFICIAL INVESTIGATION SEALED",
            "climax_q1": f"WHAT REALLY HAPPENED TO {topic.upper()}?",
            "climax_q2": "AND WHY WERE THE FINDINGS CLASSIFIED?",
            "narration_script": (
                f"For decades, official government archives sealed the complete records on {topic}. "
                "According to declassified investigation logs, the first anomalies were detected at 0200 hours. "
                "Radar operators tracked an impossible trajectory moving at speeds conventional aircraft could never sustain. "
                "When recovery teams finally arrived at the coordinates, standard physical laws seemed to break down entirely. "
                "No distress signal had ever been transmitted... and the official report was classified under national security orders. "
                f"To this day, the central question remains: was {topic} a tragic coincidence... or evidence of something we were never meant to discover?"
            ),
            "subtitles": [
                f"For decades, official archives sealed the complete records on {topic}.",
                "According to declassified logs, the first anomalies were detected at 0200 hours.",
                "Radar operators tracked an impossible trajectory moving at unbelievable speeds.",
                "When recovery teams arrived at the coordinates, standard physical laws broke down.",
                f"To this day, was {topic} a tragic anomaly... or something deliberately hidden?"
            ],
            "subtitles_json": json.dumps([
                {"time": 0.5, "text": f"For decades, official archives sealed the records on {topic}."},
                {"time": 10.5, "text": "According to logs, the first anomaly was detected at 0200 hours."},
                {"time": 21.0, "text": "Radar operators tracked an impossible trajectory at hypersonic speed."},
                {"time": 33.0, "text": "When recovery teams arrived, physical laws broke down entirely."},
                {"time": 46.0, "text": f"Was {topic} an anomaly... or something deliberately hidden?"}
            ]),
            "thumbnail_title": f"THE {topic.upper()}\\nSECRET FILES",
            "thumbnail_tag": "CLASSIFIED // DOSSIER"
        }
