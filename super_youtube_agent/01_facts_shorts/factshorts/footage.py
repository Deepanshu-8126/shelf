"""Footage providers - all free / no-cost, commercial-use friendly:

  1. Pexels Videos API   (free key, commercial use allowed, no attribution required)
  2. Pixabay Videos API  (free key, commercial use allowed)
  3. NASA Images API     (no key needed - public domain NASA/ESA footage, great for space/science)
  4. Wikimedia Commons   (no key needed - CC/PD material, attribution stored)
  5. Local clips         (drop your own files in assets/stock/)

Every downloaded clip is stored in the SQLite cache with its licence/credit info so
the description can credit CC-BY sources automatically.
"""
from __future__ import annotations

import asyncio
import html as html_lib
import json
import random
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import httpx

from . import db
from .config import Config, get_config
from .utils import (
    human_bytes,
    media_duration,
    module_logger,
    slugify,
    video_size,
)

log = module_logger("footage")

PEXELS_SEARCH = "https://api.pexels.com/videos/search"
PIXABAY_SEARCH = "https://pixabay.com/api/videos/"
COMMONS_API = "https://commons.wikimedia.org/w/api.php"
NASA_SEARCH = "https://images-api.nasa.gov/search"

# titles that usually mean "screen recording / chart / audio visualisation" rather than
# usable B-roll. Cheap heuristic that keeps junk out of the render.
JUNK_TITLE_RE = re.compile(
    r"(spectrogram|waveform|screen ?record|screen ?shot|screenshot|test ?card|tutorial|"
    r"slideshow|powerpoint|logo animation|bar chart|graph of|debug|render test)",
    re.I,
)

# NASA's library mixes beautiful B-roll with press briefings/interviews - skip the latter.
NASA_JUNK_RE = re.compile(
    r"(briefing|interview|press conference|teleconference|media day|hearing|panel discussion|"
    r"science chat|profile:|episode|podcast|update on|what.?s next|what.?s up|skywatching|tips|"
    r"town hall|qa session|q&a|ask a|watch:|tour of|virtual tour|"
    r"administrator|budget|career|internship|job|hiring|"
    r"grblre|color ?bar|test pattern|calibration|chart|diagram|poster|infographic)",
    re.I,
)
NASA_GOOD_RE = re.compile(
    r"(timelapse|time-lapse|animation|visualization|fly.?through|flyover|4k|8k|zoom|"
    r"flyby|footage|views?|flight|orbit|surface|panorama|closeup|close-up)",
    re.I,
)

COMMONS_EXTRA_QUERIES = [
    "nature timelapse", "ocean underwater", "clouds sky timelapse", "city night timelapse",
    "microscope science", "forest aerial", "stars night sky timelapse", "water surface macro",
    "laboratory science", "desert aerial", "deep space nebula", "animal wildlife closeup",
]


@dataclass
class ClipCandidate:
    source: str
    source_id: str
    download_url: str
    page_url: str = ""
    author: str = ""
    license: str = ""
    duration: float = 0.0
    width: int = 0
    height: int = 0
    query: str = ""
    filesize: int = 0
    title: str = ""
    archival: bool = False   # came from a long produced film (title cards / interviews)

    @property
    def key(self) -> str:
        return f"{self.source}:{self.source_id}"


@dataclass
class Clip:
    path: Path
    candidate: ClipCandidate
    duration: float = 0.0
    width: int = 0
    height: int = 0
    from_cache: bool = False
    sharpness: float | None = None   # blurdetect score, filled in by the renderer


class FootageError(RuntimeError):
    pass


