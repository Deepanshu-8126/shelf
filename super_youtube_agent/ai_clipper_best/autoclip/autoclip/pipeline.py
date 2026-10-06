"""End to end: link (or channel / search) -> branded vertical clips.

    from autoclip import run
    run("https://youtu.be/xxxx", clips=2, genre="reality")
"""
from __future__ import annotations

import json
import os
import re
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

from . import brand, captions, hooks, sources, transcribe
from .render import probe_size, render_clip

DEFAULT_PROFILE = Path(__file__).parent.parent / "profiles" / "default.json"


def slug(s: str, n: int = 36) -> str:
    s = re.sub(r"[^\w\s-]", "", s, flags=re.U).strip().lower()
    return re.sub(r"[\s_]+", "-", s)[:n].strip("-") or "clip"


# /tmp is a 993 MB tmpfs here, and a 70-minute 1080p episode is 1.4 GB. When it
# fills, yt-dlp does not error -- it stalls and the run dies with an empty log.
# ~/.cache sits on the 20 GB root volume and is excluded from workspace
# snapshots, so it costs nothing and holds a full episode.
DEFAULT_WORKDIR = os.environ.get("AUTOCLIP_WORKDIR") or str(
    Path.home() / ".cache" / "autoclip")


def load_profile(path: str | Path | None) -> dict:
    p = Path(path or DEFAULT_PROFILE)
    cfg = json.loads(p.read_text())
    root = Path(__file__).parent.parent
    for k in ("watermark", "title_font", "emoji_dir", "fontdir"):
        if cfg.get(k):
            cfg[k] = str((root / cfg[k]).resolve()) if not os.path.isabs(cfg[k]) else cfg[k]
    return cfg


def _one(job: dict) -> dict:
    """Runs in a worker process."""
    r = render_clip(job["src"], job["start"], job["end"], Path(job["out"]),
                    profile=job["profile"], ass=Path(job["ass"]) if job["ass"] else None,
                    title_png=Path(job["title_png"]) if job["title_png"] else None,
                    watermark=job["profile"].get("watermark"),
                    punches=job["punches"], safe_level=job["safe_level"])
    return {**{k: job[k] for k in ("name", "title", "start", "end", "hook")}, **r}


