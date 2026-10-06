# CreatorOps — Research-first YouTube Agent Studio

CreatorOps is a local-first operations MVP for an original-content YouTube pilot. It combines a public-signal niche scout, a practical growth-plan/calendar generator, a documentary-style research brief and script package, a one-command storyboard preview workflow, owner-only analytics, and hard human-review gates. A separate **GTA VI Clips Lab** targets an India-facing Hindi/Hinglish gaming channel without changing the existing U.S.-audience strategy.

**This is software, not an income promise.** A U.S. region/language filter does not guarantee U.S. viewers; an India/hi-IN channel setting does not guarantee Indian viewers or age reach. Neither proves YPP eligibility, RPM, watch time, growth, or revenue. Public competitor metadata cannot reveal private retention or actual competitor earnings.

The documentary/workflow repository audit is in [`REPOSITORY_REVIEW.md`](REPOSITORY_REVIEW.md); the original GTA clipping references are assessed in [`GTA6_CLIP_REPO_REVIEW.md`](GTA6_CLIP_REPO_REVIEW.md). The nine-repository architecture proposal is audited in [`NINE_REPO_UPGRADE_AUDIT.md`](NINE_REPO_UPGRADE_AUDIT.md), and the optional 4K/captions/editing/audio stack is assessed in [`VIDEO_QUALITY_STACK_AUDIT.md`](VIDEO_QUALITY_STACK_AUDIT.md). Both are covered by the staged, approval-gated [`ANTIGRAVITY_SAFE_UPGRADE_PROMPT.md`](ANTIGRAVITY_SAFE_UPGRADE_PROMPT.md). No candidate repository or model from either proposal was installed, executed, copied, or downloaded into this project.

## What works

- Three configurable YouTube channel slots; each channel needs its own account authorization and eligibility.
- Market Scout demo mode, clearly labelled illustrative.
- Optional live YouTube Data API scan with up to 25 matching videos per publication cohort: 0–30, 31–90, and 91–180 days. It saves video URLs, publish dates, views, visible subscriber counts, cohort summaries, sample methodology and limitations.
- Evidence signals include sample size, sampled creator diversity, heuristic 3× subscriber outliers, and whether outliers appear across multiple sampled cohorts. These are screening signals—not a market census or a six-month forecast.
- A 14-day growth playbook with a provisional niche recommendation, four documentary-style idea slots, content pillars, experiments, and a review loop. Rebuilding the plan incorporates available owner-only analytics snapshots; it does not self-modify goals or publish automatically.
- Shorts, Long-form and Documentary content packages. Packages include script, scene plan, timeline, SRT captions, research brief, editor-supplied source log, unverified claim ledger, rights checklist, metadata and platform copy variants.
- One-command **Build package + render preview**. It creates the package and a 9:16 Shorts or 16:9 long-form text-and-shape storyboard preview. Voiceover is opt-in in the form and uses whichever configured provider is enabled. The preview is not a finished documentary or publish-ready video.
- Optional voice providers: ElevenLabs, or Edge TTS when installed/configured. Edge TTS sends narration text to a network service; review provider terms/privacy and availability. FFmpeg can mux audio when available.
- Editable copy-only distribution variants for TikTok, Telegram, Bluesky, Mastodon, Discord, and Meta. **Only YouTube has an upload adapter today.** Other channels are not posted to; each requires its own official API integration, credentials, permissions and review.
- Separate **GTA VI Clips Lab** for the India/hi-IN audience concept (the unused channel slot 02 is prefilled as a draft; slot 01 remains U.S./en-US). It scans only operator-provided local files in `data/gaming_sources/` and can suggest abrupt frame-change windows for manual review; this is not semantic kill/explosion detection. It trims a manually selected 5–60 second segment to a 1080×1920 vertical MP4 and writes a manually supplied Hinglish SRT with rough evenly divided timings. An optional kinetic mode creates a word-highlight ASS subtitle and burns it into the MP4 using FFmpeg's ASS/libass filter; the SRT sidecar remains available. This is approximate timing—not ASR or forced alignment—and the complete burn-in render has not been tested in this workspace because FFmpeg is unavailable. Hindi voiceover can optionally use the configured network provider. No remote video download, live streamer capture, chat scraping, face tracking, game-event detection, or unattended publishing is implemented.
- GTA VI publication has an extra case-specific written Rockstar/Take-Two commercial-permission gate, separate from rights to a streamer's recording. Rockstar's general fan-video policy describes use as non-commercial; no monetized upload is authorized by this local workflow. Human confirmation of original commentary, all audio/music rights and no leaked/prohibited material is also required. See [`GTA6_CLIP_REPO_REVIEW.md`](GTA6_CLIP_REPO_REVIEW.md).
- Explicit rights attestation, human fact-check note, final-render review, approval, scheduling, private test upload and publication blockers.
- Optional daily worker: at most one scan-led draft per configured channel slot per day when enabled. Draft generation does not automatically approve or publish.
- Optional official YouTube API OAuth publisher and YouTube Analytics API snapshots.

