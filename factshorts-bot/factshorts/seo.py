"""SEO module: title (<=60 chars, keyword first), description with hashtags, tags, pinned comment."""
from __future__ import annotations

import random
import re

from .config import Config, get_config
from .llm import LLM, LLMError
from .script_writer import Script
from .topic_engine import Topic
from .utils import clean_text, module_logger

log = module_logger("seo")

TITLE_SUFFIXES = [
    "Why?", "Explained", "You Didn't Know", "Facts", "In 15 Seconds",
]
NICHE_TAGS = {
    "space": ["space facts", "astronomy", "universe", "science facts", "space shorts", "nasa", "cosmos", "astrophysics"],
    "psychology": ["psychology facts", "dark psychology", "human behavior", "mind tricks", "psychological hacks", "manipulation techniques", "psychology shorts", "body language", "psychology tips"],
    "history": ["history facts", "historical mysteries", "unsolved history", "ancient history", "bizarre history", "history shorts", "did you know history", "archaeology discoveries"],
    "mystery": ["unsolved mysteries", "strange events", "creepy mysteries", "conspiracy facts", "bizarre facts", "mystery shorts", "dark mysteries"],
    "finance": ["personal finance", "money tips", "wealth mindset", "credit card hacks", "investing for beginners", "financial freedom", "money hacks", "finance shorts", "wealth secrets", "passive income"],
    "legal": ["legal hacks", "court drama", "consumer rights", "lawyer tips", "crazy laws", "legal advice", "bizarre court cases", "legal rights", "law shorts"],
    "science": ["science facts", "science shorts", "amazing science", "physics facts", "biology facts", "scientific discoveries"],
    "animals": ["animal facts", "wildlife facts", "animal shorts", "nature facts", "amazing animals", "nature shorts"],
    "kids": ["kids learning", "fun facts for kids", "cartoon facts", "amazing facts kids", "educational shorts"],
}
BASE_TAGS = ["shorts", "didyouknow", "facts", "fact shorts", "learn something new", "youtube shorts", "interesting facts", "viral shorts"]


def _clip_title(text: str, limit: int = 60) -> str:
    text = clean_text(text)
    if len(text) <= limit:
        return text
    cut = text[:limit]
    if " " in cut[limit - 15 :]:
        cut = cut[: cut.rfind(" ")]
    return cut.rstrip(" ,.;:-") or text[:limit]


POWER_KEYWORDS = [
    "The Truth About", "Why Nobody Talks About", "What Happens If",
    "The Terrifying Reason", "The Hidden Secret Of", "The Science Behind",
    "Why You Should Never", "Explained in 15 Seconds", "The Real Reason"
]


