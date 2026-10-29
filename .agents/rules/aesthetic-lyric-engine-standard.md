# Aesthetic Lyric Video Engine Standard

## 1. Core Visual DNA (Design System Lock)
- **Canvas / Background**: Warm Vintage Handmade Ivory/Parchment (`#FAF8F4` / `RGB(250, 248, 244)`).
  - Shimmering Water Caustics light reflection overlay (moving sunlight through water).
  - Subtle audio-reactive fluid wave accent in negative space.
  - Procedural 2-3% fine film grain (Gaussian noise).
  - Soft radial breathing vignette (12-15% edge falloff).
  - Subtle floating dust specks (25-30 organic floating particles).
  - **Zero Player Clutter**: Bottom Spotify scrubber is disabled by default for 9:16 Shorts to give maximum clean negative space (can be toggled via `--player`).
- **Typography & Color Palette**:
  - Primary Font: Google Font `RozhaOne-Regular.ttf` for Devanagari calligraphy / Hindi lyrics.
  - Accent Red: Rich Crimson Red (`#C8102E` / `RGB(200, 16, 46)`).
  - Metadata Font: Sleek Latin tracking serif (`#968C82` / `RGB(150, 140, 130)`).
  - Progress / Line Accents: Soft parchment lines (`#E1DAD2`).
- **Motion Graphic Kinetics (Top-Creator Viral Standard)**:
  - **Word-by-Word Kinetic Cascade**: Words enter with elastic spring overshoot ($0.92 \rightarrow 1.05 \rightarrow 1.0$) and slide-up ($dy = 22\text{px} \rightarrow 0\text{px}$).
  - **Ambient Crimson Aura**: Active sung words cast a radiant Gaussian blurred shadow (`#C8102E`, blur 10px).
  - **Ghost Silhouette Anticipation**: Upcoming words in active line and entering stanzas display in soft ghost grey (`#D7CDC3`) to keep viewer retention hooked.
  - **Dynamic Line Glide & Color Morph**: When next line begins, previous lines smoothly glide up ($dy = -20\text{px}$) and morph from crimson into warm muted vintage taupe (`#91847A`).
  - **Music Beat Pulse**: Active vocals subtly breathe in sync with audio RMS energy.
  - **Seamless Stanza Transition**: Exiting verse smoothly glides up ($-40\text{px}$) and fades out, while next verse glides up from below ($+35\text{px}$) in ghost anticipation with zero blank gap and zero text collision.

## 2. Layouts by Aspect Ratio
- **16:9 Landscape (YouTube / Desktop / Master)**:
  - **Left Section (Spinning Vinyl Turntable)**: Continuous 360° spinning vinyl record (`size=520px`) with concentric micro-grooves, rotating light sheen, and a **circular artist photo/artwork medallion** (`r_label=96px`) framed with crimson (`#C8102E`) and metallic gold trim, plus an ambient crimson breathing aura glow.
  - **Right Section (Kinetic Typography)**: Vertically centered Devanagari calligraphy stack (`RozhaOne-Regular.ttf`) popping with kinetic scale on vocal drops.
  - **Bottom (Interactive Player)**: Full-width Spotify-style playback timeline with seek dot and real-time timestamps.
- **9:16 Vertical (Instagram Reels / YouTube Shorts)**:
  - **Center Stack**: 2-3 line kinetic cards with breathing vertical rhythm.
  - **Top**: Clean artist & track metadata badge (`SONG • ARTIST`).
  - **Bottom Negative Space**: Shimmering water caustics + audio-reactive fluid ripple wave.

## 3. Reticle Audio-Vocal Alignment Standard (Zero Mismatch Law - STRICT LOCK)
- **Zero-Trust Crowdsourced Policy**:
  - NEVER feed raw crowdsourced `.lrc` (LRCLIB, Spotify, Musixmatch, Megalobiz) directly into the video encoder. Crowdsourced LRCs suffer from **cumulative human latency lag** (1.2s - 2.5s delay), missing stanza repetitions, and phonetically butchered Hindi/Punjabi/Saraiki lyrics.
- **The "Pehle Line Theek, Aage Jaake Kharab" Anti-Drift Protocol**:
  1. **Intro-Silence Zero-Point Alignment ($t_0$)**: YouTube audio rips, Spotify stems, and master WAVs differ in lead-in silence (0.3s to 2.0s). Always calibrate the very first vocal onset against audio RMS energy.
  2. **Stanza Repeat Auditing**: South Asian / Bollywood songs frequently repeat the Mukhda and Antara lines twice. Verify that repeated couplets exist in the `.lrc`. If a repeat is missing, all subsequent lines will catastrophically drift out of phase.
  3. **Instrumental Solo Breaks**: Long instrumental passages (flute, sarangi, guitar solos) must have explicit pause markers (`[mm:ss.xx] <empty>`), preventing text ghosting during negative space.
  4. **Waveform Energy Verification**: Every lyric timestamp must be cross-checked against localized RMS energy or Whisper onsets. Error threshold must be $< 350\text{ms}$.
- **Pristine Devanagari Typography Shaping Law**:
  - Never break Devanagari / Gurmukhi scripts using `.split(" ")` with custom word bounding-box calculations. Matras (ि, ी, ु, ू, ँ, ं) and conjuncts (क्, त्) will collide and disintegrate (`केरेमोचोगरिदे`).
  - Always render full sentences using HarfBuzz / FreeType shaping, employing dynamic step-down fonts (`font_hero → font_large → font_med`) if line width exceeds canvas boundary.
- **Master execution command**:
  ```bash
  python core/studio_master.py --pipeline lyric --audio "output/song_master.wav" --title "Song Title" --artist "Artist" --ratio 16:9 --duration 135.65 --lrc "raw_stems/song.lrc" --floral --player --output "output/master.mp4"
  ```

## 4. Autonomous Audio Intelligence & Dynamic Tempo Sensing
- The engine automatically calculates exact track BPM and dynamic RMS energy without manual guessing.
- Automatically switches between 3 dynamic pacing modes:
  - **`SLOW_SOULFUL`** ($\text{BPM} < 105$): 45°/s chill vintage vinyl spin, 0.95s dreamy crossfade, 0.20s word cadence, 1.04x gentle bounce.
  - **`MODERATE_LOFI`** ($105 \le \text{BPM} \le 125$): 62°/s standard vinyl spin, 0.80s transition, 0.17s word cadence, 1.06x balanced pop.
  - **`UPBEAT_PUNCHY`** ($\text{BPM} > 125$): 82°/s energetic groove spin, 0.65s snappy transition, 0.14s rapid-fire word cadence, 1.09x punchy overshoot.
- Real-time RMS audio energy dynamically modulates the active line scale pulse on every transient beat.
