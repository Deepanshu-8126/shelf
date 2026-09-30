"""Script writer: scripts for both video modes, plus keyword hooks for footage.

* ``facts`` mode - 26-46 words for a 10-15 s Short (VIDEO_MAX_DURATION).
* ``story`` mode - 130-200 words (about 60 s of narration) with a real narrative arc:
  hook -> setup -> turn -> payoff. Shorts allow 3 minutes, so 60 s is comfortably
  inside the format and long enough to tell a story instead of dropping one fact.

Output shape:
  hook      -> first 2 seconds, must stop the scroll
  body      -> the surprising fact
  closing   -> one-line payoff / call to follow
  sentences -> list of (text, keywords) used to pick matching stock clips
"""
from __future__ import annotations

import random
import re
from dataclasses import dataclass, field

from .config import Config, get_config
from .llm import LLM, LLMError
from .topic_engine import Topic
from .utils import clean_text, module_logger, words_of

log = module_logger("script_writer")

MIN_WORDS = 26           # facts mode window (kept as the module default)
MAX_WORDS = 46

# Neutral narrative glue for the offline story template. These lines add no facts -
# they only hold the story together, so nothing here can be wrong.
STORY_BRIDGES = [
    "It started with something completely ordinary.",
    "The details are what make it strange.",
    "That is where the story turns.",
    "And the record agrees.",
    "Put those two things together and it gets interesting.",
    "Which brings us to the part most people never hear about.",
    "The explanation is simpler than it looks.",
    "Once you see it, it is hard to unsee.",
    "That is the part worth sitting with.",
    "Which is why it still gets talked about today.",
]
STORY_CLOSERS = {
    "none": ["And that is the whole story.", "Which is exactly why it stuck.", "That is where it lands."],
    "soft": ["Worth remembering.", "Now you know the rest.", "That one stays with you."],
    "follow": ["Follow for a story like this daily.", "Follow for one of these every day.",
               "Follow if you want the next story."],
}


def word_window(cfg: Config) -> tuple[int, int, int]:
    """(min_words, max_words, target_words) for the active mode."""
    profile = cfg.profile()
    return profile.min_words, profile.max_words, profile.target_words

_STOP = {
    "a", "an", "the", "of", "to", "and", "in", "is", "it", "that", "this", "for", "on", "with",
    "as", "at", "by", "from", "are", "was", "be", "you", "your", "day", "one", "than", "then",
}

# Fallback visual directions per niche so footage search never gets junk keywords
# such as "a" or "day" (that is how you end up with a screen recording in your video).
GENERIC_VISUALS: dict[str, list[str]] = {
    "space": ["space nebula", "planet surface", "stars night sky", "earth from space", "galaxy timelapse"],
    "psychology": ["human brain abstract", "person thinking", "neon abstract motion", "library books"],
    "history": ["ancient ruins", "old manuscripts", "museum artifacts", "desert archaeology"],
    "science": ["laboratory science", "microscope footage", "water droplets macro", "physics experiment"],
    "animals": ["wildlife closeup", "ocean underwater", "birds in flight", "forest animals"],
}
MIN_KEYWORD_LEN = 3

# Voice/tone presets. The default ("friendly") deliberately avoids advert language:
# no "in this video", no "smash that subscribe", no fake urgency. Hooks create curiosity
# from the fact itself instead of shouting.
STYLE_PROMPTS = {
    "friendly": (
        "Tone: like explaining something fascinating to a friend. Warm, curious, plain words. "
        "Short sentences. No hype adjectives, no shouting, no 'guys', no 'literally'."
    ),
    "documentary": (
        "Tone: calm, precise science-documentary narration. Measured pace, concrete nouns, "
        "no rhetorical questions, no exclamation marks."
    ),
    "punchy": (
        "Tone: high-energy short-form narration - still factual and never clickbait. "
        "Very short sentences, strong verbs, one idea per line."
    ),
}

