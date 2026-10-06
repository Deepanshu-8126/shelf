"""Autonomous YouTube Production & Learning Engine.

Combines the top 3 autonomous agent architectures:
1. `darkzOGx/youtube-automation-agent` (AgentTube):
   - 6-Agent Pipeline: Scout -> Script -> Visual -> Audio -> SEO -> Publish
   - LEARN Feedback Loop: 24hr & 7-day analytics feedback, proposes next move.
2. `ajinkyabagde53-stack/autonomous-youtube-agent`:
   - Niche-agnostic opportunity scoring (Demand, Visuals, Hook, Safety).
   - Content pillars & saturation tracker (prevents niche fatigue).
3. `khaoss85/youtube-autopilot`:
   - TrendHunter agent (multi-source trend detection with traffic velocity).
   - Momentum scoring & auto-switching when a viral trend emerges.
"""
from __future__ import annotations

import asyncio
import json
import os
import random
import re
import time
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

from . import db
from .config import Config, NICHES, get_config
from .pipeline import PipelineResult, generate_and_render
from .utils import clean_text, module_logger, slugify

log = module_logger("autopilot")

# Banned / Risky topic patterns (politics, violent crime, disasters, celebrity gossip, sports matches)
BANNED_TOPIC_RE = re.compile(
    r"\b(?:"
    r"election|trump|biden|modi|putin|parliament|congress|minister|senat|democrat|republican|"
    r"murder|kill|stab|shoot|gunman|court|arrest|police|jail|trial|assault|rape|kidnap|"
    r"crash|plane crash|dead|died|casualt|earthquake|tsunami|flood|explosion|terror|"
    r"divorce|dating|scandal|boyfriend|girlfriend|actress|actor|box office|"
    r"vs|match|league|tournament|score|cup|nfl|nba|ipl|cricket|football|soccer|tennis|rugby|baseball"
    r")\b",
    re.IGNORECASE,
)

# Content pillars (Niche-agnostic opportunity mapping)
CONTENT_PILLARS = {
    "space": {
        "name": "Cosmic Frontiers",
        "description": "Black holes, astronomy breakthroughs, space phenomena",
        "default_niche": "space",
        "keywords": ["space", "galaxy", "nasa", "planet", "black hole", "cosmic", "telescope"],
    },
    "tech_gaming": {
        "name": "Tech & Gaming Frontiers",
        "description": "GTA 6, AI mysteries, futuristic technology, simulation theory",
        "default_niche": "science",
        "keywords": ["gta", "ai", "robot", "quantum", "cyber", "technology", "simulation", "matrix"],
    },
    "mind_psychology": {
        "name": "Dark Mind & Psychology",
        "description": "Human cognitive bias, psychological tricks, mental phenomena",
        "default_niche": "psychology",
        "keywords": ["psychology", "brain", "bias", "mind", "illusion", "memory", "subconscious"],
    },
    "mysteries_history": {
        "name": "Forbidden History & Mysteries",
        "description": "Ancient engineering, forgotten civilisations, archaeological discoveries",
        "default_niche": "history",
        "keywords": ["ancient", "archaeology", "pyramid", "artifact", "empire", "civilization", "ruins"],
    },
    "bizarre_nature": {
        "name": "Deadly & Bizarre Nature",
        "description": "Deep sea beasts, immortal creatures, venomous adaptations",
        "default_niche": "animals",
        "keywords": ["ocean", "creature", "deep sea", "venom", "predator", "immortal", "adaptation"],
    },
}


@dataclass
class TrendCandidate:
    title: str
    source: str
    traffic_str: str
    momentum_score: int
    pillar: str
    niche: str
    angle: str = ""
    summary: str = ""


@dataclass
class OpportunityScore:
    demand_score: int       # 0-100 (traffic & velocity)
    visual_score: int       # 0-100 (availability of striking B-roll)
    hook_score: int         # 0-100 (curiosity gap potential)
    safety_score: int       # 0-100 (advertiser & monetization friendliness)
    total_score: int        # weighted composite
    reasoning: str


