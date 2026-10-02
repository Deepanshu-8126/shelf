"""Topic engine: produce a unique, accurate, non-controversial fact per run.

Flow: LLM (Gemini/Groq) -> verification pass -> dedupe against SQLite history.
No API key? The built-in offline fact bank keeps the pipeline alive (useful for
tests / demo renders); every bank entry is a well-established, checkable fact.
"""
from __future__ import annotations

import random
import re
from dataclasses import dataclass, field

from . import db
from .config import Config, NICHES, get_config
from .llm import LLM, LLMError
from .utils import clean_text, is_similar, module_logger, slugify

log = module_logger("topic_engine")

# ---------------------------------------------------------------------------
# Offline fact bank - used when no LLM key is configured and as an emergency
# fallback. All entries are textbook-level facts (safe, verifiable, evergreen).
# ---------------------------------------------------------------------------
FACT_BANK: dict[str, list[dict[str, str]]] = {
    "space": [
        {"topic": "Venus spins backwards",
         "fact": "Venus rotates in the opposite direction to almost every other planet in the Solar System, "
                 "and one Venusian day is longer than its year.",
         "angle": "a day longer than a year"},
        {"topic": "Moon drifting away",
         "fact": "The Moon moves about 3.8 centimetres farther from Earth every year, measured by laser "
                 "reflectors left by Apollo astronauts.",
         "angle": "the Moon is leaving us"},
        {"topic": "Neutron star density",
         "fact": "A teaspoon of neutron star material would weigh roughly as much as Mount Everest, because "
                 "a star's worth of matter is squeezed into a city-sized sphere.",
         "angle": "a teaspoon heavier than a mountain"},
        {"topic": "Space metals weld themselves",
         "fact": "In a vacuum, two clean pieces of the same metal fuse together on contact, a phenomenon "
                 "called cold welding.",
         "angle": "metal welds itself in space"},
        {"topic": "Sunlight takes 8 minutes",
         "fact": "Sunlight needs about 8 minutes 20 seconds to reach Earth, but the energy inside the Sun may "
                 "have taken over 100,000 years to escape its core.",
         "angle": "the 100,000 year journey of sunlight"},
        {"topic": "Olympus Mons is huge",
         "fact": "Mars hosts Olympus Mons, the tallest volcano in the Solar System, about two and a half times "
                 "the height of Mount Everest.",
         "angle": "the tallest volcano is not on Earth"},
        {"topic": "A day on Mercury",
         "fact": "Mercury spins so slowly that a single solar day there lasts about 176 Earth days.",
         "angle": "176 days of daylight"},
        {"topic": "Black Holes stop time",
         "fact": "Near the event horizon of a black hole, gravity is so extreme that time dilates until it appears completely frozen to an outside observer.",
         "angle": "time stops inside a black hole"},
        {"topic": "Spaghettification",
         "fact": "Falling into a stellar black hole stretches your body into a thin string of atoms before you reach the singularity, a real physics process called spaghettification.",
         "angle": "gravity stretches you into noodles"},
        {"topic": "Black hole TON 618",
         "fact": "TON 618 is an ultramassive black hole with the mass of 66 billion Suns, so gigantic that eleven of our solar systems could sit inside it side by side.",
         "angle": "a monster 66 billion times heavier than the Sun"},
    ],
    "psychology": [
        {"topic": "Spacing effect",
         "fact": "Studying the same material across several short sessions produces far stronger long-term "
                 "memory than one long cramming session; psychologists call it the spacing effect.",
         "angle": "cramming barely works"},
        {"topic": "Zeigarnik effect",
         "fact": "People remember interrupted or unfinished tasks much better than completed ones, known as "
                 "the Zeigarnik effect.",
         "angle": "unfinished tasks stick in your head"},
        {"topic": "Dunning-Kruger effect",
         "fact": "People with the least skill in a task often rate their ability highest, because the skills "
                 "needed to perform well are the same ones needed to judge performance.",
         "angle": "why beginners feel overconfident"},
        {"topic": "Testing effect",
         "fact": "Actively recalling information strengthens memory more than re-reading it, an effect so "
                 "reliable that it is called the testing effect.",
         "angle": "quizzing yourself beats re-reading"},
        {"topic": "Sleep and memory",
         "fact": "During deep sleep the brain replays recently learned patterns, helping to convert fragile "
                 "short-term memories into lasting ones.",
         "angle": "sleep is when you save your memories"},
        {"topic": "Facial feedback",
         "fact": "Holding a pen in your teeth, which forces a smile shape, makes cartoons feel funnier in "
                 "controlled experiments, evidence for the facial feedback hypothesis.",
         "angle": "your face can change your mood"},
    ],
    "history": [
        {"topic": "Oxford is older than the Aztec Empire",
         "fact": "Teaching at Oxford began in the late 11th century, more than 300 years before the Aztec "
                 "capital Tenochtitlan was founded in 1325.",
         "angle": "a university older than an empire"},
        {"topic": "The shortest war",
         "fact": "The Anglo-Zanzibar War of 1896 lasted roughly 38 minutes, making it the shortest recorded "
                 "war in history.",
         "angle": "a war shorter than a TV episode"},
        {"topic": "Cleopatra lived closer to the Moon landing",
         "fact": "Cleopatra lived closer in time to the first Moon landing than to the building of the Great "
                 "Pyramid of Giza.",
         "angle": "history is nearer than it feels"},
        {"topic": "Ada Lovelace's first program",
         "fact": "Ada Lovelace published an algorithm for Charles Babbage's Analytical Engine in 1843, a "
                 "century before the first electronic computers were built.",
         "angle": "code written 100 years early"},
        {"topic": "The fax machine predates the telephone",
         "fact": "The first facsimile machine was patented in 1843, more than 30 years before Alexander Graham "
                 "Bell patented the telephone in 1876.",
         "angle": "the fax came before the phone"},
    ],
    "science": [
        {"topic": "Honey never spoils",
         "fact": "Sealed honey found in Egyptian tombs thousands of years old was still edible, thanks to its "
                 "low water content and natural acidity.",
         "angle": "the food that never expires"},
        {"topic": "Human body element count",
         "fact": "Around 60 percent of an adult human body is water, and oxygen alone makes up about 65 "
                 "percent of body mass by weight.",
         "angle": "you are mostly oxygen"},
        {"topic": "Bacteria outnumber human cells",
         "fact": "The human body hosts roughly as many bacterial cells as human cells, and most of them live "
                 "in the gut.",
         "angle": "you are a walking ecosystem"},
        {"topic": "Glass is a slow-moving liquid? No.",
         "fact": "Glass is a solid, not a slow-flowing liquid; the thicker panes in old windows are a result "
                 "of how they were made, not sagging glass.",
         "angle": "a myth about glass debunked"},
        {"topic": "Lightning heats the air",
         "fact": "A lightning bolt heats the air around it to about 30,000 kelvin, roughly five times hotter "
                 "than the surface of the Sun.",
         "angle": "5 times hotter than the Sun"},
        {"topic": "Water expands when it freezes",
         "fact": "Water is unusual because it becomes less dense as it freezes, which is why ice floats and "
                 "why fish can survive under frozen lakes.",
         "angle": "why ice floats"},
    ],
    "animals": [
        {"topic": "Tardigrades survive vacuum",
         "fact": "Tardigrades can survive the vacuum of space, extreme radiation and decades of drought by "
                 "entering a dried-out state called tun.",
         "angle": "the animal that survives space"},
        {"topic": "Octopuses have three hearts",
         "fact": "An octopus has three hearts: two pump blood through the gills and one through the body, and "
                 "the main one stops when the octopus swims.",
         "angle": "why octopuses prefer crawling"},
        {"topic": "Mantis shrimp punch",
         "fact": "A mantis shrimp strikes with the speed of a bullet, and the collapsing bubble it creates "
                 "releases a second shock wave that can stun prey.",
         "angle": "a punch faster than a bullet"},
        {"topic": "Elephants hear with their feet",
         "fact": "Elephants detect low-frequency rumbles through their feet, letting herds communicate over "
                 "several kilometres.",
         "angle": "talking through the ground"},
        {"topic": "Ants lift many times their weight",
         "fact": "Many ant species can carry 10 to 50 times their own body weight, and collectively ants move "
                 "more soil than earthworms in many ecosystems.",
         "angle": "the strongest lifters on Earth"},
        {"topic": "Immortal jellyfish",
         "fact": "The jellyfish Turritopsis dohrnii can revert to its juvenile polyp stage after reaching "
                 "adulthood, effectively restarting its life cycle.",
         "angle": "the jellyfish that starts over"},
    ],
}


