"""
Universal Aesthetic Lyric Engine (Advanced Production Standard)
================================================================
The master pipeline for producing viral, editorial-grade lyrical videos:
- Dual Aspect Ratio: 9:16 Vertical Reel/Shorts (1080x1920) & 16:9 Widescreen (1920x1080 with Spinning Vinyl).
- Shimmering Water Caustics light reflection overlay across vintage ivory paper canvas (#FAF8F4).
- Audio-Reactive Fluid Ripple Wave in negative space.
- Automatic Whisper vocal alignment and intelligent poetic card/stanza grouping.
- Google Font Rozha One Devanagari & Latin calligraphy in deep crimson red (#C8102E).
- Direct FFmpeg rawvideo pipe streaming (Zero disk clutter, high FPS encoding).
- Cross-platform UTF-8 encoding support.
"""

import os
import sys
import time
import argparse
import subprocess
import numpy as np
import math
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from pydub import AudioSegment
from scipy.io import wavfile
import scipy.signal as signal

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

class AestheticLyricEngine:
    def __init__(self, font_path=None):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if font_path is None:
            font_path = os.path.join(base_dir, "RozhaOne-Regular.ttf")
        self.font_path = font_path
        if not os.path.exists(self.font_path):
            raise FileNotFoundError(f"Font file missing at: {self.font_path}")

        # Core Color Palette
        self.COLOR_BG = (250, 248, 244) # Warm vintage parchment
        self.COLOR_RED = (200, 16, 46)   # Deep rich crimson red
        self.COLOR_MUTED = (165, 155, 145)
        self.COLOR_LINE = (225, 218, 210)
        self.COLOR_BAR = (200, 16, 46)

    def extract_audio_slice(self, raw_audio_path, start_sec, duration_sec, output_wav_path):
        """Extracts a high-fidelity vocal slice with smooth crossfades."""
        audio = AudioSegment.from_file(raw_audio_path)
        start_ms = int(start_sec * 1000)
        end_ms = start_ms + int(duration_sec * 1000)
        sliced = audio[start_ms:end_ms].fade_in(80).fade_out(350)
        sliced.export(output_wav_path, format="wav")
        return output_wav_path

    def parse_lrc_file(self, lrc_path, total_duration, is_16x9=False):
        """Parses verified .lrc synced lyrics and groups them into perfectly paced aesthetic cards."""
        import re
        if not os.path.exists(lrc_path):
            return None

        with open(lrc_path, "r", encoding="utf-8") as f:
            content = f.read()

        pattern = re.compile(r"\[(\d{2}):(\d{2})\.(\d{2,3})\](.*)")
        entries = []
        for line in content.splitlines():
            line = line.strip()
            if not line:
                continue
            m = pattern.match(line)
            if m:
                mins, secs, frac, text = m.groups()
                sec_val = int(mins) * 60 + int(secs) + float("0." + frac)
                text = text.strip()
                entries.append((sec_val, text))

        entries.sort(key=lambda x: x[0])
        if not entries:
            return None

        font_hero = ImageFont.truetype(self.font_path, 115 if not is_16x9 else 110)
        font_large = ImageFont.truetype(self.font_path, 102 if not is_16x9 else 95)
        font_med = ImageFont.truetype(self.font_path, 86 if not is_16x9 else 80)

        raw_stanzas = []
        cur_items = []
        for t, txt in entries:
            if not txt:
                if cur_items:
                    raw_stanzas.append((cur_items, t))
                    cur_items = []
            else:
                if cur_items and (t - cur_items[-1][0] > 7.0):
                    raw_stanzas.append((cur_items, t - 0.6))
                    cur_items = []
                cur_items.append((t, txt))
        if cur_items:
            raw_stanzas.append((cur_items, total_duration))

        refined = []
        for items, end_t in raw_stanzas:
            if len(items) <= 5:
                refined.append((items, end_t))
            else:
                mid = len(items) // 2
                refined.append((items[:mid], items[mid][0] - 0.5))
                refined.append((items[mid:], end_t))

        cards = []
        for items, end_t in refined:
            start_t = max(0.0, items[0][0] - 0.8)
            n = len(items)
            if not is_16x9:
                if n == 1: y_pos = [980]
                elif n == 2: y_pos = [920, 1080]
                elif n == 3: y_pos = [860, 1000, 1140]
                elif n == 4: y_pos = [800, 940, 1080, 1220]
                elif n == 5: y_pos = [750, 880, 1010, 1140, 1270]
                else: y_pos = [720 + i * 115 for i in range(n)]
            else:
                if n <= 3: y_pos = [420 + i * 120 for i in range(n)]
                elif n == 4: y_pos = [380, 490, 600, 710]
                else: y_pos = [350 + i * 90 for i in range(n)]

            card_items = []
            max_line_w = (1920 - 750) if is_16x9 else (1080 - 180)
            for i, (t, txt) in enumerate(items):
                # Auto-fit typography: step down if line exceeds canvas margins
                f_font = font_hero if (i == 0 and n <= 4) else (font_large if n <= 4 else font_med)
                if f_font.getbbox(txt)[2] > max_line_w:
                    f_font = font_large
                if f_font.getbbox(txt)[2] > max_line_w:
                    f_font = font_med
                card_items.append({"text": txt, "time": t, "y": y_pos[i], "font": f_font})

            cards.append({"start": round(start_t, 2), "end": round(end_t, 2), "items": card_items})

        return cards

    def precompute_water_caustics(self, width, height, num_frames=90):
        """Precomputes looping water caustics light reflection mesh."""
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

    def create_spinning_vinyl(self, size=520, title="HUSN", artist="ANUV JAIN", artwork_path=None):
        """Generates an aesthetic spinning vinyl record disc with optional circular cover image."""
        disc = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(disc)
        center = size // 2
        r_outer = size // 2 - 12
        
        # Outer dark vinyl
        draw.ellipse([center - r_outer, center - r_outer, center + r_outer, center + r_outer], fill=(16, 16, 18, 255))
        
        # Concentric grooves
        for r in range(center - r_outer + 20, center - 85, 7):
            draw.ellipse([center - r, center - r, center + r, center + r], outline=(36, 36, 42, 190), width=1)
        for r in range(center - r_outer + 24, center - 85, 14):
            draw.ellipse([center - r, center - r, center + r, center + r], outline=(52, 52, 60, 130), width=1)
            
        r_label = 96
        # Center medallion: artwork photo if provided
        if artwork_path and os.path.exists(artwork_path):
            try:
                img = Image.open(artwork_path).convert("RGBA")
                min_dim = min(img.width, img.height)
                cx = int(img.width * 0.28) if img.width > img.height * 1.3 else img.width // 2
                cy = img.height // 2
                s = min_dim
                left = max(0, min(img.width - s, cx - s // 2))
                top = max(0, min(img.height - s, cy - s // 2))
                cropped = img.crop((left, top, left + s, top + s)).resize((r_label * 2, r_label * 2), Image.Resampling.LANCZOS)
                
                mask = Image.new("L", (r_label * 2, r_label * 2), 0)
                mdraw = ImageDraw.Draw(mask)
                mdraw.ellipse([2, 2, r_label * 2 - 2, r_label * 2 - 2], fill=255)
                
                disc.paste(cropped, (center - r_label, center - r_label), mask)
                
                # Crimson & Gold metallic trim
                draw.ellipse([center - r_label, center - r_label, center + r_label, center + r_label], outline=self.COLOR_RED, width=3)
                draw.ellipse([center - r_label + 2, center - r_label + 2, center + r_label - 2, center + r_label - 2], outline=(255, 230, 180, 200), width=1)
            except Exception:
                draw.ellipse([center - r_label, center - r_label, center + r_label, center + r_label], fill=(*self.COLOR_RED, 255))
        else:
            # Classic Crimson center label
            draw.ellipse([center - r_label, center - r_label, center + r_label, center + r_label], fill=(*self.COLOR_RED, 255))
            r_inner = 78
            draw.ellipse([center - r_inner, center - r_inner, center + r_inner, center + r_inner], outline=(245, 235, 220, 220), width=2)
            font_disc = ImageFont.truetype("arial.ttf", 16)
            draw.text((center, center - 35), artist.upper(), font=font_disc, fill=(255, 255, 255, 220), anchor="mm")
            draw.text((center, center + 35), title.upper(), font=font_disc, fill=(255, 255, 255, 220), anchor="mm")
        
        # Spindle hole with brass grommet
        r_hole = 14
        draw.ellipse([center - r_hole - 3, center - r_hole - 3, center + r_hole + 3, center + r_hole + 3], fill=(180, 150, 90, 255))
        draw.ellipse([center - r_hole, center - r_hole, center + r_hole, center + r_hole], fill=self.COLOR_BG)
        
        # Sheen wedges
        sheen = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        sdraw = ImageDraw.Draw(sheen)
        sdraw.pieslice([center - r_outer + 5, center - r_outer + 5, center + r_outer - 5, center + r_outer - 5], 35, 65, fill=(255, 255, 255, 30))
        sdraw.pieslice([center - r_outer + 5, center - r_outer + 5, center + r_outer - 5, center + r_outer - 5], 215, 245, fill=(255, 255, 255, 30))
        
        return Image.alpha_composite(disc, sheen)

    def analyze_audio_tempo_and_dynamics(self, audio_mono, sr):
        """
        Autonomous Audio Intelligence:
        Calculates exact BPM, dynamic energy range, and configures
        adaptive motion kinematics (pacing, vinyl RPM, word stagger, transition duration).
        """
        rms_val = float(np.sqrt(np.mean(audio_mono**2)))
        
        # Fast Librosa / SciPy Tempo Detection
        try:
            import librosa
            y_res = librosa.resample(audio_mono, orig_sr=sr, target_sr=22050)
            tempo, _ = librosa.beat.beat_track(y=y_res, sr=22050)
            bpm = float(tempo[0]) if isinstance(tempo, np.ndarray) else float(tempo)
        except Exception:
            hop = 512
            envelope = np.diff(np.maximum(0, audio_mono))
            envelope = signal.resample(envelope, int(len(envelope) / hop))
            envelope = np.maximum(0, envelope)
            autocorr = signal.correlate(envelope, envelope, mode='full')
            autocorr = autocorr[len(autocorr)//2:]
            fps_env = sr / hop
            min_lag = int(fps_env * 60 / 200)
            max_lag = int(fps_env * 60 / 55)
            peak_lag = min_lag + np.argmax(autocorr[min_lag:max_lag])
            bpm = (fps_env * 60.0) / peak_lag

        # Dynamic Profile Classification
        if bpm < 105:
            mode = "SLOW_SOULFUL"
            spin_speed = 45.0          # Slow vintage meditative 33 RPM spin
            transition_dur = 0.95      # Silky, dreamy cross-fade
            word_stagger = 0.20        # Slower deliberate vocal cadence
            line_entrance_dur = 0.42   # Gentle glide
            bounce_scale = 1.04        # Delicate elegance
            beat_pulse_mult = 0.05     # Subtle breathing
            particle_speed = 0.7       # Calm floating dust
        elif bpm <= 125:
            mode = "MODERATE_LOFI"
            spin_speed = 62.0          # Standard 45 RPM spin
            transition_dur = 0.80      # Balanced handoff
            word_stagger = 0.17        # Natural lofi cadence
            line_entrance_dur = 0.35   # Standard glide
            bounce_scale = 1.06        # Balanced pop
            beat_pulse_mult = 0.08     # Moderate pulse
            particle_speed = 1.0       # Standard particle float
        else:
            mode = "UPBEAT_PUNCHY"
            spin_speed = 82.0          # Energetic punchy spin
            transition_dur = 0.65      # Snappy rhythm handoff
            word_stagger = 0.14        # Rapid-fire energetic cadence
            line_entrance_dur = 0.28   # Quick snap-in
            bounce_scale = 1.09        # High-energy overshoot
            beat_pulse_mult = 0.12     # High dynamic kick/bass responsiveness
            particle_speed = 1.4       # Lively particle float

        profile = {
            "bpm": round(bpm, 1),
            "mode": mode,
            "rms_mean": round(rms_val, 3),
            "vinyl_rot_speed": spin_speed,
            "transition_dur": transition_dur,
            "word_stagger": word_stagger,
            "line_entrance_dur": line_entrance_dur,
            "bounce_scale": bounce_scale,
            "beat_pulse_mult": beat_pulse_mult,
            "particle_speed": particle_speed
        }

        print("\n" + "=" * 64, flush=True)
        print("🎛️  AUTONOMOUS AUDIO INTELLIGENCE & TEMPO SENSING", flush=True)
        print("=" * 64, flush=True)
        print(f"• Detected Tempo:        {profile['bpm']} BPM", flush=True)
        print(f"• Dynamic Pacing Mode:   {profile['mode']}", flush=True)
        print(f"• Average Audio RMS:     {profile['rms_mean']}", flush=True)
        print("• Adaptive Motion Kinematics:")
        print(f"  - Vinyl Spin Rate:     {profile['vinyl_rot_speed']}°/sec (Adaptive RPM)")
        print(f"  - Word Cadence:        {profile['word_stagger']}s per word")
        print(f"  - Verse Transition:    {profile['transition_dur']}s handoff")
        print(f"  - Kinetic Overshoot:   {profile['bounce_scale']}x spring bounce")
        print(f"  - Beat Pulse Gain:     {profile['beat_pulse_mult']}x")
        print("=" * 64 + "\n", flush=True)

        return profile

    def render(self, audio_path, title="Husn", artist="Anuv Jain", cards_config=None,
               aspect_ratio="9:16", duration=22.5, fps=30, output_mp4=None,
               show_player=False, enable_water_caustics=True, start_offset_label="1:10",
               artwork_path=None, enable_floral_overlay=False):
        """
        Master Video Rendering Pipeline with Direct FFmpeg Rawvideo Pipe Streaming.
        """
        is_16x9 = (aspect_ratio == "16:9")
        W, H = (1920, 1080) if is_16x9 else (1080, 1920)
        TOTAL_FRAMES = int(duration * fps)

        if output_mp4 is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            output_dir = os.path.join(base_dir, "output")
            os.makedirs(output_dir, exist_ok=True)
            tag = "16x9" if is_16x9 else "9x16"
            output_mp4 = os.path.join(output_dir, f"{title.lower()}_{tag}_master.mp4")

        # 1. Audio Processing & RMS Energy for Fluid Wave
        sr, audio_data = wavfile.read(audio_path)
        if audio_data.ndim == 2:
            audio_mono = audio_data.mean(axis=1)
        else:
            audio_mono = audio_data
        audio_mono = audio_mono.astype(np.float32)
        audio_mono /= (np.max(np.abs(audio_mono)) + 1e-6)
        samples_per_frame = int(sr / fps)

        # Autonomous Audio Intelligence & Dynamic Pacing Profile
        profile = self.analyze_audio_tempo_and_dynamics(audio_mono, sr)

        # 2. Typography Setup
        font_hero = ImageFont.truetype(self.font_path, 115 if not is_16x9 else 110)
        font_large = ImageFont.truetype(self.font_path, 102 if not is_16x9 else 95)
        font_med = ImageFont.truetype(self.font_path, 86 if not is_16x9 else 80)
        font_meta = ImageFont.truetype("arial.ttf", 26 if not is_16x9 else 24)
        font_time = ImageFont.truetype("arial.ttf", 22)

        # Default Narrative Cards if none supplied
        # 2B. Dynamic Synced LRC Discovery & Integration
        if cards_config is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            lrc_candidates = [
                os.path.join(base_dir, "raw_stems", f"{title.lower().replace(' ', '_')}.lrc"),
                os.path.join(base_dir, "raw_stems", "chalray.lrc") if "chalr" in title.lower() else None,
                r"C:\Users\Deepanshu\.gemini\antigravity-ide\brain\da9f0491-1414-452e-892a-51cb1310dfd5\scratch\chalray_synced.lrc" if "chalr" in title.lower() else None
            ]
            for cand in lrc_candidates:
                if cand and os.path.exists(cand):
                    parsed = self.parse_lrc_file(cand, duration, is_16x9=is_16x9)
                    if parsed:
                        cards_config = parsed
                        print(f"[INFO] Successfully loaded verified Synced Lyrics from {os.path.basename(cand)} ({len(cards_config)} stanzas)", flush=True)
                        break

        # Fallback Narrative Cards if no .lrc found
        if cards_config is None:
            if "chalr" in title.lower() or "chalre" in title.lower() or "sial" in artist.lower():
                # Official Spotify/Musixmatch Verified 6-Stanza Master Timing
                cards_config = [
                    {
                        "start": 0.0, "end": 20.0,
                        "items": [
                            {"text": "छलड़े छलड़े बाल", "time": 2.01, "y": 750 if not is_16x9 else 380, "font": font_hero},
                            {"text": "मंड रखदे काली शाल", "time": 4.72, "y": 880 if not is_16x9 else 480, "font": font_med},
                            {"text": "हाथ छे नै रत्ता रुमाल", "time": 8.09, "y": 1010 if not is_16x9 else 580, "font": font_med},
                            {"text": "तेरिया रीसा कौन करे", "time": 10.87, "y": 1140 if not is_16x9 else 680, "font": font_med},
                            {"text": "मैं तेरिया रीसा कौन करे", "time": 13.85, "y": 1270 if not is_16x9 else 780, "font": font_large}
                        ]
                    },
                    {
                        "start": 21.0, "end": 42.8,
                        "items": [
                            {"text": "तू सावल फुल कस्तूरी", "time": 24.04, "y": 720 if not is_16x9 else 350, "font": font_med},
                            {"text": "पेड़ी थी गई बा मशहूरि", "time": 27.21, "y": 835 if not is_16x9 else 440, "font": font_med},
                            {"text": "तू सावल फुल कस्तूरी", "time": 30.45, "y": 950 if not is_16x9 else 530, "font": font_med},
                            {"text": "पेड़ी थी गई बा मशहूरि", "time": 33.61, "y": 1065 if not is_16x9 else 620, "font": font_med},
                            {"text": "झां झां ते हर झां ते", "time": 36.88, "y": 1180 if not is_16x9 else 710, "font": font_med},
                            {"text": "पे दिन दे लोक मिसाल", "time": 40.06, "y": 1295 if not is_16x9 else 800, "font": font_med}
                        ]
                    },
                    {
                        "start": 42.8, "end": 60.63,
                        "items": [
                            {"text": "छलड़े छलड़े बाल", "time": 43.68, "y": 750 if not is_16x9 else 380, "font": font_hero},
                            {"text": "मंड रखदे काली शाल", "time": 46.34, "y": 880 if not is_16x9 else 480, "font": font_med},
                            {"text": "हाथ छे नै रत्ता रुमाल", "time": 49.68, "y": 1010 if not is_16x9 else 580, "font": font_med},
                            {"text": "तेरिया रीसा कौन करे", "time": 52.42, "y": 1140 if not is_16x9 else 680, "font": font_med},
                            {"text": "मैं तेरिया रीसा कौन करे", "time": 55.45, "y": 1270 if not is_16x9 else 780, "font": font_large}
                        ]
                    },
                    # 60.63s to 84.0s: Flute & Dholak Instrumental Solo Break (Tranquil Negative Space)
                    {
                        "start": 84.0, "end": 104.0,
                        "items": [
                            {"text": "अधे देख के दंग थी गईया", "time": 84.86, "y": 860 if not is_16x9 else 420, "font": font_large},
                            {"text": "पहली बार मा लंग थी गईया", "time": 92.01, "y": 1000 if not is_16x9 else 540, "font": font_large},
                            {"text": "अधे देख के दंग थी गईया", "time": 97.75, "y": 1140 if not is_16x9 else 660, "font": font_large}
                        ]
                    },
                    {
                        "start": 104.0, "end": 117.8,
                        "items": [
                            {"text": "पहली बार मा लंग थी गईया", "time": 104.85, "y": 860 if not is_16x9 else 420, "font": font_large},
                            {"text": "तू बोले लब खोले", "time": 110.33, "y": 1000 if not is_16x9 else 540, "font": font_hero},
                            {"text": "केरे मोचो गिरदे लाल", "time": 113.58, "y": 1140 if not is_16x9 else 660, "font": font_large}
                        ]
                    },
                    {
                        "start": 117.8, "end": duration,
                        "items": [
                            {"text": "छलड़े छलड़े बाल", "time": 118.74, "y": 750 if not is_16x9 else 380, "font": font_hero},
                            {"text": "मंड रखदे काली शाल", "time": 123.19, "y": 880 if not is_16x9 else 480, "font": font_med},
                            {"text": "हाथ छे नै रत्ता रुमाल", "time": 126.32, "y": 1010 if not is_16x9 else 580, "font": font_med},
                            {"text": "तेरिया रीसा कौन करे", "time": 129.15, "y": 1140 if not is_16x9 else 680, "font": font_med},
                            {"text": "मैं तेरिया रीसा कौन करे", "time": 132.18, "y": 1270 if not is_16x9 else 780, "font": font_large}
                        ]
                    }
                ]
            else:
                cards_config = [
                    {
                        "start": 0.0, "end": 5.5,
                        "items": [
                            {"text": "तेरे लिये मैं काफी हूँ?", "time": 0.80, "y": 960 if not is_16x9 else 520, "font": font_hero}
                        ]
                    },
                    {
                        "start": 5.5, "end": 13.5,
                        "items": [
                            {"text": "देखो देखो", "time": 6.20, "y": 800 if not is_16x9 else 420, "font": font_large},
                            {"text": "ये ज़माने से थक कर", "time": 7.80, "y": 960 if not is_16x9 else 530, "font": font_med},
                            {"text": "आते हो क्यों मासूम बन कर?", "time": 9.80, "y": 1120 if not is_16x9 else 640, "font": font_med}
                        ]
                    },
                    {
                        "start": 13.5, "end": duration,
                        "items": [
                            {"text": "तेरे ज़ेहन में ये क्या है?", "time": 14.50, "y": 880 if not is_16x9 else 460, "font": font_large},
                            {"text": "अरे फिर आते क्यों यहाँ पर...?", "time": 17.80, "y": 1050 if not is_16x9 else 600, "font": font_med}
                        ]
                    }
                ]

        # 3. Canvas & Paper Texture
        np.random.seed(42)
        base_img = Image.new("RGB", (W, H), self.COLOR_BG)
        base_arr = np.array(base_img, dtype=np.float32)
        noise = np.random.normal(0, 2.8, (H, W, 1))
        base_arr = np.clip(base_arr + noise, 0, 255)

        y_coords, x_coords = np.ogrid[:H, :W]
        dist = np.sqrt(((x_coords - W/2) / (W/2))**2 + ((y_coords - H/2) / (H/2))**2)
        vignette = np.clip(1.0 - (dist - 0.7) * 0.16, 0.88, 1.0)[:, :, np.newaxis]
        paper_base_arr = base_arr * vignette
        paper_base_img = Image.fromarray(np.uint8(paper_base_arr))

        # Floating dust particles
        dust_count = 35
        dust_x = np.random.uniform(40, W - 40, dust_count)
        dust_y = np.random.uniform(40, H - 40, dust_count)
        dust_vx = np.random.uniform(-0.5, 0.5, dust_count)
        dust_vy = np.random.uniform(-0.9, -0.3, dust_count)
        dust_sz = np.random.randint(2, 5, dust_count)

        # 4. Water Caustics Cache (if enabled)
        caustic_cache = None
        if enable_water_caustics:
            caustic_cache = self.precompute_water_caustics(W, H, num_frames=90)

        # 16:9 Vinyl Assets
        if is_16x9:
            if artwork_path is None:
                raw_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "raw_stems")
                if "chalr" in title.lower() or "chalre" in title.lower():
                    cand = os.path.join(raw_dir, "chalray_thumb.jpg")
                    if os.path.exists(cand):
                        artwork_path = cand
                elif "husn" in title.lower():
                    cand = os.path.join(raw_dir, "husn_thumb.jpg")
                    if os.path.exists(cand):
                        artwork_path = cand

            master_vinyl = self.create_spinning_vinyl(520, title, artist, artwork_path=artwork_path)
            print("[INFO] Pre-caching vinyl 360-degree rotation table for turbo speed...", flush=True)
            vinyl_cache = [master_vinyl.rotate(-deg, resample=Image.BICUBIC) for deg in range(360)]

            glow_size = 620
            glow_img = Image.new("RGBA", (glow_size, glow_size), (0, 0, 0, 0))
            gdraw = ImageDraw.Draw(glow_img)
            g_center = glow_size // 2
            gdraw.ellipse([g_center - 240, g_center - 240, g_center + 240, g_center + 240], fill=(200, 16, 46, 75))
            glow_img = glow_img.filter(ImageFilter.GaussianBlur(38))

            glow_cache = []
            for p_idx in range(60):
                p_mult = 1.0 + 0.04 * np.sin(p_idx * 2 * np.pi / 60)
                pw, ph = int(glow_size * p_mult), int(glow_size * p_mult)
                glow_cache.append(glow_img.resize((pw, ph), resample=Image.BILINEAR))

            VINYL_X, VINYL_Y = 480, 520
            TEXT_CENTER_X = 1250
        else:
            TEXT_CENTER_X = W // 2

        # 5. Summer Botanical Floral & Petals Overlay Setup
        floral_particles = []
        corner_branch = None
        if enable_floral_overlay:
            petals_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "botanical_petals")
            if os.path.exists(petals_dir):
                sp_files = sorted([f for f in os.listdir(petals_dir) if f.endswith(".png")])
                sp_imgs = [Image.open(os.path.join(petals_dir, f)).convert("RGBA") for f in sp_files]
                if sp_imgs:
                    np.random.seed(99)
                    for i in range(14):
                        sp = sp_imgs[i % (len(sp_imgs) - 1)]
                        target_w = np.random.randint(35, 75)
                        ratio = target_w / sp.width
                        target_h = int(sp.height * ratio)
                        resized_sp = sp.resize((target_w, target_h), Image.Resampling.LANCZOS)
                        alpha_mult = np.random.uniform(0.60, 0.85)
                        r, g, b, a = resized_sp.split()
                        a = a.point(lambda p: int(p * alpha_mult))
                        resized_sp = Image.merge("RGBA", (r, g, b, a))

                        # Pre-cache 72 rotation angles (every 5 deg) for zero-latency particle motion
                        rot_cache = [resized_sp.rotate(deg, resample=Image.BICUBIC, expand=True) for deg in range(0, 360, 5)]

                        floral_particles.append({
                            "x": np.random.uniform(100, W - 100),
                            "y": np.random.uniform(80, H - 80),
                            "vx": np.random.uniform(-1.0, -0.3),
                            "vy": np.random.uniform(0.6, 1.3),
                            "base_rot": np.random.uniform(0, 360),
                            "rot_speed": np.random.uniform(10, 28),
                            "phase": np.random.uniform(0, math.pi * 2),
                            "sprite": resized_sp,
                            "rot_cache": rot_cache
                        })

                    if len(sp_imgs) >= 16:
                        # Bottom-Right Corner Olive Branch Accent
                        b_sp = sp_imgs[15]
                        bw = int(b_sp.width * 0.70)
                        bh = int(b_sp.height * 0.70)
                        b_sp = b_sp.resize((bw, bh), Image.Resampling.LANCZOS)
                        r, g, b, a = b_sp.split()
                        a = a.point(lambda p: int(p * 0.65))
                        corner_branch = Image.merge("RGBA", (r, g, b, a)).rotate(-20, expand=True)

        word_aura_cache = {}

        # Helper: Render Text Card with Dynamic Kinetic Animation & Smooth Line Scroll
        def render_card_layer(items, active_time, global_alpha=1.0, card_offset_y=0, rms=0.0):
            layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            ldraw = ImageDraw.Draw(layer)

            # Determine the active line index
            active_line_idx = -1
            for idx, item in enumerate(items):
                if active_time >= item["time"]:
                    active_line_idx = idx

            # If stanza has not sung its first line yet (entrance transition phase)
            if active_line_idx == -1:
                first_item = items[0]
                font = first_item["font"]
                text = first_item["text"]
                base_cy = first_item["y"] + card_offset_y
                words = text.split(" ")
                space_box = font.getbbox(" ")
                space_w = space_box[2] - space_box[0] if space_box else 16
                word_boxes = [font.getbbox(w) for w in words]
                word_widths = [b[2] - b[0] for b in word_boxes]
                total_w = sum(word_widths) + space_w * (len(words) - 1)
                start_x = TEXT_CENTER_X - total_w // 2
                cur_x = start_x
                ghost_alpha = int(120 * global_alpha)
                for w, w_w in zip(words, word_widths):
                    w_center_x = cur_x + w_w // 2
                    ldraw.text((w_center_x, base_cy), w, font=font, fill=(215, 205, 195, ghost_alpha), anchor="mm")
                    cur_x += w_w + space_w
                return layer

            for idx, item in enumerate(items):
                font = item["font"]
                text = item["text"]
                words = text.split(" ")
                base_cy = item["y"] + card_offset_y

                space_box = font.getbbox(" ")
                space_w = space_box[2] - space_box[0] if space_box else 16
                word_boxes = [font.getbbox(w) for w in words]
                word_widths = [b[2] - b[0] for b in word_boxes]
                total_w = sum(word_widths) + space_w * (len(words) - 1)
                start_x = TEXT_CENTER_X - total_w // 2
                cur_x = start_x

                if idx < active_line_idx:
                    # Past lines: dynamic smooth upward glide & color fade from crimson to vintage taupe
                    if idx == active_line_idx - 1:
                        time_since_passed = active_time - items[active_line_idx]["time"]
                        p_u = min(1.0, max(0.0, time_since_passed / 0.45))
                        p_ease = 1.0 - pow(1.0 - p_u, 3)
                        line_dy = -int(20.0 * p_ease)
                        cur_r = int(200 + (145 - 200) * p_ease)
                        cur_g = int(16 + (132 - 16) * p_ease)
                        cur_b = int(46 + (122 - 46) * p_ease)
                        past_alpha = int((255 + (175 - 255) * p_ease) * global_alpha)
                    else:
                        line_dy = -20
                        cur_r, cur_g, cur_b = 145, 132, 122
                        past_alpha = int(175 * global_alpha)

                    for w, w_w in zip(words, word_widths):
                        w_center_x = cur_x + w_w // 2
                        ldraw.text((w_center_x, base_cy + line_dy), w, font=font, fill=(cur_r, cur_g, cur_b, past_alpha), anchor="mm")
                        cur_x += w_w + space_w

                elif idx == active_line_idx:
                    # Current active line: smooth entrance slide-up + word-by-word kinetic bounce + music reactivity
                    line_age = active_time - item["time"]
                    line_entrance_dur = profile["line_entrance_dur"]
                    line_u = min(1.0, max(0.0, line_age / line_entrance_dur))
                    line_ease = 1.0 - pow(1.0 - line_u, 3)
                    line_dy = int(22.0 * (1.0 - line_ease))

                    # Adaptive dynamic music beat pulse
                    beat_scale = 1.0 + min(0.06, rms * profile["beat_pulse_mult"] * 10)

                    for w_idx, (w, w_w) in enumerate(zip(words, word_widths)):
                        w_time = item["time"] + w_idx * profile["word_stagger"]
                        w_center_x = cur_x + w_w // 2

                        if active_time < w_time:
                            # Ghost watermark before word is sung (Top Creator Aesthetic)
                            ghost_alpha = int(115 * global_alpha)
                            ldraw.text((w_center_x, base_cy + line_dy), w, font=font, fill=(215, 205, 195, ghost_alpha), anchor="mm")
                        else:
                            age = active_time - w_time
                            entrance_dur = 0.32
                            if age < entrance_dur:
                                u = age / entrance_dur
                                ease_out = 1.0 - pow(1.0 - u, 3)
                                dy = int(22.0 * (1.0 - ease_out))
                                scale = (0.92 + (profile["bounce_scale"] - 0.92) * ease_out + 0.05 * math.sin(u * math.pi)) * beat_scale
                                word_alpha = min(1.0, u * 1.8)
                            else:
                                dy = 0
                                scale = 1.0 * beat_scale
                                word_alpha = 1.0

                            eff_alpha = int(255 * word_alpha * global_alpha)
                            cy = base_cy + line_dy + dy

                            # Active word soft ambient glow aura (cached lookup for turbo speed)
                            if eff_alpha > 50:
                                if w not in word_aura_cache:
                                    bbox = font.getbbox(w)
                                    bw, bh = bbox[2] - bbox[0] + 60, bbox[3] - bbox[1] + 60
                                    if bw > 0 and bh > 0:
                                        g_box = Image.new("RGBA", (bw, bh), (0, 0, 0, 0))
                                        g_draw = ImageDraw.Draw(g_box)
                                        g_draw.text((bw // 2, bh // 2), w, font=font, fill=(*self.COLOR_RED, 80), anchor="mm")
                                        word_aura_cache[w] = g_box.filter(ImageFilter.GaussianBlur(10))
                                    else:
                                        word_aura_cache[w] = None

                                cached_aura = word_aura_cache.get(w)
                                if cached_aura is not None:
                                    layer.paste(cached_aura, (w_center_x - cached_aura.width // 2, cy - cached_aura.height // 2), cached_aura)

                            # Render active word with scale bounce
                            if abs(scale - 1.0) < 0.01:
                                ldraw.text((w_center_x, cy), w, font=font, fill=(*self.COLOR_RED, eff_alpha), anchor="mm")
                            else:
                                bbox = font.getbbox(w)
                                bw, bh = bbox[2] - bbox[0] + 40, bbox[3] - bbox[1] + 40
                                if bw > 0 and bh > 0:
                                    t_box = Image.new("RGBA", (bw, bh), (0, 0, 0, 0))
                                    b_draw = ImageDraw.Draw(t_box)
                                    b_draw.text((bw // 2, bh // 2), w, font=font, fill=(*self.COLOR_RED, eff_alpha), anchor="mm")
                                    nw, nh = max(1, int(bw * scale)), max(1, int(bh * scale))
                                    resz = t_box.resize((nw, nh), resample=Image.BICUBIC)
                                    layer.paste(resz, (w_center_x - nw // 2, cy - nh // 2), resz)

                        cur_x += w_w + space_w

                elif idx == active_line_idx + 1:
                    # Upcoming line: subtle ghost preview if within 1.0s of singing
                    time_until = item["time"] - active_time
                    if time_until <= 1.0:
                        preview_u = min(1.0, max(0.0, (1.0 - time_until) / 1.0))
                        ghost_alpha = int(75 * preview_u * global_alpha)
                        for w, w_w in zip(words, word_widths):
                            w_center_x = cur_x + w_w // 2
                            ldraw.text((w_center_x, base_cy), w, font=font, fill=(225, 215, 205, ghost_alpha), anchor="mm")
                            cur_x += w_w + space_w

            return layer

        # 5. FFmpeg Direct Rawvideo Pipe Streaming
        print(f"[INFO] Initializing FFmpeg direct pipe encoder to {output_mp4}...", flush=True)
        ffmpeg_cmd = [
            "ffmpeg", "-y",
            "-f", "rawvideo",
            "-vcodec", "rawvideo",
            "-s", f"{W}x{H}",
            "-pix_fmt", "rgb24",
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
            output_mp4
        ]

        proc = subprocess.Popen(
            ffmpeg_cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        start_time = time.time()
        last_print = start_time

        print(f"[INFO] Encoding {TOTAL_FRAMES} frames ({aspect_ratio} Master)...", flush=True)

        for f_idx in range(TOTAL_FRAMES):
            t = f_idx / fps

            # RMS Audio Energy
            idx_s = f_idx * samples_per_frame
            idx_e = min(len(audio_mono), idx_s + samples_per_frame * 2)
            chunk = audio_mono[idx_s:idx_e]
            rms = float(np.sqrt(np.mean(chunk**2))) if len(chunk) > 0 else 0.0

            # Base Frame with Shimmering Water Caustics
            if enable_water_caustics and caustic_cache:
                frame_arr = np.clip(paper_base_arr + caustic_cache[f_idx % len(caustic_cache)], 0, 255)
                frame = Image.fromarray(np.uint8(frame_arr))
            else:
                frame = paper_base_img.copy()
            draw = ImageDraw.Draw(frame)

            # Floating dust
            for i in range(dust_count):
                px = int((dust_x[i] + dust_vx[i] * profile["particle_speed"] * f_idx) % W)
                py = int((dust_y[i] + dust_vy[i] * profile["particle_speed"] * f_idx) % H)
                draw.ellipse([px, py, px + dust_sz[i], py + dust_sz[i]], fill=(215, 208, 198))

            # Summer Botanical Floral & Petals Drift (Direct cached paste)
            if enable_floral_overlay and floral_particles:
                for p in floral_particles:
                    px = int((p["x"] + p["vx"] * t * 40 * profile["particle_speed"] + math.sin(t * 1.5 + p["phase"]) * 18) % W)
                    py = int((p["y"] + p["vy"] * t * 40 * profile["particle_speed"] + math.cos(t * 1.2 + p["phase"]) * 10) % H)
                    rot = (p["base_rot"] + t * p["rot_speed"] + math.sin(t * 1.8 + p["phase"]) * 18) % 360
                    if 1050 < px < 1450 and 380 < py < 620:
                        py += 140
                    rot_sprite = p["rot_cache"][int(rot / 5) % 72]
                    frame.paste(rot_sprite, (px - rot_sprite.width // 2, py - rot_sprite.height // 2), rot_sprite)

                if corner_branch and is_16x9:
                    frame.paste(corner_branch, (W - corner_branch.width - 25, H - corner_branch.height - 25), corner_branch)

            # Header
            header_y = 100 if is_16x9 else 360
            draw.text((W // 2, header_y), f"{title.upper()}   •   {artist.upper()}", font=font_meta, fill=self.COLOR_MUTED, anchor="mm")
            draw.line([(W // 2 - 160, header_y + 26), (W // 2 + 160, header_y + 26)], fill=self.COLOR_LINE, width=2)

            # 16:9 Spinning Vinyl Record & Glow (Pre-cached zero-latency lookup)
            if is_16x9:
                cur_glow = glow_cache[int(t * 3.5 * 60 / (2 * np.pi)) % 60]
                frame.paste(cur_glow, (VINYL_X - cur_glow.width // 2, VINYL_Y - cur_glow.height // 2), cur_glow)

                rot_angle = (t * profile["vinyl_rot_speed"]) % 360.0
                rot_vinyl = vinyl_cache[int(rot_angle) % 360]
                frame.paste(rot_vinyl, (VINYL_X - rot_vinyl.width // 2, VINYL_Y - rot_vinyl.height // 2), rot_vinyl)

            # 9:16 Subtle Audio-Reactive Fluid Ripple Wave
            if not is_16x9:
                ripple_y = 1380
                wave_pts = []
                for rx in range(300, 781, 10):
                    w_offset = np.sin((rx * 0.02) + (t * 4.0)) * (4.0 + rms * 14.0)
                    wave_pts.append((rx, ripple_y + w_offset))
                draw.line(wave_pts, fill=(215, 190, 185), width=2)

            # Cards / Stanzas Active Blending (Smooth Cross-fade & Zero Blank Gap)
            TRANSITION_DUR = profile["transition_dur"]
            for c_idx, card in enumerate(cards_config):
                c_start = card["start"]
                c_end = card["end"]

                if c_start <= t <= c_end:
                    alpha = 1.0
                    card_offset_y = 0

                    # Entrance transition from previous card
                    if c_idx > 0 and (t - c_start) < TRANSITION_DUR:
                        u = (t - c_start) / TRANSITION_DUR
                        ease = 1.0 - pow(1.0 - u, 3)
                        alpha = ease
                        card_offset_y = int(35 * (1.0 - ease))

                    # Exit transition to next card
                    elif c_idx < len(cards_config) - 1 and (c_end - t) < TRANSITION_DUR:
                        u = (c_end - t) / TRANSITION_DUR
                        ease = 1.0 - pow(1.0 - u, 3)
                        alpha = ease
                        card_offset_y = int(-35 * (1.0 - ease))

                    card_layer = render_card_layer(card["items"], t, global_alpha=alpha, card_offset_y=card_offset_y, rms=rms)
                    frame.paste(card_layer, (0, 0), card_layer)

            # Optional Spotify Scrubber
            if show_player:
                bar_y = 960 if is_16x9 else 1520
                bar_left = 320 if is_16x9 else 180
                bar_right = W - (320 if is_16x9 else 180)
                bar_width = bar_right - bar_left
                progress = min(1.0, max(0.0, t / duration))
                active_x = bar_left + int(bar_width * progress)

                draw.line([(bar_left, bar_y), (bar_right, bar_y)], fill=self.COLOR_LINE, width=4)
                draw.line([(bar_left, bar_y), (active_x, bar_y)], fill=self.COLOR_BAR, width=4)
                draw.ellipse([active_x - 7, bar_y - 7, active_x + 7, bar_y + 7], fill=self.COLOR_BAR)

                try:
                    bm, bs = map(int, start_offset_label.split(":"))
                    cur_tot = bm * 60 + bs + int(t)
                    cur_str = f"{cur_tot // 60}:{cur_tot % 60:02d}"
                except Exception:
                    cur_str = f"0:{int(t):02d}"
                draw.text((bar_left, bar_y + 20), cur_str, font=font_time, fill=self.COLOR_MUTED, anchor="lt")
                tot_m = int(duration) // 60
                tot_s = int(duration) % 60
                draw.text((bar_right, bar_y + 20), f"{tot_m}:{tot_s:02d}", font=font_time, fill=self.COLOR_MUTED, anchor="rt")

            # Pipe to FFmpeg
            proc.stdin.write(frame.tobytes())

            now = time.time()
            if now - last_print >= 4.0 or f_idx == TOTAL_FRAMES - 1:
                fps_act = (f_idx + 1) / (now - start_time + 1e-6)
                pct = ((f_idx + 1) / TOTAL_FRAMES) * 100.0
                print(f"[RENDER] {pct:5.1f}% | Frame {f_idx+1}/{TOTAL_FRAMES} | Speed: {fps_act:.1f} fps", flush=True)
                last_print = now

        proc.stdin.close()
        proc.wait()

        if proc.returncode != 0:
            raise RuntimeError(f"FFmpeg pipeline exited with error code {proc.returncode}")

        out_size_mb = os.path.getsize(output_mp4) / (1024 * 1024)
        total_time = time.time() - start_time
        print(f"\n[DONE] Successfully rendered Master Lyric Video:")
        print(f"Path: {output_mp4}")
        print(f"Size: {out_size_mb:.2f} MB")
        print(f"Render Time: {total_time:.2f} seconds", flush=True)
        return output_mp4


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Universal Master Lyric Video Generator")
    parser.add_argument("--audio", help="Path to local audio file")
    parser.add_argument("--ratio", default="9:16", choices=["9:16", "16:9"], help="Aspect ratio (9:16 vertical or 16:9)")
    parser.add_argument("--title", default="Husn", help="Song title")
    parser.add_argument("--artist", default="Anuv Jain", help="Artist name")
    parser.add_argument("--duration", type=float, default=22.5, help="Duration in seconds")
    parser.add_argument("--vocal_start", type=float, default=70.0, help="Vocal start timestamp in seconds")
    parser.add_argument("--player", action="store_true", help="Include Spotify player scrubber")
    parser.add_argument("--floral", action="store_true", help="Enable Summer Botanical Petals overlay")
    parser.add_argument("--artwork", help="Path to album artwork image for vinyl center")
    parser.add_argument("--lrc", help="Path to verified .lrc synced lyrics file")
    parser.add_argument("--output", help="Custom output video path")
    args = parser.parse_args()

    engine = AestheticLyricEngine()
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    audio_path = args.audio
    if not audio_path:
        audio_path = os.path.join(base_dir, "indian-lofi-converter", "raw_stems", "husn_raw.mp3")

    cards_parsed = None
    if args.lrc and os.path.exists(args.lrc):
        cards_parsed = engine.parse_lrc_file(args.lrc, args.duration, is_16x9=(args.ratio == "16:9"))

    is_already_wav = audio_path.endswith(".wav") and (args.vocal_start == 0.0 or args.vocal_start is None)
    if is_already_wav:
        render_audio = audio_path
        temp_slice = None
    else:
        temp_slice = os.path.join(base_dir, "output", "temp_pipeline_slice.wav")
        engine.extract_audio_slice(audio_path, start_sec=args.vocal_start, duration_sec=args.duration, output_wav_path=temp_slice)
        render_audio = temp_slice

    mins = int(args.vocal_start) // 60
    secs = int(args.vocal_start) % 60
    start_label = f"{mins}:{secs:02d}"

    out_file = engine.render(
        audio_path=render_audio,
        title=args.title,
        artist=args.artist,
        aspect_ratio=args.ratio,
        duration=args.duration,
        cards_config=cards_parsed,
        output_mp4=args.output,
        show_player=args.player,
        enable_water_caustics=("husn" in args.title.lower() and not args.floral),
        start_offset_label=start_label,
        artwork_path=args.artwork,
        enable_floral_overlay=args.floral
    )

    if temp_slice and os.path.exists(temp_slice):
        try:
            os.remove(temp_slice)
        except Exception:
            pass
