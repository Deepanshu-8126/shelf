# Prompt for Antigravity — safe, staged CreatorOps upgrade

Copy the prompt below into Antigravity. It is deliberately phased: audit first, then wait for approval before editing code or enabling integrations.

---

You are working on the **existing CreatorOps project**, not a new greenfield app. Preserve its current design, data, APIs, channel settings, and rights controls. Before changing anything, identify the actual project root and read its `README.md`, `GTA6_CLIP_REPO_REVIEW.md`, `NINE_REPO_UPGRADE_AUDIT.md`, `VIDEO_QUALITY_STACK_AUDIT.md`, tests, and the GTA clip/publish policy code. Do not assume that any feature listed in a README is implemented or tested.

## Stage 0 — read-only audit; do not edit files yet

1. Report the current project root, architecture, existing behavior, channel slots, test status, missing runtime dependencies (especially FFmpeg), and untested real-world paths.
2. Compare the nine-repository proposal and the optional video-quality stack—including the LTX-2.3 GGUF/ComfyUI/Kaggle candidate and LTX Desktop local/API modes—against `NINE_REPO_UPGRADE_AUDIT.md` and `VIDEO_QUALITY_STACK_AUDIT.md`. Do **not** clone, install, execute, vendor, copy, or download repositories, model weights, or assets. Do not add dependencies, launch hosted notebooks/cloud GPUs, or make paid/provider calls. Treat repository-code licenses and the exact selected model/checkpoint/asset licenses separately; recheck current terms before any adoption.
3. Produce a concise `UPGRADE_PLAN.md` or, if any project edits are not yet approved, return the plan in chat only. List proposed files, data migrations, renderer/runtime and GPU/storage needs, provider/API needs, known and unknown recurring/per-use costs and quotas, rights/privacy risks, tests, human review gates, and rollback steps. Split optional features into independently approvable increments.
4. Stop and wait for explicit approval before modifying application code, databases, credentials, scheduled jobs, or platform accounts. Do not ask the user to paste secrets in chat.

## Non-negotiable product boundaries

- Keep the channel strategies separate: `ch-1` stays U.S./`en-US`; `ch-2` is a separate India/`hi-IN` GTA VI draft; preserve `ch-3` and all existing configuration. Never silently change a channel's niche, audience, region, or language.
- Keep CreatorOps YouTube-first and preserve the existing local-first workflow, tests, review prompts, and read-only workspace viewer. Do not grant arbitrary workspace file-write access through the viewer.
- Treat “NO HUMAN INPUT,” “₹0,” guaranteed virality, fixed growth percentages, and guaranteed monetization as unverified product claims. Do not display them as facts or infer them from star counts, agent count, or example output.
- Do not scrape, download, record, or republish third-party YouTube/Twitch/Kick/Instagram/TikTok media or chat. Do not use browser cookies, `yt-dlp`, browser automation, or another bypass to get around a platform access restriction. Accept only local files the operator owns or has explicit permission to use, unless a later task separately proves an official, permitted API path and documents the rights basis.
- For GTA VI, local ownership of a recording or a streamer’s permission does **not** clear Rockstar/Take-Two game IP, music, or other embedded rights. Preserve the existing fail-closed checks for commercial permission, original commentary, audio/music rights, no leaks/prohibited material, human render QA, and approval. Do not weaken the pre-release authorization gate. Never process leaked pre-release footage.
- Source credit is not a rights grant. YouTube reused-content/monetization eligibility is separate from copyright permission. Never claim that the software verifies a license reference.
- Automate only low-risk, read-only research and local draft generation. Keep rights decisions, final render review, niche changes, account authorization, and public posting behind explicit owner approval.
- Keep API keys and OAuth tokens out of chat, source code, logs, screenshots, and generated reports. Use existing local secret storage or a local `.env` file that is git-ignored; never reveal secret values in API responses.

## Approved implementation direction — only after Stage 0 approval

Implement in small, testable steps inside the existing CreatorOps architecture. Do **not** build a second dashboard or merge nine standalone applications.

### A. Three advisory clip-analysis layers

