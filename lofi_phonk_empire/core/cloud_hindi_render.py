"""
Cloud Hindi Trending Songs Master Renderer (30-Minute Master Turbo Engine)
--------------------------------------------------------------------------
- 10-Song Trending Bollywood / Hindi Indie Master Playlist (https://youtu.be/InBgERNHf_s).
- Minimalist Warm Ivory Designer Grid (#FAF8F4) with subtle architectural crosshairs.
- 360-degree rotating vinyl record with ambient crimson aura & gold-trimmed label.
- Summer botanical floral petals & dried olive leaves drift organically across margins.
- Rozha One luxury editorial typography with automatic song chapter transitions.
- Real-time audio-reactive spectrum waveform visualizer (FFT-driven).
- Clean Spotify seekbar with real-time timestamps (NO 82 BPM badge, NO Sunday Vibes header).
- Highly optimized for GitHub Actions cloud runners (30+ FPS throughput).
"""

import os
import sys
import time
import math
import subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from scipy.io import wavfile

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Color Palette
BG_COLOR = (250, 248, 244)       # Warm Ivory White
GRID_COLOR = (235, 230, 222)     # Soft Architectural Grid
CROSS_COLOR = (210, 202, 192)    # Subtle Grid Crosshairs
ACCENT_RED = (200, 16, 46)       # Crimson Accent
MUTED_TEXT = (140, 130, 120)     # Warm Taupe
DARK_TEXT = (26, 26, 26)         # Charcoal Black
BAR_TAUPE = (185, 175, 165)      # Visualizer Taupe Flanks
LINE_COLOR = (225, 218, 210)     # Subtle Separator Line

# 10 Song Tracklist Chapters with Authentic Cover Artwork
CHAPTERS = [
    {"title": "BARSAAT", "artist": "BAIRAN  •  TRENDING HINDI INDIE", "start": 0.0, "end": 180.0, "cover": "01_barsaat.jpg"},
    {"title": "ZULFEIN", "artist": "MEHUL MAHESH  •  TRENDING HINDI INDIE", "start": 180.0, "end": 364.0, "cover": "02_zulfein.jpg"},
    {"title": "TU AAJA NE RAAJI", "artist": "FOLK INDIE  •  TRENDING HINDI INDIE", "start": 364.0, "end": 586.0, "cover": "03_tu_aaja_ne_raaji.jpg"},
    {"title": "AARZU", "artist": "ASIM AZHAR  •  TRENDING HINDI INDIE", "start": 586.0, "end": 755.0, "cover": "04_aarzu.jpg"},
    {"title": "MADIRA", "artist": "HARDIK BHARDWAJ  •  TRENDING HINDI INDIE", "start": 755.0, "end": 918.0, "cover": "05_madira.jpg"},
    {"title": "BAIRAN", "artist": "BAIRAN  •  TRENDING HINDI INDIE", "start": 918.0, "end": 1064.0, "cover": "06_bairan.jpg"},
    {"title": "TAAKKNE", "artist": "SARRB  •  TRENDING PUNJABI INDIE", "start": 1064.0, "end": 1284.0, "cover": "07_taakkne.jpg"},
    {"title": "TAARE", "artist": "FARAK  •  TRENDING HINDI INDIE", "start": 1284.0, "end": 1440.0, "cover": "08_taare.jpg"},
    {"title": "DOORON DOORON", "artist": "PARESH PAHUJA  •  TRENDING HINDI INDIE", "start": 1440.0, "end": 1724.0, "cover": "09_dooron_dooron.jpg"},
    {"title": "PAL PAL", "artist": "AFUSIC  •  TRENDING HINDI INDIE", "start": 1724.0, "end": 1910.0, "cover": "10_pal_pal.jpg"}
]

