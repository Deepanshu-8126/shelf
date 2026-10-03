"""
==============================================================================
✨ PINTEREST HIGH-FASHION EDITORIAL AESTHETIC & POSE MATRIX
==============================================================================
Designed from viral Pinterest fashion boards:
- Eliminates repetitive phone-mirror selfies.
- Features authentic, natural high-editorial poses used by top fashion creators:
  1. GRAND_STAIRCASE_ELEGANCE: Walking down grand marble spiral staircase, gown train trailing.
  2. HAIR_UPDO_BACK_DETAIL: Hands lifting long hair, showcasing back cut, strappy ties & silhouette.
  3. HOTEL_CORRIDOR_STRUT: Editorial candid walk through minimalist luxury hotel hallway / archway.
  4. SUNLIT_CAFE_SIDE_GLANCE: Seated/standing by outdoor cafe bistro table with natural side daylight.
  5. YACHT_DECK_WIND_FLOW: Standing on sunlit wooden deck/balcony, gentle breeze flowing through dress.
  6. ARCHITECTURAL_PILLAR_LEAN: Effortless posture leaning against modern concrete/marble column.
  7. 85MM_PORTRAIT_BOKEH: Medium close-up, dreamy soft focus background, subtle head turn.
  8. PENTHOUSE_EVENING_GLOW: Standing near floor-to-ceiling glass window overlooking city sunset.
  9. PALACE_JHAROKHA_SAREE: Regal Saree drape with gentle hand resting on traditional carved arch.
  10. MINIMALIST_STUDIO_DAYLIGHT: Clean soft studio daylight, high-fashion relaxed editorial posture.
==============================================================================
"""

import random
from typing import Dict, Any

PINTEREST_EDITORIAL_POSES = {
    "GRAND_STAIRCASE_ELEGANCE": {
        "name": "Grand Marble Staircase Descent",
        "pose_desc": "poised full-length posture gracefully walking down an opulent curved marble staircase in a luxury villa, one hand lightly brushing the ornate wrought-iron railing, showcasing the elegant sweeping drape and movement of the outfit",
        "setting": "high-ceiling architectural mansion with classical chandelier and marble floors",
        "lighting": "Soft warm ambient palace lighting with gentle floor reflections"
    },
    "HAIR_UPDO_BACK_DETAIL": {
        "name": "Candid Hair-Lift & Back Silhouette",
        "pose_desc": "candid posture with both hands naturally gathering her voluminous dark wavy hair up at the crown of her head, turning back slightly to showcase the delicate back silhouette, neckline cuts, and fitted tailoring of the garment",
        "setting": "clean aesthetic sunlit minimalist room with neutral warm off-white curtains",
        "lighting": "Natural soft diffused daylight streaming through sheer window drapes"
    },
    "HOTEL_CORRIDOR_STRUT": {
        "name": "Luxury Hotel Hallway Editorial Stride",
        "pose_desc": "effortless high-fashion walking stride down a modern architectural hotel corridor, relaxed arms, candid side glance away from camera, capturing authentic fabric flow and contour",
        "setting": "sleek contemporary hallway with warm wood paneling and marble pillar accents",
        "lighting": "Warm recessed ceiling cove lights creating subtle edge contouring"
    },
    "SUNLIT_CAFE_SIDE_GLANCE": {
        "name": "European Outdoor Cafe Elegance",
        "pose_desc": "standing or seated gracefully next to a chic outdoor bistro marble table, holding an espresso cup, candid relaxed smile looking slightly off-camera",
        "setting": "cobblestone street cafe terrace with lush potted olive plants",
        "lighting": "Bright golden hour morning sunlight casting natural soft shadows"
    },
    "YACHT_DECK_WIND_FLOW": {
        "name": "Sunlit Balcony & Breeze Flow",
        "pose_desc": "standing gracefully on a sunny teak wood balcony deck, one hand gently steadying the hem in a gentle coastal breeze, showcasing the lightweight drape and movement of the fabric",
        "setting": "open-air sunlit terrace overlooking deep blue water horizon",
        "lighting": "Brilliant natural open-sky daylight with soft golden rim light on hair"
    },
    "ARCHITECTURAL_PILLAR_LEAN": {
        "name": "Minimalist Column Lean",
        "pose_desc": "leaning back casually and effortlessly against a smooth limestone architectural pillar, one leg softly bent, relaxed hands at her sides with silver bangles catching the light",
        "setting": "modern art gallery courtyard with clean geometric lines",
        "lighting": "High-key directional natural daylight creating rich natural contrast"
    },
    "85MM_PORTRAIT_BOKEH": {
        "name": "Dreamy 85mm Close-Up Portrait",
        "pose_desc": "cinematic medium 85mm portrait shot, face turned 45-degrees with a serene enigmatic gaze, one hand delicately touching her collarbone, highlighting earring sparkle and neckline fit",
        "setting": "soft blurred botanical background with lush green foliage bokeh",
        "lighting": "Flattering soft beauty lighting with luminous eye catchlights"
    },
    "PALACE_JHAROKHA_SAREE": {
        "name": "Heritage Palace Archway Saree Drape",
        "pose_desc": "regal traditional posture standing beside a carved stone jharokha archway, both hands delicately holding the ornate pleated pallu drape, looking out gracefully with serene dignity",
        "setting": "sunlit heritage Indian palace courtyard with sandstone arches and flowering bougainvillea",
        "lighting": "Warm golden afternoon sunlight creating rich warm skin tones and fabric luster"
    }
}


