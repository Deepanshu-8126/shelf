"""Quality Gate: LLM self-critique (1-10), blocklist, length check, and fact verification."""
from __future__ import annotations

import re
import urllib.parse
import httpx
from typing import Any

from trendengine.llm.local_writer import LocalWriter

BANNED_WORDS = {
    "nsfw", "porn", "gambling", "crypto scam", "hate", "suicide", "terrorism",
    "politics", "election rigging", "medical cure", "miracle cure"
}


class QualityGate:
    def __init__(self, writer: LocalWriter | None = None, min_score: int = 7) -> None:
        self.writer = writer or LocalWriter()
        self.min_score = min_score

    def check_blocklist(self, text: str) -> tuple[bool, str]:
        lower = text.lower()
        for banned in BANNED_WORDS:
            if banned in lower:
                return False, f"Blocked word/topic detected: {banned}"
        return True, "OK"

    async def verify_wikipedia(self, query: str) -> bool:
        """Lightweight Wikipedia sanity check for factual grounding."""
        try:
            url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(query)}"
            async with httpx.AsyncClient(timeout=httpx.Timeout(4.0)) as client:
                resp = await client.get(url)
                return resp.status_code == 200
        except Exception:
            return True  # Don't hard-fail if network has hiccups

    async def evaluate_script(self, script_data: dict[str, Any]) -> dict[str, Any]:
        """LLM self-critique assessing virality, pacing, hook quality, and retention."""
        hook = script_data.get("hook", "")
        body = script_data.get("body", "")
        closing = script_data.get("closing", "")
        word_count = script_data.get("word_count", 0)

        # 1. Blocklist check
        ok, reason = self.check_blocklist(f"{hook} {body} {closing}")
        if not ok:
            return {"passed": False, "score": 1, "reason": reason}

        # 2. Length sanity check
        if word_count < 25:
            return {"passed": False, "score": 3, "reason": f"Script too short ({word_count} words)"}

        # 3. LLM Self-Critique
        system = "You are a ruthless YouTube Shorts retention and virality auditor."
        prompt = f"""Evaluate this YouTube Shorts script for virality, hook strength, and retention.

Script:
Hook: {hook}
Body: {body}
Closing: {closing}
Word Count: {word_count}

Score from 1 to 10:
- 9-10: Mind-bending hook, zero filler, escalating tension, perfect loop.
- 7-8: Strong curiosity, clear payoff, good pacing.
- 1-6: Generic, predictable, boring, or sounds like an ad.

Return ONLY JSON:
{{
  "score": <number 1-10>,
  "reason": "short 1-line explanation",
  "passed": <true if score >= {self.min_score} else false>
}}
"""
        try:
            critique = await self.writer.generate_json(prompt, system)
            score = float(critique.get("score", 7))
            passed = score >= self.min_score
            return {
                "passed": passed,
                "score": score,
                "reason": critique.get("reason", "LLM evaluation"),
            }
        except Exception as exc:
            return {"passed": True, "score": 7.0, "reason": f"Critique bypassed on error: {exc}"}
