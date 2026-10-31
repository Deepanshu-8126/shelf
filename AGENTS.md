# AGENTS.md - Workspace Constitution & Engineering Laws

## 1. Clean Workspace Architecture & Zero Clutter Policy
- **No Root Dumping**: Never create scratch, test, or tuning scripts (`test_*.py`, `tune_*.py`, `tmp_*`) directly in project root folders.
- **Media Hygiene**: Large audio/video intermediate WAV chunks (`tmp_*.wav`, `chunk_*.wav`, `test_*.wav`) must be immediately deleted upon generation.
- **Mandatory 4-Folder Architecture**:
  - `core/`: Production pipeline code.
  - `raw_stems/`: Source high-resolution media.
  - `output/`: Final verified production master files.
  - `archive/`: Historical experiments and deprecated assets.

## 2. Brahmastra Runtime Verification (Reticle Protocol)
- Follow **Look -> Act -> Observe -> Assert**.
- Never claim success without running build/audio verification tools and checking logs for `0 errors`.
- Auto-heal immediately if any regression occurs.

## 3. Copyright Stealth Standards
- 100% zero Content ID claims across the entire timeline verified by `deep_sliding_copyright_audit.py` before final delivery.
- No chipmunk vocals; maintain natural warmth and authentic acoustic instruments.

## 4. Viral Lyric Sync, Header Purity & Aesthetic Template Laws
- **Zero Guesswork Whisper Mandate**: Never manually estimate lyric timestamps. Always run local Whisper base model on the exact audio slice to extract millisecond ground-truth onsets.
- **Zero Code Syntax in Visual Canvas**: Never inject `//`, `REEL SESSIONS`, `TEMP`, or code-style markers into visible video frames. Headers must be pure luxury typography (`SONG • ARTIST` with hairline divider).
- **Design System Lock for Hindi/Lofi Lyric Videos**: Mandatory baseline is `#FAF8F4` ivory parchment + 90-frame looping water caustics mesh + drifting botanical rose petals + 360° spinning vinyl disc with Devanagari medallion + Rozha One Devanagari calligraphy (`#C8102E` with glow aura).
- **Zero Emoji Unicode in PIL**: Never pass unicode emojis (`🌹`, `⚡`) to PIL `draw.text` with standard TTF fonts; always use transparent PNG sprites or pure typography.

## 5. Lyrical Mode Production Laws (Zero Bootleg & Zero Overlay)
- **Official Label Audio Mandate**: Never use unofficial, fan-uploaded clips with random intros. Always verify and pull directly from the official record label channel (Saregama, T-Series, Zee Music, Sony Music, official artist).
- **Audio-Slice First, Whisper Second**: Always slice the exact audio FIRST (`ffmpeg -ss ... -t ...`). Then run Whisper base directly on THAT isolated slice (with `torch.set_num_threads(4)`) so `0.0s` in Whisper maps 1:1 to `0.0s` in the video timeline.
- **Zero Black Overlay / Box Law**: Never draw dark translucent rectangles, letterboxes, or tint overlays over cinematic video plates. The background must remain 100% natural and vibrant.
- **Rock-Solid Typography (Zero Jitter)**: Text coordinates must be locked as immutable constants (`y = 380`). Never use sine-wave bobbing formulas (`int(np.sin(...) * 2)`) that cause jitter tremors. Contrast is achieved exclusively via Gaussian drop-shadow (radius 5, dark alpha 240) directly beneath glyphs.
- **Ping-Pong Seamless Loop**: Background video must cycle forward and reverse smoothly to eliminate jump cuts entirely.

## 6. Zero-Mistake Universal Song Production Mandate
- **Full-Length Song Default (Pura Gaana Standard)**: Unless explicitly instructed to create a 30–45s Short/Reel, ALWAYS produce the complete, full-length song (3–4+ minutes) from start to finish.
- **Pure Studio Audio Mandate (Zero Dialogue & Zero Ads)**: Sourced tracks must be stripped of any sponsor voiceovers (e.g. Saregama Carvaan ads) and movie dialogues. 0.0s must begin right at the authentic music intro.
- **Section-by-Section Slicing & VAD Gate (`universal_lyric_aligner.py`)**:
  - NEVER feed a raw 4-minute song blindly into Whisper in a single pass.
  - Automatically detect and isolate Instrumental Breaks (> 3.5s of flute, violin, guitar, or beat drops).
  - Enforce ZERO lyrics during instrumental solos so musical breaks never bleed into lyric timestamps.
  - Feed Whisper ONLY isolated vocal slices to extract 100% exact onsets.
  - Every timestamp MUST pass the 300Hz–3400Hz Voice Activity Detection (VAD) energy check to guarantee vocal attack.
- **Cloud-First Rendering Mandate (Zero Local Overheating)**: Full-length video rendering (5,000+ frames) MUST NEVER run locally on the user's PC. Always route heavy video rendering to GitHub Actions cloud runners (`ubuntu-latest`) with automated Artifact & Release delivery.
- **Pre-Flight 5-Point Validation**: Never declare any song ready without running: (1) Audio purity check, (2) VAD Gate lyric timing check, (3) Visual frame integrity check, (4) Asset git tracking check, and (5) Dry-run sanity check with 0 errors.


