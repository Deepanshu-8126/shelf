import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from factshorts.ai_video import (
    VERIFIED_MODELS,
    UNVERIFIED_BLACKLIST,
    is_model_verified,
    get_recommended_model,
    get_model_specs_summary,
)


def test_verified_models_catalog():
    assert "ltx-2.3" in VERIFIED_MODELS
    assert "wan-2.2" in VERIFIED_MODELS
    assert "hunyuan-1.5" in VERIFIED_MODELS
    assert "z-image-turbo" in VERIFIED_MODELS


def test_model_verification_and_blacklist():
    # Verified models
    ok, msg = is_model_verified("ltx-2.3")
    assert ok is True
    assert "VERIFIED" in msg

    # Blacklisted models
    ok_wan3, msg_wan3 = is_model_verified("wan-3.0")
    assert ok_wan3 is False
    assert "BANNED" in msg_wan3

    ok_hh, msg_hh = is_model_verified("happyhorse")
    assert ok_hh is False
    assert "BANNED" in msg_hh


def test_recommended_models_for_use_cases():
    assert get_recommended_model("factshorts").name == "LTX-2.3"
    assert get_recommended_model("ai influencer").name == "LTX-2.3"
    assert get_recommended_model("long-form youtube").name == "HunyuanVideo 1.5"
    assert get_recommended_model("b-roll clips").name == "Wan 2.2"
    assert get_recommended_model("website hero").name == "Z-Image-Turbo"


def test_model_specs_summary():
    specs = get_model_specs_summary()
    assert len(specs) >= 4
    names = [s["name"] for s in specs]
    assert "LTX-2.3" in names
    assert "Wan 2.2" in names
    assert "HunyuanVideo 1.5" in names