def get_pinterest_brand_prompt(product_title: str, fabric: str = "Silk/Lycra", pose_key: str = None) -> tuple[str, str]:
    """Generates a high-end, organic Pinterest brand photoshoot prompt (No iPhone selfies)."""
    if pose_key and pose_key in PINTEREST_EDITORIAL_POSES:
        p = PINTEREST_EDITORIAL_POSES[pose_key]
    else:
        # Pick appropriate pose
        is_saree = any(w in product_title.lower() for w in ["saree", "sari", "ethnic", "lehenga", "anarkali"])
        if is_saree:
            p = PINTEREST_EDITORIAL_POSES["PALACE_JHAROKHA_SAREE"]
        else:
            candidates = ["GRAND_STAIRCASE_ELEGANCE", "HAIR_UPDO_BACK_DETAIL", "HOTEL_CORRIDOR_STRUT", "SUNLIT_CAFE_SIDE_GLANCE", "ARCHITECTURAL_PILLAR_LEAN", "85MM_PORTRAIT_BOKEH"]
            p = PINTEREST_EDITORIAL_POSES[random.choice(candidates)]

    prompt = (
        f"Authentic raw 35mm fashion editorial photograph of the exact same 21-year-old young Indian creator "
        f"(natural soft-oval face shape, warm glowing honey-toned skin with visible fine pores and real texture, "
        f"expressive warm honey-brown almond eyes with subtle dark tightline, delicate nose, soft rose-pink lips, "
        f"signature tiny round black bindi centered above eyebrows, voluminous dark espresso black wavy hair styled with soft wispy curtain strands, "
        f"traditional silver oxidised bell-shaped jhumkas and delicate stacked silver bangles) "
        f"wearing the {product_title} in premium {fabric} shown in the attached reference image. "
        f"Pose: {p['pose_desc']}. "
        f"Environment: {p['setting']}. "
        f"Lighting & Atmosphere: {p['lighting']}. "
        f"Shot on Hasselblad 50mm f/1.8 lens, natural Kodak Portra 400 film tones, organic optical depth of field, "
        f"hyper-realistic fabric weave and natural drape, high-fashion Pinterest influencer aesthetic, zero phone in hand, zero mirror selfie, zero CGI smooth plastic skin."
    )

    return p["name"], prompt
