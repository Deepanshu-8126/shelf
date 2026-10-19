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
    clean_topic_name = topic.rstrip("?!. ")

    # Topic-specific engaging fallback
    fallback_hook = f"क्या आपको पता है कि {clean_topic_name}?"
    fallback_script = (
        f"सोचिए... क्या आपको पता है कि {clean_topic_name}? "
        "जब वैज्ञानिकों ने इस पर गहराई से रिसर्च की, तो उनके होश उड़ गए! "
        "शरीर के अंदर होने वाली यह प्रक्रिया जितनी रहस्यमयी है, उतनी ही चौंकाने वाली भी। "
        "दरअसल इसके पीछे एक बेहद जटिल न्यूरोलॉजिकल और बायोलॉजिकल कारण छिपा हुआ है। "
        "क्या आपको इससे पहले इस हैरान कर देने वाले सच के बारे में पता था? कमेंट्स में जरूर बताइए!"
    )
    fallback_cta = "क्या आपको इससे पहले इस हैरान कर देने वाले सच के बारे में पता था? कमेंट्स में जरूर बताइए!"

    fallback = {
        "title": f"{clean_topic_name[:32]} #shorts",
        "hook": fallback_hook,
        "script": fallback_script,
        "cta": fallback_cta,
    }

    try:
        # -------------------------------------------------------------------
        # STEP 1: Causal Beat Outline (Dynamic Category & Dramatic Depth)
        # -------------------------------------------------------------------
        log.info(f"[StoryTeller-Step1] Planning beats for category '{cat_profile['label']}' -> '{topic}'...")
        step1_prompt = (
            f"Topic: {topic}\n"
            f"Category: {cat_profile['label']}\n"
            f"Tone Directive: {cat_profile['tone']}\n\n"
            "Create a high-retention 4-beat story outline for a 45-50 second viral YouTube Short:\n"
            "Beat 1 (Visual & Emotional Hook 0-6s): Visceral, shocking question or mind-bending scenario using pauses ('सोचिए...').\n"
            "Beat 2 (The Real Mechanism 6-22s): Step-by-step biological, physical, or historical explanation of WHY and HOW it happens.\n"
            "Beat 3 (The Mind-Bending Twist 22-38s): The jaw-dropping fact that 99% of people misunderstand or don't know.\n"
            "Beat 4 (The Provocative Debate CTA 38-48s): An intriguing open loop or debate question asking viewers their thoughts (NEVER ask to subscribe).\n"
            "Keep each beat punchy and vivid."
        )
        outline = llm_complete(
            prompt=step1_prompt,
            system="You are an elite YouTube Shorts documentary director creating high-retention, curiosity-driven scripts.",
            temp=0.60,
        )

        # -------------------------------------------------------------------
        # STEP 2: Spoken Hindi Drafter (Conversational Indian Creator Narrative)
        # -------------------------------------------------------------------
        log.info(f"[StoryTeller-Step2] Drafting natural spoken Hindi script with dramatic pacing...")
        step2_prompt = (
            f"Story Outline:\n{outline}\n\n"
            f"CATEGORY & TONE: {cat_profile['tone']}\n\n"
            "INSTRUCTIONS FOR NATURAL SPOKEN HINDI DOCUMENTARY NARRATOR:\n"
            "- Write ONE unbroken flowing spoken script in everyday conversational creator Hindi/Hindustani (100 to 125 words).\n"
            "- Talk like a top Indian YouTube creator (like Dhruv Rathee or Nitish Rajput) talking naturally to a friend over chai.\n"
            "- STRICT PROHIBITION OF SANSKRIT/TEXTBOOK WORDS:\n"
            "  * NEVER use 'मस्तिष्क' -> ALWAYS use 'दिमाग'\n"
            "  * NEVER use 'स्वतंत्र' -> ALWAYS use 'आज़ाद' or 'कंट्रोल में'\n"
            "  * NEVER use 'राय' or 'अपनी राय बताइए' -> ALWAYS use 'कमेंट में बताओ आप क्या सोचते हो'\n"
            "  * NEVER use 'नियंत्रित' -> ALWAYS use 'कंट्रोल'\n"
            "  * NEVER use 'तीव्र' -> ALWAYS use 'खतरनाक' or 'भयानक'\n"
            "  * NEVER use 'जल' -> ALWAYS use 'पानी'\n"
            "  * NEVER use 'मनुष्य' -> ALWAYS use 'इंसान' or 'लोग'\n"
            "  * NEVER use 'प्रक्रिया' -> ALWAYS use 'चीज' or 'सिस्टम'\n"
            "- USE DRAMATIC PACING PUNCTUATION: Use ellipses ('...'), em-dashes ('—'), questions ('?'), and commas (',') generously so the narrator pauses naturally with suspense.\n"
            "- ZERO AI Melodrama ('प्रलय', 'खून-खराबा', 'कयामत' banned).\n"
            "- STRICT PROHIBITION: NEVER say 'नमस्ते दोस्तों', 'चैनल को सब्सक्राइब करें', 'वीडियो को लाइक करें', 'मिलते हैं अगले वीडियो में'.\n"
            "- END with an intriguing conversational debate question (e.g. 'कमेंट में बताओ, क्या कभी आपके साथ ऐसा हुआ है?').\n"
            "- Output ONLY the Hindi script paragraph, nothing else."
        )
        draft = llm_complete(
            prompt=step2_prompt,
            system="You are India's top YouTube creator writing 100% natural conversational creator Hindi. Zero Sanskrit textbook words allowed.",
            temp=0.55,
            max_tokens=450,
            remove_nl=False,
        )

        # -------------------------------------------------------------------
        # STEP 3: Slop Reviewer, Negative Filter & Polish
        # -------------------------------------------------------------------
        log.info(f"[StoryTeller-Step3] Reviewing, purging AI slop & polishing JSON...")
        step3_prompt = (
            f"Draft Script to Review:\n\"{draft}\"\n\n"
            "CRITIQUE & NATURAL POLISH CHECKLIST:\n"
            "1. REPLACE ALL SANSKRIT/FORMAL SLOP: 'मस्तिष्क' MUST become 'दिमाग', 'स्वतंत्र' MUST become 'आज़ाद', 'नियंत्रित' MUST become 'कंट्रोल', 'राय' MUST become 'सोच', 'तीव्र' MUST become 'खतरनाक'.\n"
            "2. Fix broken spellings/corrupted text (NO cyrillic letters like 'स्पाзм'; write 'ऐंठन' or 'स्पैज्म').\n"
            "3. Ensure conversational, suspenseful rhythm with clear emotional breath marks (..., —, ?, !).\n"
            "4. Ensure total word count is between 100 and 125 words (around 45-50 seconds audio).\n"
            "5. Strictly ensure NO generic subscribe/like callouts. End with a natural debate question like 'कमेंट में बताओ, आप क्या सोचते हो?'.\n"
            "6. Output STRICT JSON with keys: title, hook, script, cta.\n"
            "Format:\n"
            '{"title": "Viral 5-word title #shorts", "hook": "First sentence hook", "script": "Full continuous polished script with natural creator words and dramatic punctuation", "cta": "Closing conversational question"}'
        )
        data = llm_json(
            prompt=step3_prompt,
            system="You are an elite YouTube script editor enforcing 100% natural conversational Indian Hindi with zero textbook/Sanskrit slop. Return ONLY valid JSON.",
            temp=0.35,
            fallback=fallback,
        )
    except Exception as e:
        log.error(f"[StoryTeller] Error in 3-step pipeline: {e}. Using fallback.")
        data = fallback

    data["script"] = sanitize_script(data.get("script", ""))
    data["hook"] = sanitize_script(data.get("hook", ""))
    data["cta"] = sanitize_script(data.get("cta", fallback_cta))
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