# Visual search keywords per offline-bank topic. Keeping these explicit is what makes
# the footage actually match the fact (Pexels/Pixabay/Wikimedia searches).
TOPIC_KEYWORDS: dict[str, list[str]] = {
    "Venus spins backwards": ["planet venus", "solar system animation", "space animation"],
    "Moon drifting away": ["moon surface", "earth from space", "night sky timelapse"],
    "Neutron star density": ["neutron star animation", "galaxy stars", "deep space nebula"],
    "Space metals weld themselves": ["space station", "metal laboratory", "satellite orbit"],
    "Sunlight takes 8 minutes": ["sun surface", "sunrise timelapse", "solar flare"],
    "Olympus Mons is huge": ["mars surface", "volcano aerial", "red desert aerial"],
    "A day on Mercury": ["mercury planet", "sunrise timelapse", "space animation"],
    "Spacing effect": ["student studying", "notebook writing", "library books"],
    "Zeigarnik effect": ["person thinking", "sticky notes", "office desk"],
    "Dunning-Kruger effect": ["crowd of people", "chess thinking", "abstract brain"],
    "Testing effect": ["flashcards study", "student writing", "classroom"],
    "Sleep and memory": ["person sleeping", "night bedroom", "sleeping peacefully"],
    "Facial feedback": ["person smiling", "portrait face closeup", "mirror face"],
    "Oxford is older than the Aztec Empire": ["oxford university", "ancient stone building", "aztec ruins"],
    "The shortest war": ["old warship", "historical archive", "vintage map"],
    "Cleopatra lived closer to the Moon landing": ["egyptian pyramids", "apollo moon landing", "ancient egypt"],
    "Ada Lovelace's first program": ["vintage mechanical gears", "old book writing", "antique machine"],
    "The fax machine predates the telephone": ["vintage office machine", "old typewriter", "antique telephone"],
    "Honey never spoils": ["honey dripping", "honeycomb macro", "egyptian tomb"],
    "Human body element count": ["water splash macro", "human body abstract", "molecules animation"],
    "Bacteria outnumber human cells": ["microscope bacteria", "laboratory science", "cell animation"],
    "Glass is a slow-moving liquid? No.": ["glass window light", "glass blowing", "stained glass"],
    "Lightning heats the air": ["lightning storm", "thunderstorm clouds", "night storm"],
    "Water expands when it freezes": ["ice freezing macro", "frozen lake", "water surface macro"],
    "Tardigrades survive vacuum": ["microscope macro", "space vacuum", "microscopic world"],
    "Octopuses have three hearts": ["octopus underwater", "coral reef", "ocean underwater"],
    "Mantis shrimp punch": ["mantis shrimp", "coral reef macro", "underwater closeup"],
    "Elephants hear with their feet": ["elephant walking", "savanna africa", "elephant herd"],
    "Ants lift many times their weight": ["ants macro", "ant colony", "insect closeup"],
    "Immortal jellyfish": ["jellyfish swimming", "deep ocean", "underwater jellyfish"],
}


