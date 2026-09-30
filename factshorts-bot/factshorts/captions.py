"""Captions: big, bold, centred, word-by-word highlighted captions burned into the video.

Timing source (CAPTION_SOURCE):
  * "edge"    -> WordBoundary events from edge-tts (default: no extra deps, accurate to ~30 ms)
  * "whisper" -> faster-whisper word timestamps (more accurate on hard words, needs the package)

Rendering uses the libass `ass` filter, so every word style change is a cheap ASS
override tag: no per-frame PNG rendering, and it burns in fast.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence

from .config import Config, get_config
from .utils import esc_ass, fmt_ts_ass, module_logger
from .voice import WordTiming

log = module_logger("captions")

HIGHLIGHT = "&H0000E5FF"   # ASS is &HAABBGGRR -> this is orange/gold
WHITE = "&H00FFFFFF"
OUTLINE = "&H00000000"
SHADOW = "&H80000000"


@dataclass
class CaptionPage:
    words: list[str]
    start: float
    end: float
    highlight_index: int = -1  # -1 = no highlight, else word index inside `words`


# --------------------------------------------------------------------- timings
def _normalise(word: str) -> str:
    return "".join(ch for ch in word.lower() if ch.isalnum() or ch == "'")


def align_timings(words: Iterable[WordTiming], text: str) -> list[WordTiming]:
    """Match edge-tts WordBoundary events onto the source text words.

    edge-tts sometimes splits differently than a plain whitespace split
    (e.g. "12,000" or "mind-blowing"). We walk both sequences and re-attach any
    leftover text words to the nearest event, keeping the timing monotonic.
    """
    events = [w for w in words if _normalise(w.word)]
    if not events:
        return []
    text_words = [w for w in (text or "").split() if w.strip()]
    if not text_words:
        return events
    if len(text_words) == len(events):
        return [
            WordTiming(tw, e.start, e.end)
            for tw, e in zip(text_words, events)
        ]

    # merge/split alignment: greedily consume text words for each event
    out: list[WordTiming] = []
    ti = 0
    for idx, ev in enumerate(events):
        norm_ev = _normalise(ev.word)
        consumed: list[str] = []
        while ti < len(text_words) and sum(len(_normalise(c)) for c in consumed) < len(norm_ev):
            consumed.append(text_words[ti])
            ti += 1
        if not consumed:
            consumed = [ev.word]
        # distribute the event window across the consumed words
        total_chars = max(1, sum(len(_normalise(c)) for c in consumed))
        t = ev.start
        span = max(0.06, ev.end - ev.start)
        for c in consumed:
            share = span * (len(_normalise(c)) / total_chars)
            out.append(WordTiming(c, t, t + share))
            t += share
    # any trailing text words: append to the last event's end
    if ti < len(text_words) and out:
        end = out[-1].end
        for c in text_words[ti:]:
            out.append(WordTiming(c, end, end + 0.18))
            end += 0.18
    return out


def timings_from_whisper(
    audio_path: str | Path, cfg: Config | None = None, script_text: str = ""
) -> list[WordTiming]:
    """Word-level timestamps via faster-whisper (optional, but default for local voices).

    Whisper transcribes the narration we just generated and its word boundaries are
    mapped back onto the script text, so captions show the *script* spelling with
    real timings (see ``factshorts.align.snap_to_script``).
    """
    from . import align

    cfg = cfg or get_config()
    return [WordTiming(*w) for w in align.whisper_words(audio_path, script_text, cfg)]


# ------------------------------------------------------------------- grouping
def _group_words(words: Sequence[WordTiming], words_per_page: int, chars_per_line: int) -> list[list[WordTiming]]:
    groups: list[list[WordTiming]] = []
    idx = 0
    while idx < len(words):
        chunk: list[WordTiming] = []
        chars = 0
        while idx < len(words) and len(chunk) < max(1, words_per_page):
            w = words[idx]
            added = len(w.word) + (1 if chunk else 0)
            if chunk and chars + added > chars_per_line:
                break
            chunk.append(w)
            chars += added
            idx += 1
        if not chunk:  # single very long word
            chunk = [words[idx]]
            idx += 1
        groups.append(chunk)
    return groups


def build_pages(
    words: Sequence[WordTiming],
    words_per_page: int = 3,
    chars_per_line: int = 20,
    duration: float = 0.0,
) -> list[CaptionPage]:
    """Group words into 2-3 word "pages"; each page is emitted once per word so the
    active word can be highlighted.

    Guarantee: page N never overlaps page N+1 (exactly one caption block on screen at
    any time). Fast function words ("in", "the", "a") used to create overlaps when a
    page was padded, which showed the same line twice - that is fixed by deriving each
    page's end from the *next* page's start.
    """
    words = [w for w in words if w.word.strip()]
    if not words:
        return []
    if duration <= 0:
        duration = words[-1].end

    groups = _group_words(words, words_per_page, chars_per_line)
    # page boundaries: a page stays on screen until the next page's first word starts
    boundaries: list[tuple[float, float]] = []
    for i, chunk in enumerate(groups):
        start = max(0.0, chunk[0].start)
        if i + 1 < len(groups):
            end = max(start + 0.05, groups[i + 1][0].start)
        else:
            end = max(start + 0.05, chunk[-1].end, min(duration, chunk[-1].end + 0.35))
        boundaries.append((start, end))

    pages: list[CaptionPage] = []
    for i, chunk in enumerate(groups):
        page_start, page_end = boundaries[i]
        page_words = [c.word for c in chunk]
        for j, w in enumerate(chunk):
            w_start = min(max(page_start, w.start), page_end - 0.05)
            if j + 1 < len(chunk):
                w_end = min(chunk[j + 1].start, page_end)
            else:
                w_end = page_end
            if w_end - w_start < 0.04:  # skip blocks that would be invisible anyway
                continue
            pages.append(CaptionPage(page_words, w_start, w_end, highlight_index=j))
    return pages


PUNCH_WORDS = {
    "stop", "explodes", "explode", "exploded", "exploding", "secret", "secrets",
    "never", "killer", "massive", "dangerous", "danger", "frozen", "freeze",
    "monster", "shocking", "impossible", "insane", "disaster", "extreme",
    "deadly", "warning", "dead", "black", "hole", "holes", "destroy", "gravity", "giant",
    "bizarre", "terrifying", "huge", "worst", "unbelievable", "truth", "die", "killed",
}

CAPTION_STYLES: dict[str, dict[str, Any]] = {
    "hormozi": {
        "primary": WHITE,
        "highlight": "&H0000FFFF",  # Electric Bold Yellow
        "outline": "&H00000000",
        "shadow": "&H80000000",
        "outline_size": 9,
        "shadow_size": 4,
        "spacing": 1.5,
        "anim": r"{\c&H0000FFFF\t(0,60,\fscx130\fscy130)\t(60,140,\fscx110\fscy110)}",
        "uppercase": False,
    },
    "mrbeast": {
        "primary": WHITE,
        "highlight": "&H0014F000",  # Toxic Lime Green
        "outline": "&H00000000",
        "shadow": "&H90000000",
        "outline_size": 10,
        "shadow_size": 5,
        "spacing": 1.2,
        "anim": r"{\c&H0014F000\t(0,60,\frz-3\fscx126\fscy126)\t(60,130,\frz1\fscx108\fscy108)}",
        "uppercase": False,
    },
    "karaoke": {
        "primary": "&H80FFFFFF",   # Translucent white base
        "highlight": "&H0000E5FF",  # Bright orange/gold
        "outline": "&H00000000",
        "shadow": "&H60000000",
        "outline_size": 7,
        "shadow_size": 3,
        "spacing": 1.5,
        "anim": r"{\c&H0000E5FF\t(0,90,\fscx115\fscy115)\t(90,160,\fscx104\fscy104)}",
        "uppercase": False,
    },
    "neon_glow": {
        "primary": "&H00FFFF00",   # Cyan
        "highlight": "&H00D200FF",  # Magenta glow
        "outline": "&H00000000",
        "shadow": "&H70D200FF",
        "outline_size": 8,
        "shadow_size": 4,
        "spacing": 2.0,
        "anim": r"{\c&H00D200FF\t(0,80,\fscx120\fscy120\blur4)\t(80,160,\fscx106\fscy106\blur1)}",
        "uppercase": True,
    },
    "cinematic": {
        "primary": "&H00E8E8E8",   # Soft ivory white
        "highlight": "&H0058C8F0",  # Warm golden amber
        "outline": "&H00151515",
        "shadow": "&HA0000000",
        "outline_size": 4,
        "shadow_size": 2,
        "spacing": 3.0,
        "anim": r"{\c&H0058C8F0\t(0,100,\fscx112\fscy112)\t(100,200,\fscx104\fscy104)}",
        "uppercase": False,
    },
    "pop_bounce": {
        "primary": WHITE,
        "highlight": "&H0000E5FF",  # Gold
        "outline": "&H00000000",
        "shadow": "&H80000000",
        "outline_size": 7,
        "shadow_size": 3,
        "spacing": 1.5,
        "anim": r"{\c&H0000E5FF\t(0,70,\fscx125\fscy125)\t(70,140,\fscx96\fscy96)\t(140,200,\fscx106\fscy106)}",
        "uppercase": False,
    },
}


# ---------------------------------------------------------------------- ASS out
def build_ass(
    pages: Sequence[CaptionPage],
    total_duration: float,
    cfg: Config | None = None,
    hook_text: str = "",
) -> str:
    cfg = cfg or get_config()
    width, height = cfg.width, cfg.height
    font_size = cfg.caption_font_size
    margin_v = int(height * 0.22)  # keep captions clear of the UI-safe zone

    style_key = getattr(cfg, "caption_style", "hormozi").lower()
    style_spec = CAPTION_STYLES.get(style_key, CAPTION_STYLES["hormozi"])

    primary_color = style_spec["primary"]
    highlight = cfg.caption_highlight if cfg.caption_highlight != HIGHLIGHT else style_spec["highlight"]
    outline_color = style_spec["outline"]
    shadow_color = style_spec["shadow"]
    outline_size = style_spec["outline_size"]
    shadow_size = style_spec["shadow_size"]
    spacing = style_spec["spacing"]
    uppercase_mode = style_spec["uppercase"]

    header = f"""[Script Info]
