"""
Alfaaz Viral Reel / Short Engine (9:16 Vertical 1080x1920)
-----------------------------------------------------------
- Authentic Aesthetic Hindi Narrative Template (Google Font Rozha One).
- Clean Minimalist Luxury Editorial Header (NO // or generic tags).
- Shimmering Water Caustics light reflection mesh over vintage ivory parchment (#FAF8F4).
- 360-Degree Continuous Rotating Vinyl Record with Gold Rim and Devanagari Medallion.
- Floating Botanical Rose Petals drifting down with sinusoidal wind drift.
- Audio-Reactive Fluid Ripple Wave in negative space.
- Exact Whisper Ground-Truth Synced Devanagari Typography for the viral 'Baaghan Vichon' hook.
- Real-time kinetic line entrance, royal crimson glow aura, and beat-reactive pulse.
- Progress seekbar with elapsed and total time.
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

# Palette
COLOR_BG = (250, 248, 244)        # Luxury Warm Vintage Ivory
COLOR_RED = (200, 16, 46)          # Royal Crimson Red
COLOR_MUTED = (145, 135, 125)      # Editorial Muted Taupe
COLOR_UPCOMING = (165, 155, 145)   # Upcoming Lyric Taupe
COLOR_LINE = (225, 218, 210)       # Accent Dividing Line
GOLD_ACCENT = (212, 160, 48)       # Antique Gold Metallic
DARK_CHARCOAL = (32, 32, 36)       # Rich Charcoal

ROOT_DIR = r"D:\facts_yt\lofi_phonk_empire"
ROZHA_FONT_PATH = os.path.join(ROOT_DIR, "RozhaOne-Regular.ttf")

def get_rozha_font(size=60):
    if os.path.exists(ROZHA_FONT_PATH):
        try:
            return ImageFont.truetype(ROZHA_FONT_PATH, size)
        except Exception:
            pass
    # Fallback to Nirmala UI on Windows
    p = r"C:\Windows\Fonts\Nirmala.ttc"
    if os.path.exists(p):
        try:
            return ImageFont.truetype(p, size)
        except Exception:
            pass
    return ImageFont.load_default()

def get_arial_font(size=20, bold=False):
    c = "arialbd.ttf" if bold else "arial.ttf"
    p = os.path.join("C:\\Windows\\Fonts", c)
    if os.path.exists(p):
        try:
            return ImageFont.truetype(p, size)
        except:
            pass
    return ImageFont.load_default()

def create_spinning_vinyl(size=520):
    vinyl = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(vinyl)
    c = size // 2
    r_outer = size // 2 - 8

    # Outer dark vinyl body
    draw.ellipse([c - r_outer, c - r_outer, c + r_outer, c + r_outer], fill=(18, 18, 20, 255))

    # Concentric grooves
    for gr in range(c - r_outer + 20, c - 70, 7):
        draw.ellipse([c - gr, c - gr, c + gr, c + gr], outline=(38, 38, 44, 180), width=1)
    for gr in range(c - r_outer + 24, c - 70, 14):
        draw.ellipse([c - gr, c - gr, c + gr, c + gr], outline=(54, 54, 62, 130), width=1)

    # Center Medallion
    r_label = 92
    draw.ellipse([c - r_label, c - r_label, c + r_label, c + r_label], fill=(248, 244, 238, 255), outline=GOLD_ACCENT, width=3)
    draw.ellipse([c - r_label + 4, c - r_label + 4, c + r_label - 4, c + r_label - 4], outline=COLOR_RED, width=1)

    f_label = get_rozha_font(size=28)
    f_sub = get_arial_font(size=12)
    draw.text((c, c - 18), "अल्फ़ाज़", font=f_label, fill=COLOR_RED, anchor="mm")
    draw.text((c, c + 20), "VIRAL HOOK", font=f_sub, fill=(110, 100, 90), anchor="mm")

    # Spindle hole
    r_spindle = 14
    draw.ellipse([c - r_spindle, c - r_spindle, c + r_spindle, c + r_spindle], fill=COLOR_BG, outline=GOLD_ACCENT, width=2)
    return vinyl

def precompute_water_caustics(width, height, num_frames=90):
    y_idx, x_idx = np.indices((height, width))
    cache = []
    for c_i in range(num_frames):
        phase = (c_i / num_frames) * 2.0 * np.pi
        w1 = np.sin(x_idx * 0.006 + y_idx * 0.003 + phase)
        w2 = np.cos(x_idx * 0.003 - y_idx * 0.005 + phase * 0.8)
        w3 = np.sin((x_idx + y_idx) * 0.004 - phase * 1.2)
        caust = ((w1 + w2 + w3) / 3.0 + 1.0) / 2.0
        caust = np.power(caust, 3.2)[:, :, np.newaxis]
        cache.append((caust * 24.0).astype(np.float32))
    return cache

def render_alfaaz_reel():
    W, H = 1080, 1920
    FPS = 24
    duration = 45.0
    total_frames = int(FPS * duration)

    root_dir = ROOT_DIR
    audio_path = os.path.join(root_dir, "raw_stems", "audio", "alfaaz_baaghan_vichon_viral_hook.mp3")
    if not os.path.exists(audio_path):
        audio_path = os.path.join(root_dir, "output", "alfaaz_baaghan_vichon_viral_hook.mp3")

    out_dir = os.path.join(root_dir, "output", "reels_9x16")
    os.makedirs(out_dir, exist_ok=True)
    out_mp4 = os.path.join(out_dir, "alfaaz_baaghan_vichon_reel_9x16.mp4")
    petals_dir = os.path.join(root_dir, "assets", "botanical_petals")

    print("=" * 65)
    print("RENDERING ALFAAZ VIRAL 9:16 REEL (AUTHENTIC ROZHA ONE HINDI TEMPLATE)")
    print("=" * 65)

    # 1. Audio WAV extraction for FFT & RMS
    temp_wav = os.path.join(root_dir, "output", "temp_alfaaz_mono.wav")
    cmd_wav = ["ffmpeg", "-y", "-i", audio_path, "-ac", "1", "-ar", "44100", temp_wav]
    subprocess.run(cmd_wav, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    sr, audio_mono = wavfile.read(temp_wav)
    audio_mono = audio_mono.astype(np.float32)
    audio_mono /= (np.max(np.abs(audio_mono)) + 1e-6)
    samples_per_frame = int(sr / FPS)

    # 2. Base Parchment Canvas with Subtle Grain & Vignette
    np.random.seed(42)
    base_img = Image.new("RGB", (W, H), COLOR_BG)
    base_arr = np.array(base_img, dtype=np.float32)
    noise = np.random.normal(0, 2.5, (H, W, 1))
    base_arr = np.clip(base_arr + noise, 0, 255)

    y_coords, x_coords = np.ogrid[:H, :W]
    dist = np.sqrt(((x_coords - W/2) / (W/2))**2 + ((y_coords - H/2) / (H/2))**2)
    vignette = np.clip(1.0 - (dist - 0.7) * 0.16, 0.90, 1.0)[:, :, np.newaxis]
    paper_base_arr = base_arr * vignette

    # 3. Floating Dust Particles
    dust_count = 35
    dust_x = np.random.uniform(40, W - 40, dust_count)
    dust_y = np.random.uniform(40, H - 40, dust_count)
    dust_vx = np.random.uniform(-0.4, 0.4, dust_count)
    dust_vy = np.random.uniform(-0.8, -0.2, dust_count)
    dust_sz = np.random.randint(2, 5, dust_count)

    # 4. Water Caustics Cache (90 Frames Looping)
    print("[INFO] Pre-rendering 90-frame looping water caustics reflection mesh...", flush=True)
    caustic_cache = precompute_water_caustics(W, H, num_frames=90)

    # 5. Spinning Vinyl Setup
    vinyl_size = 500
    vinyl_cx = W // 2
    vinyl_cy = 480
    master_vinyl = create_spinning_vinyl(vinyl_size)
    print("[INFO] Pre-caching vinyl rotation table for turbo speed...", flush=True)
    vinyl_cache = [master_vinyl.rotate(deg, resample=Image.Resampling.BILINEAR) for deg in range(0, 360, 2)]

    # 6. Botanical Rose Petals (Phool Girte Hue)
    petals = []
    if os.path.exists(petals_dir):
        pfiles = sorted([f for f in os.listdir(petals_dir) if f.endswith(".png")])
        pimgs = [Image.open(os.path.join(petals_dir, f)).convert("RGBA") for f in pfiles]
        if pimgs:
            np.random.seed(99)
            for i in range(18):
                sp = pimgs[i % len(pimgs)]
                tw = np.random.randint(38, 70)
                ratio = tw / sp.width
                th = int(sp.height * ratio)
                scaled_sp = sp.resize((tw, th), Image.Resampling.LANCZOS)
                alpha_mult = np.random.uniform(0.60, 0.85)
                r, g, b, a = scaled_sp.split()
                a = a.point(lambda p: int(p * alpha_mult))
                scaled_sp = Image.merge("RGBA", (r, g, b, a))
                rot_cache = [scaled_sp.rotate(d, resample=Image.Resampling.BILINEAR, expand=True) for d in range(0, 360, 15)]

                petals.append({
                    "x": np.random.uniform(50, W - 50),
                    "y": np.random.uniform(0, H),
                    "vx": np.random.uniform(-0.6, 0.4),
                    "vy": np.random.uniform(0.7, 1.6),
                    "rot_speed": np.random.uniform(14, 28),
                    "phase": np.random.uniform(0, math.pi * 2),
                    "cache": rot_cache
                })

    # 7. Typography
    font_hero = get_rozha_font(size=64)
    font_sub_lyric = get_rozha_font(size=54)
    font_card3 = get_rozha_font(size=48)
    font_header_title = get_rozha_font(size=40)
    font_header_meta = get_arial_font(size=22)
    font_time = get_arial_font(size=20)

    # 8. Synced Narrative Cards (Whisper Ground Truth Alignment)
    cards_config = [
        # Card 1: Intro (0.0s -> 5.5s)
        {
            "start": 0.0,
            "end": 5.5,
            "items": [
                {"text": "वेखां तैनूं रात सारी चढ़दी सवेर तक...", "time": 0.50, "y": 980, "font": font_hero}
            ]
        },
        # Card 2: The Viral Hook Drop (5.5s -> 17.2s)
        {
            "start": 5.5,
            "end": 17.2,
            "items": [
                {"text": "बाग़ां विचों मैं ते तोड़े तेरे लई गुलाब वे,", "time": 5.76, "y": 960, "font": font_hero},
                {"text": "मैं ते बस कहंदा रहंदा आप जनाब वे!", "time": 11.76, "y": 1100, "font": font_hero}
            ]
        },
        # Card 3: The Starlight Hook (17.2s -> 29.2s)
        {
            "start": 17.2,
            "end": 29.2,
            "items": [
                {"text": "तू ते तारेयां तों वी सोहणा ऐ,", "time": 17.44, "y": 880, "font": font_card3},
                {"text": "तेरे वरगा कोई ना होणा ऐ!", "time": 20.16, "y": 990, "font": font_card3},
                {"text": "तू ते तारेयां तों वी सोहणा ऐ,", "time": 23.20, "y": 1100, "font": font_card3},
                {"text": "तेरे वरगा कोई ना होणा ऐ!", "time": 26.16, "y": 1210, "font": font_card3}
            ]
        },
        # Card 4: The Love Climax (29.2s -> 42.0s)
        {
            "start": 29.2,
            "end": 42.0,
            "items": [
                {"text": "जिन्हां आउंदा सी मैनूं प्यार करना जी,", "time": 29.72, "y": 960, "font": font_hero},
                {"text": "मैं ते तेरे नाल कर लेया ऐ...", "time": 34.00, "y": 1100, "font": font_hero}
            ]
        }
    ]

    # Pre-render soft aura glow for each line
    word_aura_cache = {}
    for card in cards_config:
        for item in card["items"]:
            txt = item["text"]
            f = item["font"]
            bbox = f.getbbox(txt)
            bw = bbox[2] - bbox[0] + 70
            bh = bbox[3] - bbox[1] + 70
            g_box = Image.new("RGBA", (bw, bh), (0, 0, 0, 0))
            g_draw = ImageDraw.Draw(g_box)
            g_draw.text((bw // 2, bh // 2), txt, font=f, fill=(*COLOR_RED, 65), anchor="mm")
            word_aura_cache[txt] = g_box.filter(ImageFilter.GaussianBlur(10))

    # Helper: Render Narrative Card Layer
    def render_card_layer(items, cur_t, global_alpha=1.0, card_offset_y=0, rms=0.0):
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ldraw = ImageDraw.Draw(layer)

        # Active line index
        active_idx = -1
        for idx, item in enumerate(items):
            if cur_t >= item["time"]:
                active_idx = idx

        for idx, item in enumerate(items):
            txt = item["text"]
            f = item["font"]
            base_cy = item["y"] + card_offset_y

            if active_idx == -1:
                # Pre-entrance: Upcoming taupe
                alpha = int(170 * global_alpha)
                ldraw.text((W // 2, base_cy), txt, font=f, fill=(*COLOR_UPCOMING, alpha), anchor="mm")

            elif idx < active_idx:
                # Past lines: Muted taupe/charcoal with subtle upward drift
                time_passed = cur_t - items[active_idx]["time"]
                p_u = min(1.0, max(0.0, time_passed / 0.40))
                p_ease = 1.0 - pow(1.0 - p_u, 3)
                line_dy = -int(14.0 * p_ease)
                alpha = int(175 * global_alpha)
                ldraw.text((W // 2, base_cy + line_dy), txt, font=f, fill=(*COLOR_MUTED, alpha), anchor="mm")

            elif idx == active_idx:
                # Current active line: Entrance slide-up + Beat Pulse + Royal Crimson Focus
                line_age = cur_t - item["time"]
                line_u = min(1.0, max(0.0, line_age / 0.28))
                line_ease = 1.0 - pow(1.0 - line_u, 3)
                line_dy = int(14.0 * (1.0 - line_ease))

                beat_scale = 1.0 + min(0.04, rms * 0.25)
                cy = base_cy + line_dy

                # Soft Royal Crimson ambient aura glow
                aura = word_aura_cache.get(txt)
                if aura is not None and global_alpha > 0.3:
                    layer.paste(aura, (W // 2 - aura.width // 2, cy - aura.height // 2), aura)

                # Draw active text with kinetic beat-pulse
                if abs(beat_scale - 1.0) < 0.01:
                    ldraw.text((W // 2, cy), txt, font=f, fill=(*COLOR_RED, int(255 * global_alpha)), anchor="mm")
                else:
                    bbox = f.getbbox(txt)
                    bw, bh = bbox[2] - bbox[0] + 40, bbox[3] - bbox[1] + 40
                    t_box = Image.new("RGBA", (bw, bh), (0, 0, 0, 0))
                    b_draw = ImageDraw.Draw(t_box)
                    b_draw.text((bw // 2, bh // 2), txt, font=f, fill=(*COLOR_RED, int(255 * global_alpha)), anchor="mm")
                    nw, nh = max(1, int(bw * beat_scale)), max(1, int(bh * beat_scale))
                    resz = t_box.resize((nw, nh), resample=Image.BICUBIC)
                    layer.paste(resz, (W // 2 - nw // 2, cy - nh // 2), resz)

            else:
                # Upcoming lines: Clearly legible, elegant warm taupe
                alpha = int(165 * global_alpha)
                ldraw.text((W // 2, base_cy), txt, font=f, fill=(*COLOR_UPCOMING, alpha), anchor="mm")

        return layer

    # 9. FFmpeg Streaming Pipe
    out_cmd = [
        "ffmpeg", "-y",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-s", f"{W}x{H}",
        "-pix_fmt", "rgb24",
        "-r", str(FPS),
        "-i", "-",
        "-i", audio_path,
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "320k",
        "-shortest",
        out_mp4
    ]
    proc = subprocess.Popen(out_cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    print(f"[INFO] Encoding {total_frames} frames into 9:16 Vertical Master...", flush=True)
    start_time = time.time()
    last_print = start_time

    for f_idx in range(total_frames):
        cur_t = f_idx / FPS

        # Audio RMS energy
        idx_s = f_idx * samples_per_frame
        idx_e = min(len(audio_mono), idx_s + samples_per_frame * 2)
        chunk = audio_mono[idx_s:idx_e]
        rms = float(np.sqrt(np.mean(chunk**2))) if len(chunk) > 0 else 0.0

        # 1. Base Frame with Shimmering Water Caustics
        caust = caustic_cache[f_idx % len(caustic_cache)]
        frame_arr = np.clip(paper_base_arr + caust, 0, 255)
        frame = Image.fromarray(np.uint8(frame_arr))
        draw = ImageDraw.Draw(frame)

        # 2. Floating Dust Particles
        for i in range(dust_count):
            px = int((dust_x[i] + dust_vx[i] * f_idx) % W)
            py = int((dust_y[i] + dust_vy[i] * f_idx) % H)
            draw.ellipse([px, py, px + dust_sz[i], py + dust_sz[i]], fill=(215, 208, 198))

        # 3. Clean Minimalist Luxury Editorial Header (NO //)
        header_y = 120
        draw.text((W // 2, header_y - 25), "अल्फ़ाज़   •   ALFAAZ", font=font_header_title, fill=(35, 35, 38), anchor="mm")
        draw.text((W // 2, header_y + 25), "HAMZA MALIK   x   ZAIN ZOHAIB", font=font_header_meta, fill=COLOR_MUTED, anchor="mm")
        draw.line([(W // 2 - 200, header_y + 55), (W // 2 + 200, header_y + 55)], fill=COLOR_LINE, width=2)

        # 4. Spinning Vinyl Disc
        deg_idx = int((f_idx * 4.0) % 360 // 2)
        v_img = vinyl_cache[deg_idx]
        frame.paste(v_img, (vinyl_cx - vinyl_size // 2, vinyl_cy - vinyl_size // 2), v_img)

        # 5. Botanical Rose Petals (Phool Girte Hue)
        for p in petals:
            px = int((p["x"] + p["vx"] * cur_t * 30 + math.sin(cur_t * 1.5 + p["phase"]) * 18) % W)
            py = int((p["y"] + p["vy"] * cur_t * 32 + math.cos(cur_t * 1.2 + p["phase"]) * 12) % H)
            rot = (cur_t * p["rot_speed"]) % 360
            rot_idx = int(rot / 15) % len(p["cache"])
            sprite = p["cache"][rot_idx]
            frame.paste(sprite, (px - sprite.width // 2, py - sprite.height // 2), sprite)

        # 6. Audio-Reactive Fluid Ripple Wave in negative space
        ripple_y = 1380
        wave_pts = []
        for rx in range(280, 801, 10):
            w_offset = math.sin((rx * 0.02) + (cur_t * 4.0)) * (4.0 + rms * 14.0)
            wave_pts.append((rx, ripple_y + w_offset))
        draw.line(wave_pts, fill=(215, 190, 185), width=2)

        # 7. Synced Narrative Stanzas / Cards
        TRANSITION_DUR = 0.65
        for c_idx, card in enumerate(cards_config):
            c_start = card["start"]
            c_end = card["end"]

            if c_start <= cur_t <= c_end:
                alpha = 1.0
                card_offset_y = 0

                # Entrance transition from previous card
                if c_idx > 0 and (cur_t - c_start) < TRANSITION_DUR:
                    u = (cur_t - c_start) / TRANSITION_DUR
                    ease = 1.0 - pow(1.0 - u, 3)
                    alpha = ease
                    card_offset_y = int(25 * (1.0 - ease))

                # Exit transition to next card
                elif c_idx < len(cards_config) - 1 and (c_end - cur_t) < TRANSITION_DUR:
                    u = (c_end - cur_t) / TRANSITION_DUR
                    ease = 1.0 - pow(1.0 - u, 3)
                    alpha = ease
                    card_offset_y = int(-25 * (1.0 - ease))

                card_layer = render_card_layer(card["items"], cur_t, global_alpha=alpha, card_offset_y=card_offset_y, rms=rms)
                frame.paste(card_layer, (0, 0), card_layer)

        # 8. Spotify Style Progress Bar & Timestamps
        sb_y = 1680
        sb_x0, sb_x1 = 160, W - 160
        sb_w = sb_x1 - sb_x0
        draw.line([(sb_x0, sb_y), (sb_x1, sb_y)], fill=COLOR_LINE, width=4)
        prog = min(1.0, max(0.0, cur_t / duration))
        active_x = int(sb_x0 + prog * sb_w)
        draw.line([(sb_x0, sb_y), (active_x, sb_y)], fill=COLOR_RED, width=4)
        draw.ellipse([active_x - 7, sb_y - 7, active_x + 7, sb_y + 7], fill=COLOR_RED)

        cur_m, cur_s = int(cur_t // 60), int(cur_t % 60)
        tot_m, tot_s = int(duration // 60), int(duration % 60)
        draw.text((sb_x0, sb_y + 24), f"{cur_m}:{cur_s:02d}", font=font_time, fill=COLOR_MUTED, anchor="lm")
        draw.text((sb_x1, sb_y + 24), f"{tot_m}:{tot_s:02d}", font=font_time, fill=COLOR_MUTED, anchor="rm")

        proc.stdin.write(frame.tobytes())

        now = time.time()
        if now - last_print >= 4.0 or f_idx == total_frames - 1:
            fps_speed = (f_idx + 1) / (now - start_time + 1e-6)
            pct = ((f_idx + 1) / total_frames) * 100.0
            print(f"[REEL] {pct:5.1f}% | Frame {f_idx+1}/{total_frames} | Speed: {fps_speed:.1f} fps", flush=True)
            last_print = now

    proc.stdin.close()
    proc.wait()

    if os.path.exists(temp_wav):
        try:
            os.remove(temp_wav)
        except:
            pass

    out_mb = os.path.getsize(out_mp4) / (1024 * 1024)
    print(f"\n[DONE] Rendered Viral Hindi Reel: {out_mp4}")
    print(f"Size: {out_mb:.2f} MB | Resolution: {W}x{H} (9:16 Vertical)")
    return out_mp4

if __name__ == "__main__":
    render_alfaaz_reel()
