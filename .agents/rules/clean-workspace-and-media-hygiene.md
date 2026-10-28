# Workspace Rule: Clean Structure & Media Hygiene (Zero Clutter Policy)

Permanently enforce strict folder cleanliness, zero file bloat, and automated media cleanup across this workspace:

1. **Zero-Clutter Policy**:
   - No loose scratch scripts (`test_*.py`, `tune_*.py`, `tmp_*`) dumped in project roots.
   - All scratch work must go to `archive/experiments/` or temporary execution.

2. **Media Hygiene**:
   - No loose intermediate audio/video chunks (`chunk_*.wav`, `tmp_*.wav`, `test_*.wav`).
   - Every script must clean up intermediate audio buffers immediately using `unlink(missing_ok=True)`.

3. **Standard 4-Folder Production Layout**:
   - `core/`: Production scripts only.
   - `raw_stems/`: Input media files.
   - `output/`: Final production master files (`.mp3`, `.mp4`).
   - `archive/`: Old experiments and retired media.

4. **Self-Auditing**:
   - Keep root folders lean (< 10 files). Zero clutter allowed.
