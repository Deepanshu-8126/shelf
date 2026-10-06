"""
=============================================================================
SMART CAPTION DECISION ROUTER (PIPELINE DECISION ENGINE)
=============================================================================
Dynamically selects the highest-retention visual caption style based on:
1. Video Niche / Category (Space, Tech, Finance, Crime, Viral, Action)
2. Script topic keywords and emotional sentiment
3. Optional user override from CLI or .env (e.g. CAPTION_STYLE=mrbeast_fire)
=============================================================================
"""
from __future__ import annotations

import logging
from typing import Optional

log = logging.getLogger("factshorts.smart_caption_router")


def resolve_caption_style(
    topic: str = "",
    niche: str = "",
    script_text: str = "",
    user_override: Optional[str] = None
) -> str:
    """
    Intelligently determines the best caption style for maximum viewer retention.
    
    Returns one of:
      - 'cyber_glow'   (#00E5FF) -> Space, Astronomy, AI, Tech, Sci-Fi
      - 'mrbeast_fire'  (#FF3300) -> Action, Danger, Catastrophe, Extreme Shock
      - 'hormozi_yellow' (#FFE600) -> Business, Finance, Wealth, High-Authority
      - 'vox_minimal'   (#38BDF8) -> Crime, Mystery, Geopolitics, Serious Dossier
      - 'tiktok_green'  (#00FF88) -> General Viral Facts, Psychology, Trivia
    """
    if user_override and user_override.strip() and user_override.lower() != "auto":
        style_key = user_override.strip().lower()
        log.info("Caption style forced via override: %s", style_key)
        return style_key

    content = f"{topic} {niche} {script_text[:200]}".lower()

    # Helper for whole-word or substring match
    def has_kw(keywords: list[str]) -> bool:
        import re
        for kw in keywords:
            if len(kw) <= 3:
                # Use word boundary for short keywords like 'ai', 'war', 'spy', 'cia', 'die'
                if re.search(rf"\b{re.escape(kw)}\b", content):
                    return True
            elif kw in content:
                return True
        return False

    # 1. Space / Astronomy / AI / Future Tech -> Cyber Glow (Electric Cyan #00E5FF)
    space_tech_signals = [
        "space", "mercury", "planet", "galaxy", "nasa", "isro", "universe",
        "asteroid", "neutron", "star", "solar", "black hole", "telescope",
        "ai", "robot", "tech", "quantum", "alien", "cosmic", "mars", "moon"
    ]
    if has_kw(space_tech_signals):
        log.info("Smart Caption Router: Selected 'cyber_glow' for space/tech theme.")
        return "cyber_glow"

    # 2. Danger / Shock / Catastrophe / Survival -> MrBeast Fire (Fiery Orange #FF3300)
    urgency_danger_signals = [
        "danger", "deadly", "die", "kill", "shocking", "monster", "extinction",
        "explosion", "tsunami", "volcano", "survive", "survival", "horror",
        "attack", "banned", "illegal", "lethal", "terrifying", "warning"
    ]
    if has_kw(urgency_danger_signals):
        log.info("Smart Caption Router: Selected 'mrbeast_fire' for high-urgency theme.")
        return "mrbeast_fire"

    # 3. Wealth / Money / Business / Success -> Hormozi Gold (Cyber Yellow #FFE600)
    business_wealth_signals = [
        "money", "billionaire", "millionaire", "rich", "wealth", "business",
        "dollar", "crypto", "bitcoin", "invest", "stock", "company", "ceo",
        "income", "profit", "luxury", "success", "expensive"
    ]
    if has_kw(business_wealth_signals):
        log.info("Smart Caption Router: Selected 'hormozi_yellow' for business/wealth theme.")
        return "hormozi_yellow"

    # 4. Crime / Mystery / Geopolitics / Secret Dossiers -> Vox Clean (Sky Blue #38BDF8)
    documentary_signals = [
        "secret", "mystery", "crime", "investigation", "dossier", "cia",
        "fbi", "kgb", "declassified", "history", "ancient", "conspiracy",
        "government", "military", "war", "spy", "assassin"
    ]
    if has_kw(documentary_signals):
        log.info("Smart Caption Router: Selected 'vox_minimal' for documentary theme.")
        return "vox_minimal"

    # 5. Dynamic Fallback: Alternates smoothly among top viral styles
    import random
    picked = random.choice(["tiktok_green", "cyber_glow", "hormozi_yellow"])
    log.info("Smart Caption Router: Selected dynamic variety '%s'", picked)
    return picked
