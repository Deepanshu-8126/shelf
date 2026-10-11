"""
Dynamic BGM Cueing & Synchronization Engine.
Solves the "3-minute audio dead intro" problem by:
1. Seeking directly to the iconic melodic hook / main instrument entry.
2. Skipping dead air / quiet warm-ups.
3. Dynamically analyzing unknown tracks using RMS onset detection.
4. Applying smooth micro-fades for seamless sync with video duration.
"""
import sys
import subprocess
from pathlib import Path
from typing import Tuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Golden Cue Offsets for our Curated Tracks (in seconds)
# Sourced from exact musical entrance points
TRACK_CUE_POINTS = {
    "01_forensic_the_dread.mp3": {
        "hook_offset": 18.0,      # Eerie bowed acoustic cello enters
        "volume_boost": 0.52,     # 52% prominent cinematic mix
        "description": "Cello tension onset"
    },
    "02_psychology_echoes_of_time.mp3": {
        "hook_offset": 14.5,      # Melancholic piano motif enters
        "volume_boost": 0.50,     # 50% prominent mix
        "description": "Piano & low strings motif"
    },
    "03_mystery_lightless_dawn.mp3": {
        "hook_offset": 20.0,      # Deep orchestral suspense entry
        "volume_boost": 0.55,     # 55% prominent mix
        "description": "Orchestral suspense entry"
    },
    "04_investigation_apprehension.mp3": {
        "hook_offset": 10.0,      # Interrogation room pulse starts
        "volume_boost": 0.50,     # 50% prominent mix
        "description": "Investigative pulse"
    },
    "05_noir_crime_dark_walk.mp3": {
        "hook_offset": 4.0,       # Noir upright bass & brushes
        "volume_boost": 0.50,     # 50% prominent mix
        "description": "Classic noir bass theme"
    },
    "06_cosmic_deep_noise.mp3": {
        "hook_offset": 8.0,       # Deep space resonant drone
        "volume_boost": 0.52,     # 52% prominent mix
        "description": "Cosmic resonance onset"
    }
}

def detect_musical_onset(track_path: Path, max_scan_sec: int = 50) -> float:
    """
    Scans the first 50 seconds of an unknown track to find where
    the musical body actually starts (skipping quiet intro/silence).
    """
    best_offset = 0.0
    best_rms = -999.0
    
    # Sample every 4 seconds
    for offset in range(0, max_scan_sec, 4):
        cmd = [
            "ffmpeg", "-y", "-ss", str(offset), "-t", "3",
            "-i", str(track_path),
            "-af", "astats=metadata=1:reset=1",
            "-f", "null", "-"
        ]
        res = subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.DEVNULL, text=True)
        for line in res.stderr.splitlines():
            if "RMS level dB:" in line:
                try:
                    val = float(line.split(":")[1].strip())
                    if val > best_rms:
                        best_rms = val
                        best_offset = float(offset)
                except ValueError:
                    pass
                break
                
    # Return offset where energy is strong
    return best_offset if best_offset > 0 else 0.0

def prepare_synced_bgm(
    track_path: Path,
    target_duration: float,
    output_path: Path,
    preferred_offset: float = None
) -> Tuple[Path, float]:
    """
    Extracts the best musical portion of the 3-minute track to match the Short duration.
    Returns (output_path, recommended_mix_volume).
    """
    filename = track_path.name
    cue_info = TRACK_CUE_POINTS.get(filename)
    
    if preferred_offset is not None:
        start_sec = preferred_offset
        volume = 0.50
    elif cue_info:
        start_sec = cue_info["hook_offset"]
        volume = cue_info["volume_boost"]
        print(f"🎯 Smart Cue Applied: '{filename}' starting at {start_sec:.1f}s ({cue_info['description']}) [Volume: {int(volume*100)}%]")
    else:
        # Dynamic Auto-detection for any new track
        start_sec = detect_musical_onset(track_path)
        volume = 0.50
        print(f"🤖 Dynamic Onset Detected: '{filename}' starting at {start_sec:.1f}s [Volume: {int(volume*100)}%]")

    fade_out_start = max(target_duration - 1.5, 0.5)
    
    # Precise extraction with clean stream seeking
    cmd = [
        "ffmpeg", "-y",
        "-ss", f"{start_sec:.2f}",
        "-i", str(track_path),
        "-t", f"{target_duration:.2f}",
        "-af", f"afade=t=in:ss=0:d=0.6,afade=t=out:st={fade_out_start:.2f}:d=1.5",
        "-c:a", "libmp3lame", "-b:a", "192k",
        str(output_path)
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    return output_path, volume

if __name__ == "__main__":
    bgm_dir = Path(__file__).resolve().parent / "assets" / "bgm"
    test_track = bgm_dir / "01_forensic_the_dread.mp3"
    out_test = Path(__file__).resolve().parent / "output" / "test_synced_bgm.mp3"
    out_test.parent.mkdir(parents=True, exist_ok=True)
    
    if test_track.exists():
        p, vol = prepare_synced_bgm(test_track, 10.0, out_test)
        print(f"✅ Synced 10s BGM rendered at: {p} (Vol: {vol})")