@dataclass
class Topic:
    niche: str
    topic: str
    fact: str
    angle: str = ""
    keywords: list[str] = field(default_factory=list)
    verified: bool = False
    source: str = "llm"
    source_url: str = ""      # citable origin (Wikipedia article, NASA page, ...)
    source_name: str = ""     # "Wikipedia" / "NASA" / "Google Trends + Wikipedia"
    trend_kind: str = ""      # mostread | onthisday | google | random | "" (evergreen)

    @property
    def fingerprint(self) -> str:
        return slugify(self.topic, 80)


def _bank_topics(niche: str) -> list[dict[str, str]]:
    pool = FACT_BANK.get(niche) or FACT_BANK["space"]
    return pool


def _is_duplicate(topic: Topic, history: list[dict]) -> bool:
    for row in history:
        if row.get("fingerprint") == topic.fingerprint:
            return True
        if row.get("topic") and is_similar(row["topic"], topic.topic, 0.5):
            return True
        if row.get("fact") and is_similar(row["fact"], topic.fact, 0.72):
            return True
    return False


async def _verify(topic: Topic, llm: LLM) -> bool:
    """Second LLM pass: is this fact accurate, current and safe to publish?"""
    prompt = (
        "You are a fact-checker for a short-form video channel.\n"
        f"Claim to check: {topic.fact}\n\n"
        'Return JSON: {"accurate": true|false, "controversial": true|false, "confidence": 0-1, '
        '"reason": "short explanation"}\n'
        "Mark accurate=false if the claim is wrong, outdated, exaggerated, or depends on disputed sources. "
        "Mark controversial=true if it touches politics, religion, medical advice or fringe claims."
    )
    try:
        data = await llm.json(prompt, "You verify facts strictly and conservatively.", max_tokens=300, temperature=0.2)
    except LLMError as exc:
        log.warning("verification skipped (%s)", exc)
        return False
    ok = bool(data.get("accurate")) and not bool(data.get("controversial"))
    if not ok:
        log.info("topic rejected by verifier: %s | %s", data.get("reason"), topic.topic)
    return ok


