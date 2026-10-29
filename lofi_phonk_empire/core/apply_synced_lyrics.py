"""
Universal Synced Lyrics Applicator (Option A Engine)
Applies 0% CPU cloud timed lyrics to any MP3 stem and embeds ID3 tags + exports LRC.
"""
import sys
import re
import subprocess as sp
from pathlib import Path
from mutagen.id3 import ID3, TIT2, TPE1, TALB, USLT, SYLT
from mutagen.mp3 import MP3

sys.stdout.reconfigure(encoding='utf-8')

def embed_lrc_into_mp3(mp3_path: Path, lrc_path: Path, title: str = "", artist: str = ""):
    if not mp3_path.exists() or not lrc_path.exists():
        print(f"[ERROR] Missing file: {mp3_path} or {lrc_path}")
        return False

    with open(lrc_path, "r", encoding="utf-8") as f:
        lrc_text = f.read()

    audio = MP3(str(mp3_path), ID3=ID3)
    try:
        audio.add_tags()
    except Exception:
        pass

    if title:
        audio.tags.add(TIT2(encoding=3, text=title))
    if artist:
        audio.tags.add(TPE1(encoding=3, text=artist))

    # USLT (Full Plain Lyrics)
    plain_lines = [l.split("]", 1)[1].strip() for l in lrc_text.splitlines() if "]" in l and l.split("]", 1)[1].strip()]
    audio.tags.add(USLT(encoding=3, lang='hin', desc='Hindi Lyrics', text="\n".join(plain_lines)))

    # SYLT (Millisecond Timestamps)
    sylt_entries = []
    pattern = re.compile(r'\[(\d+):(\d+\.\d+)\](.*)')
    for line in lrc_text.splitlines():
        m = pattern.match(line.strip())
        if m:
            mm, ss, txt = m.groups()
            ms = int((int(mm) * 60 + float(ss)) * 1000)
            txt = txt.strip()
            if txt:
                sylt_entries.append((txt, ms))

    if sylt_entries:
        audio.tags.add(SYLT(encoding=3, lang='hin', format=2, type=1, desc='Synced Lyrics', text=sylt_entries))

    audio.save()
    print(f"[DONE] Embedded {len(sylt_entries)} synced lyric lines into {mp3_path.name}")
    return True

if __name__ == "__main__":
    base = Path(r"d:\facts_yt\lofi_phonk_empire")
    mp3 = base / "output" / "chalray_true_lofi_master.mp3"
    lrc = base / "raw_stems" / "chalray.lrc"
    embed_lrc_into_mp3(mp3, lrc, "Chalray Chalray Waal", "Shanzy Siyal")