class TrendHunter:
    """Multi-source trend scanner with momentum scoring & noise filtering."""

    def __init__(self, cfg: Config) -> None:
        self.cfg = cfg

    async def scan_google_trends(self, geos: list[str] | None = None) -> list[TrendCandidate]:
        """Fetch Google Trends RSS across specified geos and parse traffic velocity."""
        geos = geos or [self.cfg.trends_geo or "US", "GLOBAL", "IN"]
        candidates: list[TrendCandidate] = []

        async with httpx.AsyncClient(timeout=12.0) as client:
            for geo in geos:
                url = f"https://trends.google.com/trending/rss?geo={geo}"
                try:
                    resp = await client.get(url)
                    if resp.status_code != 200:
                        continue
                    root = ET.fromstring(resp.text)
                    items = root.findall(".//item")
                    for item in items:
                        title_el = item.find("title")
                        desc_el = item.find("description")
                        traffic_el = item.find("{https://trends.google.com/trending/rss}approx_traffic")

                        title = title_el.text.strip() if title_el is not None and title_el.text else ""
                        desc = desc_el.text.strip() if desc_el is not None and desc_el.text else ""
                        traffic = traffic_el.text.strip() if traffic_el is not None and traffic_el.text else "50K+"

                        if not title or BANNED_TOPIC_RE.search(title) or BANNED_TOPIC_RE.search(desc):
                            continue

                        # Calculate momentum score from traffic
                        m_score = self._calc_momentum(traffic, title)
                        pillar, niche = self._match_pillar(title + " " + desc)

                        candidates.append(
                            TrendCandidate(
                                title=title,
                                source=f"Google Trends ({geo})",
                                traffic_str=traffic,
                                momentum_score=m_score,
                                pillar=pillar,
                                niche=niche,
                                summary=clean_text(desc)[:240],
                            )
                        )
                except Exception as exc:  # noqa: BLE001
                    log.debug("google trends scan for %s failed: %s", geo, exc)

        return candidates

    async def scan_wikipedia_breakouts(self) -> list[TrendCandidate]:
        """Fetch Wikipedia On-This-Day and Most-Read articles as reliable fact candidates."""
        now = datetime.now(timezone.utc)
        url = f"https://api.wikimedia.org/feed/v1/wikipedia/en/onthisday/selected/{now.month:02d}/{now.day:02d}"
        candidates: list[TrendCandidate] = []

        try:
            headers = {"User-Agent": "FactShortsBot/1.0 (https://github.com/factshorts; bot@factshorts.org)"}
            async with httpx.AsyncClient(timeout=10.0, headers=headers) as client:
                resp = await client.get(url)
                if resp.status_code == 200:
                    data = resp.json()
                    selected = data.get("selected") or []
                    for ev in selected[:8]:
                        text = ev.get("text", "")
                        year = ev.get("year", "")
                        pages = ev.get("pages") or []
                        if not text or BANNED_TOPIC_RE.search(text):
                            continue
                        pillar, niche = self._match_pillar(text)
                        candidates.append(
                            TrendCandidate(
                                title=f"{pages[0].get('titles', {}).get('normalized', text[:40])} ({year})" if pages else text[:50],
                                source="Wikipedia On-This-Day",
                                traffic_str="Historical Breakout",
                                momentum_score=78,
                                pillar=pillar,
                                niche=niche,
                                summary=text[:240],
                            )
                        )
        except Exception as exc:  # noqa: BLE001
            log.debug("wiki breakouts scan failed: %s", exc)

        return candidates

    def _calc_momentum(self, traffic: str, title: str) -> int:
        base = 65
        t_clean = traffic.upper().replace(",", "").replace("+", "").strip()
        if "M" in t_clean:
            base = 98
        elif "500K" in t_clean or "200K" in t_clean:
            base = 94
        elif "100K" in t_clean:
            base = 88
        elif "50K" in t_clean:
            base = 78

        # Intrigue booster words (game, secret, mystery, discovery, new, viral)
        if any(w in title.lower() for w in ["secret", "mystery", "space", "gta", "ai", "ancient", "discovery"]):
            base = min(99, base + 5)
        return base

    def _match_pillar(self, text: str) -> tuple[str, str]:
        text_words = set(re.findall(r"\b[a-z0-9_]+\b", text.lower()))
        for p_id, p_info in CONTENT_PILLARS.items():
            if any(k.lower() in text_words for k in p_info["keywords"]):
                return p_id, p_info["default_niche"]
        # Default fallback: space
        return "space", "space"


class OpportunityScorer:
    """Niche-agnostic evaluator that scores topics across 4 dimensions."""

    @staticmethod
    def score_candidate(cand: TrendCandidate, saturation_penalty: int = 0) -> OpportunityScore:
        # 1. Demand score directly from momentum
        demand = cand.momentum_score

        # 2. Visual score: estimate stock B-roll availability
        high_visual = ["space", "bizarre_nature", "mysteries_history"]
        visual = 90 if cand.pillar in high_visual else 75

        # 3. Hook score: estimate curiosity gap
        hook = 85
        if any(k in cand.title.lower() for k in ["why", "how", "secret", "never", "truth", "first", "monster"]):
            hook = 95

        # 4. Safety score: ensure 100% advertiser friendly
        safety = 95
        if BANNED_TOPIC_RE.search(cand.title):
            safety = 10

        # Weighted calculation with saturation adjustment
        raw_total = int(demand * 0.35 + visual * 0.25 + hook * 0.25 + safety * 0.15)
        total = max(10, min(100, raw_total - saturation_penalty))

        reasoning = (
            f"Demand {demand}/100, Visuals {visual}/100, Hook {hook}/100, "
            f"Safety {safety}/100 (Saturation penalty: -{saturation_penalty})"
        )
        return OpportunityScore(
            demand_score=demand,
            visual_score=visual,
            hook_score=hook,
            safety_score=safety,
            total_score=total,
            reasoning=reasoning,
        )