1. **Eligibility layer (hard gate):** local source path, ownership/license evidence, GTA-specific commercial-permission reference, release/leak restrictions, audio/music rights, and channel target. Fail closed on missing evidence. Scores must never override this layer.
2. **Local cue layer:** preserve the current OpenCV frame-change cue. If adding speech/audio cues, process only the authorized local file. If transcription needs Whisper or another model, make it an optional provider with visible dependency, privacy, quota, and cost status. No chat scraping, remote video downloads, or claims that a visual change is a kill/explosion/story event.
3. **Explainable candidate-ranking layer:** show candidate timestamps, dimensions/signals, reasons, confidence/limitations, and source provenance. Multiple scoring perspectives or an LLM may rank candidates for human review; a `4/5` threshold is advisory only and cannot approve rights, export, or publication. Do not claim the number of “agents” proves quality or virality.

The existing workflow's manual Hinglish captions, optional configured Hindi voiceover, and local render path remain available. Do not label captions as ASR unless speech recognition was actually run and reviewed.

### B. Daily research and feedback loop

- Use official/permitted sources for public metadata, beginning with the YouTube Data API where configured; surface quota, sample size, collection time, baseline, source URLs, and limitations.
- Use YouTube Analytics only for a channel the owner has authorized. Do not claim access to competitors' private retention, RPM, audience demographics, or revenue.
- A daily job may collect read-only signals, update an evidence ledger, and prepare drafts/recommendations. It must not publish, mass-comment, change a niche, or retarget another channel.
- Any breakout/trend percentage must have a reproducible baseline, time window, sample, and formula. If evidence is missing, display “not verified” rather than a fabricated percentage.
- Niche changes are proposals for the owner after a configurable multi-week sample and minimum evidence threshold. Never switch because of one day's results.

### C. Publishing and platform integrations

- Keep the existing official YouTube OAuth publisher and private-by-default behavior. Test only a private upload if credentials and user authorization are deliberately configured; never enable public autopublishing by default.
- Do not implement TikTok/Instagram/Telegram/Discord posting as if one key or one third-party service made them universally ready. Before adding any adapter, document that platform's official API, account requirements, app review, scopes, consent, quotas, content restrictions, and fees. If these are not configured, report `not connected` or `export only`.
- Do not use a browser-profile uploader or a third-party autoposter to bypass official platform gates. Add a kill switch and auditable publish record to any later authorized uploader.

### D. Cost and setup honesty

- Report required hardware, storage, runtime dependencies, network providers, API keys, free-tier caps, quotas, and possible costs. “Software is open source” is not equivalent to “the workflow costs ₹0.” Free tiers may change.
- Default to local processing where available, but never claim a local model, GPU, Node version, or FFmpeg exists until it is actually detected. Do not make paid calls during tests without explicit approval.
- Show the configured provider and known per-run estimate or “unknown,” never imply free usage where pricing/quota was not checked. Do not rely on Kaggle/Colab or a free-tier quota as an always-on production renderer.

### E. Optional pro-video quality stack — only as separately approved increments

Read `VIDEO_QUALITY_STACK_AUDIT.md` before proposing this work. The stack is optional; do not replace the current renderer or make model generation, upscaling, local TTS/music, or a new editor a baseline dependency.

