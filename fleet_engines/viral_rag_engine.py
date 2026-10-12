"""
Viral Transcripts RAG Engine.
Uses real 10M+ view Hindi YouTube Shorts transcripts as in-context reference
so LLMs clone authentic human speaking rhythm, cadence, and vocabulary
instead of generating synthetic textbook AI slop.
"""
import os
import sys
import re
import json
import logging
from pathlib import Path
from typing import Dict, Any, List

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

FLEET_DIR = Path(__file__).resolve().parent
if str(FLEET_DIR) not in sys.path:
    sys.path.insert(0, str(FLEET_DIR))

from llm_engine import llm_json, llm_complete, sanitize_script


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

    topic_lower = topic.lower()
    topic_words = [w for w in re.findall(r"[\w]+", topic_lower) if len(w) >= 2]
    best_item = category[0]
    best_score = 0

    for item in category:
        t_title = (item.get("topic", "") + " " + item.get("id", "")).lower()
        t_body = item.get("transcript", "").lower()
        score = 0
        for w in topic_words:
            if w in t_title:
                score += 5
            elif w in t_body:
                score += 2
        if score > best_score:
            best_score = score
            best_item = item

    return best_item


def generate_rag_viral_script(
    topic: str,
    niche: str = "cosmic_what_if",
    lang: str = "hi",
    word_count_target: int = 72,
) -> Dict[str, Any]:
    """
    Generates a viral YouTube Shorts script using an Agentic 3-Step Storyteller pipeline:
      STEP 1: Causal Beat Outline (Hook -> First Shock -> Real Physics Numbers -> Climax Twist)
      STEP 2: Spoken Hindi Drafter (Flowing conversational paragraph without robotic jargon)
      STEP 3: Slop Reviewer & Polish (Enforces negative constraints, verifies word count & strict JSON)
    Clones authentic human cadence from real 15M+ view viral references.
    """
    ref = retrieve_best_transcript(topic, niche=niche)
    ref_transcript = ref.get("transcript", "")
    ref_hook = ref.get("hook", "")
    ref_notes = ref.get("style_notes", "")
    ref_views = ref.get("views", "15M")

    fallback = {
        "title": f"अगर {topic} सच हो जाए? #shorts",
        "hook": ref_hook or f"अगर {topic}, तो क्या होगा?",
        "script": ref_transcript or f"अगर आज रात अचानक {topic}, तो सबसे पहला झटका धरती को लगेगा! 400 किलोमीटर की तूफानी हवाएं चलेंगी और दिन-रात का चक्र बेकाबू हो जाएगा। क्या इंसान ऐसी दुनिया में ज़िंदा रह पाएगा? नीचे बताओ।",
        "cta": ref.get("cta", "आपकी क्या राय है? नीचे कमेंट में बताओ।"),
    }

    try:
        # -------------------------------------------------------------------
        # STEP 1: Causal Beat Outline (Causal Planning & Tension Architecture)
        # -------------------------------------------------------------------
        log.info(f"[StoryTeller-Step1] Planning 4-beat outline for '{topic}'...")
        step1_prompt = (
            f"Topic: {topic}\n"
            f"Niche: {niche}\n"
            "Create a high-retention 4-beat story outline for a 30-second viral YouTube Short:\n"
            "Beat 1 (Hook 0-3s): Impossible curiosity question / instant physical mystery.\n"
            "Beat 2 (First Physical Shock): What breaks first physically in tangible everyday words.\n"
            "Beat 3 (Escalating Chaos & Real Numbers): Cause-and-effect physics with concrete numbers (e.g., 3x faster, 6 hours, 400 km/h, -50°C).\n"
            "Beat 4 (Climax Twist & Debate Question): Terrifying consequence + spicy question that forces comments.\n"
            "Keep each beat 1 short punchy sentence."
        )
        outline = llm_complete(
            prompt=step1_prompt,
            system="You are a master viral suspense story architect.",
            temp=0.65,
        )

        # -------------------------------------------------------------------
        # STEP 2: Spoken Hindi Drafter (Conversational Suspense Narrative)
        # -------------------------------------------------------------------
        log.info(f"[StoryTeller-Step2] Drafting natural spoken Hindi script...")
        step2_prompt = (
            f"Story Outline:\n{outline}\n\n"
            f"VERIFIED VIRAL REFERENCE STYLE (from {ref_views} views video):\n"
            f"\"{ref_transcript}\"\n\n"
            "INSTRUCTIONS FOR PURE NATURAL CONVERSATIONAL HINDI:\n"
            "- Write ONE unbroken flowing spoken script in natural Devanagari Hindi.\n"
            "- Speak directly to the viewer like a gripping Indian documentary narrator / friend over chai.\n"
            "- Use natural everyday conversational loan words in Devanagari: 'ग्रैविटी' (NOT गुरुत्वाकर्षण), 'ऑर्बिट' (NOT कक्षा), 'सोलर सिस्टम' (NOT सौरमंडल), 'स्पीड' (NOT गति), 'एस्टेरॉयड' (NOT क्षुद्रग्रह), 'टेम्परेचर' (NOT तापमान).\n"
            "- Use natural conversational connectors:\n"
            "   * 'आप शायद सोच रहे होंगे कि...'\n"
            "   * 'लेकिन असली झटका तो तब लगेगा...'\n"
            "   * 'और सबसे डरावनी बात पता है क्या है?...'\n"
            "- NO robotic Sanskrit/textbook words (NO घूर्णन, चक्र, अस्तित्व, मनुष्य, अराजकता, यदि, मानव जाति).\n"
            "- USE ultra-simple words: घूमना, अंधेरा, इंसान, लोग, तेज़ हवाएं, तबाही.\n"
            f"- TARGET LENGTH: Exactly {word_count_target - 5} to {word_count_target + 5} words in Devanagari.\n"
            "- Output ONLY the Hindi script paragraph, nothing else."
        )
        draft = llm_complete(
            prompt=step2_prompt,
            system="You are India's top YouTube Shorts narrator writing spoken Hindi like a real human creator.",
            temp=0.55,
            max_tokens=350,
            remove_nl=False,
        )

        # -------------------------------------------------------------------
        # STEP 3: Slop Reviewer, Negative Filter & Polish
        # -------------------------------------------------------------------
        log.info(f"[StoryTeller-Step3] Reviewing, purging AI slop & polishing JSON...")
        step3_prompt = (
            f"Draft Script to Review:\n\"{draft}\"\n\n"
            "CRITIQUE & NATURAL POLISH CHECKLIST:\n"
            "1. Replace any robotic/textbook words: (गुरुत्वाकर्षण -> ग्रैविटी, कक्षा -> ऑर्बिट, सौरमंडल -> सोलर सिस्टम, गति -> स्पीड, मनुष्य -> इंसान, यदि -> अगर, तापमान -> टेम्परेचर).\n"
            "2. Make sure sentences are punchy, breathless, and conversational (30-second spoken short).\n"
            "3. Ending MUST be a natural spoken debate challenge: 'क्या लगता है, इंसान कभी ऐसी तबाही से बच पाएगा? अपनी राय नीचे बताओ।' (NEVER use 'क्या आप सोचते हैं').\n"
            f"4. Ensure script length is between {word_count_target - 8} and {word_count_target + 8} Devanagari words.\n"
            "5. Output STRICT JSON with keys: title, hook, script, cta.\n"
            "Format:\n"
            '{"title": "Viral 5-word title #shorts", "hook": "First sentence hook", "script": "Full continuous polished script", "cta": "Provocative debate question"}'
        )
        data = llm_json(
            prompt=step3_prompt,
            system="You are an elite script editor enforcing 100% natural conversational Indian Hindi. Return ONLY valid JSON with zero conversational filler.",
            temp=0.35,
            fallback=fallback,
        )
    except Exception as e:
        log.error(f"[StoryTeller] Error in 3-step pipeline: {e}. Using fallback.")
        data = fallback

    data["script"] = sanitize_script(data.get("script", ""))
    data["hook"] = sanitize_script(data.get("hook", ""))
    data["cta"] = sanitize_script(data.get("cta", ""))
    data["reference_used"] = ref.get("id", "default")
    data["views_cloned"] = ref_views
    data["word_count"] = len(data["script"].split())
    data["pipeline"] = "3-step-agentic-storyteller"

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
