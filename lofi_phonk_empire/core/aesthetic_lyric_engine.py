"""
Aesthetic Lyric Video Engine (Production Locked)
-----------------------------------------------
Features:
- Aspect Ratios: 16:9 Widescreen (with Spinning Glowing Vinyl Record) and 9:16 Vertical (Reel/Shorts)
- Automatic Whisper vocal alignment with millisecond precision
- Google Font Rozha One Devanagari calligraphy rendering
- Procedural handmade paper texture + fine film grain + soft vignette + floating dust
- Full Spotify playback timeline scrubber
"""

import os
import shutil
import argparse
import subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from pydub import AudioSegment
import whisper

class AestheticLyricEngine:
    def __init__(self, font_path=None):
        if font_path is None:
            # Look in parent or root directory
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            font_path = os.path.join(base_dir, "RozhaOne-Regular.ttf")
        self.font_path = font_path
        if not os.path.exists(self.font_path):
            raise FileNotFoundError(f"Font not found at {self.font_path}")

        # Color Palette
        self.COLOR_BG = (250, 248, 244) # Warm vintage parchment
        self.COLOR_RED = (200, 16, 46)   # Deep rich crimson red
        self.COLOR_MUTED = (150, 140, 130)
        self.COLOR_LINE = (225, 218, 210)
        self.COLOR_BAR = (200, 16, 46)

    def extract_vocal_slice(self, raw_audio_path, start_sec, duration_sec, output_wav_path):
        """Cleanly extracts an audio slice with crossfades."""
        audio = AudioSegment.from_file(raw_audio_path)
        start_ms = int(start_sec * 1000)
        end_ms = start_ms + int(duration_sec * 1000)
        slice_audio = audio[start_ms:end_ms]
        slice_audio = slice_audio.fade_in(50).fade_out(150)
        slice_audio.export(output_wav_path, format="wav")
        return output_wav_path

    def auto_align_words(self, audio_wav_path, lang="hi"):
        """Extracts word-level timestamps using Whisper."""
        model = whisper.load_model("base")
        res = model.transcribe(audio_wav_path, language=lang, word_timestamps=True)
        words = []
        for seg in res["segments"]:
            for w in seg.get("words", []):
                words.append({
                    "word": w["word"].strip(),
                    "start": round(w["start"], 2),
                    "end": round(w["end"], 2)
                })
        return words

    def create_master_vinyl(self, size=520, title="HUSN", artist="ANUV JAIN"):
        """Generates an aesthetic high-resolution spinning vinyl disc."""
        disc = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(disc)
        center = size // 2
        r_outer = size // 2 - 12
        
        # Outer dark vinyl
        draw.ellipse([center - r_outer, center - r_outer, center + r_outer, center + r_outer], fill=(16, 16, 18, 255))
        
        # Concentric grooves
        for r in range(center - r_outer + 20, center - 75, 7):
            draw.ellipse([center - r, center - r, center + r, center + r], outline=(36, 36, 42, 190), width=1)
        for r in range(center - r_outer + 24, center - 75, 14):
            draw.ellipse([center - r, center - r, center + r, center + r], outline=(52, 52, 60, 130), width=1)
            
        # Crimson center label
        r_label = 85
        draw.ellipse([center - r_label, center - r_label, center + r_label, center + r_label], fill=(200, 16, 46, 255))
        r_inner = 72
        draw.ellipse([center - r_inner, center - r_inner, center + r_inner, center + r_inner], outline=(245, 235, 220, 220), width=2)
        
        # Center label text
        font_disc = ImageFont.truetype("arial.ttf", 16)
        draw.text((center, center - 35), artist.upper(), font=font_disc, fill=(255, 255, 255, 220), anchor="mm")
        draw.text((center, center + 35), title.upper(), font=font_disc, fill=(255, 255, 255, 220), anchor="mm")
        
        # Spindle hole
        r_hole = 14
        draw.ellipse([center - r_hole, center - r_hole, center + r_hole, center + r_hole], fill=self.COLOR_BG)
        
        # Light sheen wedges
        sheen = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        sdraw = ImageDraw.Draw(sheen)
        sdraw.pieslice([center - r_outer + 5, center - r_outer + 5, center + r_outer - 5, center + r_outer - 5], 35, 65, fill=(255, 255, 255, 30))
        sdraw.pieslice([center - r_outer + 5, center - r_outer + 5, center + r_outer - 5, center + r_outer - 5], 215, 245, fill=(255, 255, 255, 30))
        
        return Image.alpha_composite(disc, sheen)

    def render(self, audio_path, title, artist, lines_config, aspect_ratio="16:9", duration=5.0, fps=30, output_mp4=None, start_offset_label="1:16"):
        """
        Renders the lyric video.
        lines_config: List of dicts, e.g.:
        [
            {"text": "देखो देखो", "time": 0.75, "scale_pop": 0.12},
            {"text": "ये ज़माने से थक कर", "time": 2.30, "scale_pop": 0.12},
            {"text": "आते हो क्यों...", "time": 3.40, "scale_pop": 0.15}
        ]
        """
        is_16x9 = (aspect_ratio == "16:9")
        WIDTH, HEIGHT = (1920, 1080) if is_16x9 else (1080, 1920)
        TOTAL_FRAMES = int(duration * fps)

        if output_mp4 is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            output_dir = os.path.join(base_dir, "output")
            os.makedirs(output_dir, exist_ok=True)
            ratio_tag = "16x9" if is_16x9 else "9x16"
            output_mp4 = os.path.join(output_dir, f"{title.lower()}_{ratio_tag}_master.mp4")

        tmp_frames = os.path.join(os.path.dirname(output_mp4), f"tmp_frames_{aspect_ratio.replace(':', '_')}")
        if os.path.exists(tmp_frames):
            shutil.rmtree(tmp_frames)
        os.makedirs(tmp_frames, exist_ok=True)

        # Fonts
        font_large = ImageFont.truetype(self.font_path, 110 if is_16x9 else 115)
        font_med = ImageFont.truetype(self.font_path, 88 if is_16x9 else 92)
        font_meta = ImageFont.truetype("arial.ttf", 26 if is_16x9 else 28)
        font_time = ImageFont.truetype("arial.ttf", 22)
        font_badge = ImageFont.truetype("arial.ttf", 18)

        # Generate base paper canvas
        np.random.seed(42)
        base_img = Image.new("RGB", (WIDTH, HEIGHT), self.COLOR_BG)
        base_arr = np.array(base_img, dtype=np.float32)
        noise = np.random.normal(0, 3.5, (HEIGHT, WIDTH, 1))
        base_arr = np.clip(base_arr + noise, 0, 255)

        y_coords, x_coords = np.ogrid[:HEIGHT, :WIDTH]
        dist = np.sqrt(((x_coords - WIDTH/2) / (WIDTH/2))**2 + ((y_coords - HEIGHT/2) / (HEIGHT/2))**2)
        vignette = np.clip(1.0 - (dist - 0.7) * 0.15, 0.88, 1.0)[:, :, np.newaxis]
        base_arr = base_arr * vignette
        paper_base = Image.fromarray(np.uint8(base_arr))

        # Dust particles
        num_particles = 30
        dust_x = np.random.uniform(50, WIDTH - 50, num_particles)
        dust_y = np.random.uniform(50, HEIGHT - 50, num_particles)
        dust_vx = np.random.uniform(-0.6, 0.6, num_particles)
        dust_vy = np.random.uniform(-1.0, -0.2, num_particles)
        dust_size = np.random.randint(2, 5, num_particles)

        # 16:9 Vinyl Assets
        if is_16x9:
            master_vinyl = self.create_master_vinyl(520, title, artist)
            glow_size = 620
            glow_img = Image.new("RGBA", (glow_size, glow_size), (0, 0, 0, 0))
            gdraw = ImageDraw.Draw(glow_img)
            g_center = glow_size // 2
            gdraw.ellipse([g_center - 240, g_center - 240, g_center + 240, g_center + 240], fill=(200, 16, 46, 75))
            glow_img = glow_img.filter(ImageFilter.GaussianBlur(38))
            VINYL_X, VINYL_Y = 480, 500
            TEXT_X, TEXT_Y = 1250, 500
        else:
            TEXT_X = WIDTH // 2

        print(f"Rendering {TOTAL_FRAMES} frames ({aspect_ratio})...")

        for f_idx in range(TOTAL_FRAMES):
            t = f_idx / fps
            frame = paper_base.copy()
            draw = ImageDraw.Draw(frame)

            # Dust
            for i in range(num_particles):
                px = (dust_x[i] + dust_vx[i] * f_idx) % WIDTH
                py = (dust_y[i] + dust_vy[i] * f_idx) % HEIGHT
                draw.ellipse([px, py, px + dust_size[i], py + dust_size[i]], fill=(215, 208, 198))

            # Header
            header_y = 100 if is_16x9 else 440
            draw.text((WIDTH // 2, header_y), f"{title.upper()}   •   {artist.upper()}", font=font_meta, fill=self.COLOR_MUTED, anchor="mm")
            draw.line([(WIDTH // 2 - 220, header_y + 30), (WIDTH // 2 + 220, header_y + 30)], fill=self.COLOR_LINE, width=2)

            # 16:9 Vinyl Record Spin & Glow
            if is_16x9:
                pulse = 1.0 + 0.04 * np.sin(t * 3.5)
                pw, ph = int(glow_size * pulse), int(glow_size * pulse)
                cur_glow = glow_img.resize((pw, ph), resample=Image.BILINEAR)
                frame.paste(cur_glow, (VINYL_X - pw // 2, VINYL_Y - ph // 2), cur_glow)

                rot_angle = (t * 72.0) % 360.0
                rot_vinyl = master_vinyl.rotate(-rot_angle, resample=Image.BICUBIC)
                frame.paste(rot_vinyl, (VINYL_X - rot_vinyl.width // 2, VINYL_Y - rot_vinyl.height // 2), rot_vinyl)
                draw.text((VINYL_X, VINYL_Y + 310), "NOW PLAYING  •  SPOTIFY AUDIO", font=font_badge, fill=self.COLOR_MUTED, anchor="mm")

            # Kinetic Scaled Text Helper
            def draw_scaled_text(target_img, text, font, cx, cy, scale, color):
                if not text:
                    return
                if abs(scale - 1.0) < 0.01:
                    d = ImageDraw.Draw(target_img)
                    d.text((cx, cy), text, font=font, fill=color, anchor="mm")
                else:
                    bbox = font.getbbox(text)
                    tw, th = bbox[2] - bbox[0] + 60, bbox[3] - bbox[1] + 60
                    layer = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
                    ldraw = ImageDraw.Draw(layer)
                    ldraw.text((tw // 2, th // 2), text, font=font, fill=(*color, 255), anchor="mm")
                    nw, nh = int(tw * scale), int(th * scale)
                    resz = layer.resize((nw, nh), resample=Image.BICUBIC)
                    target_img.paste(resz, (cx - nw // 2, cy - nh // 2), resz)

            # Render text lines
            y_offsets_16x9 = [390, 520, 640]
            y_offsets_9x16 = [850, 1000, 1140]
            y_offsets = y_offsets_16x9 if is_16x9 else y_offsets_9x16

            for idx, item in enumerate(lines_config):
                if t >= item["time"]:
                    pop_age = t - item["time"]
                    scale = 1.0
                    if pop_age < 0.2:
                        scale = 1.0 + item.get("scale_pop", 0.12) * (1.0 - pop_age / 0.2)
                    cur_font = font_large if idx < 2 else font_med
                    draw_scaled_text(frame, item["text"], cur_font, TEXT_X, y_offsets[idx], scale, self.COLOR_RED)

            # Spotify Timeline Scrubber
            bar_y = 960 if is_16x9 else 1500
            bar_left = 320 if is_16x9 else 180
            bar_right = WIDTH - (320 if is_16x9 else 180)
            bar_width = bar_right - bar_left

            progress = min(1.0, max(0.0, t / duration))
            active_x = bar_left + int(bar_width * progress)

            draw.line([(bar_left, bar_y), (bar_right, bar_y)], fill=self.COLOR_LINE, width=4)
            draw.line([(bar_left, bar_y), (active_x, bar_y)], fill=self.COLOR_BAR, width=4)
            draw.ellipse([active_x - 7, bar_y - 7, active_x + 7, bar_y + 7], fill=self.COLOR_BAR)

            # Scrubber timestamps
            try:
                base_mins, base_secs = map(int, start_offset_label.split(":"))
                cur_total = base_mins * 60 + base_secs + int(t)
                cur_str = f"{cur_total // 60}:{cur_total % 60:02d}"
            except Exception:
                cur_str = f"0:{int(t):02d}"

            draw.text((bar_left, bar_y + 20), cur_str, font=font_time, fill=self.COLOR_MUTED, anchor="lt")
            draw.text((bar_right, bar_y + 20), "3:38", font=font_time, fill=self.COLOR_MUTED, anchor="rt")

            frame.save(os.path.join(tmp_frames, f"frame_{f_idx:04d}.jpg"), quality=90)

        # FFmpeg Mux
        ffmpeg_cmd = [
            "ffmpeg", "-y",
            "-r", str(fps),
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
        print(f"SUCCESS: Rendered {aspect_ratio} master to {output_mp4}")
        return output_mp4


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Aesthetic Lyric Video Generator")
    parser.add_argument("--ratio", default="16:9", choices=["16:9", "9:16"], help="Aspect ratio")
    parser.add_argument("--title", default="Husn", help="Song title")
    parser.add_argument("--artist", default="Anuv Jain", help="Artist name")
    args = parser.parse_args()

    engine = AestheticLyricEngine()
    
    # Audio setup
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    raw_audio = os.path.join(base_dir, "indian-lofi-converter", "raw_stems", "husn_raw.mp3")
    slice_wav = os.path.join(base_dir, "output", "temp_vocal_slice.wav")
    
    engine.extract_vocal_slice(raw_audio, start_sec=76.5, duration_sec=5.0, output_wav_path=slice_wav)
    
    lines = [
        {"text": "देखो देखो", "time": 0.75, "scale_pop": 0.12},
        {"text": "ये ज़माने से थक कर", "time": 2.30, "scale_pop": 0.12},
        {"text": "आते हो क्यों...", "time": 3.40, "scale_pop": 0.15}
    ]
    
    out_file = engine.render(
        audio_path=slice_wav,
        title=args.title,
        artist=args.artist,
        lines_config=lines,
        aspect_ratio=args.ratio,
        duration=5.0,
        start_offset_label="1:16"
    )
    
    if os.path.exists(slice_wav):
        os.remove(slice_wav)
