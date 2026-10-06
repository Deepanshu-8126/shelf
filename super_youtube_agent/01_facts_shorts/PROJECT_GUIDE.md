# FactShorts Bot — Poora Project Guide (Hinglish)

> **Ye file padh lena pehle.** Isme hai: kaun-kaun se open-source repos use kiye, humne kya banaya,
> project ka structure, aage better kaise karna hai, aur Antigravity mein setup kaise karna hai.
> Baaki detail ke liye: `README.md` (full docs), `docs/` folder (YouTube / Instagram / Deployment).

**Aaj ki date par project:** 25 Python files · ~8,970 lines · 46 tests pass · 0 lint errors · 22 MB workspace.

---

## 1. Kaun-kaun se repos / tools use kiye (aur license kya hai)

Sabse important section — kyunki aap monetized channel chala rahe ho, to **license galat hua to
channel pe strike aa sakta hai**.

### 1.1 Voice (narration) — yahi asli kaam hai

| Kaam | Repo / Model | License | Commercial? | Kahan se aata hai |
|---|---|---|---|---|
| **Voice #1 (default)** | **Kokoro-82M** (`hexgrad/Kokoro-82M`) | **Apache-2.0** | ✅ Haan, bilkul free | Model GitHub release `thewh1teagle/kokoro-onnx` (model-files-v1.0) se auto-download, 325 MB + 28 MB voices |
| Voice #1 ka Python wrapper | `thewh1teagle/kokoro-onnx` | MIT | ✅ | `pip install kokoro-onnx onnxruntime` |
| **Voice #2 (halka/fast)** | **Piper** (`rhasspy/piper`, `OHF-Voice/piper1-gpl`) | **MIT** | ✅ | `pip install piper-tts` + voice `.onnx` HuggingFace `rhasspy/piper-voices` se (63 MB per voice) |
| **Captions ka timing** | **faster-whisper** (`SYSTRAN/faster-whisper`) | MIT | ✅ | `pip install faster-whisper`; model `tiny.en` / `base.en` HuggingFace se auto-download |
| Whisper model (asli weights) | OpenAI Whisper | MIT | ✅ | same |
| Voice #3 (fallback only) | `rany2/edge-tts` | **GPL-3.0** | ⚠️ **Nahi** (neeche note) | `pip install edge-tts` |
| Voice #4 (optional, paid) | ElevenLabs API | proprietary | ❌ free tier non-commercial | aap ne khud key daali to hi chalega |

