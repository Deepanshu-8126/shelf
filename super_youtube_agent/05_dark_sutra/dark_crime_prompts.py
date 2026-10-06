"""
Dark Crime & Mystery AI Visual Prompts (OpenReels / Lemmino / Netflix Tier).
Curated negative prompts, lighting descriptors, and true crime scene archetypes.
"""
from __future__ import annotations
import random

PROMPTS: dict[str, str] = {
    "crime_scene": (
        "Dark crime scene at night, yellow police tape, numbered evidence markers, "
        "flashlight beams cutting through thick fog, rain wet asphalt, "
        "cinematic documentary photography, moody cold blue tones, "
        "shallow depth of field, 35mm film grain, 4K documentary"
    ),
    "interrogation": (
        "Dim interrogation room, single overhead hanging tungsten lamp, "
        "shadowy detective figure behind metal table, cigarette smoke in light beam, "
        "true crime documentary style, noir aesthetic, high contrast, dramatic shadows"
    ),
    "classified_files": (
        "Stack of declassified secret government dossier documents on dark metal desk, "
        "black redacted marker text, red TOP SECRET rubber stamps, vintage typewriter font, "
        "yellowing archival paper, overhead dramatic spotlight, true crime investigative photography"
    ),
    "mystery_location": (
        "Eerie abandoned mansion in dense foggy forest, broken gothic windows, "
        "subtle moonlight illumination, overgrown wild vegetation, cold oppressive atmosphere, "
        "cinematic wide angle shot, true crime documentary aesthetic, fine film grain"
    ),
    "forensic": (
        "Forensic crime investigator examining microscopic evidence under purple UV light, "
        "latex gloved hands holding tweezers, dark laboratory background, eerie fluorescent glow, "
        "documentary macro close-up, shallow depth of field, intense forensic tension"
    ),
    "newspaper": (
        "Old torn newspaper clipping on dark weathered wooden table, "
        "bold headline reporting mysterious disappearance, aged sepia paper, "
        "dramatic side rim lighting, shallow focus, 35mm archival noir look"
    ),
    "prison": (
        "Dark maximum security prison corridor, cold concrete walls and steel bars, "
        "single flickering fluorescent light, long creeping shadows, solitary confinement, "
        "cinematic wide angle, cold desaturated blue grade, gritty documentary feel"
    ),
    "map_investigation": (
        "Vintage city wall map with taut red strings connecting crime scene locations, "
        "pinned black and white suspect photos, dark detective office, "
        "warm desk lamp glow amidst dark shadows, investigative evidence board"
    ),
}

CRIME_PROMPTS: list[str] = list(PROMPTS.values())

NEGATIVE_PROMPT: str = (
    "bright, colorful, happy, cartoon, anime, 3d render, low quality, "
    "blurry, watermark, text overlay, oversaturated, generic stock"
)

PEXELS_QUERIES: dict[str, list[str]] = {
    "crime_scene": ["crime scene police", "police tape night", "night city police lights", "dark evidence"],
    "interrogation": ["interrogation room shadow", "detective thinking dark", "shadowy man desk"],
    "classified_files": ["old document archive", "typewriter paper dark", "vintage confidential files"],
    "mystery_location": ["abandoned house fog", "creepy forest night", "dark hallway mystery"],
    "forensic": ["forensic laboratory", "microscope dark lab", "scientist evidence analysis"],
    "newspaper": ["old newspaper headline", "vintage paper desk", "archival newspaper clippings"],
    "prison": ["prison bars shadow", "dark corridor prison", "abandoned cell block"],
    "map_investigation": ["map pins evidence", "detective board mystery", "compass old map dark"],
}


def get_visual_prompt(theme: str = "crime_scene", topic: str = "") -> dict[str, str]:
    """Returns a rich prompt and matching stock search terms for any crime beat."""
    base_theme = theme if theme in PROMPTS else random.choice(list(PROMPTS.keys()))
    prompt_text = PROMPTS[base_theme]
    if topic:
        prompt_text = f"{prompt_text}, related to {topic} investigation"
    
    stock_terms = PEXELS_QUERIES.get(base_theme, ["dark mystery investigation", "crime scene night"])
    return {
        "theme": base_theme,
        "sd_prompt": prompt_text,
        "negative_prompt": NEGATIVE_PROMPT,
        "stock_query": random.choice(stock_terms),
    }
