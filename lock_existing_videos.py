import json
import os
import hashlib
from pathlib import Path

DATA_DIR = Path("D:/affi;ate/trend-earning-system/data")
MEMORY_DIR = DATA_DIR / "memory"
MEMORY_DIR.mkdir(parents=True, exist_ok=True)
REGISTRY_FILE = MEMORY_DIR / "sent_videos_registry.json"

def get_file_hash(filepath: Path) -> str:
    hasher = hashlib.md5()
    with open(filepath, "rb") as f:
        buf = f.read(65536)
        while len(buf) > 0:
            hasher.update(buf)
            buf = f.read(65536)
    return hasher.hexdigest()

def lock_all_existing_videos():
    registry = {"locked_files": {}, "sent_hashes": set(), "sent_filenames": set()}
    if REGISTRY_FILE.exists():
        try:
            with open(REGISTRY_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                registry["locked_files"] = loaded.get("locked_files", {})
                registry["sent_hashes"] = set(loaded.get("sent_hashes", []))
                registry["sent_filenames"] = set(loaded.get("sent_filenames", []))
        except Exception:
            pass

    # Search all existing video folders and files recursively
    search_roots = [
        Path("D:/affi;ate/trend-earning-system"),
        Path("D:/facts_yt")
    ]

    locked_count = 0
    for root in search_roots:
        if root.exists():
            for mp4 in root.glob("**/*.mp4"):
                try:
                    f_hash = get_file_hash(mp4)
                    f_size = mp4.stat().st_size
                    registry["locked_files"][mp4.name] = {
                        "path": str(mp4),
                        "size": f_size,
                        "hash": f_hash,
                        "locked": True
                    }
                    registry["sent_hashes"].add(f_hash)
                    registry["sent_filenames"].add(mp4.name)
                    locked_count += 1
                except Exception as e:
                    print(f"Error locking {mp4.name}: {e}")

    # Save to disk
    save_data = {
        "locked_files": registry["locked_files"],
        "sent_hashes": list(registry["sent_hashes"]),
        "sent_filenames": list(registry["sent_filenames"])
    }
    with open(REGISTRY_FILE, "w", encoding="utf-8") as f:
        json.dump(save_data, f, indent=2)

    print(f"[LOCKED] Successfully LOCKED {locked_count} existing video files in registry!")
    print(f"[REGISTRY] Saved to: {REGISTRY_FILE}")

if __name__ == "__main__":
    import sys
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    lock_all_existing_videos()
