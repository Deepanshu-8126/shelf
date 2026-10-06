# autoclip

**Ek link do → branded vertical shorts bahar.** Download, transcript, hook detection,
kinetic Hindi/English captions, logo watermark, emoji title card, copyright-safe
transforms — sab automatic.

```bash
autoclip "https://youtu.be/VIDEOID" --clips 2
autoclip "https://www.youtube.com/@BiggBoss" --limit 3 --clips 2 --genre reality
autoclip "ytsearch5:bigg boss fight" --genre reality --safe 2
```

Measured end-to-end on a 16-minute Hindi vlog (2-core box, no GPU):
**link se 2 finished shorts tak — 85 seconds.**

---

## Kyun (why this exists)

Most auto-clippers assume English, a GPU, and an OpenAI key. This one is built for
Indian clip channels: Hindi-first captions, works on a cheap CPU box, and runs without
any API key (an LLM is used only if you give it one).

## Install

```bash
git clone https://github.com/<you>/autoclip.git
cd autoclip
pip install -r requirements.txt     # ffmpeg bundled via imageio-ffmpeg
pip install -e .                    # gives you the `autoclip` command
export OPENAI_API_KEY=sk-...        # OPTIONAL: smarter hooks + auto titles
```

## Pipeline

| Step | What happens | Notes |
|---|---|---|
| 1. Crawl | URL / playlist / channel / `ytsearchN:` | `sources.expand()` |
| 2. Download | yt-dlp, ≤720p by default | reused for every clip |
| 3. Transcript | **YouTube auto-captions first**, Whisper fallback | see below |
| 4. Hooks | LLM if key, else drama-lexicon scorer | `--genre vlog\|reality\|gaming\|news` |
| 5. Render | punch-ins, grade, watermark, title card, karaoke subs | parallel-aware |

Output per video: `Shorts/<video-slug>/NAME.mp4`, `.ass`, `.srt`, `_title.png`,
plus `clips.json` with hooks, timings and file paths.

## Why YouTube captions before Whisper

On a 16-minute Hindi vlog:

| Method | Time | Quality |
|---|---|---|
| YouTube auto-captions | **2 s** | clean Devanagari, 2,859 word timings |
| faster-whisper `base` int8/CPU | **18.7 min** | unusable — Urdu script, random languages, "Mushroom" ×5 |

So captions are tried first, per language, and Whisper only runs when a source has none.

## Copyright: what actually matters

Read this before trusting `--safe`:

* **Content ID claim ≠ copyright strike.** Claims usually don't hurt the channel.
  But a Short **1–3 minutes long with an active claim gets blocked**, so claims matter
  a lot in this format. ([YouTube Help](https://support.google.com/youtube/answer/6013276))
* `--safe 1..3` applies zoom, grading, speed-up, mirroring and grain. These lower the
  chance of a **video** fingerprint match. **Audio is matched separately and is much
  harder to defeat** — a music bed will usually still be caught. Mitigation, not immunity.
* The bigger risk for clip channels is the **reused content policy**: it is judged on
  whether you add value (commentary, edits, captions), applies to your **whole channel**,
  and is independent of copyright or permission.
  ([YouTube Help](https://support.google.com/youtube/answer/1311392))
  → Captions, titles and your own commentary are both the compliance story *and* the
  strongest fingerprint breakers. Ship them.

| `--safe` | zoom | mirror | speed | grade | grain |
|---|---|---|---|---|---|
| 0 | — | — | — | — | — |
| 1 (default) | 1.03× | — | — | light | — |
| 2 | 1.06× | — | 1.03× | medium + hue | light |
| 3 | 1.10× | ✔ | 1.05× | strong + hue | medium |

## Branding (multi-channel)

Everything lives in a profile JSON — copy one per channel, pass `--profile`:

```bash
autoclip "<url>" --profile profiles/biggboss.json
```

```jsonc
{
  "channel": "DKX",
  "watermark": "assets/dkx_watermark.png",   "watermark_pos": "top-right",
  "accent": "#E8192C",                        "title_card": true,
  "caption_font": "Noto Sans Devanagari ExtraBold",
  "caption_highlight": "&H0024E8FF",          "punch_zoom": 1.14
}
```

Captions auto-place themselves: `captions.auto_margin_v()` computes the fitted video
band from the source aspect ratio and keeps text inside it, clear of the Shorts UI
(bottom ~17 % and the right-hand action rail).

## Hard-won gotchas (all fixed in here)

1. **edge-tts ≥ 7.x defaults to `SentenceBoundary`** — you get audio but zero word
   timings and silently empty karaoke captions. Pass `boundary="WordBoundary"`.
2. **Noto Color Emoji is COLRv1**; Pillow cannot rasterise it and draws nothing.
   We composite Twemoji PNGs instead (`assets/emoji/`).
3. **libass ignores variable-font axes** → thin captions. Ship a *static* instance
   (`assets/NotoSansDevanagari-ExtraBold.ttf`).
4. **A still PNG decodes as one frame at t=0**, so `fade`/`enable` never see a timeline
   and your title card silently never appears. Use `-loop 1 -framerate N -t <dur>`.
5. **yt-dlp needs a binary literally named `ffmpeg`** in `ffmpeg_location`;
   imageio-ffmpeg's is `ffmpeg-linux-x86_64-v7.0.2`, so merges fail with
   "ffmpeg is not installed". `ffmpeg.shim_dir()` symlinks it.
6. **Requesting several subtitle languages at once**: one HTTP 429 aborts the whole
   call even if the first language already downloaded. Request them one at a time.
7. **Don't run one ffmpeg per core.** Two parallel renders on a 2-core box thrashed for
   19 minutes and died; sequential finished the same work in 70 s. Default is one
   worker per 2 cores, with an automatic sequential retry.
8. **Blur at full 1080×1920 is the most expensive filter.** Downscale 4×, blur, upscale:
   visually identical, 55 s → 38 s per clip.

## Performance

| | before | after |
|---|---|---|
| per clip (35 s, 1080×1920) | 124 s | **38 s** |
| full run, link → 2 shorts | — | **85 s** |

## Roadmap

* face/subject tracking crop (MediaPipe) instead of centre punch-in
* auto-upload via YouTube Data API v3
* EN/ES dubbing with Edge-TTS (free neural voices)

## Licence

MIT — see `LICENSE`. You are responsible for the rights to whatever you clip.
