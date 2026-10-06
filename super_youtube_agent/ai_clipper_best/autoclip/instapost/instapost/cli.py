"""Post one clip to Instagram from the command line.

    python3 -m instapost.cli --video-url https://host/video?p=ID \
        --caption "title #shorts" --story
"""

from __future__ import annotations

import argparse
import sys

from .ig import IGError, Instagram
from . import store


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser("instapost")
    p.add_argument("--video-url", required=True,
                   help="public HTTPS url Meta can fetch the mp4 from")
    p.add_argument("--caption", default="")
    p.add_argument("--clip-id", default="", help="key used to avoid reposting")
    p.add_argument("--story", action="store_true",
                   help="also push it to Stories (counts as a 2nd post)")
    p.add_argument("--no-feed", action="store_true",
                   help="keep it out of the main feed")
    a = p.parse_args(argv)

    ig = Instagram()
    if not ig.configured():
        print("not configured: set IG_USER_ID and IG_ACCESS_TOKEN in .env")
        return 2
    try:
        used, total = ig.quota()
        print(f"quota {used}/{total} used in the last 24h")
        if used >= total:
            print("daily publishing limit reached, try later")
            return 1
        if a.clip_id and store.already_posted(a.clip_id, "reel"):
            print(f"{a.clip_id} already posted as a reel, skipping")
        else:
            mid = ig.post_reel(a.video_url, a.caption,
                               share_to_feed=not a.no_feed)
            print(f"reel published: {mid}")
            store.record(a.clip_id or a.video_url, "reel", mid, a.caption)
        if a.story:
            if a.clip_id and store.already_posted(a.clip_id, "story"):
                print(f"{a.clip_id} already on story, skipping")
            else:
                sid = ig.post_story(a.video_url)
                print(f"story published: {sid}")
                store.record(a.clip_id or a.video_url, "story", sid)
    except IGError as e:
        print(f"instagram error: {e}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
