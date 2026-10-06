"""Trend & source engine: what to make a video about *today*.

Free, key-less sources:
  * Google Trends RSS      - what people are actually searching right now (geo aware, e.g. IN)
  * Wikipedia "On this day" - anniversaries and events, ideal for the history niche
  * Wikipedia most-read     - what the world read today, filtered down to your niche
  * Wikipedia random        - evergreen fallback so the pipeline never runs dry

Every seed carries its source URL, so the finished video can cite where the fact came
from (accuracy + trust, and it keeps the channel out of "mass-produced vague claims"
territory). Grounding the LLM in a real Wikipedia extract is also what stops it from
inventing statistics.
"""
from __future__ import annotations

import asyncio
import json
import re
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import httpx

from .config import Config, get_config
from .utils import clean_text, module_logger, slugify

log = module_logger("trends")

WIKI_FEATURED = "https://api.wikimedia.org/feed/v1/wikipedia/en/featured/{y}/{m:02d}/{d:02d}"
WIKI_ONTHISDAY = "https://api.wikimedia.org/feed/v1/wikipedia/en/onthisday/selected/{m:02d}/{d:02d}"
WIKI_ONTHISDAY_EVENTS = "https://api.wikimedia.org/feed/v1/wikipedia/en/onthisday/events/{m:02d}/{d:02d}"
WIKI_SUMMARY = "https://en.wikipedia.org/api/rest_v1/page/summary/{title}"
WIKI_RANDOM = "https://en.wikipedia.org/api/rest_v1/page/random/summary"
WIKI_ACTION = "https://en.wikipedia.org/w/api.php"
WIKI_REST_SEARCH = "https://en.wikipedia.org/w/rest.php/v1/search/page"
GOOGLE_TRENDS_RSS = "https://trends.google.com/trending/rss?geo={geo}"
MAX_GOOGLE_LOOKUPS = 3   # max 3 fast lookups to keep trend phase snappy
ASCII_ONLY_RE = re.compile(r"^[\x00-\x7F]+$")

HEADERS = {
    "User-Agent": "FactShortsBot/1.0 (https://github.com/factshorts/factshorts-bot; contact@factshorts.org)"
}

# niche -> query used by the "search" source: a guaranteed-niche subject when the
# daily feeds have nothing usable (Google Trends is often sport/politics/regional).
NICHE_QUERIES: dict[str, str] = {
    "space": "space exploration mission NASA ESA astronomy",
    "psychology": "cognitive psychology experiment human behaviour study",
    "history": "archaeology discovery historical event excavation",
    "science": "scientific discovery physics chemistry biology research",
    "animals": "animal behaviour wildlife species research study",
}

# niche -> keywords that mark an article as relevant. Order matters: first match wins.
NICHE_KEYWORDS: dict[str, list[str]] = {
    "space": ["space", "nasa", "esa", "planet", "star", "galaxy", "orbit", "telescope", "astronom",
              "asteroid", "comet", "rocket", "satellite", "cosmolog", "black hole", "nebula",
              "spacecraft", "solar", "lunar", "mars", "moon", "astro"],
    "psychology": ["psycholog", "psychiatr", "mental", "behavio", "cognit", "memory", "brain",
                   "emotion", "therapy", "perception", "decision", "cognitive bias", "mind"],
    "history": ["war", "empire", "dynasty", "century", "ancient", "revolution", "treaty", "kingdom",
                "archaeolog", "civilis", "civiliz", "medieval", "colonial", "battle", "roman",
                "artifact", "excavat", "manuscript"],
    "science": ["physic", "chemist", "biolog", "scientist", "research", "experiment", "quantum",
                "gene", "dna", "species", "cell", "atom", "molecule", "climate", "energy",
                "mathematic", "geolog", "vaccine", "medicine", "virus", "bacteri"],
    "animals": ["animal", "bird", "fish", "insect", "species", "wildlife", "mammal", "reptile",
                "amphibian", "predator", "habitat", "ecosystem", "shark", "whale", "spider",
                "butterfl", "octopus", "elephant", "tardigrade", "bee"],
}

