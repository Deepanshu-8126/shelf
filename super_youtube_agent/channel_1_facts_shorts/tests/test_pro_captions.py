import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from factshorts.captions import build_ass, CaptionPage, CAPTION_STYLES, PUNCH_WORDS
from factshorts.config import get_config


def test_caption_styles_exist():
    styles = ["hormozi", "mrbeast", "karaoke", "neon_glow", "cinematic", "pop_bounce"]
    for s in styles:
        assert s in CAPTION_STYLES
        assert "primary" in CAPTION_STYLES[s]
        assert "highlight" in CAPTION_STYLES[s]
        assert "anim" in CAPTION_STYLES[s]


def test_build_ass_with_hormozi():
    cfg = get_config(refresh=True)
    cfg.caption_style = "hormozi"
    pages = [CaptionPage(["Black", "holes", "slow", "down"], 0.0, 2.0, highlight_index=2)]
    ass_text = build_ass(pages, total_duration=3.0, cfg=cfg, hook_text="Time stops here")
    assert "style: hormozi" in ass_text
    assert "slow" in ass_text
    # Hook V2 badge
    assert any(b in ass_text for b in ["🚨", "📌"])


def test_build_ass_with_punch_word():
    cfg = get_config(refresh=True)
    cfg.caption_style = "mrbeast"
    cfg.animate_punch_words = True
    # "monster" is in PUNCH_WORDS
    pages = [CaptionPage(["A", "monster", "black", "hole"], 0.0, 2.0, highlight_index=1)]
    ass_text = build_ass(pages, total_duration=3.0, cfg=cfg)
    # Check explosive punch highlight color in ASS
    assert "&H000030FF" in ass_text