; FactShorts Bot - generated pro captions (style: {style_key})
ScriptType: v4.00+
PlayResX: {width}
PlayResY: {height}
WrapStyle: 2
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.709

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Caption,{cfg.caption_font},{font_size},{primary_color},{highlight},{outline_color},{shadow_color},-1,0,0,0,100,100,{spacing},0,1,{outline_size},{shadow_size},5,60,60,{margin_v},1
Style: Hook,{cfg.caption_font},{int(font_size * 0.72)},{WHITE},{highlight},{OUTLINE},{SHADOW},-1,0,0,0,100,100,1.0,0,1,6,2,8,80,80,{int(height * 0.13)},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    lines: list[str] = []
    for page in pages:
        parts: list[str] = []
        for i, word in enumerate(page.words):
            clean_w = _normalise(word)
            is_punch = cfg.animate_punch_words and clean_w in PUNCH_WORDS
            display_word = word.upper() if (uppercase_mode or is_punch) else word
            token = esc_ass(display_word)

            if i == page.highlight_index:
                if is_punch:
                    # Animate-Your-Word explosive punch highlight (+40% scale explosion, fire-red)
                    anim_tag = r"{\c&H000030FF\t(0,60,\fscx140\fscy140)\t(60,140,\fscx116\fscy116)}"
                else:
                    anim_tag = style_spec["anim"]
                reset_tag = r"{\c" + primary_color + r"\fscx100\fscy100\frz0\blur0}"
                parts.append(f"{anim_tag}{token}{reset_tag}")
            else:
                parts.append(token)
        text = " ".join(parts)
        lines.append(
            f"Dialogue: 0,{fmt_ts_ass(page.start)},{fmt_ts_ass(page.end)},Caption,,0,0,0,,{text}"
        )

    if hook_text and (cfg.hook_v2 or cfg.hook_banner):
        start, end = 0.05, 2.3
        if total_duration < 2.5:
            end = max(1.0, total_duration - 0.2)
        # Hook V2: Attention-grabbing top alert banner with pill badge style
        banner = _shorten(hook_text.upper(), 32)
        text = r"{\fad(100,150)\bord7\shad3\c&H0000FFFF}🚨 " + esc_ass(banner)
        lines.append(f"Dialogue: 1,{fmt_ts_ass(start)},{fmt_ts_ass(end)},Hook,,0,0,0,,{text}")

    return header + "\n".join(lines) + "\n"


