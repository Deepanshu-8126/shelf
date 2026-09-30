"""Generate a viral fact video using the 100% free AI stack and send directly to Telegram."""
import asyncio
import os
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import httpx

from factshorts import db
from factshorts.config import get_config
from factshorts.pipeline import generate_and_render
from factshorts.utils import human_bytes


async def progress_printer(msg: str):
    print(f"⚡ [PIPELINE] {msg}")


async def main():
    cfg = get_config()
    db.init_db()

    # Pick a viral, high-retention topic
    viral_topics = [
        ("psychology", "The Baader-Meinhof Phenomenon: Why you suddenly see something everywhere"),
        ("space", "Gravitational Time Dilation: Why time slows down near supermassive black holes"),
        ("science", "The Immortal Jellyfish: The only creature on Earth that can reset its age to zero"),
        ("history", "The Lost Library of Alexandria: The greatest knowledge catastrophe in human history"),
    ]

    import random
    niche, topic = random.choice(viral_topics)
    print("=" * 60)
    print(f"🎬 STARTING FACT GENERATION: [{niche.upper()}]")
    print(f"📌 Topic: {topic}")
    print(f"⚡ Connected Kaggle GPU: {cfg.gpu_worker_url or 'Offline (CPU mode)'}")
    print(f"🎙️ Voice: {cfg.voice_provider}")
    print("=" * 60)

    result = await generate_and_render(
        niche=niche,
        forced_topic=topic,
        progress=progress_printer,
        cfg=cfg,
    )

    print("\n" + "=" * 60)
    print(f"✅ RENDER COMPLETE: {result.path}")
    print(f"⏱️ Duration: {result.duration:.2f}s | Size: {human_bytes(result.path.stat().st_size)}")
    print(f"📝 Title: {result.seo.get('title')}")
    print("=" * 60)

    # Send video directly to user's Telegram
    print("\n📤 Uploading video to Telegram phone...")
    caption = (
        f"🔥 {result.seo.get('title')}\n\n"
        f"📊 Duration: {result.duration:.1f}s | Clips: {result.clip_count}\n"
        f"🎙️ Voice: Kokoro-82M (100% Free Open-Source)\n"
        f"✨ Captions: Dynamic Animated ASS Highlights\n\n"
        f"📝 Description:\n{result.seo.get('description', '')[:300]}...\n\n"
        f"🏷️ Tags: {', '.join(result.seo.get('tags', [])[:5])}"
    )

    from factshorts.telegram_notify import TelegramNotifier
    notifier = TelegramNotifier(cfg)
    tg_resp = await notifier.send_video(result.path, caption=caption)
    if tg_resp and tg_resp.get("ok"):
        print(">> VIDEO DELIVERED TO TELEGRAM SUCCESSFULLY!")
    else:
        print(f"Telegram upload result: {tg_resp}")
    await notifier.aclose()


if __name__ == "__main__":
    asyncio.run(main())
