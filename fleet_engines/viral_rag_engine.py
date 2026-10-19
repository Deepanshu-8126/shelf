"""
Viral Transcripts RAG Engine.
Dynamically calibrates topic category, tone, and pacing using real 10M+ view
authentic Hindi YouTube Shorts transcripts as in-context references.
Eliminates cartoonish AI apocalypse slop in favor of genuine human curiosity.
"""
import os
import sys
import re
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

FLEET_DIR = Path(__file__).resolve().parent
if str(FLEET_DIR) not in sys.path:
    sys.path.insert(0, str(FLEET_DIR))

from llm_engine import llm_json, llm_complete, sanitize_script

log = logging.getLogger("viral_rag_engine")

_RAG_BANK_FILE = FLEET_DIR / "viral_rag_bank.json"

CATEGORY_TONE_PROFILES = {
    "deep_earth_ocean": {
        "label": "Deep Earth & Ocean Anomalies",
        "tone": "Eerie exploration & claustrophobic depth mystery. Focus on real underwater pressures, strange blind creatures, and unexplained subterranean heat.",
        "hook_starter": "क्या आपको पता है कि समंदर के 11 किलोमीटर नीचे...",
        "keywords": ["trench", "ocean", "sea", "samandar", "mariana", "borehole", "abyss", "underwater", "गड्ढा", "गहराई", "खाई", "पानी", "ट्रेंच"]
    },
    "bizarre_human_science": {
        "label": "Bizarre Human Body & Mind Science",
        "tone": "Intimate biological and psychological curiosity. Relatable sensations (like lack of sleep or muscle spasms), fascinating medical science, zero preaching.",
        "hook_starter": "कभी सोचा है कि अगर आप लगातार 7 दिन तक न सोएं...",
        "keywords": ["sleep", "neend", "brain", "dimaag", "body", "sharir", "rabies", "virus", "cells", "insomnia", "नींद", "दिमाग", "शरीर", "रेबीज", "इंसान"]
    },
    "everyday_what_ifs": {
        "label": "Real Everyday What-Ifs",
        "tone": "Fast-paced realistic domino effect on everyday life (phones, Wi-Fi, food supply, flights). Real measurable economic and physical impacts.",
        "hook_starter": "कभी सोचा है कि अगर सिर्फ 24 घंटे के लिए दुनिया का इंटरनेट बंद हो जाए...",
        "keywords": ["internet", "wifi", "bees", "insects", "oxygen", "phone", "electricity", "food", "इंटरनेट", "मधुमक्खी", "ऑक्सीजन", "बिजली", "हवाई"]
    },
    "dark_science_anomalies": {
        "label": "Mysterious Historic & Dark Science Anomalies",
        "tone": "Investigative historical curiosity and forbidden physics (Chernobyl radiation, mysterious sonic frequencies). Grounded in real documented events.",
        "hook_starter": "क्या आप जानते हैं कि दुनिया में एक ऐसा पत्थर है...",
        "keywords": ["chernobyl", "radiation", "elephant", "foot", "hum", "frequency", "sound", "stone", "चेरनोबिल", "रेडिएशन", "आवाज", "पत्थर", "हर्ट्ज"]
    },
    "mind_bending_space": {
        "label": "Mind-Bending Deep Space Curiosities",
        "tone": "Awe-inspiring astrophysics without cartoonish doom. Real celestial wonders like diamond planets, gravitational time dilation, and cosmic speed.",
        "hook_starter": "क्या आपको पता है कि हमारे ब्रह्मांड में एक ऐसा ग्रह है...",
        "keywords": ["space", "planet", "diamond", "time", "dilation", "black hole", "galaxy", "orbit", "gravity", "चाँद", "सूरज", "ग्रह", "अंतरिक्ष", "ब्लैक होल", "हीरा", "समय"]
    }
}


def load_rag_bank() -> Dict[str, List[Dict[str, Any]]]:
    """Loads verified viral transcripts knowledge bank."""
    if not _RAG_BANK_FILE.exists():
        return {}
    try:
        return json.loads(_RAG_BANK_FILE.read_text(encoding="utf-8"))
    except Exception as e:
        log.warning(f"Failed to load RAG bank: {e}")
        return {}


