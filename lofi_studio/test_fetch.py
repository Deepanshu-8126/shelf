import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')
from music_fetcher import get_copyright_free_tracks
from pathlib import Path

tracks = get_copyright_free_tracks(count=3, output_dir=Path('cache/music'))
print(f'Downloaded tracks: {len(tracks)}')
for t in tracks:
    p = Path(t["path"])
    size = p.stat().st_size // 1024 if p.exists() else 0
    print(f'  OK: {t["title"]} by {t["artist"]} ({size} KB)')