def score_title_ctr(title: str, topic_keyword: str) -> float:
    """Claude-SEO inspired CTR scoring algorithm for YouTube Shorts titles."""
    score = 50.0
    t_lower = title.lower()
    kw_lower = topic_keyword.lower()

    # Optimal mobile length: 32 - 52 chars
    length = len(title)
    if 35 <= length <= 52:
        score += 20.0
    elif 25 <= length <= 60:
        score += 10.0
    else:
        score -= 15.0

    # Keyword in the first half
    if kw_lower and kw_lower in t_lower[:len(title)//2 + 5]:
        score += 15.0

    # Power/curiosity triggers
    triggers = ["why", "how", "what", "secret", "never", "truth", "hidden", "real", "freeze", "stop", "explained"]
    matches = sum(1 for tr in triggers if tr in t_lower.split())
    score += min(matches * 5.0, 15.0)

    # Question or dash structure
    if "?" in title or "—" in title or ":" in title:
        score += 5.0

    return min(max(score, 10.0), 99.0)


def _offline_title(topic: Topic, script: Script) -> str:
    base = topic.topic.strip().rstrip(".")
    base = base[0].upper() + base[1:] if base else "Mind Blowing Fact"

    variants = [
        f"{base} Explained",
        f"The Truth About {base}",
        f"Why {base} Will Blow Your Mind",
        f"{base} — What You Didn't Know",
        f"{base} in 15 Seconds",
        f"The Secret of {base}"
    ]

    scored = []
    for var in variants:
        clipped = _clip_title(var, 58)
        s = score_title_ctr(clipped, base)
        scored.append((s, clipped))

    scored.sort(key=lambda x: x[0], reverse=True)
    best_score, best_title = scored[0]
    log.info("selected highest CTR title: %r (score: %.1f/100)", best_title, best_score)
    return best_title


def _offline_description(topic: Topic, script: Script) -> str:
    tags = NICHE_TAGS.get(topic.niche, NICHE_TAGS["science"])
    hashtags = " ".join("#" + t.replace(" ", "") for t in tags[:4])
    return (
        f"{script.hook}\n\n"
        f"{clean_text(topic.fact)}\n\n"
        "Real footage, original scripting and editing. Every fact is checked before posting. "
        "If you spot an error, tell me in the comments and I will pin the correction.\n\n"
        f"#{topic.niche} #shorts #facts #didyouknow\n{hashtags}\n\n"
        "Video: free stock footage (Pexels / Pixabay / Wikimedia Commons). "
        "Voice: synthetic narration, disclosed as altered or synthetic content."
    )


def _offline_tags(topic: Topic) -> list[str]:
    tags = [topic.niche, f"{topic.niche} facts", "facts", "shorts", "didyouknow", "fact shorts"]
    tags += NICHE_TAGS.get(topic.niche, [])
    tags += [topic.topic.lower(), f"{topic.topic.lower()} facts"]
    out: list[str] = []
    for t in tags:
        t = clean_text(t, 35).lower()
        if t and t not in out:
            out.append(t)
    return out[:14]


async def build_seo(topic: Topic, script: Script, llm: LLM | None = None, cfg: Config | None = None) -> dict:
    """Returns {title, description, tags, pinned_comment, hashtags}."""
    cfg = cfg or get_config()
    llm = llm or LLM(cfg)

    if llm.available and not cfg.test_mode:
        system = (
            "You are a YouTube Shorts SEO specialist. Be honest, no clickbait lies, "
            "no promises about money or health, plain English, no emojis in the title."
        )
        prompt = (
            f"Niche: {topic.niche}\nTopic: {topic.topic}\nFact: {topic.fact}\n"
            f"Spoken script: {script.full_text}\n\n"
            "Return JSON with keys:\n"
            '- title: <= 60 characters, main keyword in the first 3 words, no emojis\n'
            '- description: 3 short paragraphs, ends with 4-6 hashtags including #shorts\n'
            '- tags: array of 10-15 lowercase search tags\n'
            '- pinned_comment: one engaging question (max 12 words) that invites a reply\n'
            '- hashtags: array of the 4-6 hashtags used in the description'
        )
        try:
            data = await llm.json(prompt, system, max_tokens=900, temperature=0.7)
            title = _clip_title(str(data.get("title") or ""), 60)
            description = clean_text(str(data.get("description") or ""))
            tags = [clean_text(str(t), 35).lower() for t in (data.get("tags") or []) if str(t).strip()]
            pinned = clean_text(str(data.get("pinned_comment") or ""), 120)
            hashtags = ["#" + str(h).strip("#").replace(" ", "") for h in (data.get("hashtags") or [])]
            if len(title) >= 12 and len(description) >= 80 and len(tags) >= 8:
                return {
                    "title": title,
                    "description": description,
                    "tags": tags[:15],
                    "pinned_comment": pinned or "What surprised you most here?",
                    "hashtags": hashtags[:6] or ["#shorts"],
                    "source": llm.last_provider or "llm",
                }
            log.info("SEO response too thin, using offline generator")
        except LLMError as exc:
            log.warning("SEO generation failed (%s) -> offline generator", exc)

    tags = _offline_tags(topic)
    return {
        "title": _offline_title(topic, script),
        "description": _offline_description(topic, script),
        "tags": tags,
        "pinned_comment": "What surprised you most here? Tell me below.",
        "hashtags": ["#shorts"] + ["#" + t.replace(" ", "") for t in NICHE_TAGS.get(topic.niche, [])[:3]],
        "source": "offline-generator",
    }


def fix_hashtag_spacing(text: str) -> str:
    """YouTube ignores hashtags that are glued to a word; keep them clean."""
    return re.sub(r"(?<!\w)#(\w+)", lambda m: " #" + m.group(1), text).strip()
