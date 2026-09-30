"""FactShorts Bot - CLI entrypoint.

  python main.py --check                 # config + dependency health check
  python main.py --selftest              # tiny offline render (no network/keys needed)
  python main.py --auth                  # YouTube OAuth consent (once)
  python main.py --generate space        # make one video now
  python main.py --generate --offline    # use the offline fact bank (no LLM key needed)
  python main.py --generate --upload     # make it and upload immediately
  python main.py --demo                  # offline bank + free Wikimedia footage + render (no keys)
  python main.py --upload 12 --privacy unlisted
  python main.py --bot                   # Telegram bot + daily scheduler
  python main.py --daemon                # headless scheduler only (no bot polling)
"""
from __future__ import annotations

import argparse
import os
import asyncio
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from factshorts import db
from factshorts.config import NICHES, get_config
from factshorts.utils import have_binary, module_logger, setup_logging

log = module_logger("main")


def cmd_check() -> int:
    cfg = get_config()
    log.info("FactShorts Bot - environment check")
    print("─" * 62)
    print(cfg.describe())
    print("─" * 62)
    checks: list[tuple[str, bool, str]] = [
        ("ffmpeg", have_binary("ffmpeg"), "required for rendering"),
        ("ffprobe", have_binary("ffprobe"), "required for media inspection"),
        ("edge-tts (module)", _mod("edge_tts"), "free voiceover"),
        ("python-telegram-bot", _mod("telegram"), "only needed for --bot"),
        ("httpx", _mod("httpx"), "HTTP for all APIs"),
        ("APScheduler", _mod("apscheduler"), "only needed for scheduling"),
        ("google-api-python-client", _mod("googleapiclient"), "only needed for uploads"),
        ("faster-whisper (optional)", _mod("faster_whisper"), "CAPTION_SOURCE=whisper"),
        ("ElevenLabs key (optional)", bool(cfg.elevenlabs_api_key), "VOICE_PROVIDER=elevenlabs"),
    ]
    ok = True
    for name, present, why in checks:
        mark = "✅" if present else ("⚠️ " if "optional" in name or "only needed" in why else "❌")
        if mark == "❌":
            ok = False
        print(f"{mark} {name:28s} {'' if present else '— ' + why}")
    print("─" * 62)
    if not cfg.gemini_api_key and not cfg.groq_api_key:
        print("ℹ️  No LLM key set → the offline fact bank will be used (fine for testing).")
    if not cfg.pexels_api_key and not cfg.pixabay_api_key:
        print("ℹ️  No stock-footage key → Wikimedia Commons + assets/stock/ will be used.")
    if not cfg.yt_client_secrets.exists():
        print("ℹ️  credentials/client_secret.json not found → YouTube uploads disabled until you add it.")
    if "instagram" in cfg.platforms and not (cfg.ig_user_id and cfg.ig_access_token):
        print("ℹ️  Instagram selected but IG_USER_ID / IG_ACCESS_TOKEN missing → see docs/INSTAGRAM_SETUP.md")
    if not cfg.pexels_api_key:
        print("ℹ️  Trends: Google Trends + Wikipedia need no key (USE_TRENDS=%s, geo=%s)."
              % (cfg.use_trends, cfg.trends_geo))
    print("All hard requirements satisfied." if ok else "Install the ❌ items before rendering.")
    return 0 if ok else 1


def _mod(name: str) -> bool:
    import importlib.util

    return importlib.util.find_spec(name) is not None


def cmd_selftest() -> int:
    from factshorts.render import render_placeholder

    path = asyncio.run(render_placeholder(3.0))
    print(f"✅ selftest render: {path}")
    return 0


def cmd_auth() -> int:
    from factshorts.uploader import run_oauth_flow

    token = run_oauth_flow()
    print(f"✅ token saved: {token}")
    return 0


def cmd_generate(niche: str | None, offline: bool, upload: bool, privacy: str | None, dry_run: bool,
                 topic: str | None = None, platforms: list[str] | None = None) -> int:
    cfg = get_config()
    if offline:
        cfg.test_mode = True  # forces the offline fact bank + templates
        cfg.llm_provider = "offline"
        print("ℹ️  offline mode: built-in fact bank + template scripts (no LLM calls)")

    async def run():
        from factshorts.pipeline import generate_and_render, pipeline_summary
        from factshorts.publish import publish_video, summary_text

        def progress(stage: str) -> None:
            print(f"   • {stage}")

        async def aprogress(stage: str) -> None:
            progress(stage)

        result = await generate_and_render(niche=niche, progress=aprogress, forced_topic=topic)
        print("\n" + pipeline_summary(result))
        print(f"\n🎬 {result.path}  ({result.duration:.2f}s, {result.clip_count} clips)")
        if upload:
            results = await publish_video(result.video_id, platforms=platforms, privacy=privacy, dry_run=dry_run)
            print(summary_text(results))
            if all(r.get("error") for r in results.values()):
                return 1
        else:
            print(f"ℹ️  approve/upload later with: python main.py --upload {result.video_id}")
        return 0

    return asyncio.run(run())