# Things that make a *fact* video risky, dated or boring: politics, crime, celeb news, sport.
# NOTE: the leading \b matters - without it "studied" matches "died" and half of science
# gets filtered out. Short words that are also prefixes of common words get their own
# whole-word branch.
NOISE_RE = re.compile(
    r"\b(?:"
    r"election|politic|president|minister|parliament|senate|congress|"
    r"murder|killing|shooting|attack|terror|arrest|trial|convict|sentenc|prison|"
    r"box office|movie|series|season finale|album|rapper|actress|"
    r"football|cricket|tennis|olympic|tournament|championship|transfer|"
    r"obituary|hospital|pandemic|outbreak|"
    r"stock market|inflation|crypto|bitcoin)"
    r"|\b(?:death|died|dies|film|actor|singer|match|league|economy|price|stock|news)\b",
    re.I,
)

# list/statistics articles that make terrible shorts ("Deaths in 2026", "List of ...")
BAD_TITLE_RE = re.compile(
    r"^(list of|timeline of|deaths in|index of|outline of|glossary of|"
    r"\.\w{2,4}$|category:|template:|portal:)", re.I
)

# subjects that are unsuitable for a general-audience facts channel: the niche rule is
# "surprising but safe" - anything medical, sexual, violent or politically loaded is out
SENSITIVE_RE = re.compile(
    r"\b(?:sex|sexual|homosexual|pornograph|prostitut|rape|abortion|suicide|self-harm|"
    r"drug|narcotic|cocaine|heroin|cannabis|alcohol|smoking|tobacco|"
    r"abuse|torture|massacre|genocide|holocaust|nazi|terroris|extremis|"
    r"cult|satanis|occult|witch|exorcis|"
    r"cancer|tumou?r|hiv|aids|depress|schizophren|autis|disorder|syndrome|"
    r"conspiracy|hoax|pseudo-?scien|alien abduction|flat earth)\b",
    re.I,
)

SPORT_PERSON_RE = re.compile(
    r"\b(?:batsman|batter|bowler|goalkeeper|quarterback|footballer|midfielder|wicketkeeper)\b", re.I
)

# visual keywords per niche for footage search (trend articles rarely hint at B-roll)
NICHE_VISUALS: dict[str, list[str]] = {
    "space": ["space nebula", "stars night sky", "planet surface", "earth from space"],
    "psychology": ["human brain abstract", "person thinking", "abstract motion"],
    "history": ["ancient ruins", "old manuscripts", "museum artifacts"],
    "science": ["laboratory science", "microscope footage", "water droplets macro"],
    "animals": ["wildlife closeup", "ocean underwater", "birds in flight"],
}


@dataclass
class TrendSeed:
    """One candidate subject, always with a citable source."""
    title: str
    summary: str = ""
    source: str = "wikipedia"          # wikipedia | google-trends
    source_url: str = ""
    kind: str = "mostread"             # mostread | onthisday | google | random | featured
    niche: str = ""
    year: int | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    def keywords(self) -> list[str]:
        words = [w for w in re.findall(r"[A-Za-z]{4,}", self.title)][:3]
        return [" ".join(words[:2]).strip()] + NICHE_VISUALS.get(self.niche, []) if words else \
            list(NICHE_VISUALS.get(self.niche, []))

    def label(self) -> str:
        return f"[{self.source}/{self.kind}] {self.title}" + (f" ({self.year})" if self.year else "")