def run(target: str, *, clips: int = 2, genre: str = "vlog", outdir: str = "Shorts",
        caption_style: str | None = None,
        caption_box: bool | None = None,
        profile: str | Path | None = None, limit: int = 1, safe_level: int = 1,
        workdir: str = DEFAULT_WORKDIR, langs: tuple[str, ...] = ("hi", "en"),
        whisper_model: str = "base", height: int = 1080, workers: int | None = None,
        crf: int | None = None,
        api_key: str | None = None, cookies: str | None = None) -> list[dict]:
    t0 = time.time()
    cfg = load_profile(profile)
    if crf is not None:
        cfg["crf"] = int(crf)
    out_root = Path(outdir)
    work = Path(workdir)
    api_key = api_key or os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("AUTOCLIP_LLM_BASE")
    model = os.getenv("AUTOCLIP_LLM_MODEL", "gpt-4o-mini")
    if not api_key and os.getenv("GROQ_API_KEY"):      # free tier, no card
        api_key = os.getenv("GROQ_API_KEY")
        base_url = base_url or "https://api.groq.com/openai/v1"
        model = os.getenv("AUTOCLIP_LLM_MODEL", "llama-3.3-70b-versatile")
    results: list[dict] = []

    videos = sources.expand(target, limit=limit)
    print(f"[1/5] {len(videos)} video(s) queued")

    for v in videos:
        print(f"[2/5] download  {v['title'][:60]!r}")
        meta = sources.download(v["url"], work / "src", height=height, cookies=cookies)

        print("[3/5] transcript", end=" ", flush=True)
        words, src_kind = transcribe.get_words(
            v["url"], meta["path"], work / f"{meta['id']}.words.json",
            langs=langs, model=whisper_model)
        words = transcribe.dedupe(words)
        print(f"-> {len(words)} words via {src_kind}")

        picked = hooks.select(words, n=clips, genre=genre, api_key=api_key,
                              model=model, base_url=base_url)
        print(f"[4/5] {len(picked)} clip(s): " +
              ", ".join(f"{c['start']:.0f}-{c['end']:.0f}s" for c in picked))

        sw, sh = probe_size(meta["path"])
        mv = captions.auto_margin_v(cfg["width"], cfg["height"], sw, sh,
                                    cfg.get("blur_bg", True))
        vdir = out_root / slug(meta["title"])
        vdir.mkdir(parents=True, exist_ok=True)
        jobs = []
        for i, c in enumerate(picked, 1):
            # prefer the LLM title for the filename; fall back to the hook text
            label = c.get("title") or c.get("hook", "")
            name = f"{cfg.get('channel','clip')}_{i:02d}_{slug(label, 24)}"
            rel = [{"word": w["word"], "start": w["start"] - c["start"],
                    "end": w["end"] - c["start"]}
                   for w in words if c["start"] <= w["start"] < c["end"]]
            ass = captions.build(rel, vdir / f"{name}.ass", width=cfg["width"],
                                 height=cfg["height"], font=cfg["caption_font"],
                                 size_pct=cfg.get("caption_size_pct", 0.062),
                                 margin_v=mv, primary=cfg.get("caption_color", "&H00FFFFFF"),
                                 highlight=cfg.get("caption_highlight", "&H0024E8FF"),
                                 style=caption_style or cfg.get("caption_style", "karaoke"),
                                 box=bool(cfg.get("caption_box", False)) if caption_box is None else caption_box,
                                 max_cps=float(cfg.get("max_cps", 20.0)))
            (vdir / f"{name}.srt").write_text(captions.to_srt(rel), encoding="utf-8")
            title = c.get("title") or (c.get("hook", "")[:28] + " 🔥")
            tp = brand.title_card(title, vdir / f"{name}_title.png", width=cfg["width"],
                                  font_path=cfg["title_font"],
                                  emoji_dir=Path(cfg["emoji_dir"]),
                                  accent=cfg.get("accent", "#E8192C")) \
                if cfg.get("title_card", True) else None
            dur = c["end"] - c["start"]
            punches = [[1.2, 4.6], [max(dur - 9, 6), max(dur - 5, 9)]]
            jobs.append({"src": meta["path"], "start": c["start"], "end": c["end"],
                         "out": str(vdir / f"{name}.mp4"), "ass": str(ass),
                         "title_png": str(tp) if tp else None, "punches": punches,
                         "safe_level": safe_level, "profile": cfg, "name": name,
                         "title": title, "hook": c.get("hook", "")})

        # x264 already threads well. Running one ffmpeg per core OVERSUBSCRIBES the box:
        # on a 2-core machine two parallel renders thrashed for 19 min and then died,
        # while the same two clips run sequentially in ~70 s. One worker per 2 cores.
        cpu = os.cpu_count() or 2
        nw = workers or max(1, min(len(jobs), cpu // 2))
        print(f"[5/5] rendering {len(jobs)} clip(s) on {nw} worker(s) ({cpu} cores)")
        failed: list[dict] = []
        if nw > 1 and len(jobs) > 1:
            with ProcessPoolExecutor(max_workers=nw) as ex:
                futs = {ex.submit(_one, j): j for j in jobs}
                for f in as_completed(futs):
                    try:
                        r = f.result()
                        print(f"   ✓ {r['name']}  {r['duration']}s  {r['size_mb']} MB")
                        results.append(r)
                    except Exception as exc:  # noqa: BLE001
                        print(f"   ! {futs[f]['name']} failed in parallel ({str(exc)[:80]}),"
                              f" will retry sequentially")
                        failed.append(futs[f])
        else:
            failed = jobs
        for j in failed:
            try:
                r = _one(j)
                print(f"   ✓ {r['name']}  {r['duration']}s  {r['size_mb']} MB")
                results.append(r)
            except Exception as exc:  # noqa: BLE001
                print(f"   ✗ {j['name']} FAILED: {str(exc)[:200]}")

        (vdir / "clips.json").write_text(
            json.dumps({"source": meta, "transcript_source": src_kind,
                        # kept so the dashboard can re-render a single clip
                        "profile": cfg, "safe_level": safe_level,
                        "caption_box": (bool(cfg.get("caption_box", False))
                                        if caption_box is None else caption_box),
                        "caption_style": caption_style or cfg.get("caption_style",
                                                                  "karaoke"),
                        "words_json": str(wj) if (wj := work / f"{meta['id']}.words.json")
                        .is_file() else "",
                        "clips": results}, indent=2, ensure_ascii=False))

    print(f"done in {time.time() - t0:.0f}s -> {out_root}")
    return results
