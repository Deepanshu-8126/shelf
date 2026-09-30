import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from datetime import date

from agent.adapters import distribution_variants, platform_matrix
from agent.db import init_db
from agent.game_clips import (
    _ffmpeg_supports_ass,
    _local_source,
    _render_vertical_clip,
    captions_to_ass,
    captions_to_srt,
)
from agent.llm import _fallback
from agent.pipeline import _clean_source_urls
from agent.policy import publish_blockers, safe_privacy
from agent.research import _score_candidate, cohort_summaries, demo_candidates
from agent.strategy import build_strategy


class CreatorOpsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
    def test_demo_scan_is_explicitly_demo(self):
        candidates = demo_candidates()
        self.assertGreaterEqual(len(candidates), 3)
        self.assertTrue(all(c["mode"] == "demo" for c in candidates))
        self.assertTrue(all("Demo" in c["note"] for c in candidates))

    def test_publish_fails_closed_for_unreviewed_draft(self):
        job = {
            "id": "test", "channel_id": "missing", "rights_status": "uncleared",
            "rights_evidence": "", "human_approved": False, "has_audio": False,
            "video_path": "", "data": {"fact_check_status": "needs_review"},
        }
        blockers = publish_blockers(job)
        self.assertGreaterEqual(len(blockers), 5)
        self.assertTrue(any("Rights" in item for item in blockers))
        self.assertTrue(any("fact-check" in item for item in blockers))

    def test_public_upload_is_private_without_both_explicit_switches(self):
        self.assertEqual(safe_privacy("public"), "private")
        self.assertIn("private", {safe_privacy("private"), safe_privacy("public")})

    def test_cohort_sample_reports_heuristic_outliers_and_repeatability(self):
        rows = [
            {"cohort": "0-30", "channel_id": "c1", "channel": "One", "views": 3000, "views_per_day": 100, "view_subscriber_ratio": 3.1},
            {"cohort": "31-90", "channel_id": "c2", "channel": "Two", "views": 2400, "views_per_day": 40, "view_subscriber_ratio": 4.0},
            {"cohort": "91-180", "channel_id": "c3", "channel": "Three", "views": 1800, "views_per_day": 20, "view_subscriber_ratio": 2.0},
        ]
        summaries = cohort_summaries(rows)
        self.assertEqual(summaries["0-30"]["sample_count"], 1)
        self.assertEqual(summaries["31-90"]["heuristic_outlier_videos"], 1)
        self.assertEqual(summaries["91-180"]["heuristic_outlier_videos"], 0)
        scored = _score_candidate({"name": "test", "query": "x", "monetization_fit": 50, "production_ease": 50}, rows, "2026-09-30T00:00:00Z")
        self.assertIn("repeatability", scored["sustainability_signal"])
        self.assertIn("commercial_intent_prior", scored["methodology"])

    def test_source_urls_are_http_only_deduplicated_and_bounded(self):
        urls = _clean_source_urls(["https://example.com/source", "javascript:alert(1)", "https://example.com/source", "ftp://example.com/file"])
        self.assertEqual(urls, ["https://example.com/source"])

    def test_documentary_fallback_is_research_first_not_fake_research(self):
        draft = _fallback("A case study", "Technology", "Documentary", source_urls=["https://example.org/report"])
        self.assertEqual(len(draft["scenes"]), 6)
        self.assertEqual(draft["factual_claims"], [])
        self.assertTrue(draft["verification_required"])
        self.assertEqual(draft["source_urls"], ["https://example.org/report"])
        self.assertIn("has not analyzed", draft["script"])

    def test_strategy_plan_is_provisional_in_demo_and_has_calendar(self):
        plan = build_strategy("ch-1", {"mode": "demo", "candidates": demo_candidates()}, [], date(2026, 9, 30))
        self.assertTrue(plan["status"].startswith("provisional"))
        self.assertEqual(len(plan["calendar"]), 4)
        self.assertEqual(plan["calendar"][0]["date"], "2026-10-05")
        self.assertEqual(plan["owner_analytics_baseline"]["status"], "no owner analytics yet")

    def test_distribution_exports_do_not_claim_live_publishers(self):
        variants = distribution_variants({"title": "Test", "hook": "A useful hook", "tags": ["demo"]}, "Documentary")
        self.assertIn("youtube", variants["platforms"])
        self.assertEqual(variants["platforms"]["tiktok"]["status"], "draft only · no adapter")
        self.assertIn("no cross-platform posting", variants["delivery_mode"])
        matrix = platform_matrix([])
        self.assertEqual(next(x for x in matrix if x["id"] == "youtube")["state"], "implemented")
        self.assertTrue(all(x["state"] == "export_only" for x in matrix if x["id"] != "youtube"))

    def test_gaming_caption_srt_uses_human_supplied_hinglish_lines(self):
        srt = captions_to_srt(["Scene yahan se palat ti hai", "आख़िरी turn sab badal deta hai"], 10)
        self.assertIn("00:00:00,000 --> 00:00:05,000", srt)
        self.assertIn("00:00:05,000 --> 00:00:10,000", srt)
        self.assertIn("आख़िरी turn", srt)
        with self.assertRaises(ValueError):
            captions_to_srt(["caption"], 61)

    def test_kinetic_caption_ass_has_word_timing_and_hindi_text(self):
        ass = captions_to_ass(["Yahan se", "आख़िरी turn"], 10)
        self.assertIn("PlayResX: 1080", ass)
        self.assertIn("PlayResY: 1920", ass)
        self.assertIn(r"{\kf250}Yahan {\kf250}se", ass)
        self.assertIn("आख़िरी", ass)
        self.assertEqual(ass.count("Dialogue: "), 2)
        self.assertTrue(ass.endswith("\n"))

    def test_kinetic_caption_ass_sanitizes_override_syntax_and_rejects_impossible_timing(self):
        ass = captions_to_ass([r"safe {\b1}"], 5)
        self.assertNotIn(r"{\b1}", ass)
        self.assertIn("｛", ass)
        self.assertIn("｝", ass)
        with self.assertRaises(ValueError):
            captions_to_ass(["one two three"], 0.02)

    def test_ffmpeg_ass_filter_detection_is_explicit(self):
        result = SimpleNamespace(returncode=0, stdout=" .. ass V->V render ASS subtitles\n", stderr="")
        with patch("agent.game_clips.subprocess.run", return_value=result):
            self.assertTrue(_ffmpeg_supports_ass("ffmpeg"))
        result = SimpleNamespace(returncode=0, stdout=" .. scale V->V resize video\n", stderr="")
        with patch("agent.game_clips.subprocess.run", return_value=result):
            self.assertFalse(_ffmpeg_supports_ass("ffmpeg"))

    def test_kinetic_render_adds_ass_filter_and_keeps_filter_path_quoted(self):
        with tempfile.TemporaryDirectory(prefix="kinetic captions ") as directory:
            root = Path(directory)
            target = root / "rendered.mp4"
            captions = root / "captions.ass"
            captions.write_text("[Script Info]\\n", encoding="utf-8")
            called = {}

            def fake_run(command, timeout=900):
                called["command"] = command
                Path(command[-1]).write_bytes(b"0" * 10000)

            with patch("agent.game_clips._run", side_effect=fake_run):
                _render_vertical_clip(Path("source.mp4"), target, "ffmpeg", 0, 5, False, captions_ass=captions)
            command = called["command"]
            graph = command[command.index("-filter_complex") + 1]
            self.assertIn("ass=filename=", graph)
            self.assertIn("captions.ass", graph)
            self.assertIn("'", graph)

    def test_gaming_source_path_is_local_and_confined(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "my_gameplay.mp4").write_bytes(b"local video placeholder")
            with patch("agent.game_clips.SOURCE_DIR", root):
                self.assertEqual(_local_source("my_gameplay.mp4"), root / "my_gameplay.mp4")
                with self.assertRaises(ValueError):
                    _local_source("../outside.mp4")
                with self.assertRaises(ValueError):
                    _local_source("https://youtube.com/watch?v=example")

    def test_fresh_channel_slots_keep_us_pilot_and_add_separate_india_game_slot(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch("agent.db.DB_PATH", root / "fresh.sqlite3"), patch("agent.db.DATA_DIR", root):
                init_db()
                from agent.db import list_channels
                channels = {item["id"]: item for item in list_channels()}
                self.assertEqual((channels["ch-1"]["audience_country"], channels["ch-1"]["language"]), ("US", "en-US"))
                self.assertEqual((channels["ch-2"]["audience_country"], channels["ch-2"]["language"]), ("IN", "hi-IN"))
                self.assertIn("GTA VI", channels["ch-2"]["name"])

    def test_gta_clip_publication_requires_case_specific_commercial_license(self):
        job = {
            "id": "test", "channel_id": "ch-2", "rights_status": "owned",
            "rights_evidence": "This is my recorded gameplay.", "human_approved": False,
            "has_audio": False, "video_path": "",
            "data": {"fact_check_status": "needs_review", "gaming_clip": {"source_kind": "owned_gameplay"}},
        }
        blockers = publish_blockers(job)
        self.assertTrue(any("Rockstar/Take-Two" in item for item in blockers))
        self.assertTrue(any("commentary" in item for item in blockers))
        self.assertTrue(any("leaked footage" in item for item in blockers))
        missing_metadata = dict(job, format="Game Clip", data={"fact_check_status": "verified_by_human"})
        metadata_blockers = publish_blockers(missing_metadata)
        self.assertTrue(any("metadata is missing" in item for item in metadata_blockers))


if __name__ == "__main__":
    unittest.main()
