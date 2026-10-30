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

---

## 6. Lyrical Mode Master Standard (Zero Bootleg Audio & Zero Black Overlays)
- **Official Label Audio Mandate:** NEVER use fan-made uploads, bootlegs, or mashups with speech intros. Always verify and pull directly from the official record label channel (Saregama, T-Series, Zee Music, Sony Music, or official artist topic channel).
- **Audio-Slice First, Whisper Second:** Always slice the exact 30–45s hook audio FIRST (`ffmpeg -ss ... -t ...`). Then run Whisper base directly on THAT isolated slice (with `torch.set_num_threads(4)`) so `0.0s` in Whisper maps 1:1 to `0.0s` in the video timeline. Zero guessing, zero manual offset math.
- **Zero Black Overlay / Box Law:** NEVER draw dark translucent rectangles, letterboxes, or tint overlays over cinematic background plates. The video must remain 100% natural, crisp, and vibrant.
- **Rock-Solid Typography Law (Zero Jitter):** Text coordinates must be locked as immutable constants (`y = 380`). NEVER apply sine-wave bobbing/wobbling formulas (`int(np.sin(...) * 2)`) that cause 1–2px jitter tremors.
- **Legibility via Localized Drop Shadow Only:** Contrast is achieved strictly via Gaussian-blurred text shadow (blur radius 5, dark alpha 240) directly beneath glyphs.
- **Hermite Smooth Dissolves:** Use Hermite ease-in-out (`t*t*(3 - 2*t)`) for 0.4s fade-in and 0.4s fade-out.
- **Ping-Pong Seamless Loop:** Background video must play forward and reverse smoothly to eliminate jump cuts entirely.

---

## 7. Zero-Mistake Universal Song Production Mandate (Full-Length Cloud Engine)
- **Full-Length Song Default (Pura Gaana Standard):** Unless the user explicitly asks for a 30–45s Short/Reel, ALWAYS produce the complete, full-length song (3–4+ minutes) from start to finish.
- **Pure Studio Audio Mandate (Zero Dialogue & Zero Ads):** Sourced tracks must be stripped of any sponsor voiceovers (e.g. Saregama Carvaan ads) and movie dialogues. 0.0s must begin right at the authentic music intro.
- **Whisper Ground-Truth Full Schedule:** Run Whisper on the entire clean song track to generate millisecond onsets for EVERY verse, chorus, bridge, and outro. Save full schedule as `.lrc` and `_schedule.json`.
- **Cloud-First Rendering Mandate (Zero Local Overheating):** Full-length video rendering (5,000+ frames) MUST NEVER run locally on the user's PC. Always route heavy video rendering to GitHub Actions cloud runners (`ubuntu-latest`) with automated Artifact & Release delivery.
- **Pre-Flight 5-Point Validation:** Never declare any song ready without running: (1) Audio purity check, (2) Lyrics timing check, (3) Visual frame integrity check, (4) Asset git tracking check, and (5) Dry-run sanity check with 0 errors.

