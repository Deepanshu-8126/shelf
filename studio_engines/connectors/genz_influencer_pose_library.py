"""
GenZ AI Influencer Pose & iPhone Photography Aesthetic Library.
Trains Gemini Vision, Google Veo AI, and Image Generation engines on viral Pinterest/Instagram AI Influencer poses (@derosa_finds aesthetic).

Features 6 Trained Pose Categories:
1. MIRROR_SELFIE_FLASH_POSE: Model holding iPhone in front of aesthetic mirror, cute phone case, showing full-length outfit with subtle flash.
2. HAIR_TUCK_WINDOW_LIGHT: Standing near soft window daylight, one hand casually tucking curtain bangs behind ear, showing neckline & top fit.
3. BEDROOM_CROSS_LEGGED_LAZY: Sitting cross-legged on white linen bed with Kinfolk magazine and coffee mug, casual relaxed influencer vibe.
4. OVER_SHOULDER_CANDID_GLANCE: Over-the-shoulder candid glance towards camera while walking past white paneled door.
5. PRODUCT_DETAIL_TEXTURE_HOLD: Close-up hands holding fabric texture or silver jhumkas towards camera with soft portrait blur.
6. FLATLAY_CREATOR_HANDS_IN_FRAME: Top-down POV angle showing manicured hands arranging 4-piece outfit on white linen bedsheet.

iPhone Camera Aesthetics:
- Shot on iPhone 16 Pro, 24mm / 85mm lens, natural film grain, golden hour daylight, direct flash highlights, raw social media photography look, ZERO CGI smooth skin.
"""
from __future__ import annotations

import random
from typing import Dict, Any, List


