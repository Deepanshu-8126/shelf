# FactShorts Bot 🎬

**Free, fully automated Shorts/Reels generator controlled from Telegram.** Real stock footage + voiceover + burned-in captions → preview on Telegram → approve → publish to **YouTube Shorts and Instagram Reels**. Facts come from **today's trends** (Google Trends + Wikipedia), twice-daily scheduling, and a voice that is **free and open-source end to end** — Kokoro-82M (Apache-2.0) or Piper (MIT) run on your own CPU, no keys and no quota. No paid services anywhere in the stack.

```
Telegram command ─► trends today (Google Trends / Wikipedia on-this-day / most-read / search)
   ─► fact verified + cited ─► script: 10-15 s fact OR ~60 s story (ad-free tone)
   ─► free stock clips (Pexels / Pixabay / NASA / Wikimedia / your own)
   ─► voice: Kokoro-82M or Piper (free, local, no key) ─► word timings from faster-whisper
   ─► burned captions ─► ffmpeg render (1080×1920) ─► title + description + tags
   ─► Telegram preview ─► /approve ─► YouTube Shorts + Instagram Reels
   └─ APScheduler runs this at every slot you set (default 08:30 and 19:30)
```

Two video modes, switchable live with `/mode`:

| Mode | Length | Shape |
|---|---|---|
| `facts` (default) | 10-15 s | one surprising fact, hook first 2 s |
| `story` | ~60 s (Shorts allow 3 min) | hook → setup → turn → payoff, 130-200 words, up to 10 shots |

---

## 5-minute quickstart (no API key needed)

```bash
git clone <your-repo> factshorts-bot && cd factshorts-bot
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python main.py --check          # health check (ffmpeg, deps, keys, platforms)
python main.py --trends         # see what is trending right now (no key needed)
python main.py --selftest       # 3 second test render - proves ffmpeg + captions work
python scripts/fetch_demo_footage.py --niche space --count 6
python main.py --demo           # full video: curated assets/stock/ footage + free TTS
python main.py --demo --topic "Sunlight takes 8 minutes"   # force a specific fact
```
`--demo` renders a real Short with zero API keys. Check `output/*.mp4` and play it.
(There is a rendered sample in `output/` and a copy at the repo root as `sample_factshort.mp4`.)

Then add keys for the real quality bump (Pexels portrait clips, Gemini facts), and turn on the bot:

```bash
cp .env.example .env            # fill TELEGRAM_BOT_TOKEN + TELEGRAM_ALLOWED_USER_IDS
python main.py --auth           # one-time YouTube OAuth consent
python main.py --bot            # Telegram bot + daily scheduler
```

Docker instead: `docker compose up -d --build`

---

## What's in the box