def get_audio_wav(youtube_url, output_wav, local_source=None):
    """Retrieve master audio via local cache or yt-dlp."""
    if os.path.exists(output_wav) and os.path.getsize(output_wav) > 1000000:
        print(f"[OK] Audio WAV ready: {output_wav}", flush=True)
        return output_wav

    if local_source and os.path.exists(local_source):
        print(f"[OK] Found local source ({local_source}). Converting to WAV...", flush=True)
        subprocess.run(["ffmpeg", "-y", "-i", local_source, "-vn", "-ac", "2", "-ar", "44100", output_wav],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return output_wav

    print(f"[INFO] Downloading master audio from {youtube_url} via yt-dlp...", flush=True)
    import yt_dlp
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'wav',
            'preferredquality': '192',
        }],
        'outtmpl': output_wav.replace('.wav', ''),
        'quiet': False,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([youtube_url])
    return output_wav

def create_vinyl_disc(size=520, cover_path=None):
    """High-resolution vinyl disc with realistic grooves and custom song cover art."""
    vinyl = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    vdraw = ImageDraw.Draw(vinyl)
    center = size // 2
    radius = size // 2 - 4

    # Disc body
    vdraw.ellipse([center - radius, center - radius, center + radius, center + radius], fill=(20, 20, 22, 255))

    # Grooves
    for r in range(center - 15, int(radius * 0.42), -6):
        alpha = 110 if r % 18 == 0 else 55
        vdraw.ellipse([center - r, center - r, center + r, center + r], outline=(48, 48, 52, alpha), width=1)

    label_r = int(radius * 0.38)
    
    # Custom track artwork or classic crimson label
    if cover_path and os.path.exists(cover_path):
        try:
            cov = Image.open(cover_path).convert("RGBA")
            min_dim = min(cov.width, cov.height)
            cov_sq = cov.crop(((cov.width - min_dim) // 2, (cov.height - min_dim) // 2,
                              (cov.width + min_dim) // 2, (cov.height + min_dim) // 2))
            cov_resized = cov_sq.resize((label_r * 2, label_r * 2), Image.Resampling.LANCZOS)
            mask = Image.new("L", (label_r * 2, label_r * 2), 0)
            mdraw = ImageDraw.Draw(mask)
            mdraw.ellipse([0, 0, label_r * 2, label_r * 2], fill=255)
            vinyl.paste(cov_resized, (center - label_r, center - label_r), mask)
            vdraw.ellipse([center - label_r, center - label_r, center + label_r, center + label_r],
                          outline=(212, 175, 55, 230), width=3)
        except Exception:
            vdraw.ellipse([center - label_r, center - label_r, center + label_r, center + label_r],
                          fill=(180, 16, 40, 255), outline=(212, 175, 55, 255), width=3)
    else:
        vdraw.ellipse([center - label_r, center - label_r, center + label_r, center + label_r],
                      fill=(180, 16, 40, 255), outline=(212, 175, 55, 255), width=3)

    # Spindle hole
    spindle_r = int(label_r * 0.18)
    vdraw.ellipse([center - spindle_r, center - spindle_r, center + spindle_r, center + spindle_r],
                  fill=(250, 248, 244, 255), outline=(180, 170, 160, 255), width=2)
    return vinyl

def compute_audio_spectrum(audio_mono, sr, fps, num_bars=48):
    """Fast pre-computation of audio FFT frequency spectrum for all frames."""
    total_frames = int(len(audio_mono) / sr * fps)
    samples_per_frame = int(sr / fps)
    freqs = np.logspace(np.log10(40), np.log10(7500), num_bars + 1)

    spectrum_frames = []
    prev_spectrum = np.zeros(num_bars, dtype=np.float32)

    for f in range(total_frames):
        start_idx = f * samples_per_frame
        end_idx = min(len(audio_mono), start_idx + samples_per_frame * 2)
        chunk = audio_mono[start_idx:end_idx]

        if len(chunk) < 256:
            spectrum_frames.append(prev_spectrum * 0.8)
            continue

        window = np.hanning(len(chunk))
        fft_vals = np.abs(np.fft.rfft(chunk * window))
        fft_freqs = np.fft.rfftfreq(len(chunk), 1.0 / sr)

        bar_vals = np.zeros(num_bars, dtype=np.float32)
        for b in range(num_bars):
            f_low, f_high = freqs[b], freqs[b + 1]
            mask = (fft_freqs >= f_low) & (fft_freqs < f_high)
            if np.any(mask):
                bar_vals[b] = np.mean(fft_vals[mask])

        bar_vals = np.log1p(bar_vals * 5.0)
        decayed = np.maximum(bar_vals, prev_spectrum * 0.76)
        prev_spectrum = decayed
        spectrum_frames.append(decayed)

    spectrum_matrix = np.array(spectrum_frames, dtype=np.float32)
    max_val = np.percentile(spectrum_matrix, 99.5) + 1e-6
    spectrum_matrix = np.clip(spectrum_matrix / max_val, 0.0, 1.0)
    return spectrum_matrix

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_dir = os.path.join(base_dir, "output")
    os.makedirs(output_dir, exist_ok=True)

    master_output = os.path.join(output_dir, "HINDI_TRENDING_30M_MASTER.mp4")
    temp_wav = os.path.join(base_dir, "raw_stems", "hindi_trending_30m.wav")
    os.makedirs(os.path.dirname(temp_wav), exist_ok=True)

    # 1. Download or get Audio
    yt_url = "https://youtu.be/InBgERNHf_s"
    local_source = os.path.join(base_dir, "raw_stems", "hindi_trending_30m.mp3")
    get_audio_wav(yt_url, temp_wav, local_source=local_source)

    sr, audio_data = wavfile.read(temp_wav)
    if audio_data.ndim == 2:
        audio_mono = audio_data.mean(axis=1)
    else:
        audio_mono = audio_data
    audio_mono = audio_mono.astype(np.float32)
    audio_mono /= (np.max(np.abs(audio_mono)) + 1e-6)

    duration = len(audio_mono) / float(sr)
    fps = 30
    total_frames = int(duration * fps)
    W, H = 1920, 1080

    print(f"[INFO] Master Audio: {duration:.1f}s ({duration/60:.1f} mins) | Frames: {total_frames} @ {fps}fps", flush=True)

    # 2. Typography Setup
    font_hero_path = os.path.join(base_dir, "RozhaOne-Regular.ttf")
    if not os.path.exists(font_hero_path):
        font_hero_path = "arial.ttf"

    font_title = ImageFont.truetype(font_hero_path, 80)
    font_sub = ImageFont.truetype("arial.ttf", 26)
    font_meta = ImageFont.truetype("arial.ttf", 20)

    # 3. Base White Grid Designer Canvas
    grid_size = 60
    base_canvas = Image.new("RGB", (W, H), BG_COLOR)
    bdraw = ImageDraw.Draw(base_canvas)

    for x in range(0, W, grid_size):
        bdraw.line([(x, 0), (x, H)], fill=GRID_COLOR, width=1)
    for y in range(0, H, grid_size):
        bdraw.line([(0, y), (W, y)], fill=GRID_COLOR, width=1)
    for x in range(grid_size, W, grid_size * 2):
        for y in range(grid_size, H, grid_size * 2):
            bdraw.line([(x - 3, y), (x + 3, y)], fill=CROSS_COLOR, width=1)
            bdraw.line([(x, y - 3), (x, y + 3)], fill=CROSS_COLOR, width=1)

    # 4. Vinyl Discs with Dynamic Song Artwork & Ambient Glow
    VINYL_X, VINYL_Y = 460, 520
    vinyl_size = 520
    covers_dir = os.path.join(base_dir, "assets", "track_covers")
    print("[INFO] Generating vinyl turntable discs with official cover art for all 10 tracks...", flush=True)
    chapter_discs = []
    for ch in CHAPTERS:
        cov_file = os.path.join(covers_dir, ch["cover"]) if "cover" in ch else None
        chapter_discs.append(create_vinyl_disc(vinyl_size, cov_file))

    glow_size = vinyl_size + 140
    glow_img = Image.new("RGBA", (glow_size, glow_size), (0, 0, 0, 0))
    gdraw = ImageDraw.Draw(glow_img)
    gc = glow_size // 2
    gdraw.ellipse([gc - vinyl_size // 2 - 20, gc - vinyl_size // 2 - 20,
                   gc + vinyl_size // 2 + 20, gc + vinyl_size // 2 + 20], fill=(200, 16, 46, 50))
    glow_img = glow_img.filter(ImageFilter.GaussianBlur(34))
    base_canvas.paste(glow_img, (VINYL_X - glow_size // 2, VINYL_Y - glow_size // 2), glow_img)

    # 5. Botanical Petals (Phool Girte Hue) Setup
    floral_particles = []
    corner_branch = None
    petals_dir = os.path.join(base_dir, "assets", "botanical_petals")
    if os.path.exists(petals_dir):
        sp_files = sorted([f for f in os.listdir(petals_dir) if f.endswith(".png")])
        sp_imgs = [Image.open(os.path.join(petals_dir, f)).convert("RGBA") for f in sp_files]
        if sp_imgs:
            np.random.seed(110)
            for i in range(16):
                sp = sp_imgs[i % len(sp_imgs)]
                target_w = np.random.randint(45, 90)
                ratio = target_w / sp.width
                target_h = int(sp.height * ratio)
                resized_sp = sp.resize((target_w, target_h), Image.Resampling.LANCZOS)
                alpha_mult = np.random.uniform(0.70, 0.90)
                r, g, b, a = resized_sp.split()
                a = a.point(lambda p: int(p * alpha_mult))
                resized_sp = Image.merge("RGBA", (r, g, b, a))

                rot_cache = [resized_sp.rotate(deg, resample=Image.Resampling.BILINEAR, expand=True) for deg in range(0, 360, 15)]
                floral_particles.append({
                    "x": np.random.uniform(60, W - 60),
                    "y": np.random.uniform(40, H - 40),
                    "vx": np.random.uniform(-0.8, -0.2),
                    "vy": np.random.uniform(0.5, 1.2),
                    "base_rot": np.random.uniform(0, 360),
                    "rot_speed": np.random.uniform(12, 28),
                    "phase": np.random.uniform(0, math.pi * 2),
                    "rot_cache": rot_cache
                })

            if len(sp_imgs) >= 16:
                b_sp = sp_imgs[15]
                bw = int(b_sp.width * 0.65)
                bh = int(b_sp.height * 0.65)
                b_sp = b_sp.resize((bw, bh), Image.Resampling.LANCZOS)
                r, g, b, a = b_sp.split()
                a = a.point(lambda p: int(p * 0.65))
                corner_branch = Image.merge("RGBA", (r, g, b, a)).rotate(-25, expand=True)

    # 6. Audio-Reactive Spectrum
    num_bars = 48
    bar_w, bar_gap = 7, 6
    total_bar_w = num_bars * (bar_w + bar_gap)
    TEXT_CENTER_X = 1250
    vis_start_x = TEXT_CENTER_X - total_bar_w // 2
    vis_base_y = 610
    active_range_start = int(num_bars * 0.28)
    active_range_end = int(num_bars * 0.72)

    print("[INFO] Computing real-time FFT spectrum...", flush=True)
    spectrum_matrix = compute_audio_spectrum(audio_mono, sr, fps, num_bars)

    # Base NumPy canvas for high-speed cloning
    base_arr = np.array(base_canvas)

    # 7. Launch FFmpeg Encoder
    ffmpeg_cmd = [
        "ffmpeg", "-y",
        "-f", "rawvideo",
        "-pix_fmt", "rgb24",
        "-s", f"{W}x{H}",
        "-r", str(fps),
        "-i", "-",
        "-i", temp_wav,
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "20",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "256k",
        "-shortest",
        master_output
    ]

    print(f"[INFO] Launching FFmpeg encoder pipe: {master_output}...", flush=True)
    proc = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    total_min = int(duration // 60)
    total_sec = int(duration % 60)
    total_dur_str = f"{total_min:02d}:{total_sec:02d}"

    deg_per_frame = 200.0 / fps
    start_time = time.time()
    last_print = start_time

    for f_idx in range(total_frames):
        t = f_idx / fps

        # Find Current Active Chapter
        cur_ch = CHAPTERS[-1]
        cur_ch_idx = len(CHAPTERS) - 1
        for idx, ch in enumerate(CHAPTERS):
            if ch["start"] <= t < ch["end"]:
                cur_ch = ch
                cur_ch_idx = idx
                break

        # Clone Base Canvas
        frame = Image.fromarray(base_arr.copy())
        draw = ImageDraw.Draw(frame)

        # 1. Paste Rotating Vinyl with Track-Specific Artwork
        deg = int((f_idx * deg_per_frame) % 360)
        cur_vinyl = chapter_discs[cur_ch_idx].rotate(-deg, resample=Image.Resampling.BILINEAR)
        frame.paste(cur_vinyl, (VINYL_X - vinyl_size // 2, VINYL_Y - vinyl_size // 2), cur_vinyl)

        # 2. Drifting Botanical Petals (Phool Girte Hue)
        if floral_particles:
            for p in floral_particles:
                px = int((p["x"] + p["vx"] * t * 38 + math.sin(t * 1.4 + p["phase"]) * 16) % W)
                py = int((p["y"] + p["vy"] * t * 38 + math.cos(t * 1.1 + p["phase"]) * 10) % H)
                rot = (p["base_rot"] + t * p["rot_speed"] + math.sin(t * 1.6 + p["phase"]) * 16) % 360
                # Protect title & artist text readability
                if 1050 < px < 1500 and 380 < py < 530:
                    py = (py + 160) % (H - 80)
                rot_sprite = p["rot_cache"][int(rot / 15) % len(p["rot_cache"])]
                frame.paste(rot_sprite, (px - rot_sprite.width // 2, py - rot_sprite.height // 2), rot_sprite)

            if corner_branch:
                frame.paste(corner_branch, (W - corner_branch.width - 25, H - corner_branch.height - 25), corner_branch)

        # 3. Dynamic Chapter Title & Artist (Rozha One Editorial)
        draw.text((TEXT_CENTER_X, 420), cur_ch["title"], font=font_title, fill=DARK_TEXT, anchor="mm")
        draw.text((TEXT_CENTER_X, 490), cur_ch["artist"], font=font_sub, fill=MUTED_TEXT, anchor="mm")

        # 4. Live Audio-Reactive Spectrum Waveform Bars
        cur_spec = spectrum_matrix[f_idx]
        for b in range(num_bars):
            val = cur_spec[b]
            h_bar = int(8 + val * 105)
            bx = vis_start_x + b * (bar_w + bar_gap)
            bar_color = ACCENT_RED if (active_range_start <= b <= active_range_end) else BAR_TAUPE
            draw.rounded_rectangle([bx, vis_base_y - h_bar // 2, bx + bar_w, vis_base_y + h_bar // 2],
                                  radius=3, fill=bar_color)

        # 5. Clean Spotify Seekbar
        bar_x1, bar_x2 = 280, W - 280
        bar_y = 960
        progress_u = min(1.0, max(0.0, t / duration))
        draw.line([(bar_x1, bar_y), (bar_x2, bar_y)], fill=LINE_COLOR, width=2)
        cur_px = int(bar_x1 + (bar_x2 - bar_x1) * progress_u)
        draw.line([(bar_x1, bar_y), (cur_px, bar_y)], fill=ACCENT_RED, width=3)
        draw.ellipse([cur_px - 7, bar_y - 7, cur_px + 7, bar_y + 7], fill=ACCENT_RED)

        cur_str = f"{int(t // 60):02d}:{int(t % 60):02d}"
        draw.text((bar_x1 - 50, bar_y), cur_str, font=font_meta, fill=MUTED_TEXT, anchor="mm")
        draw.text((bar_x2 + 50, bar_y), total_dur_str, font=font_meta, fill=MUTED_TEXT, anchor="mm")

        # Send raw bytes to FFmpeg stdin
        proc.stdin.write(frame.tobytes())

        if time.time() - last_print >= 5.0 or f_idx == total_frames - 1:
            fps_speed = f_idx / max(0.001, time.time() - start_time)
            pct = (f_idx / total_frames) * 100.0
            print(f"[RENDER] {pct:5.1f}% | Frame {f_idx}/{total_frames} | Speed: {fps_speed:.1f} fps", flush=True)
            last_print = time.time()

    proc.stdin.close()
    proc.wait()

    total_time = time.time() - start_time
    print(f"\n[DONE] Successfully rendered 30-Minute Master Video in {total_time:.1f}s ({total_frames/total_time:.1f} fps):")
    print(f"Path: {master_output}")
    print(f"Size: {os.path.getsize(master_output)/(1024*1024):.2f} MB")

if __name__ == "__main__":
    main()
