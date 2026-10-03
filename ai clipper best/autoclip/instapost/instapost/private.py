"""Second posting driver: instagrapi (Instagram's private mobile API).

Why this exists alongside ig.py
-------------------------------
The official Graph API (ig.py) needs a Business account, Meta App Review, and
a publicly reachable HTTPS URL for every video. This driver needs none of
that: it logs in like the phone app and uploads the local mp4 directly, from
a personal account, today.

What it costs
-------------
It violates Instagram's Terms of Use and accounts do get banned. instagrapi's
own README says private-API automation is "fragile in production" and tells
you to prefer the official API for business workflows. So this module is
built defensively:

* the login session is saved and REUSED -- logging in fresh every run is the
  single biggest ban trigger,
* every action is spaced by a randomised human-like delay,
* a conservative daily cap, far below anything Instagram would notice.

Same method names as ig.Instagram, so dashboard code can swap drivers.
"""

from __future__ import annotations

import os
import random
import time
from pathlib import Path

from .ig import IGError, load_env

SESSION = Path.home() / ".cache" / "instapost" / "session.json"

# Nothing like Meta's 25/day. A real person does not post 25 reels a day, and
# the point of this driver is to look like a real person.
DAILY_CAP = 8
MIN_GAP_S, MAX_GAP_S = 25.0, 70.0


# Owner's standing instruction: NO BAN RISK. This driver is therefore off by
# default and stays off unless someone deliberately sets the opt-in below.
# The code is kept because it is correct and the decision may change; it is
# simply not reachable by accident.
RISK_FLAG = "INSTAPOST_I_ACCEPT_BAN_RISK"


def _risk_accepted() -> bool:
    return os.environ.get(RISK_FLAG, "").strip().lower() in ("yes", "1", "true")


def _sleep_human() -> None:
    time.sleep(random.uniform(MIN_GAP_S, MAX_GAP_S))


class PrivateInstagram:
    """instagrapi wrapper with the same surface as ig.Instagram."""

    def __init__(self, username: str = "", password: str = ""):
        load_env()
        self.username = username or os.environ.get("IG_USERNAME", "").strip()
        self.password = password or os.environ.get("IG_PASSWORD", "").strip()
        self._cl = None

    def configured(self) -> bool:
        return bool(self.username and self.password) and _risk_accepted()

    # -- login ------------------------------------------------------------
    def client(self):
        """Log in, reusing the saved session whenever possible."""
        if self._cl is not None:
            return self._cl
        try:
            from instagrapi import Client
        except ImportError:
            raise IGError("instagrapi not installed: pip install instagrapi") from None
        if not _risk_accepted():
            raise IGError(
                "instagrapi driver is disabled: it breaks Instagram's terms "
                "and accounts do get banned. Use the official Graph API "
                f"driver, or set {RISK_FLAG}=yes if you accept losing the "
                "account.")
        if not self.username or not self.password:
            raise IGError("set IG_USERNAME and IG_PASSWORD in .env")

        cl = Client()
        cl.delay_range = [2, 6]          # instagrapi's own inter-request jitter
        SESSION.parent.mkdir(parents=True, exist_ok=True)

        if SESSION.exists():
            try:
                cl.load_settings(SESSION)
                cl.login(self.username, self.password)
                cl.get_timeline_feed()    # cheap call that proves the session
                self._cl = cl
                return cl
            except Exception:
                # Session died. Fall through to a fresh login, but keep the
                # device fingerprint so we do not look like a new phone.
                try:
                    old = cl.get_settings()
                    cl.set_settings({})
                    cl.set_uuids(old.get("uuids", {}))
                except Exception:
                    pass

        try:
            cl.login(self.username, self.password)
        except Exception as e:
            # Never let a password reach the logs.
            raise IGError(f"login failed: {type(e).__name__}: "
                          f"{str(e).replace(self.password, '***')[:200]}") from None
        cl.dump_settings(SESSION)
        try:
            SESSION.chmod(0o600)
        except OSError:
            pass
        self._cl = cl
        return cl

    # -- posting ----------------------------------------------------------
    def quota(self) -> tuple[int, int]:
        """Our own conservative cap -- the private API exposes no quota."""
        from . import store
        return store.today_count(), DAILY_CAP

    def post_reel(self, video_path: str | Path, caption: str = "",
                  share_to_feed: bool = True, cover_url: str = "") -> str:
        """`video_path` is a LOCAL file here, not a URL -- that is the point."""
        p = Path(video_path)
        if not p.exists():
            raise IGError(f"file not found: {p}")
        cl = self.client()
        _sleep_human()
        try:
            media = cl.clip_upload(p, caption[:2200], feed_show=share_to_feed)
        except Exception as e:
            raise IGError(f"{type(e).__name__}: {str(e)[:200]}") from None
        return str(getattr(media, "pk", "") or getattr(media, "id", ""))

    def post_story(self, video_path: str | Path) -> str:
        p = Path(video_path)
        if not p.exists():
            raise IGError(f"file not found: {p}")
        cl = self.client()
        _sleep_human()
        try:
            media = cl.video_upload_to_story(p)
        except Exception as e:
            raise IGError(f"{type(e).__name__}: {str(e)[:200]}") from None
        return str(getattr(media, "pk", "") or getattr(media, "id", ""))


def get_driver(name: str = ""):
    """Pick a driver: 'graph' (official) or 'private' (instagrapi).

    Defaults to whichever is actually configured, preferring the official one
    because it cannot get the account banned.
    """
    from .ig import Instagram

    name = (name or os.environ.get("INSTAPOST_DRIVER", "")).strip().lower()
    if name == "graph":
        return Instagram()
    if name == "private":
        return PrivateInstagram()
    # Default is always the official driver. Never silently fall back to the
    # private API just because the official one is not set up yet -- that
    # would trade the account for convenience without anyone deciding to.
    return Instagram()
