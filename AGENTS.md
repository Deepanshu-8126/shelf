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
