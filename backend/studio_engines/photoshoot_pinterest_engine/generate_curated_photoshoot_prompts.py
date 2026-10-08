"""
==============================================================================
✨ MASTER CURATED SAREE & ETHNIC PHOTOSHOOT PIN GENERATOR
==============================================================================
1. Reads scraped Meesho CSV (`meesho-com-2026-10-03.csv`).
2. Generates bespoke Saree & Ethnic Photoshoot Prompts with:
   - Consistent 21yo Indian Model Character Sheet (Bindi, Jhumkas, Honey Eyes)
   - Saree Draping & Pallu Flaunt Poses
   - Golden Hour & Courtyard / Mirror Aesthetics
3. Auto-downloads product reference images.
4. Performs Gemini Logo Delogo Clean + 4K Micro-Sharpening + Pinterest Shopping Card.
==============================================================================
"""

import os
import sys
import re
import csv
import json
import urllib.request
from pathlib import Path
from PIL import Image, ImageEnhance, ImageFilter, ImageDraw, ImageFont

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
RAW_PHOTOS_DIR = CURRENT_DIR / "raw_photos"
RENDERED_DIR = CURRENT_DIR / "rendered_posts"

RAW_PHOTOS_DIR.mkdir(parents=True, exist_ok=True)
RENDERED_DIR.mkdir(parents=True, exist_ok=True)

CSV_FILE = CURRENT_DIR / "meesho-com-2026-10-03.csv"


def clean_title_and_price(raw_title: str, raw_price: str) -> tuple[str, str]:
    """Cleans up scraped Meesho title strings like 'Trendy Fashionista Women Dresses₹391 4.2'."""
    # Clean price
    price_match = re.search(r'₹\s*(\d+)', str(raw_price))
    if not price_match:
        price_match = re.search(r'₹\s*(\d+)', str(raw_title))
    price = f"₹{price_match.group(1)}" if price_match else "₹399"

    # Clean title
    title = str(raw_title)
    title = re.sub(r'₹\s*\d+.*', '', title)
    title = re.sub(r'\+\d+\s*More', '', title)
    title = re.sub(r'Supplier.*', '', title)
    title = re.sub(r'\d\.\d.*', '', title)
    title = title.strip()
    if not title:
        title = "Graceful Indian Saree / Ethnic Outfit"
    return title, price


def build_saree_photoshoot_prompt(product_title: str, fabric: str = "Georgette/Silk") -> str:
    """Creates a high-fashion, ultra-photorealistic Saree photoshoot prompt for the 21yo Indian Model."""
    return (
        f"Authentic raw 4K photoshoot of the exact same 21-year-old young Indian girl creator "
        f"(youthful natural soft-oval face shape with gentle feminine jawline, smooth glowing cheeks, "
        f"large expressive warm honey-brown almond eyes with subtle tightline, cute delicate straight nose, "
        f"soft rose-pink lips with defined cupid's bow, signature tiny round black bindi centered above eyebrows, "
        f"long dark espresso black wavy hair styled with effortless face-framing tendrils, "
        f"wearing traditional silver oxidised bell-shaped jhumkas and delicate stacked silver bangles) "
        f"elegantly styled in the {product_title} in premium {fabric} fabric. "
        f"Full-length graceful pose holding and flaunting the pleated pallu drape over her shoulder, "
        f"gentle side-turn looking towards camera with a soft warm smile in a sunlit aesthetic indoor courtyard / mirror setting. "
        f"Natural golden hour sunlight, authentic 35mm film grain, hyper-realistic fabric texture and weave, 8K ultra-detailed, zero CGI."
    )


def build_western_dress_prompt(product_title: str, fabric: str = "Lycra/Cotton") -> str:
    """Creates a viral GenZ mirror selfie prompt for western dresses / gowns."""
    return (
        f"Authentic raw smartphone mirror selfie video/photo of the exact same 21-year-old young Indian girl creator "
        f"(youthful natural soft-oval face shape, warm honey-brown almond eyes, signature tiny round black bindi, "
        f"dark espresso black wavy hair with curtain tendrils, delicate silver jhumkas) "
        f"doing a real outfit check wearing the {product_title} in fitted {fabric} fabric. "
        f"Full-length mirror perspective holding iPhone, stepping back and turning side-to-side to show silhouette and fit. "
        f"Sunlit aesthetic bedroom, natural daylight, crisp iPhone 16 Pro camera clarity, real fabric stretch and drape, 8K ultra-detailed."
    )


