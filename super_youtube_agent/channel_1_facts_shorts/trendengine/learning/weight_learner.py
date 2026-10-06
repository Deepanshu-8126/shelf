"""Weight Learner: adjusts trend discovery scoring weights based on published video success."""
from __future__ import annotations

import sqlite3
from typing import Any

from trendengine.db.models import get_db


class WeightLearner:
    def __init__(self, db_path: str = "data/trendengine.db") -> None:
        self.db_path = db_path

    def get_weights(self) -> dict[str, float]:
        default_weights = {
            "velocity": 0.40,
            "recency": 0.25,
            "niche_fit": 0.25,
            "source_authority": 0.10,
        }
        conn = get_db(self.db_path)
        cur = conn.cursor()
        cur.execute("SELECT feature_name, weight FROM scoring_weights")
        rows = cur.fetchall()
        conn.close()
        if not rows:
            return default_weights
        weights = {r["feature_name"]: r["weight"] for r in rows}
        return {**default_weights, **weights}

    def update_weights_from_performance(self, feature_performance: dict[str, float]) -> dict[str, float]:
        """Adjusts weights towards features with higher average views/retention."""
        weights = self.get_weights()
        learning_rate = 0.05

        for feat, score in feature_performance.items():
            if feat in weights:
                # Gradient step towards high performance
                weights[feat] = max(0.05, min(0.60, weights[feat] + (score - 0.5) * learning_rate))

        # Normalize weights so sum is 1.0
        total = sum(weights.values())
        if total > 0:
            weights = {k: round(v / total, 3) for k, v in weights.items()}

        conn = get_db(self.db_path)
        cur = conn.cursor()
        import time
        now = time.time()
        for k, v in weights.items():
            cur.execute("""
                INSERT OR REPLACE INTO scoring_weights (feature_name, weight, updated_at)
                VALUES (?, ?, ?)
            """, (k, v, now))
        conn.commit()
        conn.close()
        return weights
