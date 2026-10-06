"""
Beat Director & Beats.json Generator (Cold Open Mystery Arc).
Structures every true crime short into a 4-beat narrative with frame-accurate cues.
"""
from __future__ import annotations

import json
from pathlib import Path
try:
    from .dark_crime_prompts import get_visual_prompt
except ImportError:
    from dark_crime_prompts import get_visual_prompt

BEAT_ARCS = {
    "cold_open_mystery": [
        {
            "beat_index": 1,
            "role": "hook_cold_open",
            "ken_burns": "slow_zoom_in",
            "sfx": "low_drone_hit",
            "theme": "mystery_location",
        },
        {
            "beat_index": 2,
            "role": "crime_scene_investigation",
            "ken_burns": "pan_right",
            "sfx": "police_siren_distant",
            "theme": "crime_scene",
        },
        {
            "beat_index": 3,
            "role": "unexplained_clue_twist",
            "ken_burns": "slow_zoom_out",
            "sfx": "paper_rustle",
            "theme": "classified_files",
        },
        {
            "beat_index": 4,
            "role": "chilling_cliffhanger",
            "ken_burns": "drift",
            "sfx": "heartbeat",
            "theme": "interrogation",
        },
    ]
}


def build_beats(
    topic: str = "Burari Deaths Case",
    custom_script: str | None = None,
    output_json: Path | str | None = None,
) -> dict:
    """Builds a structured beats.json for the topic."""
    default_text = {
        1: f"रात के सन्नाटे में, {topic} की वो डरावनी सच्चाई जिसने पूरे देश को हिला कर रख दिया।",
        2: "जब पुलिस पहली बार अंदर दाखिल हुई, तो कमरे का मंजर देखकर अनुभवी अफसर भी कांप उठे।",
        3: "जांच में मिले अजीब सुराग और डायरी के पन्ने, जो किसी रहस्यमयी अनुष्ठान की ओर इशारा कर रहे थे।",
        4: "लेकिन सबसे बड़ा सवाल आज भी वही है... क्या ये खुदकुशी थी, या किसी अनदेखी ताकत का साया?",
    }

    beats_list = []
    template_arc = BEAT_ARCS["cold_open_mystery"]

    for item in template_arc:
        idx = item["beat_index"]
        text_line = default_text.get(idx, f"रहस्यमयी घटना: {topic}")
        visual_info = get_visual_prompt(item["theme"], topic)

        beat_entry = {
            "id": idx,
            "role": item["role"],
            "text": text_line,
            "image_prompt": visual_info["sd_prompt"],
            "image_source": f"pexels:{visual_info['stock_query']}",
            "ken_burns": item["ken_burns"],
            "sfx": item["sfx"],
            "duration": 5.0,
        }
        beats_list.append(beat_entry)

    beat_map = {
        "topic": topic,
        "category": "true_crime",
        "arc": "cold_open_mystery",
        "voice": "hm_omega",
        "speed": 0.85,
        "beats": beats_list,
    }

    if output_json:
        out_p = Path(output_json)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        with open(out_p, "w", encoding="utf-8") as f:
            json.dump(beat_map, f, ensure_ascii=False, indent=2)

    return beat_map
