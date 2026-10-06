"""Jake Schincariol 21 Viral Hook Formulas & Automated Hook Scorer Engine.

Infuses proven YouTube retention psychology into automated Shorts production.
"""
from __future__ import annotations

import re
from typing import Any

HOOK_FORMULAS = [
    {
        "id": "curiosity_gap_paradox",
        "name": "Curiosity Gap Paradox",
        "example": "A day on Mercury is twice as long as its entire year.",
        "rule": "State two contradictory facts that seem physically impossible together.",
    },
    {
        "id": "negative_consequence",
        "name": "Negative Consequence",
        "example": "If two clean metals touch in space, they fuse permanently into one.",
        "rule": "Start with a simple action and an irreversible, shocking consequence.",
    },
    {
        "id": "scale_comparison",
        "name": "Extreme Scale Comparison",
        "example": "One teaspoon of a neutron star weighs more than Mount Everest.",
        "rule": "Compare a microscopic or household object with a planetary scale.",
    },
    {
        "id": "forbidden_truth",
        "name": "Forbidden / Classified Secret",
        "example": "The classified reason NASA never landed a probe on Venus's surface again.",
        "rule": "Frame a known phenomenon as a buried secret or untold reality.",
    },
    {
        "id": "immediate_in_media_res",
        "name": "Immediate In Media Res",
        "example": "Right now beneath Antarctica, an ancient ocean is quietly boiling.",
        "rule": "Drop the viewer directly into a dramatic present-tense event happening now.",
    },
    {
        "id": "sensory_impossibility",
        "name": "Sensory Impossibility",
        "example": "There is a planet where it rains liquid glass sideways at 4,000 mph.",
        "rule": "Describe an environment that breaks all human sensory expectations.",
    },
    {
        "id": "counter_intuitive_physics",
        "name": "Counter-Intuitive Physics",
        "example": "Hot water actually freezes faster than cold water, and physics cannot agree why.",
        "rule": "Highlight a common scientific law that appears completely broken.",
    },
    {
        "id": "time_displacement",
        "name": "Time Displacement Shock",
        "example": "Cleopatra lived closer in time to the iPhone than to the building of the Pyramids.",
        "rule": "Connect historical eras in a way that shatters chronological intuition.",
    },
    {
        "id": "hidden_danger",
        "name": "Hidden Micro Danger",
        "example": "The world's deadliest creature is smaller than your fingernail.",
        "rule": "Reveal an invisible or overlooked lethal threat.",
    },
    {
        "id": "anomaly_record",
        "name": "Record-Breaking Anomaly",
        "example": "Scientists detected a sound underwater so loud it traveled 3,000 miles.",
        "rule": "Anchor on an extreme physical measurement or recorded anomaly.",
    },
    {
        "id": "biological_glitch",
        "name": "Human Biological Glitch",
        "example": "Your brain deletes your own nose from your vision 24 hours a day.",
        "rule": "Expose an active subconscious trick or blindspot in the viewer's own body.",
    },
    {
        "id": "historical_mass_hysteria",
        "name": "Historical Mass Event",
        "example": "In 1518, an entire city danced uncontrollably until hundreds died.",
        "rule": "Cite an eerie historical mystery that documented records cannot explain.",
    },
    {
        "id": "unsolved_disappearance",
        "name": "Unsolved Vanishing",
        "example": "In 1971, a passenger vanished at 10,000 feet and was never found.",
        "rule": "State a real-world disappearance with an impossible escape route.",
    },
    {
        "id": "cosmic_extinction",
        "name": "Cosmic Extinction Threat",
        "example": "A rogue black hole could pass through our solar system without making a sound.",
        "rule": "Highlight a silent cosmic force that could erase Earth instantly.",
    },
    {
        "id": "micro_macro_inversion",
        "name": "Micro-Macro Inversion",
        "example": "There are more trees on Earth than stars in the entire Milky Way galaxy.",
        "rule": "Show how an Earth phenomenon dwarfs a cosmic number.",
    },
    {
        "id": "death_clock",
        "name": "The Resetting Death Clock",
        "example": "You are only 3 minutes away from dying—breathing just resets the clock.",
        "rule": "Reframe a routine survival reflex as a precarious countdown.",
    },
    {
        "id": "shock_origin",
        "name": "Shocking Origin Story",
        "example": "The chainsaw was originally invented by doctors for human childbirth.",
        "rule": "Reveal the terrifying original purpose of an everyday tool.",
    },
    {
        "id": "secret_organ",
        "name": "Newly Discovered Anatomy",
        "example": "Doctors just discovered a brand new organ hidden inside human skull bones.",
        "rule": "Expose a recent anatomical discovery inside our own bodies.",
    },
    {
        "id": "deep_ocean_alien",
        "name": "Alien Ocean Reality",
        "example": "We have clearer maps of Mars than of the floor of our own oceans.",
        "rule": "Compare ocean depths to extraterrestrial planets.",
    },
    {
        "id": "shock_equivalence",
        "name": "Heavy Weight Inversion",
        "example": "A single cumulus cloud weighs over one million pounds.",
        "rule": "Show the colossal invisible mass of something that appears weightless.",
    },
    {
        "id": "ultimate_physics_conundrum",
        "name": "Light Speed Time Freeze",
        "example": "At the speed of light, time completely stops for a traveling photon.",
        "rule": "Explain how relativity erases time for particles traveling across space.",
    },
]


