"""
Alfaaz Full Master Lyrical Mode Video Renderer (45 Seconds Master)
Complete Viral Song Production Master:
- Audio: 00:00:00 to 00:00:45 (Full Viral Hook & Acoustic Outro)
- Visual Plate: Dreamina 720p Himalayan Dusk Cinematic Loop (Ping-Pong)
- Aesthetic: 100% Lyrical Mode (Zero black overlays, natural mountain colors)
- Typography: Dancing Script White Calligraphy with soft Gaussian Drop Shadow
- Stability: Rock-solid fixed coordinates (Zero jitter, zero wobble)
- Transitions: Hermite ease-in-out cross dissolves
- Master Quality: CRF 17 High Profile, 320k Audio Master
"""

import os
import cv2
import numpy as np
from PIL import Image, ImageFont, ImageDraw, ImageFilter
import subprocess

def ease_in_out(val):
    val = max(0.0, min(1.0, val))
    return val * val * (3.0 - 2.0 * val)

def render_alfaaz_full_master():
    video_in = "d:/facts_yt/lofi_phonk_empire/dreamina-seedance-2.0-720p_b_Create_a_premium_cin.mp4"
    audio_in = "d:/facts_yt/lofi_phonk_empire/raw_stems/audio/alfaaz_baaghan_vichon_viral_hook.mp3"
    font_path = "d:/facts_yt/lofi_phonk_empire/assets/fonts_en/DancingScript.ttf"
    tag_font_path = "d:/facts_yt/lofi_phonk_empire/assets/fonts_en/BebasNeue.ttf"
    
    output_dir = "d:/facts_yt/lofi_phonk_empire/output/youtube_16x9"
    os.makedirs(output_dir, exist_ok=True)
    temp_video = "d:/facts_yt/lofi_phonk_empire/temp_alfaaz_master_raw.mp4"
    final_output = os.path.join(output_dir, "alfaaz_official_lyrical_mode_master_45s.mp4")
    
    # 1. Load source video frames
    cap = cv2.VideoCapture(video_in)
    raw_frames = []
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        raw_frames.append(frame)
    cap.release()
    n_raw = len(raw_frames)
    print(f"Loaded {n_raw} background frames for ping-pong cycling.")
    
    fps = 24.0
    duration_sec = 45.0
    total_frames = int(fps * duration_sec) # 1080 frames
    width = 1280
    height = 720
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(temp_video, fourcc, fps, (width, height))
    
    font_lyric_2line = ImageFont.truetype(font_path, 56)
    font_lyric_1line = ImageFont.truetype(font_path, 58)
    font_tag = ImageFont.truetype(tag_font_path, 24)
    
    brand_tag = "ALFAAZ  •  HAMZA MALIK x ZAIN ZOHAIB"
    
    # Bottom Tag Layer
    tag_img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    d_tag = ImageDraw.Draw(tag_img)
    d_tag.text((width // 2, 667), brand_tag, font=font_tag, fill=(2, 4, 10, 220), anchor="mm")
    tag_blurred = tag_img.filter(ImageFilter.GaussianBlur(radius=4))
    d_tag_fg = ImageDraw.Draw(tag_blurred)
    d_tag_fg.text((width // 2, 665), brand_tag, font=font_tag, fill=(255, 255, 255, 220), anchor="mm")
    tag_arr = np.array(tag_blurred, dtype=np.float32)
    
    # 2. Complete Lyrics Schedule (0.0s to 45.0s)
    lyrics_schedule = [
        {
            "start": 0.50,
            "end": 5.20,
            "lines": ["Vekhan tainu raat saari chadhdi saver tak..."],
            "font": font_lyric_1line,
            "is_2line": False
        },
        {
            "start": 5.76,
            "end": 11.20,
            "lines": ["Baaghan vichon main te tode", "tere layi gulab ve..."],
            "font": font_lyric_2line,
            "is_2line": True
        },
        {
            "start": 11.76,
            "end": 16.80,
            "lines": ["Main te bas kehnda rehnda", "aap janab ve!"],
            "font": font_lyric_2line,
            "is_2line": True
        },
        {
            "start": 17.30,
            "end": 20.00,
            "lines": ["Tu te taareyan ton vi sohna ae..."],
            "font": font_lyric_1line,
            "is_2line": False
        },
        {
            "start": 20.10,
            "end": 22.90,
            "lines": ["Tere warga koi na hona ae!"],
            "font": font_lyric_1line,
            "is_2line": False
        },
        {
            "start": 23.10,
            "end": 25.80,
            "lines": ["Tu te taareyan ton vi sohna ae..."],
            "font": font_lyric_1line,
            "is_2line": False
        },
        {
            "start": 26.00,
            "end": 29.20,
            "lines": ["Tere warga koi na hona ae!"],
            "font": font_lyric_1line,
            "is_2line": False
        },
        {
            "start": 29.60,
            "end": 33.50,
            "lines": ["Jinna aunda si mainu pyar karna ji..."],
            "font": font_lyric_1line,
            "is_2line": False
        },
        {
            "start": 33.90,
            "end": 38.50,
            "lines": ["Main te tere naal kar leya ae..."],
            "font": font_lyric_1line,
            "is_2line": False
        }
    ]
    
    # 3. Pre-render templates for rock-solid stability & high FPS
    y_center = 380
    for item in lyrics_schedule:
        lyric_img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        f = item["font"]
        lines = item["lines"]
        
        # Shadow
        sh_img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        d_sh = ImageDraw.Draw(sh_img)
        if item["is_2line"]:
            d_sh.text((width // 2, y_center - 36), lines[0], font=f, fill=(2, 4, 10, 240), anchor="mm")
            d_sh.text((width // 2, y_center + 38), lines[1], font=f, fill=(2, 4, 10, 240), anchor="mm")
        else:
            d_sh.text((width // 2, y_center), lines[0], font=f, fill=(2, 4, 10, 240), anchor="mm")
        sh_blur = sh_img.filter(ImageFilter.GaussianBlur(radius=5))
        
        # Text
        txt_img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        d_txt = ImageDraw.Draw(txt_img)
        if item["is_2line"]:
            d_txt.text((width // 2, y_center - 38), lines[0], font=f, fill=(255, 255, 255, 255), anchor="mm")
            d_txt.text((width // 2, y_center + 36), lines[1], font=f, fill=(255, 255, 255, 255), anchor="mm")
        else:
            d_txt.text((width // 2, y_center - 2), lines[0], font=f, fill=(255, 255, 255, 255), anchor="mm")
            
        combined = Image.alpha_composite(sh_blur, txt_img)
        item["arr"] = np.array(combined, dtype=np.float32)

    cycle = 2 * (n_raw - 1)
    
    print("Rendering 1080 frames (45.0 seconds master)...")
    for f in range(total_frames):
        t = f / fps
        
        # Ping-pong background frame selection
        pos = f % cycle
        frame_idx = pos if pos < n_raw else (cycle - pos)
        raw_bgr = raw_frames[frame_idx]
        frame_rgb = cv2.cvtColor(raw_bgr, cv2.COLOR_BGR2RGB)
        im = Image.fromarray(frame_rgb).convert('RGBA')
        
        # Bottom branding tag
        tag_fade = ease_in_out(min(1.0, t / 1.0))
        if tag_fade > 0.01:
            cur_tag = tag_arr.copy()
            cur_tag[:, :, 3] *= tag_fade
            im = Image.alpha_composite(im, Image.fromarray(np.uint8(cur_tag), 'RGBA'))
            
        # Check active lyric line
        for item in lyrics_schedule:
            st = item["start"]
            et = item["end"]
            if st <= t <= et:
                fade_in_time = 0.40
                fade_out_time = 0.40
                if (t - st) < fade_in_time:
                    alpha = ease_in_out((t - st) / fade_in_time)
                elif (et - t) < fade_out_time:
                    alpha = ease_in_out((et - t) / fade_out_time)
                else:
                    alpha = 1.0
                    
                if alpha > 0.01:
                    cur_lyric = item["arr"].copy()
                    cur_lyric[:, :, 3] *= alpha
                    im = Image.alpha_composite(im, Image.fromarray(np.uint8(cur_lyric), 'RGBA'))
                break
                
        final_bgr = cv2.cvtColor(np.array(im.convert('RGB')), cv2.COLOR_RGB2BGR)
        out.write(final_bgr)
        
    out.release()
    print("Video frames generated. Muxing 45-second high-fidelity master audio...")
    
    # Mux full 45s audio
    cmd = [
        "ffmpeg", "-y",
        "-i", audio_in,
        "-i", temp_video,
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "17", "-preset", "slow",
        "-c:a", "aac", "-b:a", "320k",
        "-map", "1:v:0", "-map", "0:a:0",
        "-shortest", final_output
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if os.path.exists(temp_video):
        os.remove(temp_video)
        
    print("Full 45-second master video rendered successfully:", final_output)
    return final_output

if __name__ == "__main__":
    render_alfaaz_full_master()