class GenZInfluencerPoseLibrary:
    """
    Trained GenZ AI Influencer Pose & iPhone Visual Library.
    """

    IPHONE_CAMERA_TOKENS = (
        "Shot on iPhone 16 Pro, 24mm lens, crisp natural skin texture, golden hour daylight, "
        "raw unedited Instagram aesthetic, realistic film grain, zero CGI smooth skin, 8K ultra-detailed."
    )

    POSES = {
        "MIRROR_SELFIE_FLASH_POSE": {
            "name": "GenZ Mirror Selfie with iPhone",
            "pose_description": (
                "Model standing in front of an aesthetic full-length bedroom mirror, holding a chic iPhone with a cute phone case, "
                "tilting her head slightly with a serene half-smile, displaying her complete outfit fit in the mirror reflection."
            ),
            "camera_angle": "Eye-level mirror reflection shot",
            "lighting": "Soft indoor ambient daylight with subtle mirror flash reflection"
        },
        "HAIR_TUCK_WINDOW_LIGHT": {
            "name": "Candid Hair-Tuck Window Daylight Pose",
            "pose_description": (
                "Model standing casually near a sunlit window, one hand naturally tucking her soft dark curtain bangs behind her ear, "
                "gaze soft and romantic towards the camera, highlighting her silver oxidised jhumkas and neckline fit."
            ),
            "camera_angle": "Medium 85mm portrait shot",
            "lighting": "Warm golden hour natural window sunlight streaming across face"
        },
        "BEDROOM_CROSS_LEGGED_LAZY": {
            "name": "Lazy Sunday Bedroom Sitting Pose",
            "pose_description": (
                "Model sitting cross-legged casually on a white linen bed, leaning on one hand with a coffee mug and Kinfolk magazine nearby, "
                "relaxed candid posture showcasing the comfortable drape of her top and wide-leg jeans."
            ),
            "camera_angle": "Slightly elevated 45-degree angle",
            "lighting": "Warm morning sunlight filtering through sheer curtains"
        },
        "OVER_SHOULDER_CANDID_GLANCE": {
            "name": "Over-the-Shoulder Candid Glance",
            "pose_description": (
                "Model walking past a white paneled shutter door, turning her head back over her shoulder with a relaxed elegant smile, "
                "showing the silhouette, back pattern, and waist tailoring of her outfit."
            ),
            "camera_angle": "Candid street-style over-the-shoulder tracking shot",
            "lighting": "Bright natural outdoor daylight"
        },
        "PRODUCT_DETAIL_TEXTURE_HOLD": {
            "name": "Fabric Texture & Detail Close-Up",
            "pose_description": (
                "Close-up shot of model's manicured hands holding up the fabric hem and dori tassels of her outfit towards the iPhone camera, "
                "with her face softly blurred in the background portrait bokeh."
            ),
            "camera_angle": "Macro close-up portrait shot",
            "lighting": "Direct soft daylight highlighting fabric weave and embroidery"
        },
        "FLATLAY_CREATOR_HANDS_IN_FRAME": {
            "name": "Pinterest 4-Piece Flatlay Combo POV",
            "pose_description": (
                "Top-down 90-degree POV shot showing model's hands placing the final Y2K handbag next to a styled outfit combo "
                "(graphic baby tee + denim jeans + retro brown sneakers) laid out on a white linen bedsheet."
            ),
            "camera_angle": "Vertical top-down flatlay angle",
            "lighting": "Flat even studio daylight"
        },
        "LOW_ANGLE_SNEAKER_SQUAT": {
            "name": "Low-Angle Streetwear Sneaker & Jersey Squat Pose",
            "pose_description": (
                "Model squatting/crouching low towards the camera in an oversized varsity jersey and baggy wide-leg jeans, "
                "resting her chin casually on one hand while staring into the lens, with chunky Nike Dunk Low sneakers "
                "prominently featured in the foreground close-up perspective."
            ),
            "camera_angle": "Low-angle ground-level wide perspective",
            "lighting": "Clean studio portrait lighting with soft shadow fill"
        },
        "OVERSIZED_JERSEY_STREETWEAR": {
            "name": "Oversized Baseball Jersey & Baggy Jeans Streetwear Pose",
            "pose_description": (
                "Model standing in a relaxed streetwear posture wearing an oversized #86 athletic jersey with baggy charcoal denim cargos, "
                "holding a Y2K shoulder bag with a NY Yankees cap, casually looking at camera."
            ),
            "camera_angle": "Full-body vertical 9:16 portrait shot",
            "lighting": "Natural golden hour sun shadow against urban outdoor wall"
        },
        "STUDIO_CUBE_SITTING_POSE": {
            "name": "Minimalist Studio Cube Sitting Pose (Satomi AI Style)",
            "pose_description": (
                "Model sitting casually on a minimalist white studio cube/block in cargo pants and fresh matching sneakers, "
                "leaning forward with relaxed leg angle against a soft mint gradient studio backdrop."
            ),
            "camera_angle": "Eye-level full-body studio portrait angle",
            "lighting": "Soft gradient studio rim lighting with subtle floor reflection"
        },
        "CYBER_RED_NEON_GRID_LEAN": {
            "name": "Cyberpunk Red Neon Grid Wall Lean Pose",
            "pose_description": (
                "Model leaning back gracefully against a vibrant red neon LED grid tiled wall, arching back slightly with waist exposed, "
                "wearing a black micro crop baby tee + loose trackpants + dark Y2K sunglasses tilted down her nose."
            ),
            "camera_angle": "Low-to-mid angle high-fashion editorial portrait shot",
            "lighting": "Atmospheric red neon LED ambient light glow with sharp edge highlights"
        },
        "NIRVANA_BAND_TEE_STAIRS_FLASH": {
            "name": "Night Flash Concrete Stairs Band Tee Pose",
            "pose_description": (
                "Model sitting on urban concrete outdoor stairs at night, wearing a dark NY Yankees cap + vintage yellow NIRVANA band tee + "
                "cream oversized cardigan + dark green cargo trousers + Nike Dunk High sneakers, looking into camera."
            ),
            "camera_angle": "Slightly elevated night portrait shot",
            "lighting": "Direct hard direct camera flash photography at night"
        },
        "DENIM_JORTS_ICED_COFFEE_STREET": {
            "name": "Street Corner Iced Coffee & Denim Jorts Pose",
            "pose_description": (
                "Model standing on a sunlit urban street corner holding a clear iced coffee cup with straw, wearing a navy #91 California jersey tee + "
                "baggy long denim jorts + white crew socks + Adidas Samba sneakers, casually touching her cap."
            ),
            "camera_angle": "Full-length 9:16 vertical street style shot",
            "lighting": "Bright natural sunlit street shadows"
        },
        "GRAFFITI_TUNNEL_FLASH_POSE": {
            "name": "Underground Spray-Paint Graffiti Wall Flash Pose",
            "pose_description": (
                "Model standing or leaning casually against a vibrant urban spray-paint graffiti wall, wearing a backwards black baseball cap + "
                "clear-frame optical glasses + off-shoulder Y2K crop top + low-rise baggy cargo jeans with exposed waistband and silver chain belt."
            ),
            "camera_angle": "Eye-level medium portrait shot with slight tilt",
            "lighting": "Hard camera direct flash photography creating dramatic urban night mood and sharp edge highlights"
        },
        "BIRDS_EYE_90DEG_HIGH_ANGLE": {
            "name": "90-Degree Top-Down Bird's Eye POV Selfie Pose",
            "pose_description": (
                "Camera positioned directly overhead 90 degrees looking straight down at model. Model standing or sitting, looking up into camera lens "
                "wearing slim black oval sunglasses, extending one hand towards camera in a playful candid gesture."
            ),
            "camera_angle": "90-degree steep top-down overhead perspective",
            "lighting": "Bright high-key studio or outdoor daylight"
        },
        "FISHEYE_NEON_CONVENIENCE_STORE": {
            "name": "12mm Fisheye Green Neon Convenience Store Pose",
            "pose_description": (
                "Model standing in front of a glowing green neon convenience store / arcade background, wearing a black ribbed crop top + "
                "wide-leg denim jeans + slim black sunglasses, hands on hips with distinctive circular fisheye lens curvature."
            ),
            "camera_angle": "12mm ultra-wide fisheye lens distortion perspective",
            "lighting": "Atmospheric green neon glow with high-contrast ambient reflections"
        },
        "HAND_TO_CAMERA_FORESHORTENING": {
            "name": "Hand-to-Lens Perspective Foreshortening Pose",
            "pose_description": (
                "Model crouching or standing on urban asphalt street, reaching one hand directly forward towards the camera lens, "
                "creating dramatic perspective foreshortening with fingers in foreground close-up while face and outfit remain in sharp focus."
            ),
            "camera_angle": "Ultra-wide low-angle perspective shot",
            "lighting": "Natural overcast open-sky daylight"
        },
        "SUBWAY_TRAIN_SEAT_LEAN": {
            "name": "Metro Public Subway Seat Transit Lean",
            "pose_description": (
                "Model sitting relaxed on a public metro subway car blue seat, leaning back against stainless steel handrails, "
                "wearing a graphic streetwear tee + camo cargo pants + tilted NY cap, resting her chin thoughtfully on her hand."
            ),
            "camera_angle": "Medium interior transit portrait shot",
            "lighting": "Cool fluorescent subway train ambient lighting"
        },
        "ROOFTOP_GROUND_SQUAT_FUNKY": {
            "name": "Funky Yellow Sunglasses Rooftop Squat Pose",
            "pose_description": (
                "Model squatting low on open rooftop concrete ground under bright blue sky with white clouds, wearing tinted yellow oval sunglasses, "
                "popping her tongue out playfully while adjusting her glasses frame with manicured fingers."
            ),
            "camera_angle": "Low-angle wide sky-frame perspective",
            "lighting": "Direct bright sunlight with high-contrast blue sky background"
        },
        "CROSSWALK_NIGHT_FLOOR_SPREAD": {
            "name": "Night Street Crosswalk Zebra Spread Pose",
            "pose_description": (
                "Model sitting flat on street crosswalk white zebra pavement at night, legs spread casually wide in a low-angle wide perspective, "
                "wearing black micro tee + wide-leg vintage wash jeans + chunky white sneakers, looking into camera."
            ),
            "camera_angle": "Ground-level wide low perspective shot",
            "lighting": "Street lamp ambient glow with subtle passing car headlight rim light"
        }
    }

    EXPRESSIONS = {
        "CONFIDENT_PLAYFUL": "radiant confident playful grin with slight dimple, bright sparkling eyes directly engaging the viewer",
        "CHIC_SMIRK": "effortless chic Gen Z half-smirk, one eyebrow raised subtly, playful confident stare",
        "DREAMY_OFF_CAMERA": "soft dreamy candid look glancing slightly off-camera, gentle serene parted lips catching natural light",
        "LAUGHING_CANDID": "spontaneous mid-laugh candid expression, joyful natural crinkle around eyes, radiating authentic creator energy",
        "HIGH_FASHION_POUT": "cool editorial high-fashion relaxed neutral expression, intense focused eyes, subtle soft parted lips",
        "DELIGHTED_REACTION": "delighted excited smile reacting to how flattering the outfit looks, energetic friendly expression",
        "SOPHISTICATED_CHARM": "poised sophisticated gentle smile, eyes softly illuminated, warm graceful aura",
        "EDGY_ATTITUDE": "cool unbothered attitude, chin tilted up slightly, relaxed lips, effortless street style presence"
    }

    CATEGORY_POSE_MAP = {
        "ethnic": [
            "HAIR_TUCK_WINDOW_LIGHT",
            "OVER_SHOULDER_CANDID_GLANCE",
            "PRODUCT_DETAIL_TEXTURE_HOLD",
            "BEDROOM_CROSS_LEGGED_LAZY",
            "MIRROR_SELFIE_FLASH_POSE"
        ],
        "streetwear": [
            "LOW_ANGLE_SNEAKER_SQUAT",
            "OVERSIZED_JERSEY_STREETWEAR",
            "STUDIO_CUBE_SITTING_POSE",
            "CYBER_RED_NEON_GRID_LEAN",
            "NIRVANA_BAND_TEE_STAIRS_FLASH",
            "DENIM_JORTS_ICED_COFFEE_STREET",
            "GRAFFITI_TUNNEL_FLASH_POSE",
            "BIRDS_EYE_90DEG_HIGH_ANGLE",
            "FISHEYE_NEON_CONVENIENCE_STORE",
            "HAND_TO_CAMERA_FORESHORTENING",
            "SUBWAY_TRAIN_SEAT_LEAN",
            "ROOFTOP_GROUND_SQUAT_FUNKY"
        ],
        "dresses": [
            "OVER_SHOULDER_CANDID_GLANCE",
            "MIRROR_SELFIE_FLASH_POSE",
            "STUDIO_CUBE_SITTING_POSE",
            "HAIR_TUCK_WINDOW_LIGHT",
            "BEDROOM_CROSS_LEGGED_LAZY",
            "CYBER_RED_NEON_GRID_LEAN"
        ],
        "casual": [
            "HAIR_TUCK_WINDOW_LIGHT",
            "DENIM_JORTS_ICED_COFFEE_STREET",
            "BEDROOM_CROSS_LEGGED_LAZY",
            "FLATLAY_CREATOR_HANDS_IN_FRAME",
            "STUDIO_CUBE_SITTING_POSE",
            "MIRROR_SELFIE_FLASH_POSE"
        ]
    }

    _recent_pose_history: List[str] = []

    @classmethod
    def get_pose(cls, pose_key: str | None = None) -> Dict[str, Any]:
        """Returns specific pose dict or picks a non-repeating random GenZ pose."""
        if pose_key and pose_key in cls.POSES:
            selected_key = pose_key
        else:
            available = [k for k in cls.POSES.keys() if k not in cls._recent_pose_history[-4:]]
            if not available:
                available = list(cls.POSES.keys())
            selected_key = random.choice(available)

        cls._recent_pose_history.append(selected_key)
        if len(cls._recent_pose_history) > 10:
            cls._recent_pose_history.pop(0)

        pose_info = cls.POSES[selected_key]
        return {
            "pose_key": selected_key,
            "pose_name": pose_info["name"],
            "description": pose_info["pose_description"],
            "camera_angle": pose_info["camera_angle"],
            "lighting": pose_info["lighting"],
            "camera_tokens": cls.IPHONE_CAMERA_TOKENS
        }

    @classmethod
    def get_dynamic_pose_and_expression(cls, category_hint: str | None = None) -> Dict[str, Any]:
        """
        Dynamically selects a non-repeating, category-matching pose paired with a complementary facial expression.
        Guarantees diverse visuals even with the same character sheet.
        """
        cat_lower = (category_hint or "").lower()
        matched_category = "casual"
        if any(w in cat_lower for w in ["kurti", "saree", "anarkali", "lehenga", "ethnic"]):
            matched_category = "ethnic"
        elif any(w in cat_lower for w in ["cargo", "hoodie", "jersey", "jorts", "street", "sneaker"]):
            matched_category = "streetwear"
        elif any(w in cat_lower for w in ["dress", "gown", "bodycon", "maxi", "midi"]):
            matched_category = "dresses"

        pose_pool = cls.CATEGORY_POSE_MAP.get(matched_category, list(cls.POSES.keys()))
        fresh_pool = [k for k in pose_pool if k not in cls._recent_pose_history[-3:]]
        selected_pose_key = random.choice(fresh_pool if fresh_pool else pose_pool)

        pose_data = cls.get_pose(selected_pose_key)
        expr_key, expr_desc = random.choice(list(cls.EXPRESSIONS.items()))

        pose_data["expression_key"] = expr_key
        pose_data["expression"] = expr_desc
        return pose_data

    @classmethod
    def format_influencer_prompt(cls, outfit_name: str, pose_key: str | None = None, category_hint: str | None = None) -> str:
        """Constructs full AI Influencer prompt with dynamic GenZ pose, expression, and iPhone camera aesthetic."""
        if pose_key:
            p = cls.get_pose(pose_key)
            _, expr_desc = random.choice(list(cls.EXPRESSIONS.items()))
        else:
            p = cls.get_dynamic_pose_and_expression(category_hint or outfit_name)
            expr_desc = p["expression"]

        return (
            f"Hyper-realistic 4K 60fps GenZ AI Influencer photoshoot. "
            f"Outfit: {outfit_name}. "
            f"Facial Expression: {expr_desc}. "
            f"Pose & Action: {p['description']} "
            f"Camera & Angle: {p['camera_angle']}. "
            f"Lighting & Environment: {p['lighting']}. "
            f"{p['camera_tokens']}"
        )


if __name__ == "__main__":
    lib = GenZInfluencerPoseLibrary()
    print("\n[Dynamic Editorial GenZ Pose & Expression Demo]:")
    for cat in ["Ethnic Kurti", "Baggy Tactical Cargo", "Bodycon Maxi Dress"]:
        sample = lib.get_dynamic_pose_and_expression(cat)
        print(f"\n--- Category: {cat} ---")
        print(f"  • Selected Pose : {sample['pose_name']}")
        print(f"  • Expression    : {sample['expression']}")
        print(f"  • Angle         : {sample['camera_angle']}")

