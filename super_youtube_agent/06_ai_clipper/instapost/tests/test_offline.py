"""Offline tests. No network, no Instagram account, no token needed.

The whole publish flow is exercised against a fake `_call` so the container ->
poll -> publish sequence and the error paths are covered without touching Meta.
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from instapost import store                      # noqa: E402
from instapost.ig import IGError, Instagram, check_clip   # noqa: E402
import instapost.ig as _ig_mod                            # noqa: E402

_ig_mod.time.sleep = lambda *_a, **_k: None   # keep the suite instant


class Fake(Instagram):
    """Instagram with the HTTP layer swapped out for a script of replies."""

    def __init__(self, statuses=("IN_PROGRESS", "FINISHED")):
        super().__init__(user_id="123", token="fake-token")
        self.statuses = list(statuses)
        self.calls: list[tuple[str, str, dict]] = []

    def _call(self, method, path, params):
        self.calls.append((method, path, params))
        if path.endswith("content_publishing_limit"):
            return {"data": [{"quota_usage": 3, "config": {"quota_total": 25}}]}
        if path.endswith("/media"):
            return {"id": "CONTAINER1"}
        if path.endswith("media_publish"):
            return {"id": "MEDIA1"}
        return {"status_code": self.statuses.pop(0) if self.statuses
                else "FINISHED"}


def test_reel_flow():
    ig = Fake()
    mid = ig.post_reel("https://h/v.mp4", "hello #shorts")
    assert mid == "MEDIA1"
    create = [c for c in ig.calls if c[1].endswith("/media")][0]
    assert create[2]["media_type"] == "REELS"
    assert create[2]["video_url"] == "https://h/v.mp4"
    assert create[2]["share_to_feed"] == "true"
    # It must poll before publishing, not publish straight away.
    order = [c[1] for c in ig.calls]
    assert order.index("CONTAINER1") < order.index("123/media_publish")
    print("  reel_flow    ok  -> container, poll, publish in order")


def test_story_flow():
    ig = Fake(statuses=("FINISHED",))
    mid = ig.post_story("https://h/v.mp4")
    assert mid == "MEDIA1"
    create = [c for c in ig.calls if c[1].endswith("/media")][0]
    assert create[2]["media_type"] == "STORIES"
    assert "caption" not in create[2], "Meta ignores caption on stories"
    print("  story_flow   ok  -> media_type=STORIES, no caption")


def test_container_error():
    ig = Fake(statuses=("ERROR",))
    try:
        ig.post_reel("https://h/v.mp4", "x")
    except IGError as e:
        assert "ERROR" in str(e)
        print("  error_path   ok  -> container ERROR raises, no publish call")
        assert not any(c[1].endswith("media_publish") for c in ig.calls)
        return
    raise AssertionError("expected IGError")


def test_quota():
    used, total = Fake().quota()
    assert (used, total) == (3, 25)
    print("  quota        ok  -> 3/25 parsed")


def test_checks():
    f = Path(tempfile.mkdtemp()) / "a.mp4"
    f.write_bytes(b"x" * 1000)
    assert check_clip(f, 12, 1080, 1920) == []
    bad = check_clip(f, 200, 1280, 720)
    assert len(bad) == 2, bad
    assert check_clip(f.parent / "nope.mp4", 12, 1080, 1920)
    print("  checks       ok  -> duration, aspect and missing file caught")


def test_no_double_post():
    d = Path(tempfile.mkdtemp()) / "posted.json"
    assert store.already_posted("clip1", "reel", d) is None
    store.record("clip1", "reel", "M1", "cap", d)
    assert store.already_posted("clip1", "reel", d)["media_id"] == "M1"
    # A story of the same clip is a separate thing and must still be allowed.
    assert store.already_posted("clip1", "story", d) is None
    print("  no_double    ok  -> reel logged, story still allowed")


def test_token_never_logged():
    """An API error must not leak the access token into the message."""
    ig = Instagram(user_id="1", token="SECRET-TOKEN-VALUE")
    try:
        ig._call("GET", "nonexistent.invalid", {})
    except IGError as e:
        assert "SECRET-TOKEN-VALUE" not in str(e)
        print("  no_leak      ok  -> token absent from error text")
        return
    raise AssertionError("expected IGError")


def test_private_driver():
    """The instagrapi driver must take a LOCAL path, not a URL, and must not
    leak the password when login fails."""
    from instapost.private import PrivateInstagram, get_driver
    from instapost.ig import IGError

    d = PrivateInstagram(username="u", password="hunter2")
    # Off by default: the owner does not want ban risk.
    assert not d.configured(), "private driver must be disabled by default"
    try:
        d.client()
    except IGError as e:
        assert "disabled" in str(e)
    else:
        raise AssertionError("disabled driver must refuse to log in")
    # Never a silent fallback to the risky driver.
    assert type(get_driver()).__name__ == "Instagram"
    try:
        d.post_reel("/definitely/not/here.mp4", "x")
    except IGError as e:
        assert "not found" in str(e)
        assert "hunter2" not in str(e)
    else:
        raise AssertionError("expected IGError for a missing file")

    used, cap = d.quota()
    assert cap <= 10, "private driver cap must stay conservative"
    # Driver choice must be explicit and must not silently pick the risky one.
    assert type(get_driver("graph")).__name__ == "Instagram"
    assert type(get_driver("private")).__name__ == "PrivateInstagram"
    print(f"  private      ok  -> local path enforced, cap {cap}/day, no leak")


if __name__ == "__main__":
    print("instapost offline tests")
    for fn in (test_reel_flow, test_story_flow, test_container_error,
               test_quota, test_checks, test_no_double_post,
               test_token_never_logged, test_private_driver):
        fn()
    print("all passed")