def cmd_upload(video_id: int, privacy: str | None, dry_run: bool, platforms: list[str] | None = None) -> int:
    """Upload/publish an existing render to one or more platforms."""
    from factshorts.publish import publish_video, summary_text

    results = asyncio.run(publish_video(video_id, platforms=platforms, privacy=privacy, dry_run=dry_run))
    print(summary_text(results))
    return 0 if any(not r.get("error") for r in results.values()) else 1


def cmd_autonomous(upload: bool = False) -> int:
    """100% Autonomous loop: Scout -> Script -> Visual -> Audio -> SEO -> Publish -> Learn."""
    from factshorts.autopilot import AutonomousStudio

    studio = AutonomousStudio()
    result = asyncio.run(studio.run_cycle(upload=upload))
    report = studio.format_eod_report(result)
    print("\n" + report + "\n")
    return 0


def cmd_eod_report() -> int:
    """Displays latest autonomous learning insights and next move proposal."""
    from factshorts.autopilot import AutonomousStudio

    studio = AutonomousStudio()
    memory = studio.memory
    proposal = memory.propose_next_move()
    recent = memory.data.get("history") or []
    last = recent[-1] if recent else {}
    mock_rep = {
        "title": last.get("topic", "N/A"),
        "video_path": last.get("video_path", "N/A"),
        "chosen_topic": last.get("topic", "N/A"),
        "pillar": last.get("pillar", proposal.get("current_pillar")),
        "niche": proposal.get("current_pillar"),
        "opportunity_score": last.get("opportunity_score", 90),
        "duration": 15.0,
        "uploaded": False,
        "next_move_proposal": proposal,
    }
    print("\n" + studio.format_eod_report(mock_rep) + "\n")
    return 0


def cmd_trends(geo: str | None, niche: str | None) -> int:
    """Show what is trending right now (Google Trends + Wikipedia)."""
    from factshorts.trends import list_trends

    data = asyncio.run(list_trends(geo, niche or ""))
    for label, items in data.items():
        print(f"\n=== {label} ===")
        if not items:
            print("  (nothing usable right now)")
        for seed in items[:12]:
            traffic = seed.extra.get("traffic") or seed.extra.get("views") or ""
            print(f"  • {seed.title[:75]:75s} {traffic}")
    return 0


def cmd_publish_info() -> int:
    """Show platform readiness + Instagram quota."""
    from factshorts.publish import instagram_status, platform_health, platforms_from_setting

    async def run():
        print("platforms:", ", ".join(platforms_from_setting()))
        for name, state in platform_health().items():
            print(f"  {name:10s} {state}")
        ig = await instagram_status()
        if ig:
            print(" ", ig)

    asyncio.run(run())
    return 0


def cmd_script_test(niche: str | None) -> int:
    """Offline sanity check of topic -> script -> SEO (no rendering)."""

    async def run():
        from factshorts.llm import LLM
        from factshorts.script_writer import write_script
        from factshorts.seo import build_seo
        from factshorts.topic_engine import generate_topic

        cfg = get_config()
        llm = LLM(cfg)
        topic = await generate_topic(niche=niche, llm=llm, cfg=cfg)
        print(f"TOPIC  [{topic.source}] {topic.topic}\nFACT   {topic.fact}\n")
        script = await write_script(topic, llm=llm, cfg=cfg)
        print(f"HOOK   {script.hook}\nBODY   {script.body}\nCLOSE  {script.closing}")
        print(f"WORDS  {script.word_count}\nKEYWORDS {script.visual_keywords()}")
        seo = await build_seo(topic, script, llm=llm, cfg=cfg)
        print(f"\nTITLE  {seo['title']}  ({len(seo['title'])} chars)")
        print(f"TAGS   {', '.join(seo['tags'])}")
        print(f"PIN    {seo['pinned_comment']}\n\nDESCRIPTION\n{seo['description']}")
        await llm.aclose()

    asyncio.run(run())
    return 0


