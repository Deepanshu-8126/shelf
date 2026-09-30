from __future__ import annotations

import statistics
from datetime import date, timedelta
from typing import Any

from .db import get_channel

PLACEHOLDER_NICHES = {"awaiting market scan", "selected by the market scout", "not selected yet"}


def _next_monday(start: date) -> date:
    delta = (7 - start.weekday()) % 7
    return start + timedelta(days=delta or 7)


def _owner_baseline(channel_id: str, analytics: list[dict[str, Any]]) -> dict[str, Any]:
    rows = [row for row in analytics if row.get("channel_id") == channel_id]
    views = [int(row.get("views") or 0) for row in rows]
    durations = [float(row["average_view_duration_seconds"]) for row in rows
                 if row.get("average_view_duration_seconds") is not None]
    result: dict[str, Any] = {"snapshot_count": len(rows), "status": "no owner analytics yet"}
    if rows:
        result["status"] = "exploratory own-channel baseline; pulls may overlap in date range"
        result["median_views_per_pull"] = int(statistics.median(views)) if views else None
        result["median_average_view_duration_seconds"] = round(statistics.median(durations), 1) if durations else None
        result["latest_snapshot_date"] = max(str(row.get("snapshot_date", "")) for row in rows)
    return result


def build_strategy(channel_id: str, scan: dict[str, Any] | None,
                   analytics: list[dict[str, Any]] | None = None,
                   today: date | None = None) -> dict[str, Any]:
    channel = get_channel(channel_id)
    if not channel:
        raise ValueError("Unknown channel slot")
    scan = scan or {"mode": "demo", "candidates": []}
    candidates = scan.get("candidates", []) or []
    top = candidates[0] if candidates else None
    configured_niche = str(channel.get("niche", "")).strip()
    selected = next((item for item in candidates if item.get("name", "").lower() == configured_niche.lower()), None)
    if configured_niche.lower() in PLACEHOLDER_NICHES or not configured_niche:
        selected = top
    niche = (selected or top or {}).get("name") or configured_niche or "Undecided · gather a live market sample"
    mode = str(scan.get("mode", "demo"))
    candidate_evidence = selected or top or {}
    provisional = (mode != "live" or
                   (not selected and configured_niche.lower() not in PLACEHOLDER_NICHES) or
                   not int(candidate_evidence.get("sample_count", 0) or 0))
    if not selected and top and configured_niche.lower() not in PLACEHOLDER_NICHES:
        selection_note = "Configured channel niche is not one of today's seed candidates; plan uses its label and the scout's top candidate only as a comparison signal."
    elif mode != "live":
        selection_note = "Provisional: demo fixtures are not market evidence. Run a live scan before committing the channel niche."
    elif not int(candidate_evidence.get("sample_count", 0) or 0):
        selection_note = "Insufficient live sample: keep the niche provisional and inspect API errors before deciding."
    else:
        selection_note = "A test hypothesis, not a permanent niche decision or a revenue forecast."
    summaries = candidate_evidence.get("cohort_summary", {})
    source_urls = [str(row.get("url", "")) for row in candidate_evidence.get("evidence", []) if row.get("url")][:8]
    today = today or date.today()
    first_monday = _next_monday(today)
    calendar_specs = [
        (0, "A clear beginner's map", f"A source-led introduction to {niche}", "Define one viewer question and explain the key terms without promising an outcome."),
        (3, "Compare the trade-offs", f"How to compare choices in {niche} using transparent criteria", "Show a reusable comparison framework; support each factual point with primary sources."),
        (7, "Investigate a specific case", f"A documented case study in {niche}: what the evidence supports", "Choose a public, well-documented example; include limitations and a counterpoint."),
        (10, "Answer the next question", f"What people should verify before acting on {niche}", "Use questions from viewers or search results; separate established facts from open questions."),
    ]
    calendar = []
    for index, (offset, pillar, topic, angle) in enumerate(calendar_specs, start=1):
        calendar.append({
            "slot": index,
            "date": (first_monday + timedelta(days=offset)).isoformat(),
            "format": "Documentary",
            "pillar": pillar,
            "topic": topic,
            "angle": angle,
            "research_check": "Capture at least two reliable sources, record the date/geography, and note a counterexample or limitation.",
            "success_metrics": ["YouTube Studio impressions and click-through rate (manual)",
                                "Owner Analytics average view duration", "Audience geography and viewer questions (manual)"],
            "status": "idea only · not scheduled or approved",
        })

    analytics = analytics or []
    baseline = _owner_baseline(channel_id, analytics)
    repeatability = candidate_evidence.get("sustainability_signal", "not assessed")
    market_evidence = {
        "mode": mode,
        "candidate": niche,
        "screening_score": candidate_evidence.get("score"),
        "sample_count": candidate_evidence.get("sample_count", 0),
        "confidence": candidate_evidence.get("confidence", "low · no scan"),
        "repeatability_signal": repeatability,
        "publication_cohorts": summaries,
        "sample_video_urls": source_urls,
        "interpretation": "A small public search sample is a shortlist signal; lifetime public views do not reveal actual recent momentum or RPM.",
    }
    return {
        "channel_id": channel_id,
        "channel_name": channel.get("name", channel_id),
        "created_date": today.isoformat(),
        "horizon_days": 14,
        "status": "provisional · demo evidence" if provisional else "live-sample hypothesis",
        "decision_note": selection_note,
        "audience": f"{channel.get('audience_country', 'US')} · {channel.get('language', 'en-US')}",
        "recommended_niche": niche,
        "positioning_hypothesis": f"Make {niche} useful to a US viewer by answering one specific question per video, showing sources on screen, and stating uncertainty plainly.",
        "market_evidence": market_evidence,
        "content_pillars": [
            {"name": "Foundations", "purpose": "Help a new viewer understand the terms, choices and stakes.", "evidence_rule": "Use primary/official sources for factual claims."},
            {"name": "Comparisons", "purpose": "Explain trade-offs with transparent criteria, not unsupported rankings.", "evidence_rule": "State what is and is not being compared."},
            {"name": "Documented cases", "purpose": "Use a verifiable example to make the idea concrete.", "evidence_rule": "Keep a source log and include limitations or counterevidence."},
        ],
        "calendar": calendar,
        "experiments": [
            {
                "name": "Opening structure",
                "hypothesis": "A specific question plus a concise preview may help the right viewers understand the promise quickly.",
                "change_one_thing": "Compare question-first openings across two otherwise similar videos.",
                "measure": "Average view duration from owner Analytics; inspect the retention graph in Studio manually.",
                "guardrail": "Do not infer causality from two videos; record topic, length and date as possible confounders.",
            },
            {
                "name": "Packaging clarity",
                "hypothesis": "A concrete viewer outcome may make the title/thumbnail promise easier to recognize.",
                "change_one_thing": "For each video, save two title/thumbnail concepts; use YouTube Studio's native testing if available.",
                "measure": "Studio impressions and click-through rate; the public API does not provide a general automated thumbnail A/B test.",
                "guardrail": "Keep claims accurate; never change metadata to promise results the video does not deliver.",
            },
            {
                "name": "Audience fit",
                "hypothesis": "Examples, terminology and units should feel natural to the intended US audience.",
                "change_one_thing": "Use one US-context example and one plain-language explanation per episode.",
                "measure": "Owner Analytics geography, comments/questions and returning-viewer signals where available.",
                "guardrail": "US targeting does not guarantee US viewership, monetization eligibility or a particular RPM.",
            },
        ],
        "owner_analytics_baseline": baseline,
        "review_loop": [
            "After each upload, pull owner-only analytics for a consistent date range and record the date range.",
            "Review impressions/CTR and retention in YouTube Studio; these are not fully represented by this API pull.",
            "After four original uploads, compare against this channel's own baseline and decide whether to refine, continue or stop.",
            "Repeat the market scan weekly; this app does not infer six-month sustainability from one scan.",
        ],
        "limits": [
            "Calendar entries are research ideas, not verified scripts, scheduled jobs or approved posts.",
            "The scan uses public search samples; the sustainability field is a repeatability proxy, not a prediction.",
            "No RPM, revenue, growth multiplier or YPP eligibility is guaranteed.",
        ],
    }