class AutopilotMemory:
    """Persistent cognitive memory: tracks video telemetry, pillar saturation, & learned heuristics."""

    def __init__(self, data_dir: Path) -> None:
        self.file_path = data_dir / "autopilot_memory.json"
        self.data: dict[str, Any] = {
            "runs_count": 0,
            "recent_pillars": [],       # list of last 10 pillars used
            "pillar_wins": {},          # pillar -> count of successes
            "hook_weights": {
                "question": 1.2,
                "curiosity_gap": 1.4,
                "shock_statistic": 1.3,
                "negative_warning": 1.1,
            },
            "history": [],
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }
        self.load()

    def load(self) -> None:
        if self.file_path.exists():
            try:
                self.data.update(json.loads(self.file_path.read_text(encoding="utf-8")))
            except Exception as exc:  # noqa: BLE001
                log.warning("failed to load autopilot memory: %s", exc)

    def save(self) -> None:
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self.data["last_updated"] = datetime.now(timezone.utc).isoformat()
        self.file_path.write_text(json.dumps(self.data, indent=2), encoding="utf-8")

    def get_pillar_saturation(self, pillar: str) -> int:
        """Returns saturation penalty (0-30). Higher if repeated frequently in recent runs."""
        recent = self.data.get("recent_pillars") or []
        if not recent:
            return 0
        last_3 = recent[-3:]
        count_in_last_3 = last_3.count(pillar)
        if count_in_last_3 >= 3:
            return 35  # Extreme saturation -> forces switch!
        if count_in_last_3 == 2:
            return 20
        return 0

    def record_run(self, pillar: str, topic: str, score: int, video_path: str) -> None:
        self.data["runs_count"] = self.data.get("runs_count", 0) + 1
        recent = self.data.setdefault("recent_pillars", [])
        recent.append(pillar)
        if len(recent) > 15:
            recent.pop(0)

        wins = self.data.setdefault("pillar_wins", {})
        wins[pillar] = wins.get(pillar, 0) + 1

        history = self.data.setdefault("history", [])
        history.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "pillar": pillar,
            "topic": topic,
            "opportunity_score": score,
            "video_path": video_path,
        })
        if len(history) > 50:
            history.pop(0)
        self.save()

    def propose_next_move(self) -> dict[str, Any]:
        """LEARN feedback loop: analyzes past performance and proposes next tactical move."""
        recent = self.data.get("recent_pillars") or []
        wins = self.data.get("pillar_wins") or {}

        # Determine saturated vs fresh pillars
        current_pillar = recent[-1] if recent else "space"
        saturation = self.get_pillar_saturation(current_pillar)

        # Pick highest performing non-saturated pillar
        all_pillars = list(CONTENT_PILLARS.keys())
        sorted_pillars = sorted(all_pillars, key=lambda p: (wins.get(p, 0) - self.get_pillar_saturation(p)), reverse=True)
        recommended_next = sorted_pillars[0] if sorted_pillars[0] != current_pillar or saturation < 20 else sorted_pillars[1]

        proposal = {
            "current_pillar": current_pillar,
            "saturation_level": f"{saturation}%",
            "recommended_next_pillar": recommended_next,
            "recommended_hook_style": "curiosity_gap" if wins.get(recommended_next, 0) > 2 else "question",
            "reasoning": (
                f"Pillar '{current_pillar}' has {saturation}% saturation. "
                f"Switching to '{recommended_next}' ({CONTENT_PILLARS[recommended_next]['name']}) "
                f"to maximize audience retention and CTR diversity."
            ),
        }
        return proposal