1. **Renderer/captions:** inspect and validate CreatorOps' optional `kinetic_karaoke` path in `agent/game_clips.py` first. It builds an ASS word-highlight sidecar from manually entered caption lines, asks FFmpeg/libass to burn it into the MP4, and retains the standard SRT; its equal word timings are a draft, not ASR/alignment. Static SRT remains the default. Do not claim burn-in works until a synthetic render on the target FFmpeg build is actually checked. HyperFrames is only a later candidate if a different renderer is needed, not a required migration: it needs Node.js 22+ and FFmpeg. Current workspace probe was Node `v20.20.2`, no `ffmpeg` on `PATH`, and no usable `nvidia-smi` probe; re-check rather than assume. Choose one renderer, not multiple full editor stacks. Treat motion/kinetic skill packs as optional instructions, not an editor. Keep manual editable captions and the SRT fallback available.
2. **ASR/alignment:** if separately approved, test one backend on authorized local speech. Do not bundle WhisperX, archived Stable-ts, and a separate captioning web app together. Verify model/alignment-weight terms and Hindi/Hinglish results; keep names, transliteration, and timings human-correctable. Never call hand-entered captions ASR.
3. **TTS/music:** Kokoro is a possible Hindi local-TTS test because its official README documents Hindi; test pronunciation, naturalness, dependencies, runtime, and exact licenses before replacing a provider. Qwen3-TTS does not list Hindi in its official language table, and 97 ms refers to first-packet streaming latency, not a complete narration. ACE-Step is optional; verify the exact checkpoint terms/resources and audition each generated track. Do not send scripts/audio to hosted services or consume paid quotas without explicit approval.
4. **Video generation/upscaling:** treat LTX-2.5, Wan 2.2, HunyuanVideo, Real-ESRGAN, and the newly documented LTX-2.3 Q4_K_M GGUF + ComfyUI/Kaggle and LTX Desktop routes as separate optional, unverified capabilities. The selected third-party LTX-2.3 GGUF is 14.3 GB and follows custom LTX-2 Community terms (not Apache); the GGUF alone is not a complete ComfyUI setup, so verify all required text encoder, video/audio VAE, upscaler, and compatible node/workflow versions. Do not assume a free Kaggle single 16 GB T4, persistent storage, 720p/10-second runtime, or a commercial-use right; quotas and availability can change. The current LTX Desktop README says LTX-2.5 Fast is the local default and LTX-2.3 Fast remains selectable; explicitly select/verify the desired model. It requires at least 16 GB VRAM for local Windows/Linux (not 12 GB), 16 GB RAM (32 GB recommended), and 160 GB+ free disk on Windows; unsupported hardware may require API-only mode with an LTX API key. Keep API/cloud calls disabled absent explicit approval, and verify model-weight terms separately from app-code licenses. Never auto-download weights, allocate a cloud/Kaggle GPU, or assume upscaling creates native 4K detail. Exclude HappyHorse unless a verifiable official model card, weights, and license become available. Never present generated footage as actual GTA VI gameplay.
5. **Output QA:** report measured resolution, aspect ratio, frame rate, duration, codec, and audio/loudness metadata where the installed tools can inspect them. `1080x1920` is vertical 1080p, not vertical 4K; a common 9:16 4K profile is `2160x3840`. Treat `-14 LUFS` and `-18 dB` music ducking as configurable starting values, not universal compliance or quality guarantees. Review caption sync, crops/safe areas, flicker, intelligibility, music, and the entire final video by a human. No agent score or automated QA threshold may approve rights or publication.
6. **Publishing:** keep the existing YouTube-first, private-by-default, rights-cleared, human-approval workflow. Any other platform needs its own official-API/account-consent/app-review/quota/cost review. A rendering or caption change does not authorize cross-posting or public autopublishing.

Do not begin any optional installation, model download, dependency change, hosted inference, or renderer migration until the user separately approves the specific increment and its cost/rights/hardware plan.

## Testing and completion criteria

After approval and implementation:

1. Keep all existing tests passing and add tests for source/rights fail-closed behavior, channel separation, advisory-only ranking, secret redaction, and disabled-by-default publishing.
2. Use synthetic video/test data only; do not download or retain third-party footage. No real social post or public upload in automated tests.
3. Run the documented unit suite, Python compilation, JavaScript syntax check, and API smoke tests. Run a real render only if FFmpeg is installed and the test uses synthetic footage. Report explicitly if rendering was not possible.
4. Verify that `ch-1` remains U.S./`en-US`, `ch-2` remains India/`hi-IN` draft, and no existing data is overwritten. Back up before any approved migration.
5. End with an exact summary: files changed, tests actually run and results, dependencies still missing, integrations still unconfigured, cost unknowns, rights limitations, and any untested publish/render path. Do not report a feature as completed merely because a README or UI says it exists.

First complete **Stage 0 only** and wait for approval.