def detect_category(topic: str) -> str:
    """Detects the best matching category for a topic based on keyword scoring."""
    t_lower = topic.lower()
    best_cat = "mind_bending_space"
    max_score = 0
    for cat, data in CATEGORY_TONE_PROFILES.items():
        score = sum(1 for kw in data["keywords"] if kw in t_lower)
        if score > max_score:
            max_score = score
            best_cat = cat
    return best_cat


def retrieve_best_transcript(topic: str, forced_category: str = None) -> Tuple[Dict[str, Any], str, int]:
    """
    Finds the most relevant viral transcript from the knowledge bank
    across all 5 categories using semantic keyword overlap.
    """
    bank = load_rag_bank()
    if forced_category and forced_category in bank:
        cat_key = forced_category
    else:
        cat_key = detect_category(topic)
    items = bank.get(cat_key, [])

    if not items:
        # Fallback across all categories
        for k, c in bank.items():
            if c:
                items = c
                cat_key = k
                break

    if not items:
        return {}, cat_key, 0

    topic_lower = topic.lower()
    topic_words = [w for w in re.findall(r"[\w]+", topic_lower) if len(w) >= 2]
    best_item = items[0]
    best_score = -1

    for item in items:
        t_meta = (item.get("topic", "") + " " + item.get("id", "")).lower()
        t_body = item.get("transcript", "").lower()
        score = sum(5 for w in topic_words if w in t_meta) + sum(2 for w in topic_words if w in t_body)
        if score > best_score:
            best_score = score
            best_item = item

    return best_item, cat_key, max(0, best_score)


