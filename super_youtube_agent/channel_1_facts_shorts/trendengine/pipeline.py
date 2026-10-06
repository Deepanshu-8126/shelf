"""Master Autopilot Pipeline for Trend-Engine: discover -> score -> draft -> gate -> render -> learn."""
from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import yaml

from trendengine.db.models import init_db, save_discovered_topics, get_top_topics, mark_topic_status
from trendengine.sources.reddit_scout import RedditScout
from trendengine.sources.trends_scout import TrendsScout
from trendengine.sources.rss_scout import RSSScout
from trendengine.sources.youtube_scout import YouTubeScout
from trendengine.analysis.scorer import TopicScorer
from trendengine.llm.local_writer import LocalWriter
from trendengine.generation.drafter import ScriptDrafter
from trendengine.guardrails.quality_gate import QualityGate
from trendengine.learning.bandit import ThompsonBandit
from trendengine.learning.weight_learner import WeightLearner


def load_config(config_path: str = "trendengine/config.yaml") -> dict[str, Any]:
    p = Path(config_path)
    if p.exists():
        with open(p, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}


async def discover_all_trends(cfg: dict[str, Any]) -> list[dict[str, Any]]:
    """Runs all 4 scouts concurrently to gather trending subjects."""
    reddit = RedditScout()
    trends = TrendsScout(geo=cfg.get("sources", {}).get("google_trends", {}).get("geo", "IN"))
    rss = RSSScout()
    youtube = YouTubeScout()

    tasks = [
        reddit.fetch_trends(),
        trends.fetch_trends(),
        rss.fetch_trends(),
        youtube.fetch_trends(),
    ]
    gathered = await asyncio.gather(*tasks, return_exceptions=True)
    all_items: list[dict[str, Any]] = []
    for batch in gathered:
        if isinstance(batch, list):
            all_items.extend(batch)
    return all_items


async def run_cycle(
    config_path: str = "trendengine/config.yaml",
    forced_topic: str | None = None,
) -> dict[str, Any]:
    """Autonomous execution cycle: discover -> score -> draft -> quality gate."""
    cfg = load_config(config_path)
    db_path = cfg.get("db_path", "data/trendengine.db")
    init_db(db_path)

    bandit = ThompsonBandit(db_path)
    learner = WeightLearner(db_path)
    current_weights = learner.get_weights()
    scorer = TopicScorer(weights=current_weights)

    # 1. Discover or use forced topic
    if forced_topic:
        top_topic = {
            "title": forced_topic,
            "summary": forced_topic,
            "source": "manual",
            "source_url": "",
            "niche": "science",
            "score": 100.0,
            "velocity": 50.0,
        }
    else:
        raw_trends = await discover_all_trends(cfg)
        save_discovered_topics(raw_trends, db_path)
        ranked = scorer.score_topics(raw_trends)
        if not ranked:
            # Fallback to stored topics
            ranked = get_top_topics(limit=5, db_path=db_path)
        if not ranked:
            ranked = [{
                "title": "Quantum Entanglement Faster Than Light",
                "summary": "Particles remain instantly connected across billions of light years.",
                "source": "fallback",
                "source_url": "",
                "niche": "science",
                "score": 90.0,
                "velocity": 20.0,
            }]
        top_topic = ranked[0]

    # 2. Thompson Bandit selects optimal Hook & CTA styles
    hook_arms = cfg.get("bandit", {}).get("arms", {}).get(
        "hook_styles", ["pattern_interrupt", "paradox_question", "bold_shock_claim"]
    )
    cta_arms = cfg.get("bandit", {}).get("arms", {}).get(
        "cta_styles", ["loop_curiosity", "comment_debate", "follow_series"]
    )
    selected_hook = bandit.select_arm("hook_style", hook_arms)
    selected_cta = bandit.select_arm("cta_style", cta_arms)

    # 3. Draft Script with Local LLM (Ollama / Qwen3 / Gemini)
    writer = LocalWriter(
        ollama_host=cfg.get("ollama_host", "http://localhost:11434"),
        model=cfg.get("local_model", "qwen2.5:7b"),
    )
    drafter = ScriptDrafter(writer)
    gate = QualityGate(writer, min_score=cfg.get("quality_threshold", 7))

    script_result: dict[str, Any] = {}
    quality_result: dict[str, Any] = {}

    # 4. Quality Gate with up to 2 retries
    for attempt in range(1, 4):
        script_result = await drafter.draft_script(
            topic=top_topic,
            brand_voice=cfg.get("brand_voice", "casual, curious, slightly humorous"),
            audience=cfg.get("audience", "18-35, Indian + global"),
            language=cfg.get("language", "Hinglish"),
            hook_style=selected_hook,
            cta_style=selected_cta,
        )
        quality_result = await gate.evaluate_script(script_result)
        if quality_result.get("passed"):
            break

    # Persist in DB
    topic_id = top_topic.get("id", 1)
    if isinstance(topic_id, int):
        mark_topic_status(topic_id, "drafted", db_path)

    return {
        "topic": top_topic,
        "script": script_result,
        "quality": quality_result,
        "hook_style": selected_hook,
        "cta_style": selected_cta,
        "visual_keywords": script_result.get("visual_keywords", []),
    }
