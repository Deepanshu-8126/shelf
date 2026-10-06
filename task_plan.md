# 📋 Task Plan: High-Quality Facts Pipeline with Option 1 Animated Captions & Smart Style Decision Engine

## Status: Planning Completed (Awaiting User Review)

---

### Phase 1: Deep Analysis of "20 A Day on Mercury" ✅
- [x] Extracted metadata and inspected footage, voice, and audio ducking specs.
- [x] Identified winning voice: Kokoro-82M `am_michael` (American Male Michael, 24kHz).
- [x] Identified stock footage pipeline: 6 curated Pexels clips with Ken-Burns motion & xfade.
- [x] Documented findings in `findings.md`.

---

### Phase 2: Design System & Smart Caption Router ✅
- [x] Create `factshorts/smart_caption_router.py` to intelligently decide caption style:
  - Space / Tech / AI -> `cyber_glow` (#00E5FF)
  - Danger / Shock / Extinction -> `mrbeast_fire` (#FF3300)
  - Money / Wealth / Finance -> `hormozi_yellow` (#FFE600)
  - Documentary / Crime / History -> `vox_minimal` (#38BDF8)
  - General Viral / Psychology -> `tiktok_green` (#00FF88)
- [x] Unit tested with 6/6 test cases passing.

---

### Phase 3: Pipeline Integration & Bug Fixes in `01_facts_shorts` ✅
- [x] Fixed FFmpeg crop out-of-bounds crash in `_zoom_chain` using bounds clamp (`max(0, min(in_w - w, ...))`).
- [x] Fixed isolated worker path in `tts_local.py`.
- [x] Created multi-voice engine in `factshorts/multi_voice.py` supporting 2-3 speaker handoffs.
- [x] Locked English voices: `am_michael`, `en-US-ChristopherNeural`, `en-US-JennyNeural`, `elevenlabs:Adam`.

---

### Phase 4: Mercury Gold Standard Standardization & Verification 🟡
- [ ] Add CLI runner to `caption_studio/engine.py` to isolate Playwright sync execution from parent asyncio loops.
- [ ] Connect `factshorts/render.py` to invoke `caption_studio.engine` via clean subprocess.
- [ ] Execute end-to-end verification render and capture frame previews.
- [ ] Deliver final walkthrough and proof to user.