## Research limitations and scoring

Each live niche is sampled using YouTube Data API search with U.S.-region and English relevance filters. Results are capped at 25 videos per publication cohort and are not random or exhaustive. Public `viewCount` is lifetime views at scan time; `views/day` divides lifetime views by video age and is **not** historical daily velocity. Visible subscriber counts are current counts and may be hidden. A video at least 3× its channel's current visible subscribers is a heuristic outlier, not a universal breakout definition.

The score weights are: recent-cohort demand 25%, outlier signal 25%, inverse sampled creator diversity 15%, a hand-set qualitative commercial-intent prior 15%, production ease 10%, and cohort repeatability 10%. Commercial intent is not advertiser bids, CPM, RPM or income. Repeated scans over time and original pilot uploads are needed to make a better decision.

## Run the dashboard

Requires Python 3.10+ for the standard-library dashboard and demo mode.

```bash
cd youtube_agent_studio
python server.py
```

Open `http://localhost:8787`. In the Arena workspace preview the server binds to `0.0.0.0`; the preview is suitable for demonstrating the UI, **not for storing/authorizing production credentials**. This MVP has no user-login layer; do not expose it on a public internet server as-is.

Optional rendering, speech and publishing dependencies:

```bash
python -m pip install -r requirements.txt
```

## Configure live research and drafting

```bash
cp .env.example .env
```

Edit `.env` locally. Never paste secrets into chat, screenshots, GitHub, or a public preview.

- `YOUTUBE_DATA_API_KEY`: YouTube Data API v3 key for public market metadata. Each scan makes multiple search requests; watch your project's API quota.
- `GEMINI_API_KEY`: optional Gemini key for original package drafting.
- Or set `LLM_BASE_URL`, `LLM_API_KEY`, and `LLM_MODEL` for an OpenAI-compatible endpoint. A local endpoint may be used if available; cloud endpoints receive prompt content.
- `ELEVENLABS_API_KEY` and `ELEVENLABS_VOICE_ID`: optional paid/quota-limited narration provider.
- Or configure `EDGE_TTS_VOICE` after installing dependencies. This is a network speech service, not offline/local TTS.
- `FFMPEG_BINARY`: optional ffmpeg path override; `imageio-ffmpeg` is also used as a fallback when installed.

Restart the server after editing `.env`; the dashboard reports readiness without revealing key values.

## Connect an owned YouTube channel

1. In Google Cloud, create a project and enable YouTube Data API v3 and YouTube Analytics API.
2. Configure an OAuth consent screen and create an OAuth **Desktop app** client.
3. Save the downloaded JSON as `secrets/client_secret.json` (`secrets/` is git-ignored).
4. Install optional dependencies with `pip install -r requirements.txt`.
5. Authorize each channel slot separately:

```bash
python -m agent.auth_youtube --channel ch-1
python -m agent.auth_youtube --channel ch-2
python -m agent.auth_youtube --channel ch-3
```

Follow Google's consent flow locally. Tokens are saved in `secrets/tokens/` and never returned by the API. You must own or be authorized to manage each channel.

## Suggested workflow

