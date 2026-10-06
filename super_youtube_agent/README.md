# 🚀 Super YouTube Agent — Multi-Channel Production Suite

Unified production architecture for 5 automated YouTube channels, autonomous documentary engines, and AI video clippers. All engines share a single master environment configuration ([.env](file:///d:/facts_yt/.env)) and centralized runner scripts.

---

## 🏛️ Channel Directory & Architecture Map

```text
super_youtube_agent/
│
├── 01_facts_shorts/     # 🎬 [Channel 1: FactShorts] Viral 9:16 Facts Pipeline (Gemini/Groq + Pexels + ElevenLabs)
│   ├── factshorts/      # Core Shorts engine & kinetic subtitle generator
│   ├── venv/            # Central Python production virtual environment
│   └── main.py          # CLI / Scheduler entry point
│
├── 02_story_studio/     # 🕹️ [Channel 2: Story Studio] Web Dashboard (http://localhost:8787)
│   ├── web/             # Full Web Control UI
│   ├── agent/           # Market scout, GTA VI clips lab & script drafts
│   └── server.py        # Web server backend
│
├── 03_dark_sutra/       # 🕵️ [Channel 3: Dark Sutra] True Crime & Forensic Mystery Studio
│   ├── dark_sutra_brain.py # 4-Beat Hindi true crime script dossier generator
│   ├── kenburns_engine.py  # 2.5D archival photo zoom & pan
│   ├── document_highlighter.py # Vintage declassified marker wipe
│   └── main.py          # Master documentary generator (4K + CapCut export)
│
├── 04_lofi_studio/      # ☕ [Channel 4: Lofi Studio] 24/7 Lofi Ambient Music & Streamer
│   ├── audio_dsp.py     # Slowed + Reverb + Vinyl crackle + Rain DSP
│   └── main_lofi.py     # Mixtape builder & YouTube Live streamer
│
├── 05_vox_ledger/       # 🌐 [Channel 5: The Global Ledger] Geopolitics & Animated Satellite Maps
│   ├── motion_templates.py # GSAP 2.5D map animations, coordinates & route vectors
│   ├── gemini_rag_scriptwriter.py # High-CPM geopolitical scripts (Hindi/Hinglish)
│   └── cli.py           # Master CLI generator (4K + CapCut export)
│
├── 06_ai_clipper/       # ✂️ [AI Clipper Best] Auto-Clipper for Podcasts & Long Streams
│   └── autoclip/        # Video segmenting, speaker tracking & viral hook clipper
│
├── veo_flow_engine.py   # 🎥 Google Flow (Veo 2) Autonomous Scene Generator & FFmpeg Delogo
├── hardcore_motion_editor.py # 🎯 Hardcore 2.5D Motion Graphics & Tactical HUD Radar Engine (60fps)
├── enhancer_engine.py   # ⚡ 4K Cinema Upscaler (60fps) + Top 3 Viral Caption Master
├── seo_schema_generator.py # 🔍 Google Rich Results Schema.org VideoObject JSON-LD
└── run.bat              # Unified local launcher
```

---

## 📺 Channel Deep Dive

| Channel / Studio | Format | Niche & Style | AI / Engine Stack |
| :--- | :--- | :--- | :--- |
| **Channel 1: Facts Shorts** | 9:16 Shorts (15–60s) | Space, Science, History, Viral Facts | **Pexels & Pixabay** (B-Roll), **ElevenLabs / Kokoro** (Voice), **Gemini & Groq** (Scripts), **Whisper** (Kinetic Subtitles) |
| **Channel 2: Story Studio** | 16:9 & 9:16 | Gaming, Hindi/Hinglish Stories, GTA VI | **Web UI (:8787)**, Market Scout, YouTube OAuth Auto-draft & Publisher |
| **Channel 3: Dark Case Studio** | 9:16 & 16:9 Docs | True Crime, Unsolved Mysteries, Declassified Dossiers | **Wikimedia Archival Scraper**, **2.5D Ken Burns**, **Document Highlighter Sweep**, **Procedural Tension Drones** |
| **Channel 4: Lofi Studio** | 16:9 (Long / Live) | Hindi Sad, Study, Rain, Dark Midnight, Anime Lo-Fi | **Audio DSP** (Slowed + Reverb), **Live RTMP Streamer**, Aesthetic Loop Compositor |
| **Channel 5: Vox Studio** | 9:16 & 16:9 | Visual Journalism, Geopolitics, Johnny Harris style | **Interactive Map Engines**, **GSAP Motion Templates**, **Gemini RAG Research** |
| **AI Clipper Best** | 9:16 Shorts | Auto-Clips from Long Podcasts / Streams | Face Detection, Silence Trimming, Auto-Subtitles |

---

## 🔑 Shared Master Environment: [.env](file:///d:/facts_yt/.env)

Every channel automatically loads credentials and configurations from the master root environment file:

```ini
# Voice AI (ElevenLabs)
ELEVENLABS_API_KEY=sk_...
ELEVENLABS_VOICE_ID=pNInz6obpgDQGcFmaJgB
ELEVENLABS_MODEL=eleven_multilingual_v2

# LLM Intelligence (Gemini & Groq)
GEMINI_API_KEY=AQ.Ab8RN6...
GROQ_API_KEY=gsk_...
GROQ_MODEL=qwen/qwen3.8-27b

# Stock Media
PEXELS_API_KEY=Ng530...
PIXABAY_API_KEY=578418...

# Telegram Bot
TELEGRAM_BOT_TOKEN=8809830963:...
TELEGRAM_CHAT_ID=6486771356

# Research & Cloud GPU
APIFY_TOKEN=apify_api_...
TAVILY_API_KEY=tvly-dev-...
GPU_WORKER_URL=https://...trycloudflare.com
```

> [!TIP]
> You only ever need to edit **`d:\facts_yt\.env`**. Any key added or updated there is immediately available across all channels.

---

## ⚡ Quick Start: How to Run Any Channel

From the project root (`d:\facts_yt\`) or from inside `super_youtube_agent\`:

### 1. Channel 1: FactShorts
```cmd
# Render a fast demo Short
run.bat

# Generate a custom viral fact short
run.bat --channel1 --topic "James Webb Telescope Anomaly"
```

### 2. Channel 2: YouTube Story Studio
```cmd
# Launches web interface at http://localhost:8787
run.bat --channel2
# or: run.bat --studio
```

### 3. Channel 3: Dark Sutra (True Crime & Forensic Mysteries)
> **Brand Identity:** Dark Sutra | *Raaz Jo Daba Diye Gaye*
> **Content Style:** Hindi / Hinglish investigative documentary, cold cases, forensic dossiers, high-tension soundscapes.
> **Media Engine:** Wikimedia Archival Records + Pexels 4K Crime B-Roll + Pixabay Textures + Cross-Studio Tactical Satellite Map Radar.
```cmd
# Generate a viral 9:16 Short (Bermuda Triangle / Case File)
run.bat --sutra --topic "Bermuda Triangle Mystery" --format short

# Generate a high-retention 16:9 Mini-Documentary
run.bat --sutra --topic "Black Dolphin Prison Escapees" --format doc

# Use the --channel3 alias
run.bat --channel3 --topic "Dyatlov Pass Incident" --format doc
```

### 4. Channel 4: Lofi Ambient Studio
```cmd
# Render a 15-second test mixtape in 'rain' style
run.bat --channel4 --demo --style rain

# Render full 10-track dark midnight mixtape
run.bat --channel4 --run --style dark_midnight --count 10
```

### 5. Channel 5: The Global Ledger (Geopolitics & Strategic Maps)
> **Brand Identity:** The Global Ledger | *World Affairs, Money & Choke Points Decoded*
> **Content Style:** Vox / Johnny Harris style, geopolitical deep-dives, economic trade routes, animated satellite maps, high CPM ($8-$15/1000 views).
> **Niche Formula:** `global_ledger` (geopolitics, strategic waterways, defense, macroeconomics in Hindi/Hinglish).
```cmd
# Create a geopolitical explainer with animated maps
run.bat --ledger create "Strait of Hormuz Oil War" --niche global_ledger

# Create a Taiwan semiconductor explainer
run.bat --ledger create "The Silicon Shield: TSMC & Taiwan"

# Fetch breakout Google search trends and auto-produce
run.bat --ledger trends
```

### 6. AI Clipper Best
```cmd
# Auto-clip long podcasts or gameplay into viral shorts
run.bat --clipper
```

---

## 🎯 Dual-Channel Strategy: Dark Sutra vs The Global Ledger

| Feature | 🕵️ **Dark Sutra** (Ch 3) | 🌐 **The Global Ledger** (Ch 5) |
| :--- | :--- | :--- |
| **Primary Audience** | Crime, Mystery, Paranormal & Forensics | Geopolitics, Economics, Defense & World Strategy |
| **Monetization (CPM)** | Medium-High ($3 – $7 / 1,000 views) | Ultra-High ($8 – $15 / 1,000 views, Tech/Finance ads) |
| **Visual Core** | 2.5D Ken Burns, Classified Doc Markers, Red String Dossiers | GSAP Kinetic Typography, Satellite Maps, Animated Route Lines |
| **Voice Tone** | Deep, atmospheric, suspenseful Hindi documentary | Authoritative, inquisitive, fast-paced analytical Hindi |
| **Shorts (<60s)** | Single twist / mystery hook (instant virality) | Single choke-point / stat reveal (viral intellectual debate) |
| **Long-Form (8-12m)** | Full incident investigation with timeline reconstruction | Multi-chapter geopolitical breakdown with animated maps |
| **CLI Switch** | `--sutra` / `--channel3` / `-Sutra` | `--ledger` / `--channel5` / `-Ledger` |

---

## 🎨 Top 3 Viral Caption Styles & 4K Cinema Enhancer

Har render ke sath CapCut aur Premiere Pro me direct drag-and-drop karne ke liye `.ass` aur `.srt` files automatically output folder me save hoti hain.

### 1. `hormozi_pop` (MrBeast & Alex Hormozi Style)
- **Features:** Punchy 2–3 words/screen, bold sans-serif, electric yellow (`#FFFF00`) & neon green active word highlight, scale bounce pop-in.
- **Best for:** Fast-paced viral Shorts, retention maximization.
- **Command:** `run.bat --sutra --topic "Bermuda Triangle" --caption-style hormozi_pop`

### 2. `vox_minimal` (Johnny Harris / Vox Style)
- **Features:** Clean elegant typography, lower-third positioning, translucent dark backing pill, gold/amber accent highlights.
- **Best for:** Geopolitical explainers, intellectual debate, high-CPM audiences.
- **Command:** `run.bat --ledger create "Strait of Malacca" --caption-style vox_minimal`

### 3. `dark_dossier` (True Crime / Forensic Style)
- **Features:** Courier typewriter / distress look, blood-red (`#CC0000`) alert accents, classified stamp framing.
- **Best for:** Dark Sutra true crime, cold cases, declassified CIA/KGB files.
- **Command:** `run.bat --sutra --topic "Burari Deaths" --caption-style dark_dossier`

### ⚡ 4K 60FPS Cinema Video Enhancement
- Run with `--quality 4k` (default) to trigger the FFmpeg cinema grade filter chain:
  - **4K Master:** `2160x3840` (Shorts) / `3840x2160` (Docs)
  - **Lanczos Scaling + Unsharp Clarity Mask:** `unsharp=5:5:0.8:3:3:0.4`
  - **Dynamic Contrast & Vibrance:** `eq=contrast=1.06:brightness=0.01:saturation=1.12`
  - **Fluid 60 FPS:** Smooth motion playback with 320kbps high-fidelity audio.

