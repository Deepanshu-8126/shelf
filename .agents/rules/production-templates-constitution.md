# Production Templates Constitution & Studio Standard

This rule permanently locks the 2 production video templates in `d:\facts_yt\lofi_phonk_empire\core\`:

---

## 1. Unified Studio Master Entrypoint
**NEVER create random one-off test scripts in the root directory.**
Always invoke the studio master CLI:
```bash
python core/studio_master.py --pipeline [lyric|phonk] [options]
```

---

## 2. Template 1: Aesthetic Lyric Pipeline (`--pipeline lyric`)
- **Use Case**: Romantic / Lofi / Hindi songs (e.g. *Husn*, *Choo Lo*, *Tum Se Hi*).
- **Aesthetic**:
  - Warm vintage ivory paper canvas (`#FAF8F4`).
  - Google Font `RozhaOne-Regular.ttf` for Devanagari calligraphy in crimson red (`#C8102E`).
  - 16:9 mode: 360° continuously spinning vinyl record with soft red ambient breathing glow.
  - 9:16 mode: Centered vertical kinetic stack popping on vocal beats.
  - Floating organic dust motes + sleek Spotify playback scrubber with real-time timestamps.
- **Auto-Sync Rule**:
  - Always uses Whisper audio verification to cut exactly where vocals start (preventing silent/guitar intro mismatches).
- **Execution Command**:
  ```bash
  python core/studio_master.py --pipeline lyric --title "Husn" --artist "Anuv Jain" --ratio 16:9
  ```

---

## 3. Template 2: Phonk Soundwave Dagger Pipeline (`--pipeline phonk`)
- **Use Case**: Gym Phonk / Brazilian Phonk / Drift Phonk / High-Adrenaline videos.
- **Aesthetic**:
  - Custom Gym Warrior / Manga Artwork (`gym_warrior_1080p.png`).
  - Brutalist branding `[DOPAMINE]` / `[EGOIST]` in bold black grotesque font.
  - **Audio-Reactive Soundwave Dagger Blade**: Katana hilt with blood-red tip + real-time 808 frequency waveform blade.
  - **Clearance Law**: Wave is locked at `y=280` so it has ample breathing room and NEVER cuts into the character's t-shirt or collar.
  - **Full-Screen 8K Overlays**:
    - Dual-layer atmospheric particles (foreground out-of-focus soft bokeh + midground floating embers).
    - 808 sub-bass beat pump (exposure flash synced to kicks).
    - Chromatic Aberration RGB channel split (2-3px on bass drops).
    - Cinematic slow push-in zoom ($1.00 \times \rightarrow 1.025 \times$).
    - 35mm film grain + subtle CRT scanline texture.
- **Execution Command**:
  ```bash
  python core/studio_master.py --pipeline phonk --title "[DOPAMINE]" --subtitle "will make you the main character"
  ```
