"""
Autonomous UGC Fashion & Girls Outfit Unboxing Studio (Google Veo & Gemini Pro).
Generates exact Pinterest / Instagram viral UGC video format:
1. POV Real Hands opening delivery package & unfolding clothing fabric
2. Picture-in-Picture Model Try-On inset in bottom-right corner
3. Aesthetic Top Typography ('Gothic Chic Unboxing ✨', 'Meesho Kurti Haul 🌸')
4. Zero Watermarks / Logos (clean 1080x1920 60fps MP4)
5. ASMR Parcel Crinkle & Trending Background Audio
"""
from __future__ import annotations

import json
import os
import random
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from PIL import Image, ImageDraw, ImageFont

from core.logging_utils import get_logger

log = get_logger("ugc_fashion_unboxer")


def _get_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    font_names = [
        "georgiab.ttf" if bold else "georgia.ttf",
        "arialbd.ttf" if bold else "arial.ttf",
        "tahomabd.ttf" if bold else "tahoma.ttf",
    ]
    for fn in font_names:
        try:
            return ImageFont.truetype(fn, size)
        except Exception:
            continue
    return ImageFont.load_default()


VIRAL_FASHION_CATALOG = [
    {
        "title": "Gothic Chic Spiderweb Mesh Top",
        "niche": "Y2K & Grunge Aesthetic Outfits",
        "headline": "Gothic Chic Unboxing ✨",
        "mrp": "₹1,299",
        "sale_price": "₹349",
        "discount": "73% OFF",
        "fabric": "Sheer black stretchable spiderweb mesh",
        "packaging": "Silver metallic courier parcel",
        "unboxing_script": "POV hands with nude manicured nails tearing open the silver courier parcel, pulling out the sheer spiderweb mesh top, unfolding the delicate fabric against warm daylight, and showing off the collar and sleeve details.",
        "model_look": "Asian model with sleek dark hair and winged eyeliner wearing the spiderweb mesh top with high-waisted black jeans against a clean white studio background",
        "hook": "Meesho Gothic Mesh Top under ₹350! Quality and stretch is literally 10/10 ✨ Link in Bio!"
    },
    {
        "title": "Floral Anarkali Cotton Kurti Set",
        "niche": "Ethnic Wear & Festive Haul",
        "headline": "Meesho Kurti Set Haul 🌸",
        "mrp": "₹2,499",
        "sale_price": "₹699",
        "discount": "72% OFF",
        "fabric": "Pure cotton printed with pink floral motifs and gold lace border",
        "packaging": "Transparent sealed brand polybag",
        "unboxing_script": "POV hands holding delivery bag, gently sliding out the folded floral kurti, unfolding the full flare to reveal the rich printed dupatta and pants in natural room light.",
        "model_look": "Indian model wearing the pastel floral kurti set with jhumkas and minimal makeup in a bright aesthetically lit room",
        "hook": "Ye ₹699 ka viral Meesho kurti set looks exactly like a ₹3,000 designer piece! Dupatta fabric is pure magic 🌸 Link in Bio!"
    },
    {
        "title": "Korean Oversized Knit Cardigan",
        "niche": "Pastel Cozy Streetwear",
        "headline": "Cozy Autumn Unboxing ☕",
        "mrp": "₹1,899",
        "sale_price": "₹549",
        "discount": "71% OFF",
        "fabric": "Chunky soft pastel beige ribbed knit wool",
        "packaging": "Frosted ziplock apparel pouch",
        "unboxing_script": "POV hands unzipping frosted pouch with satisfying ASMR sound, pulling out the chunky knit sweater, touching the ultra-soft wool texture, and displaying the tortoiseshell buttons.",
        "model_look": "Gen Z creator wearing the oversized beige cardigan over a white crop top and pleated tennis skirt",
        "hook": "The softest Pinterest cardigan for college outfits! Under ₹550 only ☕ Link in Bio!"
    }
]


