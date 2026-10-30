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

## 5. Native Vocaloid Pipeline Protocol (Zero Custom Code Hack Law)
- **Zero Ad-Hoc Scripting**: Never write scratch Python scripts (`render_*.py`, PIL hacks, OpenCV video loops) to fake or bypass the Vocaloid-style MV engine.
- **100% Author's Native Pipeline Only**: Strictly execute the official `vocaloid-style-mv-pipeline` workflow:
  - Scaffolding: `python skills/vocaloid-style-mv/scripts/new_project.py <dir> --song <song.wav> --lyrics <lyrics> --setup`
  - Audio Analysis: `python tools/analyze_audio.py`
  - Animation & Typography: Native `engine/timeline.js` (Canvas2D + WebGL2 post + JIZURA 字面)
  - Headless Browser Rendering: `node tools/render_final.mjs --codec x264` (Playwright Chromium + ffmpeg)
  - Frame Review: `node tools/stills.mjs` and `python tools/contact_sheet.py`
