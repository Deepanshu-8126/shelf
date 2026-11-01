"""
White Grid Indian Song Visualizer Engine (16:9 Widescreen & 9:16 Vertical Reel)
-------------------------------------------------------------------------------
- Minimalist warm ivory designer grid (#FAF8F4) with subtle crosshairs.
- 360-degree rotating vinyl record with custom album/artist cover art & gold trim.
- Real-time audio-reactive spectrum waveform visualizer (FFT-driven).
- Rozha One luxury editorial typography for Hindi/Punjabi/Indian song titles.
- Minimalist playback seekbar with dynamic elapsed & total timestamps.
- Zero lyric sync headaches, zero CPU overheating, ultra-fast FFmpeg rawvideo pipe.
"""

import os
import sys
import time
import math
import argparse
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

def get_audio_wav(audio_input, temp_wav_path):
    """Ensure audio is accessible as standard WAV for FFT processing."""
    if audio_input.lower().endswith(".wav") and os.path.exists(audio_input):
        return audio_input
    
    cmd = [
        "ffmpeg", "-y", "-i", audio_input,
        "-ac", "2", "-ar", "44100",
        temp_wav_path
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return temp_wav_path

def create_vinyl_disc(size=520, cover_path=None):
    """Generate high-resolution vinyl record with grooves and optional cover art."""
    vinyl = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    vdraw = ImageDraw.Draw(vinyl)
    center = size // 2
    radius = size // 2 - 4

    # Vinyl disc body
    vdraw.ellipse([center - radius, center - radius, center + radius, center + radius], fill=(20, 20, 22, 255))

    # Realistic Vinyl Grooves
    for r in range(center - 15, int(radius * 0.42), -6):
        alpha = 110 if r % 18 == 0 else 55
        vdraw.ellipse([center - r, center - r, center + r, center + r], outline=(48, 48, 52, alpha), width=1)

    label_r = int(radius * 0.38)

    # Center artwork or classic crimson label
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
            # Gold rim border
            vdraw.ellipse([center - label_r, center - label_r, center + label_r, center + label_r],
                          outline=(212, 175, 55, 230), width=3)
        except Exception:
            vdraw.ellipse([center - label_r, center - label_r, center + label_r, center + label_r],
                          fill=(180, 16, 40, 255), outline=(212, 175, 55, 255), width=2)
    else:
        vdraw.ellipse([center - label_r, center - label_r, center + label_r, center + label_r],
                      fill=(180, 16, 40, 255), outline=(212, 175, 55, 255), width=2)

    # Spindle hole
    spindle_r = int(label_r * 0.18)
    vdraw.ellipse([center - spindle_r, center - spindle_r, center + spindle_r, center + spindle_r],
                  fill=(250, 248, 244, 255), outline=(180, 170, 160, 255), width=2)
    return vinyl

def compute_audio_spectrum(audio_mono, sr, fps, num_bars=48):
    """Compute real FFT-based frequency magnitudes for each video frame."""
    total_frames = int(len(audio_mono) / sr * fps)
    samples_per_frame = int(sr / fps)
    
    # Frequency band centers (logarithmic spacing for musical perception)
    freqs = np.logspace(np.log10(40), np.log10(7500), num_bars + 1)
    
    spectrum_frames = []
    prev_spectrum = np.zeros(num_bars, dtype=np.float32)
    
    # Pre-compute FFT for all frames
    for f in range(total_frames):
        start_idx = f * samples_per_frame
        end_idx = min(len(audio_mono), start_idx + samples_per_frame * 2)
        chunk = audio_mono[start_idx:end_idx]
        
        if len(chunk) < 256:
            spectrum_frames.append(prev_spectrum * 0.8)
            continue
            
        # Hanning window for smooth spectral leakage control
        window = np.hanning(len(chunk))
        fft_vals = np.abs(np.fft.rfft(chunk * window))
        fft_freqs = np.fft.rfftfreq(len(chunk), 1.0 / sr)
        
        bar_vals = np.zeros(num_bars, dtype=np.float32)
        for b in range(num_bars):
            f_low, f_high = freqs[b], freqs[b + 1]
            mask = (fft_freqs >= f_low) & (fft_freqs < f_high)
            if np.any(mask):
                bar_vals[b] = np.mean(fft_vals[mask])
        
        # Logarithmic compression & normalization
        bar_vals = np.log1p(bar_vals * 5.0)
        
        # Smooth decay envelope (visual persistence without jitter)
        decayed = np.maximum(bar_vals, prev_spectrum * 0.76)
        prev_spectrum = decayed
        spectrum_frames.append(decayed)
        
    spectrum_matrix = np.array(spectrum_frames, dtype=np.float32)
    max_val = np.percentile(spectrum_matrix, 99.5) + 1e-6
    spectrum_matrix = np.clip(spectrum_matrix / max_val, 0.0, 1.0)
    return spectrum_matrix

def render_white_grid_video(
    audio_path,
    output_path,
    title="Indian Lo-Fi Master",
    artist="Original Artist",
    badge="● 82 BPM • SLOWED + REVERB",
    header="INDIAN LO-FI MASTERS  •  EXCLUSIVE SUNDAY VIBES",
    cover_path=None,
    aspect="16:9",
    fps=30
):
    """Render the master video with audio-reactive visualizer and spinning vinyl."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    temp_wav = os.path.join(base_dir, "scratch", "temp_visualizer_audio.wav")
    os.makedirs(os.path.dirname(temp_wav), exist_ok=True)
    
    print(f"[INFO] Preparing audio stream from: {audio_path}", flush=True)
    wav_file = get_audio_wav(audio_path, temp_wav)
    
    sr, audio_data = wavfile.read(wav_file)
    if audio_data.ndim == 2:
        audio_mono = audio_data.mean(axis=1)
    else:
        audio_mono = audio_data
    audio_mono = audio_mono.astype(np.float32)
    max_audio = np.max(np.abs(audio_mono)) + 1e-6
    audio_mono /= max_audio
    
    duration = len(audio_mono) / float(sr)
    total_frames = int(duration * fps)
    
    # Aspect Ratio Layouts
    if aspect == "9:16":
        W, H = 1080, 1920
        num_bars = 42
        bar_w, bar_gap = 8, 7
        vinyl_size = 600
        vinyl_center = (W // 2, 750)
        title_y, sub_y = 1180, 1250
        vis_base_y = 1380
        badge_y = 1490
        seek_y = 1720
        seek_start, seek_end = 140, W - 140
        time_x_left, time_x_right = 95, W - 95
        title_size = 74
        header_y = 220
    else:
        # 16:9 Landscape
        W, H = 1920, 1080
        num_bars = 48
        bar_w, bar_gap = 7, 6
        vinyl_size = 520
        vinyl_center = (460, 520)
        right_cx = 1250
        title_y, sub_y = 380, 445
        vis_base_y = 570
        badge_y = 668
        seek_y = 960
        seek_start, seek_end = 280, W - 280
        time_x_left, time_x_right = 230, W - 230
        title_size = 74
        header_y = 80

    print(f"[INFO] Resolution: {W}x{H} ({aspect}) | Total Frames: {total_frames} ({duration:.1f}s)", flush=True)
    print("[INFO] Computing real-time FFT spectrum...", flush=True)
    spectrum_matrix = compute_audio_spectrum(audio_mono, sr, fps, num_bars)
    
    # Fonts
    font_hero_path = os.path.join(base_dir, "RozhaOne-Regular.ttf")
    if not os.path.exists(font_hero_path):
        font_hero_path = "arial.ttf"
    
    font_title = ImageFont.truetype(font_hero_path, title_size)
    font_sub = ImageFont.truetype("arial.ttf", 26 if aspect == "9:16" else 24)
    font_meta = ImageFont.truetype("arial.ttf", 22 if aspect == "9:16" else 18)
    
    # 1. Base Static Canvas with Designer Grid & Vignette
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
            
    # Title & Subtitle (Static text on background)
    cx = W // 2 if aspect == "9:16" else right_cx
    bdraw.text((cx, title_y), title, fill=DARK_TEXT, font=font_title, anchor="mm")
    bdraw.text((cx, sub_y), artist, fill=MUTED_TEXT, font=font_sub, anchor="mm")
    
    # Pre-render Vinyl & 360-degree rotation cache (0 CPU overhead in loop)
    print(f"[INFO] Pre-caching 360-degree vinyl turntable rotation ({vinyl_size}px)...", flush=True)
    master_vinyl = create_vinyl_disc(vinyl_size, cover_path)
    vinyl_cache = [master_vinyl.rotate(-deg, resample=Image.Resampling.BILINEAR) for deg in range(360)]
    
    # Ambient red glow
    glow_pad = 70
    glow_size = vinyl_size + glow_pad * 2
    glow_img = Image.new("RGBA", (glow_size, glow_size), (0, 0, 0, 0))
    gdraw = ImageDraw.Draw(glow_img)
    gc = glow_size // 2
    gdraw.ellipse([gc - vinyl_size // 2 - 20, gc - vinyl_size // 2 - 20,
                   gc + vinyl_size // 2 + 20, gc + vinyl_size // 2 + 20], fill=(200, 16, 46, 55))
    glow_img = glow_img.filter(ImageFilter.GaussianBlur(38))
    
    # Composite glow into base canvas once
    glow_x = vinyl_center[0] - glow_size // 2
    glow_y = vinyl_center[1] - glow_size // 2
    base_canvas.paste(glow_img, (glow_x, glow_y), glow_img)

    # Botanical Petals (Phool Girte Hue) Setup
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
    
    # Pre-convert base canvas to numpy array for fast copying
    base_arr = np.array(base_canvas)
    
    # Spectrum coordinates
    total_w = num_bars * (bar_w + bar_gap)
    vis_start_x = cx - total_w // 2
    active_range_start = int(num_bars * 0.28)
    active_range_end = int(num_bars * 0.72)
    
    # Setup FFmpeg output pipe
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    ffmpeg_cmd = [
        "ffmpeg", "-y",
        "-f", "rawvideo",
        "-pix_fmt", "rgb24",
        "-s", f"{W}x{H}",
        "-r", str(fps),
        "-i", "-",
        "-i", audio_path,
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "320k",
        "-shortest",
        output_path
    ]
    
    print(f"[INFO] Launching FFmpeg video encoder pipe to: {output_path}", flush=True)
    proc = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # Time formatting helper
    total_min = int(duration // 60)
    total_sec = int(duration % 60)
    dur_str = f"{total_min}:{total_sec:02d}"
    
    print("[INFO] Rendering frames...", flush=True)
    t0 = time.time()
    
    # Rotation speed (approx 33.3 RPM = ~200 deg/sec)
    deg_per_frame = 200.0 / fps
    
    for frame_idx in range(total_frames):
        # 1. Clone base canvas
        frame_img = Image.fromarray(base_arr.copy())
        fdraw = ImageDraw.Draw(frame_img)
        
        # 2. Paste spinning vinyl
        deg = int((frame_idx * deg_per_frame) % 360)
        cur_vinyl = vinyl_cache[deg]
        frame_img.paste(cur_vinyl, (vinyl_center[0] - vinyl_size // 2, vinyl_center[1] - vinyl_size // 2), cur_vinyl)
        
        # 3. Drifting Botanical Petals (Phool Girte Hue)
        cur_t = frame_idx / fps
        if floral_particles:
            for p in floral_particles:
                px = int((p["x"] + p["vx"] * cur_t * 38 + math.sin(cur_t * 1.4 + p["phase"]) * 16) % W)
                py = int((p["y"] + p["vy"] * cur_t * 38 + math.cos(cur_t * 1.1 + p["phase"]) * 10) % H)
                rot = (p["base_rot"] + cur_t * p["rot_speed"] + math.sin(cur_t * 1.6 + p["phase"]) * 16) % 360
                if (cx - 200 < px < cx + 200 and title_y - 40 < py < sub_y + 40):
                    py = (py + 150) % (H - 80)
                rot_sprite = p["rot_cache"][int(rot / 15) % len(p["rot_cache"])]
                frame_img.paste(rot_sprite, (px - rot_sprite.width // 2, py - rot_sprite.height // 2), rot_sprite)

            if corner_branch:
                frame_img.paste(corner_branch, (W - corner_branch.width - 25, H - corner_branch.height - 25), corner_branch)

        # 4. Draw live audio-reactive waveform bars
        cur_spectrum = spectrum_matrix[frame_idx]
        for b in range(num_bars):
            val = cur_spectrum[b]
            h_bar = int(8 + val * 105)
            bx = vis_start_x + b * (bar_w + bar_gap)
            bar_color = ACCENT_RED if (active_range_start <= b <= active_range_end) else BAR_TAUPE
            fdraw.rounded_rectangle([bx, vis_base_y - h_bar // 2, bx + bar_w, vis_base_y + h_bar // 2],
                                   radius=3, fill=bar_color)
            
        # 4. Draw moving seekbar and timestamps
        cur_t = frame_idx / fps
        cur_min = int(cur_t // 60)
        cur_sec = int(cur_t % 60)
        cur_time_str = f"{cur_min}:{cur_sec:02d}"
        
        progress = cur_t / max(duration, 0.001)
        cur_seek_x = int(seek_start + progress * (seek_end - seek_start))
        
        fdraw.line([(seek_start, seek_y), (seek_end, seek_y)], fill=LINE_COLOR, width=3)
        fdraw.line([(seek_start, seek_y), (cur_seek_x, seek_y)], fill=ACCENT_RED, width=4)
        fdraw.ellipse([cur_seek_x - 8, seek_y - 8, cur_seek_x + 8, seek_y + 8], fill=ACCENT_RED)
        
        fdraw.text((time_x_left, seek_y), cur_time_str, fill=MUTED_TEXT, font=font_meta, anchor="mm")
        fdraw.text((time_x_right, seek_y), dur_str, fill=MUTED_TEXT, font=font_meta, anchor="mm")
        
        # 5. Pipe RGB raw bytes to FFmpeg
        proc.stdin.write(frame_img.tobytes())
        
        if frame_idx % (fps * 15) == 0 and frame_idx > 0:
            elapsed = time.time() - t0
            fps_speed = frame_idx / elapsed
            print(f"  Frame {frame_idx}/{total_frames} ({progress*100:.1f}%) | Speed: {fps_speed:.1f} FPS", flush=True)

    proc.stdin.close()
    proc.wait()
    
    total_time = time.time() - t0
    print(f"[SUCCESS] Master video created in {total_time:.1f}s ({total_frames/total_time:.1f} FPS) at:\n -> {output_path}", flush=True)
    
    # Cleanup temp wav if created
    if os.path.exists(temp_wav) and temp_wav != audio_path:
        try:
            os.remove(temp_wav)
        except Exception:
            pass
            
    return output_path

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="White Grid Indian Song Visualizer Master")
    parser.add_argument("--audio", required=True, help="Path to input audio (MP3/WAV)")
    parser.add_argument("--output", required=True, help="Path to output MP4")
    parser.add_argument("--title", default="Indian Lo-Fi Master", help="Song Title")
    parser.add_argument("--artist", default="Original Artist", help="Artist Name")
    parser.add_argument("--badge", default="● 82 BPM • SLOWED + REVERB", help="Subtitle Badge")
    parser.add_argument("--header", default="INDIAN LO-FI MASTERS  •  EXCLUSIVE SUNDAY VIBES", help="Top Header")
    parser.add_argument("--cover", default=None, help="Album/Artist Cover Image for Vinyl Center")
    parser.add_argument("--aspect", default="16:9", choices=["16:9", "9:16"], help="Aspect ratio")
    parser.add_argument("--fps", type=int, default=30, help="Frames per second")
    
    args = parser.parse_args()
    render_white_grid_video(
        audio_path=args.audio,
        output_path=args.output,
        title=args.title,
        artist=args.artist,
        badge=args.badge,
        header=args.header,
        cover_path=args.cover,
        aspect=args.aspect,
        fps=args.fps
    )
