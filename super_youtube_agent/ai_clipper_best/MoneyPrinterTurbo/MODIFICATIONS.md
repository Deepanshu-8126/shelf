# Local modifications to the upstream clone

Cloned `harry0703/MoneyPrinterTurbo` v1.3.7 (`--depth 1`, 2026-10-01) and changed:

## 1. Slimmed 338 MB → 15 MB (workspace snapshot cap)
* deleted `.git` (135 MB)
* deleted 4 CJK fonts (142 MB): `STHeitiLight/Medium.ttc`, `MicrosoftYaHei{Normal,Bold}.ttc`
  — irrelevant for English/Spanish
* kept 4 of 29 BGM tracks in `resource/songs` (56 MB → 8 MB)

Full restore: `git clone --depth 1 https://github.com/harry0703/MoneyPrinterTurbo.git`

## 2. Font defaults repointed (required by #1)
`STHeitiMedium.ttc` was the hardcoded default in 5 places and would now crash.
Repointed to **`BeVietnamPro-Bold.ttf`** — a Latin font with full `á é í ó ú ñ ¿ ¡` coverage:

| File | Change |
|---|---|
| `app/models/schema.py` | `VideoParams.font_name`, `SubtitleRequest.font_name` defaults (2) |
| `app/controllers/v1/video.py:242` | API fallback font |
| `app/services/video.py:1496` | render-time fallback |
| `webui/Main.py:194` | WebUI default |
| `cli.py:577` | help text |

## 3. `config.toml` created and tuned for EN/ES shorts
From `config.example.toml`, with the `[ui]` defaults uncommented and set:

```toml
language = "en"              video_language = "en-US"
tts_server = "azure-tts-v1"  # free Edge-TTS path, no API key
voice_name = "en-US-ChristopherNeural-Male"
voice_rate = 1.08            video_aspect_pexels = "9:16"
subtitle_display_mode = "word_by_word"   # kinetic captions
subtitle_animation  = "pop_spring"
font_name = "BeVietnamPro-Bold.ttf"      font_size = 64
subtitle_position = "two_thirds_bottom"  stroke_width = 2.5
video_concat_mode = "sequential"         bgm_volume = 0.12
```
Also `[whisper] model_size`: `large-v3` → **`base`** (large-v3 on `cpu`/`int8` is
unusable for iteration; raise it once you have a GPU).

Spanish voices are selected per-task in the manifest, not here —
`es-ES-AlvaroNeural-Male`, `es-MX-JorgeNeural-Male`, plus 43 more in
`app/services/data/azure_voices.json`.

## 4. `tasks.jsonl` — generated, not hand-written
Produced by `../yt-clipper/to_mpt.py`. **All 6 tasks validate against
`app.models.schema.VideoParams`** (MPT rejects unknown fields, so this was verified,
not assumed).

## Still required before a real render
```bash
pip install -r requirements.txt        # or: uv sync
```
* an LLM key in `config.toml` (`llm_provider`, default `moonshot`) — only needed when MPT
  writes the script. Our manifests ship `video_script`, so you can skip it.
* `pexels_api_keys` — only for stock footage. Not needed with `video_source = "local"`.
* ffmpeg on PATH.
