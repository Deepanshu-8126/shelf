"""Instagram Reels + Stories publishing over Meta's Content Publishing API.

The whole design is forced by three Meta rules that cannot be worked around:

1. Meta's servers FETCH the video from a public HTTPS URL. There is no plain
   file upload on this endpoint, so the mp4 has to be reachable from the
   internet at the moment you publish. The autoclip dashboard already serves
   every clip at /video, so we hand Meta that URL.
2. Publishing is a two-step container flow: create the container, poll it
   until it says FINISHED, only then publish. Publishing too early fails.
3. 25 published items per account per 24 hours. Reels and Stories share the
   same bucket, so posting a Reel + a Story is 2 of your 25.

Stdlib only -- no requests, no SDK. Installed packages do not survive here.
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

# graph.instagram.com is the "Instagram Login" path: no Facebook Page needed.
# Set INSTAPOST_BASE to https://graph.facebook.com/v21.0 for the older
# "Facebook Login" path, which does require a linked Page.
DEFAULT_BASE = "https://graph.instagram.com/v23.0"

TIMEOUT = 60


class IGError(RuntimeError):
    """A Meta API error, with the message Meta actually returned."""


def _env(name: str, default: str = "") -> str:
    v = os.environ.get(name, default)
    return v.strip() if v else default


def load_env(path: str | Path = "/home/user/autoclip/.env") -> None:
    """Read KEY=VALUE lines into os.environ without printing anything.

    Values are secrets -- this never logs them.
    """
    p = Path(path)
    if not p.exists():
        return
    for line in p.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


class Instagram:
    def __init__(self, user_id: str = "", token: str = "", base: str = ""):
        load_env()
        self.user_id = user_id or _env("IG_USER_ID")
        self.token = token or _env("IG_ACCESS_TOKEN")
        self.base = (base or _env("INSTAPOST_BASE") or DEFAULT_BASE).rstrip("/")

    # -- plumbing ---------------------------------------------------------
    def configured(self) -> bool:
        return bool(self.user_id and self.token)

    def _call(self, method: str, path: str, params: dict) -> dict:
        body = dict(params)
        body["access_token"] = self.token
        url = f"{self.base}/{path.lstrip('/')}"
        data = urllib.parse.urlencode(body).encode()
        if method == "GET":
            url = f"{url}?{data.decode()}"
            data = None
        req = urllib.request.Request(url, data=data, method=method)
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
                return json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            raw = e.read().decode(errors="replace")
            try:
                msg = json.loads(raw)["error"]["message"]
            except Exception:
                msg = raw[:300]
            # Never echo the token back out of here.
            raise IGError(msg) from None
        except urllib.error.URLError as e:
            raise IGError(f"network: {e.reason}") from None

    # -- public -----------------------------------------------------------
    def quota(self) -> tuple[int, int]:
        """(used, total) published items in the rolling 24 h window."""
        d = self._call("GET", f"{self.user_id}/content_publishing_limit",
                       {"fields": "config,quota_usage"})
        item = (d.get("data") or [{}])[0]
        return (int(item.get("quota_usage", 0)),
                int((item.get("config") or {}).get("quota_total", 25)))

    def _container(self, params: dict) -> str:
        d = self._call("POST", f"{self.user_id}/media", params)
        cid = d.get("id")
        if not cid:
            raise IGError(f"no container id in response: {d}")
        return str(cid)

    def _wait(self, container_id: str, timeout: float = 600) -> None:
        """Poll until FINISHED. Backs off so a long video does not spam Meta."""
        deadline = time.time() + timeout
        delay = 5.0
        while time.time() < deadline:
            d = self._call("GET", container_id, {"fields": "status_code,status"})
            code = d.get("status_code", "")
            if code == "FINISHED":
                return
            if code in ("ERROR", "EXPIRED"):
                raise IGError(f"container {code}: {d.get('status', '')}")
            time.sleep(delay)
            delay = min(delay * 1.5, 30.0)
        raise IGError("container still processing after 10 minutes")

    def _publish(self, container_id: str) -> str:
        d = self._call("POST", f"{self.user_id}/media_publish",
                       {"creation_id": container_id})
        mid = d.get("id")
        if not mid:
            raise IGError(f"no media id in response: {d}")
        return str(mid)

    def post_reel(self, video_url: str, caption: str = "",
                  share_to_feed: bool = True, cover_url: str = "") -> str:
        params = {"media_type": "REELS", "video_url": video_url,
                  "caption": caption[:2200],
                  "share_to_feed": "true" if share_to_feed else "false"}
        if cover_url:
            params["cover_url"] = cover_url
        cid = self._container(params)
        self._wait(cid)
        return self._publish(cid)

    def post_story(self, video_url: str) -> str:
        """Stories take no caption -- Meta ignores it on media_type=STORIES."""
        cid = self._container({"media_type": "STORIES", "video_url": video_url})
        self._wait(cid)
        return self._publish(cid)


def verify_public(url: str, timeout: float = 25.0) -> str:
    """Prove Meta will be able to fetch `url`, before we ask it to.

    "Media URL not accessible" is the single most common publish failure and
    Meta reports it minutes later, after the container has already been
    created. One ranged GET here turns that into an instant, clear error.

    Returns "" when fine, else the reason it would fail.
    """
    req = urllib.request.Request(url, headers={"Range": "bytes=0-1023"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            code = r.status
            ctype = r.headers.get("Content-Type", "")
            body = r.read(1024)
    except urllib.error.HTTPError as e:
        return f"public URL returned HTTP {e.code}"
    except Exception as e:
        return f"public URL unreachable: {type(e).__name__}"
    if code not in (200, 206):
        return f"public URL returned HTTP {code}"
    if "video" not in ctype:
        return f"public URL served '{ctype}', not video"
    if len(body) < 8 or b"ftyp" not in body[:64]:
        return "public URL did not serve an mp4 (no ftyp box)"
    return ""


# -- local checks, so a bad clip fails here instead of 5 minutes into Meta --

REEL_MIN_S, REEL_MAX_S = 3.0, 90.0
STORY_MIN_S, STORY_MAX_S = 3.0, 90.0
MAX_MB = 100.0


def check_clip(path: str | Path, duration: float, width: int, height: int,
               story: bool = False) -> list[str]:
    """Return a list of reasons Meta would reject this clip. Empty == fine."""
    p = Path(path)
    bad: list[str] = []
    if not p.exists():
        return [f"file missing: {p}"]
    mb = p.stat().st_size / 1e6
    if mb > MAX_MB:
        bad.append(f"{mb:.0f} MB is over Meta's {MAX_MB:.0f} MB limit")
    lo, hi = (STORY_MIN_S, STORY_MAX_S) if story else (REEL_MIN_S, REEL_MAX_S)
    if not (lo <= duration <= hi):
        bad.append(f"{duration:.1f}s is outside {lo:.0f}-{hi:.0f}s")
    if height and width:
        ratio = width / height
        if abs(ratio - 9 / 16) > 0.02:
            bad.append(f"aspect {width}x{height} is not 9:16 "
                       "(Reels tab needs 9:16)")
    return bad
