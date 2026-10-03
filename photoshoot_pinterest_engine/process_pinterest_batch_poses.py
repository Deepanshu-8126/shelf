"""
==============================================================================
🎨 MASTER PINTEREST BATCH AESTHETIC & POSE ENGINE (from esko_karo.csv)
==============================================================================
Combines the exact Pinterest aesthetic boards:
- Hazy Dreamy Golden Hour
- Dim Luxury Hotel Corridor
- Grand Marble Staircase Descent
- Backless Hair-Lift Silhouette
- Penthouse Bathtub Evening Glow
- Terracotta Sun-Drenched Terrace
- European Cafe Date Outfit
- 35mm CineStill & Portra 400 Color Grading
==============================================================================
"""

import os
import sys
import re
import json
import urllib.request
from pathlib import Path
import pandas as pd
from PIL import Image, ImageEnhance, ImageFilter

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
PINTEREST_STYLES_DIR = CURRENT_DIR / "pinterest_styles"
PINTEREST_STYLES_DIR.mkdir(parents=True, exist_ok=True)

CSV_PINTEREST = CURRENT_DIR / "esko_karo.csv"
CSV_MEESHO = CURRENT_DIR / "meesho-com-2026-10-03.csv"

# Exact curated Pinterest visual styles mapped from esko_karo pins
PINTEREST_VIBE_PRESETS = [
    {
        "style_id": "BURGUNDY_HOTEL_HALLWAY",
        "title": "Dim Luxury Hotel Corridor & Bodycon Drape",
        "pose": "effortless high-fashion walking stride down a minimalist luxury hotel hallway with warm wood paneling, hands relaxed at her sides grazing the hem, slight 45-degree candid head turn away from camera",
        "lighting_grade": "Warm recessed ceiling cove lights casting soft downward highlights on collarbone and fabric sheen, deep moody shadows, CineStill 800T warm tungsten color grade",
        "color_filter": "Hazy warm amber glow, soft golden undertones, velvety deep blacks"
    },
    {
        "style_id": "GRAND_MARBLE_STAIRCASE",
        "title": "Grand Spiral Marble Staircase Descent",
        "pose": "poised full-length posture descending a curved white marble staircase in a luxury neoclassical villa, one hand lightly brushing the ornate wrought-iron railing, floor-length gown trailing elegantly",
        "lighting_grade": "Soft diffused palace ambient light with natural marble floor reflections, Hasselblad 50mm f/1.8 optical depth of field",
        "color_filter": "Clean luminous champagne tones, organic soft contrast, filmic highlight rolloff"
    },
    {
        "style_id": "HAIR_LIFT_BACKLESS",
        "title": "Backless Lace Silhouette & Hair-Updo",
        "pose": "candid rear three-quarter posture with both hands naturally gathering her long dark wavy hair up at the crown of her head, showcasing the delicate backless straps, lace patterns, and sculpted waistline",
        "lighting_grade": "Soft natural morning daylight streaming through sheer linen curtains casting gentle contour shadows across shoulder blades",
        "color_filter": "Dreamy soft-focus haze, Kodak Portra 400 neutral skin tones, fine organic 35mm grain"
    },
    {
        "style_id": "PENTHOUSE_BATHTUB_LOUNGE",
        "title": "Luxury Penthouse Bathtub Evening Glow",
        "pose": "leaning back gracefully against a sleek freestanding oval bathtub in an aesthetic penthouse bathroom with floor-to-ceiling glass, legs softly bent in a relaxed glamorous evening pose",
        "lighting_grade": "Soft ambient evening light mixed with distant city lights bokeh through glass window",
        "color_filter": "Moody editorial contrast, warm rose-gold highlights, velvety soft shadows"
    },
    {
        "style_id": "TERRACOTTA_SUMMER_BREEZE",
        "title": "Sun-Drenched Terracotta & Cottagecore Glow",
        "pose": "standing beside a rustic sunlit terracotta wall with climbing green vines, gentle side profile looking down thoughtfully with delicate floral earring catching the light",
        "lighting_grade": "Direct warm golden hour afternoon sun casting crisp architectural tree shadows across the dress",
        "color_filter": "Warm honey-golden sun haze, vibrant earthy tones, rich tactile fabric texture"
    },
    {
        "style_id": "YACHT_DECK_WIND_FLOW",
        "title": "Open-Air Yacht Terrace Breeze Flow",
        "pose": "standing gracefully on a sunny teak wood yacht balcony deck, one hand steadying the hem as gentle coastal breeze catches the ruffled slit, natural organic kinetic movement",
        "lighting_grade": "Brilliant open-sky Mediterranean daylight with soft warm rim light along dark wavy hair",
        "color_filter": "Crisp sun-kissed natural tones, soft pastel sky gradient, zero artificial oversaturation"
    },
    {
        "style_id": "EUROPEAN_CAFE_CANDID",
        "title": "Chic Street Cafe Date Outfit",
        "pose": "standing or seated next to an outdoor Parisian cafe bistro marble table with espresso cup, candid relaxed smile gazing slightly off-camera",
        "lighting_grade": "Natural side daylight filtering through street trees with soft ambient bounce",
        "color_filter": "Editorial fashion magazine color science, creamy 85mm background blur"
    }
]