| # | Module | What it does |
|---|--------|--------------|
| 0 | `trends.py` | **Trend engine (free, no key):** Google Trends RSS, Wikipedia *On this day*, Wikipedia most-read, Wikipedia niche search, random article. Filters out news/celebrity/sport/politics/sensitive subjects, caches responses on disk, and hands the pipeline a **cited** subject with a Wikipedia extract to write from. |
| 1 | `topic_engine.py` | Generates a fact per run, **verifies it with a second LLM pass** (rejects wrong/controversial), stores fingerprints in SQLite and never repeats. Offline fact bank included (30+ seed facts) so it works without any LLM key. |
| 2 | `script_writer.py` | Mode-aware: hook + body + closing in 26-46 words (facts) or a 130-200 word story with a real arc (story mode), plus **2-3 footage search keywords per sentence**. Stopwords/single letters are filtered out so you never get a random screen recording as your B-roll. |
| 3 | `footage.py` | Pexels → Pixabay → NASA Image Library → Wikimedia Commons → your own `assets/stock/` clips. Throttling, retry on 429, licence/credit capture, SQLite clip cache, junk-title filter, resolution guard. |
| 4 | `voice.py` | Narration. **Free local engines first:** Kokoro-82M (Apache-2.0, ~325 MB model, 54 voices, ~1.3× realtime on a CPU) or Piper (MIT, ~63 MB per voice, ~8× realtime); then edge-tts (free cloud, no key); ElevenLabs only if you ask for it *and* set a key. Rotates voices per niche and tracks ElevenLabs character usage. |
| 4a | `tts_local.py` | The free voice engine: model download/cache (`TTS_MODEL_DIR`), sentence-by-sentence synthesis for exact sentence anchors, WAV→MP3 with ffmpeg, and `--worker` mode so the engine runs in a child process (onnxruntime holds ~1 GB for Kokoro — this keeps the bot alive on 1 GB hosts). |
| 4b | `align.py` | Caption timing for engines that have none: runs **faster-whisper** (MIT, local, ~20× realtime) over the finished narration and maps its word boundaries back onto the **script** words, so captions keep the written spelling with real timings. Includes a dependency-free syllable/pause estimator (within ~120 ms of whisper in testing) for when whisper is not installed. |
| 4c | `instagram.py` | **Instagram Reels publishing** via the official Content Publishing API: container → resumable upload → status poll → publish. See `docs/INSTAGRAM_SETUP.md`. |
| 4d | `publish.py` | One call publishes to **YouTube + Instagram**; per-platform results, retries, quota awareness, `/stats` shows both ids. |
| 5 | `captions.py` | Timing sources chained automatically (`CAPTION_SOURCE=auto`): whisper → the engine's own timings → the syllable estimator → even spread. 3-4 word pages, **active word highlighted in gold**, non-overlapping pages, safe-area aware. |
| 6 | `render.py` | 1080×1920 @30fps: cover-crop, alternating Ken-Burns zoom (per-frame `scale`+`crop`, not the buggy `zoompan`), cross-fades, voice + ducked background music, burned captions, fade-out, `+faststart`. **Quality guards:** clips are ranked sharpest-first before rendering (`blurdetect`), and any slice that comes out black/flat (luma + dynamic range from `signalstats`) or soft gets its window shifted automatically. |
| 7 | `seo.py` | Title ≤60 chars (keyword first), description with `#shorts` + niche hashtags, 10-15 tags, a question for the pinned comment. |
| 8 | `uploader.py` | YouTube OAuth, resumable upload with retry, `publishAt` scheduling, **honest `containsSyntheticMedia` disclosure**, daily upload cap for the 10k unit quota, posts the first comment. |
| 9 | `bot.py` | All Telegram commands + inline Approve/Regenerate/Reject buttons, restricted to your user id. |
| 10 | `scheduler.py` | **Multiple daily slots** (e.g. morning + night), optional niche rotation across slots, 30-min publish retry, temp cleanup. Every job is wrapped: a failure notifies you on Telegram and the scheduler keeps running. |

---

## Telegram commands

| Command | What it does |
|---|---|
| `/generate [niche]` | Build a video now (live progress in chat) |
| `/mode facts\|story` | 10-15 s single fact, or a ~60 s story (persistent) |
| `/approve [id]` · `/reject [id]` · `/regenerate [id]` | Review flow (also available as inline buttons under the preview) |
| `/upload <id> [public\|unlisted\|private]` | Upload an older render |
| `/schedule 08:30,19:30` | Daily slots (morning + night). Single value also works. Applies without a restart |
| `/platforms youtube,instagram` | Where videos go |
| `/trends [IN\|US]` | Show what's trending + Wikipedia hot topics right now |
| `/voiceprovider auto\|edge\|elevenlabs` | Switch narration engine (see the licensing note below) |
| `/niche <name>` | `space \| psychology \| history \| science \| animals` |
| `/auto on\|off` | Upload without waiting for approval |
| `/voice <name\|list>` | Pick an edge-tts voice (or rotate automatically) |
| `/queue` · `/stats` · `/status` · `/whoami` | Queue, upload history, config + quota, your user id |

---

## Setup

### 1. Telegram (2 minutes)
1. **@BotFather** → `/newbot` → copy the token → `TELEGRAM_BOT_TOKEN`.
2. **@userinfobot** → send any message → copy your numeric id → `TELEGRAM_ALLOWED_USER_IDS`.
   (Without this the bot answers everyone. Set it.)

### 2. LLM for facts/scripts/SEO — free tier
- **Gemini**: <https://aistudio.google.com/apikey> → `GEMINI_API_KEY` (default, recommended)
- **Groq** (fallback/provider): <https://console.groq.com/keys> → `GROQ_API_KEY`
- No key? `LLM_PROVIDER=offline` uses the built-in fact bank + templates (works, less variety).

