# Aesthetic Lyric Video Engine Standard

## 1. Core Visual DNA (Design System Lock)
- **Canvas / Background**: Warm Vintage Handmade Ivory/Parchment (`#FAF8F4` / `RGB(250, 248, 244)`).
  - Procedural 2-3% fine film grain (Gaussian noise).
  - Soft radial breathing vignette (12-15% edge falloff).
  - Subtle floating dust specks (25-30 organic floating particles).
  - **Zero Dark Silhouettes / Zero AI Slop**: Never insert random black foreground silhouettes or distracting busy stock video unless explicitly requested.
- **Typography & Color Palette**:
  - Primary Font: Google Font `RozhaOne-Regular.ttf` for Devanagari calligraphy / Hindi lyrics.
  - Accent Red: Rich Crimson Red (`#C8102E` / `RGB(200, 16, 46)`).
  - Metadata Font: Sleek Latin tracking serif (`#968C82` / `RGB(150, 140, 130)`).
  - Progress / Line Accents: Soft parchment lines (`#E1DAD2`).
- **Motion Graphic Kinetics**:
  - Snappy word-by-word reveal popping directly on vocal hits.
  - Elastic micro-zoom ($1.15 \times \rightarrow 1.00 \times$) over 5-6 frames.
  - No text blur or abrupt jump cuts.

## 2. Layouts by Aspect Ratio
- **16:9 Landscape (YouTube / Desktop / Master)**:
  - **Left Section**: Continuous 360° spinning vinyl record (concentric groove rings, Anuv Jain/track center label, soft red ambient breathing glow).
  - **Right Section**: Vertically centered Devanagari calligraphy stack popping on vocal beats.
  - **Bottom**: Full-width Spotify-style playback timeline with current and total timestamps.
- **9:16 Vertical (Instagram Reels / YouTube Shorts)**:
  - **Center Stack**: Kinetic word-by-word reveal centered with vertical rhythm.
  - **Top**: Clean artist & track metadata badge.
  - **Bottom**: Minimalist progress scrubber.

## 3. Reticle Audio-Vocal Alignment Standard (Zero Mismatch Law)
- Never guess or manually hardcode lyric timestamps without running audio-stem Whisper verification.
- Always slice the audio from the actual vocal entry point (confirming singer is singing, not guitar solo/intro).
- Use word-level timestamps (`whisper.transcribe(..., word_timestamps=True)`).
- Ensure audio fades (50ms in, 150ms out) to eliminate pops and clicks.
