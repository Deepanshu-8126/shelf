import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from factshorts.autopilot import (
    AutopilotMemory,
    OpportunityScorer,
    TrendCandidate,
    TrendHunter,
    AutonomousStudio,
)
from factshorts.config import get_config


def test_trend_hunter_momentum():
    cfg = get_config()
    hunter = TrendHunter(cfg)
    # High traffic
    assert hunter._calc_momentum("500K+", "Space discovery") >= 94
    # Moderate traffic
    assert hunter._calc_momentum("50K+", "Normal topic") >= 78


def test_opportunity_scorer():
    cand = TrendCandidate(
        title="Why Black Holes Freeze Time",
        source="Test",
        traffic_str="200K+",
        momentum_score=92,
        pillar="space",
        niche="space",
    )
    score = OpportunityScorer.score_candidate(cand, saturation_penalty=0)
    assert score.total_score >= 80
    assert score.safety_score == 95

    # With saturation penalty
    sat_score = OpportunityScorer.score_candidate(cand, saturation_penalty=20)
    assert sat_score.total_score == score.total_score - 20


def test_autopilot_memory(tmp_path: Path):
    memory = AutopilotMemory(tmp_path)
    assert memory.get_pillar_saturation("space") == 0

    # Record 3 runs of space
    for i in range(3):
        memory.record_run("space", f"Topic {i}", 90, f"video_{i}.mp4")

    # Should have saturation penalty
    assert memory.get_pillar_saturation("space") >= 20

    # Propose next move should recommend another pillar
    next_move = memory.propose_next_move()
    assert next_move["current_pillar"] == "space"
    assert next_move["recommended_next_pillar"] != "space"


def test_format_eod_report():
    studio = AutonomousStudio()
    mock_report = {
        "title": "Quantum AI Secret",
        "video_path": "output/test.mp4",
        "chosen_topic": "Quantum AI Secret",
        "pillar": "tech_gaming",
        "niche": "science",
        "opportunity_score": 93,
        "duration": 14.5,
        "uploaded": False,
        "next_move_proposal": {
            "current_pillar": "tech_gaming",
            "saturation_level": "0%",
            "recommended_next_pillar": "space",
            "recommended_hook_style": "curiosity_gap",
            "reasoning": "Keep rotating pillars for peak engagement.",
        },
    }
    report_text = studio.format_eod_report(mock_report)
    assert "FACTSHORTS AUTOPILOT EOD REPORT" in report_text
    assert "Quantum AI Secret" in report_text
    assert "93/100" in report_text
