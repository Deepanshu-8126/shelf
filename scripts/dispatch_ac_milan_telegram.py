import os
import sys
import json
import urllib.request
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).resolve().parent.parent

TELEGRAM_BOT_TOKEN = "8564017881:AAGgH4xtjjOZYdyVG6CfNT86i-7t1s9ob7c"
TELEGRAM_CHAT_ID = "6486771356"

product_data = {
    "title": "Embroidery AC Milan Maldini 3 Retro Football Jersey (Classic White)",
    "price": 499,
    "old_price": 1499,
    "discount": "67% OFF",
    "rating": "4.8 ★",
    "ext_id": "i7s47c",
    "category": "Retro Football / Gen-Z Streetwear",
    "affiliate_url": "https://www.meesho.com/af_invite/374453404:youtube_long_form:12492338?ext_id=i7s47c&utm_source=instagram_reels",
    "veo_prompt": (
        "A vertical 9:16 cinematic 4K 60fps editorial fashion reel. "
        "A stylish 21-year-old Indian creator model with subtle athletic build wearing the authentic AC Milan 2007 White Retro Football Jersey with embroidered crest on chest and crisp red 'MALDINI 3' lettering on the back, paired with relaxed baggy vintage dark wash denim jeans and clean white retro sneakers. "
        "The model walks smoothly into a sunlit European-style loft studio with warm golden hour sunlight casting soft shadows. "
        "The camera executes a dynamic low-angle slow-motion tracking shot, panning smoothly across the embroidered Milan badge and breathable fabric mesh texture, "
        "then the model turns around effortlessly with a confident smile, showcasing the iconic 'MALDINI 3' back print. "
        "35mm film grain, 60fps fluid motion, natural skin texture, realistic cloth simulation and physics, shallow depth of field, high-fashion street style aesthetic."
    ),
    "viral_caption": (
        "POV: You found the holy grail AC Milan Maldini 3 Retro Jersey on Meesho for just ₹499 ⚽🔥✨\n\n"
        "Quality: Heavy breathable sports mesh with authentic embroidered badge & crisp Maldini 3 back print! Styled this with baggy denim and it’s a whole 10/10 fit 🤌\n\n"
        "💰 Price: ₹499 (MRP: ₹1499 · 67% OFF)\n"
        "🔗 Tap the link in bio / comment 'LINK' to get direct shop invite!\n\n"
        "#acmilan #maldini #retrojersey #footballjersey #streetwearindia #meeshofinds #meeshomusthaves #blockecore #y2kstreetwear #vintagejersey #jerseyoutfit #aestheticoutfits #mensfashionindia #genzfashion #affiliatemarketing"
    )
}

# Save output
out_dir = PROJECT_ROOT / "data" / "reels_output"
out_dir.mkdir(parents=True, exist_ok=True)
(out_dir / "ac_milan_maldini_reel.json").write_text(json.dumps(product_data, indent=2), encoding="utf-8")

# Send to Telegram Bot
tg_msg = (
    "⚽ *GOOGLE VEO 3.1 & FLOW STUDIO REEL PIPELINE*\n\n"
    f"📌 *Product:* {product_data['title']}\n"
    f"💰 *Price:* ₹{product_data['price']} (MRP: ₹{product_data['old_price']} · {product_data['discount']})\n"
    f"⭐ *Rating:* {product_data['rating']} · Category: {product_data['category']}\n\n"
    f"🔗 *Creator Affiliate Invite Link:*\n{product_data['affiliate_url']}\n\n"
    "🎬 *Google Veo 3.1 4K 60fps Prompt (Locked & Queued):*\n"
    f"_{product_data['veo_prompt']}_\n\n"
    "📝 *Viral Caption:*\n"
    f"{product_data['viral_caption']}\n\n"
    "⚡ _Status: Flow Studio Generation Queued & Dispatched to @Bbyjihotbot!_"
)

url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
req = urllib.request.Request(
    url,
    data=json.dumps({
        "chat_id": TELEGRAM_CHAT_ID,
        "text": tg_msg,
        "parse_mode": "Markdown"
    }).encode("utf-8"),
    headers={"Content-Type": "application/json"}
)

with urllib.request.urlopen(req) as resp:
    print(f"[✓] Successfully delivered live update to Telegram Bot (@Bbyjihotbot)! HTTP Status: {resp.status}")
