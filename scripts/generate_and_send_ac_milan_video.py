import os
import sys
import json
import urllib.request
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
STUDIO_DIR = PROJECT_ROOT / "studio_engines"
if str(STUDIO_DIR) not in sys.path:
    sys.path.insert(0, str(STUDIO_DIR))

from connectors.universal_meesho_engine import UniversalMeeshoEngine
from connectors.telegram_video_bot import TelegramVideoBot

def main():
    print("=== Generating 1080x1920 60fps Video Reel for AC Milan Maldini 3 Jersey ===")
    
    url = "https://www.meesho.com/embroidery-ac-milan-maldini-3-retro-football-jersey-classic-white-short-sleeve-soccer-shirt/p/i7s47c"
    
    engine = UniversalMeeshoEngine()
    
    # Generate video reel with watermark removal, Ken Burns 60fps motion, and DM FOR LINK badge
    res = engine.process_universal_product(url)
    
    print(f"[✓] Video Created Successfully: {res.get('video_path')}")
    
    # Telegram Dispatch
    video_file = Path(res["video_path"])
    caption = (
        "⚽ *AC MILAN RETRO MALDINI 3 JERSEY (4K REEL READY)*\n\n"
        f"📦 *Product:* {res['title']}\n"
        f"💰 *Price:* ₹499 (MRP: ₹1,499 · 67% OFF)\n"
        "⭐ *Rating:* 4.8 ★ | Free Delivery\n\n"
        "🔗 *Creator Affiliate Invite Link:*\n"
        "https://www.meesho.com/af_invite/374453404:youtube_long_form:12492338?ext_id=i7s47c&utm_source=instagram_reels\n\n"
        "👉 *Call To Action:* Comment 'LINK' to get secret shop invite!\n\n"
        "⚡ _100% Watermark-Free 1080x1920 60fps Reel_"
    )
    
    bot = TelegramVideoBot()
    print(f"[*] Uploading video file ({video_file.stat().st_size // 1024} KB) directly to Telegram Bot (@Bbyjihotbot)...")
    success = bot.send_video_file(video_file, caption=caption)
    
    if success:
        print("[✓] Video Reel successfully delivered to your Telegram Phone Bot!")
    else:
        print("[!] Video saved locally.")

if __name__ == "__main__":
    main()
