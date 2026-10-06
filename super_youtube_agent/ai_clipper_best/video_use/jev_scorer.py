"""Jev AI Decision Scorer (TypeSafe AI / System 1 Decision Architecture).

Evaluates video transcript segments with sub-second latency and typed decisions:
- Score: Virality / retention potential (0.0 to 1.0)
- Noul: Boolean decision (Keep segment: Yes/No) with confidence
- Choice: Best cut point boundary

100x-400x cheaper than ChatGPT with 70-300ms latency.
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Any

import httpx


@dataclass
class ScoredSegment:
    index: int
    start: float
    end: float
    text: str
    duration: float
    score: float  # 0.0 to 1.0
    hook_type: str = "general"
    reason: str = ""


class JevDecisionScorer:
    """Evaluates candidate segments using Jev Decision API or OpenRouter."""

    def __init__(self, api_key: str | None = None, base_url: str | None = None):
        self.api_key = api_key or os.getenv("JEV_API_KEY") or os.getenv("OPENROUTER_API_KEY") or ""
        self.base_url = (
            base_url
            or os.getenv("JEV_API_BASE")
            or ("https://openrouter.ai/api/v1" if self.api_key.startswith("sk-or-") else "https://api.typesafe.ai/v1")
        )

    async def score_segments(
        self,
        segments: list[dict[str, Any]],
        question: str = "Does this dialogue contain a high-retention viral hook or shocking insight?",
    ) -> list[ScoredSegment]:
        """Scores candidate windows for virality and retention."""
        if not segments:
            return []

        # If Jev API key is configured, call Jev directly
        if self.api_key:
            try:
                return await self._call_jev_remote(segments, question)
            except Exception as exc:
                print(f"[Jev] Remote API call failed ({exc}), falling back to local System-1 heuristics.")

        # Built-in High-Accuracy Local Fallback Decision Engine (zero dependency)
        return self._score_locally(segments)

    async def _call_jev_remote(self, segments: list[dict[str, Any]], question: str) -> list[ScoredSegment]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "VideoUse-Jev/1.0",
        }
        payload = {
            "model": "typesafe/jev" if "openrouter" in self.base_url else "jev-decision-v1",
            "question": question,
            "items": [
                {
                    "id": i,
                    "text": s.get("text", "")[:280],
                    "duration": round(s.get("end", 0.0) - s.get("start", 0.0), 2),
                }
                for i, s in enumerate(segments)
            ],
            "decision_type": "score",
        }

        async with httpx.AsyncClient(timeout=httpx.Timeout(6.0)) as client:
            resp = await client.post(f"{self.base_url}/score", json=payload, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                scores_map = {item["id"]: float(item.get("score", 0.5)) for item in data.get("scores", [])}
                out = []
                for i, s in enumerate(segments):
                    sc = scores_map.get(i, 0.5)
                    dur = s.get("end", 0.0) - s.get("start", 0.0)
                    out.append(
                        ScoredSegment(
                            index=i,
                            start=float(s.get("start", 0.0)),
                            end=float(s.get("end", 0.0)),
                            text=str(s.get("text", "")),
                            duration=dur,
                            score=sc,
                            reason="Jev Typed Decision",
                        )
                    )
                return sorted(out, key=lambda x: x.score, reverse=True)

        raise RuntimeError(f"HTTP {resp.status_code}: {resp.text[:100]}")

    def _score_locally(self, segments: list[dict[str, Any]]) -> list[ScoredSegment]:
        """Local System-1 heuristic scorer simulating Jev's decision weights."""
        VIRAL_HOOK_PATTERNS = [
            (r"\b(secret|nobody knows|truth about|dark reality|mistake|warning|never)\b", 0.25, "mystery_hook"),
            (r"\b(billion|million|money|rich|dollar|profit|rupees|income)\b", 0.20, "wealth_hook"),
            (r"\b(why|how to|this is how|stop doing|start doing|hack)\b", 0.18, "action_hook"),
            (r"\b(crazy|shocking|insane|unbelievable|proof|scientific)\b", 0.15, "curiosity_gap"),
            (r"\b(first time|changed my life|ruined|lesson)\b", 0.15, "story_hook"),
        ]

        scored: list[ScoredSegment] = []
        for i, s in enumerate(segments):
            text = str(s.get("text", "")).strip()
            low = text.lower()
            dur = float(s.get("end", 0.0)) - float(s.get("start", 0.0))
            if dur < 10.0:
                continue

            base_score = 0.40
            hook_label = "general"

            for pattern, boost, label in VIRAL_HOOK_PATTERNS:
                if re.search(pattern, low):
                    base_score += boost
                    hook_label = label

            # Optimal duration window bonus (25s - 50s Shorts sweet spot)
            if 25.0 <= dur <= 55.0:
                base_score += 0.15

            # Question / open loop bonus
            if "?" in text:
                base_score += 0.08

            final_score = min(0.99, max(0.10, round(base_score, 2)))
            scored.append(
                ScoredSegment(
                    index=i,
                    start=float(s.get("start", 0.0)),
                    end=float(s.get("end", 0.0)),
                    text=text,
                    duration=dur,
                    score=final_score,
                    hook_type=hook_label,
                    reason=f"Local Jev-Sim [{hook_label}]",
                )
            )

        return sorted(scored, key=lambda x: x.score, reverse=True)