def polish_and_delogo_image(img_path: Path, out_path: Path, title: str, price: str) -> Path:
    """Removes logo watermark, applies 4K sharpening and adds sleek Pinterest tag."""
    img = Image.open(img_path).convert("RGBA")
    w, h = img.size

    # Watermark delogo patch in bottom-right corner
    logo_w = int(w * 0.14)
    logo_h = int(h * 0.08)
    br_box = (w - logo_w - 5, h - logo_h - 5, w, h)
    patch = img.crop(br_box).filter(ImageFilter.GaussianBlur(radius=10))
    img.paste(patch, br_box)

    rgb = img.convert("RGB")

    # 4K Micro-Sharpening & Contrast
    enhancer_s = ImageEnhance.Sharpness(rgb)
    sharp = enhancer_s.enhance(1.4)

    enhancer_c = ImageEnhance.Contrast(sharp)
    contrast = enhancer_c.enhance(1.05)

    enhancer_col = ImageEnhance.Color(contrast)
    color = enhancer_col.enhance(1.04)

    polished = color.filter(ImageFilter.UnsharpMask(radius=2, percent=140, threshold=2))

    # Add Pinterest Shopping Glass Badge
    overlay = Image.new("RGBA", polished.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    bw, bh = min(w - 40, 360), 68
    bx = (w - bw) // 2
    by = h - 90
    d.rounded_rectangle([bx, by, bx + bw, by + bh], radius=20, fill=(15, 17, 22, 230), outline=(255, 255, 255, 70), width=2)
    polished = Image.alpha_composite(polished.convert("RGBA"), overlay).convert("RGB")

    draw = ImageDraw.Draw(polished)
    try:
        font_b = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 21)
        font_s = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 17)
    except Exception:
        font_b = font_s = ImageFont.load_default()

    draw.text((bx + 20, by + 12), title[:22], font=font_b, fill=(255, 255, 255))
    draw.text((bx + 20, by + 38), f"Deal: {price}  •  Tap to Buy ›", font=font_s, fill=(245, 166, 35))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    polished.save(out_path, "JPEG", quality=96, subsampling=0)
    return out_path


def process_curated_batch():
    if not CSV_FILE.exists():
        print(f"❌ CSV not found at {CSV_FILE}")
        return

    import pandas as pd
    df = pd.read_csv(CSV_FILE)
    print("=" * 75)
    print(f"🚀 CURATING BEST SAREE & ETHNIC PHOTOSHOOT PROMPTS ({len(df)} Products)")
    print("=" * 75)

    curated_data = []

    for idx, row in df.iterrows():
        raw_title = str(row.get('item_page_title') or row.get('title') or row.get('name') or row.get('title_1') or f"Product {idx+1}")
        raw_price = str(row.get('price') or row.get('price_1') or row.get('price_2') or "₹399")
        link = str(row.get('item_page_link') or row.get('web_scraper_start_url') or "")
        img_url = str(row.get('image') or row.get('image_1') or row.get('image2') or row.get('image_2') or "")
        fabric = str(row.get('product_fabric') or 'Lycra/Georgette').replace("Fabric", "").replace(":", "").strip()

        title, price = clean_title_and_price(raw_title, raw_price)

        # Detect Saree vs Western
        is_saree = any(w in (title + " " + fabric).lower() for w in ["saree", "sari", "ethnic", "kurti", "lehenga", "anarkali", "net"])
        if is_saree:
            prompt = build_saree_photoshoot_prompt(title, fabric)
            cat_tag = "🥻 Saree / Ethnic Shoot"
        else:
            prompt = build_western_dress_prompt(title, fabric)
            cat_tag = "👗 Western Outfit Check"

        print(f"\n[{idx+1}/{len(df)}] {cat_tag}: {title} ({price})")
        print(f"  🔗 Link: {link[:65]}...")
        print(f"  🎨 Character Sheet + Product Prompt:")
        print(f"     \"{prompt[:180]}...\"")

        # Download product image if URL is valid
        local_img = RAW_PHOTOS_DIR / f"product_{idx+1}_ref.jpg"
        polished_img = RENDERED_DIR / f"PIN_POST_{idx+1}_{title.lower().replace(' ', '_')[:20]}.jpg"
        
        if img_url.startswith("http"):
            try:
                headers = {"User-Agent": "Mozilla/5.0"}
                req = urllib.request.Request(img_url, headers=headers)
                with urllib.request.urlopen(req, timeout=10) as resp, open(local_img, "wb") as f:
                    f.write(resp.read())
                
                # Apply Delogo and 4K Polish
                polish_and_delogo_image(local_img, polished_img, title, price)
                print(f"  ✨ [Rendered & Delogoed 4K Pin]: {polished_img.name}")
            except Exception as e:
                print(f"  ⚠️ Image download notice: {e}")

        curated_data.append({
            "index": idx + 1,
            "category": cat_tag,
            "title": title,
            "price": price,
            "fabric": fabric,
            "link": link,
            "image_url": img_url,
            "master_prompt": prompt
        })

    # Save curated prompts JSON for instant access
    json_out = CURRENT_DIR / "curated_photoshoot_prompts.json"
    with open(json_out, "w", encoding="utf-8") as jf:
        json.dump(curated_data, jf, indent=2, ensure_ascii=False)

    print("\n" + "=" * 75)
    print(f"🎉 MASTER PROMPT LIBRARY SAVED TO: {json_out.name}")
    print(f"🖼️ RENDERED 4K PINS SAVED TO: photoshoot_pinterest_engine/rendered_posts/")
    print("=" * 75)


if __name__ == "__main__":
    process_curated_batch()