HOOKS = {
    "friendly": [
        "Here's something strange.", "Nobody talks about this one.", "This one is quietly wild.",
        "Wait until you hear the number.", "Small thing, big consequence.", "I did not expect this.",
    ],
    "documentary": [
        "Consider this.", "This is stranger than it sounds.", "There is a detail here most people miss.",
        "The record is clear on this.", "It begins with something ordinary.",
    ],
    "punchy": [
        "This is wild.", "One detail changes everything.", "Look at the numbers.", "Real quick, it's strange.",
        "Nobody expects this part.",
    ],
}

CLOSINGS = {
    "none": [
        "That is the whole trick.", "Which explains a lot.", "And it has always been that way.",
        "Which is exactly why it matters.", "Small fact, real consequences.",
    ],
    "soft": [
        "Now you know.", "Save this before you forget.", "Sit with that for a moment.",
        "Worth remembering.", "That one tends to stick.",
    ],
    "follow": [
        "Follow for one fact a day.", "Follow and you'll learn one of these daily.",
        "Follow if you want the next one.",
    ],
}

# phrases that make a fact video sound like an advertisement - stripped or rejected
AD_PHRASES = [
    "in this video", "don't forget to subscribe", "do not forget to subscribe", "smash that",
    "link in the description", "link in description", "check the link", "swipe up", "click below",
    "comment below", "drop a comment", "like and subscribe", "hit the bell", "stay tuned",
    "you won't believe", "you wont believe", "insane", "crazy fact", "mind blowing", "mind-blowing",
    "guys", "literally", "must watch", "viral", "secret trick", "life hack",
]
CTA_LEAD_INS = {"none", "soft", "follow"}


def style_of(cfg: Config) -> str:
    style = (cfg.script_style or "friendly").lower()
    return style if style in STYLE_PROMPTS else "friendly"


def cta_of(cfg: Config) -> str:
    cta = (cfg.cta_style or "soft").lower()
    return cta if cta in CTA_LEAD_INS else "soft"


def strip_ad_language(text: str) -> str:
    """Remove advert/marketing phrasing from a generated line (keeps the meaning)."""
    out = text or ""
    for phrase in AD_PHRASES:
        if phrase in out.lower():
            pattern = re.compile(re.escape(phrase), re.I)
            out = pattern.sub("", out)
    out = re.sub(r"\s{2,}", " ", out)
    out = re.sub(r"\s+([,.;:!?])", r"\1", out)
    out = re.sub(r"^[,.;:!?\s]+", "", out)
    if out and out[0].islower():
        out = out[0].upper() + out[1:]
    return out.strip()


@dataclass
class Sentence:
    text: str
    keywords: list[str] = field(default_factory=list)


CTA_PAYOFF = "That is the whole trick."   # used when CTA_STYLE=none and the closing is missing


@dataclass
class Script:
    hook: str
    body: str
    closing: str
    sentences: list[Sentence]
    topic: str = ""
    niche: str = ""
    source: str = "llm"

    @property
    def full_text(self) -> str:
        for_hook = f"{self.hook} " if self.hook else ""
        return clean_text(f"{for_hook}{self.body} {self.closing}")

    @property
    def word_count(self) -> int:
        return len(words_of(self.full_text))

    def as_dict(self) -> dict:
        return {
            "hook": self.hook,
            "body": self.body,
            "closing": self.closing,
            "full_text": self.full_text,
            "word_count": self.word_count,
            "sentences": [{"text": s.text, "keywords": s.keywords} for s in self.sentences],
            "topic": self.topic,
            "niche": self.niche,
            "source": self.source,
        }

    def visual_keywords(self) -> list[str]:
        """Ordered list of search keywords, one group per sentence (for footage)."""
        out: list[str] = []
        for sentence in self.sentences:
            for kw in sanitize_keywords(sentence.keywords, self.niche):
                if kw.lower() not in [o.lower() for o in out]:
                    out.append(kw)
        return sanitize_keywords(out or [], self.niche)


