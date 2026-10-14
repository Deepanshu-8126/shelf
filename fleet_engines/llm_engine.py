"""
=============================================================================
CENTRALIZED LLM ENGINE  -  Single source of truth for all Groq API calls.
=============================================================================
All channels import from here. Never hardcode a model name or API key elsewhere.

Supported models (fall-through cascade):
  PRIMARY   : llama-3.3-70b-versatile   (fast, very capable)
  SECONDARY : llama3-70b-8192           (stable fallback)
  TERTIARY  : llama3-8b-8192            (ultra-fast emergency)

Exported helpers:
  llm_complete(prompt, system, ...)          -> str
  llm_json(prompt, system, ...)              -> dict
  extract_keywords_llm(story, dur)           -> list[dict]
  generate_reddit_package()                  -> {question, story}
  generate_channel2_script(topic, ..)        -> {title, hook, script, cta}
=============================================================================
"""

import os
import sys
import re
import json

import time
import random
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from openai import OpenAI
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Bootstrap
# ---------------------------------------------------------------------------
_FLEET_DIR = Path(__file__).resolve().parent
_WORKSPACE_ROOT = _FLEET_DIR.parent
for _p in [str(_FLEET_DIR), str(_WORKSPACE_ROOT)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

load_dotenv(_WORKSPACE_ROOT / ".env")

log = logging.getLogger("llm_engine")


# ---------------------------------------------------------------------------
# Config - edit ONLY here, never in individual channel scripts
# ---------------------------------------------------------------------------
GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")

# Model cascade: tries each in order until one succeeds
# Primary: Qwen 3 (27B) - Top-tier creative multilingual & Hindi storytelling
_MODEL_CASCADE = [
    "qwen/qwen3.8-27b",      # Primary: highest quality for Hindi/multilingual storytelling
    "openai/gpt-oss-120b",   # Secondary: high parameter reasoning fallback
    "openai/gpt-oss-20b",    # Tertiary: fast fallback
]


_GROQ_BASE_URL = "https://api.groq.com/openai/v1"


# ---------------------------------------------------------------------------
# Core: universal LLM completion with cascade + retry
# ---------------------------------------------------------------------------
def llm_complete(
    prompt: str = "",
    system: str = "",
    temp: float = 0.72,
    max_tokens: int = 600,
    conversation: Optional[List[Dict]] = None,
    remove_nl: bool = True,
) -> str:
    """
    Universal text completion via Groq with automatic model cascade.
    Returns response text. Raises RuntimeError if all models fail.
    """
    if not GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY is not set. Add it to .env")

    client = OpenAI(api_key=GROQ_API_KEY, base_url=_GROQ_BASE_URL)
    messages = conversation or [
        {"role": "system", "content": system or "You are a helpful assistant."},
        {"role": "user", "content": prompt},
    ]

    last_err: Exception = RuntimeError("No models attempted.")
    for model in _MODEL_CASCADE:
        for attempt in range(2):
            try:
                resp = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temp,
                    timeout=40,
                )
                text = resp.choices[0].message.content.strip()
                if remove_nl:
                    text = re.sub(r"\s+", " ", text)
                log.debug(f"[LLM] model={model} tokens={len(text.split())}")
                return text
            except Exception as e:
                last_err = e
                log.warning(f"[LLM] {model} attempt {attempt + 1} failed: {e}")
                time.sleep(1 + attempt)

    raise RuntimeError(f"All LLM models failed. Last error: {last_err}")


