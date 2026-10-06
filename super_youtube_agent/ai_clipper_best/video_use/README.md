# 🎬 Video-Use: Conversational AI Video Editing & Auto-Clipping Engine

Inspired by **`browser-use/video-use`** and powered by **Jev AI Decision Engine (TypeSafe AI)** + FFmpeg Cinematic Chains.

---

## ⚡ What It Does
Instead of spending hours manually scrubbing timelines, trimming dead space, and color grading in Premiere Pro or DaVinci Resolve:
You provide your raw video and a single conversational prompt:
```bash
python -m video_use.video_use_engine --input raw_take.mp4 --prompt "Edit these raw takes into a 45-second high-energy launch video with cinematic color grade and punchy captions"
```

### Key Features:
1. **Jev Decision Virality Scorer**:
   - Sub-second decision engine evaluating 20s-50s candidate dialogue windows.
   - Outputs virality score (0.0 to 1.0) and retention confidence.
2. **30ms Pop-Free Audio Crossfades**:
   - Eliminates clicks and audio popping on cut transitions.
3. **Automated Cinematic Grading**:
   - Supports `cinematic` (teal-orange warmth), `warm_punch`, `dark_moody`, and `cyberpunk` LUT curves.
4. **Vertical 9:16 Smart Framing**:
   - Centers and scales landscape footage for vertical YouTube Shorts, TikToks, and Instagram Reels.
5. **Self-Evaluating Quality Gate**:
   - Automatically verifies render integrity and file sizes before completion.

---

## 🚀 Quick Start

```bash
cd "d:\facts_yt\ai clipper best"

# Run with any natural language command
python -m video_use.video_use_engine --input "your_raw_video.mp4" --prompt "Make a 30s punchy dark moody short with high energy"
```

## 🔑 Optional Jev / OpenRouter Hookup
In `.env` or system environment:
```env
JEV_API_KEY=your_jev_api_key_or_openrouter_key
```
*(If no key is provided, the built-in local Jev-Sim heuristic decision engine executes with ₹0 cost).*