class FootageClient:
    def __init__(self, cfg: Config | None = None) -> None:
        self.cfg = cfg or get_config()
        self._client: httpx.AsyncClient | None = None
        self._lock = asyncio.Lock()
        self._throttle_lock = asyncio.Lock()
        self._last_call: dict[str, float] = {}

    # ------------------------------------------------------------------ plumbing
    async def client(self) -> httpx.AsyncClient:
        async with self._lock:
            if self._client is None or self._client.is_closed:
                self._client = httpx.AsyncClient(
                    timeout=httpx.Timeout(30.0, read=self.cfg.clip_download_timeout),
                    follow_redirects=True,
                    headers={"User-Agent": "FactShortsBot/1.0 (https://github.com/factshorts/factshorts-bot; contact@factshorts.org)"},
                )
        return self._client

    async def aclose(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def _throttle(self, key: str, min_interval: float = 1.0) -> None:
        """Space out requests per host: Wikimedia (and any API) will 429 if hammered."""
        async with self._throttle_lock:
            wait = min_interval - (time.monotonic() - self._last_call.get(key, 0.0))
            if wait > 0:
                await asyncio.sleep(wait)
            self._last_call[key] = time.monotonic()

    async def _get_with_retry(self, method: str, url: str, *, attempts: int = 3, **kwargs) -> httpx.Response:
        """GET with throttling + backoff on 429/5xx (Wikimedia throttles aggressively)."""
        client = await self.client()
        key = "host:" + (httpx.URL(url).host or "unknown")
        last: Exception | None = None
        for i in range(1, attempts + 1):
            await self._throttle(key, 1.1)
            try:
                resp = await client.request(method, url, **kwargs)
            except Exception as exc:  # noqa: BLE001 - network hiccup
                last = exc
                log.warning("%s %s failed (%s), retry %d/%d", method, key, exc, i, attempts)
                await asyncio.sleep(1.5 * i)
                continue
            if resp.status_code in (429, 500, 502, 503, 504) and i < attempts:
                delay = float(resp.headers.get("retry-after") or 0) or 1.5 * i
                log.warning("%s %s -> HTTP %s, retry in %.1fs (%d/%d)", method, key, resp.status_code, delay, i, attempts)
                await asyncio.sleep(min(delay, 15))
                continue
            return resp
        if last:
            raise last
        raise FootageError(f"{method} {url} failed after {attempts} attempts")

    # ---------------------------------------------------------------- providers
    async def _pexels(self, query: str, limit: int = 8) -> list[ClipCandidate]:
        if not self.cfg.pexels_api_key:
            return []
        resp = await self._get_with_retry(
            "GET",
            PEXELS_SEARCH,
            params={"query": query, "orientation": "portrait", "per_page": max(limit, 8), "size": "medium"},
            headers={"Authorization": self.cfg.pexels_api_key},
        )
        if resp.status_code >= 400:
            raise FootageError(f"pexels HTTP {resp.status_code}: {resp.text[:200]}")
        out: list[ClipCandidate] = []
        for video in resp.json().get("videos", []):
            best = self._pick_pexels_file(video.get("video_files") or [])
            if not best:
                continue
            out.append(
                ClipCandidate(
                    source="pexels",
                    source_id=str(video.get("id")),
                    download_url=best.get("link", ""),
                    page_url=video.get("url", ""),
                    author=(video.get("user") or {}).get("name", ""),
                    license="Pexels License (free for commercial use, no attribution required)",
                    duration=float(video.get("duration") or 0),
                    width=int(best.get("width") or video.get("width") or 0),
                    height=int(best.get("height") or video.get("height") or 0),
                    query=query,
                    filesize=int(best.get("file_size") or 0),
                )
            )
        return out

    def _pick_pexels_file(self, files: list[dict[str, Any]]) -> dict[str, Any] | None:
        usable = [f for f in files if (f.get("file_type") or "").startswith("video/mp4") and f.get("link")]
        if not usable:
            return None
        portrait = [f for f in usable if (f.get("height") or 0) >= (f.get("width") or 0)]

        def rank(f: dict[str, Any]) -> tuple[int, int]:
            h = int(f.get("height") or 0)
            too_big = 1 if h > self.cfg.clip_max_height else 0
            return (too_big, -h)  # prefer not-too-big, then the tallest

        pool = portrait or usable
        return sorted(pool, key=rank)[0]

    async def _pixabay(self, query: str, limit: int = 8) -> list[ClipCandidate]:
        if not self.cfg.pixabay_api_key:
            return []
        resp = await self._get_with_retry(
            "GET",
            PIXABAY_SEARCH,
            params={
                "key": self.cfg.pixabay_api_key,
                "q": query,
                "video_type": "film",
                "safesearch": "true",
                "per_page": max(3, min(limit, 20)),
            },
        )
        if resp.status_code >= 400:
            raise FootageError(f"pixabay HTTP {resp.status_code}: {resp.text[:200]}")
        out: list[ClipCandidate] = []
        for hit in resp.json().get("hits", []):
            variants = hit.get("videos") or {}
            best = variants.get("large") or variants.get("medium") or variants.get("small")
            if not best or not best.get("url"):
                continue
            out.append(
                ClipCandidate(
                    source="pixabay",
                    source_id=str(hit.get("id")),
                    download_url=best["url"],
                    page_url=hit.get("pageURL", ""),
                    author=hit.get("user", ""),
                    license="Pixabay Content License (free for commercial use)",
                    duration=float(hit.get("duration") or 0),
                    width=int(best.get("width") or 0),
                    height=int(best.get("height") or 0),
                    query=query,
                    filesize=int(best.get("size") or 0),
                )
            )
        return out

    async def _nasa(self, query: str, limit: int = 8) -> list[ClipCandidate]:
        """NASA Image and Video Library: no API key, public-domain footage.
        Ideal for space/science niches when no stock-video key is configured."""
        resp = await self._get_with_retry(
            "GET",
            NASA_SEARCH,
            params={"q": query, "media_type": "video", "page_size": max(3, min(limit, 20))},
        )
        if resp.status_code >= 400:
            raise FootageError(f"nasa HTTP {resp.status_code}: {resp.text[:160]}")
        items = (resp.json().get("collection") or {}).get("items") or []
        # B-roll-looking titles first: NASA mixes press briefings and interviews into search
        # results and we cannot detect a talking head reliably, so prefer good candidates.
        items = sorted(
            items,
            key=lambda it: (
                0 if NASA_GOOD_RE.search(str(((it.get("data") or [{}])[0]).get("title") or "")) else 1,
                str(((it.get("data") or [{}])[0]).get("date_created") or ""),
            ),
        )
        out: list[ClipCandidate] = []
        for item in items:
            data = (item.get("data") or [{}])[0]
            title = str(data.get("title") or "").strip()
            if title and NASA_JUNK_RE.search(title):
                log.debug("nasa: skipping non-visual item %r", title[:60])
                continue
            if len(out) >= limit:
                break
            nasa_id = str(data.get("nasa_id") or "")
            href = item.get("href") or (f"https://images-assets.nasa.gov/video/{nasa_id}/collection.json" if nasa_id else "")
            if not href:
                continue
            try:
                assets = await self._get_with_retry("GET", href)
                payload = assets.json()
                # NASA asset collections answer with a plain JSON array of file URLs
                # (older endpoints wrapped it in {"collection": {"items": [...]}})
                if isinstance(payload, list):
                    files = [str(u) for u in payload]
                else:
                    files = [a.get("href", "") for a in (payload.get("collection") or {}).get("items", [])]
            except Exception as exc:  # noqa: BLE001
                log.debug("nasa asset list failed for %s: %s", nasa_id, exc)
                continue
            mp4s = [f for f in files if f.lower().endswith(".mp4")]
            if not mp4s:
                continue
            def rank(url: str) -> int:
                u = url.lower()
                if "~orig" in u:
                    return 0
                if "~large" in u:
                    return 1
                if "~medium" in u:
                    return 2
                if "~mobile" in u or "~small" in u:
                    return 3
                return 1

            # pick the best variant that is not absurdly large (HEAD check, cheap)
            chosen = ""
            for candidate_url in sorted(mp4s, key=rank):
                size = await self._head_size(candidate_url)
                if size == 0 or size <= 60 * 1024 * 1024:
                    chosen = candidate_url
                    break
            if not chosen:
                log.debug("nasa: every variant of %s is >60MB, skipping", nasa_id)
                continue
            out.append(
                ClipCandidate(
                    source="nasa",
                    source_id=nasa_id or slugify(title, 40),
                    download_url=chosen.replace("http://", "https://"),
                    page_url=f"https://images.nasa.gov/details-{nasa_id}" if nasa_id else "",
                    author="NASA",
                    license="NASA media (generally not copyrighted - see NASA media usage guidelines)",
                    duration=float(data.get("duration") or 0) if isinstance(data.get("duration"), (int, float)) else 0.0,
                    query=query,
                    title=title,
                )
            )
        return out

    async def _head_size(self, url: str) -> int:
        try:
            resp = await self._get_with_retry("HEAD", url, attempts=1)
            return int(resp.headers.get("content-length") or 0)
        except Exception:  # noqa: BLE001
            return 0

    async def _wikimedia(self, query: str, limit: int = 6) -> list[ClipCandidate]:
        """Royalty-free CC/PD video from Wikimedia Commons. No API key required."""
        search = (
            f"filetype:video filesize:<{25 * 1024 * 1024} "
            "-intitle:test -intitle:screen -intitle:spectrogram -intitle:waveform "
            "-intitle:screenshot -intitle:logo "
        ) + query
        params = {
            "action": "query",
            "format": "json",
            "generator": "search",
            "gsrsearch": search,
            "gsrlimit": max(3, min(limit, 10)),
            "gsrnamespace": "6",
            "prop": "imageinfo",
            "iiprop": "url|size|mime|extmetadata",
        }
        resp = await self._get_with_retry("GET", COMMONS_API, params=params)
        if resp.status_code >= 400:
            raise FootageError(f"commons HTTP {resp.status_code}")
        pages = (resp.json().get("query") or {}).get("pages") or {}
        out: list[ClipCandidate] = []
        for page in pages.values():
            info = (page.get("imageinfo") or [{}])[0]
            mime = info.get("mime") or ""
            url = info.get("url") or ""
            if not url or not mime.startswith("video"):
                continue
            width, height = int(info.get("width") or 0), int(info.get("height") or 0)
            if width * height > 3840 * 2160:
                continue  # skip 8K monsters
            meta = info.get("extmetadata") or {}
            license_ = (meta.get("LicenseShortName") or {}).get("value", "see file page")
            author = html_lib.unescape(re.sub(r"<[^>]+>", "", (meta.get("Artist") or {}).get("value", "")))[:80]
            title = str(page.get("title") or "").removeprefix("File:")
            out.append(
                ClipCandidate(
                    source="wikimedia",
                    source_id=str(page.get("pageid")),
                    download_url=url,
                    page_url=f"https://commons.wikimedia.org/?curid={page.get('pageid')}",
                    author=author,
                    license=f"Wikimedia Commons: {license_}",
                    duration=0.0,  # resolved after download via ffprobe
                    width=width,
                    height=height,
                    query=query,
                    filesize=int(info.get("size") or 0),
                    title=title,
                )
            )
        return out

    def _local(self, query: str, limit: int = 8) -> list[ClipCandidate]:
        """Own clips from assets/stock/. Files named after their query (that is how the
        fetch script saves them) are ranked first, so keywords still steer the choice."""
        folder = self.cfg.assets_dir / "stock"
        if not folder.exists():
            return []
        files = [p for p in sorted(folder.iterdir()) if p.suffix.lower() in {".mp4", ".mov", ".webm", ".mkv"}]
        if not files:
            return []
        tokens = {t for t in (query or "").lower().replace("-", " ").split() if len(t) > 2}
        # the fetch script records where each downloaded file came from, so archival files
        # still inherit the "skip long produced videos" rule even though they are local now
        manifest: dict[str, dict] = {}
        manifest_path = folder / "manifest.json"
        if manifest_path.exists():
            try:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            except Exception as exc:  # noqa: BLE001
                log.debug("could not read stock manifest: %s", exc)

        def relevance(path: Path) -> int:
            name = path.stem.lower().replace("_", " ").replace("-", " ")
            return -sum(1 for t in tokens if t in name)

        files.sort(key=relevance)
        out: list[ClipCandidate] = []
        for path in files[: max(limit, 12)]:
            dur = media_duration(path)
            w, h = video_size(path)
            meta = manifest.get(path.name) or {}
            out.append(
                ClipCandidate(
                    source="local",
                    source_id=slugify(path.stem, 40),
                    download_url=path.as_uri(),
                    page_url=meta.get("page", ""),
                    author=meta.get("author", "local library"),
                    license=meta.get("license", "user-provided local clip"),
                    duration=dur,
                    width=w,
                    height=h,
                    query=query or meta.get("query", "local"),
                    title=meta.get("title", ""),
                    archival=(meta.get("source") in self.cfg.duration_capped_sources),
                )
            )
        random.shuffle(out)
        return out

    # ------------------------------------------------------------------ search
    async def search(self, query: str, per_provider: int = 25) -> list[ClipCandidate]:
        """Search providers in the configured order; return everything usable."""
        results: list[ClipCandidate] = []
        errors: list[str] = []

        async def safe(name: str, coro) -> list[ClipCandidate]:
            try:
                return await coro
            except Exception as exc:  # noqa: BLE001
                errors.append(f"{name}: {exc}")
                log.warning("provider %s failed for %r: %s", name, query, exc)
                return []

        tasks = []
        for provider in self.cfg.footage_providers:
            if provider == "pexels":
                tasks.append(safe("pexels", self._pexels(query, per_provider)))
            elif provider == "pixabay":
                tasks.append(safe("pixabay", self._pixabay(query, per_provider)))
            elif provider == "nasa":
                tasks.append(safe("nasa", self._nasa(query, per_provider)))
            elif provider == "wikimedia":
                tasks.append(safe("wikimedia", self._wikimedia(query, per_provider)))
            elif provider == "local":
                tasks.append(safe("local", asyncio.to_thread(self._local, query, 4)))
        for provider_results in await asyncio.gather(*tasks):
            results.extend(provider_results)

        # filter: long enough, vertical-ish or croppable, not absurdly large
        usable: list[ClipCandidate] = []
        for c in results:
            if not c.download_url:
                continue
            if c.duration and c.duration < self.cfg.min_clip_seconds():
                continue
            if c.filesize and c.filesize > 80 * 1024 * 1024:
                continue
            if c.title and JUNK_TITLE_RE.search(c.title):
                log.debug("skipping junk-looking clip: %s", c.title)
                continue
            cap = self.cfg.clip_max_source_duration
            if cap and (c.archival or c.source in self.cfg.duration_capped_sources) and c.duration and c.duration > cap:
                log.debug("skipping %s: %.0fs source is longer than the %.0fs cap", c.key, c.duration, cap)
                continue
            usable.append(c)
        random.shuffle(usable)
        # interleave providers so one provider does not dominate
        usable.sort(key=lambda c: self.cfg.footage_providers.index(c.source) if c.source in self.cfg.footage_providers else 9)
        log.info("search %-28s -> %d usable candidates (errors: %s)", query, len(usable), "; ".join(errors) or "none")
        return usable

    # ---------------------------------------------------------------- download
    async def _download_http(self, cand: ClipCandidate, target: Path) -> bool:
        """Stream an HTTP(S) clip to disk with retry on 429/5xx. False on failure."""
        client = await self.client()
        host_key = "host:" + (httpx.URL(cand.download_url).host or "download")
        for attempt in range(1, 4):
            await self._throttle(host_key, 0.3)
            try:
                async with client.stream("GET", cand.download_url) as resp:
                    if resp.status_code >= 400:
                        raise FootageError(f"download HTTP {resp.status_code}")
                    tmp = target.with_suffix(target.suffix + ".part")
                    size = 0
                    with open(tmp, "wb") as fh:
                        async for chunk in resp.aiter_bytes(1 << 16):
                            fh.write(chunk)
                            size += len(chunk)
                            if size > 90 * 1024 * 1024:
                                raise FootageError("clip exceeds 90 MB, aborting")
                    tmp.replace(target)
                    log.info("downloaded %s (%s)", target.name, human_bytes(size))
                return True
            except Exception as exc:  # noqa: BLE001
                target.unlink(missing_ok=True)
                if attempt < 3:
                    log.warning("download attempt %d failed for %s: %s", attempt, cand.key, exc)
                    await asyncio.sleep(2.0 * attempt)
                else:
                    log.warning("download failed for %s after %d attempts: %s", cand.key, attempt, exc)
        return False

    async def download(self, cand: ClipCandidate) -> Clip | None:
        """Download (with cache) and return a ready-to-use clip."""
        cached_row = db.clip_get(cand.source, cand.source_id)
        if cached_row:
            path = Path(cached_row["path"])
            if path.exists() and path.stat().st_size > 10_000:
                duration = float(cached_row.get("duration") or 0) or media_duration(path)
                if duration >= self.cfg.min_clip_seconds() * 0.5:
                    db.clip_mark_used(cand.source, cand.source_id)
                    log.info("cache hit %s (%.1fs)", cand.key, duration)
                    return Clip(
                        path=path,
                        candidate=cand,
                        duration=duration,
                        width=int(cached_row.get("width") or cand.width),
                        height=int(cached_row.get("height") or cand.height),
                        from_cache=True,
                    )
            else:
                log.warning("cached file missing, re-downloading: %s", path)

        clips_dir = self.cfg.cache_dir / "clips" / cand.source
        clips_dir.mkdir(parents=True, exist_ok=True)
        suffix = Path(cand.download_url.split("?")[0]).suffix or ".mp4"
        if suffix.lower() not in {".mp4", ".mov", ".webm", ".mkv", ".ogv"}:
            suffix = ".mp4"
        target = clips_dir / f"{slugify(cand.query, 24)}-{cand.source_id}{suffix}"

        if not (target.exists() and target.stat().st_size > 10_000):
            if cand.source == "local" or cand.download_url.startswith("file:"):
                try:
                    if cand.download_url.startswith("file:"):
                        from urllib.parse import unquote, urlparse
                        p_str = unquote(urlparse(cand.download_url).path)
                        if len(p_str) > 2 and p_str[0] == "/" and p_str[2] == ":":
                            p_str = p_str[1:]
                        src = Path(p_str)
                    else:
                        src = Path(cand.download_url)
                    if not src.exists():
                        log.warning("local clip missing: %s", src)
                        return None
                    target.write_bytes(src.read_bytes())
                    log.info("linked local clip %s", target.name)
                except Exception as exc:  # noqa: BLE001
                    log.warning("could not use local clip %s: %s", cand.source_id, exc)
                    return None
            else:
                await self._download_http(cand, target)
        if not target.exists() or target.stat().st_size < 10_000:
            return None

        duration = media_duration(target)
        width, height = video_size(target)
        if duration < self.cfg.min_clip_seconds() * 0.5:
            log.warning("clip too short after download (%.1fs): %s", duration, target.name)
            target.unlink(missing_ok=True)
            return None
        cap = self.cfg.clip_max_source_duration
        if cap and (cand.archival or cand.source in self.cfg.duration_capped_sources) and duration > cap:
            log.info("skipping %s: source video is %.0fs (cap %.0fs) - long archival videos carry "
                     "title cards and interviews", cand.key, duration, cap)
            target.unlink(missing_ok=True)
            return None
        short_side = min(width, height) if width and height else 0
        if 0 < short_side < self.cfg.clip_min_short_side:
            # e.g. 320x212 NASA "mobile" files: cropping those to 1080x1920 looks like mush
            log.warning("clip too low resolution (%dx%d): %s - skipped", width, height, target.name)
            target.unlink(missing_ok=True)
            return None

        db.clip_add(
            cand.source, cand.source_id, str(target), cand.page_url, cand.author, cand.license,
            cand.query, duration, width, height,
        )
        db.clip_mark_used(cand.source, cand.source_id)
        return Clip(path=target, candidate=cand, duration=duration, width=width, height=height)


async def collect_clips(
    keywords: Iterable[str],
    count: int,
    cfg: Config | None = None,
    client: FootageClient | None = None,
) -> list[Clip]:
    """Get `count` distinct clips matching the script keywords in parallel."""
    cfg = cfg or get_config()
    client = client or FootageClient(cfg)
    kws = [k for k in keywords if k and k.strip()]
    if not kws:
        kws = [cfg.niche, "abstract background", "nature timelapse"]

    # 1. Search script keywords concurrently
    search_tasks = [client.search(q) for q in kws[:max(count, 4)]]
    search_results = await asyncio.gather(*search_tasks, return_exceptions=True)

    fresh_candidates: list[ClipCandidate] = []
    used_candidates: list[ClipCandidate] = []
    seen_keys: set[str] = set()

    from . import db

    for res in search_results:
        if isinstance(res, list):
            for cand in res:
                if cand.key not in seen_keys:
                    seen_keys.add(cand.key)
                    cached = db.clip_get(cand.source, cand.source_id)
                    if cached and cached.get("used_count", 0) > 0:
                        used_candidates.append(cand)
                    else:
                        fresh_candidates.append(cand)
                        
    candidates_pool = fresh_candidates + used_candidates

    # Backfill with commons extra queries if candidate pool is thin
    if len(candidates_pool) < count:
        extra_res = await asyncio.gather(
            *[client.search(q) for q in COMMONS_EXTRA_QUERIES[:3]], return_exceptions=True
        )
        for res in extra_res:
            if isinstance(res, list):
                for cand in res:
                    if cand.key not in seen_keys:
                        seen_keys.add(cand.key)
                        candidates_pool.append(cand)

    # 2. Download candidate clips concurrently for instant parallel retrieval
    to_download = candidates_pool[:count + 2]
    dl_results = await asyncio.gather(*[client.download(c) for c in to_download], return_exceptions=True)
    clips: list[Clip] = [c for c in dl_results if isinstance(c, Clip) and c is not None][:count]

    # Fallback to remainder if needed
    if len(clips) < count:
        for cand in candidates_pool[count + 2:]:
            c = await client.download(cand)
            if c:
                clips.append(c)
                if len(clips) >= count:
                    break

    if clips and len(clips) < count:
        log.info("only %d of %d clips found - sequences will be reused", len(clips), count)
    if not clips:
        raise FootageError(
            "no footage available. Add a PEXELS_API_KEY / PIXABAY_API_KEY to .env, "
            "or drop a few mp4 files into assets/stock/."
        )
    log.info("collected %d clips (%s)", len(clips), ", ".join(f"{c.candidate.key}" for c in clips))
    return clips


async def collect_clips_for_sentences(
    sentences: list[Any],
    niche: str,
    cfg: Config | None = None,
    client: FootageClient | None = None,
) -> list[Clip]:
    """1:1 Semantic Matching: For every spoken sentence beat, finds a real video clip
    that specifically depicts what the narrator is saying (avoids generic AI/irrelevant footage)."""
    cfg = cfg or get_config()
    client = client or FootageClient(cfg)
    clips: list[Clip] = []
    used_keys: set[str] = set()

    for idx, s in enumerate(sentences):
        # Extract keywords for this exact sentence
        raw_kws = getattr(s, "keywords", []) or []
        sentence_text = getattr(s, "text", str(s))
        
        # Build search queries prioritizing specific visual nouns
        queries = [k.strip() for k in raw_kws if k and len(k.strip()) >= 3]
        if not queries:
            words = [w.lower() for w in re.findall(r"\b[a-zA-Z]{3,}\b", sentence_text)
                     if w.lower() not in {"the", "and", "that", "this", "with", "from", "have", "been", "would", "could"}]
            if len(words) >= 2:
                queries.append(f"{words[0]} {words[1]}")
            elif words:
                queries.append(f"{words[0]} {niche}")
            else:
                queries.append(niche)

        found: Clip | None = None
        for q in queries[:2]:
            candidates = await client.search(q, per_provider=6)
            for cand in candidates:
                if cand.key not in used_keys:
                    c = await client.download(cand)
                    if c:
                        used_keys.add(cand.key)
                        found = c
                        log.info("1:1 visual match for sentence %d: '%s' -> %s (%s)",
                                 idx + 1, q, c.candidate.key, c.candidate.query)
                        break
            if found:
                break

        # Fallback to thematic niche visual query if no specific hit
        if not found:
            generic_fallback = COMMONS_EXTRA_QUERIES[idx % len(COMMONS_EXTRA_QUERIES)]
            candidates = await client.search(f"{niche} {generic_fallback}", per_provider=4)
            for cand in candidates:
                if cand.key not in used_keys:
                    c = await client.download(cand)
                    if c:
                        used_keys.add(cand.key)
                        found = c
                        break

        if found:
            clips.append(found)

    return clips


def credits_line(clips: list[Clip]) -> str:
    """Attribution string for CC-BY sources (Pexels/Pixabay need none, but we credit anyway)."""
    parts: list[str] = []
    for clip in clips:
        c = clip.candidate
        if c.source in {"pexels", "pixabay", "local"}:
            continue
        who = c.author or "Wikimedia Commons contributors"
        parts.append(f"{who} / {c.license}")
    if not parts:
        return ""
    uniq = list(dict.fromkeys(parts))[:5]
    return "Footage credits: " + "; ".join(uniq) + "."