def find_bank_topic(query: str) -> tuple[str, dict[str, str]] | None:
    """Fuzzy-match a topic name against the offline fact bank (for --topic overrides)."""
    q = (query or "").strip().lower()
    if not q:
        return None
    for niche, entries in FACT_BANK.items():
        for entry in entries:
            name = entry["topic"].lower()
            if q == name or q in name or name in q:
                return niche, entry
    return None


def topic_from_bank(entry: dict[str, str], niche: str) -> Topic:
    return Topic(
        niche=niche,
        topic=entry["topic"],
        fact=entry["fact"],
        angle=entry.get("angle", ""),
        keywords=TOPIC_KEYWORDS.get(entry["topic"], [f"{niche} facts", niche, "abstract motion"]),
        verified=True,
        source="offline-bank(forced)",
    )


def topic_from_seed(seed, niche: str, long: bool = False) -> Topic:
    """Offline: the Wikipedia / source extract itself becomes the fact (already citable).

    ``long`` (story mode) keeps four sentences of the extract instead of two, so a
    60-second narration has enough verified material without inventing anything.
    """
    text = (seed.summary or "").strip()
    parts = re.split(r"(?<=[.!?])\s+", text)
    keep = 4 if long else 2
    fact = " ".join(parts[:keep]).strip() or text[:300]
    return Topic(
        niche=niche,
        topic=seed.title,
        fact=fact,
        angle="",
        keywords=seed.keywords(),
        verified=True,
        source=f"{seed.source}-{seed.kind}",
        source_url=seed.source_url,
        source_name="Wikipedia" if seed.source.startswith("wiki") else seed.source.title(),
        trend_kind=seed.kind,
    )


async def widen_material(topic: Topic, client, target_words: int = 110) -> Topic:
    """Give story mode enough verified material for a ~60 s narration.

    A feed excerpt is often 40-60 words, which cannot carry a 60-second story without
    padding it with filler. When the topic has a Wikipedia page we pull the full lead
    section (key-less REST call) and append the sentences that are not already there.
    Nothing is invented - the worst case is that the material stays as short as before.
    """
    have = len(topic.fact.split())
    if not topic.topic or have >= target_words or client is None:
        return topic
    added: list[str] = []
    existing = topic.fact.lower()
    for full_text in (False, True):          # lead section first, then the rest of the article
        if have + len(" ".join(added).split()) >= target_words:
            break
        try:
            found = await client.wikipedia_summary(topic.topic, full_text=full_text)
        except Exception as exc:  # noqa: BLE001
            log.warning("could not widen material for %r (full=%s): %s", topic.topic, full_text, exc)
            continue
        if not found or not found.summary:
            continue
        for sentence in re.split(r"(?<=[.!?])\s+", found.summary):
            sentence = sentence.strip()
            if not sentence:
                continue
            head = " ".join(sentence.lower().split()[:6])
            if head and head in existing:
                continue
            if any(sentence.lower()[:40] in a.lower()[:40] for a in added):
                continue
            added.append(sentence)
            if have + len(" ".join(added).split()) >= target_words:
                break
    if not added:
        return topic
    topic.fact = clean_text(f"{topic.fact} {' '.join(added)}")
    if found.source_url and not topic.source_url:
        topic.source_url = found.source_url
    log.info("story material widened to %d words for %s", len(topic.fact.split()), topic.topic)
    return topic