def cmd_demo(topic: str | None = None) -> int:
    """No-API demo: offline fact bank + free Wikimedia/Commons footage + full render."""
    cfg = get_config()
    cfg.test_mode = True
    cfg.llm_provider = "offline"
    stock = sorted((cfg.assets_dir / "stock").glob("*.mp4"))
    if stock:
        # the demo library downloaded by scripts/fetch_demo_footage.py is curated, so use it first
        cfg.footage_providers = ["local"] + [p for p in cfg.footage_providers if p != "local"]
        print(f"ℹ️  {len(stock)} clips in assets/stock/ - using them first")

    async def run():
        from factshorts.pipeline import generate_and_render

        def progress(stage: str) -> None:
            print(f"   • {stage}")

        async def aprogress(stage: str) -> None:
            progress(stage)

        result = await generate_and_render(niche=cfg.niche, cfg=cfg, progress=aprogress, forced_topic=topic)
        print(f"\n🎬 demo render: {result.path} ({result.duration:.2f}s)")
        return result

    return 0 if asyncio.run(run()) else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="FactShorts Bot", formatter_class=argparse.RawDescriptionHelpFormatter,
                                     epilog=__doc__)
    parser.add_argument("--check", action="store_true", help="environment/config health check")
    parser.add_argument("--selftest", action="store_true", help="tiny offline test render")
    parser.add_argument("--auth", action="store_true", help="YouTube OAuth consent flow")
    parser.add_argument("--generate", action="store_true", help="generate + render one video now")
    parser.add_argument("--demo", action="store_true", help="offline demo render (no API keys)")
    parser.add_argument("--script-test", action="store_true", help="topic/script/SEO dry run (no render)")
    parser.add_argument("--upload", type=int, metavar="VIDEO_ID", help="publish an existing render by id")
    parser.add_argument("--platforms", default=None, help="comma separated: youtube,instagram")
    parser.add_argument("--trends", action="store_true", help="show what is trending (Google Trends + Wikipedia)")
    parser.add_argument("--trends-geo", default=None, help="trend region, e.g. IN or US")
    parser.add_argument("--platform-status", action="store_true", help="platform readiness + Instagram quota")
    parser.add_argument("--niche", default=None, help=f"one of: {', '.join(NICHES)}")
    parser.add_argument("--mode", default=None, choices=["facts", "story"],
                        help="facts = 10-15s single fact, story = ~60s story (this run only; "
                             "/mode in Telegram or VIDEO_MODE in .env is persistent)")
    parser.add_argument("--topic", default=None, help="force a specific topic (matches the offline bank, else hints the LLM)")
    parser.add_argument("--brief", default=None, help="ReelForge mode: 1 brief = 1 full video (e.g. --brief 'Why time slows down near black holes')")
    parser.add_argument("--offline", action="store_true", help="use the offline fact bank instead of the LLM")
    parser.add_argument("--privacy", default=None, choices=["public", "unlisted", "private"])
    parser.add_argument("--dry-run", action="store_true", help="do everything except the real upload")
    parser.add_argument("--bot", action="store_true", help="run the Telegram bot + scheduler")
    parser.add_argument("--daemon", action="store_true", help="run the scheduler only (no bot)")
    parser.add_argument("--autonomous", action="store_true", help="100% autonomous mode: AI selects niche, discovers topic, produces video, and learns")
    parser.add_argument("--eod-report", action="store_true", help="display latest autonomous learning telemetry & EOD report")
    args = parser.parse_args(argv)

    if args.brief:
        args.generate = True
        args.topic = args.brief

    setup_logging()
    db.init_db()

    if args.mode:
        # per-run override; the persistent switch lives in SQLite (Telegram /mode)
        os.environ["VIDEO_MODE"] = args.mode
        from factshorts.config import get_config as _gc

        _gc(refresh=True)  # the config snapshot may already have been built at import time

    if args.check:
        return cmd_check()
    if args.selftest:
        return cmd_selftest()
    if args.auth:
        return cmd_auth()
    if args.script_test:
        return cmd_script_test(args.niche)
    if args.demo:
        return cmd_demo(args.topic)
    if args.generate:
        platforms = [p.strip().lower() for p in args.platforms.split(",")] if args.platforms else None
        return cmd_generate(args.niche, args.offline or args.demo, bool(args.upload), args.privacy,
                            args.dry_run, topic=args.topic, platforms=platforms)
    if args.upload:
        platforms = [p.strip().lower() for p in args.platforms.split(",")] if args.platforms else None
        return cmd_upload(args.upload, args.privacy, args.dry_run, platforms)
    if args.trends:
        return cmd_trends(args.trends_geo, args.niche)
    if args.platform_status:
        return cmd_publish_info()
    if args.bot:
        from factshorts.bot import run

        run()
        return 0
    if args.daemon:
        from factshorts.scheduler import run_forever

        run_forever()
        return 0
    if args.autonomous:
        return cmd_autonomous(upload=bool(args.upload))
    if args.eod_report:
        return cmd_eod_report()

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
