from __future__ import annotations

import json
import math
import statistics
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from typing import Any

from .config import env

# These are deliberately cohort samples, not a claim to enumerate every video in a niche.
WINDOWS = [
    {"key": "0-30", "label": "0–30 days", "start_days": 0, "end_days": 30},
    {"key": "31-90", "label": "31–90 days", "start_days": 31, "end_days": 90},
    {"key": "91-180", "label": "91–180 days", "start_days": 91, "end_days": 180},
]
RESULTS_PER_COHORT = 25
OUTLIER_SUBSCRIBER_MULTIPLE = 3.0  # heuristic only; not an industry benchmark

SEEDS = [
    {"name": "Practical AI & software workflows", "query": "AI tools productivity workflow tutorial", "monetization_fit": 78, "production_ease": 82, "rights_risk": 12},
    {"name": "US career skills & workplace explainers", "query": "US career skills interview workplace advice", "monetization_fit": 72, "production_ease": 76, "rights_risk": 10},
    {"name": "Consumer technology explainers", "query": "technology explained consumer apps AI", "monetization_fit": 74, "production_ease": 70, "rights_risk": 16},
    {"name": "Personal finance fundamentals", "query": "US credit score budgeting finance education", "monetization_fit": 88, "production_ease": 68, "rights_risk": 42},
]


def demo_candidates() -> list[dict]:
    # Illustrative UI-only scores. Never presented as live research or RPM data.
    demo = [
        ("Practical AI & software workflows", 84, 81, 62, 79, 82, "Demo score only; connect YouTube Data API for live public metadata."),
        ("US career skills & workplace explainers", 77, 72, 58, 72, 76, "Demo score only; validate with a live sample and a 30-day pilot."),
        ("Consumer technology explainers", 74, 70, 68, 74, 70, "Demo score only; competition and audience retention need live testing."),
        ("Personal finance fundamentals", 70, 76, 72, 88, 68, "Demo score only; higher fact-checking and compliance burden."),
    ]
    result = []
    for name, score, demand, breakout, monetization, ease, note in demo:
        result.append({
            "name": name, "score": score, "demand": demand, "breakout": breakout,
            "competition": 100 - ease, "monetization_fit": monetization,
            "commercial_intent_prior": monetization, "production_ease": ease,
            "sustainability": 0, "sustainability_signal": "not assessed · demo",
            "sample_count": 0, "unique_channels": 0, "median_views": None,
            "median_views_per_day": None, "cohort_summary": {}, "evidence": [],
            "confidence": "low · demo", "mode": "demo", "note": note,
            "methodology": {"source": "illustrative fixture", "sampling": "No live data collected."},
        })
    return result


def _get_json(url: str) -> dict:
    request = urllib.request.Request(url, headers={"User-Agent": "CreatorOps-Research/0.2"})
    with urllib.request.urlopen(request, timeout=25) as response:
        return json.loads(response.read().decode("utf-8"))


def _api(endpoint: str, params: dict) -> dict:
    key = env("YOUTUBE_DATA_API_KEY")
    if not key:
        raise RuntimeError("YOUTUBE_DATA_API_KEY is not configured")
    query = urllib.parse.urlencode({**params, "key": key})
    return _get_json(f"https://www.googleapis.com/youtube/v3/{endpoint}?{query}")


def _median(values: list[float]) -> float | None:
    return float(statistics.median(values)) if values else None


