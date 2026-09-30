"""Topic Scorer: multi-factor ranking (recency, velocity, niche fit, learned weights) + dedup."""
from __future__ import annotations

import re
from typing import Any


def _tokenize(text: str) -> set[str]:
    words = re.findall(r"\w+", (text or "").lower())
    return {w for w in words if len(w) > 3}


def jaccard_similarity(a: str, b: str) -> float:
    set_a = _tokenize(a)
    set_b = _tokenize(b)
    if not set_a or not set_b:
        return 0.0
    return len(set_a & set_b) / len(set_a | set_b)


class TopicScorer:
    def __init__(self, weights: dict[str, float] | None = None) -> None:
        self.weights = weights or {
            "velocity": 0.40,
            "recency": 0.25,
            "niche_fit": 0.25,
            "source_authority": 0.10,
        }

    def score_topics(
        self,
        raw_topics: list[dict[str, Any]],
        target_niches: list[str] | None = None,
        history_titles: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        niches = [n.lower() for n in (target_niches or ["space", "science", "facts", "psychology"])]
        history = history_titles or []
        scored: list[dict[str, Any]] = []

        for item in raw_topics:
            title = item.get("title", "")
            if not title:
                continue

            # 1. Semantic dedup against past published titles
            if any(jaccard_similarity(title, past) > 0.45 for past in history):
                continue

            # 2. Recency score (decays over hours)
            age_hours = float(item.get("age_hours", 2.0))
            recency_score = max(0.1, 1.0 / (1.0 + (age_hours / 12.0)))

            # 3. Velocity score (normalized log-scale)
            raw_vel = float(item.get("velocity", 10.0))
            velocity_score = min(1.0, raw_vel / 100.0)

            # 4. Niche relevance
            niche = str(item.get("niche", "science")).lower()
            text_corpus = f"{title} {item.get('summary', '')}".lower()
            niche_fit = 1.0 if niche in niches or any(n in text_corpus for n in niches) else 0.4

            # 5. Source authority
            src = str(item.get("source", "")).lower()
            authority = 0.9 if "rss" in src or "nasa" in src else (0.85 if "reddit" in src else 0.75)

            # Composite weighted calculation
            final_score = (
                self.weights.get("velocity", 0.40) * velocity_score
                + self.weights.get("recency", 0.25) * recency_score
                + self.weights.get("niche_fit", 0.25) * niche_fit
                + self.weights.get("source_authority", 0.10) * authority
            ) * 100.0

            enriched = dict(item)
            enriched["score"] = round(final_score, 2)
            scored.append(enriched)

        # Sort descending by score
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored
