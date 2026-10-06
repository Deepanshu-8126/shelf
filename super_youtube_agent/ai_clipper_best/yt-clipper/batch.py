#!/usr/bin/env python3
"""Batch runner — the 'queue 100 scripts' loop.

Input: a CSV with columns  id,script[,langs][,voice]   (langs/voice optional)
       or a folder of .txt files (filename = id).

For every script x every language it writes:
  out/batch/<id>/<lang>.mp3   voiceover (Edge-TTS, free, no API key)
  out/batch/<id>/<lang>.ass   karaoke captions synced to that voiceover
  out/batch/<id>/<lang>.srt   plain subtitles (for YouTube upload)
  out/batch/manifest.json     every row: text, voice, duration, word count, paths

Resumable (skips finished items), parallel, and retries flaky TTS connections.

  python batch.py scripts.csv --langs en es --workers 4
  python batch.py scripts/ --langs en es-mx --translate
"""
from __future__ import annotations

import argparse
import asyncio
import csv
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from clipper import captions, tts
from clipper.config import VOICES, settings

ROOT = Path(__file__).parent


def load_items(src: Path) -> list[dict]:
    items = []
    if src.is_dir():
        for f in sorted(src.glob("*.txt")):
            items.append({"id": f.stem, "script": f.read_text(encoding="utf-8").strip()})
    else:
        with open(src, newline="", encoding="utf-8") as fh:
            for i, row in enumerate(csv.DictReader(fh), 1):
                if not (row.get("script") or "").strip():
                    continue
                items.append({
                    "id": (row.get("id") or f"item{i:03d}").strip(),
                    "script": row["script"].strip(),
                    "langs": [x for x in (row.get("langs") or "").split("|") if x],
                    "voice": (row.get("voice") or "").strip(),
                })
    return items


def srt_from_words(words: list[dict], max_words: int = 8) -> str:
    def ts(t: float) -> str:
        h, r = divmod(max(t, 0), 3600)
        m, s = divmod(r, 60)
        return f"{int(h):02d}:{int(m):02d}:{int(s):02d},{int((s % 1) * 1000):03d}"

    out, n = [], 0
    for g in captions.chunk_words(words, max_words, max_gap=1.2):
        n += 1
        out.append(f"{n}\n{ts(g[0]['start'])} --> {ts(g[-1]['end'])}\n"
                   f"{' '.join(w['word'] for w in g)}\n")
    return "\n".join(out)


def do_one(item: dict, lang: str, out_root: Path, translate: bool,
           retries: int = 3) -> dict:
    d = out_root / item["id"]
    d.mkdir(parents=True, exist_ok=True)
    mp3, ass, srt = d / f"{lang}.mp3", d / f"{lang}.ass", d / f"{lang}.srt"
    rec = {"id": item["id"], "lang": lang, "mp3": str(mp3), "ass": str(ass),
           "srt": str(srt), "voice": item.get("voice") or VOICES.get(lang, lang)}

    if mp3.exists() and ass.exists() and (d / f"{lang}.json").exists():
        rec.update(json.loads((d / f"{lang}.json").read_text()), status="cached")
        return rec

    text = item["script"]
    if translate and lang.split("-")[0] != item.get("src_lang", "en"):
        text = tts.translate(text, lang.split("-")[0])

    last = None
    for attempt in range(retries):
        try:
            res = tts.synthesize(text, item.get("voice") or lang, mp3)
            break
        except Exception as exc:  # noqa: BLE001  flaky websocket -> back off
            last = exc
            time.sleep(1.5 * (attempt + 1))
    else:
        return {**rec, "status": "failed", "error": str(last)}

    words = res["words"]
    captions.build_ass(words, ass)
    srt.write_text(srt_from_words(words), encoding="utf-8")
    info = {"text": text, "voice": res["voice"], "words": len(words),
            "duration": round(words[-1]["end"], 2) if words else 0.0}
    (d / f"{lang}.json").write_text(json.dumps({**info, "word_times": words},
                                               ensure_ascii=False))
    return {**rec, **info, "status": "ok"}


def main() -> None:
    p = argparse.ArgumentParser(description="Batch multi-language voiceover generator")
    p.add_argument("source", help="scripts.csv or a folder of .txt files")
    p.add_argument("--langs", nargs="+", default=["en", "es"])
    p.add_argument("--translate", action="store_true",
                   help="translate each script per language (needs OPENAI_API_KEY)")
    p.add_argument("--workers", type=int, default=4)
    p.add_argument("--out", default=str(ROOT / "out" / "batch"))
    a = p.parse_args()

    items = load_items(Path(a.source))
    out_root = Path(a.out)
    out_root.mkdir(parents=True, exist_ok=True)
    jobs = [(it, lang) for it in items for lang in (it.get("langs") or a.langs)]
    print(f"{len(items)} scripts x langs -> {len(jobs)} voiceovers "
          f"({a.workers} workers, translate={a.translate})")

    results = []
    with ThreadPoolExecutor(max_workers=a.workers) as pool:
        futs = {pool.submit(do_one, it, lang, out_root, a.translate): (it["id"], lang)
                for it, lang in jobs}
        for n, f in enumerate(as_completed(futs), 1):
            r = f.result()
            results.append(r)
            flag = {"ok": "✓", "cached": "·", "failed": "✗"}[r["status"]]
            print(f"  {flag} [{n}/{len(futs)}] {r['id']} [{r['lang']}] "
                  f"{r.get('voice','')} {r.get('duration','')}s {r.get('error','')}")

    results.sort(key=lambda r: (r["id"], r["lang"]))
    (out_root / "manifest.json").write_text(json.dumps(results, indent=2, ensure_ascii=False))
    ok = sum(r["status"] != "failed" for r in results)
    total = sum(r.get("duration", 0) for r in results)
    print(f"\n{ok}/{len(results)} succeeded · {total/60:.1f} min of audio · "
          f"manifest: {out_root/'manifest.json'}")


if __name__ == "__main__":
    main()
