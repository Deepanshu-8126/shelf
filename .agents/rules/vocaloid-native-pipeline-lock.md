# Vocaloid Pipeline Official Lock (Zero Custom Code Hack Law)

## 1. Absolute Prohibition of Ad-Hoc Code
- **Never Write Custom Renderers**: Under no circumstances should the agent write scratch Python scripts (`render_*.py`, PIL canvas scripts, OpenCV video writers) to simulate or fake Vocaloid visual effects.
- **No Mock Pipelines**: Do not invent fake timeline generators or ad-hoc animation loops.

## 2. 100% Native Tooling & Trained Stack
All Vocaloid-style MVs must strictly use the official open-source pipeline (`vocaloid-style-mv-pipeline` by NikusonP):
- **Front-end Engine**: Deterministic Canvas2D scene layers + WebGL2 post-processing (line-boil, OKLab LUTs, bloom, chromatic aberration) + JIZURA (字面) kinetic typography layer.
- **Deterministic Time**: Every frame is a pure mathematical function of song time $t$. No wall-clock randomness.
- **Beat-Locked Grid**: Cuts must snap to `B(n)` bar boundaries or `nb(t)` nearest beats from `analysis/audio.json`.

## 3. Official Execution Protocol
1. **Scaffold Project**:
   ```bash
   python skills/vocaloid-style-mv/scripts/new_project.py <target_dir> --song <audio.wav> --lyrics <lyrics.lrc> --setup
   ```
2. **Audio Analysis**:
   ```bash
   python tools/analyze_audio.py
   ```
3. **Art & Asset Generation**:
   - Character bible + reference master -> chroma-key RGBA assets in `assets/char/`.
4. **Timeline Configuration**:
   - Edit native `engine/timeline.js` to configure shots, scene parameters, and JIZURA typography plans.
5. **Native Headless Render**:
   - Render via Playwright + ffmpeg:
   ```bash
   node tools/render_final.mjs --codec x264
   ```
   *(Use `--codec x264` when running on systems without NVIDIA NVENC)*
6. **Official Verification**:
   - Inspect stills and contact sheets using `node tools/stills.mjs` and `python tools/contact_sheet.py`.