> ⚠️ **edge-tts ke baare mein honest baat (important):**
> 1. `rany2/edge-tts` **GPL-3.0** hai — commercial use allowed hai par aapko apna code disclose karna
>    padta hai (same license).
> 2. Wo Microsoft ke **Edge "Read Aloud" service** ko use karta hai, aur Microsoft ke apne jawab ke
>    hisaab se wo service commercial TTS product banane ke liye licensed nahi hai
>    ([Microsoft Q&A](https://learn.microsoft.com/en-us/answers/questions/2088770/are-opensource-edge-tts-free-for-commercial-use)).
> 3. Isliye **v3 mein humne default hi Kokoro/Piper kar diya** — edge-tts sirf backup hai.
>    Aap `VOICE_PROVIDER=kokoro` (ya `piper`) set karke rakho, to ye issue hi nahi aata.

**Jin models ko humne jaan-boojh kar nahi use kiya** (aur kyun):

| Model | Kyun nahi |
|---|---|
| XTTS v2 (Coqui) | weights ka license **non-commercial** hai (Coqui CPML) → monetized channel pe allowed nahi |
| Chatterbox (Resemble AI) | MIT hai par 0.5B, **4-6 GB VRAM GPU** chahiye — free hosting pe nahi chalega |
| Fish Speech / Bark | non-commercial ya unstable, Hinglish/hosted ke liye risky |
| ElevenLabs free tier | non-commercial + attribution → paid plan chahiye |

### 1.2 Baaki pipeline

| Kaam | Tool / Source | License / Terms | Notes |
|---|---|---|---|
| Facts (trends) | **Google Trends RSS** (`trends.google.com/trending/rss?geo=IN`) | keyless, unofficial RSS | koi key nahi chahiye |
| Facts (content) | **Wikipedia REST + Action API** | CC BY-SA 4.0 | attribution bot description + pinned comment mein daalta hai |
| Facts (backup) | Built-in offline FACT_BANK | aapka apna | 30 facts, 5 niches |
| Script/facts LLM | **Gemini free tier** (default) / **Groq free tier** (fallback) | free tier ToS | key na ho to offline template chalta hai |
| Footage #1 | **Pexels API** | free, commercial OK, no attribution needed | `PEXELS_API_KEY` |
| Footage #2 | **Pixabay API** | free, commercial OK | `PIXABAY_API_KEY` |
| Footage #3 | **NASA Image & Video Library** | mostly public domain | keyless |
| Footage #4 | **Wikimedia Commons** | CC-BY / CC0 / PD — **attribution auto jaata hai** | keyless, 429 handling built-in |
| Render engine | **FFmpeg 7** | LGPL/GPL (build pe depend) | system package |
| Caption font | **Montserrat ExtraBold** | SIL OFL 1.1 | repo mein included (`assets/fonts/`) |
| Telegram bot | `python-telegram-bot` | LGPL-3.0 | `pip install` |
| Scheduler | `APScheduler` | MIT | 2 daily slots |
| HTTP | `httpx` | BSD-3 | async downloads |
| YouTube upload | `google-api-python-client` + `google-auth-oauthlib` | Apache-2.0 | OAuth, audit needed |
| Instagram Reels | **Meta Graph API** (Content Publishing) | free, app review needed | `docs/INSTAGRAM_SETUP.md` |
| Env loader | `python-dotenv` | BSD-3 | `.env` support |

---

## 2. Humne kya kiya (aaj tak ka safar)

### v1 — Pooora bot zero se
- 18 CLI flags wala `main.py`, 18 Telegram commands wala `bot.py`
- Topic engine (repeat-proof, SQLite fingerprint memory), script writer, footage fetch (4 sources),
  captions (word-by-word gold highlight), render (1080×1920, Ken-Burns zoom, cross-fade),
  SEO (title <60 chars, tags, pinned comment), YouTube uploader, scheduler, Dockerfile, README.
- Pehla E2E render: 14.5s space Short ✅

### v2 — Human voice + trends + 2 platforms
- **Trends engine**: Google Trends RSS + Wikipedia (on-this-day / most-read / search / random),
  sensitive-topic filter, disk cache, 429 backoff.
- Ad-free script tone, `CTA_STYLE`, voice rotation per niche.
- Instagram Reels publishing (container → resumable upload → status → publish).
- Do daily slots (08:30 + 19:30 IST), GitHub Actions workflow, 4 hosting options documented.
- **Quality guards**: clip sharpness ranking (blurdetect) se dhundhe clips reject,
  black/flat frame detection (signalstats), dry-run publish bug fix.
- 39 tests, 94/94 config keys documented.

### v3 (aaj) — 100% free voice + 60 second story mode
| Kya joda | Kahan |
|---|---|
| **Kokoro-82M** local voice (Apache-2.0, ~1.3× realtime, 54 voices) | `factshorts/tts_local.py` |
| **Piper** local voice (MIT, ~8× realtime, 63 MB) | `factshorts/tts_local.py` |
| Sentence-by-sentence synthesis → exact sentence anchors | `tts_local.py` |
| **Whisper word-timings** (script spelling + real timings) | `factshorts/align.py` |
| Syllable/pause **estimator** (~120 ms accuracy) — whisper na ho to | `align.py` |
| Model auto-download + cache (`TTS_MODEL_DIR`), mirror support | `tts_local.py` |
| **Subprocess isolation** — Kokoro ~1 GB RAM leta hai, render se pehle chhod deta hai | `tts_local.py --worker` |
| **Story mode (~60s)**: 165-word narrative, 10 shots, 6.5s per shot | `config.py` ModeProfile |
| Narration lambi ho to **pehle tez re-record**, phir trim | `pipeline.py` |
| Story ke liye material widening (Wikipedia lead + full text) | `topic_engine.widen_material` |
| `/mode facts\|story` Telegram command + `--mode` CLI flag | `bot.py`, `main.py` |
| Free local voice `MODE` ka pura doc + licensing | `README.md`, `.env.example` |
| 46 tests, 0 lint | `tests/test_smoke.py` |

**Aakhri E2E run (aaj) kahan tak pahuncha:** material 177 words → script 181 words → narration 71.9s →
auto speed-up se **66.7s** → 10/10 clips download + normalize ✅ → **final encode pe sandbox OOM**
(yahan sirf 2 GB RAM hai). Code sahi hai; host pe zyada RAM hone par ye step bhi pass hoga.

---

## 3. Project structure (proper tree)

```
factshorts-bot/
├── main.py                     # CLI: --check --generate --auth --bot --daemon --demo --mode ... (19 flags)
├── requirements.txt            # core + free local TTS + whisper (koi paid key nahi)
├── .env.example                # 126 lines — har setting commented, 100+ keys
├── README.md                   # full documentation (Hinglish + English)
├── PROJECT_GUIDE.md            # ← ye file (repos, structure, roadmap, Antigravity setup)
├── Dockerfile / docker-compose.yml
├── Makefile                    # make check / test / demo / trends / deploy
│
├── factshorts/                 # asli code (25 files)
│   ├── config.py               # env → Config object + ModeProfile (facts | story)
│   ├── db.py                   # SQLite: videos, topics, clips, settings, meta merge
│   ├── utils.py                # logging, ffprobe helpers, sanitizers, run_cmd
│   │
│   ├── trends.py               # Google Trends + Wikipedia (5 sources, cache, filters)
│   ├── topic_engine.py         # fact banana + verify + repeat-proof + material widening
│   ├── script_writer.py        # facts mode (26-46 words) / story mode (130-200 words)
│   ├── llm.py                  # Gemini → Groq → offline fallback
│   │
│   ├── footage.py              # Pexels → Pixabay → NASA → Wikimedia → local assets
│   ├── tts_local.py            # ⭐ Kokoro + Piper (free voice), model download, --worker
│   ├── voice.py                # voice provider router (kokoro/piper/local/edge/elevenlabs/espeak)
│   ├── align.py                # ⭐ whisper word timings + syllable estimator
│   ├── captions.py             # ASS captions, word highlight, timing-source chain
│   ├── render.py               # ffmpeg: crop, zoom, transitions, captions, music, quality guards
│   ├── seo.py                  # title / description / tags / pinned comment
│   ├── uploader.py             # YouTube OAuth + resumable upload + synthetic disclosure
│   ├── instagram.py            # Reels publishing (Meta Graph API)
│   ├── publish.py              # YouTube + Instagram ek saath, dry-run safe
│   ├── telegram_notify.py      # bot se bahar notification bhejna
│   ├── bot.py                  # 19 Telegram commands + inline buttons
│   ├── scheduler.py            # APScheduler: 2 daily slots, niche rotation, crash-proof
│   └── pipeline.py             # poora flow: topic → script → footage → voice → render → SEO
│
├── tests/test_smoke.py         # 46 offline tests
├── scripts/fetch_demo_footage.py
│
├── docs/
│   ├── YOUTUBE_SETUP.md        # OAuth + API audit (private-lock issue)
│   ├── INSTAGRAM_SETUP.md      # Meta app, token, IG_USER_ID
│   └── DEPLOYMENT.md           # 4 hosting options (GH Actions recommended) + RAM/disk notes
│
├── assets/
│   ├── fonts/Montserrat-ExtraBold.ttf + OFL.txt
│   ├── stock/                  # 7 offline fallback clips (space) + manifest.json
│   └── music/                  # apni royalty-free music yahan daalo
│
├── .github/workflows/daily.yml # free hosting: 2 cron slots, secrets, DB commit back
├── credentials/                # client_secret.json + token.json (gitignored)
├── data/factshorts.db          # SQLite (topic memory, video status)
├── output/                     # final mp4 + report json
└── cache/                      # clips / tmp / trends / tts models (gitignored, safai kar sakte ho)
```

### Ek video ka safar (data flow)

```
1. Telegram /generate  ya  cron (08:30 / 19:30 IST)
2. trends.py      → aaj ka subject + Wikipedia extract (cited)
3. topic_engine   → fact + verify + repeat check  (story mode: material ko 165 words tak widen)
4. script_writer  → hook + body + closing  (+ har sentence ke liye footage keywords)
5. footage.py     → Pexels/Pixabay/NASA/Wikimedia/local se clips → sharpness ranking
6. voice.py       → tts_local (Kokoro/Piper) subprocess mein narration + sentence anchors
                    (lambi ho to speed-up loop → phir trim)
7. align.py       → faster-whisper se word timings → script words pe snap
8. captions.py    → ASS file (highlight word-by-word)
9. render.py      → 1080×1920 mp4: crop + zoom + transition + captions + music + fade
10. seo.py        → title / description / tags / pinned comment
11. Telegram preview → /approve → YouTube (+ Instagram) upload
```

---

## 4. Aur better kaise kar sakte hain (priority order mein)

### A. Sabse pehle (free, 1-2 ghante ka kaam, sabse zyada fayda)

1. **Gemini free key daalo** (`GEMINI_API_KEY`) — offline template ~45s story deta hai, LLM key se
   60s + better hook + better footage keywords. Ye sabse bada quality jump hai.
2. **Host pe render settings tune karo** — 2 GB RAM host pe `VIDEO_THREADS=2`, `VIDEO_PRESET=veryfast`,
   `VOICE_PROVIDER=piper`, `WHISPER_MODEL=tiny.en`. 4 GB+ pe `medium` preset rakho, quality better.
3. **YouTube API audit** form bhar do (nahi to uploads private-lock rehte hain). `docs/YOUTUBE_SETUP.md`.

### B. Quality upgrades (medium effort)

4. **B-roll relevance scoring** — abhi keyword search hai (script sentence → search term). Better:
   har clip ke tags/description ko script sentence se **embedding similarity** (free: `sentence-transformers`
   ka `all-MiniLM-L6-v2`, 80 MB) se match karo → galat clip aa hi nahi sakti.
5. **Caption animation** — word pop/scale bounce, 2-line pages, per-niche color, emoji-free. ASS
   tags se ho jaata hai (`\t(\fscx115\fscy115)`, `\move`, `\fad`). Retention pe seedha asar.
6. **Audio loudness normalize** — `-af loudnorm=I=-14:TP=-1.5:LRA=11` (YouTube ka standard). Music
   ducking bhi tighten karo (sidechain compress).
7. **Hook A/B testing** — 3 hook variants generate karo, YouTube "Test & Compare" se best nikalo;
   jo pattern jeete wo `script_writer` ke HOOKS bank mein daal do.
8. **Story structure upgrade** — 3-act beat sheet + **loop ending** (last line pehli line se connect ho)
   → rewatch badhta hai, Shorts algorithm ko wahi chahiye.

### C. Naya level (bada effort, bada fayda)

9. **Hinglish / Hindi channel version** — Piper ke `hi_IN` voices free hain, Kokoro mein Hindi nahi.
   Aap UP se ho, Hinglish audience bada hai aur competition kam. Script: LLM se Hinglish narration,
   captions English+Devanagari mix.
10. **Analytics feedback loop** — YouTube Analytics API se retention/CTR padho, SQLite mein store karo,
    phir niche/topic/length ko data ke hisaab se weight karo (jo topic 70%+ retention deta hai usse
    zyada banao). Ye "auto-improving bot" ban jaata hai.
11. **WhisperX / forced alignment** — script text ko hi alignment ke liye do (guessing band) → caption
    timing frame-accurate (abhi whisper ke word boundaries + snap use ho raha hai, wo bhi kaafi accha hai).
12. **Kokoro quantized/int8 model** — RAM 1 GB se ~300 MB pe aa jaayega, phir 1 GB VPS pe bhi Kokoro chalega.
13. **Auto thumbnail + Reels cover** — ffmpeg se ek frame + text overlay; Instagram feed pe farak padta hai.
14. **Topic dedupe semantic** — abhi word-level similarity hai; embeddings se "same story alag words" bhi
    pakad mein aayega (mass-produced content ka risk kam).
15. **CI** — GitHub Actions pe `pytest -q` + `pyflakes` har push pe; ek "golden render" test (fixed 3 clips,
    5s) taaki koi change render tod de to turant pata chale.
16. **Model pre-download in Dockerfile** — pehla run slow hota hai (350 MB download); image mein bake kar
    do to deploy ke baad turant ready.

### D. Kal ka kaam (jab channel chal jaaye)

17. Multi-platform: Facebook Reels, X, Snapchat — same mp4 jaata hai.
18. Audience comments se topic mining (YouTube Comments API) — log kya poochhte hain, wahi video banao.
19. Cost tracking dashboard (`/stats` ka expansion) + Telegram pe weekly report.
20. Backup: SQLite + renders ka rclone backup (free: Google Drive 15 GB).

---

## 5. Antigravity mein setup (step by step)

**Pehle ye samajh lo:** is workspace mein **models nahi hain** (Kokoro 325 MB + Piper 63 MB ko humne
jaan-boojh kar `/tmp` mein rakha tha taaki workspace halka rahe). Antigravity mein pehli render pe
models khud download honge — isliye `TTS_MODEL_DIR` aisi jagah set karna jahan 1 GB jagah ho.

### Step 0 — Zaroorat
- Python **3.11+**, Git, **FFmpeg** (system package), internet
- RAM: 2 GB minimum (Piper + tiny.en whisper), 4 GB comfortable (Kokoro + base.en)

### Step 1 — Project Antigravity mein kholo
```
File → Open Folder → factshorts-bot
```
Agar git repo bana ke rakhna hai (recommended):
```bash
cd factshorts-bot
git init && git add -A && git commit -m "v3: free local voice + story mode"
```

### Step 2 — Environment
```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
ffmpeg -version                     # check (Ubuntu: sudo apt install ffmpeg)
```

### Step 3 — `.env` banao
```bash
cp .env.example .env
```
Minimum keys (sirf 3 chahiye pehle test ke liye):

| Key | Kahan se | Zaroori? |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | @BotFather | bot ke liye haan |
| `TELEGRAM_ALLOWED_USER_IDS` | @userinfobot | haan (security) |
| `GEMINI_API_KEY` | aistudio.google.com (free) | story 60s ke liye strongly recommended |
| `PEXELS_API_KEY` | pexels.com/api (free) | recommended (better footage) |

Voice ke liye **koi key nahi** — bas pehli baar:
```ini
VOICE_PROVIDER=kokoro          # ya piper (halka, 8x fast)
VIDEO_MODE=story               # ~60s story videos
TTS_MODEL_DIR=/home/yourname/factshorts-models   # 1 GB jagah wala folder
```

### Step 4 — Verify aur pehla video
```bash
python main.py --check                                  # sab green hona chahiye
python main.py --mode story --niche animals --generate   # pehla ~60s video (model download hoga)
python main.py --demo                                    # 10-15s quick test, offline
python main.py --bot                                     # Telegram bot + scheduler chalu
```

### Step 5 — Publishing (jab video pasand aa jaye)
```bash
python main.py --auth                    # YouTube OAuth (ek baar, browser)
python main.py --upload 1                # ya Telegram se /approve
```
Instagram ke liye `docs/INSTAGRAM_SETUP.md`, hosting ke liye `docs/DEPLOYMENT.md`.

### Antigravity ko kya prompt dena hai (copy-paste)

```
Read PROJECT_GUIDE.md and README.md completely first.
This is a Python 3.11 YouTube Shorts auto-generator. Voice is 100% free and local
(Kokoro-82M / Piper via factshorts/tts_local.py), captions get word timings from
factshorts/align.py (faster-whisper), and factshorts/config.py has two modes
(facts = 10-15s, story = ~60s).

Rules:
- Never add a paid API or key to the voice path.
- Run `pytest -q` and `python -m pyflakes factshorts/*.py main.py` after every change; both must stay clean.
- Update .env.example for every new config key and mention it in README.md.
- Keep the render under the host's RAM (2 GB): VIDEO_THREADS / VIDEO_PRESET knobs exist for that.

Task: <jo karna hai wo likho — e.g. "add caption pop animation" ya "add Hindi (hi_IN) Piper voice support">
```

---

## 6. Cheat sheet — sabse zyada kaam aane wale commands

```bash
python main.py --check                                   # config + dependency health
python main.py --selftest                                # 5 sec test render
python main.py --generate --niche space                  # 10-15s fact video
python main.py --generate --mode story --niche animals --topic "immortal jellyfish"
python main.py --trends --niche science --trends-geo IN  # aaj ke trending subjects
python main.py --demo                                    # keys ke bina offline demo
python main.py --script-test                             # script + SEO only (koi render nahi)
python main.py --bot                                     # Telegram bot + scheduler
python main.py --daemon                                  # sirf scheduler (headless)
pytest -q                                                # 46 tests
python -m pyflakes factshorts/*.py main.py               # lint
```

Telegram se: `/generate` · `/mode story` · `/voiceprovider kokoro` · `/voice list` · `/approve` ·
`/regenerate` · `/schedule 08:30,19:30` · `/queue` · `/stats` · `/status`

---

## 7. Ek nazar mein: "kya free hai, kya nahi"

| Cheez | Status |
|---|---|
| Voice (Kokoro / Piper) | ✅ 100% free, open-source, offline, commercial OK |
| Captions (faster-whisper) | ✅ free, local, MIT |
| Footage (Pexels/Pixabay/NASA/Wikimedia) | ✅ free commercial |
| Facts (Google Trends + Wikipedia) | ✅ free, keyless (Wikipedia CC BY-SA → credit jaata hai) |
| LLM (Gemini/Groq free tier) | ✅ free tier (limits hain) — optional |
| Render (FFmpeg) | ✅ free |
| Telegram bot | ✅ free |
| YouTube/Instagram upload | ✅ free (API quota limits) |
| Hosting | ✅ free options hain (GitHub Actions / Oracle free tier) |
| **Total monthly cost** | **₹0** — bas internet aur thodi CPU |

Sawaal ho to bolo, main samjha dunga.