def cohort_summaries(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Summarize sampled publication cohorts using lifetime views normalized by video age.

    The Data API does not return historical daily view curves. Therefore `views_per_day`
    is lifetime public views divided by age, not views actually earned during a cohort.
    """
    summaries: dict[str, dict[str, Any]] = {}
    for window in WINDOWS:
        cohort = [r for r in rows if r.get("cohort") == window["key"]]
        ratios = [float(r["view_subscriber_ratio"]) for r in cohort if r.get("view_subscriber_ratio") is not None]
        channels = {r.get("channel_id") or r.get("channel") for r in cohort if r.get("channel_id") or r.get("channel")}
        outliers = [r for r in cohort if r.get("view_subscriber_ratio") is not None
                    and float(r["view_subscriber_ratio"]) >= OUTLIER_SUBSCRIBER_MULTIPLE]
        summaries[window["key"]] = {
            "label": window["label"],
            "sample_count": len(cohort),
            "unique_channels": len(channels),
            "median_views": int(_median([float(r.get("views", 0)) for r in cohort]) or 0),
            "median_lifetime_views_per_day": round(_median([float(r.get("views_per_day", 0)) for r in cohort]) or 0, 1),
            "median_view_subscriber_ratio": round(_median(ratios), 2) if ratios else None,
            "heuristic_outlier_videos": len(outliers),
            "heuristic_outlier_channels": len({r.get("channel_id") or r.get("channel") for r in outliers}),
        }
    return summaries


def _sustainability_signal(summaries: dict[str, dict[str, Any]], unique_breakout_channels: int) -> tuple[int, str]:
    populated = [s for s in summaries.values() if s["sample_count"]]
    breakout_windows = sum(1 for s in summaries.values() if s["heuristic_outlier_videos"])
    cohort_coverage = len(populated)
    coverage_score = 25 * cohort_coverage / len(WINDOWS)
    repeat_score = 40 * breakout_windows / len(WINDOWS)
    diversity_score = 35 * min(1.0, unique_breakout_channels / 3)
    score = round(coverage_score + repeat_score + diversity_score)
    if cohort_coverage < 2 or unique_breakout_channels < 2:
        label = "not established · thin or concentrated sample"
    elif breakout_windows >= 2 and unique_breakout_channels >= 3:
        label = "repeatability signal across sampled cohorts"
    else:
        label = "mixed · repeatability not established"
    return score, label


def _score_candidate(seed: dict, rows: list[dict[str, Any]], sampled_at: str,
                     window_errors: list[str] | None = None) -> dict[str, Any]:
    summaries = cohort_summaries(rows)
    sample_count = len(rows)
    unique_channels = len({r.get("channel_id") or r.get("channel") for r in rows if r.get("channel_id") or r.get("channel")})
    breakout_rows = [r for r in rows if r.get("view_subscriber_ratio") is not None
                     and float(r["view_subscriber_ratio"]) >= OUTLIER_SUBSCRIBER_MULTIPLE]
    unique_breakout_channels = len({r.get("channel_id") or r.get("channel") for r in breakout_rows})
    recent_daily = summaries["0-30"]["median_lifetime_views_per_day"]
    all_ratios = [float(r["view_subscriber_ratio"]) for r in rows if r.get("view_subscriber_ratio") is not None]
    median_ratio = _median(all_ratios) or 0.0
    median_views = int(_median([float(r.get("views", 0)) for r in rows]) or 0)

    # These are ranking heuristics, not market-size, revenue, or future-growth estimates.
    demand = max(0, min(100, round(18 + 17 * math.log10(float(recent_daily or 0) + 1)))) if sample_count else 0
    breakout = max(0, min(100, round(20 + 24 * math.log10(max(median_ratio, 0.0) + 0.2)
                                      + min(20, unique_breakout_channels * 5)))) if sample_count else 0
    competition = max(0, min(100, round(100 * unique_channels / max(1, sample_count))))
    sustainability, sustainability_label = _sustainability_signal(summaries, unique_breakout_channels)
    score = (round(0.25 * demand + 0.25 * breakout + 0.15 * (100 - competition)
                   + 0.15 * seed["monetization_fit"] + 0.10 * seed["production_ease"]
                   + 0.10 * sustainability) if sample_count else 0)
    if sample_count >= 30 and len([s for s in summaries.values() if s["sample_count"]]) == 3:
        confidence = "medium · 180-day cohorts, non-random sample"
    elif sample_count >= 12:
        confidence = "low-medium · partial/small cohort sample"
    elif sample_count:
        confidence = "low · small sample"
    else:
        confidence = "low · no sample"

    # Prefer repeated, smaller-channel outliers for inspection, then other public signals.
    rows.sort(key=lambda r: (
        float(r.get("view_subscriber_ratio") or 0),
        float(r.get("views_per_day") or 0),
    ), reverse=True)
    note = (
        "Public-metadata screening proxy only. 3× subscriber outliers and lifetime views/day are heuristics; "
        "results are a relevance/query sample, not a census or proof of future demand/RPM."
    )
    if window_errors:
        note += " Some cohort requests failed; inspect scan notes."
    return {
        "name": seed["name"], "score": score, "demand": demand, "breakout": breakout,
        "competition": competition, "monetization_fit": seed["monetization_fit"],
        "commercial_intent_prior": seed["monetization_fit"], "production_ease": seed["production_ease"],
        "sustainability": sustainability, "sustainability_signal": sustainability_label,
        "sample_count": sample_count, "unique_channels": unique_channels,
        "median_views": median_views, "median_views_per_day": round(float(recent_daily or 0)),
        "cohort_summary": summaries, "heuristic_outlier_count": len(breakout_rows),
        "heuristic_outlier_channels": unique_breakout_channels,
        "evidence": rows[:15], "confidence": confidence, "mode": "live", "note": note,
        "methodology": {
            "source": "YouTube Data API v3 public search/video/channel metadata",
            "sampled_at": sampled_at,
            "query": seed["query"],
            "region_filter": "US",
            "language_filter": "en",
            "cohorts": [{"key": w["key"], "label": w["label"], "max_results": RESULTS_PER_COHORT} for w in WINDOWS],
            "sampling": "Most-recent matching public videos per publication cohort; search results are not a random or complete market sample.",
            "view_metric": "Lifetime public views at scan time; views/day divides lifetime views by video age. It is not historical daily view velocity.",
            "outlier_rule": f"Heuristic: views/current visible channel subscribers >= {OUTLIER_SUBSCRIBER_MULTIPLE:g}; unavailable where subscriber counts are hidden.",
            "commercial_intent_prior": "Hand-set qualitative prior; not measured CPM, RPM, advertiser bids, or income.",
            "window_errors": window_errors or [],
        },
    }


def _live_candidate(seed: dict, now: datetime | None = None) -> dict:
    now = now or datetime.now(timezone.utc)
    sampled_at = now.replace(microsecond=0).isoformat().replace("+00:00", "Z")
    found: dict[str, dict[str, Any]] = {}
    window_errors: list[str] = []
    for window in WINDOWS:
        after = now - timedelta(days=window["end_days"])
        before = now - timedelta(days=window["start_days"])
        params = {
            "part": "snippet", "q": seed["query"], "type": "video", "order": "date",
            "maxResults": RESULTS_PER_COHORT,
            "publishedAfter": after.replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            "publishedBefore": before.replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            "regionCode": "US", "relevanceLanguage": "en",
        }
        try:
            search = _api("search", params)
        except Exception as exc:
            window_errors.append(f"{window['label']}: {type(exc).__name__}: {exc}")
            continue
        for item in search.get("items", []):
            video_id = item.get("id", {}).get("videoId")
            snippet = item.get("snippet", {})
            if not video_id or video_id in found:
                continue
            found[video_id] = {
                "video_id": video_id,
                "title": snippet.get("title", ""),
                "url": f"https://www.youtube.com/watch?v={video_id}",
                "channel": snippet.get("channelTitle", ""),
                "channel_id": snippet.get("channelId", ""),
                "published_at": snippet.get("publishedAt", ""),
                "cohort": window["key"],
            }

    ids = list(found)
    video_items: list[dict[str, Any]] = []
    for offset in range(0, len(ids), 50):
        batch = ids[offset:offset + 50]
        if batch:
            try:
                video_items.extend(_api("videos", {"part": "snippet,statistics,contentDetails", "id": ",".join(batch)}).get("items", []))
            except Exception as exc:
                window_errors.append(f"Video statistics: {type(exc).__name__}: {exc}")

    channel_ids = list({item.get("snippet", {}).get("channelId", "") for item in video_items
                        if item.get("snippet", {}).get("channelId")})
    channel_subs: dict[str, int] = {}
    for offset in range(0, len(channel_ids), 50):
        batch = channel_ids[offset:offset + 50]
        if not batch:
            continue
        try:
            payload = _api("channels", {"part": "statistics", "id": ",".join(batch)})
            for channel in payload.get("items", []):
                stats = channel.get("statistics", {})
                if not stats.get("hiddenSubscriberCount") and "subscriberCount" in stats:
                    channel_subs[channel["id"]] = int(stats.get("subscriberCount", 0))
        except Exception as exc:
            window_errors.append(f"Channel statistics: {type(exc).__name__}: {exc}")

    rows: list[dict[str, Any]] = []
    for item in video_items:
        stats = item.get("statistics", {})
        snippet = item.get("snippet", {})
        video_id = item.get("id", "")
        base = found.get(video_id, {})
        views = int(stats.get("viewCount", 0))
        published = snippet.get("publishedAt", base.get("published_at", ""))
        try:
            age_days = max(1, (now - datetime.fromisoformat(published.replace("Z", "+00:00"))).days)
        except Exception:
            age_days = 30
        channel_id = snippet.get("channelId", base.get("channel_id", ""))
        subs = channel_subs.get(channel_id)
        rows.append({
            **base,
            "title": snippet.get("title", base.get("title", "")),
            "channel": snippet.get("channelTitle", base.get("channel", "")),
            "channel_id": channel_id,
            "published_at": published,
            "views": views,
            "age_days": age_days,
            "views_per_day": round(views / age_days, 1),
            "subscriber_count": subs,
            "view_subscriber_ratio": (views / subs) if subs and subs > 0 else None,
        })
    return _score_candidate(seed, rows, sampled_at, window_errors)


def scan_market() -> dict:
    if not env("YOUTUBE_DATA_API_KEY"):
        return {"mode": "demo", "candidates": demo_candidates(),
                "notes": "Demo mode: no YouTube Data API key is configured. Scores are illustrative, not live market data."}
    candidates = []
    errors = []
    for seed in SEEDS:
        try:
            candidates.append(_live_candidate(seed))
        except urllib.error.HTTPError as exc:
            try:
                detail = exc.read().decode("utf-8")[:300]
            except Exception:
                detail = str(exc)
            errors.append(f"{seed['name']}: YouTube API returned HTTP {exc.code} ({detail})")
        except Exception as exc:
            errors.append(f"{seed['name']}: {type(exc).__name__}: {exc}")
    if not candidates:
        return {"mode": "error", "candidates": [], "notes": "\n".join(errors) or "Live scan failed."}
    candidates.sort(key=lambda item: item.get("score", 0), reverse=True)
    note = (
        "Live public YouTube metadata, US-region/en relevance filters. Each candidate samples up to 25 matching videos "
        "from each of three publication cohorts (0–30, 31–90, 91–180 days). These are non-random search samples. "
        "Views are lifetime counts normalized by age, not historical cohort growth. 3× subscriber outliers and "
        "commercial-intent priors are heuristic; no RPM, audience retention, or income estimate is produced."
    )
    if errors:
        note += " Partial scan errors: " + " | ".join(errors)
    return {"mode": "live", "candidates": candidates, "notes": note}
