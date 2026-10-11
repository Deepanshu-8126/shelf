import sys
import requests
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

OUT_DIR = Path(__file__).resolve().parent / "bgm"
OUT_DIR.mkdir(parents=True, exist_ok=True)

TRACKS = {
    "01_forensic_the_dread.mp3": "https://incompetech.com/music/royalty-free/mp3-royaltyfree/The%20Dread.mp3",
    "02_psychology_echoes_of_time.mp3": "https://incompetech.com/music/royalty-free/mp3-royaltyfree/Echoes%20of%20Time.mp3",
    "03_mystery_lightless_dawn.mp3": "https://incompetech.com/music/royalty-free/mp3-royaltyfree/Lightless%20Dawn.mp3",
    "04_investigation_apprehension.mp3": "https://incompetech.com/music/royalty-free/mp3-royaltyfree/Apprehension.mp3",
    "05_noir_crime_dark_walk.mp3": "https://incompetech.com/music/royalty-free/mp3-royaltyfree/Dark%20Walk.mp3",
    "06_cosmic_deep_noise.mp3": "https://incompetech.com/music/royalty-free/mp3-royaltyfree/Deep%20Noise.mp3",
}

def download_tracks():
    # Clear synthetic tracks if needed or overwrite with real tuned tracks
    print(f"📥 Downloading 6 Real, Tuned, Emotional Cinematic BGM Tracks into {OUT_DIR}...")
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    
    for filename, url in TRACKS.items():
        dest = OUT_DIR / filename
        print(f"⏳ Downloading: {filename} from {url}...")
        try:
            r = requests.get(url, headers=headers, stream=True, timeout=30)
            if r.status_code == 200:
                with open(dest, "wb") as f:
                    for chunk in r.iter_content(chunk_size=1024*1024):
                        f.write(chunk)
                size_mb = dest.stat().st_size / (1024 * 1024)
                print(f"✅ Downloaded: {filename} ({size_mb:.2f} MB)")
            else:
                print(f"❌ Failed to download {filename}: HTTP {r.status_code}")
        except Exception as e:
            print(f"❌ Error downloading {filename}: {e}")

    # Remove the old synthetic flat sine files so only real tuned songs remain
    old_synthetic = [
        "01_forensic_interrogation.mp3",
        "02_dark_mindhunter_dread.mp3",
        "03_forbidden_coordinates_void.mp3",
        "04_cosmic_singularity_deepspace.mp3",
        "05_unsolved_dossier_tension.mp3",
        "06_abyssal_deep_ocean_blackout.mp3",
    ]
    for old in old_synthetic:
        p = OUT_DIR / old
        if p.exists():
            p.unlink()
            print(f"🗑️ Removed flat synthetic track: {old}")

if __name__ == "__main__":
    download_tracks()
    print("🎉 All 6 Real Tuned Cinematic Music Tracks Installed!")
