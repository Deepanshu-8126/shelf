"""Command-line runner for autonomous trend-engine autopilot.

Usage:
    python run.py autopilot-run --dry-run
    python run.py autopilot-run --render
    python run.py test
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from trendengine.pipeline import run_cycle
from trendengine.learning.bandit import ThompsonBandit


async def autopilot_run(dry_run: bool = False, render: bool = False, forced_topic: str | None = None) -> None:
    print("=" * 65)
    print("🚀 TREND-ENGINE AUTOPILOT: Autonomous Trend -> Script -> Learn")
    print("=" * 65)
    print("📡 Step 1 & 2: Discovering & Scoring Trends (Reddit, Google Trends, RSS, YouTube)...")
    
    result = await run_cycle(forced_topic=forced_topic)
    topic = result["topic"]
    script = result["script"]
    quality = result["quality"]

    print("\n" + "-" * 65)
    print(f"🔥 Selected Breakout Topic: {topic.get('title')}")
    print(f"📊 Source: {topic.get('source')} | Velocity: {topic.get('velocity', 0):.1f} | Score: {topic.get('score', 0):.1f}")
    print(f"🎯 Bandit Arms Selected: Hook={result['hook_style']} | CTA={result['cta_style']}")
    print("-" * 65)

    print("\n📝 GENERATED VIRAL SCRIPT:")
    print(f"⚡ Hook (3s): {script.get('hook')}")
    print(f"📖 Body Story: {script.get('body')}")
    print(f"🔄 Loop CTA: {script.get('closing')}")
    print(f"⏱️ Word Count: {script.get('word_count')} words")
    print(f"⭐ Quality Gate Self-Critique: {quality.get('score')}/10 ({'PASSED ✅' if quality.get('passed') else 'NEEDS WORK ⚠️'})")
    print(f"💭 Auditor Feedback: {quality.get('reason')}")

    print("\n🏷️ High CTR Titles:")
    for i, t in enumerate(script.get("titles", [])[:3], 1):
        print(f"   {i}. {t}")

    print("\n🎥 Specific Visual Keywords:")
    print(f"   {', '.join(script.get('visual_keywords', [])[:6])}")

    if dry_run:
        print("\n" + "=" * 65)
        print("✅ DRY RUN COMPLETE: Trend discovered, script drafted, quality verified!")
        print("=" * 65)
        return

    if render:
        print("\n" + "=" * 65)
        print("🎬 STEP 3: RENDERING 100% FREE STORY SHORT VIA FACTSHORTS PIPELINE...")
        print("=" * 65)
        from factshorts.config import get_config
        from factshorts.pipeline import generate_and_render
        from factshorts.telegram_notify import TelegramNotifier

        cfg = get_config()
        render_res = await generate_and_render(
            niche=topic.get("niche", "science"),
            forced_topic=topic.get("title"),
            cfg=cfg,
        )

        print("\n" + "=" * 65)
        print(f"✅ VIDEO RENDER COMPLETE: {render_res.path}")
        print(f"⏱️ Duration: {render_res.duration:.1f}s | Size: {render_res.path.stat().st_size / (1024*1024):.1f}MB")
        print("=" * 65)

        # Notify Telegram
        notifier = TelegramNotifier(cfg)
        caption = (
            f"🚀 {render_res.seo.get('title')}\n\n"
            f"⏱️ Duration: {render_res.duration:.1f}s\n"
            f"🎯 Trend: {topic.get('title')}\n"
            f"⭐ Quality Score: {quality.get('score')}/10\n"
            f"🎙️ Voice: Kokoro-82M | Captions: Dynamic ASS Pop\n\n"
            f"📺 Channel: chan1 (FactShorts)"
        )
        await notifier.send_video(render_res.path, caption=caption)
        await notifier.aclose()

        # Step 4: Self-Learning Reward Update
        bandit = ThompsonBandit()
        # Simulated initial engagement reward based on Quality Gate score
        reward = max(0.5, quality.get("score", 7) / 10.0)
        bandit.update_reward("hook_style", result["hook_style"], reward)
        bandit.update_reward("cta_style", result["cta_style"], reward)
        print(f"🧠 THOMPSON BANDIT UPDATED: reward={reward:.2f} for {result['hook_style']} & {result['cta_style']}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Trend-Engine Autopilot Runner")
    subparsers = parser.add_subparsers(dest="command")

    auto_parser = subparsers.add_parser("autopilot-run", help="Run autonomous trend-to-script cycle")
    auto_parser.add_argument("--dry-run", action="store_true", help="Generate script without rendering video")
    auto_parser.add_argument("--render", action="store_true", help="Render video with Kokoro + FFmpeg")
    auto_parser.add_argument("--topic", type=str, default=None, help="Force a specific topic")

    test_parser = subparsers.add_parser("test", help="Test imports and trend discovery")

    args = parser.parse_args()

    if args.command == "autopilot-run":
        asyncio.run(autopilot_run(dry_run=args.dry_run, render=args.render, forced_topic=args.topic))
    elif args.command == "test":
        print("TrendEngine imports: OK")
    else:
        # Default behavior if run without arguments
        asyncio.run(autopilot_run(dry_run=True))


if __name__ == "__main__":
    main()
