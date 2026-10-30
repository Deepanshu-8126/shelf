# Viral Lyric Sync, Editorial Typography & Zero-Drift Laws
**Status:** STRICT PERMANENT LOCK (Constitutional Law)

This document locks the mandatory protocols and prevents recurring regressions discovered during viral short production:

---

## 1. Zero Guesswork Audio-Lyric Synchronization Law (Whisper Mandate)
- **The Core Violation:** Manually estimating lyrics timestamps or translating full-song positions (e.g. assuming "1:24" starts at 16s in a 45s cut) causes catastrophic 10+ second sync lag.
- **The Mandatory Protocol:**
  1. Whenever an audio slice is extracted for YouTube Shorts / Instagram Reels, **NEVER** write a single line of `LYRICS_TIMELINE` manually.
  2. **Mandatory Automated Step:** Immediately run local OpenAI Whisper (`whisper.load_model('base')`) directly on the exported audio slice (`.mp3` or `.wav`).
  3. Extract exact millisecond onsets (`start` and `end` timestamps) for every sung line and couplet.
  4. Build the narrative cards directly from the Whisper ground-truth transcription.
  5. Error threshold between vocal onset in audio and text display must be **$< 150\text{ms}$**.

---

## 2. Zero Code Syntax in Visual Canvas Law (No `//` or Debug Strings)
- **The Core Violation:** Injecting developer syntax (`// VIRAL REEL SESSIONS`, `// AURA PHONK 2026`, `// SESSION`) into the visual canvas destroys high-fashion editorial aesthetics.
- **The Mandatory Protocol:**
  1. **Strictly Forbidden Characters:** `//`, `/*`, `-->`, `#`, `DEBUG`, `SESSION`, `TEMP`, or any coding comment markers on the visible video frame.
  2. **Approved Header Format:** Pure luxury typography:
     - Title in Google Font `RozhaOne-Regular.ttf` or Latin serif (e.g., `अल्फ़ाज़   •   ALFAAZ`).
     - Subtitle: `ARTIST 1   x   ARTIST 2` in tracked uppercase sans-serif (e.g., Arial 20-24pt).
     - Divider: Clean hairline accent rule (`#E1DAD2` / `#C8102E`, width 1-2px, width 320-400px centered).
     - Nothing else.

---

## 3. Aesthetic Template Lock (No Cold Technical Grids for Indie/Lofi)
- **The Core Violation:** Drifting away from the proven, beloved aesthetic template into technical architect grids with crosshairs.
- **The Mandatory Protocol for Hindi/Punjabi/Lofi Lyric Videos:**
  - **Canvas:** Warm vintage handmade ivory parchment (`#FAF8F4`) with subtle Gaussian grain (2-3%) and radial vignette (10-15%).
  - **Atmosphere:** Precomputed 90-frame looping water caustics reflection mesh (simulating shimmering sunlight through water).
  - **Floating Elements:** 16-18 botanical rose petals (`assets/botanical_petals`) drifting with sine-wave wind sway, plus floating organic dust motes.
  - **Spinning Vinyl Disc:** 360° continuously rotating dark vinyl record (`size=500-520px`) with realistic micro-grooves, antique gold metallic trim, and a Devanagari center label (`#FAF4EE` with crimson border).
  - **Typography (Rozha One):**
    - Active line: Rich Royal Crimson (`#C8102E`) with a 10px Gaussian blur crimson glow aura and dynamic beat scale pulse ($1.00 \times \rightarrow 1.04 \times$).
    - Upcoming/Past lines: Warm muted taupe (`#91847A` / `#A59B91`) with smooth $-14\text{px}$ glide and color morph.
  - **Negative Space:** Audio-reactive fluid ripple wave at `y = 1380`.
  - **Timeline:** Minimalist Spotify scrubber at bottom (`y = 1680`) with clean `0:08 / 0:45` elapsed/total duration.

---

## 4. Zero Unicode Emoji Box Glitch Law (`□`)
- **The Core Violation:** Passing emoji characters (`🌹`, `⚡`, `✨`) into PIL `ImageDraw.text()` when using standard TTF fonts (`RozhaOne-Regular.ttf` or `arial.ttf`) causes them to render as ugly empty rectangular boxes `□`.
- **The Mandatory Protocol:**
  1. Never put emoji Unicode in strings rendered via standard TrueType fonts.
  2. Always use real high-resolution transparent PNG sprites (e.g. `assets/botanical_petals`) or pure typographic glyphs (`•`, `—`, `|`).

---

## 5. Media Hygiene & Disk Saturation Protection (Drive D: Laws)
- **The Core Violation:** Leaving 300+ MB intermediate `.wav` chunks in `output/` reduces Drive D: capacity to critical levels (< 10 MB), crashing ffmpeg and Git operations.
- **The Mandatory Protocol:**
  1. Clean up intermediate WAV slices (`temp_*.wav`, `test_*.wav`, `temp_*_mono.wav`) inside `try ... finally` blocks immediately after RMS/FFT extraction.
  2. Use `Move-Item` instead of `Copy-Item` when relocating large video/audio files on the same drive volume.