BANNED_FLUFF_PATTERNS = [
    r"\bdid you know\b",
    r"\bin this video\b",
    r"\btoday we will\b",
    r"\bhave you ever wondered\b",
    r"\bhere is a fact\b",
    r"\bwelcome back\b",
    r"\blet's explore\b",
    r"\bcheck this out\b",
    r"\bwait until the end\b",
]

HIGH_CURIOSITY_WORDS = {
    "twice", "never", "only", "secret", "hidden", "instantly", "forever", "cannot",
    "impossible", "billion", "weighs", "stops", "boiling", "freezes", "vanished",
    "deadliest", "deletes", "erases", "mercury", "black hole", "neutron star",
    "fused", "liquid", "rains", "alien", "quietly", "underwater", "thousands",
}


def score_hook(hook: str) -> dict[str, Any]:
    """Score a hook string from 0 to 100 based on Jake Schincariol's retention metrics."""
    cleaned = hook.strip()
    words = cleaned.split()
    word_count = len(words)
    lower = cleaned.lower()

    score = 70.0
    penalties = []
    bonuses = []

    # 1. Fluff penalty: immediate -40 deduction
    for pat in BANNED_FLUFF_PATTERNS:
        if re.search(pat, lower):
            score -= 40.0
            penalties.append(f"Contains banned AI filler phrase: '{pat}'")

    # 2. Word count check: optimal Shorts hook is 6 to 14 words
    if 6 <= word_count <= 14:
        score += 15.0
        bonuses.append("Optimal punchy hook length (6-14 words)")
    elif word_count < 5:
        score -= 20.0
        penalties.append(f"Too short ({word_count} words) - insufficient intrigue")
    elif word_count > 18:
        score -= 25.0
        penalties.append(f"Too long ({word_count} words) - viewer will swipe away before finished")

    # 3. Curiosity keywords
    curiosity_hits = [w for w in HIGH_CURIOSITY_WORDS if w in lower]
    if curiosity_hits:
        bonus = min(20.0, len(curiosity_hits) * 6.0)
        score += bonus
        bonuses.append(f"High-retention vocabulary ({', '.join(curiosity_hits[:3])})")

    # 4. Check for concrete numerical anchor or physical noun
    has_number = bool(re.search(r"\b(?:\d+|twice|million|billion|half|zero|one|two)\b", lower))
    if has_number:
        score += 10.0
        bonuses.append("Concrete numerical/scale anchor present")

    # Bound score
    final_score = max(0.0, min(100.0, score))
    passed = final_score >= 80.0

    return {
        "hook": hook,
        "score": round(final_score, 1),
        "passed": passed,
        "bonuses": bonuses,
        "penalties": penalties,
    }


def format_hook_prompt_guide() -> str:
    """Format instructions for Gemini / DeepSeek-R1 prompt injection."""
    formulas_sample = "\n".join(
        f"- {f['name']}: e.g. '{f['example']}' ({f['rule']})"
        for f in HOOK_FORMULAS[:10]
    )
    return f"""JAKE SCHINCARIOL 21 VIRAL HOOK SYSTEM:
You MUST choose one of these proven retention archetypes for the first sentence:
{formulas_sample}

CRITICAL HOOK RULES:
1. First 2 seconds MUST stop the thumb from swiping.
2. ZERO filler words (BANNED: 'Did you know', 'In this video', 'Have you ever wondered', 'Here is a fact').
3. Length: Strictly 7 to 13 spoken words.
4. Must include at least one concrete physical noun or numerical anchor."""
