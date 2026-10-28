"""
Phonk Soundwave Dagger Engine (Production Locked)
-----------------------------------------------
Features:
- High-contrast Gym / Manga aesthetic with audio-reactive Soundwave Dagger Blade
- Depth-layered atmospheric particles (out-of-focus foreground bokeh + midground embers)
- 808 Sub-bass beat pump (full-screen exposure lift)
- Chromatic aberration RGB channel split on heavy bass kicks
- Visceral camera micro-shake (1-2px)
- 35mm film grain & CRT scanline overlay
"""

import os
import shutil
import subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from scipy.io import wavfile
from pydub import AudioSegment

class PhonkDaggerEngine:
    def __init__(self):
        self.W, self.H = 1920, 1080
        self.FPS = 30

    def extract_audio_slice(self, raw_audio_path, start_sec, duration_sec, output_wav_path):
        """Extracts audio slice with smooth crossfades."""
        aud = AudioSegment.from_file(raw_audio_path)
        start_ms = int(start_sec * 1000)
        end_ms = start_ms + int(duration_sec * 1000)
        sliced = aud[start_ms:end_ms].fade_in(40).fade_out(100)
        sliced.export(output_wav_path, format="wav")
        return output_wav_path

    def render(self, audio_path, base_img_path, title="[DOPAMINE]", subtitle="will make you the main character",
               track_label="AINSI BAS LA VIDA  •  SUPER SLOWED", duration=5.0, output_mp4=None):
        W, H = self.W, self.H
        FPS = self.FPS
        TOTAL_FRAMES = int(duration * FPS)

        if output_mp4 is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            output_mp4 = os.path.join(base_dir, "output", f"phonk_dagger_{duration}s_master.mp4")
            os.makedirs(os.path.dirname(output_mp4), exist_ok=True)

        tmp_frames = os.path.join(os.path.dirname(output_mp4), "tmp_frames_phonk")
        if os.path.exists(tmp_frames):
            shutil.rmtree(tmp_frames)
        os.makedirs(tmp_frames, exist_ok=True)

        # 1. Audio Processing
        sr, audio_data = wavfile.read(audio_path)
        if audio_data.ndim == 2:
            audio_mono = audio_data.mean(axis=1)
        else:
            audio_mono = audio_data
        audio_mono = audio_mono.astype(np.float32)
        audio_mono /= (np.max(np.abs(audio_mono)) + 1e-6)
        samples_per_frame = int(sr / FPS)

        # 2. Base Artwork
        base_art = Image.open(base_img_path).convert("RGBA")
        if base_art.size != (W, H):
            base_art = base_art.resize((W, H), resample=Image.LANCZOS)

        # Fonts
        font_title = ImageFont.truetype("arialbd.ttf", 74)
        font_sub = ImageFont.truetype("arial.ttf", 26)
        font_meta = ImageFont.truetype("arial.ttf", 20)

        # Coordinates
        TEXT_CX = 1600
        TITLE_Y = 130
        SUB_Y = 185

        HILT_CX = 1380
        HILT_CY = 280
        BLADE_START_X = 1400
        BLADE_END_X = 1850
        BLADE_Y = 280
        NUM_BARS = 62
        bar_xs = np.linspace(BLADE_START_X, BLADE_END_X, NUM_BARS)

        # Atmospheric Particles
        np.random.seed(42)
        fg_count = 16
        fg_x = np.random.uniform(50, W - 50, fg_count)
        fg_y = np.random.uniform(50, H - 50, fg_count)
        fg_vx = np.random.uniform(-1.2, 1.2, fg_count)
        fg_vy = np.random.uniform(-2.5, -1.0, fg_count)
        fg_size = np.random.randint(8, 16, fg_count)

        mg_count = 65
        mg_x = np.random.uniform(20, W - 20, mg_count)
        mg_y = np.random.uniform(20, H - 20, mg_count)
        mg_vx = np.random.uniform(-0.8, 0.8, mg_count)
        mg_vy = np.random.uniform(-1.8, -0.6, mg_count)
        mg_size = np.random.randint(2, 6, mg_count)

        # Vignette mask
        y_coords, x_coords = np.ogrid[:H, :W]
        dist_from_center = np.sqrt(((x_coords - W/2) / (W/2))**2 + ((y_coords - H/2) / (H/2))**2)
        vignette_mask = np.clip(1.0 - (dist_from_center - 0.75) * 0.28, 0.80, 1.0)[:, :, np.newaxis]

        print(f"Rendering {TOTAL_FRAMES} frames (Phonk Soundwave Dagger Master)...")

        for f_idx in range(TOTAL_FRAMES):
            idx_start = f_idx * samples_per_frame
            idx_end = min(len(audio_mono), idx_start + samples_per_frame * 2)
            chunk = audio_mono[idx_start:idx_end]
            
            rms = np.sqrt(np.mean(chunk**2)) if len(chunk) > 0 else 0.0
            bass_scale = min(1.85, 0.6 + rms * 2.8)
            
            shake_x = int(np.random.uniform(-2.5, 2.5) * (rms**1.5))
            shake_y = int(np.random.uniform(-2.5, 2.5) * (rms**1.5))

            # Slow push zoom
            zoom = 1.0 + 0.025 * (f_idx / TOTAL_FRAMES)
            zw, zh = int(W * zoom), int(H * zoom)
            frame_zoomed = base_art.resize((zw, zh), resample=Image.BILINEAR)
            crop_x = (zw - W) // 2
            crop_y = (zh - H) // 2
            frame = frame_zoomed.crop((crop_x, crop_y, crop_x + W, crop_y + H))
            draw = ImageDraw.Draw(frame)

            # Title & Subtitle
            draw.text((TEXT_CX + shake_x, TITLE_Y + shake_y), title, font=font_title, fill=(14, 15, 18, 255), anchor="mm")
            draw.text((TEXT_CX + shake_x, SUB_Y + shake_y), subtitle, font=font_sub, fill=(55, 60, 68, 230), anchor="mm")

            # Dagger Hilt
            h_cx = HILT_CX + shake_x
            h_cy = HILT_CY + shake_y
            draw.line([(h_cx - 12, h_cy - 65), (h_cx - 4, h_cy - 35)], fill=(185, 15, 32, 255), width=12)
            draw.line([(h_cx - 4, h_cy - 35), (h_cx + 16, h_cy + 55)], fill=(18, 20, 24, 255), width=15)
            for step in range(-30, 48, 13):
                gx = h_cx + int(step * 0.22)
                gy = h_cy + step
                draw.line([(gx - 8, gy + 3), (gx + 8, gy - 3)], fill=(55, 58, 65, 255), width=3)

            # Frequency Waveform Blade
            fft_vals = np.abs(np.fft.rfft(chunk, n=256)) if len(chunk) > 0 else np.zeros(128)
            fft_vals = fft_vals[:NUM_BARS] if len(fft_vals) >= NUM_BARS else np.pad(fft_vals, (0, NUM_BARS - len(fft_vals)))
            fft_norm = fft_vals / (np.max(fft_vals) + 1e-6)
            blade_y_pos = BLADE_Y + shake_y

            for i, bx in enumerate(bar_xs):
                bx_cur = bx + shake_x
                taper = (1.0 - (i / NUM_BARS))**1.75
                freq_energy = fft_norm[i] * 0.7 + rms * 0.5
                bar_h = max(2, int(60 * taper * bass_scale * (0.35 + 0.65 * freq_energy)))

                draw.line([(bx_cur, blade_y_pos - bar_h), (bx_cur, blade_y_pos + bar_h)], fill=(18, 20, 24, 255), width=4)
                draw.line([(bx_cur, blade_y_pos - 2), (bx_cur, blade_y_pos + 2)], fill=(185, 15, 32, 255), width=4)

            # Track footer
            draw.text((TEXT_CX + shake_x, 355 + shake_y), track_label, font=font_meta, fill=(120, 125, 135, 240), anchor="mm")

            # Midground particles
            for i in range(mg_count):
                px = (mg_x[i] + mg_vx[i] * f_idx) % W
                py = (mg_y[i] + mg_vy[i] * f_idx) % H
                sz = mg_size[i]
                if py > 550:
                    p_col = (255, 190, 160, 200) if (px < 900) else (160, 220, 255, 200)
                else:
                    p_col = (130, 135, 150, 140)
                draw.ellipse([px, py, px + sz, py + sz], fill=p_col)

            # Foreground bokeh layer
            bokeh_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            bdraw = ImageDraw.Draw(bokeh_layer)
            for i in range(fg_count):
                px = (fg_x[i] + fg_vx[i] * f_idx) % W
                py = (fg_y[i] + fg_vy[i] * f_idx) % H
                sz = fg_size[i]
                b_col = (255, 140, 120, 70) if (px < 950) else (140, 180, 255, 60)
                bdraw.ellipse([px, py, px + sz, py + sz], fill=b_col)
            bokeh_layer = bokeh_layer.filter(ImageFilter.GaussianBlur(5))
            frame = Image.alpha_composite(frame, bokeh_layer)

            # Post-processing
            frame_rgb = frame.convert("RGB")
            frame_arr = np.array(frame_rgb, dtype=np.float32)

            # Chromatic Aberration on 808 drop
            if rms > 0.32:
                split_px = int(np.clip((rms - 0.32) * 14, 1, 3))
                frame_arr[:, split_px:, 0] = frame_arr[:, :-split_px, 0]
                frame_arr[:, :-split_px, 2] = frame_arr[:, split_px:, 2]

            # Bass exposure pump
            bass_pump = 1.0 + (rms**1.5) * 0.09
            frame_arr = np.clip(frame_arr * bass_pump, 0, 255)

            # Vignette, 35mm grain & retro scanlines
            frame_arr = frame_arr * vignette_mask
            grain = np.random.normal(0, 2.8, (H, W, 1))
            frame_arr = np.clip(frame_arr + grain, 0, 255)
            frame_arr[::4, :, :] *= 0.965

            frame_crisp = Image.fromarray(np.uint8(frame_arr))
            frame_crisp.save(os.path.join(tmp_frames, f"frame_{f_idx:04d}.jpg"), quality=93)

        # Mux with FFmpeg
        ffmpeg_cmd = [
            "ffmpeg", "-y",
            "-r", str(FPS),
            "-i", os.path.join(tmp_frames, "frame_%04d.jpg"),
            "-i", audio_path,
            "-c:v", "libx264",
            "-preset", "fast",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "192k",
            "-t", str(duration),
            output_mp4
        ]
        res = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
        if res.returncode != 0:
            raise RuntimeError(f"FFmpeg error: {res.stderr}")

        shutil.rmtree(tmp_frames)
        print(f"SUCCESS: Rendered Phonk master to {output_mp4}")
        return output_mp4