class UGCFashionUnboxingStudio:
    """Produces authentic, high-converting UGC Outfit Unboxing Reels with Model Try-on Inset."""

    def __init__(self, output_dir: Path | str | None = None):
        if output_dir:
            self.output_dir = Path(output_dir)
        else:
            self.output_dir = Path(__file__).resolve().parent.parent / "data" / "ugc_fashion_videos"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_ugc_veo_prompt(self, item: dict[str, Any]) -> str:
        """Constructs ultra-detailed Google Veo / Gemini Pro unboxing prompt."""
        prompt = (
            f"Hyper-realistic 4K 60fps POV camera perspective of an authentic UGC unboxing of {item['title']}. "
            f"Main Visual: {item['unboxing_script']}. "
            f"Natural studio/bedroom daylight, realistic tactile fabric physics, real human skin textures with zero plastic look. "
            f"Bottom-Right Inset: Picture-in-picture card showing a {item['model_look']}. "
            f"Top Overlay: Elegant aesthetic typography reading '{item['headline']}'. "
            f"Zero watermarks, zero Gemini logos, clean vertical 9:16 aspect ratio."
        )
        return prompt

    def render_ugc_composite_frame(self, item: dict[str, Any], bg_unboxing_img: Path | None = None, model_inset_img: Path | None = None) -> Path:
        """Renders 1080x1920 UGC video frame with Real Hands Unboxing + Model Inset + Headline."""
        w, h = 1080, 1920
        canvas = Image.new("RGBA", (w, h), (22, 20, 24, 255))
        draw = ImageDraw.Draw(canvas)

        # 1. Base Layer: POV Unboxing Scene (Realistic daylight room gradient if no raw frame)
        for y in range(0, h, 6):
            ratio = y / h
            r = int(140 - 40 * ratio)
            g = int(135 - 35 * ratio)
            b = int(130 - 30 * ratio)
            draw.rectangle([0, y, w, y + 6], fill=(r, g, b, 255))

        # Draw Simulated Real Hands & Unboxing Package in Center
        # Package shadow
        draw.rounded_rectangle([180, 480, 900, 1380], radius=18, fill=(80, 75, 70, 180))
        # Courier Bag
        draw.rounded_rectangle([160, 460, 880, 1350], radius=20, fill=(235, 230, 225, 255), outline=(200, 195, 190, 255), width=2)
        # Barcode sticker on bag
        draw.rectangle([200, 500, 440, 620], fill=(255, 255, 255, 255))
        draw.text((220, 520), "EXP-AIR-TRACK\n||||| |||| ||||||", fill=(0, 0, 0, 255), font=_get_font(18, bold=True))

        # Unfolded Fabric Showcase
        draw.rounded_rectangle([220, 660, 820, 1280], radius=16, fill=(50, 40, 45, 255))
        draw.text((520, 940), f"✨ {item['title']}\n{item['fabric']}", fill=(240, 230, 235, 255), font=_get_font(26, bold=True), anchor="mm")

        # 2. Bottom-Right Picture-in-Picture Model Try-on Card
        # Card shadow & border
        inset_x, inset_y, inset_w, inset_h = 560, 920, 480, 900
        draw.rounded_rectangle([inset_x - 8, inset_y - 8, inset_x + inset_w + 8, inset_y + inset_h + 8], radius=28, fill=(0, 0, 0, 140))
        draw.rounded_rectangle([inset_x, inset_y, inset_x + inset_w, inset_y + inset_h], radius=24, fill=(30, 28, 32, 255), outline=(255, 255, 255, 220), width=3)

        # Model silhouette / Try-on preview with REAL reference image if provided
        inset_content_drawn = False
        if model_inset_img and Path(model_inset_img).exists():
            try:
                raw_inset = Image.open(model_inset_img).convert("RGBA")
                target_w = inset_w - 24
                target_h = inset_h - 24
                aspect = target_w / target_h
                img_aspect = raw_inset.width / raw_inset.height
                if img_aspect > aspect:
                    new_w = int(raw_inset.height * aspect)
                    left = (raw_inset.width - new_w) // 2
                    raw_inset = raw_inset.crop((left, 0, left + new_w, raw_inset.height))
                else:
                    new_h = int(raw_inset.width / aspect)
                    top = (raw_inset.height - new_h) // 2
                    raw_inset = raw_inset.crop((0, top, raw_inset.width, top + new_h))

                raw_inset = raw_inset.resize((target_w, target_h), Image.Resampling.LANCZOS)
                mask = Image.new("L", (target_w, target_h), 0)
                mask_draw = ImageDraw.Draw(mask)
                mask_draw.rounded_rectangle([0, 0, target_w, target_h], radius=18, fill=255)

                canvas.paste(raw_inset, (inset_x + 12, inset_y + 12), mask)
                # Subtle overlay gradient at bottom of try-on card for price
                draw.rounded_rectangle([inset_x + 20, inset_y + target_h - 75, inset_x + target_w + 4, inset_y + target_h + 4], radius=12, fill=(0, 0, 0, 210))
                draw.text((inset_x + target_w // 2 + 12, inset_y + target_h - 40), f"👗 TRY-ON • {item.get('sale_price', 'SALE')}", fill=(255, 255, 255, 255), font=_get_font(22, bold=True), anchor="mm")
                inset_content_drawn = True
            except Exception as e:
                log.warning("Could not composite real model inset: %s", e)

        if not inset_content_drawn:
            draw.rounded_rectangle([inset_x + 12, inset_y + 12, inset_x + inset_w - 12, inset_y + inset_h - 12], radius=18, fill=(45, 38, 48, 255))
            draw.text((inset_x + inset_w // 2, inset_y + 360), f"👗 TRY-ON LOOK\n\n{item['title'][:20]}\n\n⭐ 4.8 / 5.0\nSALE: {item.get('sale_price', '₹499')}", fill=(255, 240, 245, 255), font=_get_font(24, bold=True), anchor="mm")

        # 3. Top Aesthetic Gothic / Chic Headline
        # Text with black outline & drop shadow for viral visibility
        headline = item.get('headline', 'Aesthetic Unboxing ✨')
        font_title = _get_font(56, bold=True)
        # Drop shadow
        draw.text((542, 202), headline, fill=(0, 0, 0, 200), font=font_title, anchor="mm")
        draw.text((540, 200), headline, fill=(255, 255, 255, 255), font=font_title, anchor="mm")

        # Subtitle Price & Discount Badge
        discount_text = f"🔥 {item.get('discount', '70% OFF')} • ONLY {item.get('sale_price', '₹499')}"
        draw.rounded_rectangle([300, 260, 780, 320], radius=16, fill=(244, 63, 94, 255))
        draw.text((540, 290), discount_text, fill=(255, 255, 255, 255), font=_get_font(24, bold=True), anchor="mm")

        slug = item['title'][:15].lower().replace(" ", "_")
        out_frame = self.output_dir / f"ugc_frame_{slug}.png"
        canvas.convert("RGB").save(out_frame, format="PNG", quality=95)
        return out_frame

    def render_aesthetic_header_banner(self, item: dict[str, Any], out_path: Path) -> Path:
        """Renders ultra-crisp frosted aesthetic header card covering any background artifacts."""
        w, h = 1080, 1920
        banner = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(banner)

        # Clean headline without unicode emoji fallback glitches
        raw_head = item.get("headline", "Meesho Viral Outfit").replace("✨", "").replace("🌸", "").replace("☕", "").strip()
        headline = raw_head.upper()
        font_title = _get_font(44, bold=True)

        # Frosted glass card backing (cleanly hides any background text)
        card_x1, card_y1, card_x2, card_y2 = 40, 80, 1040, 420
        draw.rounded_rectangle([card_x1 - 4, card_y1 - 4, card_x2 + 4, card_y2 + 4], radius=26, fill=(0, 0, 0, 180))
        draw.rounded_rectangle([card_x1, card_y1, card_x2, card_y2], radius=24, fill=(14, 12, 18, 250), outline=(255, 255, 255, 220), width=3)

        # Header Title
        draw.text((w // 2, 195), headline, fill=(255, 255, 255, 255), font=font_title, anchor="mm")

        # Discount & Price Pill
        disc = item.get("discount", "70% OFF").replace("🔥", "").strip()
        price = item.get("sale_price", "₹399").replace("₹", "RS. ")
        badge_text = f"{disc}  |  ONLY {price}"
        font_b = _get_font(26, bold=True)
        bw, bh = 480, 64
        bx, by = (w - bw) // 2, 280
        draw.rounded_rectangle([bx, by, bx + bw, by + bh], radius=18, fill=(244, 30, 85, 255))
        draw.text((w // 2, by + bh // 2), badge_text, fill=(255, 255, 255, 255), font=font_b, anchor="mm")

        banner.save(out_path, format="PNG")
        return out_path

    def composite_full_motion_reel(
        self,
        item: dict[str, Any],
        bg_video_path: Path | str,
        model_img_or_video: Path | str,
        audio_path: Path | str | None = None,
        out_mp4_path: Path | str | None = None
    ) -> Path:
        """
        True multi-layer UGC video compositor:
        - Layer 1: Full-motion POV unboxing footage (1080x1920 60fps)
        - Layer 2: Real Model Inset floating card with rounded corners & border in bottom-right
        - Layer 3: Top aesthetic typography banner
        - Layer 4: Real parcel opening ASMR audio (ZERO robotic synthetic speech)
        """
        bg_video = Path(bg_video_path)
        model_p = Path(model_img_or_video)
        audio_p = Path(audio_path) if audio_path else Path(__file__).resolve().parent.parent / "data" / "asmr_unboxing_audio_ref1.aac"
        
        slug = re.sub(r"[^a-zA-Z0-9]+", "_", item['title'][:15]).lower().strip("_")
        out_mp4 = Path(out_mp4_path) if out_mp4_path else self.output_dir / f"VIRAL_UGC_{slug.upper()}_REEL.mp4"

        # 1. Render Top Banner Overlay
        banner_png = self.output_dir / f"header_banner_{slug}.png"
        self.render_aesthetic_header_banner(item, banner_png)

        # 2. Render Inset Card with Real Model
        inset_x, inset_y, inset_w, inset_h = 620, 900, 430, 780
        inset_png = self.output_dir / f"model_card_{slug}.png"
        inset_canvas = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
        draw_inset = ImageDraw.Draw(inset_canvas)

        if model_p.exists():
            try:
                m_img = Image.open(model_p).convert("RGBA")
                aspect = inset_w / inset_h
                img_aspect = m_img.width / m_img.height
                if img_aspect > aspect:
                    nw = int(m_img.height * aspect)
                    left = (m_img.width - nw) // 2
                    m_img = m_img.crop((left, 0, left + nw, m_img.height))
                else:
                    nh = int(m_img.width / aspect)
                    top = (m_img.height - nh) // 2
                    m_img = m_img.crop((0, top, m_img.width, top + nh))
                m_img = m_img.resize((inset_w, inset_h), Image.Resampling.LANCZOS)

                mask = Image.new("L", (inset_w, inset_h), 0)
                mdraw = ImageDraw.Draw(mask)
                mdraw.rounded_rectangle([0, 0, inset_w, inset_h], radius=24, fill=255)

                # Shadow
                draw_inset.rounded_rectangle([inset_x - 6, inset_y - 6, inset_x + inset_w + 6, inset_y + inset_h + 6], radius=28, fill=(0, 0, 0, 160))
                # Model photo
                inset_canvas.paste(m_img, (inset_x, inset_y), mask)
                # Border
                draw_inset.rounded_rectangle([inset_x, inset_y, inset_x + inset_w, inset_y + inset_h], radius=24, outline=(255, 255, 255, 240), width=3)
                # Try-on tag
                tag_h = 56
                raw_price = item.get('sale_price', 'SALE').replace('₹', 'RS. ')
                draw_inset.rounded_rectangle([inset_x + 16, inset_y + inset_h - tag_h - 16, inset_x + inset_w - 16, inset_y + inset_h - 16], radius=12, fill=(0, 0, 0, 220))
                draw_inset.text((inset_x + inset_w // 2, inset_y + inset_h - tag_h // 2 - 16), f"TRY-ON  |  {raw_price}", fill=(255, 255, 255, 255), font=_get_font(22, bold=True), anchor="mm")
            except Exception as e:
                log.warning("Could not format model inset: %s", e)

        inset_canvas.save(inset_png, format="PNG")

        # 3. Combine with FFmpeg
        log.info("🎬 [UGCStudio] Compositing full-motion UGC video with ASMR audio (Voice shut)...")
        cmd = [
            "ffmpeg", "-y",
            "-i", str(bg_video),
            "-i", str(inset_png),
            "-i", str(banner_png),
        ]
        if audio_p.exists():
            cmd.extend(["-i", str(audio_p)])
            cmd.extend([
                "-filter_complex", "[0:v][1:v]overlay=0:0[v1];[v1][2:v]overlay=0:0[v]",
                "-map", "[v]",
                "-map", "3:a",
                "-c:v", "libx264", "-pix_fmt", "yuv420p",
                "-c:a", "aac", "-b:a", "192k",
                "-shortest",
                str(out_mp4)
            ])
        else:
            cmd.extend([
                "-filter_complex", "[0:v][1:v]overlay=0:0[v1];[v1][2:v]overlay=0:0[v]",
                "-map", "[v]",
                "-map", "0:a?",
                "-c:v", "libx264", "-pix_fmt", "yuv420p",
                str(out_mp4)
            ])

        try:
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            log.info("✅ [UGCStudio] Full-motion viral UGC Reel rendered: %s", out_mp4)
        except Exception as e:
            log.error("FFmpeg compositing error: %s", e)

        return out_mp4

    def produce_ugc_fashion_reel(self, item: dict[str, Any] | None = None, image_path: str | Path | None = None) -> dict[str, Any]:
        """Creates 1080x1920 60fps UGC Unboxing Video + Veo Prompt with zero manual work."""
        ref_image = Path(image_path) if image_path else None

        if item is None:
            item = {
                "title": "Women Solid Long Sleeve Bodycon Maxi Dress",
                "headline": "Meesho Viral Bodycon Maxi ✨",
                "mrp": "₹1,499",
                "sale_price": "₹399",
                "discount": "73% OFF",
                "fabric": "Premium ribbed stretch fabric with sculpted silhouette and floor-grazing hem",
                "hook": "Meesho viral bodycon maxi dress under ₹400! Fit and stretch is literally 10/10 ✨ Link in bio!"
            }

        # Select real model photo from trained dataset
        if not ref_image or not ref_image.exists():
            from connectors.model_face_identity_trainer import ModelFaceIdentityTrainer
            dataset = ModelFaceIdentityTrainer.get_dataset_image_paths()
            ref_image = dataset[2] if len(dataset) > 2 else dataset[0]  # model_face_3.jpg (black dress) or 1

        # Use reference unboxing video
        bg_video = Path("C:/Users/Deepanshu/Downloads/Unboxing_mesh_top_product_showcase_20261002102901.mp4")
        audio_file = Path(__file__).resolve().parent.parent / "data" / "asmr_unboxing_audio_ref1.aac"

        log.info("Generating UGC Fashion Video for: '%s'", item['title'])
        final_mp4 = self.composite_full_motion_reel(
            item=item,
            bg_video_path=bg_video,
            model_img_or_video=ref_image,
            audio_path=audio_file
        )

        caption = (
            f"✨ {item['headline']}\n\n"
            f"👗 Outfit: {item['title']}\n"
            f"💰 Price: {item['sale_price']} (MRP {item['mrp']} - {item['discount']})\n"
            f"🧵 Fabric: {item['fabric']}\n\n"
            f"👉 How to buy:\n"
            f"1️⃣ Comment 'LINK' and I will DM the direct link to your inbox!\n"
            f"2️⃣ Direct product link is also in my bio ✨\n\n"
            f"#meeshohaul #bodycondress #unboxingvideo #pinterestoutfits #meeshofinds #under500 #aestheticunboxing"
        )

        from connectors.model_face_identity_trainer import ModelFaceIdentityTrainer
        veo_prompt = ModelFaceIdentityTrainer.get_ugc_unboxing_prompt(
            product_name=item['title'],
            fabric=item.get('fabric', 'soft stretchable fabric')
        )

        return {
            "status": "success",
            "title": item['title'],
            "headline": item['headline'],
            "video_path": str(final_mp4),
            "cover_frame": str(ref_image),
            "veo_prompt": veo_prompt,
            "caption": caption
        }


if __name__ == "__main__":
    studio = UGCFashionUnboxingStudio()
    res = studio.produce_ugc_fashion_reel()
    print("\n🎉 [UGC Fashion Unboxing Reel Generated!]")
    print(f"  • Title: {res['title']}")
    print(f"  • Video: {res['video_path']}")
    print(f"\n🎥 [Google Veo Prompt]:\n{res['veo_prompt']}")
    print(f"\n📱 [Caption]:\n{res['caption']}")