def build_bespoke_pinterest_prompt(product_title: str, price: str, fabric: str, style_idx: int) -> dict:
    preset = PINTEREST_VIBE_PRESETS[style_idx % len(PINTEREST_VIBE_PRESETS)]
    
    is_saree = any(w in (product_title + " " + fabric).lower() for w in ["saree", "sari", "ethnic", "kurti", "lehenga"])
    if is_saree:
        pose_desc = f"regal Saree drape posture with pleated pallu held delicately in manicured fingers, standing beside a sunlit sandstone archway, gentle dignified gaze"
        setting = "heritage Indian palace courtyard with golden afternoon light streaming through carved jharokhas"
    else:
        pose_desc = preset["pose"]
        setting = preset["title"]

    prompt = (
        f"Authentic raw 35mm high-fashion editorial photograph of the exact same 21-year-old young Indian creator "
        f"(natural soft-oval face shape with gentle jawline, smooth glowing warm honey skin with real fine pores and skin texture, "
        f"expressive warm honey-brown almond eyes with subtle dark tightline, delicate straight nose, soft rose-pink lips with natural sheen, "
        f"signature tiny round black bindi centered precisely above eyebrows, voluminous dark espresso black wavy hair styled with face-framing curtain tendrils, "
        f"traditional silver oxidised bell-shaped jhumkas and delicate stacked silver bangles) "
        f"wearing the {product_title} in premium {fabric} shown in the attached product image. "
        f"Pose: {pose_desc}. "
        f"Setting & Vibe: {setting}. "
        f"Lighting & Film Grade: {preset['lighting_grade']}. Color Aesthetic: {preset['color_filter']}. "
        f"Shot on Hasselblad 50mm f/1.8 / Leica M11, authentic Kodak Portra 400 / CineStill 800T natural film tones, "
        f"organic optical depth of field, real fabric weave and drape, high-fashion Pinterest influencer aesthetic, "
        f"zero phone in hand, zero mirror selfie, zero AI plastic smoothness, 8K ultra-detailed."
    )

    return {
        "style_id": preset["style_id"],
        "style_title": preset["title"],
        "product_title": product_title,
        "price": price,
        "fabric": fabric,
        "color_filter": preset["color_filter"],
        "prompt": prompt
    }


def main():
    print("=" * 80)
    print("🚀 BUILDING PINTEREST AESTHETIC BATCH CATALOG (from esko_karo.csv + meesho)")
    print("=" * 80)

    # 1. Download reference pins from esko_karo.csv
    if CSV_PINTEREST.exists():
        df_pin = pd.read_csv(CSV_PINTEREST)
        print(f"📥 Downloading {len(df_pin)} Pinterest inspiration reference pins...")
        for i, r in df_pin.iterrows():
            img_url = str(r.get("image", ""))
            if img_url.startswith("http"):
                local_f = PINTEREST_STYLES_DIR / f"pinterest_ref_{i+1}.jpg"
                try:
                    req = urllib.request.Request(img_url, headers={"User-Agent": "Mozilla/5.0"})
                    with urllib.request.urlopen(req, timeout=10) as resp, open(local_f, "wb") as f:
                        f.write(resp.read())
                    print(f"  ✅ Saved Pinterest Ref [{i+1}]: {local_f.name}")
                except Exception as e:
                    print(f"  ⚠️ Error downloading pin {i+1}: {e}")

    # 2. Build full bespoke Pinterest catalog for all products in meesho batch
    df_m = pd.read_csv(CSV_MEESHO)
    catalog = []

    print(f"\n🎨 Generating {len(df_m)} bespoke Pinterest Editorial Prompts...")
    for idx, row in df_m.iterrows():
        raw_title = str(row.get('item_page_title') or row.get('title') or row.get('name') or f"Product {idx+1}")
        raw_price = str(row.get('price') or row.get('price_1') or "₹499")
        fabric = str(row.get('product_fabric') or 'Lycra/Georgette').replace("Fabric", "").replace(":", "").strip()

        price_m = re.search(r'₹\s*(\d+)', raw_price) or re.search(r'₹\s*(\d+)', raw_title)
        price = f"₹{price_m.group(1)}" if price_m else "₹499"
        title = re.sub(r'₹\s*\d+.*', '', raw_title)
        title = re.sub(r'\+\d+\s*More', '', title)
        title = re.sub(r'Supplier.*', '', title).strip()
        if not title:
            title = "Trendy Outfit"

        item_data = build_bespoke_pinterest_prompt(title, price, fabric, idx)
        item_data["product_index"] = idx + 1
        catalog.append(item_data)

        print(f"  [{idx+1}/{len(df_m)}] ✨ {title} ({price}) ➔ {item_data['style_title']}")

    # Save to JSON & CSV
    out_json = CURRENT_DIR / "curated_pinterest_poses_catalog.json"
    with open(out_json, "w", encoding="utf-8") as jf:
        json.dump(catalog, jf, indent=2, ensure_ascii=False)

    out_csv = CURRENT_DIR / "curated_pinterest_poses_catalog.csv"
    pd.DataFrame(catalog).to_csv(out_csv, index=False, encoding="utf-8")

    print("\n" + "=" * 80)
    print(f"🎉 PINTEREST AESTHETIC BATCH CATALOG READY!")
    print(f"📁 JSON Catalog: {out_json}")
    print(f"📊 CSV Catalog : {out_csv}")
    print("=" * 80)


if __name__ == "__main__":
    main()