### 3. Stock footage — free, commercial use
- **Pexels**: <https://www.pexels.com/api/> → `PEXELS_API_KEY` ← *best results, portrait clips*
- **Pixabay**: <https://pixabay.com/api/docs/> → `PIXABAY_API_KEY`
- **NASA** + **Wikimedia Commons**: no key, enabled by default (`FOOTAGE_PROVIDERS`)
- Or drop your own mp4s in `assets/stock/` (mixkit, coverr, your own camera)

### 4. YouTube upload
Full walkthrough with the **API audit** requirement: [`docs/YOUTUBE_SETUP.md`](docs/YOUTUBE_SETUP.md).
Short version: Cloud Console → enable *YouTube Data API v3* → OAuth *Desktop app* client → save JSON to `credentials/client_secret.json` → `python main.py --auth`.

> ⚠️ **Plan for the audit.** Videos uploaded through a **new, unverified API project are locked to private** (Google's rule since 28 Jul 2020). Fill the audit form for your own channel; until it clears you can either (a) upload with the API and flip to public manually in the YT Studio, or (b) let the bot render + preview on Telegram and upload by hand. Never try to fake the client or hide that the upload is automated — that's what gets projects rejected.

### 5. Voice: 100% free, open-source, runs on your CPU

| Engine | Licence | Size | Speed (CPU) | Timings | Notes |
|---|---|---|---|---|---|
| **Kokoro-82M** (default) | Apache-2.0 | ~325 MB model + 28 MB voices | ~1.3× realtime | via whisper | best quality of the free options, 54 voices, commercial use allowed |
| **Piper** | MIT | ~63 MB per voice | ~8× realtime | via whisper | lightest and fastest — ideal for a 1 GB VPS |
| edge-tts | GPL-3.0 wrapper over a Microsoft service | 0 MB | fast | built in | needs internet, no key. **Fallback only** — see the note below |
| ElevenLabs | proprietary | 0 MB | fast | built in | **optional paid**; free tier is non-commercial |

```ini
VOICE_PROVIDER=auto      # auto = kokoro if installed, else piper, else edge-tts
KOKORO_SPEED=1.05        # 0.8 slower ... 1.2 faster
PIPER_VOICE=             # empty = en_US-lessac-medium
TTS_MODEL_DIR=           # empty = cache/tts (models download once, then fully offline)
TTS_ISOLATE=true         # run the engine in a child process (recommended)
```

One-time install of the free engines (both are optional — without them `auto` uses edge-tts):

```bash
pip install kokoro-onnx onnxruntime      # Kokoro-82M, Apache-2.0
pip install piper-tts                    # Piper, MIT
pip install faster-whisper               # word-accurate captions for local voices (MIT)
```

Models download on the first render into `TTS_MODEL_DIR` (Kokoro ~350 MB, Piper ~63 MB) and are
reused forever after. Nothing in this path needs a key, an account or a credit card.

**How captions stay in sync without timestamps.** Kokoro and Piper do not return word boundaries
(`create_timed` / `include_alignments` come back empty on the standard exports). Two things fix that:

1. narration is synthesised **sentence by sentence**, so every sentence has an exact start time as an anchor,
2. `align.py` runs **faster-whisper** (free, local, MIT — `tiny.en` is ~20× realtime on a CPU) over the
   finished audio and maps its word boundaries onto the script words. Script spelling, real timings.

If whisper is not installed the built-in syllable/pause estimator takes over — measured within
~120 ms mean error against whisper on the same audio, which is fine for 3-4 word caption pages.
`CAPTION_SOURCE=auto` picks the best available automatically; `/status` shows what is in use.

> **edge-tts ka licensing note (honest):** `rany2/edge-tts` GPL-3.0 hai aur wo Microsoft ke Edge
> "Read Aloud" service ko use karta hai, jiske baare mein Microsoft kehta hai ki wo commercial TTS
> product ke liye licensed nahi hai. Isliye v3 mein **default hi Kokoro/Piper** hai — dono ka license
> (Apache-2.0 / MIT) monetized channel ke liye clean hai. edge-tts sirf tab chalta hai jab koi local
> engine install na ho.

> **Memory note.** onnxruntime keeps ~1 GB while the Kokoro model is loaded. `TTS_ISOLATE=true`
> (default) runs the engine in a short-lived child process so that memory is released before
> whisper and ffmpeg start. On a 512 MB-1 GB host use Piper instead:
> `VOICE_PROVIDER=piper`.

### 6. Facts from trends (default on)

```ini
USE_TRENDS=true
TRENDS_GEO=IN                     # your country's Google Trends feed
TREND_SOURCES=google,onthisday,mostread,search,random
CITE_SOURCE=true                  # appends "Source: Wikipedia → <url>" to the description
```

Order of attack each run: **Google Trends** (resolved through Wikipedia so the fact is real) →
**On this day** (great for history/space) → **most-read** → **niche search** (guaranteed subjects
per niche) → **random article**. Everything is filtered for niche relevance and against
news/celebrity/sport/politics/crime/medical content, cached on disk (so the free APIs aren't
hammered), and the winning subject arrives with a Wikipedia extract that the LLM must stay inside —
that's what keeps facts accurate and citable instead of invented.

Turn it off with `USE_TRENDS=false` and the bot uses the LLM/offline fact bank as before.

### 7. Tone: don't sound like an ad

```ini
SCRIPT_STYLE=friendly     # friendly | documentary | punchy
CTA_STYLE=soft            # none (no call to action at all) | soft | follow
```
Every generated line passes through a filter that strips advert language
("in this video", "don't forget to subscribe", "you won't believe", "insane", "guys",
"link in the description", …) and the prompts run at `temperature ≈ 0.85` with explicit
instructions to explain rather than sell. Use `CTA_STYLE=none` for a pure-value channel with no
ask at all.

### 8. Background music (optional)
Put royalty-free files in `assets/music/` (YouTube Audio Library, Pixabay Music, Free Music Archive CC0). Music is ducked under the narration automatically. **Never** use copyrighted music — Shorts get muted or the channel gets strikes.

---

## Configuration (`​.env`)

Most-used knobs — full list in [`.env.example`](.env.example):

| Variable | Default | Notes |
|---|---|---|
| `VOICE` | *(rotate)* | e.g. `en-US-ChristopherNeural`, `en-GB-RyanNeural`, `en-IN-NeerjaNeural` |
| `VOICE_RATE` | `+10%` | Shorts narration sounds better slightly fast |
| `CAPTION_SOURCE` | `edge` | `whisper` = faster-whisper (install it, more accurate on hard words) |
| `VIDEO_CLIP_COUNT` | `4` | Max shots; the renderer paces shots to ~3.8 s |
| `CLIP_MAX_SOURCE_DURATION` | `45` | Skip longer archival videos (NASA/Commons) — they are full of title cards and interviews |
| `CLIP_MIN_SHORT_SIDE` | `640` | Reject low-res "mobile" renditions that look like mush when cropped to 9:16 |
| `VIDEO_TRANSITION` | `fade` | `fade` or `cut` |
| `VIDEO_ZOOM` | `0.10` | Ken-Burns strength (0 = off) |
| `VIDEO_MAX_DURATION` | `14.5` | Keeps you in the Shorts window with headroom |
| `YOUTUBE_SYNTHETIC_DISCLOSURE` | `true` | **Keep it true** — the voice is synthetic |
| `YOUTUBE_PRIVACY_STATUS` | `public` | Use `unlisted` while you test |
| `AUTO_MODE` | `false` | `true` = upload without approval |
| `MAX_UPLOADS_PER_DAY` | `5` | Default quota = 10k units/day, one upload ≈ 1600 units |
| `SCHEDULE_TIMES` / `TIMEZONE` | `08:30,19:30` / `Asia/Kolkata` | Morning + night runs (any number of slots) |
| `NICHE_ROTATE` | `false` | Rotate the niche across slots (more variety) |
| `PLATFORMS` | `youtube` | `youtube,instagram` publishes to both |
| `USE_TRENDS` / `TRENDS_GEO` | `true` / `IN` | Trend-driven subjects, region aware |
| `SCRIPT_STYLE` / `CTA_STYLE` | `friendly` / `soft` | Tone; `CTA_STYLE=none` = no call to action |
| `VOICE_PROVIDER` | `auto` | `edge` (free) or `elevenlabs` |
| `IG_*` | – | Instagram Reels credentials + upload mode (see `docs/INSTAGRAM_SETUP.md`) |

---

## Story mode (~60 s videos)

```ini
VIDEO_MODE=story          # or /mode story in Telegram (persists), or --mode story for one run
STORY_TARGET_WORDS=165     # ≈60 s of narration at the free voices' ~2.8 words/second
STORY_MIN_WORDS=130
STORY_MAX_WORDS=200
STORY_MAX_DURATION=68      # the audio decides the video length (Shorts allow 3 minutes)
STORY_CLIP_COUNT=10        # more shots, calmer cutting (6.5 s per shot vs 3.8 s)
```

What changes in story mode:

* the writer switches to a **narrative prompt** (hook → setup → turn → payoff, only the verified material),
* the topic is allowed a **longer source**: up to 4 sentences of a Wikipedia extract instead of 2,
  and if that still is not enough the pipeline pulls the page's full lead section (`widen_material`)
  so a 60 s narration never has to be padded with invented content,
* **10 shots instead of 4**, and the footage search asks for clips at least ~4.9 s long so a shot
  is never a loop of a 3 s clip,
* if the narration still runs long the bot **re-records it slightly faster** (up to `STORY_MAX_SPEED`)
  before it starts cutting sentences, so the story stays whole,
* caption pages become 4 words / 24 characters.

Note for the offline path: with no LLM key the story comes from the built-in fact bank plus neutral
narrative glue, which usually lands around 40-50 s. Add a free Gemini/Groq key and it hits ~60 s.

## CLI reference

```bash
python main.py --check                 # config + dependency health
python main.py --selftest              # tiny offline render
python main.py --auth                  # YouTube OAuth (once)
python main.py --script-test           # topic + script + SEO, no render
python main.py --generate --niche space            # one video now (10-15s fact)
python main.py --generate --mode story --niche animals --topic "immortal jellyfish"   # ~60s story
python main.py --mode story --check     # see the story-mode numbers before you run it
python main.py --generate --topic "Octopuses have three hearts"
python main.py --generate --offline --upload       # offline bank, then upload
python main.py --demo                  # no keys at all, free public-domain footage
python main.py --trends --niche space --trends-geo IN   # today's trending subjects
python main.py --upload 12 --platforms youtube,instagram   # publish everywhere
python main.py --platform-status       # platform readiness + Instagram quota
python main.py --bot                   # Telegram bot + scheduler
python main.py --daemon                # scheduler only (headless worker)
python -m factshorts.uploader --status # YouTube auth/quota state
python scripts/fetch_demo_footage.py --list        # free footage library manager
pytest -q                              # 46 smoke tests, no network needed
```

---

## Deployment (free options)

| Where | How | Notes |
|---|---|---|
| **GitHub Actions** | `.github/workflows/daily.yml` (twice daily cron) | **Zero server, free, nothing runs on your PC** — recommended if you just want 2 videos/day. Ephemeral: the topic-memory DB is committed back to the repo |
| **Oracle Cloud Free Tier** | 4-core ARM VM free forever, systemd unit | Best for always-on + stateful. Free, no PC needed — see `docs/DEPLOYMENT.md` |
| **Your PC** | `python main.py --bot` (Windows: Task Scheduler / NSSM service) | Simplest; PC must be on at post time |
| **Oracle Cloud Free Tier** | 4-core ARM VM free forever, systemd unit | Best "always-on and free" option — see [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) |
| **Docker** | `docker compose up -d --build` | Volumes for data/cache/output/credentials |
| **Any ₹0 VPS / Raspberry Pi** | systemd unit, same as Oracle | Pi renders slower (ffmpeg on ARM) |


---

## Quality, monetization and policy notes (read this once)

- **YouTube's "mass-produced / repetitious content" rule** is the real risk, not the tool. This bot fights it in code: LLM-verified facts, original scripts, rotated voices, varied hooks, different footage each time, and a "never repeat a topic" database. Add your own taste: change niches weekly, edit scripts by hand when a hook is weak, and don't post 8 videos a day of the same template.
- **Disclosure is honest and automatic**: the narration is synthetic, so `status.containsSyntheticMedia = true` is set on every upload. Real stock footage is *not* AI-generated imagery, so you are not claiming otherwise.
- **Copyright**: Pexels/Pixabay licences allow commercial use; NASA material is generally not copyrighted; Wikimedia files carry CC/PD licences and the bot stores the credit and appends it to the description. Music only from royalty-free sources.
- **What this project deliberately does not do**: remove watermarks from other tools' output, or disguise AI-generated clips as real footage. Both break the source tool's terms and YouTube policy, and both are a good way to lose a channel. Want AI-generated B-roll? Use a tool that ships watermark-free output under its own licence, then let this bot handle the rest (script, voice, captions, SEO, upload).

---

## Project layout

```
factshorts-bot/
├── main.py                     # CLI entrypoint
├── factshorts/
│   ├── config.py               # .env -> Config
│   ├── db.py                   # SQLite: topics, videos, clip cache, settings
│   ├── llm.py                  # Gemini / Groq with fallback + JSON repair
│   ├── trends.py               # Google Trends + Wikipedia sources (cached, filtered)
│   ├── topic_engine.py         # fact generation, verification, offline bank
│   ├── script_writer.py        # script + footage keywords
│   ├── footage.py              # Pexels/Pixabay/NASA/Wikimedia/local + cache
│   ├── voice.py                # edge-tts + word timings
│   ├── captions.py             # ASS caption builder (highlighted word)
│   ├── render.py               # ffmpeg render pipeline + quality guards
│   ├── seo.py                  # title/description/tags/pinned comment
│   ├── uploader.py             # YouTube OAuth upload + quota + disclosure
│   ├── instagram.py            # Instagram Reels (container → resumable → publish)
│   ├── publish.py              # multi-platform dispatch + per-platform results
│   ├── bot.py                  # Telegram commands & buttons
│   ├── scheduler.py            # APScheduler daily job
│   ├── pipeline.py             # orchestrates one video end to end
│   └── telegram_notify.py      # dependency-light notifier
├── scripts/fetch_demo_footage.py
├── tests/test_smoke.py
├── assets/{fonts,music,stock}/
├── docs/{YOUTUBE_SETUP.md,INSTAGRAM_SETUP.md,DEPLOYMENT.md}
├── Dockerfile · docker-compose.yml · Makefile · requirements.txt · .env.example
```

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| `edge-tts` fails / no audio | `pip install -U edge-tts`; corporate DNS/VPN may block it — espeak-ng fallback kicks in (`apt install espeak-ng`) |
| No footage found | Add `PEXELS_API_KEY`; check `FOOTAGE_PROVIDERS`; Wikimedia rate-limits hard from some IPs — the bot retries and falls through providers |
| Archive clips show captions/title cards | Those are produced films, not B-roll: lower `CLIP_MAX_SOURCE_DURATION` (e.g. `25`) or raise the Pexels share in `FOOTAGE_PROVIDERS` |
| Video has a black/flat shot | The renderer measures luma + dynamic range and re-picks the window automatically; clips are also ranked by sharpness before rendering (`blurdetect`). Add `PEXELS_API_KEY` for the crispest B-roll |
| Upload says quota exceeded | Default quota ≈ 6 uploads/day. Lower `MAX_UPLOADS_PER_DAY` or request a quota increase |
| Uploads land as private | Expected until your API audit passes — see `docs/YOUTUBE_SETUP.md` |
| Captions missing in the render | Run `python main.py --selftest`; if the font is missing, `factshorts/render.py` registers `assets/fonts/*.ttf` on first run |
| Bot ignores you | `/whoami` → put the id in `TELEGRAM_ALLOWED_USER_IDS` |
| Facts feel random / off-niche | `python main.py --trends` to see the filter; tighten `TREND_SOURCES` (e.g. only `mostread,search`) or set `USE_TRENDS=false` |
| ElevenLabs says 402/quota | free tier spends 10k chars/month; check `/voiceprovider`, reduce to one video a day or move to edge-tts |
| Instagram "permission" error | account must be Business/Creator and the app needs `instagram_content_publish` — `docs/INSTAGRAM_SETUP.md` §7 |
| Published the same topic twice | shouldn't happen: topics are fingerprinted in SQLite. In GitHub Actions mode the repo must commit `data/factshorts.db` back (the workflow does) |

---

## Licence / credits

- Code: MIT (do what you like, no warranty).
- Bundled caption font: **Montserrat**, SIL Open Font License (`assets/fonts/OFL.txt`).
- Footage: whatever your providers' licences say — the bot records credits in `output/*.json` and appends CC credits to the description automatically.
