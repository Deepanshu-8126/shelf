#!/usr/bin/env python3
"""
==============================================================================
🤖 24/7 LIVE TELEGRAM CONTROLLER FOR SHELF STORE (@Bbyjihotbot)
==============================================================================
Controls Google Flow / Veo 3.1 & Meesho Affiliate Pipeline directly from your phone:
- Send any Meesho URL -> Bot auto-generates 4K full-motion Veo video + affiliate link
- Type /trending -> Auto-picks 15-18% high commission viral fashion deals
- Type /unboxing <product> -> POV unboxing video
- Type /tryon <product> -> Model motion showcase video
==============================================================================
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

# Ensure root and studio_engines in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
STUDIO_DIR = PROJECT_ROOT / "studio_engines"
if str(STUDIO_DIR) not in sys.path:
    sys.path.insert(0, str(STUDIO_DIR))

# Load .env
env_file = PROJECT_ROOT / ".env"
if env_file.exists():
    for line in env_file.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

from connectors.telegram_video_bot import TelegramVideoBot

if __name__ == "__main__":
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "8564017881:AAGgH4xtjjOZYdyVG6CfNT86i-7t1s9ob7c")
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "6486771356")
    
    bot = TelegramVideoBot(bot_token=bot_token, chat_id=chat_id)
    print("=" * 65)
    print("🤖 SHELF STORE TELEGRAM CONTROLLER IS NOW 24/7 LIVE!")
    print(f"📱 Bot: @Bbyjihotbot | Chat ID: {chat_id}")
    print("=" * 65)
    
    bot.start_polling_loop()
