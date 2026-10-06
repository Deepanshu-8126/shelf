#!/usr/bin/env python3
"""Bridge: yt-clipper output  ->  MoneyPrinterTurbo --batch-file manifest.

Two input modes (auto-detected):

  * out/<videoid>.results.json  (full pipeline)  -> one MPT task per clip x language,
    using the clip mp4 as a local material and our Edge-TTS mp3 as custom_audio_file.
  * out/batch/manifest.json     (batch.py voiceovers) -> one task per voiceover; pair it
    with --materials to supply the footage.

Usage:
  python to_mpt.py out/batch/manifest.json --materials clips/*.mp4 -o ../MoneyPrinterTurbo/tasks.jsonl
  python to_mpt.py out/abc123.results.json -o ../MoneyPrinterTurbo/tasks.jsonl

Then, in the MoneyPrinterTurbo folder:
  python cli.py --batch-file ./tasks.jsonl --stop-at video
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

# MPT wants "<voice>-<Gender>" (see get_all_azure_voices / parse_voice_name)
MPT_VOICES = {
    "en": "en-US-ChristopherNeural-Male",
    "en-f": "en-US-AriaNeural-Female",
    "es": "es-ES-AlvaroNeural-Male",
    "es-f": "es-ES-ElviraNeural-Female",
    "es-mx": "es-MX-JorgeNeural-Male",
    "es-ar": "es-AR-TomasNeural-Male",
    "es-co": "es-CO-GonzaloNeural-Male",
}
LANG_TAG = {"en": "en-US", "es": "es-ES", "es-mx": "es-MX",
            "es-ar": "es-AR", "es-co": "es-CO"}


def task(script: str, subject: str, lang: str, materials: list[str],
         audio: str | None, manifest_dir: Path, use_our_audio: bool) -> dict:
    """One VideoParams override object. Unknown fields are rejected by MPT, so
    every key here must exist on app.models.schema.VideoParams."""
    t = {
        "video_subject": subject[:100],
        "video_script": script,
        "video_source": "local",
        "video_materials": [{"provider": "local", "url": rel(m, manifest_dir), "duration": 0}
                            for m in materials],
        "video_aspect": "9:16",
        "video_fit_mode": "cover",
        "video_concat_mode": "sequential",
        "video_language": LANG_TAG.get(lang, lang),
        "subtitle_enabled": True,
        "subtitle_display_mode": "word_by_word",
        "subtitle_animation": "pop_spring",
        "subtitle_position": "two_thirds_bottom",
        "font_name": "BeVietnamPro-Bold.ttf",   # Latin font: keeps á é í ó ú ñ ¿ ¡
        "font_size": 64,
        "stroke_width": 2.5,
        "bgm_type": "random",
        "bgm_volume": 0.12,
        "n_threads": 4,
    }
    if use_our_audio and audio:
        # Reuse the voiceover batch.py already rendered; MPT then skips TTS entirely
        # and still builds subtitles from it (subtitle_provider = whisper|edge).
        t["custom_audio_file"] = rel(audio, manifest_dir)
    else:
        t["voice_name"] = MPT_VOICES.get(lang, MPT_VOICES["en"])
        t["voice_rate"] = 1.08
    return t


def rel(p: str | Path, base: Path) -> str:
    """Manifest-relative paths are resolved against the manifest dir by MPT."""
    p = Path(p).resolve()
    try:
        return str(p.relative_to(base.resolve()))
    except ValueError:
        return str(p)


def main() -> None:
    ap = argparse.ArgumentParser(description="yt-clipper -> MoneyPrinterTurbo manifest")
    ap.add_argument("source", help="results.json or batch/manifest.json")
    ap.add_argument("-o", "--out", default="tasks.jsonl")
    ap.add_argument("--materials", nargs="*", default=[],
                    help="footage to use when the source has no mp4s")
    ap.add_argument("--tts", choices=["ours", "mpt"], default="ours",
                    help="ours = reuse our Edge-TTS mp3s; mpt = let MPT speak the script")
    a = ap.parse_args()

    data = json.loads(Path(a.source).read_text())
    out_path = Path(a.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    mdir = out_path.parent
    tasks = []

    if isinstance(data, dict) and "clips" in data:          # full pipeline results
        for c in data["clips"]:
            mats = [c["mp4"]] if c.get("mp4") and Path(c["mp4"]).exists() else a.materials
            tasks.append(task(c.get("title") or c.get("hook", ""),
                              c.get("hook") or c.get("title", ""), c["lang"], mats,
                              c.get("voice"), mdir, a.tts == "ours"))
    else:                                                    # batch.py manifest
        for r in data:
            if r.get("status") == "failed":
                continue
            info = Path(r["mp3"]).with_suffix(".json")
            text = r.get("text") or (json.loads(info.read_text())["text"]
                                     if info.exists() else "")
            tasks.append(task(text, f"{r['id']} ({r['lang']})", r["lang"],
                              a.materials, r["mp3"], mdir, a.tts == "ours"))

    with out_path.open("w", encoding="utf-8") as f:
        for t in tasks:
            f.write(json.dumps(t, ensure_ascii=False) + "\n")

    if len(tasks) > 100:
        print(f"!! {len(tasks)} tasks — MPT caps a manifest at 100; split the file.")
    langs = sorted({t.get("video_language", "?") for t in tasks})
    print(f"wrote {len(tasks)} tasks -> {out_path}  (languages: {', '.join(langs)})")
    print(f"next:  cd {Path('../MoneyPrinterTurbo').resolve()} && "
          f"python cli.py --batch-file ./{out_path.name} --stop-at video")


if __name__ == "__main__":
    main()