1. **Market Scout → Run live scan.** Without a key, the demo candidates are illustrative, not evidence.
2. **Growth Playbook → Build 14-day plan.** Treat the recommended niche as a test hypothesis. The calendar is ideas only, not scheduled uploads.
3. **Content Studio → select Documentary** for a research-first outline. Add primary-source URLs and notes. CreatorOps stores the URLs/notes but does not fetch or verify pages. If an LLM is configured, your notes are sent to that provider for drafting.
4. Inspect `research_brief.md`, `source_log.md`, `claims.json`, `script.md`, `shotlist.json`, `timeline.json`, `captions.srt` and `distribution.json`. A supplied URL does not prove it supports a claim.
5. Use **Build package + render preview**. Voice generation is unchecked by default. The preview uses original generated text/shapes—not factual documentary footage or licensed media. Replace/augment visuals with assets you own or are allowed to use.
6. Record a rights note and human fact-check note. These are human attestations, not legal certification or automatic fact-checking.
7. Review the final rendered file, add a meaningful render-QA note, and approve. The publish endpoint checks rights, fact-check, render review, audio, video file, OAuth, and environment gates. Manual upload is private by default.
8. Pull owner-only analytics after upload. Rebuild the strategy after a consistent measurement window; the app uses your own snapshots instead of generic benchmark promises.

## GTA VI Clips Lab — separate India/Hindi workflow

Channel slot `ch-2` is set to `IN` / `hi-IN` as a proposed gaming slot; `ch-1` and the U.S. strategy remain unchanged. You can edit the slot in **Channels**. It is not connected to YouTube OAuth unless you authorize it separately. The `18–35` audience is only a working persona, not guaranteed reach or an organic-video targeting control.