async def _grounded_topic(seed, niche: str, llm: LLM) -> Topic | None:
    """Ask the LLM for a fact that is *only* based on the provided extract."""
    system = (
        "You turn a cited encyclopaedia extract into one accurate short-video fact. "
        "Use ONLY the information in the extract - never add numbers, dates or claims that "
        "are not in it. No politics, no religion, no medical advice, no sensational wording."
    )
    prompt = (
        f"Niche: {niche}\n"
        f"Source title: {seed.title}\n"
        f"Source: {seed.source_name if hasattr(seed, 'source_name') else 'Wikipedia'}\n"
        f"Extract:\n\"\"\"{clean_text(seed.summary, 900)}\"\"\"\n\n"
        "Return JSON with keys:\n"
        "- topic: max 8 words, the subject\n"
        "- fact: 2-3 sentences (about 30 words) that a viewer would find surprising, using only the extract\n"
        "- angle: max 6 words, plain-English angle (no hype words like 'insane', 'shocking', 'you won't believe')\n"
        "- keywords: 4-6 short English stock-footage search terms (1-3 words each)"
    )
    try:
        data = await llm.json(prompt, system, max_tokens=700, temperature=0.7)
    except LLMError as exc:
        log.warning("grounded generation failed: %s", exc)
        return None
    fact = clean_text(str(data.get("fact") or ""))
    if len(fact.split()) < 8:
        return None
    return Topic(
        niche=niche,
        topic=clean_text(str(data.get("topic") or seed.title), 90),
        fact=fact,
        angle=clean_text(str(data.get("angle") or ""), 80),
        keywords=[str(k) for k in (data.get("keywords") or []) if str(k).strip()][:6] or seed.keywords(),
        verified=True,
        source=f"{llm.last_provider}-grounded",
        source_url=seed.source_url,
        source_name="Wikipedia" if seed.source.startswith("wiki") else seed.source.title(),
        trend_kind=seed.kind,
    )