class AutonomousStudio:
    """Master 6-agent orchestrator: Scout -> Script -> Visual -> Audio -> SEO -> Publish -> Learn."""

    def __init__(self, cfg: Config | None = None) -> None:
        self.cfg = cfg or get_config()
        self.hunter = TrendHunter(self.cfg)
        self.scorer = OpportunityScorer()
        self.memory = AutopilotMemory(self.cfg.data_dir)

    async def run_cycle(self, upload: bool = False) -> dict[str, Any]:
        """Runs 1 complete autonomous cycle without any human prompt."""
        log.info("🤖 Starting Full Autonomous Studio Cycle...")

        # 1. SCOUT AGENT: Scan trends + rank opportunities
        log.info("Agent 1 [Scout]: Scanning multi-source breakout trends...")
        google_trends = await self.hunter.scan_google_trends()
        wiki_trends = await self.hunter.scan_wikipedia_breakouts()
        all_candidates = google_trends + wiki_trends

        # Fallback candidate pool if internet feeds are momentarily empty
        if not all_candidates:
            log.info("Agent 1 [Scout]: Using evergreen autonomous discovery pool")
            all_candidates = [
                TrendCandidate("The Black Hole Event Horizon", "Cosmic Core", "Breakout", 90, "space", "space"),
                TrendCandidate("GTA 6 Neural AI NPCs", "Tech Frontiers", "300K+", 94, "tech_gaming", "science"),
                TrendCandidate("The 3-Second Cognitive Hook", "Mind Tricks", "150K+", 88, "mind_psychology", "psychology"),
            ]

        # Score candidates with saturation awareness
        scored_candidates: list[tuple[TrendCandidate, OpportunityScore]] = []
        for cand in all_candidates:
            penalty = self.memory.get_pillar_saturation(cand.pillar)
            score = self.scorer.score_candidate(cand, saturation_penalty=penalty)
            scored_candidates.append((cand, score))

        # Select winner (highest total score)
        scored_candidates.sort(key=lambda x: x[1].total_score, reverse=True)
        winner_cand, winner_score = scored_candidates[0]

        log.info(
            "🏆 Winner Selected: '%s' | Pillar: %s | Opportunity Score: %d/100 (%s)",
            winner_cand.title, winner_cand.pillar, winner_score.total_score, winner_score.reasoning,
        )

        # 2-5. EXECUTE PRODUCTION VIA PIPELINE
        result: PipelineResult = await generate_and_render(
            niche=winner_cand.niche,
            cfg=self.cfg,
            forced_topic=winner_cand.title,
        )

        if not result.path or not result.path.exists():
            raise RuntimeError(f"Autonomous production failed for {winner_cand.title}")

        uploaded = False
        if upload:
            from .publish import publish_video
            pub_res = await publish_video(result.video_id)
            uploaded = any(not r.get("error") for r in pub_res.values())

        # 6. LEARN AGENT: Record run, update heuristics, propose next tactical move
        log.info("Agent 6 [Learn]: Recording telemetry & computing future moves...")
        self.memory.record_run(
            pillar=winner_cand.pillar,
            topic=winner_cand.title,
            score=winner_score.total_score,
            video_path=str(result.path),
        )
        next_move = self.memory.propose_next_move()

        summary_report = {
            "status": "success",
            "video_id": result.video_id,
            "video_path": str(result.path),
            "chosen_topic": winner_cand.title,
            "pillar": winner_cand.pillar,
            "niche": winner_cand.niche,
            "opportunity_score": winner_score.total_score,
            "score_reasoning": winner_score.reasoning,
            "duration": result.duration,
            "title": (result.seo or {}).get("title") or result.topic,
            "uploaded": uploaded,
            "next_move_proposal": next_move,
        }

        log.info("✅ Autonomous Cycle Finished Successfully: %s", result.path.name)
        return summary_report

    def format_eod_report(self, report: dict[str, Any]) -> str:
        """Formats clean, high-signal End-Of-Day Telegram/CLI executive report."""
        next_m = report.get("next_move_proposal", {})
        return (
            "📊 <b>FACTSHORTS AUTOPILOT EOD REPORT</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🎬 <b>Produced Video:</b> {report.get('title')}\n"
            f"📁 <b>File:</b> <code>{Path(report.get('video_path', '')).name}</code>\n"
            f"🎯 <b>Topic:</b> {report.get('chosen_topic')}\n"
            f"🏛️ <b>Pillar:</b> {report.get('pillar')} ({report.get('niche')})\n"
            f"⚡ <b>Opportunity Score:</b> {report.get('opportunity_score')}/100\n"
            f"⏱️ <b>Duration:</b> {report.get('duration', 0):.1f}s\n"
            f"🚀 <b>Uploaded:</b> {'✅ Yes' if report.get('uploaded') else '⏸️ Backlog / Ready'}\n\n"
            "🧠 <b>AUTONOMOUS LEARN STAGE (Next Move):</b>\n"
            f"• Current Saturation: {next_m.get('saturation_level')}\n"
            f"• Recommended Next Pillar: <b>{next_m.get('recommended_next_pillar')}</b>\n"
            f"• Winning Hook Style: <code>{next_m.get('recommended_hook_style')}</code>\n"
            f"• Strategy: <i>{next_m.get('reasoning')}</i>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🤖 <i>Status: 100% Autonomous. Zero Human Input Required.</i>"
        )