class TrendClient:
    """Fetches candidate subjects. Responses are cached on disk so the twice-daily runs
    do not hammer the free APIs (and keep working if one of them throttles us)."""

    def __init__(self, cfg: Config | None = None) -> None:
        self.cfg = cfg or get_config()
        self._client: httpx.AsyncClient | None = None
        self._cache_dir = self.cfg.cache_dir / "trends"
        self._mem: dict[str, Any] = {}

    # ------------------------------------------------------------- disk cache
    def _cache_path(self, key: str) -> Path:
        return self._cache_dir / f"{slugify(key, 90)}.json"

    def _cache_get(self, key: str, ttl: float) -> Any | None:
        if key in self._mem:
            return self._mem[key]
        path = self._cache_path(key)
        if not path.exists():
            return None
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            if time.time() - float(payload.get("_ts", 0)) > ttl:
                return None
            self._mem[key] = payload.get("data")
            return payload.get("data")
        except Exception:  # noqa: BLE001
            return None

    def _cache_set(self, key: str, data: Any) -> None:
        self._mem[key] = data
        try:
            self._cache_dir.mkdir(parents=True, exist_ok=True)
            self._cache_path(key).write_text(
                json.dumps({"_ts": time.time(), "data": data}, ensure_ascii=False), encoding="utf-8"
            )
        except Exception as exc:  # noqa: BLE001
            log.debug("trend cache write failed: %s", exc)

    async def client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=httpx.Timeout(10.0, connect=3.0), headers=HEADERS,
                                             follow_redirects=True)
        return self._client

    async def aclose(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def _get_json(self, url: str, attempts: int = 2, ttl: float = 0.0, **params) -> Any:
        """GET JSON with a disk cache and polite backoff (honours Retry-After on 429)."""
        cache_key = url + "?" + "&".join(f"{k}={v}" for k, v in sorted(params.items()))
        if ttl:
            cached = self._cache_get(cache_key, ttl)
            if cached is not None:
                return cached

        client = await self.client()
        last: Exception | None = None
        for i in range(1, attempts + 1):
            try:
                resp = await client.get(url, params=params or None)
                if resp.status_code == 200:
                    data = resp.json()
                    if ttl:
                        self._cache_set(cache_key, data)
                    return data
                last = RuntimeError(f"HTTP {resp.status_code}")
                if resp.status_code == 429:
                    wait = float(resp.headers.get("retry-after") or 0) or 3.0 * i
                    if i < attempts:
                        log.warning("trends: rate limited by %s - waiting %.0fs", url.split("/")[2], wait)
                        await asyncio.sleep(min(wait, 20))
                        continue
            except Exception as exc:  # noqa: BLE001
                last = exc
            if i < attempts:
                await asyncio.sleep(1.2 * i)
        log.warning("trends: %s failed (%s)", url.split("?")[0], last)
        return None

    # ------------------------------------------------------------------ sources
    async def google_trends(self, geo: str | None = None, limit: int = 20) -> list[TrendSeed]:
        """Google Trends daily search RSS - free, no key, unofficial but stable."""
        geo = (geo or self.cfg.trends_geo or "IN").upper()
        client = await self.client()
        try:
            resp = await client.get(GOOGLE_TRENDS_RSS.format(geo=geo))
            if resp.status_code != 200:
                log.warning("google trends HTTP %s", resp.status_code)
                return []
            xml = resp.text
        except Exception as exc:  # noqa: BLE001
            log.warning("google trends failed: %s", exc)
            return []

        seeds: list[TrendSeed] = []
        for item in re.findall(r"<item>(.*?)</item>", xml, re.S)[:limit]:
            title = re.search(r"<title>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</title>", item, re.S)
            traffic = re.search(r"<ht:approx_traffic>(.*?)</ht:approx_traffic>", item, re.S)
            picture = re.search(r"<ht:picture>(.*?)</ht:picture>", item, re.S)
            news_title = re.search(r"<ht:news_item_title>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</ht:news_item_title>", item, re.S)
            news_url = re.search(r"<ht:news_item_url>(.*?)</ht:news_item_url>", item, re.S)
            if not title or not title.group(1).strip():
                continue
            seeds.append(
                TrendSeed(
                    title=clean_text(title.group(1), 90),
                    summary=clean_text(news_title.group(1), 200) if news_title else "",
                    source="google-trends",
                    source_url=(news_url.group(1).strip() if news_url else GOOGLE_TRENDS_RSS.format(geo=geo)),
                    kind="google",
                    extra={"geo": geo, "traffic": traffic.group(1).strip() if traffic else "",
                           "picture": picture.group(1).strip() if picture else ""},
                )
            )
        log.info("google trends (%s): %d items", geo, len(seeds))
        return seeds

    async def wikipedia_mostread(self, niche: str = "", days_back: int = 1) -> list[TrendSeed]:
        """What the world read today (Wikipedia), filtered to a niche and de-noised."""
        day = datetime.now(timezone.utc) - timedelta(days=days_back)
        data = await self._get_json(WIKI_FEATURED.format(y=day.year, m=day.month, d=day.day), ttl=6 * 3600)
        if not data:
            return []
        out: list[TrendSeed] = []
        for article in (data.get("mostread") or {}).get("articles", [])[:60]:
            title = str(article.get("normalizedtitle") or article.get("title") or "")
            extract = clean_text(str(article.get("extract") or ""), 700)
            if not title or len(extract) < 80:
                continue
            if not self._relevant(extract, niche, title):
                continue
            out.append(
                TrendSeed(
                    title=title,
                    summary=extract,
                    source="wikipedia",
                    source_url=((article.get("content_urls") or {}).get("desktop") or {}).get("page")
                    or f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}",
                    kind="mostread",
                    niche=niche,
                    extra={"views": article.get("views")},
                )
            )
        tfa = data.get("tfa") or {}
        if tfa.get("normalizedtitle") and self._relevant(
            str(tfa.get("extract") or ""), niche, str(tfa.get("normalizedtitle"))
        ):
            out.insert(0, TrendSeed(
                title=str(tfa["normalizedtitle"]),
                summary=clean_text(str(tfa.get("extract") or ""), 700),
                source="wikipedia",
                source_url=((tfa.get("content_urls") or {}).get("desktop") or {}).get("page", ""),
                kind="featured",
                niche=niche,
            ))
        log.info("wikipedia mostread (%s): %d niche-relevant items", niche or "any", len(out))
        return out

    async def wikipedia_onthisday(self, niche: str = "history", day: datetime | None = None) -> list[TrendSeed]:
        """Events/anniversaries from Wikipedia's On this day feed."""
        day = day or datetime.now(timezone.utc)
        out: list[TrendSeed] = []
        for url in (WIKI_ONTHISDAY.format(m=day.month, d=day.day),
                    WIKI_ONTHISDAY_EVENTS.format(m=day.month, d=day.day)):
            data = await self._get_json(url, ttl=24 * 3600)
            if not data:
                continue
            for event in data.get("selected") or data.get("events") or []:
                text = clean_text(str(event.get("text") or ""), 600)
                year = event.get("year")
                if len(text) < 60 or NOISE_RE.search(text):
                    continue
                pages = event.get("pages") or []
                page = pages[0] if pages else {}
                out.append(
                    TrendSeed(
                        title=clean_text(str(page.get("normalizedtitle") or page.get("title") or text[:60]), 80),
                        summary=text,
                        source="wikipedia",
                        source_url=((page.get("content_urls") or {}).get("desktop") or {}).get("page", ""),
                        kind="onthisday",
                        niche=niche,
                        year=int(year) if isinstance(year, int) else None,
                    )
                )
        log.info("wikipedia on-this-day: %d usable events", len(out))
        return out

    async def wikipedia_search(self, niche: str, limit: int = 10) -> list[TrendSeed]:
        """Wikipedia full-text search for the niche - always returns subjects, so the
        pipeline never depends on today's news being useful.

        Uses the REST search endpoint first (it already returns an extract, so it is one
        request instead of two and lives in a different rate-limit bucket), then the
        action API as a fallback.
        """
        query = NICHE_QUERIES.get(niche, niche or "science")
        out: list[TrendSeed] = []

        rest = await self._get_json(
            WIKI_REST_SEARCH, q=query, limit=str(limit), ttl=12 * 3600
        )
        for page in ((rest or {}).get("pages") or []):
            title = str(page.get("title") or "")
            summary = clean_text(str(page.get("description") or "") + ". " + str(page.get("excerpt") or ""), 700)
            summary = re.sub(r"<[^>]+>", "", summary)  # the excerpt contains <span class="searchmatch">
            if not title or len(summary) < 60 or BAD_TITLE_RE.search(title) or NOISE_RE.search(title):
                continue
            if SENSITIVE_RE.search(title) or SENSITIVE_RE.search(summary):
                continue
            if not self._relevant(summary, niche, title):
                continue
            out.append(TrendSeed(
                title=title,
                summary=summary,
                source="wikipedia",
                source_url=f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}",
                kind="search",
                niche=niche,
            ))

        if not out:
            data = await self._get_json(
                WIKI_ACTION, ttl=12 * 3600, action="query", list="search", srsearch=query,
                srnamespace="0", srlimit=str(limit), format="json",
            )
            hits = ((data or {}).get("query") or {}).get("search") or []
            for hit in hits[:6]:
                title = str(hit.get("title") or "")
                if not title or BAD_TITLE_RE.search(title) or NOISE_RE.search(title) \
                        or SENSITIVE_RE.search(title):
                    continue
                seed = await self._summary_via_action_api(title)
                await asyncio.sleep(0.4)
                if seed and self._relevant(seed.summary, niche, seed.title):
                    seed.kind = "search"
                    seed.niche = niche
                    out.append(seed)
        log.info("wikipedia search (%s): %d subjects", niche, len(out))
        return out

    async def wikipedia_random(self, niche: str = "", tries: int = 6) -> TrendSeed | None:
        """Random article with a decent extract - evergreen fallback.

        Tries the REST random endpoint first, then the action-API random list + summary
        (different rate-limit bucket, so one being throttled does not starve the pipeline).
        """
        for attempt in range(tries):
            if attempt < max(1, tries // 2):
                data = await self._get_json(WIKI_RANDOM)
                if data:
                    title = str(data.get("title") or "")
                    extract = clean_text(str(data.get("extract") or ""), 700)
                    if len(extract) >= 120 and data.get("type") != "disambiguation" \
                            and self._relevant(extract, niche, title):
                        return TrendSeed(
                            title=title,
                            summary=extract,
                            source="wikipedia",
                            source_url=((data.get("content_urls") or {}).get("desktop") or {}).get("page", ""),
                            kind="random",
                            niche=niche,
                        )
                continue

            listing = await self._get_json(
                WIKI_ACTION, action="query", list="random", rnnamespace="0", rnlimit="5", format="json"
            )
            for item in ((listing or {}).get("query") or {}).get("random", []):
                seed = await self._summary_via_action_api(str(item.get("title") or ""))
                await asyncio.sleep(0.5)
                if seed and self._relevant(seed.summary, niche, seed.title):
                    seed.kind = "random"
                    seed.niche = niche
                    return seed
        return None

    async def wikipedia_summary(self, title: str, full_text: bool = False) -> TrendSeed | None:
        """Look up one title (grounds a topic in real, citable content).

        The REST summary is the lead section only; ``full_text=True`` (story mode, when the
        lead is not enough material for a 60-second narration) goes through the action API
        for the rest of the article. Still key-less.
        """
        if not title:
            return None
        if full_text:
            return await self._summary_via_action_api(title, full_text=True)
        data = await self._get_json(WIKI_SUMMARY.format(title=title.replace(" ", "_")), ttl=24 * 3600)
        if data and data.get("type") != "disambiguation":
            extract = clean_text(str(data.get("extract") or ""), 700)
            if len(extract) >= 120:
                return TrendSeed(
                    title=str(data.get("title") or title),
                    summary=extract,
                    source="wikipedia",
                    source_url=((data.get("content_urls") or {}).get("desktop") or {}).get("page", ""),
                    kind="google",
                )
        # REST endpoint throttled? the action API uses a separate rate-limit bucket
        return await self._summary_via_action_api(title)

    async def _summary_via_action_api(self, title: str, full_text: bool = False) -> TrendSeed | None:
        data = await self._get_json(
            WIKI_ACTION,
            ttl=24 * 3600,
            action="query",
            prop="extracts",
            exintro="0" if full_text else "1",
            explaintext="1",
            redirects="1",
            format="json",
            titles=title,
        )
        if not data:
            return None
        pages = ((data.get("query") or {}).get("pages") or {})
        for page in pages.values():
            limit = 4000 if full_text else 700
            extract = clean_text(str(page.get("extract") or ""), limit)
            if len(extract) < 120 or page.get("missing") is not None:
                continue
            page_title = str(page.get("title") or title)
            return TrendSeed(
                title=page_title,
                summary=extract,
                source="wikipedia",
                source_url=f"https://en.wikipedia.org/wiki/{page_title.replace(' ', '_')}",
                kind="google",
            )
        return None

    # ------------------------------------------------------------------ helpers
    @staticmethod
    def _relevant(text: str, niche: str, title: str = "") -> bool:
        """Relevance gate: a trend only becomes a video if it really belongs to the niche.

        A single incidental keyword match is not enough ("...domain .xyz..." is not a space
        story), so we require either a keyword in the *title* or at least two distinct niche
        keywords in the body, and we drop list/statistics articles and news/celebrity noise.
        """
        if BAD_TITLE_RE.search((title or text).strip()):
            return False
        if not niche:
            return not NOISE_RE.search(text)
        if NOISE_RE.search(text) or SPORT_PERSON_RE.search(text) or SENSITIVE_RE.search(text):
            return False
        keywords = NICHE_KEYWORDS.get(niche, [])
        low = (text or "").lower()
        if title and any(k in title.lower() for k in keywords):
            return True
        return sum(1 for k in keywords if k in low) >= 2

    async def find_seed(self, niche: str, geo: str | None = None) -> TrendSeed | None:
        """Best available subject for this niche right now, in priority order."""
        order = self.cfg.trend_sources or ["google", "onthisday", "mostread", "random"]
        for source in order:
            try:
                if source == "google":
                    lookups = 0
                    candidates: list[tuple[float, TrendSeed]] = []
                    for trend in await self.google_trends(geo):
                        if lookups >= MAX_GOOGLE_LOOKUPS:
                            break
                        if not ASCII_ONLY_RE.match(trend.title) or NOISE_RE.search(trend.title):
                            continue
                        lookups += 1
                        seed = await self.wikipedia_summary(trend.title)
                        await asyncio.sleep(0.2)  # fast polite gap
                        if seed and self._relevant(seed.summary, niche, seed.title):
                            seed.kind = "google"
                            seed.extra = trend.extra
                            seed.niche = niche
                            # YouTube-Autopilot breakout velocity score
                            tr_str = str((trend.extra or {}).get("traffic") or "")
                            vel = 50.0 if "M" in tr_str else (30.0 if "K" in tr_str else 10.0)
                            candidates.append((vel, seed))
                    if candidates:
                        candidates.sort(key=lambda x: x[0], reverse=True)
                        log.info("selected breakout trend: %r (velocity: %.0f)", candidates[0][1].title, candidates[0][0])
                        return candidates[0][1]
                elif source == "onthisday" and niche in {"history", "science", "space"}:
                    for seed in await self.wikipedia_onthisday(niche):
                        if self._relevant(seed.title + " " + seed.summary, niche):
                            return seed
                elif source == "search":
                    seed = next(iter(await self.wikipedia_search(niche)), None)
                    if seed:
                        return seed
                elif source == "mostread":
                    for seed in await self.wikipedia_mostread(niche):
                        return seed
                elif source == "random":
                    seed = await self.wikipedia_random(niche)
                    if seed:
                        return seed
            except Exception as exc:  # noqa: BLE001 - a broken source must not kill the run
                log.warning("trend source %s failed: %s", source, exc)
        return None


async def list_trends(geo: str | None = None, niche: str = "", limit: int = 12) -> dict[str, list[TrendSeed]]:
    """used by `main.py --trends` and the /trends Telegram command."""
    client = TrendClient()
    try:
        return {
            "google": (await client.google_trends(geo, limit))[:limit],
            "mostread": (await client.wikipedia_mostread(niche))[:limit],
            "onthisday": (await client.wikipedia_onthisday(niche or "history"))[:limit],
            "random": [s for s in [await client.wikipedia_random(niche)] if s],
        }
    finally:
        await client.aclose()
