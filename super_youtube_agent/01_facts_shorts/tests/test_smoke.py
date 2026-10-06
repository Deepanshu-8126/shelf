"""Smoke tests - run with:  pytest -q   (or: python tests/test_smoke.py)

These cover the parts that break silently in production: caption timing/overlap,
segment planning, the offline fact bank, SEO limits and the DB round-trip.
Nothing here needs an API key or a network connection.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

os.environ.setdefault("TEST_OFFLINE_MODE", "1")

import pytest  # noqa: E402

from factshorts import db  # noqa: E402
from factshorts.captions import align_timings, build_pages, build_ass  # noqa: E402
from factshorts.config import get_config  # noqa: E402
from factshorts.footage import Clip, ClipCandidate, JUNK_TITLE_RE  # noqa: E402
from factshorts.render import picking_window, plan_segments, segment_problem  # noqa: E402
from factshorts.script_writer import Script, Sentence, sanitize_keywords  # noqa: E402
from factshorts.seo import build_seo  # noqa: E402
from factshorts.topic_engine import FACT_BANK, Topic  # noqa: E402
from factshorts.utils import clean_text, esc_ass, is_similar, slugify  # noqa: E402
from factshorts.voice import WordTiming  # noqa: E402


# ------------------------------------------------------------------ test data
def make_words(pairs):
    return [WordTiming(w, s, e) for w, s, e in pairs]


@pytest.fixture()
def tmp_db(tmp_path, monkeypatch):
    cfg = get_config()
    original = cfg.db_path
    cfg.db_path = tmp_path / "test.db"
    db.init_db()
    yield cfg
    cfg.db_path = original


# --------------------------------------------------------------------- utils
def test_clean_text_and_slug():
    assert clean_text("Hello   world ,  ok") == "Hello world, ok"
    assert clean_text("Mantis shrimp punch — Facts") == "Mantis shrimp punch, Facts"
    assert slugify("Venus spins, backwards!") == "venus-spins-backwards"
    assert esc_ass("a{b}c") == "a(b)c"


def test_similarity_detects_dupes():
    assert is_similar("Venus spins backwards", "Venus rotates backwards")
    assert not is_similar("Venus spins backwards", "Octopuses have three hearts")


# ------------------------------------------------------------------ captions
def test_no_overlapping_caption_pages():
    words = make_words([("a", 0.0, 0.07), ("day", 0.07, 0.3), ("longer", 0.3, 0.9),
                        ("than", 0.9, 1.0), ("a", 1.0, 1.06), ("year", 1.06, 1.5)])
    pages = build_pages(words, words_per_page=3, chars_per_line=20, duration=1.5)
    assert pages, "pages should not be empty"
    for prev, nxt in zip(pages, pages[1:]):
        assert prev.end <= nxt.start + 1e-6, f"overlap {prev} -> {nxt}"


def test_every_page_has_a_highlighted_word():
    words = make_words([(f"w{i}", i * 0.3, i * 0.3 + 0.25) for i in range(9)])
    pages = build_pages(words, 3, 20, 3.0)
    assert all(0 <= p.highlight_index < len(p.words) for p in pages)


def test_align_timings_handles_different_splits():
    events = [WordTiming("mind-blowing", 0.0, 1.0), WordTiming("fact", 1.0, 1.4)]
    aligned = align_timings(events, "mind blowing fact")
    assert len(aligned) == 3
    assert aligned[-1].word == "fact"


def test_ass_file_is_buildable():
    pages = build_pages(make_words([("hello", 0, 0.5), ("world", 0.5, 1.0)]), 2, 20, 1.0)
    ass = build_ass(pages, 1.0, get_config(), hook_text="A very long topic label that must be trimmed")
    assert "[Events]" in ass and "Dialogue:" in ass
    assert ass.count("Dialogue:") >= 2


# ------------------------------------------------------------------- planning
def test_plan_segments_respects_duration():
    cfg = get_config()
    clips = [Clip(path=Path(f"/tmp/c{i}.mp4"), candidate=ClipCandidate("local", str(i), "file:///x.mp4"),
                  duration=12.0) for i in range(4)]
    plans = plan_segments(clips, 12.0, cfg)
    assert 1 <= len(plans) <= 4
    for plan in plans:
        assert plan.length > 1.5
        assert plan.start + plan.length <= 12.0 + 0.01


def test_plan_segments_short_clips_loop():
    cfg = get_config()
    clips = [Clip(path=Path("/tmp/a.mp4"), candidate=ClipCandidate("local", "a", "file:///a.mp4"), duration=1.2)]
    plans = plan_segments(clips, 12.0, cfg)
    assert plans[0].loop is True


def test_picking_window_prefers_middle_of_long_videos():
    low, high = picking_window(120.0, 4.0)
    assert low >= 30 and high <= 90


def test_segment_problem_flags_black_and_blurry():
    assert segment_problem((255.0, 40.0, 5.0)) == ""
    assert "black" in segment_problem((10.0, 3.0, 4.0))
    assert "focus" in segment_problem((120.0, 40.0, 30.0))


# ---------------------------------------------------------------------- voice
def test_word_timings_are_monotonic():
    words = make_words([("one", 0, 0.2), ("two", 0.2, 0.5), ("three", 0.5, 0.9)])
    assert all(a.start <= b.start for a, b in zip(words, words[1:]))


# ------------------------------------------------------------------- keywords
def test_keywords_never_contain_stopwords_or_single_letters():
    kws = sanitize_keywords(["a", "day", "the", "planet venus", "of", "space animation"], "space")
    assert "a" not in kws and "day" not in kws and "the" not in kws
    assert "planet venus" in kws


def test_keywords_fall_back_to_niche_visuals():
    kws = sanitize_keywords(["a", "of", "to"], "animals")
    assert kws and any("wildlife" in k or "ocean" in k or "forest" in k for k in kws)


# ----------------------------------------------------------------------- SEO
def test_offline_seo_respects_youtube_limits(tmp_db):
    topic = Topic(niche="space", topic="Venus spins backwards", fact="Venus rotates backwards, " * 3)
    script = Script(hook="Here is something wild.", body=FACT_BANK["space"][0]["fact"],
                    closing="Follow for one fact a day.", sentences=[Sentence("x", ["planet venus"])],
                    topic=topic.topic, niche="space")
    seo = __import__("asyncio").run(build_seo(topic, script, llm=None, cfg=tmp_db))
    assert len(seo["title"]) <= 60
    assert len(seo["tags"]) <= 15 and all(t == t.lower() for t in seo["tags"])
    assert "#shorts" in seo["description"]
    assert len(seo["description"]) < 5000
    assert seo["pinned_comment"]


# ------------------------------------------------------------------------ DB
def test_topic_dedupe_and_video_lifecycle(tmp_db):
    db.add_topic("space", "Venus spins backwards", "fact", "venus-spins-backwards", True, "test")
    assert "venus-spins-backwards" in db.topic_fingerprints()

    vid = db.create_video("space", "Venus spins backwards")
    db.update_video(vid, status="pending", title="Venus spins backwards", tags=["space", "shorts"],
                    meta={"voice": "en-US-EricNeural"})
    row = db.get_video(vid)
    assert row["status"] == "pending"
    assert "shorts" in row["tags"]
    assert db.count_videos_since(["pending"]) == 1
    stats = db.stats()
    assert stats["by_status"].get("pending") == 1


def test_settings_roundtrip(tmp_db):
    db.set_setting("niche", "animals")
    db.set_setting("auto_mode", "1")
    assert db.get_setting("niche") == "animals"
    assert db.get_bool_setting("auto_mode") is True


# ------------------------------------------------------------------- footage
def test_junk_title_filter():
    assert JUNK_TITLE_RE.search("Audio Spectrogram of the Sun")
    assert JUNK_TITLE_RE.search("Screen recording demo")
    assert not JUNK_TITLE_RE.search("Earth from the ISS (4K)")


def test_fact_bank_shape():
    for niche, entries in FACT_BANK.items():
        assert entries, f"{niche} bank is empty"
        for entry in entries:
            assert {"topic", "fact"} <= set(entry)
            assert len(entry["fact"].split()) >= 10


if __name__ == "__main__":  # allow `python tests/test_smoke.py` without pytest
    raise SystemExit(pytest.main([__file__, "-q"]))


# ============================================================================
# Trends / sources
# ============================================================================
def test_trend_seed_keywords_and_label():
    from factshorts.trends import TrendSeed

    seed = TrendSeed(title="Gol Transportes Aereos Flight 1907", source="wikipedia", kind="onthisday", niche="history")
    assert seed.keywords(), "keywords must never be empty"
    assert "wikipedia" in seed.label() and "onthisday" in seed.label()


def test_google_trends_rss_parsing(monkeypatch):
    """The Google Trends RSS reader must work without a network call."""
    from factshorts import trends as trends_mod

    xml = """<?xml version="1.0"?><rss xmlns:ht="https://trends.google.com/trending/rss"><channel>
    <item><title>James Webb telescope discovery</title><ht:approx_traffic>2000+</ht:approx_traffic>
    <ht:news_item_title><![CDATA[JWST spots something odd]]></ht:news_item_title>
    <ht:news_item_url>https://example.com/news</ht:news_item_url></item>
    <item><title><![CDATA[Another trend]]></title><ht:approx_traffic>500+</ht:approx_traffic></item>
    </channel></rss>"""
    client = trends_mod.TrendClient()

    class FakeResp:
        status_code = 200
        text = xml

    class FakeHTTP:
        async def get(self, url, params=None):
            return FakeResp()

    import asyncio

    monkeypatch.setattr(client, "client", lambda: asyncio.sleep(0, result=FakeHTTP()))
    seeds = asyncio.run(client.google_trends("IN"))
    assert len(seeds) == 2
    assert seeds[0].title == "James Webb telescope discovery"
    assert seeds[0].extra["traffic"] == "2000+"
    assert seeds[0].source_url == "https://example.com/news"


def test_niche_relevance_filter():
    from factshorts.trends import TrendClient

    assert TrendClient._relevant("NASA launched a new space telescope to study galaxies", "space")
    assert not TrendClient._relevant("Premier League transfer news and match report", "space")
    assert not TrendClient._relevant("Prime minister election results announced", "science")
    assert TrendClient._relevant("Researchers studied octopus behaviour and other marine species", "animals")
    # a single incidental keyword is not enough - that is how ".xyz" slipped through before
    assert not TrendClient._relevant("A domain ending that some registrars use for websites", "space")
    assert not TrendClient._relevant("Anything at all here", "space", title="List of tallest buildings")


def test_offline_topic_from_seed_is_citable():
    from factshorts.topic_engine import topic_from_seed
    from factshorts.trends import TrendSeed

    seed = TrendSeed(
        title="Sunlight",
        summary="Sunlight takes about 8 minutes 20 seconds to reach Earth. The energy inside the Sun "
                "may take over 100,000 years to escape its core.",
        source="wikipedia",
        source_url="https://en.wikipedia.org/wiki/Sunlight",
        kind="mostread",
    )
    topic = topic_from_seed(seed, "space")
    assert topic.verified and topic.source_url.startswith("https://en.wikipedia.org")
    assert topic.source_name == "Wikipedia"
    assert len(topic.fact.split()) >= 8


# ============================================================================
# Voice providers
# ============================================================================
def test_provider_selection(monkeypatch, tmp_db):
    from factshorts import voice as voice_mod
    from factshorts.config import Config

    cfg = Config()
    cfg.elevenlabs_api_key = ""
    cfg.voice_provider = "auto"
    # v3: auto prefers a free local engine when one is importable, else edge-tts
    installed = voice_mod.available_engines()
    expected = "kokoro" if "kokoro" in installed else ("piper" if "piper" in installed else "edge")
    assert voice_mod.provider_for(cfg) == expected

    # with nothing installed locally there is still a free key-less path
    monkeypatch.setattr(voice_mod, "available_engines", lambda: [])
    assert voice_mod.provider_for(cfg) == "edge"

    cfg.voice_provider = "local"
    assert voice_mod.provider_for(cfg) == "edge"      # asked for local, nothing installed

    monkeypatch.setattr(voice_mod, "available_engines", lambda: ["piper"])
    assert voice_mod.provider_for(cfg) == "piper"
    monkeypatch.setattr(voice_mod, "available_engines", lambda: ["kokoro", "piper"])
    assert voice_mod.provider_for(cfg) == "kokoro"

    cfg.voice_provider = "auto"
    cfg.elevenlabs_api_key = "sk_test_123"
    assert voice_mod.provider_for(cfg) == "kokoro"    # free beats paid in auto mode

    monkeypatch.undo()
    cfg.elevenlabs_api_key = "sk_test_123"
    cfg.voice_provider = "elevenlabs"
    assert voice_mod.provider_for(cfg) == "elevenlabs"

    # elevenlabs asked for but no key -> free fallback, never a crash
    cfg.elevenlabs_api_key = ""
    assert voice_mod.provider_for(cfg) in {"kokoro", "piper", "edge"}

    cfg.voice_provider = "edge"
    assert voice_mod.provider_for(cfg) == "edge"

    # the bot can override at runtime through SQLite
    tmp_db.db_path = tmp_db.db_path  # keep the fixture db
    voice_mod.db.set_setting("voice_provider", "edge")
    cfg.voice_provider = "auto"
    assert voice_mod.provider_for(cfg) == "edge"      # stored setting wins over .env

    voice_mod.db.set_setting("voice_provider", "elevenlabs")
    cfg.elevenlabs_api_key = "sk_test_123"
    assert voice_mod.provider_for(cfg) == "elevenlabs"
    cfg.elevenlabs_api_key = ""                       # no key -> back to a free engine
    assert voice_mod.provider_for(cfg) in {"kokoro", "piper", "edge"}
    voice_mod.db.set_setting("voice_provider", "")


def test_elevenlabs_alignment_to_words():
    from factshorts.voice import _alignment_to_words

    text = "Venus spins backwards."
    starts, ends, t = [], [], 0.0
    for _ in text:
        starts.append(round(t, 3))
        t += 0.06
        ends.append(round(t, 3))
    words = _alignment_to_words({
        "characters": list(text),
        "character_start_times_seconds": starts,
        "character_end_times_seconds": ends,
    })
    assert [w.word for w in words] == ["Venus", "spins", "backwards."]
    assert words[0].start == 0.0
    assert all(a.end <= b.start + 1e-6 for a, b in zip(words, words[1:]))
    assert _alignment_to_words({}) == []


def test_elevenlabs_missing_key_errors_cleanly():
    import asyncio

    from factshorts.voice import elevenlabs_usage

    class ConfigStub:
        elevenlabs_api_key = ""

    assert asyncio.run(elevenlabs_usage(ConfigStub())) == {}


# ============================================================================
# Instagram / multi-platform
# ============================================================================
def test_instagram_config_detection(tmp_db):
    from factshorts import instagram

    tmp_db.ig_user_id = ""
    tmp_db.ig_access_token = ""
    assert instagram.is_configured(tmp_db) is False
    tmp_db.ig_user_id = "17841400000000000"
    tmp_db.ig_access_token = "EAAB..."
    assert instagram.is_configured(tmp_db) is True


def test_instagram_caption_has_hashtags_and_no_links(tmp_db):
    from factshorts import instagram

    video = {
        "hook": "Here's something strange.",
        "niche": "space",
        "tags": '["space facts", "didyouknow", "nasa"]',
        "source_url": "https://en.wikipedia.org/wiki/Sunlight",
        "source_name": "Wikipedia",
        "meta": '{"script": {"full_text": "Sunlight takes eight minutes to reach Earth.", '
                '"body": "Sunlight takes eight minutes to reach Earth."}}',
    }
    caption = instagram.caption_for(video, tmp_db)
    assert "#space" in caption and "#reels" in caption
    assert "en.wikipedia.org" in caption          # source credit survives
    assert len(caption) <= 2200
    assert caption.count("#") <= tmp_db.ig_hashtag_limit + 2


def test_publish_platform_parsing(tmp_db):
    from factshorts.publish import platform_health, platforms_from_setting

    tmp_db.platforms = ["youtube"]
    import factshorts.db as dbmod

    dbmod.set_setting("platforms", "youtube,instagram,bogus")
    assert platforms_from_setting(tmp_db) == ["youtube", "instagram"]
    health = platform_health(tmp_db)
    assert {"youtube", "instagram"}.issubset(set(health))
    dbmod.set_setting("platforms", "")
    assert platforms_from_setting(tmp_db) == ["youtube"]


def test_publish_summary_text():
    from factshorts.publish import summary_text

    text = summary_text({
        "youtube": {"url": "https://youtube.com/shorts/abc", "privacy": "public", "synthetic_disclosure": True,
                    "quota_left": 4},
        "instagram": {"error": "token expired"},
    })
    assert "youtube.com/shorts/abc" in text
    assert "instagram" in text and "token expired" in text


# ============================================================================
# Script tone (no advert language)
# ============================================================================
def test_strip_ad_language():
    from factshorts.script_writer import strip_ad_language

    dirty = "In this video, guys, you won't believe this insane fact. Don't forget to subscribe!"
    clean = strip_ad_language(dirty)
    lowered = clean.lower()
    for banned in ("in this video", "subscribe", "you won't believe", "insane", "guys"):
        assert banned not in lowered
    assert clean.strip()


def test_style_and_cta_presets(tmp_db):
    from factshorts.script_writer import CLOSINGS, HOOKS, STYLE_PROMPTS, cta_of, style_of

    tmp_db.script_style = "documentary"
    tmp_db.cta_style = "none"
    assert style_of(tmp_db) == "documentary"
    assert cta_of(tmp_db) == "none"
    assert set(STYLE_PROMPTS) == {"friendly", "documentary", "punchy"}
    assert set(CLOSINGS) == {"none", "soft", "follow"}
    assert all(style in HOOKS for style in STYLE_PROMPTS)

    tmp_db.script_style = "nonsense"
    tmp_db.cta_style = "nonsense"
    assert style_of(tmp_db) == "friendly"
    assert cta_of(tmp_db) == "soft"


# ============================================================================
# Scheduler: morning + night slots
# ============================================================================
def test_schedule_slots(tmp_db, monkeypatch):
    import factshorts.db as dbmod
    from factshorts import scheduler

    dbmod.set_setting("schedule_times", "08:30,19:30")
    assert scheduler.current_times() == ["08:30", "19:30"]
    assert scheduler.current_time() == "08:30"

    dbmod.set_setting("schedule_times", "")
    tmp_db.schedule_times = ["07:00"]
    assert scheduler.current_times() == ["07:00"]

    # validation helper used by the /schedule command
    assert scheduler._normalise_time("8:5") == "08:05"
    assert scheduler._normalise_time("19:30") == "19:30"
    assert scheduler._normalise_time("25:00") is None
    assert scheduler._normalise_time("abc") is None


def test_niche_rotation(tmp_db):
    import factshorts.db as dbmod
    from factshorts.scheduler import _niche_for_slot

    dbmod.set_setting("niche", "space")
    tmp_db.niche_rotate = False
    assert _niche_for_slot(0) == "space"
    assert _niche_for_slot(1) == "space"

    tmp_db.niche_rotate = True
    first, second = _niche_for_slot(0), _niche_for_slot(1)
    assert first == "space"
    assert second != first, "rotation should move to another niche on the second slot"


def test_sensitive_and_noise_filters():
    from factshorts.trends import TrendClient

    assert not TrendClient._relevant("A study on drug addiction treatment", "psychology")
    assert not TrendClient._relevant("Ancient torture methods described in a manuscript", "history")
    assert TrendClient._relevant("Researchers mapped the genome of a deep-sea fish species", "animals")


def test_trend_seed_never_picks_list_articles():
    from factshorts.trends import TrendClient

    assert not TrendClient._relevant("A list of the tallest buildings", "science",
                                     title="List of tallest buildings")
    assert not TrendClient._relevant("A statistical table about countries", "science",
                                     title="Deaths in 2026")


def test_meta_merge_keeps_earlier_keys(tmp_db):
    from factshorts import db as dbmod

    vid = dbmod.create_video("space", "Test")
    dbmod.update_meta(vid, {"topic_source": "wikipedia", "trend": {"kind": "search"}})
    dbmod.update_meta(vid, {"voice": "en-US-EricNeural"})
    row = dbmod.get_video(vid)
    import json

    meta = json.loads(row["meta"])
    assert meta["topic_source"] == "wikipedia"
    assert meta["trend"]["kind"] == "search"
    assert meta["voice"] == "en-US-EricNeural"


def test_dry_run_publish_does_not_change_status(tmp_db, tmp_path):
    """A dry run must leave the queue alone - otherwise 'uploaded' statistics lie."""
    import asyncio

    from factshorts import db as dbmod
    from factshorts.publish import publish_video

    media = tmp_path / "clip.mp4"
    media.write_bytes(b"0" * 200_000)
    vid = dbmod.create_video("space", "Dry run subject", status="pending")
    dbmod.update_video(vid, video_path=str(media), title="t", description="d", tags=["shorts"])

    results = asyncio.run(publish_video(vid, platforms=["youtube", "instagram"], dry_run=True))
    assert all(r.get("dry_run") for r in results.values())

    row = dbmod.get_video(vid)
    assert row["status"] == "pending", f"dry run changed the status to {row['status']}"
    assert not row["yt_video_id"] and not row["ig_media_id"]
    assert not row["platforms"]


def test_segment_problem_uses_range_not_stddev():
    """signalstats has no YSTD, so structure is measured as YHIGH-YLOW."""
    from factshorts.render import segment_problem

    assert segment_problem((255.0, 200.0, 5.0)) == ""
    # dark but full of stars = usable
    assert segment_problem((18.0, 140.0, 4.0)) == ""
    # dark and empty = title card
    assert "black" in segment_problem((12.0, 3.0, 2.0))
    assert "focus" in segment_problem((120.0, 90.0, 25.0))


def test_clip_sharpness_ranking_is_relative(tmp_path):
    """rank_clips_by_sharpness drops only clips that are clearly softer than the rest."""
    import asyncio

    from factshorts.footage import Clip, ClipCandidate
    from factshorts.render import rank_clips_by_sharpness

    def clip(name, blur):
        c = Clip(path=tmp_path / f"{name}.mp4", candidate=ClipCandidate("local", name, "file:///x"))
        c.sharpness = blur
        return c

    clips = [clip("a", 5.0), clip("b", 6.0), clip("c", 40.0)]   # c is obviously soft
    kept = asyncio.run(rank_clips_by_sharpness(clips))
    assert [c.candidate.source_id for c in kept] == ["a", "b"]

    # all similar -> nothing dropped
    similar = [clip("d", 5.0), clip("e", 6.5), clip("f", 7.0)]
    assert len(asyncio.run(rank_clips_by_sharpness(similar))) == 3


# ============================================================================
# v3: free local voice + 60 second story mode
# ============================================================================
def test_local_tts_helpers(monkeypatch, tmp_path):
    from factshorts import tts_local
    from factshorts.config import Config

    cfg = Config()
    assert tts_local.split_sentences("Honey never spoils. Archaeologists dug it up. Chemistry.") == [
        "Honey never spoils.", "Archaeologists dug it up.", "Chemistry."
    ]
    # short fragments are glued to the previous sentence (two-word lines sound choppy)
    glued = tts_local.split_sentences("This is a longer first sentence about honey. Yes. Really.")
    assert glued == ["This is a longer first sentence about honey. Yes.", "Really."]

    long_line = "A single enormous sentence, " + "filled with many clauses, " * 12 + "and it ends here."
    parts = tts_local.split_sentences(long_line, max_chars=120)
    assert len(parts) > 2 and all(len(p) <= 130 for p in parts)

    # model_ready must be False on an empty model dir, and no traceback for unknown engines
    cfg.tts_model_dir = tmp_path
    assert tts_local.model_ready("kokoro", "af_heart", cfg) is False
    assert tts_local.model_ready("piper", "en_US-lessac-medium", cfg) is False
    assert tts_local.model_ready("nonsense", "x", cfg) is False


def test_word_estimator_stays_inside_the_sentence():
    from factshorts.align import estimate_span, estimate_words, syllables

    assert syllables("honey") == 2
    assert syllables("archaeologists") >= 4          # "ar-chae-o-lo-gists"
    assert syllables("the") == 1

    words = estimate_span("Honey never spoils, and that matters.", 4.0)
    assert words[0][0] == "Honey" and words[0][1] == 0.0
    assert words[-1][2] <= 4.05                       # never overruns its own sentence
    starts = [w[1] for w in words]
    assert starts == sorted(starts)                   # monotonic
    # the comma costs time: "spoils," ends later than a word of the same length would
    assert words[3][2] > words[2][2]

    spans = estimate_words([("Honey never spoils.", 1.0, 3.0), ("That matters.", 5.0, 2.0)])
    assert spans[0][1] == 1.0 and spans[-1][1] >= 5.0
    assert estimate_words([]) == []


def test_snap_to_script_keeps_script_words_and_whisper_timings():
    from factshorts.align import snap_to_script, check_accuracy

    script = "Honey never spoils in a sealed jar."
    heard = [
        ("Honey", 0.0, 0.4), ("never", 0.4, 0.7), ("spoils", 0.7, 1.2),
        ("in", 1.2, 1.3), ("a", 1.3, 1.4), ("sealed", 1.4, 1.9), ("jar", 1.9, 2.3),
    ]
    out = snap_to_script(heard, script)
    assert [w[0] for w in out] == script.split()      # exact script spelling
    assert out[0][1] == 0.0 and out[-1][1] == 1.9
    assert [w[1] for w in out] == sorted(w[1] for w in out)

    # whisper merging two words into one ("12000") must not lose words
    merged = snap_to_script([("Twelve", 0.0, 0.5), ("thousand", 0.5, 1.0), ("years", 1.0, 1.4)],
                            "12,000 years")
    assert [w[0] for w in merged] == ["12,000", "years"]
    assert len(merged) == 2

    # a word whisper missed entirely gets interpolated between its neighbours
    partial = snap_to_script([("Honey", 0.0, 0.5), ("spoils", 1.5, 2.0)], "Honey really never spoils")
    assert len(partial) == 4
    assert 0.5 <= partial[1][1] < partial[2][1] < 1.5
    mae, worst, n = check_accuracy(partial, partial)
    assert n == 4 and mae == 0.0 and worst == 0.0


def test_story_mode_profile_and_word_window(monkeypatch):
    from factshorts.config import get_config, FACTS_PROFILE
    from factshorts.script_writer import word_window
    from factshorts import db

    db.set_setting("video_mode", "")
    try:
        monkeypatch.delenv("VIDEO_MODE", raising=False)
        cfg = get_config(refresh=True)
        assert cfg.mode() == "facts" and cfg.profile().name == "facts"
        assert word_window(cfg) == (FACTS_PROFILE.min_words, FACTS_PROFILE.max_words, FACTS_PROFILE.target_words)

        monkeypatch.setenv("VIDEO_MODE", "story")
        cfg = get_config(refresh=True)
        profile = cfg.profile()
        assert cfg.mode() == "story" and profile.name == "story"
        assert profile.max_duration >= 60 >= profile.min_duration
        assert profile.clip_count > FACTS_PROFILE.clip_count          # 60 s needs more shots
        assert profile.seconds_per_clip > FACTS_PROFILE.seconds_per_clip
        min_words, max_words, target = word_window(cfg)
        assert min_words <= target <= max_words and 120 <= target <= 200

        # a live /mode switch (SQLite setting) beats the .env value
        db.set_setting("video_mode", "facts")
        assert cfg.mode() == "facts"
        db.set_setting("video_mode", "story")
        assert cfg.mode() == "story"
    finally:
        db.set_setting("video_mode", "")
        monkeypatch.delenv("VIDEO_MODE", raising=False)
        get_config(refresh=True)


def test_offline_story_script_is_story_shaped(monkeypatch):
    from factshorts.config import get_config
    from factshorts.script_writer import _offline_story, word_window
    from factshorts.topic_engine import Topic

    monkeypatch.setenv("VIDEO_MODE", "story")
    cfg = get_config(refresh=True)
    topic = Topic(
        topic="The honey that outlived the pyramids",
        fact=("Archaeologists opened Egyptian tombs and found pots of honey that were still "
              "perfectly edible after more than three thousand years. Honey is mostly sugar with "
              "very little water, so bacteria cannot grow in it, and bees add an enzyme that makes "
              "a tiny amount of hydrogen peroxide."),
        angle="a sealed jar has nowhere to go bad",
        niche="science",
        source="offline-bank",
        keywords=["honey jar", "ancient egypt tomb", "beekeeper"],
    )
    script = _offline_story(topic, cfg)
    assert script.source == "offline-story-template"
    assert script.hook and script.closing
    assert len(script.sentences) >= 3
    assert script.visual_keywords()
    min_words, max_words, _ = word_window(cfg)
    assert script.word_count >= min_words * 0.5       # a fallback story is allowed to be a bit short


def test_caption_source_chain_uses_sentence_anchors(monkeypatch, tmp_path):
    from factshorts.captions import captions_for
    from factshorts.config import get_config

    cfg = get_config(refresh=True)
    cfg.caption_source = "auto"
    text = "Honey never spoils. That is the whole trick."
    segments = [("Honey never spoils.", 0.2, 2.4), ("That is the whole trick.", 2.9, 2.1)]
    ass, pages = captions_for([], text, 5.2, tmp_path / "c.ass", cfg, audio_path=None, segments=segments)
    assert pages > 0 and ass.exists()
    body = ass.read_text()
    assert "Honey" in body and "trick" in body
    # the estimator anchored on sentence 2 must place its first word at ~2.9 s
    assert "0:00:02.9" in body or "0:00:02.8" in body


def test_story_segment_pacing_needs_more_shots():
    from factshorts.config import get_config
    from factshorts.render import plan_segments
    from factshorts.footage import Clip
    from factshorts.footage import ClipCandidate

    cfg = get_config(refresh=True)
    clips = []
    for i in range(12):
        cand = ClipCandidate(source="local", source_id=f"c{i}", query="q", width=1080, height=1920,
                             duration=20.0, download_url="")
        clips.append(Clip(path=__import__("pathlib").Path(f"/tmp/c{i}.mp4"), candidate=cand,
                          duration=20.0, width=1080, height=1920))

    cfg.video_mode = "facts"
    facts_plans = plan_segments(clips, 12.0, cfg)
    assert len(facts_plans) == 3          # ~3.8 s per shot, capped by VIDEO_CLIP_COUNT

    cfg.video_mode = "story"
    cfg.caption_words_per_line = 4
    story_plans = plan_segments(clips, 60.0, cfg)
    assert 8 <= len(story_plans) <= cfg.profile().clip_count
    assert all(p.length >= 1.6 for p in story_plans)
    assert sum(p.length for p in story_plans) + cfg.transition_duration * (len(story_plans) - 1) > 55
