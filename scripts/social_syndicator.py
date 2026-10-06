"""
Dual Social Syndicator (Instagram Reels + Pinterest Daily Batch Auto-Publisher).
Synchronizes all generated creator videos, Pinterest collages, and try-on photos across both platforms.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Dict, Any, List

root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from core.logging_utils import get_logger
from connectors.instagram_auto_poster import InstagramAutoPoster
from connectors.pinterest_auto_poster import PinterestAutoPoster
from connectors.telegram_video_bot import TelegramVideoBot

log = get_logger("social_syndicator")


class SocialSyndicator:
    def __init__(self):
        self.insta = InstagramAutoPoster()
        self.pinterest = PinterestAutoPoster()
        self.telegram = TelegramVideoBot()

    def syndicate_video_and_photos(
        self,
        video_path: Path | str,
        product_name: str,
        storefront_url: str | None = None
    ) -> Dict[str, Any]:
        """
        Publishes the video reel and prepares the 10-15 photo pins for Pinterest & Instagram.
        """
        v_path = Path(video_path)
        log.info("🌐 [Syndicator] Initiating cross-platform syndication for: %s", product_name)

        caption = (
            f"✨ Look at this viral {product_name}! Perfect fit for college, date nights & everyday chic! "
            f"Comment 'LINK' or tap the bio link to shop the verified deal! 🛍️❤️\n\n"
            f"#meeshohaul #pinterestoutfits #tryonhaul #bodycondress #meeshofinds #under500 #aestheticinspo"
        )

        # 1. Instagram Auto-Publish
        insta_res = self.insta.publish_reel(v_path, caption=caption)

        # 2. Pinterest Daily Batch of 12 Pins
        pin_batch = self.pinterest.batch_generate_daily_pins(
            product_title=product_name,
            num_pins=12
        )

        # 3. Deliver to Telegram
        tg_caption = (
            f"🚀 *CROSS-PLATFORM SYNDICATION COMPLETE*\n\n"
            f"👗 *Product:* {product_name}\n"
            f"📸 *Instagram Reel:* Ready / Published\n"
            f"📌 *Pinterest Pins:* 12 Daily Aesthetic Pins Queued\n"
            f"🔗 *Storefront:* {storefront_url or self.pinterest.storefront_url}\n\n"
            f"✨ Video features: Real try-on + Star pop-up + Tring chime audio!"
        )
        self.telegram.send_message(tg_caption)

        return {
            "instagram": insta_res,
            "pinterest_batch_count": len(pin_batch),
            "status": "success"
        }


if __name__ == "__main__":
    syndicator = SocialSyndicator()
    video_test = root_dir / "data" / "veo_extracted_videos" / "FLOW_VEO_AFFILIATE_STAR_POPUP.mp4"
    if video_test.exists():
        res = syndicator.syndicate_video_and_photos(video_test, "Women Solid Long Sleeve Bodycon Maxi Dress")
        print("Syndication result:", res)
