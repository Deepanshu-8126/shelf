"""
Viral Transcripts RAG Engine.
Uses real 10M+ view Hindi YouTube Shorts transcripts as in-context reference
so LLMs clone authentic human speaking rhythm, cadence, and vocabulary
instead of generating synthetic textbook AI slop.
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

FLEET_DIR = Path(__file__).resolve().parent
if str(FLEET_DIR) not in sys.path:
    sys.path.insert(0, str(FLEET_DIR))

from llm_engine import llm_json, sanitize_script

log = logging.getLogger("viral_rag_engine")

_RAG_BANK_FILE = FLEET_DIR / "viral_rag_bank.json"


def load_rag_bank() -> Dict[str, List[Dict[str, Any]]]:
    """Loads verified viral transcripts knowledge bank."""
    if not _RAG_BANK_FILE.exists():
        return {"cosmic_what_if": [], "vox_mystery_crime": []}
    try:
        return json.loads(_RAG_BANK_FILE.read_text(encoding="utf-8"))
    except Exception as e:
        log.warning(f"Failed to load RAG bank: {e}")
        return {"cosmic_what_if": [], "vox_mystery_crime": []}


def retrieve_best_transcript(topic: str, niche: str = "cosmic_what_if") -> Dict[str, Any]:
    """
    Finds the most relevant viral transcript from the knowledge bank
    using keyword & semantic overlap scoring.
    """
    bank = load_rag_bank()
    category = bank.get(niche, bank.get("cosmic_what_if", []))
    if not category:
        return {}

    topic_words = set(topic.lower().split())
    best_item = category[0]
    best_score = -1

    for item in category:
        item_words = set((item.get("topic", "") + " " + item.get("transcript", "")).lower().split())
        overlap = len(topic_words.intersection(item_words))
        if overlap > best_score:
            best_score = overlap
            best_item = item

    return best_item


def generate_rag_viral_script(
    topic: str,
    niche: str = "cosmic_what_if",
    lang: str = "hi",
    word_count_target: int = 72,
) -> Dict[str, Any]:
    """
    Generates a viral YouTube Shorts script by retrieving a real 15M+ view
    reference transcript and instructing the LLM to clone its exact human cadence.
    """
    ref = retrieve_best_transcript(topic, niche=niche)
    ref_transcript = ref.get("transcript", "")
    ref_hook = ref.get("hook", "")
    ref_notes = ref.get("style_notes", "")
    ref_views = ref.get("views", "15M")

    system_prompt = (
        "You are an elite Indian YouTube Shorts storyteller cloning the cadence of real viral videos.\n\n"
        "HERE IS A REAL VIRAL YOUTUBE SHORT TRANSCRIPT (VERIFIED " + ref_views + " VIEWS):\n"
        "\"\"\"\n"
        f"Topic: {ref.get('topic', '')}\n"
        f"Transcript: {ref_transcript}\n"
        f"Style: {ref_notes}\n"
        "\"\"\"\n\n"
        "HOW TO WRITE THE SCRIPT — CONTINUOUS FLOWING PARAGRAPH (like the reference above):\n"
        "- Write ONE unbroken paragraph. NO numbered sections, NO bullet points, NO headers.\n"
        "- Open with a punchy curiosity question ('अगर आज रात अचानक...').\n"
        "- Immediately give the first physical shock in simple tangible words.\n"
        "- Insert real cause-and-effect science with specific numbers (e.g. 3x faster, 6 hours, 400 km/h).\n"
        "- Escalate to climax naturally — speed, wind, freeze, or total chaos.\n"
        "- End with a chilling debate question that makes viewers comment.\n"
        "- The whole script must read like one breath — exactly like the verified reference above.\n\n"
        "STRICT NEGATIVE CONSTRAINTS:\n"
        "- NEVER use weird translated metaphors (NO 'सॉस की बोतल', NO 'पक्षी गड़बड़ाए').\n"
        "- ZERO ROBOTIC SANSKRIT/TEXTBOOK WORDS: Never say घूर्णन, अस्थिर, ध्वनि, चक्र, संचार, अस्तित्व, अदृश्य, मनुष्य, अराजकता.\n"
        "- USE ULTRA-SIMPLE 5th-grade spoken Hindi: घूमना, डगमगाना, आवाज़, हिसाब, तबाही, लोग, इंसान, सुनामी, अंधेरा.\n"
        f"- LENGTH: Exactly {word_count_target - 5} to {word_count_target + 5} words in Devanagari script.\n"
        "- Output strict JSON with keys: title, hook, script, cta"
    )

    user_prompt = (
        f"Target Topic: {topic}\n"
        f"Clone the real viral reference style for this topic. Write spoken natural Devanagari Hindi."
    )

    fallback = {
        "title": f"अगर {topic} सच हो जाए? #shorts",
        "hook": ref_hook or f"अगर {topic}, तो क्या होगा?",
        "script": ref_transcript,
        "cta": ref.get("cta", "आपकी क्या राय है? नीचे कमेंट में बताओ।"),
    }

    data = llm_json(
        prompt=user_prompt,
        system=system_prompt,
        temp=0.45,  # Lower temperature for tight adherence to reference style
        fallback=fallback,
    )

    data["script"] = sanitize_script(data.get("script", ""))
    data["hook"] = sanitize_script(data.get("hook", ""))
    data["cta"] = sanitize_script(data.get("cta", ""))
    data["reference_used"] = ref.get("id", "default")
    data["views_cloned"] = ref_views
    data["word_count"] = len(data["script"].split())

    return data


if __name__ == "__main__":
    test_topic = "अगर चांद अचानक गायब हो जाए, तो 24 घंटे में धरती पर क्या होगा?"
    res = generate_rag_viral_script(test_topic, niche="cosmic_what_if")
    print("=" * 65)
    print(f"🔥 RAG VIRAL SCRIPT (Cloned from {res.get('views_cloned')} Views Reference: {res.get('reference_used')})")
    print("=" * 65)
    print("TITLE :", res.get("title"))
    print("HOOK  :", res.get("hook"))
    print("SCRIPT:", res.get("script"))
    print("CTA   :", res.get("cta"))
    print("WORDS :", res.get("word_count"))
    print("=" * 65)