def llm_json(
    prompt: str = "",
    system: str = "",
    temp: float = 0.72,
    max_tokens: int = 450,
    conversation: Optional[List[Dict]] = None,
    fallback: Optional[Dict] = None,
) -> Dict:
    """
    Like llm_complete() but always returns a Python dict.
    Extracts JSON from response. Returns fallback dict on parse failure.
    """
    system_with_json = (
        (system or "") + "\nReturn ONLY valid JSON. No markdown fences. No explanation."
    )
    try:
        raw = llm_complete(
            prompt=prompt,
            system=system_with_json,
            temp=temp,
            max_tokens=max_tokens,
            conversation=conversation,
            remove_nl=False,
        )
    except Exception as e:
        log.warning(f"[LLM] llm_complete error: {e}")
        if fallback is not None:
            return fallback
        raise

    # Clean markdown fences if present
    cleaned_raw = re.sub(r"^```(?:json)?\s*", "", raw.strip(), flags=re.MULTILINE)
    cleaned_raw = re.sub(r"\s*```$", "", cleaned_raw.strip(), flags=re.MULTILINE)

    # Try direct parse
    try:
        return json.loads(cleaned_raw)
    except Exception:
        pass

    # Try object form
    match = re.search(r"\{.*\}", cleaned_raw, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except Exception:
            pass
    # Try array form
    match_arr = re.search(r"\[.*\]", cleaned_raw, re.DOTALL)
    if match_arr:
        try:
            return json.loads(match_arr.group(0))
        except Exception:
            pass

    # Robust regex key extractor (recovers keys even if JSON has unclosed brackets or syntax errors)
    extracted = {}
    for key in ["title", "hook", "script", "cta", "question", "story"]:
        m = re.search(rf'"{key}"\s*:\s*"([^"\\]*(?:\\.[^"\\]*)*)"', cleaned_raw)
        if m:
            try:
                extracted[key] = m.group(1).encode().decode("unicode_escape", errors="replace")
            except Exception:
                extracted[key] = m.group(1)
    if "script" in extracted or "story" in extracted:
        log.info(f"[LLM] Recovered {list(extracted.keys())} via regex key extractor.")
        if fallback is not None:
            merged = fallback.copy()
            merged.update(extracted)
            return merged
        return extracted

    if fallback is not None:
        log.warning(f"[LLM] JSON parse failed, using fallback. Raw start: {raw[:200]}")
        return fallback
    raise ValueError(f"Could not parse JSON from LLM response:\n{raw[:500]}")


# ---------------------------------------------------------------------------
# Shared: AI-slop sanitizer (used by both channels)
# ---------------------------------------------------------------------------
BANNED_AI_PHRASES = [
    "have you ever wondered", "in a world where", "delve into", "delving",
    "testament to", "tapestry of", "it turns out", "buckle up", "let's dive in",
    "let us dive in", "without further ado", "fascinating", "beacon of",
    "at the end of the day", "needless to say", "unravel the mystery",
    "unraveling", "a stark reminder", "game changer", "revolutionary",
    "like and subscribe", "don't forget to subscribe",
    "namaskar dosto", "kripya channel ko subscribe karein", "swagat hai aapka",
    "aaj hum baat karenge", "aaiye jaante hain", "like share subscribe",
    "लाइक, शेयर और सब्सक्राइब", "लाइक शेयर सब्सक्राइब", "सब्सक्राइब करना ना भूलें",
]

# Mapping of textbook robotic Hindi slop to natural spoken colloquial Hindi
HINDI_SLOP_REPLACEMENTS = {
    # Robotic openings & thought experiments
    "सोचिए, एक रात": "अगर आज रात",
    "सोचिए,": "जरा सोचो,",
    "सोचिए": "कभी सोचा है",
    "कल्पना कीजिए": "अगर ऐसा हो कि",
    "मान लीजिए": "मान लो",
    "प्रतीत होता है": "लगता है",
    
    # Hard Sanskrit / Textbook words -> Simple natural spoken words
    "घूर्णन अस्थिर": "संतुलन बिगड़ना",
    "घूर्णन": "घूमना",
    "अस्थिर": "बेकाबू",
    "अनियंत्रित": "बेकाबू",
    "सुनामी जैसी ध्वनि आएगी": "भयंकर सुनामी शहरों को बहा ले जाएगी",
    "ध्वनि आएगी": "आवाज़ गूंजेगी",
    "ध्वनि": "आवाज़",
    "दिन-रात का चक्र": "दिन और रात का हिसाब",
    "चक्र बिगड़": "हिसाब बिगड़",
    "संचार टूट जाएगा": "सारे फोन, इंटरनेट और बिजली बंद हो जाएंगे",
    "संचार टूटते": "फोन और इंटरनेट बंद होते",
    "संचार": "फोन और इंटरनेट",
    "लोग बिखरते देखेंगे": "चारों तरफ चीख-पुकार मच जाएगी",
    "तटवर्ती शहरों को धकेलेंगी": "किनारे के शहरों को डूबा देंगी",
    "तटवर्ती": "किनारे के",
    "तट के": "किनारे के",
    "तटों": "किनारों",
    "तट": "किनारे",
    "प्रकोप": "तबाही",
    "खिंचाव": "ग्रैविटी",
    "गुरुत्वाकर्षण": "ग्रैविटी",
    "कक्षा": "रास्ता",
    "अस्तित्व": "नामोनिशान",
    "अदृश्य हो जाए": "गायब हो जाए",
    "अदृश्य": "गायब",
    "मनुष्य": "लोग",
    "मानव जाति": "इंसान",
    "मानव": "इंसान",
    "अराजकता": "तबाही",
    "ज्वार‑भाटा": "समुद्र की भयानक लहरें",
    "ज्वार-भाटा": "समुद्र की भयानक लहरें",
    "ज्वार भाटा": "समुद्र की भयानक लहरें",
    "भय से कांपते": "दहशत में आ जाएंगे",
    "भय से कांपने": "दहशत में आने",
    "भयभीत": "खौफजदा",
    "विनाशकारी": "खौफनाक",
    "अंधकार": "अंधेरा",
    "अनंत": "हमेशा के लिए",
    "पवन पैटर्न": "हवाओं का रुख",
    "बायो‑रिद्म": "शरीर की घड़ी",
    "बायो-रिद्म": "शरीर की घड़ी",
    "मनोवैज्ञानिक": "दिमागी",
}


def sanitize_script(text: str) -> str:
    """Strips leaked AI cliches, markdown formatting, and transforms robotic Hindi to natural spoken Hindi."""
    cleaned = text
    # 1. Strip banned English & Hindi creator cliches
    for phrase in BANNED_AI_PHRASES:
        cleaned = re.sub(re.escape(phrase), "", cleaned, flags=re.IGNORECASE)

    # 2. Automatically replace robotic/textbook Hindi slop with natural spoken creator words
    for robotic_word, spoken_word in HINDI_SLOP_REPLACEMENTS.items():
        cleaned = re.sub(re.escape(robotic_word), spoken_word, cleaned)

    cleaned = re.sub(r"[*_#]", "", cleaned)
    cleaned = re.sub(r"^\s*\d+[.)]\s*", "", cleaned, flags=re.MULTILINE)
    return re.sub(r"\s+", " ", cleaned).strip()


# ---------------------------------------------------------------------------
# CHANNEL 1: Reddit Drama Script Generator
# ---------------------------------------------------------------------------
_REDDIT_STORY_SYSTEM = (
    "You are a world-class viral YouTube Shorts scriptwriter specializing in "
    "r/pettyrevenge and r/EntitledPeople drama.\n"
    "Your scripts consistently achieve 90%+ retention because they follow a strict 4-stage formula:\n"
    "1. [0:00-0:03s] EXPLOSIVE HOOK: First line starts with 'I...' and drops viewer into conflict.\n"
    "2. [0:03-0:30s] DRAMATIC TENSION: Punchy spoken dialogue, max 12 words per sentence.\n"
    "3. [0:30-0:40s] SATISFYING PAYOFF: Bad actor gets caught or outsmarted. Fast mic-drop.\n"
    "4. [0:40-0:45s] PROVOCATIVE CTA: Compelling debate question that forces fierce comments.\n\n"
    "Strict Constraints:\n"
    "- Length: Exactly 120-135 words (perfect for ~42 seconds of speech).\n"
    "- Language: 100% natural, crisp, conversational English.\n"
    "- Output strictly valid JSON with keys: question, story"
)

_REDDIT_THEMES = [
    "A toxic boss demands unpaid overtime on an employee's milestone day, but the employee uses the company's own policy for legal revenge.",
    "An entitled customer/Karen makes a scene trying to get a young worker fired, but security footage destroys her publicly.",
    "An arrogant roommate secretly steals groceries and lies to everyone's face, so the victim sets an undeniable visual trap.",
    "An entitled relative demands someone's first-class travel seat or heirloom, and gets utterly humiliated in front of the entire family.",
    "A coworker takes credit for someone else's project in front of the boss, but the original creator had one final card to play.",
    "A landlord tries to steal a tenant's deposit with fake damage claims, but the tenant had timestamped photo evidence.",
]

_REDDIT_FEW_SHOT = [
    {
        "role": "user",
        "content": "Theme: A toxic boss demands unpaid overtime on an employee's milestone day, but the employee uses company policy for revenge.",
    },
    {
        "role": "assistant",
        "content": json.dumps({
            "question": "What's the pettiest revenge you've ever pulled on a toxic boss?",
            "story": (
                "My manager told me: 'If you refuse unpaid overtime, turn in your laptop right now.' "
                "So I did. What he forgot was that I was the sole administrator of their cloud database. "
                "On Monday morning, their entire checkout system went pitch black. When he called me "
                "screaming that the store was losing ten thousand dollars an hour, I answered calmly: "
                "'My freelance emergency rate is two hundred dollars an hour, paid upfront.' He wired "
                "the money in three minutes flat. Did I take it too far, or did he deserve every bit "
                "of it? Drop your thoughts below."
            ),
        }),
    },
]

_REDDIT_FALLBACK = {
    "question": "What is the most satisfying revenge you've ever witnessed against an entitled person?",
    "story": (
        "My manager told me: 'If you refuse unpaid overtime, turn in your laptop right now.' So I did. "
        "What he forgot was that I was the sole administrator of their cloud database. On Monday morning, "
        "their entire checkout system went pitch black. When he called me screaming that the store was "
        "losing ten thousand dollars an hour, I answered calmly: 'My freelance emergency rate is two "
        "hundred dollars an hour, paid upfront.' He wired the money in three minutes flat. Did I take it "
        "too far, or did he deserve every bit of it? Drop your thoughts below."
    ),
}

_reddit_cache: Dict = {}


def generate_reddit_package(force_refresh: bool = False) -> Dict[str, str]:
    """
    Generates {question, story} for Channel 1.
    Result is cached per process run unless force_refresh=True.
    """
    global _reddit_cache
    if _reddit_cache and not force_refresh:
        return _reddit_cache

    theme = random.choice(_REDDIT_THEMES)
    conversation = (
        [{"role": "system", "content": _REDDIT_STORY_SYSTEM}]
        + _REDDIT_FEW_SHOT
        + [{"role": "user", "content": f"Theme: {theme}"}]
    )

    data = llm_json(conversation=conversation, fallback=_REDDIT_FALLBACK, temp=0.75)
    if "story" not in data:
        data = _REDDIT_FALLBACK.copy()

    _reddit_cache = data
    return data


# ---------------------------------------------------------------------------
# CHANNEL 2: Vox Mystery Documentary Script Generator
# ---------------------------------------------------------------------------
_VOX_SYSTEM = (
    "You are a RAW, unfiltered Indian mystery documentary filmmaker & spoken storyteller "
    "(style: Zack D. Films, MrBallen, Dhruv Rathee, Nitish Rajput).\n"
    "You write spoken, gripping, raw, conversational scripts for 35-second viral YouTube Shorts.\n\n"
    "PILLAR BENCHMARKS (replicate this energy):\n"
    "[PILLAR 1] 'Amazon ke jungle mein ek aisi jagah hai, jahan helicopter jaye toh dashboard ki saari battiyan band ho jaati hain.'\n"
    "[PILLAR 2] 'Agar koi jhooth bol raha hai, toh 4 second ke liye uski aankhon ke beech mein dekhte raho. Ek lafz mat bolo.'\n"
    "[PILLAR 3] 'James Webb ne deep space mein 300 million light years ka pura ka pura andhera dhoondha hai!'\n"
    "[PILLAR 4] 'Kisi ke maathe ke center mein ghoorte raho. 5 second mein uska gussa thanda pad jayega.'\n\n"
    "BANNED: 'विशाल', 'उभरा', 'रहस्यमय', 'namaskar dosto', 'delve', 'tapestry', 'fascinating'\n\n"
    "RULES: Spoken Roman Hinglish for Hindi. Visceral English for English. "
    "Hook in first 3 seconds. Desi analogies. Spicy 50/50 CTA debate question."
)


def generate_channel2_script(
    topic: str,
    niche_context: str = "Unsolved Mysteries & Science",
    lang: str = "hi",
    word_count_target: int = 80,
) -> Dict[str, str]:
    """
    Generates {title, hook, script, cta, lang} for Channel 2.
    """
    is_hindi = lang == "hi"
    lang_desc = (
        "Spoken Roman Hinglish (YouTube Shorts style)"
        if is_hindi
        else "Atmospheric, visceral investigative English"
    )

    user_prompt = (
        f"Topic: {topic}\n"
        f"Niche: {niche_context}\n"
        f"Language: {lang_desc}\n"
        f"Length: Exactly {word_count_target} to {word_count_target + 12} words "
        f"(single continuous spoken paragraph, short punchy sentences).\n\n"
        "Output strictly valid JSON:\n"
        '{"title": "Viral 5-word title with #shorts", '
        '"hook": "Opening 0-3 second sentence", '
        '"script": "Full continuous spoken script", '
        '"cta": "Closing spicy debate question"}'
    )

    fallback = (
        {
            "title": f"{topic} का खौफनाक सच #shorts",
            "hook": "चार सेकंड का सन्नाटा किसी भी इंसान को अंदर से तोड़ सकता है।",
            "script": (
                "चार सेकंड का सन्नाटा किसी भी इंसान को अंदर से तोड़ सकता है। "
                "एफबीआई पूछताछ में जब कोई झूठ बोलता है, तो एजेंट बहस नहीं करते। "
                "वे बस चार सेकंड तक बिना पलक झपकाए खामोश रहते हैं। "
                "क्या आपने कभी किसी का झूठ ऐसे पकड़ा है? नीचे बताओ।"
            ),
            "cta": "क्या आपने कभी किसी का झूठ ऐसे पकड़ा है? नीचे बताओ।",
        }
        if is_hindi
        else {
            "title": f"The Dark Truth of {topic} #shorts",
            "hook": "Four seconds of absolute silence can break any human mind.",
            "script": (
                "Four seconds of absolute silence can break any human mind. "
                "In federal interrogations, agents never argue with a suspect. "
                "Instead, they stare in complete silence for four agonizing seconds. "
                "The suspect's brain panics and over-explains until the lie collapses. "
                "Have you ever used silence to catch someone lying? Tell me below."
            ),
            "cta": "Have you ever used silence to catch someone lying? Tell me below.",
        }
    )

    data = llm_json(
        prompt=user_prompt,
        system=_VOX_SYSTEM,
        temp=0.70,
        fallback=fallback,
    )

    data["script"] = sanitize_script(data.get("script", ""))
    data["hook"] = sanitize_script(data.get("hook", ""))
    data["cta"] = sanitize_script(data.get("cta", ""))
    data["lang"] = lang
    return data


# ---------------------------------------------------------------------------
# CHANNEL 3: Cosmic What-If & Dark Science Script Generator (Real Logic + Ultra-Simple Hindi)
# ---------------------------------------------------------------------------
_COSMIC_SYSTEM = (
    "You are India's #1 viral science storyteller writing YouTube Shorts in spoken Hindi.\n"
    "Write ONE unbroken flowing paragraph — exactly like a real viral Hindi short transcript.\n\n"
    "WRITING STYLE — copy this structure exactly:\n"
    "Open with a direct punchy question ('अगर आज रात अचानक...'). Then immediately give the first "
    "physical shock in simple words — what breaks first, concretely. Then reveal the real hidden "
    "science with specific numbers (e.g. 3x faster, 6-8 hours, 400 km/h, 300 feet). Escalate to "
    "climax naturally. End with a chilling debate question that makes viewers comment. Write like "
    "explaining to a friend over chai — one continuous breath, zero lecture tone.\n\n"
    "BANNED WORDS — never use: घूर्णन, अस्थिर, ध्वनि, चक्र, संचार, अस्तित्व, प्रकोप, तटवर्ती, "
    "ज्वार-भाटा, अदृश्य, मनुष्य, मानव, अराजकता, लाइक, शेयर, सब्सक्राइब.\n"
    "USE INSTEAD: घूमने की रफ़्तार, बेकाबू, आवाज़, तबाही, सुनामी, गायब, इंसान, लोग, तेज़ हवाएं, दिन-रात.\n\n"
    "LENGTH: Exactly 40 to 45 words in Devanagari script. Output strict JSON: title, hook, script, cta.\n\n"
    "GOLD STANDARD — clone this exact 42-word cadence and logic depth:\n"
    "{\n"
    "  \"title\": \"अगर चाँद अचानक गायब हो जाए? #shorts\",\n"
    "  \"hook\": \"अगर आज रात चाँद अचानक गायब हो जाए, तो क्या होगा?\",\n"
    "  \"script\": \"अगर आज रात अचानक चाँद गायब हो जाए, तो समंदर में 100 मीटर ऊंची सुनामी आएगी! धरती इतनी तेज़ घूमने लगेगी कि दिन सिर्फ 6 घंटे का रह जाएगा, और 400 की स्पीड से बर्फीली हवाएं चलेंगी। क्या इंसान ऐसी तबाही में बच पाएगा? कमेंट में बताओ!\",\n"
    "  \"cta\": \"क्या इंसान 6 घंटे के दिन में जिंदा रह पाएगा? कमेंट में बताओ!\"\n"
    "}"
)


def generate_channel3_script(
    topic: str,
    pillar_name: str = "Cosmic What-If & Dark Science",
    lang: str = "hi",
    word_count_target: int = 42,
) -> Dict[str, str]:
    """
    Generates {title, hook, script, cta, lang} for Channel 3 using
    Viral Transcripts RAG (cloning real 15M+ view human creator cadence).
    """
    try:
        from viral_rag_engine import generate_rag_viral_script
        rag_data = generate_rag_viral_script(
            topic=topic,
            niche="cosmic_what_if",
            lang=lang,
            word_count_target=word_count_target,
        )
        if rag_data and rag_data.get("script"):
            rag_data["lang"] = lang
            return rag_data
    except Exception as e:
        log.warning(f"[RAG] Fallback to standard prompt due to: {e}")

    user_prompt = (
        f"Topic: {topic}\n"
        f"Niche: {pillar_name}\n"
        f"Target Length: Exactly {word_count_target} to {word_count_target + 5} words in spoken Devanagari Hindi.\n\n"
        "Output strictly valid JSON:\n"
        '{"title": "Viral 5-word title with #shorts", '
        '"hook": "Opening 0-3 second hook sentence", '
        '"script": "Full continuous spoken script in natural Devanagari Hindi (ending with a CTA debate question)", '
        '"cta": "Closing provocative debate question"}'
    )

    fallback = {
        "title": f"अगर {topic} सच हो जाए? #shorts",
        "hook": f"अगर आज रात अचानक {topic}, तो सबसे पहला झटका धरती को लगेगा!",
        "script": (
            f"अगर आज रात अचानक {topic}, तो धरती 400 की रफ्तार से घूमने लगेगी! "
            "दिन सिर्फ 6 घंटे का रह जाएगा, समंदर में विशाल सुनामी आएगी और बर्फीला अंधेरा छा जाएगा। "
            "क्या इंसान ऐसी तबाही से कभी बच पाएगा? अपनी राय कमेंट में बताओ!"
        ),
        "cta": "क्या इंसान कभी ऐसी तबाही से बच पाएगा? नीचे कमेंट में बताओ!",
    }

    data = llm_json(
        prompt=user_prompt,
        system=_COSMIC_SYSTEM,
        temp=0.55,
        fallback=fallback,
    )

    data["script"] = sanitize_script(data.get("script", ""))
    data["hook"] = sanitize_script(data.get("hook", ""))
    data["cta"] = sanitize_script(data.get("cta", ""))
    data["lang"] = lang
    return data


# ---------------------------------------------------------------------------
# SHARED: Visual Keyword NLP Extractor (popup overlays for both channels)
# ---------------------------------------------------------------------------
_KEYWORD_SYSTEM = (
    "Extract 3-4 high-impact visual nouns from the given story for video popup overlays. "
    "Each keyword must be a concrete, visualizable noun (money, phone, boss, car, etc.). "
    "Assign realistic timestamps spread evenly across the video duration. "
    "SFX mapping: objects=whoosh, money/salary=cash, dramatic twist=boom, photo/evidence=click. "
    "Return ONLY a valid JSON array, no other text, no markdown."
)


def extract_keywords_llm(
    story_text: str,
    video_duration: float,
    max_keywords: int = 4,
) -> List[Dict[str, Any]]:
    """
    Extracts visual popup keywords + timestamps from story text via LLM.
    Returns list of {keyword, timestamp, sfx_type} dicts.
    Falls back to regex extraction if LLM fails.
    """
    if not story_text.strip():
        return []

    prompt = (
        f"Story:\n{story_text}\n\n"
        f"Video duration: {video_duration:.1f}s\n"
        f"Max keywords: {max_keywords}\n\n"
        'Return JSON array like: [{"keyword": "money", "timestamp": 5.0, "sfx_type": "cash"}]'
    )

    try:
        raw = llm_complete(
            prompt=prompt,
            system=_KEYWORD_SYSTEM,
            temp=0.3,
            max_tokens=300,
            remove_nl=False,
        )
        match = re.search(r"\[.*\]", raw, re.DOTALL)
        if match:
            keywords = json.loads(match.group(0))
            valid = []
            for k in keywords[:max_keywords]:
                if isinstance(k, dict) and "keyword" in k and "timestamp" in k:
                    valid.append({
                        "keyword": str(k["keyword"]).lower().strip(),
                        "timestamp": min(float(k["timestamp"]), video_duration - 2.0),
                        "sfx_type": str(k.get("sfx_type", "whoosh")),
                    })
            if valid:
                return valid
    except Exception as e:
        log.warning(f"[LLM] Keyword extraction failed: {e}")

    return _extract_keywords_regex(story_text, video_duration, max_keywords)


def _extract_keywords_regex(story: str, duration: float, max_k: int) -> List[Dict]:
    """Regex-based local fallback when LLM unavailable."""
    VISUAL_KEYWORDS = {
        "money": "cash", "cash": "cash", "dollar": "cash", "dollars": "cash",
        "salary": "cash", "wage": "cash", "pay": "cash", "paid": "cash",
        "thousand": "cash", "thousands": "cash",
        "boss": "boom", "manager": "boom", "fired": "boom", "supervisor": "boom",
        "phone": "whoosh", "mobile": "whoosh", "laptop": "whoosh", "computer": "whoosh",
        "car": "whoosh", "house": "whoosh", "food": "whoosh",
        "photo": "click", "camera": "click", "video": "click",
        "proof": "click", "evidence": "click", "recording": "click",
    }
    found, seen = [], set()
    step = duration / (max_k + 1)
    for word in story.lower().split():
        clean = re.sub(r"[^a-z]", "", word)
        if clean in VISUAL_KEYWORDS and clean not in seen:
            idx = len(found)
            found.append({
                "keyword": clean,
                "timestamp": round(step * (idx + 1), 1),
                "sfx_type": VISUAL_KEYWORDS[clean],
            })
            seen.add(clean)
            if len(found) >= max_k:
                break
    return found


# ---------------------------------------------------------------------------
# Quick smoke-test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    print("=" * 60)
    print("LLM ENGINE SMOKE TEST")
    print("=" * 60)

    print("\n[1] Simple completion...")
    result = llm_complete("Say exactly: LLM Engine OK", temp=0.0)
    print(f"    -> {result}")

    print("\n[2] Channel 1 Reddit package...")
    pkg = generate_reddit_package()
    print(f"    Q: {pkg['question']}")
    print(f"    Story ({len(pkg['story'].split())} words): {pkg['story'][:80]}...")

    print("\n[3] Channel 2 Vox script (Hindi)...")
    s = generate_channel2_script("The FBI 4-second silence rule", lang="hi")
    print(f"    Title: {s['title']}")
    print(f"    Hook: {s['hook']}")

    print("\n[4] Keyword extractor...")
    story = "My boss fired me over cash, so I took a photo and exposed him with my laptop."
    kws = extract_keywords_llm(story, video_duration=45.0)
    print(f"    Keywords: {kws}")

    print("\n All LLM Engine tests passed.")