async def generate_topic(
    niche: str | None = None,
    llm: LLM | None = None,
    cfg: Config | None = None,
    allow_repeat: bool = False,
    forced_topic: str | None = None,
    seed=None,
    client=None,
) -> Topic:
    cfg = cfg or get_config()
    llm = llm or LLM(cfg)
    niche = (niche or cfg.niche or "space").lower()
    if niche not in NICHES:
        log.warning("unknown niche %r -> using space", niche)
        niche = "space"

    # 1) a freshly fetched trend / source seed is the highest-value subject
    if seed is not None:
        history0 = db.recent_topics(60)
        topic: Topic | None = None
        if llm.available and not cfg.test_mode:
            topic = await _grounded_topic(seed, niche, llm)
        if topic is None:
            topic = topic_from_seed(seed, niche, long=cfg.profile().name == "story")
        if _is_duplicate(topic, history0) and not allow_repeat:
            log.info("trend seed duplicates an old topic (%s) -> falling through", topic.topic)
        else:
            log.info("trend topic [%s/%s] %s", seed.source, seed.kind, topic.topic)
            _remember(topic)
            return topic

    if forced_topic:
        hit = find_bank_topic(forced_topic)
        if hit:
            bank_niche, entry = hit
            topic = topic_from_bank(entry, bank_niche)
            log.info("using forced offline-bank topic: %s", topic.topic)
            _remember(topic)
            return topic
        # 2) key-less Wikipedia lookup: any subject name works without an LLM key
        if client is not None:
            try:
                found = await client.wikipedia_summary(forced_topic)
            except Exception as exc:  # noqa: BLE001 - a lookup failure is not fatal
                log.warning("wikipedia lookup for %r failed: %s", forced_topic, exc)
                found = None
            if found and len(found.summary.split()) >= 20:
                topic = topic_from_seed(found, niche or found.niche or "science",
                                        long=cfg.profile().name == "story")
                log.info("forced topic from Wikipedia: %s (%d words of material)",
                         topic.topic, len(topic.fact.split()))
                _remember(topic)
                return topic
        log.info("forced topic %r is not in the offline bank - passing it to the LLM", forced_topic)

    history = db.recent_topics(120)
    used = [t["topic"] for t in history]
    avoid = ", ".join(used[:40]) if used else "none yet"

    if llm.available and not cfg.test_mode:
        system = (
            "You are a viral YouTube Shorts producer. Generate intense, high-stakes hypothetical scenarios or "
            "mind-bending science facts (e.g., 'What if you fell into a black hole?', 'What if a Megalodon was still alive?', "
            "'What if you were swallowed by a whale?'). Keep it factual but frame it as an extreme 'What if' or survival scenario. "
            "Never touch politics, religion, or medical advice."
        )
        story_mode = cfg.profile().name == "story"
        for attempt in range(1, 4):
            length_desc = "60 second storytelling narrative vertical video (with historical mystery, scientific paradox, or shocking consequence)" if story_mode else "12 second vertical video"
            fact_desc = "3-5 detailed sentences explaining the phenomenon, how it works, and why it is mind-bending" if story_mode else "2-3 sentences, plain English, no emojis"
            prompt = (
                f"Niche: {niche}.\n"
                + (f"Use this exact subject if it is accurate: {forced_topic}\n" if forced_topic else "")
                + f"Generate ONE surprising, verifiable subject suitable for a {length_desc}.\n"
                f"Do NOT reuse anything similar to these already used topics: {avoid}\n\n"
                f"Return JSON with keys: topic (max 8 words, phrasing it as a 'What If' question if possible), fact ({fact_desc}), "
                "angle (max 6 words curiosity hook angle), keywords (4-6 short English search keywords for "
                "matching stock footage. Make these HIGHLY visual, e.g., if it's about a dolphin, use 'dolphin swimming underwater')."
            )
            try:
                data = await llm.json(prompt, system, max_tokens=850, temperature=0.95)
            except LLMError as exc:
                log.warning("topic generation failed (%s) attempt %d/3", exc, attempt)
                continue
            candidate = Topic(
                niche=niche,
                topic=str(data.get("topic") or "").strip()[:90],
                fact=str(data.get("fact") or "").strip(),
                angle=str(data.get("angle") or "").strip()[:80],
                keywords=[str(k).strip() for k in (data.get("keywords") or []) if str(k).strip()][:6],
                source=llm.last_provider or "llm",
            )
            if len(candidate.fact.split()) < 8 or len(candidate.topic.split()) < 2:
                log.info("candidate too thin, retrying (%d/3)", attempt)
                continue
            if _is_duplicate(candidate, history) and not allow_repeat:
                log.info("duplicate topic rejected: %s", candidate.topic)
                continue
            if await _verify(candidate, llm):
                candidate.verified = True
                _remember(candidate)
                return candidate
            log.info("candidate failed verification (%d/3)", attempt)

    # ---------------- offline fallback ----------------
    pool = [t for t in _bank_topics(niche) if not _is_duplicate(
        Topic(niche=niche, topic=t["topic"], fact=t["fact"]), history
    )]
    if not pool:
        pool = _bank_topics(niche)
    pick = random.choice(pool)
    topic = Topic(
        niche=niche,
        topic=pick["topic"],
        fact=pick["fact"],
        angle=pick.get("angle", ""),
        keywords=TOPIC_KEYWORDS.get(pick["topic"], [f"{niche} facts", niche, "abstract motion"]),
        verified=True,
        source="offline-bank",
    )
    _remember(topic)
    return topic


def _remember(topic: Topic) -> None:
    try:
        db.add_topic(topic.niche, topic.topic, topic.fact, topic.fingerprint, topic.verified, topic.source,
                     source_url=topic.source_url)
    except Exception as exc:  # noqa: BLE001
        log.warning("could not store topic: %s", exc)
