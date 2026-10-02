"""Offline sanity check - no ffmpeg, no network, no API keys.

Runs: sample transcript -> heuristic clip selection -> karaoke .ass ->
CapCut draft -> the exact ffmpeg command the real run would execute.
"""
from __future__ import annotations

import json
from pathlib import Path

from clipper import capcut, captions, render, select
from clipper.config import settings

ROOT = Path(__file__).parent


def main() -> None:
    tr = json.loads((ROOT / "samples" / "transcript.json").read_text())
    settings.work_dir = ROOT / "out"
    settings.clips_per_video = 2

    clips = select.heuristic_select(tr)
    print(f"selected {len(clips)} clips")
    for i, c in enumerate(clips, 1):
        print(f"  {i}. {c['start']:>6.1f}-{c['end']:<6.1f} score={c['score']:<5} {c['hook']!r}")

        words = [{**w, "start": w["start"] - c["start"], "end": w["end"] - c["start"]}
                 for w in c["words"]]
        ass = captions.build_ass(words, ROOT / "out" / f"demo_{i}.ass")
        draft = capcut.build_draft(ROOT / "out" / f"demo_{i}.mp4", c["end"] - c["start"],
                                   f"demo_{i}_en", words=words)
        cmd = render.render_clip("source.mp4", c["start"], c["end"],
                                 ROOT / "out" / f"demo_{i}.mp4", ass=ass,
                                 voice_audio=None, dry=True)
        print(f"     ass   : {ass.relative_to(ROOT)} ({len(ass.read_text().splitlines())} lines)")
        print(f"     capcut: {draft.relative_to(ROOT)}/draft_content.json")
        print(f"     ffmpeg: {cmd[:150]}...")


if __name__ == "__main__":
    main()
