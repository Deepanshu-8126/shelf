# The actual best pick — verified 2026-10-01

## 🏆 harry0703/MoneyPrinterTurbo

| Repo | ★ | Last push | Open issues | Verdict |
|---|---|---|---|---|
| **harry0703/MoneyPrinterTurbo** | **127,690** | **2026-10-01 (today)** | 40 | **Winner** |
| FujiwaraChoki/MoneyPrinterV2 | 32,031 | 2026-09-15 | 92 | Runner-up, noisier issue tracker |
| rayventura/ShortGPT | 8,000 | 2025-02-10 | 86 | Abandoned 20 months |
| Anil-matcha/AI-Youtube-Shorts-Generator | 5,191 | 2026-09-29 | 25 | Best *clipper*, but no dubbing |
| Hao0321/video-autopilot-kit | 2,162 | 2026-09-30 | 7 | CapCut drafts only |
| ClipsAI/clipsai | 544 | 2024-01-17 | 15 | Dead |
| MatteoFasulo/Whisper-TikTok | 340 | 2026-07-10 | 1 | Tiny, fine as reference |
| NaufalRizqullah/opensource-clipping | 135 | 2026-09-26 | 0 | Too new/small to bet on |

16× the stars of ShortGPT and commits landing *today* — fixes to TTS chunking, subtitle
line-wrapping and clip isolation within the last 24 hours.

## It hits all three of your requirements, verified in source

**1. Multi-language (US English + Spanish)** — `app/services/data/azure_voices.json`
ships **321 neural voices**: **45 Spanish** (`es-ES-AlvaroNeural`, `es-MX-JorgeNeural`,
`es-AR-TomasNeural`, `es-CO-GonzaloNeural`, … every LatAm locale) and **17 en-US**.
Not a generic "30+ languages" blurb — an enumerated voice table in the repo.

**2. Copyright-free voices** — `app/services/voice.py` imports `edge_tts` directly.
Free, no key, no licence claim. Paid engines (MiniMax, SiliconFlow, ElevenLabs music)
exist but are strictly opt-in and gated behind explicit `--confirm-*-charge` flags.

**3. Batch / loop** — `cli.py` has **`--batch-file`**, `--video-count`, `--n-threads`,
`--task-id`, `--stop-at`. Plus a FastAPI service (`app/controllers/v1`) if you'd rather
queue over HTTP, and Docker / Docker-GPU compose files.

Bonus: `--subtitle-animation`, `--subtitle-display-mode`, stroke/background/position —
the CapCut-style kinetic caption controls, as real CLI flags.

## The one caveat

MoneyPrinterTurbo is a **generator**, not a clipper. Default `video_source` is `pexels`
stock footage; it won't watch a 2-hour GTA 6 stream and find the viral 30 seconds.
But `schema.py` supports `video_source: "local"` + `video_materials`, so you feed it
your own footage.

## Therefore: the strongest setup is two repos, not one

```
yt-clipper (this project)          MoneyPrinterTurbo
  yt-dlp long video            →   consumes clips as local materials
  Whisper word timings         →   adds EN/ES Edge-TTS voiceover
  LLM picks viral segments     →   animated subtitles + render
  exports 9:16 clips               --batch-file loops the whole queue
```
My pipeline does the part MoneyPrinterTurbo lacks (finding the moment); it does the part
mine does more simply (batch render farm with 321 voices and a web UI).

## Install

```bash
git clone https://github.com/harry0703/MoneyPrinterTurbo.git
cd MoneyPrinterTurbo
cp config.example.toml config.toml      # add LLM key + pexels key here
./webui.sh                              # or: webui.bat on Windows
python cli.py --help                    # batch mode
docker compose up                       # or containerised
```
Note `cp config.example.toml config.toml` — skipping it is the #1 cause of startup errors.
