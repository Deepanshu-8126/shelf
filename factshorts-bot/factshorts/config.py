"""Central configuration for FactShorts Bot.

Everything is read from environment variables (see .env.example).
Mutable runtime settings (niche, schedule time, auto mode, voice) live in SQLite
and are read/written through `factshorts.db.get_setting` / `set_setting`.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

NICHES = ["space", "psychology", "history", "science", "animals"]

VIDEO_MODES = ["facts", "story"]


@dataclass(frozen=True)
class ModeProfile:
    """Per-mode pacing. `facts` = the classic 10-15 s Short, `story` = the ~60 s story.

    A story runs up to 3 minutes inside the YouTube Shorts window, so 60 s is well
    within range and still short enough to keep retention. Numbers chosen from the
    measured narration speed of the free voices (~2.8-3.2 words/second): 165 words
    is about 55 s of speech plus pauses, and the renderer pads to the audio.
    """

    name: str
    min_duration: float
    max_duration: float
    clip_count: int
    min_words: int
    max_words: int
    target_words: int
    words_per_line: int
    chars_per_line: int
    seconds_per_clip: float


FACTS_PROFILE = ModeProfile(
    name="facts", min_duration=9.5, max_duration=14.5, clip_count=4,
    min_words=26, max_words=46, target_words=36,
    words_per_line=3, chars_per_line=20, seconds_per_clip=3.8,
)
STORY_PROFILE = ModeProfile(
    name="story", min_duration=45.0, max_duration=68.0, clip_count=10,
    min_words=130, max_words=200, target_words=165,
    words_per_line=4, chars_per_line=24, seconds_per_clip=6.5,
)

MODE_PROFILES = {"facts": FACTS_PROFILE, "story": STORY_PROFILE}


def _s(name: str, default: str = "") -> str:
    v = os.getenv(name)
    if v is None:
        return default
    s = str(v).strip()
    if not s or s.startswith("#"):
        return default
    if " #" in s:
        s = s.split(" #", 1)[0].strip()
    return s if s else default


def _i(name: str, default: int) -> int:
    try:
        return int(_s(name, str(default)))
    except ValueError:
        return default


def _f(name: str, default: float) -> float:
    try:
        return float(_s(name, str(default)))
    except ValueError:
        return default


def _b(name: str, default: bool = False) -> bool:
    return _s(name, "1" if default else "0").lower() in {"1", "true", "yes", "on", "y"}


def _env_set(name: str) -> bool:
    """True when the user explicitly set this env var (so a mode profile must not win)."""
    v = os.getenv(name)
    return v is not None and str(v).strip() != ""


def _ids(name: str) -> list[int]:
    out: list[int] = []
    for part in _s(name).replace(";", ",").split(","):
        part = part.strip()
        if part.isdigit():
            out.append(int(part))
    return out


class Config:
    """Immutable-ish snapshot of the environment configuration."""

    def __init__(self) -> None:
        # ---------- paths ----------
        self.base_dir: Path = BASE_DIR
        self.data_dir: Path = Path(_s("DATA_DIR", str(BASE_DIR / "data")))
        self.cache_dir: Path = Path(_s("CACHE_DIR", str(BASE_DIR / "cache")))
        self.output_dir: Path = Path(_s("OUTPUT_DIR", str(BASE_DIR / "output")))
        self.log_dir: Path = Path(_s("LOG_DIR", str(BASE_DIR / "logs")))
        self.music_dir: Path = Path(_s("MUSIC_DIR", str(BASE_DIR / "assets" / "music")))
        self.fonts_dir: Path = Path(_s("FONTS_DIR", str(BASE_DIR / "assets" / "fonts")))
        self.assets_dir: Path = BASE_DIR / "assets"
        self.db_path: Path = Path(_s("DB_PATH", str(self.data_dir / "factshorts.db")))
        self.credentials_dir: Path = Path(_s("CREDENTIALS_DIR", str(BASE_DIR / "credentials")))

        # ---------- telegram ----------
        self.telegram_token: str = _s("TELEGRAM_BOT_TOKEN")
        self.telegram_allowed_user_ids: list[int] = _ids("TELEGRAM_ALLOWED_USER_IDS")
        self.telegram_chat_id: int = _i("TELEGRAM_CHAT_ID", 0)

        # ---------- llm ----------
        self.gemini_api_key: str = _s("GEMINI_API_KEY")
        self.gemini_model: str = _s("GEMINI_MODEL", "gemini-3.8-flash")
        self.groq_api_key: str = _s("GROQ_API_KEY")
        self.groq_model: str = _s("GROQ_MODEL", "llama-3.3-70b-versatile")
        self.llm_provider: str = _s("LLM_PROVIDER", "auto").lower()  # auto|gemini|groq|offline
        self.llm_timeout: int = _i("LLM_TIMEOUT", 60)

        # ---------- ai video generation & gpu worker (Wan 2.2 / LTX-2.3 / Z-Image) ----------
        self.gpu_worker_url: str = _s("GPU_WORKER_URL", _s("KAGGLE_WORKER_URL", ""))
        self.video_gen_model: str = _s("VIDEO_GEN_MODEL", "wan-2.2").lower()  # wan-2.2 | ltx-2.3

        # ---------- stock footage ----------
        self.pexels_api_key: str = _s("PEXELS_API_KEY")
        self.pixabay_api_key: str = _s("PIXABAY_API_KEY")
        self.footage_providers: list[str] = [
            p.strip().lower()
            for p in _s("FOOTAGE_PROVIDERS", "pexels,pixabay,nasa,wikimedia,local").split(",")
            if p.strip()
        ]
        self.clip_min_duration: float = _f("CLIP_MIN_DURATION", 3.0)
        self.clip_min_short_side: int = _i("CLIP_MIN_SHORT_SIDE", 640)
        # Long "produced" videos (NASA briefings, Commons documentaries) are full of title
        # cards, burned-in captions and interviews, which look amateurish in a Short. Raw
        # B-roll is short, so we cap source length for the archival providers (0 = no cap).
        self.clip_max_source_duration: float = _f("CLIP_MAX_SOURCE_DURATION", 45.0)
        self.duration_capped_sources: set[str] = {"nasa", "wikimedia"}
        self.clip_max_height: int = _i("CLIP_MAX_HEIGHT", 1920)  # avoid downloading 4K
        self.clip_download_timeout: int = _i("CLIP_DOWNLOAD_TIMEOUT", 120)

        # ---------- video mode ----------
        # facts = 10-15 s one-fact Short | story = ~60 s story Short (Shorts allow 3 min)
        self.video_mode: str = _s("VIDEO_MODE", "facts").lower()
        self.story_target_seconds: float = _f("STORY_TARGET_SECONDS", 60.0)
        self.story_target_words: int = _i("STORY_TARGET_WORDS", STORY_PROFILE.target_words)
        self.story_min_words: int = _i("STORY_MIN_WORDS", STORY_PROFILE.min_words)
        self.story_max_words: int = _i("STORY_MAX_WORDS", STORY_PROFILE.max_words)
        self.story_min_duration: float = _f("STORY_MIN_DURATION", STORY_PROFILE.min_duration)
        self.story_max_duration: float = _f("STORY_MAX_DURATION", STORY_PROFILE.max_duration)
        self.story_clip_count: int = _i("STORY_CLIP_COUNT", STORY_PROFILE.clip_count)
        self.story_seconds_per_clip: float = _f("STORY_SECONDS_PER_CLIP", STORY_PROFILE.seconds_per_clip)
        # narration that overshoots by this much is re-voiced faster before the script is cut
        self.story_speed_step: float = _f("STORY_SPEED_STEP", 1.12)
        self.story_max_speed: float = _f("STORY_MAX_SPEED", 1.35)

        # ---------- video ----------
        self.width: int = _i("VIDEO_WIDTH", 1080)
        self.height: int = _i("VIDEO_HEIGHT", 1920)
        self.fps: int = _i("VIDEO_FPS", 30)
        self.max_duration: float = _f("VIDEO_MAX_DURATION", 14.5)
        self.min_duration: float = _f("VIDEO_MIN_DURATION", 9.5)
        self.clip_count: int = _i("VIDEO_CLIP_COUNT", 4)
        self.transition: str = _s("VIDEO_TRANSITION", "fade").lower()  # fade|cut
        self.transition_duration: float = _f("VIDEO_TRANSITION_DURATION", 0.28)
        self.zoom_amount: float = _f("VIDEO_ZOOM", 0.10)
        self.crf: int = _i("VIDEO_CRF", 20)
        # x264 memory scales with thread count; on a 1-2 GB host cap it (0 = ffmpeg default)
        self.video_threads: int = _i("VIDEO_THREADS", 0)
        self.preset: str = _s("VIDEO_PRESET", "medium")

        # ---------- voice ----------
        # VOICE_PROVIDER: auto (elevenlabs when a key exists, else edge) | edge | elevenlabs
        self.voice_provider: str = _s("VOICE_PROVIDER", "auto").lower()
        self.voice: str = _s("VOICE", "")  # empty = rotate per niche (edge voice name)
        self.voice_rate: str = _s("VOICE_RATE", "+10%")
        self.voice_volume: str = _s("VOICE_VOLUME", "+0%")

        # ---------- free local TTS (Kokoro / Piper - no keys, no billing) ----------
        # VOICE_PROVIDER=kokoro|piper|local|auto|edge|elevenlabs|espeak
        self.tts_model_dir: Path = Path(_s("TTS_MODEL_DIR", str(self.cache_dir / "tts")))
        self.tts_sample_rate: int = _i("TTS_SAMPLE_RATE", 0)  # 0 = keep the engine's rate
        self.tts_sentence_pause: float = _f("TTS_SENTENCE_PAUSE", 0.24)
        self.tts_lead_in: float = _f("TTS_LEAD_IN", 0.25)
        self.tts_tail: float = _f("TTS_TAIL", 0.45)
        self.piper_voice: str = _s("PIPER_VOICE", "")  # empty = en_US-lessac-medium
        # run the engine in a child process (recommended: onnxruntime keeps ~1 GB for Kokoro)
        self.tts_isolate: bool = _b("TTS_ISOLATE", True)
        self.kokoro_speed: float = _f("KOKORO_SPEED", 1.05)
        self.voice_mp3_quality: int = _i("VOICE_MP3_QUALITY", 4)  # lame -q:a
        self.tts_kokoro_model_url: str = _s("TTS_KOKORO_MODEL_URL", "")  # optional mirror
        self.tts_piper_base_url: str = _s("TTS_PIPER_BASE_URL", "")  # optional mirror

        # ---------- ElevenLabs (optional, paid for commercial use) ----------
        self.elevenlabs_api_key: str = _s("ELEVENLABS_API_KEY")
        self.elevenlabs_voice_id: str = _s("ELEVENLABS_VOICE_ID", "")
        self.elevenlabs_model: str = _s("ELEVENLABS_MODEL", "eleven_multilingual_v2")
        self.elevenlabs_output_format: str = _s("ELEVENLABS_OUTPUT_FORMAT", "mp3_44100_128")
        self.elevenlabs_stability: float = _f("ELEVENLABS_STABILITY", 0.45)
        self.elevenlabs_similarity: float = _f("ELEVENLABS_SIMILARITY", 0.80)
        self.elevenlabs_style: float = _f("ELEVENLABS_STYLE", 0.10)
        self.elevenlabs_char_limit: int = _i("ELEVENLABS_CHAR_LIMIT", 10000)  # free tier = 10k/month

        # ---------- captions ----------
        # auto (default) = provider timings, else faster-whisper, else the built-in estimator
        # whisper = force faster-whisper | edge/provider = never run whisper | estimate
        self.caption_source: str = _s("CAPTION_SOURCE", "auto").lower()
        self.whisper_model: str = _s("WHISPER_MODEL", "base.en")
        self.whisper_device: str = _s("WHISPER_DEVICE", "cpu")
        self.whisper_compute_type: str = _s("WHISPER_COMPUTE_TYPE", "int8")
        # keep the model resident between renders (faster, but ~0.5 GB stays in RAM)
        self.keep_whisper_loaded: bool = _b("KEEP_WHISPER_LOADED", False)
        self.caption_font: str = _s("CAPTION_FONT", "Montserrat ExtraBold")
        self.caption_font_size: int = _i("CAPTION_FONT_SIZE", 92)
        self.caption_highlight: str = _s("CAPTION_HIGHLIGHT", "&H0000E5FF")  # ASS BGR
        self.caption_words_per_line: int = _i("CAPTION_WORDS_PER_LINE", 3)
        self.caption_chars_per_line: int = _i("CAPTION_CHARS_PER_LINE", 20)
        self.caption_style: str = _s("CAPTION_STYLE", "hormozi").lower()
        self.hook_banner: bool = _b("HOOK_BANNER", True)
        self.hook_v2: bool = _b("HOOK_V2", True)
        self.animate_punch_words: bool = _b("ANIMATE_PUNCH_WORDS", True)

        # ---------- music ----------
        self.music_enabled: bool = _b("MUSIC_ENABLED", True)
        self.music_volume: float = _f("MUSIC_VOLUME", 0.10)

        # ---------- youtube ----------
        self.yt_client_secrets: Path = Path(
            _s("YOUTUBE_CLIENT_SECRETS", str(self.credentials_dir / "client_secret.json"))
        )
        self.yt_token_file: Path = Path(
            _s("YOUTUBE_TOKEN_FILE", str(self.credentials_dir / "token.json"))
        )
        self.yt_privacy: str = _s("YOUTUBE_PRIVACY_STATUS", "public")  # public|unlisted|private
        self.yt_category_id: str = _s("YOUTUBE_CATEGORY_ID", "27")  # 27 = Education
        self.yt_synthetic_disclosure: bool = _b("YOUTUBE_SYNTHETIC_DISCLOSURE", True)
        self.yt_made_for_kids: bool = _b("YOUTUBE_MADE_FOR_KIDS", False)
        self.yt_max_uploads_per_day: int = _i("MAX_UPLOADS_PER_DAY", 5)
        self.yt_upload_retries: int = _i("YOUTUBE_UPLOAD_RETRIES", 3)

        # ---------- trends / sources ----------
        self.use_trends: bool = _b("USE_TRENDS", True)
        self.trends_geo: str = _s("TRENDS_GEO", "IN")
        self.trend_sources: list[str] = [
            t.strip().lower() for t in _s("TREND_SOURCES", "google,onthisday,mostread,search,random").split(",") if t.strip()
        ]
        self.cite_source: bool = _b("CITE_SOURCE", True)

        # ---------- script tone ----------
        # friendly (default, "talking to a friend") | documentary | punchy
        self.script_style: str = _s("SCRIPT_STYLE", "friendly").lower()
        # none (no call to action at all) | soft | follow
        self.cta_style: str = _s("CTA_STYLE", "soft").lower()

        # ---------- platforms ----------
        self.platforms: list[str] = [
            p.strip().lower() for p in _s("PLATFORMS", "youtube").split(",") if p.strip()
        ]

        # ---------- Instagram (Reels) ----------
        self.ig_user_id: str = _s("IG_USER_ID")
        self.ig_access_token: str = _s("IG_ACCESS_TOKEN")
        self.ig_upload_mode: str = _s("IG_UPLOAD_MODE", "resumable").lower()  # resumable | url
        self.ig_public_base_url: str = _s("IG_PUBLIC_BASE_URL", "")  # for upload_mode=url
        self.ig_share_to_feed: bool = _b("IG_SHARE_TO_FEED", True)
        self.ig_graph_version: str = _s("IG_GRAPH_VERSION", "v21.0")
        # graph.facebook.com (Facebook Login for Business, supports resumable upload)
        # or graph.instagram.com (Business Login for Instagram, needs a public video url)
        self.ig_graph_host: str = _s("IG_GRAPH_HOST", "graph.facebook.com")
        self.ig_hashtag_limit: int = _i("IG_HASHTAG_LIMIT", 8)

        # ---------- scheduling ----------
        self.timezone: str = _s("TIMEZONE", "Asia/Kolkata")
        self.schedule_time: str = _s("SCHEDULE_TIME", "19:30")  # kept for backwards compat
        # morning + night by default - two Shorts a day, the second one catches another audience
        self.schedule_times: list[str] = [
            t.strip() for t in _s("SCHEDULE_TIMES", _s("SCHEDULE_TIME", "08:30,19:30")).split(",") if t.strip()
        ]
        self.niche_rotate: bool = _b("NICHE_ROTATE", False)  # true = cycle niches across the day
        self.auto_mode: bool = _b("AUTO_MODE", False)
        self.auto_publish: bool = _b("AUTO_PUBLISH", False)  # schedule upload via publishAt

        # ---------- misc ----------
        self.niche: str = _s("DEFAULT_NICHE", "space").lower()
        self.dry_run: bool = _b("DRY_RUN", False)
        self.keep_cache: bool = _b("KEEP_CACHE", True)
        self.log_level: str = _s("LOG_LEVEL", "INFO").upper()
        self.test_mode: bool = _b("TEST_OFFLINE_MODE", False)

    # ---------------------------------------------------------------- helpers
    def mode(self) -> str:
        """Active video mode. A SQLite setting wins over .env, so /mode works live."""
        try:
            from . import db

            stored = (db.get_setting("video_mode") or "").lower()
        except Exception:  # noqa: BLE001 - e.g. before init_db()
            stored = ""
        mode = stored or self.video_mode or "facts"
        return mode if mode in MODE_PROFILES else "facts"

    def profile(self) -> ModeProfile:
        """Pacing numbers for the active mode (VIDEO_MODE=facts|story)."""
        base = MODE_PROFILES[self.mode()]
        if base.name != "story":
            if _env_set("CAPTION_WORDS_PER_LINE") or _env_set("CAPTION_CHARS_PER_LINE"):
                return ModeProfile(
                    name=base.name, min_duration=base.min_duration, max_duration=base.max_duration,
                    clip_count=base.clip_count, min_words=base.min_words, max_words=base.max_words,
                    target_words=base.target_words,
                    words_per_line=self.caption_words_per_line, chars_per_line=self.caption_chars_per_line,
                    seconds_per_clip=base.seconds_per_clip,
                )
            return base
        return ModeProfile(
            name="story",
            min_duration=self.story_min_duration,
            max_duration=self.story_max_duration,
            clip_count=self.story_clip_count,
            min_words=self.story_min_words,
            max_words=self.story_max_words,
            target_words=self.story_target_words,
            words_per_line=base.words_per_line if not _env_set("CAPTION_WORDS_PER_LINE") else self.caption_words_per_line,
            chars_per_line=base.chars_per_line if not _env_set("CAPTION_CHARS_PER_LINE") else self.caption_chars_per_line,
            seconds_per_clip=self.story_seconds_per_clip,
        )

    def min_clip_seconds(self) -> float:
        """Shortest usable source clip for the active mode.

        Story shots run ~6.5 s, and looping a 3 s clip that many times looks broken,
        so story mode asks providers for longer footage.
        """
        profile = self.profile()
        if profile.name == "story":
            return max(self.clip_min_duration, round(profile.seconds_per_clip * 0.75, 2))
        return self.clip_min_duration

    @property
    def caption_font_path(self) -> Path:
        return self.fonts_dir / "Montserrat-ExtraBold.ttf"

    def ensure_dirs(self) -> None:
        for d in (
            self.data_dir,
            self.cache_dir,
            self.output_dir,
            self.log_dir,
            self.music_dir,
            self.fonts_dir,
            self.credentials_dir,
            self.tts_model_dir,
            self.cache_dir / "clips",
            self.cache_dir / "tmp",
        ):
            Path(d).mkdir(parents=True, exist_ok=True)

    def describe(self) -> str:
        """Human readable summary used by `python main.py --check` and /status."""
        llm = "gemini" if self.gemini_api_key else ("groq" if self.groq_api_key else "offline-bank")
        prov = [p for p in self.footage_providers if p != "local"]
        available = []
        if self.pexels_api_key:
            available.append("pexels")
        if self.pixabay_api_key:
            available.append("pixabay")
        if "nasa" in self.footage_providers:
            available.append("nasa(no key)")
        available.append("wikimedia(no key)")
        lines = [
            f"LLM provider        : {llm} ({self.llm_provider})",
            f"Script style        : {self.script_style} / CTA={self.cta_style}",
            f"Pexels key          : {'set' if self.pexels_api_key else 'MISSING'}",
            f"Pixabay key         : {'set' if self.pixabay_api_key else 'MISSING'}",
            f"Footage providers   : {available} (order: {prov + ['local']})",
            f"Telegram token      : {'set' if self.telegram_token else 'MISSING'}",
            f"Allowed TG user ids : {self.telegram_allowed_user_ids or 'MISSING'}",
            f"YouTube secrets     : {self.yt_client_secrets} "
            f"({'found' if self.yt_client_secrets.exists() else 'not found'})",
            f"YouTube token       : {self.yt_token_file} "
            f"({'found' if self.yt_token_file.exists() else 'not found'})",
            f"Niche / voice       : {self.niche} / {self.voice or 'auto-rotate'}",
            f"Voice provider      : {self.voice_provider}"
            + (" (ElevenLabs key set)" if self.elevenlabs_api_key else " -> free local/edge voice"),
            f"Video mode          : {self.mode()} "
            + (f"({self.story_target_words} words ~ {self.story_target_seconds:.0f}s, up to "
               f"{self.story_max_duration:.0f}s, {self.story_clip_count} clips)"
               if self.mode() == "story" else f"({FACTS_PROFILE.min_words}-{FACTS_PROFILE.max_words} words, "
                                              f"up to {FACTS_PROFILE.max_duration:.0f}s)"),
            f"Trends              : {'on' if self.use_trends else 'off'} ({self.trends_geo}) sources={self.trend_sources}",
            f"Platforms           : {self.platforms}"
            + (f" | IG user id {'set' if self.ig_user_id else 'MISSING'}" if "instagram" in self.platforms else ""),
            f"Schedule            : {', '.join(self.schedule_times)} ({self.timezone}), auto={self.auto_mode}",
            f"Output              : {self.output_dir}",
        ]
        return "\n".join(lines)


_config: Config | None = None


def get_config(refresh: bool = False) -> Config:
    global _config
    if _config is None or refresh:
        _config = Config()
        _config.ensure_dirs()
    return _config
