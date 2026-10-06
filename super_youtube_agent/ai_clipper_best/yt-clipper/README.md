# yt-clipper — automated YouTube → Shorts pipeline (EN/ES, AI voices, CapCut drafts)

A working scaffold that combines the best parts of the repos you shortlisted, instead of
forking any single one:

| Borrowed from | What it contributes here |
|---|---|
| **Anil-matcha/AI-Youtube-Shorts-Generator** (5.2k★, active) | yt-dlp → Whisper → LLM clip scoring → 9:16 reframing — the core loop |
| **MatteoFasulo/Whisper-TikTok** (340★, active) | Edge-TTS neural voices + word-level timestamps driving the captions |
| **Hao0321/video-autopilot-kit** (2.2k★, active) | `draft_content.json` output so clips open **editable** in CapCut |
| **NaufalRizqullah/opensource-clipping** (135★, active) | karaoke caption + B-roll/upload ideas |
| **rayventura/ShortGPT** (8.0k★, **last push Feb 2025**) | multi-language dubbing concept only — don't depend on it, it's stale |

## Why this shape

* **faster-whisper** over openai-whisper: 4–8× faster, same model weights, real word timings.
* **Edge-TTS word boundaries** give you dub-accurate caption timing for free — no second
  transcription pass on the Spanish audio.
* **.ass subtitles** instead of hundreds of `drawtext` filters: one file, one ffmpeg pass,
  real karaoke highlight (`\k` tags).
* **Both outputs**: a finished mp4 *and* a CapCut draft, so you can ship automatically or
  hand-polish the ones that look promising.

## Install

```bash
cd yt-clipper
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# ffmpeg + ffprobe must be on PATH (apt install ffmpeg / brew install ffmpeg)
export OPENAI_API_KEY=sk-...        # optional: LLM clip scoring + EN↔ES translation
```

Without the key everything still runs: the heuristic scorer picks clips and the TTS speaks
the original text (no translation).

## Use

```bash
python run.py --demo                                   # offline check, no deps needed
python run.py "https://youtu.be/XXXX" --langs en es    # 3 clips × 2 languages
python run.py --source long.mp4 --clips 5 --mode crop --captions block
python run.py "https://youtu.be/XXXX" --dry            # print the ffmpeg plan only
python run.py "https://youtu.be/XXXX" --no-dub         # keep original audio
```

Output per clip, per language, under `out/<lang>/`:
`…mp4` · `…mp3` (voiceover) · `…ass` (captions) · `out/capcut/<name>/draft_content.json`
plus `out/<videoid>.results.json` with hooks, scores and timings for your upload step.

## Module map

```
clipper/config.py      settings + Edge-TTS voice table (en-US-Christopher, es-ES-Alvaro…)
clipper/download.py    yt-dlp, ≤1080p mp4, cookie support for long/age-gated videos
clipper/transcribe.py  faster-whisper word timestamps + VAD, cached, SRT export
clipper/select.py      LLM JSON scorer  ->  heuristic fallback (hooks, wps, numbers, ?)
clipper/tts.py         translate() + synthesize() with WordBoundary timings
clipper/captions.py    karaoke/block .ass generator
clipper/render.py      cut → blurred-pillar or fill crop → duck+mix dub → burn captions
clipper/capcut.py      draft_content.json + draft_meta_info.json writer (µs timings)
clipper/pipeline.py    orchestration
```

## CapCut drafts

Copy `out/capcut/<name>/` into CapCut's project folder, then open the app:

* Windows `%LOCALAPPDATA%\CapCut\User Data\Projects\com.lveditor.draft`
* macOS `~/Movies/CapCut/User Data/Projects/com.lveditor.draft`

Media is referenced by absolute path — keep `out/` where it is, or relink inside CapCut.
The draft schema shifts between CapCut versions; if a draft refuses to open, create an empty
project in your installed version, diff its `draft_content.json` against ours, and bump
`version` / `new_version` in `clipper/capcut.py`.

## Next steps worth adding

1. **Face/action tracking crop** — MediaPipe face mesh → per-second crop centre keyframes
   (what `opensource-clipping` does); currently `--mode crop` is centre-fixed.
2. **Trend discovery** — YouTube Data API v3 `search.list?order=viewCount&publishedAfter=…`
   feeding URLs into the pipeline on a cron.
3. **Upload** — `youtube.videos.insert` with title/description generated from `hook`,
   one upload per language (or one channel per language, which performs better).
4. **Spanish localisation beyond audio** — translate the burned captions too; right now the
   `.ass` follows the dub, so it's already ES when `--langs es` is used with an API key.

## Legal note

Re-uploading someone else's footage is only safe when it's your content, licensed, or a
genuine transformative commentary edit. YouTube's reused-content policy demotes bulk clip
channels, and automated downloading can violate ToS — know what you're uploading.

## Batch mode (many scripts → many languages)

```bash
python batch.py samples/scripts.csv --langs en es --workers 4
python batch.py scripts/ --langs en es-mx --translate   # folder of .txt, LLM translation
```

CSV columns: `id,script[,langs][,voice]` — per-row `langs` (pipe-separated, e.g. `es|es-mx`)
and `voice` override the CLI defaults. Per item it writes `<lang>.mp3`, `<lang>.ass`
(karaoke), `<lang>.srt`, `<lang>.json` (word timings) plus a top-level `manifest.json`.
Resumable (finished items are skipped), threaded, and retries flaky TTS sockets.

Measured in this workspace: 3 scripts × 2–3 languages = **6 voiceovers, 1.3 min of audio,
in 3.5 s** — no API key, no ffmpeg needed for this stage.

### edge-tts gotcha (bit me while testing)

edge-tts **≥ 7.x defaults to `boundary="SentenceBoundary"`** — you silently get *zero*
word timings and your karaoke captions come out empty. You must pass
`Communicate(..., boundary="WordBoundary")`. Also, WordBoundary text strips punctuation;
`clipper/tts._restore_punctuation()` re-aligns against the source string to put it back.

## Bridge into MoneyPrinterTurbo

`../MoneyPrinterTurbo` is a trimmed, patched clone (see its `MODIFICATIONS.md`).
`to_mpt.py` converts our output into its `--batch-file` manifest:

```bash
python to_mpt.py out/batch/manifest.json -o ../MoneyPrinterTurbo/tasks.jsonl
python to_mpt.py out/<videoid>.results.json --materials clips/*.mp4 \
       -o ../MoneyPrinterTurbo/tasks.jsonl
cd ../MoneyPrinterTurbo && python cli.py --batch-file ./tasks.jsonl --stop-at video
```

`--tts ours` (default) passes our Edge-TTS mp3 as `custom_audio_file` so MPT skips TTS and
you keep the exact voice/timings batch.py produced. `--tts mpt` instead sets `voice_name`
per language (`es-MX-JorgeNeural-Male`, …) and lets MPT speak it.

MPT rejects unknown manifest fields, so every emitted key was validated against its
`VideoParams` model — 6/6 tasks pass. Manifest cap is 100 tasks / 1 MiB.