def _split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", clean_text(text))
    return [p.strip() for p in parts if p.strip()]


def _count(text: str) -> int:
    return len(words_of(text))


def sanitize_keywords(keywords: list[str], niche: str = "science") -> list[str]:
    """Drop stopwords/one-character tokens and keep only usable search phrases."""
    out: list[str] = []
    for raw in keywords:
        kw = clean_text(str(raw), 40).strip().lower()
        if not kw:
            continue
        if len(kw) < MIN_KEYWORD_LEN and " " not in kw:
            continue
        words = words_of(kw)
        if not words:
            continue
        if all(w in _STOP for w in words):
            continue
        if kw not in out:
            out.append(kw)
    if not out:
        out = list(GENERIC_VISUALS.get(niche, GENERIC_VISUALS["science"]))
    return out


def _trim_to_words(text: str, limit: int) -> str:
    words = text.split()
    if len(words) <= limit:
        return text
    return " ".join(words[:limit]).rstrip(",;:") + "."


def _enforce_length(script: Script, cfg: Config) -> Script:
    """Keep the spoken text inside the window for the active mode.

    facts: 26-46 words (10-15 s). story: 130-200 words (about 60 s).
    """
    min_words, max_words, _target = word_window(cfg)
    floor_body = max(12, int(min_words * 0.6))
    # trim the body first
    guard = 0
    while script.word_count > max_words and guard < 24:
        guard += 1
        body_words = script.body.split()
        if len(body_words) <= floor_body:
            break
        drop = min(max(6, (max_words // 10)), len(body_words) - floor_body)
        script.body = " ".join(body_words[:-drop]).rstrip(",;:") + "."
    # pad if too short
    guard = 0
    while script.word_count < min_words and guard < 12:
        guard += 1
        if not script.hook:
            script.hook = random.choice(HOOKS["friendly"])
        elif not script.closing:
            script.closing = random.choice(CLOSINGS["soft"])
        elif _count(script.body) < int(min_words * 0.7):
            bridge = random.choice([b for b in STORY_BRIDGES if b not in script.body] or STORY_BRIDGES)
            script.body = clean_text(f"{script.body} {bridge}")
        else:
            break
    return script


def _story_prompt(topic: Topic, cfg: Config, target: int) -> str:
    cta = cta_of(cfg)
    cta_rule = {
        "none": "closing: max 10 words, a payoff line only - NO call to action",
        "soft": "closing: max 10 words, a soft payoff line is fine, no hard selling",
        "follow": "closing: max 10 words, at most one light call to follow",
    }[cta]
    src_note = (
        f"\nSource (do not invent anything beyond this): {topic.source_name or 'given material'}"
        f" {topic.source_url}".rstrip()
    ) if topic.source_url else ""
    return (
        f"Niche: {topic.niche}\nTopic: {topic.topic}\nMaterial: {topic.fact}\nAngle: {topic.angle}"
        f"{src_note}\n\n"
        f"Write a spoken story script of {target - 15}-{target + 15} words TOTAL for a "
        "60 second vertical video. It must be a real story, not a list of facts:\n"
        "- hook: 6-12 words, opens a curiosity gap in the first 2 seconds\n"
        "- body: the story in 4-6 short sentences - setup, what actually happened, the surprising "
        "turn, and why it matters. Plain words, one idea per sentence.\n"
        f"- {cta_rule}\n"
        "Only use the material above. Never invent numbers, dates or names.\n"
        "Never use these words/phrases: in this video, subscribe, link in description, you won't "
        "believe, insane, mind-blowing, guys, literally, must watch, viral.\n\n"
        "Return JSON with keys: hook, body, closing, sentences (array of the body split into 4-6 "
        "pieces, each {\"text\": \"...\", \"keywords\": [2-3 English stock-footage search terms]})."
    )


def _offline_story(topic: Topic, cfg: Config | None = None) -> Script:
    """Story-shaped fallback built only from the verified material + neutral glue."""
    cfg = cfg or get_config()
    style = style_of(cfg)
    cta = cta_of(cfg)
    core = clean_text(topic.fact)
    if topic.angle:
        core = clean_text(f"{core} What makes it interesting is {topic.angle}.")
    parts = _split_sentences(core)
    hook = random.choice(HOOKS.get(style, HOOKS["friendly"]))
    if parts and len(parts[0].split()) <= 12:
        hook = parts[0] if len(hook.split()) >= 4 else hook
    body_parts = parts[:]
    # keep the offline story in the same shape as the LLM one: glue between facts
    enriched: list[str] = []
    for i, part in enumerate(body_parts):
        enriched.append(part)
        if i < len(body_parts) - 1:
            enriched.append(random.choice(STORY_BRIDGES))
    body = clean_text(" ".join(enriched)) or core
    sentences = [Sentence(text=t, keywords=[]) for t in _split_sentences(body)] or [Sentence(text=body)]
    probe = sanitize_keywords(list(topic.keywords) + list(GENERIC_VISUALS.get(topic.niche, [])), topic.niche)
    for i, sentence in enumerate(sentences):
        pick = [probe[i % len(probe)]]
        if len(probe) > 1:
            pick.append(probe[(i + 1) % len(probe)])
        sentence.keywords = pick
    return Script(
        hook=hook,
        body=body,
        closing=random.choice(STORY_CLOSERS.get(cta, STORY_CLOSERS["soft"])),
        sentences=sentences,
        topic=topic.topic,
        niche=topic.niche,
        source="offline-story-template",
    )


def _offline_script(topic: Topic, cfg: Config | None = None) -> Script:
    body = clean_text(topic.fact)
    if len(body.split()) < 20 and topic.angle:
        body = clean_text(f"{body} Think about what that means for {topic.angle}.")
    style = style_of(cfg) if cfg else "friendly"
    hook = random.choice(HOOKS.get(style, HOOKS["friendly"]))
    if topic.angle and len(hook.split()) < 5:
        candidate = f"{hook} {topic.angle.capitalize()}."
        if len(candidate) <= 34:  # keep the hook short; long ones get trimmed awkwardly
            hook = candidate
    sentences = [Sentence(text=t, keywords=[]) for t in _split_sentences(body)] or [Sentence(text=body)]
    probe = sanitize_keywords(list(topic.keywords) + list(GENERIC_VISUALS.get(topic.niche, [])), topic.niche)
    for i, sentence in enumerate(sentences):
        pick = [probe[i % len(probe)]]
        if len(probe) > 1:
            pick.append(probe[(i + 1) % len(probe)])
        sentence.keywords = pick
    cta = cta_of(cfg) if cfg else "soft"
    return Script(
        hook=hook,
        body=body,
        closing=random.choice(CLOSINGS.get(cta, CLOSINGS["soft"])),
        sentences=sentences,
        topic=topic.topic,
        niche=topic.niche,
        source="offline-template",
    )


async def write_script(topic: Topic, llm: LLM | None = None, cfg: Config | None = None) -> Script:
    cfg = cfg or get_config()
    llm = llm or LLM(cfg)
    _min_words, _max_words, target = word_window(cfg)
    story_mode = cfg.profile().name == "story"

    if llm.available and not cfg.test_mode:
        system = (
            "You write tight, spoken-word scripts for YouTube Shorts. Plain English only, no emojis, "
            "no hashtags, no clickbait lies, no statistics that are not in the given fact. "
            "The script must sound like a person sharing something interesting, never like an advert: "
            "no calls to action other than the one specified, no marketing filler, no exaggeration. "
            + STYLE_PROMPTS[style_of(cfg)]
        )
        cta = cta_of(cfg)
        cta_rule = {
            "none": "closing: max 8 words, a memorable payoff line only - NO call to action, no 'follow', no 'subscribe'",
            "soft": "closing: max 8 words, a soft payoff - a light 'now you know' style line is fine, no hard selling",
            "follow": "closing: max 8 words, a light call to follow (at most one, never 'smash subscribe')",
        }[cta]
        src_note = (
            f"\nSource (cite-worthy, do not invent beyond this): {topic.source_name or 'given fact'}"
            f" {topic.source_url}".rstrip()
        ) if topic.source_url else ""
        prompt = _story_prompt(topic, cfg, target) if story_mode else (
            f"Niche: {topic.niche}\nTopic: {topic.topic}\nFact: {topic.fact}\nAngle: {topic.angle}"
            f"{src_note}\n\n"
            "Write a spoken script of 30-40 words TOTAL for a 12 second vertical video.\n"
            "- hook: max 7 words, creates curiosity in the first 2 seconds, no question marks needed\n"
            "- body: 15-28 words, only the fact above, one idea per sentence\n"
            f"- {cta_rule}\n"
            "Never use these words/phrases: in this video, subscribe, link in description, you won't "
            "believe, insane, mind-blowing, guys, literally, must watch, viral.\n\n"
            "Return JSON with keys: hook, body, closing, sentences (array of the body split into 2-3 pieces, "
            "each {\"text\": \"...\", \"keywords\": [2-3 English stock-footage search terms, 1-3 words each]})."
        )
        for attempt in range(1, 3):
            try:
                data = await llm.json(prompt, system, max_tokens=800, temperature=0.85)
            except LLMError as exc:
                log.warning("script generation failed (%s) -> offline template", exc)
                break
            script = Script(
                hook=strip_ad_language(clean_text(str(data.get("hook") or ""), 70)),
                body=strip_ad_language(clean_text(str(data.get("body") or ""))),
                closing=strip_ad_language(clean_text(str(data.get("closing") or ""), 60)),
                sentences=[],
                topic=topic.topic,
                niche=topic.niche,
                source=llm.last_provider or "llm",
            )
            for item in data.get("sentences") or []:
                if isinstance(item, dict) and item.get("text"):
                    kws = [str(k).strip() for k in (item.get("keywords") or []) if str(k).strip()][:3]
                    script.sentences.append(Sentence(text=clean_text(str(item["text"])), keywords=kws))
            if not script.sentences:
                script.sentences = [Sentence(text=s) for s in _split_sentences(script.body)]
            for sentence in script.sentences:
                sentence.keywords = sanitize_keywords(sentence.keywords, topic.niche)
            if topic.keywords:
                # blend topic keywords in so footage always has something usable
                for i, kw in enumerate(sanitize_keywords(topic.keywords, topic.niche)[:3]):
                    script.sentences[i % len(script.sentences)].keywords.append(kw)
            script = _enforce_length(script, cfg)
            if _min_words <= script.word_count <= _max_words:
                log.info("script ready (%d words, %s mode=%s)", script.word_count, script.source,
                         cfg.profile().name)
                return script
            log.info("script length %d outside window %d-%d, retrying (%d/2)",
                     script.word_count, _min_words, _max_words, attempt)

    fallback = _offline_story(topic, cfg) if story_mode else _offline_script(topic, cfg)
    script = _enforce_length(fallback, cfg)
    log.info("script ready from offline %s template (%d words)", "story" if story_mode else "fact",
             script.word_count)
    return script


def rescue_script(script: Script, cfg: Config | None = None) -> Script:
    """Used when the rendered voiceover turns out too long: tighten and retry."""
    cfg = cfg or get_config()
    min_words, _max_words, _target = word_window(cfg)
    floor = max(14, int(min_words * 0.6))
    words = script.body.split()
    if len(words) > floor:
        drop = max(6, int(len(words) * 0.12))
        script.body = " ".join(words[: max(floor, len(words) - drop)]).rstrip(",;:") + "."
    if script.closing:
        script.closing = _trim_to_words(script.closing, 5)
    return _enforce_length(script, cfg)