def generate_rag_viral_script(
    topic: str,
    niche: str = None,
    lang: str = "hi",
    word_count_target: int = 75,
) -> Dict[str, Any]:
    """
    Generates a viral YouTube Shorts script using an Agentic 3-Step Storyteller pipeline:
      STEP 1: Causal Beat Outline (Relatable Hook -> Tangible Setup -> Scientific Twist -> Friendly CTA)
      STEP 2: Spoken Hindi Drafter (Flowing conversational Indian creator cadence over chai)
      STEP 3: Slop Reviewer & Polish (Purges melodrama, verifies word count & strict JSON)
    """
    ref, detected_cat, match_score = retrieve_best_transcript(topic, forced_category=niche)
    ref_transcript = ref.get("transcript", "")
    ref_hook = ref.get("hook", "")
    ref_views = ref.get("views", "25M")

    cat_profile = CATEGORY_TONE_PROFILES.get(detected_cat, CATEGORY_TONE_PROFILES["mind_bending_space"])
    standard_cta = "ऐसी ही अजीब और रोमांचक साइंस जानकारी के लिए चैनल को सब्सक्राइब कर लो, मिलते हैं अगले वीडियो में!"

    clean_topic_name = topic.rstrip("?!. ")
    # STRICT GUARD: Only use ref_transcript if it actually shares semantic keywords with topic!
    if match_score > 0 and ref_transcript:
        fallback_script = ref_transcript
        fallback_hook = ref_hook or f"क्या आपको पता है कि {clean_topic_name}?"
    else:
        fallback_hook = f"क्या आपको पता है कि {clean_topic_name}?"
        fallback_script = f"क्या आपको पता है कि {clean_topic_name}? जब वैज्ञानिकों ने इस पर गहराई से रिसर्च की, तो उनके होश उड़ गए। रिसर्च में सामने आया कि इसके पीछे एक बेहद हैरान कर देने वाला वैज्ञानिक कारण छिपा हुआ है। {standard_cta}"

    fallback = {
        "title": f"{clean_topic_name[:32]} #shorts",
        "hook": fallback_hook,
        "script": fallback_script,
        "cta": standard_cta,
    }

    try:
        # -------------------------------------------------------------------
        # STEP 1: Causal Beat Outline (Dynamic Category & Tone Alignment)
        # -------------------------------------------------------------------
        log.info(f"[StoryTeller-Step1] Planning beats for category '{cat_profile['label']}' -> '{topic}'...")
        step1_prompt = (
            f"Topic: {topic}\n"
            f"Category: {cat_profile['label']}\n"
            f"Tone Directive: {cat_profile['tone']}\n\n"
            "Create a high-retention 4-beat story outline for a 30-second viral YouTube Short:\n"
            "Beat 1 (Hook 0-3s): Direct curious question ('क्या आपको पता है कि...' or 'कभी सोचा है कि अगर...').\n"
            "Beat 2 (The Tangible Setup 3-12s): Relatable real-world context (NO screaming, NO fake apocalypse).\n"
            "Beat 3 (The Jaw-Drop Twist 12-22s): The researched scientific or historical fact that 99% of people don't know.\n"
            f"Beat 4 (Friendly Closing 22-30s): Smooth wrap-up with CTA: '{standard_cta}'.\n"
            "Keep each beat 1 short punchy sentence."
        )
        outline = llm_complete(
            prompt=step1_prompt,
            system="You are an elite YouTube Shorts storyteller writing grounded, highly curious human stories.",
            temp=0.60,
        )

        # -------------------------------------------------------------------
        # STEP 2: Spoken Hindi Drafter (Conversational Indian Creator Narrative)
        # -------------------------------------------------------------------
        log.info(f"[StoryTeller-Step2] Drafting natural spoken Hindi script...")
        step2_prompt = (
            f"Story Outline:\n{outline}\n\n"
            f"VERIFIED VIRAL REFERENCE STYLE (from {ref_views} views video):\n"
            f"\"{ref_transcript}\"\n\n"
            f"CATEGORY & TONE: {cat_profile['tone']}\n\n"
            "INSTRUCTIONS FOR NATURAL SPOKEN HINDI CREATOR STORYTELLER:\n"
            "- Write ONE unbroken flowing spoken script in natural Devanagari Hindi.\n"
            "- Talk like a 22-year-old passionate Indian creator explaining something mind-blowing to a friend over chai.\n"
            "- Open directly with either 'क्या आपको पता है कि...' or 'कभी सोचा है कि अगर...' (NEVER say 'नमस्ते दोस्तों').\n"
            "- Use natural everyday conversational loan words in Devanagari: 'ग्रैविटी', 'स्पीड', 'टेम्परेचर', 'ब्रेन', 'इंसान', 'वायरस', 'इंटरनेट', 'डायमंड', 'रेडिएशन', 'सिस्टम', 'रिसर्च'.\n"
            "- ZERO MELODRAMA: NEVER scream about 'प्रलय', 'खून-खराबा', 'कयामत', 'नरक', 'सर्वनाश'. Speak with confident curiosity.\n"
            f"- MUST END with the exact friendly CTA: '{standard_cta}'\n"
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
            "2. Ensure conversational, breathless flow (30-second spoken short).\n"
            f"3. Ending MUST be the friendly subscribe CTA: '{standard_cta}'\n"
            f"4. Ensure script length is between {word_count_target - 8} and {word_count_target + 8} Devanagari words.\n"
            "5. Output STRICT JSON with keys: title, hook, script, cta.\n"
            "Format:\n"
            '{"title": "Viral 5-word title #shorts", "hook": "First sentence hook", "script": "Full continuous polished script", "cta": "Subscribe CTA"}'
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
    data["cta"] = sanitize_script(data.get("cta", standard_cta))
    data["category"] = detected_cat
    data["category_label"] = cat_profile["label"]
    data["reference_used"] = ref.get("id", "default")
    data["views_cloned"] = ref_views
    data["word_count"] = len(data["script"].split())
    data["pipeline"] = "5-pillar-dynamic-storyteller"

    return data


if __name__ == "__main__":
    test_topics = [
        "मारियाना ट्रेंच के 11 किलोमीटर नीचे क्या मिला?",
        "अगर इंसान 7 दिन तक न सोए तो दिमाग के साथ क्या होता है?",
        "अगर 24 घंटे के लिए दुनिया का इंटरनेट बंद हो जाए?",
        "चेरनोबिल का एलीफेंट्स फुट: दुनिया का सबसे खतरनाक पत्थर",
        "अंतरिक्ष का वो ग्रह जो पूरा का पूरा हीरे का बना हुआ है"
    ]
    for top in test_topics:
        res = generate_rag_viral_script(top)
        print("=" * 65)
        print(f"[{res.get('category_label')}] -> {top}")
        print("TITLE :", res.get("title"))
        print("HOOK  :", res.get("hook"))
        print("SCRIPT:", res.get("script"))
        print("CTA   :", res.get("cta"))
        print("WORDS :", res.get("word_count"))
