"""Thompson Sampling Multi-Armed Bandit for continuous content optimization."""
from __future__ import annotations

import random
import sqlite3
from typing import Any

from trendengine.db.models import get_db


class ThompsonBandit:
    def __init__(self, db_path: str = "data/trendengine.db") -> None:
        self.db_path = db_path

    def _ensure_arm(self, arm_type: str, arm_value: str, conn: sqlite3.Connection) -> None:
        cur = conn.cursor()
        cur.execute("""
            INSERT OR IGNORE INTO bandit_arms (arm_type, arm_value, alpha, beta)
            VALUES (?, ?, 1.0, 1.0)
        """, (arm_type, arm_value))
        conn.commit()

    def select_arm(self, arm_type: str, candidate_arms: list[str]) -> str:
        """Picks the best arm using Thompson Sampling (sampling from Beta(alpha, beta))."""
        conn = get_db(self.db_path)
        cur = conn.cursor()
        best_arm = candidate_arms[0]
        max_sample = -1.0

        for arm in candidate_arms:
            self._ensure_arm(arm_type, arm, conn)
            cur.execute("""
                SELECT alpha, beta FROM bandit_arms 
                WHERE arm_type = ? AND arm_value = ?
            """, (arm_type, arm))
            row = cur.fetchone()
            alpha = row["alpha"] if row else 1.0
            beta = row["beta"] if row else 1.0
            # Sample from Beta distribution
            sample = random.betavariate(max(0.1, alpha), max(0.1, beta))
            if sample > max_sample:
                max_sample = sample
                best_arm = arm

        conn.close()
        return best_arm

    def update_reward(self, arm_type: str, arm_value: str, reward: float) -> None:
        """Update Beta distribution: reward in [0, 1] (e.g. normalized CTR / retention)."""
        r = max(0.0, min(1.0, float(reward)))
        conn = get_db(self.db_path)
        cur = conn.cursor()
        self._ensure_arm(arm_type, arm_value, conn)
        cur.execute("""
            UPDATE bandit_arms 
            SET alpha = alpha + ?, beta = beta + (1.0 - ?)
            WHERE arm_type = ? AND arm_value = ?
        """, (r, r, arm_type, arm_value))
        conn.commit()
        conn.close()
