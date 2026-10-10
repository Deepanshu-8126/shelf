"""
Asset Downloader - Pixabay SFX + Freepik Visual Stickers.
Uses your Pixabay API key for SFX. Freepik requires manual download (no free API).
"""
import os
import sys
import requests
from pathlib import Path
from dotenv import load_dotenv

# Load .env from workspace root
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(WORKSPACE_ROOT / ".env")

PIXABAY_API_KEY = os.environ.get("PIXABAY_API_KEY")
if not PIXABAY_API_KEY:
    print("ERROR: PIXABAY_API_KEY not found in .env")
    sys.exit(1)

SFX_DIR = Path(__file__).resolve().parent.parent / "assets" / "sfx"
STICKERS_DIR = Path(__file__).resolve().parent.parent / "assets" / "visual_stickers"

SFX_DIR.mkdir(parents=True, exist_ok=True)
STICKERS_DIR.mkdir(parents=True, exist_ok=True)


# Pixabay SFX search queries (optimized for our 4 sound types)
SFX_QUERIES = {
    "whoosh.mp3": ["whoosh", "swish", "transition whoosh", "fast whoosh"],
    "cash.mp3": ["cash register", "money sound", "coins", "cha-ching"],
    "boom.mp3": ["impact", "boom", "explosion", "thud", "dramatic hit"],
    "click.mp3": ["camera shutter", "click", "snap", "photo click"],
}


def download_pixabay_sfx(filename: str, queries: list) -> bool:
    """Download best matching SFX from Pixabay."""
    headers = {"Accept": "application/json"}

    for query in queries:
        url = "https://pixabay.com/api/sounds/"
        params = {
            "key": PIXABAY_API_KEY,
            "q": query,
            "per_page": 10,
            "order": "popular",
            "min_duration": 0.5,
            "max_duration": 5,
        }

        try:
            resp = requests.get(url, params=params, headers=headers, timeout=15)
            resp.raise_for_status()
            data = resp.json()

            hits = data.get("hits", [])
            if not hits:
                continue

            # Pick first result with downloadable URL
            for hit in hits:
                mp3_url = hit.get("mp3_url") or hit.get("preview_url")
                if mp3_url:
                    print(f"   Downloading {filename} from: {query} (tags: {hit.get('tags', '')})")
                    audio_resp = requests.get(mp3_url, timeout=20)
                    audio_resp.raise_for_status()

                    filepath = SFX_DIR / filename
                    filepath.write_bytes(audio_resp.content)

                    # Verify file size
                    size_kb = filepath.stat().st_size / 1024
                    print(f"   OK {filename} saved ({size_kb:.1f} KB)")
                    return True

        except Exception as e:
            print(f"   WARNING: Query '{query}' failed: {e}")
            continue

    print(f"   FAILED: Failed to download {filename}")
    return False


def download_all_sfx():
    """Download all 4 SFX files from Pixabay."""
    print("\nDownloading SFX from Pixabay...")
    print("=" * 50)

    success = 0
    for filename, queries in SFX_QUERIES.items():
        if download_pixabay_sfx(filename, queries):
            success += 1

    print(f"\nSFX Download: {success}/4 complete")
    return success == 4


def print_freepik_checklist():
    """Print manual download checklist for Freepik stickers."""
    print("\nFreepik Visual Stickers - Manual Download Checklist")
    print("=" * 50)
    print("Go to freepik.com and search each term. Download as PNG/SVG with transparent background.")
    print("Resize to 350x350 after download. Save to:")
    print(f"   {STICKERS_DIR}")
    print()

    stickers = [
        ("laptop.png", "laptop icon transparent", "Single laptop/notebook, side view, clean line art or flat"),
        ("phone.png", "smartphone icon transparent", "Modern phone front view, minimal style"),
        ("camera.png", "camera icon transparent", "DSLR or photo camera, not video camera"),
        ("money.png", "money bag icon transparent", "Dollar sign bag or cash stack, not coins"),
        ("boss.png", "boss character transparent", "Business person pointing/angry, office attire, full body or upper body"),
        ("police.png", "police officer transparent", "Police officer badge/uniform, authority figure"),
        ("eviction.png", "eviction notice transparent", "Red/white notice paper on door, or document with 'EVICTED'"),
    ]

    for i, (filename, search_term, notes) in enumerate(stickers, 1):
        filepath = STICKERS_DIR / filename
        status = "EXISTS" if filepath.exists() else "MISSING"
        print(f"  {i}. {filename} [{status}]")
        print(f"     Search: \"{search_term}\"")
        print(f"     Notes: {notes}")
        print()


def main():
    print("Channel 1 Asset Downloader")
    print("=" * 50)
    print(f"SFX dir: {SFX_DIR}")
    print(f"Stickers dir: {STICKERS_DIR}")

    # Download SFX from Pixabay
    sfx_ok = download_all_sfx()

    # Print Freepik checklist
    print_freepik_checklist()

    # Summary
    print("=" * 50)
    if sfx_ok:
        print("SUCCESS: All SFX downloaded successfully!")
    else:
        print("WARNING: Some SFX failed - check output above")

    print("\nNext steps:")
    print("1. Download missing stickers from Freepik (see checklist)")
    print("2. Resize all to 350x350 (Photopea.com -> Image -> Image Size)")
    print("3. Ensure transparent background (PNG with alpha)")
    print("4. Run pipeline: python run_reddit_pipeline.py")


if __name__ == "__main__":
    main()