def _shorten(text: str, limit: int) -> str:
    """Trim to a word boundary so a caption banner never runs off the frame."""
    text = (text or "").strip()
    if len(text) <= limit:
        return text
    cut = text[: limit + 1]
    if " " in cut:
        cut = cut[: cut.rfind(" ")]
    return cut.rstrip(" ,.;:-")


def write_ass(
    pages: Sequence[CaptionPage],
    out_path: str | Path,
    total_duration: float,
    cfg: Config | None = None,
    hook_text: str = "",
) -> Path:
    cfg = cfg or get_config()
    content = build_ass(pages, total_duration, cfg, hook_text)
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(content, encoding="utf-8")
    log.info("captions written: %s (%d pages)", out_path.name, len(pages))
    return out_path


def captions_for(
    voice_words: Sequence[WordTiming],
    script_text: str,
    duration: float,
    out_path: str | Path,
    cfg: Config | None = None,
    audio_path: str | Path | None = None,
    hook_text: str = "",
    segments: Sequence[tuple[str, float, float]] | None = None,
) -> tuple[Path, int]:
    """One-stop helper: pick the timing source, build pages, write the .ass file.

    Source order (CAPTION_SOURCE=auto, the default):

    1. faster-whisper on the finished narration - exact word boundaries and the
       default whenever the voice engine does not provide timings (Kokoro, Piper).
    2. the voice engine's own timings (edge-tts WordBoundary, ElevenLabs alignment).
    3. the built-in syllable estimator over the sentence anchors the local engines
       return (within ~120 ms of whisper in testing).
    4. even spread across the duration - only if everything above failed.
    """
    from . import align

    cfg = cfg or get_config()
    source = (cfg.caption_source or "auto").lower()
    profile = cfg.profile()
    words: list[WordTiming] = []

    want_whisper = source == "whisper" or (source == "auto" and not voice_words)
    if want_whisper and audio_path:
        try:
            words = timings_from_whisper(audio_path, cfg, script_text)
        except Exception as exc:  # noqa: BLE001 - captions must never break a render
            log.warning("whisper timing source failed (%s) -> falling back", exc)
        finally:
            # the render still has to encode 1080x1920; do not hold a speech model while it does
            if not cfg.keep_whisper_loaded:
                align.release_whisper()

    if not words and source != "estimate" and voice_words:
        words = align_timings(voice_words, script_text)

    if not words and source != "estimate" and segments:
        words = [WordTiming(*w) for w in align.estimate_words(list(segments))]
        log.info("captions: sentence-anchored estimator used (%d words)", len(words))

    if not words:
        # nothing usable: spread the script words evenly across the duration
        words = [WordTiming(*w) for w in align.proportional_words(script_text, duration)]
        if words:
            log.warning("no word timings available - using the even-spread fallback")

    pages = build_pages(words, profile.words_per_line, profile.chars_per_line, duration)
    path = write_ass(pages, out_path, duration, cfg, hook_text=hook_text if cfg.hook_banner else "")
    return path, len(pages)