1. Review [`GTA6_CLIP_REPO_REVIEW.md`](GTA6_CLIP_REPO_REVIEW.md) for the eight supplied references. No third-party clipper code was integrated; several candidates have no checked license, one is AGPL-3.0-only, and the claimed costs/capabilities are not independently verified.
2. Place only an owned or explicitly licensed local video file in `data/gaming_sources/` (`.mp4`, `.mov`, `.mkv`, `.webm`, or `.m4v`, up to 2 GB). Before November 19, the tool also requires a written pre-release authorization reference; leaked footage is prohibited. The browser form lists local files; it does not accept a YouTube/Twitch/Kick URL for downloading. Do not capture or repost a third-party stream without the rights and platform review.
3. Optionally run **Suggest visual-change windows**. The local OpenCV heuristic reports abrupt frame changes from at most the first 15 minutes; it does not identify kills, explosions, chat spikes, or story relevance. Watch the footage and choose the cut manually.
4. In **GTA VI Clips**, select the India/hi-IN slot, source file, time range, Hindi/Hinglish hook, original commentary and caption lines. The clip is capped at 60 seconds in this MVP. FFmpeg renders a vertical 1080×1920 MP4 with the full frame over a blurred fill. Choose Standard SRT or optional Kinetic word-highlight captions; kinetic burn-in needs an FFmpeg build with ASS/libass. The SRT sidecar is always kept. Both use approximate timing from your own lines, not ASR/forced alignment, and must be synced/proofread.
5. Optional Hindi voiceover uses the already configured network voice provider; language support depends on the configured voice, provider terms and quota/cost. The checkbox is off by default. If the provider is not Hindi-capable, record/edit narration separately and replace the local final MP4 before review.
6. **Do not publish leaked/pre-release GTA VI footage.** Rockstar's current general fan-video policy describes permissible fan material as non-commercial and reserves takedowns. For a monetization-oriented channel, obtain case-specific written commercial permission from Take-Two/Rockstar before any public upload; a creator's permission only covers their recording, not game IP, and a source credit is not a license. The app requires a license reference and separate human confirmations, but it cannot authenticate documents or grant permission. Rockstar's policy also restricts certain spoilers, isolated cutscenes, in-game entertainment and cheating promotion; read the current [Rockstar policy](https://support.rockstargames.com/articles/7bNaeoMFTV0iUDGhStTXvz/policy-on-posting-copyrighted-rockstar-games-material).
7. Add meaningful original commentary/analysis and review the entire final clip. YouTube reused-content review is separate from copyright permission and may reject minimally changed clips even when permission exists; see [YouTube's channel monetization policies](https://support.google.com/youtube/answer/1311392?hl=en-in). No format guarantees monetization, views, or income.
8. Other platform variants are text/copy exports only. YouTube remains the only uploader; there is no cross-posting adapter for TikTok, Instagram, Telegram, or other platforms.

Official Rockstar announced the game for **November 19, 2026**. On September 30, 2026 that is 50 full days away (51 dates if counting today inclusively); release schedules can change, so check the official announcement before planning.

## Safe publishing defaults

- `DEFAULT_PRIVACY=private`.
- `AUTO_DRAFT_ENABLED=false`.
- `AUTO_PUBLISH_ENABLED=false`.
- Public uploads are forced back to private unless **both** `AUTO_PUBLISH_ENABLED=true` and `ALLOW_PUBLIC_UPLOAD=true` are set.
- Worker uploads require an approved job, cleared rights, human fact-check/approval, a non-silent render, final-render review, and channel OAuth. GTA VI clips additionally require a documented case-specific commercial Rockstar/Take-Two license reference and human confirmations for original commentary, all game/audio/music rights, and no leaked/prohibited content.
- The system does not download competitor videos, copy transcripts, automate views/likes/comments/subscriptions, or bypass platform limits.
- Before production exposure, add login/authentication, TLS, encrypted secret storage, job-level budgets, backoff/rate limits, audit logs, content deduplication and an emergency stop.

Start the scheduler only after private-upload testing and policy review:

```bash
python -m agent.worker
```

The worker can run daily scans and draft generation if configured. Uploads remain blocked unless auto-publishing is explicitly enabled and every job gate passes. Keep `ALLOW_PUBLIC_UPLOAD=false` while testing.

## API overview

- `GET /api/health` — integration readiness, no secrets.
- `GET /api/dashboard` — channels, scan, jobs, analytics and platform matrix.
- `GET /api/platforms` — honest adapter status; non-YouTube entries are export-only.
- `GET /api/strategy/latest?channel_id=ch-1` — saved playbook, if any.
- `POST /api/research/run` — market scan.
- `POST /api/strategy/build` — `{ "channel_id":"ch-1" }`.
- `POST /api/pipeline/run` — create package + preview; accepts `channel_id`, `topic`, `format`, `angle`, `research_notes`, `source_urls`, and optional `generate_voice` (may use a configured speech provider).
- `POST /api/pipeline/generate` — create package only.
- `POST /api/pipeline/from-scout` — select one original topic from the latest scan.
- `GET /api/gaming/sources` — list local video files in `data/gaming_sources/` only; no remote URL fetch.
- `POST /api/gaming/highlights` — `{ "source_file":"local.mp4" }`; returns local frame-change windows for human review, not semantic game-event detection.
- `POST /api/gaming/clips` — render an authorized local GTA VI clip package; needs channel slot `IN` / `hi-*`, local filename, 5–60 second timecodes, source-rights note, original commentary, hook and manual Hinglish caption lines. Optional `caption_style` is `static_srt` (default) or `kinetic_karaoke` (requires FFmpeg ASS/libass and burns word-highlight captions into the MP4; keeps the SRT sidecar). Timing is approximate, not ASR/alignment. Optional voiceover uses configured network TTS.
- `POST /api/jobs/<id>/render` — render/re-render a storyboard preview.
- `POST /api/jobs/<id>/rights` — `{ "status":"owned|licensed", "evidence":"..." }`; GTA VI clips must use `licensed` plus `commercial_license_reference` for written Rockstar/Take-Two permission.
- `POST /api/jobs/<id>/factcheck` — `{ "note":"...", "sources":["https://..."] }`.
- `POST /api/jobs/<id>/render-review` — human QA attestation for a final video with audio; GTA VI clips must additionally confirm original commentary, commercial rights for every audio element, and no leaked/prohibited content.
- `POST /api/jobs/<id>/approve` — human approval.
- `POST /api/jobs/<id>/schedule` — `{ "scheduled_at":"ISO-8601 timestamp" }`.
- `POST /api/jobs/<id>/publish` — manual private test upload; blocked until every gate passes.
- `POST /api/analytics/pull` — `{ "channel_id":"ch-1", "video_id":"..." }`.

## Tests

```bash
python -m unittest discover -s tests -v
```

## Architecture

```text
YouTube public metadata ──> cohort scout + evidence ledger ──> niche test hypothesis
                                                               │
Owner Analytics snapshots ──> growth playbook + 14-day calendar ┘
                                                               │
Editor notes + source links ──> LLM/template ──> script + claims + research brief
                                                               │
Original/licensed assets ──> storyboard preview ──> human QA + rights gates
                                                               │
Authorized local gameplay ──> GTA VI vertical clip + Hinglish SRT ──> commercial IP license gate
                                                               │
YouTube OAuth uploader <── scheduler <── approval
          │
Owner Analytics API ──> saved snapshots ──> next strategy baseline
```

The LLM is a planner, not a self-modifying model. Learning should update the next plan from channel-owned analytics after consistent tests; it should not silently rewrite goals or publish unreviewed claims.
