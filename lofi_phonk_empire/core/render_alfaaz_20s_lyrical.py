"""
Alfaaz 20-Second Lyrical Mode Video Renderer
- 20.0 Seconds total runtime (Audio: 00:00:05.76 to 00:00:25.76)
- Exact Lyrical Mode aesthetic (Zero dark overlays, natural Dreamina sunset backdrop)
- Seamless ping-pong loop of 720p cinematic background (zero jump cuts)
- 5 multi-line lyric transitions with buttery smooth Hermite ease-in-out dissolves
- 100% Rock-solid coordinates (Zero shaking, zero jitter)
"""

import os
import cv2
import numpy as np
from PIL import Image, ImageFont, ImageDraw, ImageFilter
import subprocess

def ease_in_out(val):
    val = max(0.0, min(1.0, val))
    return val * val * (3.0 - 2.0 * val)

def render_alfaaz_20s():
    video_in = "d:/facts_yt/lofi_phonk_empire/dreamina-seedance-2.0-720p_b_Create_a_premium_cin.mp4"
    audio_in = "d:/facts_yt/lofi_phonk_empire/raw_stems/audio/alfaaz_baaghan_vichon_viral_hook.mp3"
    font_path = "d:/facts_yt/lofi_phonk_empire/assets/fonts_en/DancingScript.ttf"
    tag_font_path = "d:/facts_yt/lofi_phonk_empire/assets/fonts_en/BebasNeue.ttf"
    
    output_dir = "d:/facts_yt/lofi_phonk_empire/output/youtube_16x9"
    os.makedirs(output_dir, exist_ok=True)
    temp_video = "d:/facts_yt/lofi_phonk_empire/temp_alfaaz_20s_raw.mp4"
    final_output = os.path.join(output_dir, "alfaaz_lyrical_mode_20s.mp4")
    
    # 1. Load source video frames for ping-pong looping
    cap = cv2.VideoCapture(video_in)
    raw_frames = []
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        raw_frames.append(frame)
    cap.release()
    n_raw = len(raw_frames)
    print(f"Loaded {n_raw} background frames.")
    
    fps = 24.0
    duration_sec = 20.0
    total_frames = int(fps * duration_sec) # 480 frames
    width = 1280
    height = 720
    
    # Setup video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(temp_video, fourcc, fps, (width, height))
    
    font_lyric_2line = ImageFont.truetype(font_path, 56)
    font_lyric_1line = ImageFont.truetype(font_path, 60)
    font_tag = ImageFont.truetype(tag_font_path, 24)
    
    brand_tag = "ALFAAZ  •  HAMZA MALIK"
    
    # Static Bottom Tag Layer (Shadow + Text)
    tag_img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    d_tag = ImageDraw.Draw(tag_img)
    d_tag.text((width // 2, 667), brand_tag, font=font_tag, fill=(2, 4, 10, 200), anchor="mm")
    tag_blurred = tag_img.filter(ImageFilter.GaussianBlur(radius=4))
    d_tag_fg = ImageDraw.Draw(tag_blurred)
    d_tag_fg.text((width // 2, 665), brand_tag, font=font_tag, fill=(255, 255, 255, 220), anchor="mm")
    tag_arr = np.array(tag_blurred, dtype=np.float32)
    
    # 2. Define lyrics schedule: (start_t, end_t, [lines])
    # Relative to audio timestamp 00:00:05.76
    lyrics_schedule = [
        {
            "start": 0.0,
            "end": 5.70,
            "lines": ["Baaghan vichon main te tode", "tere layi gulab ve..."],
            "font": font_lyric_2line,
            "is_2line": True
        },
        {
            "start": 5.80,
            "end": 11.40,
            "lines": ["Main te bas kehnda rehnda", "aap janab ve!"],
            "font": font_lyric_2line,
            "is_2line": True
        },
        {
            "start": 11.50,
            "end": 14.10,
            "lines": ["Tu te taareyan ton vi sohna ae..."],
            "font": font_lyric_1line,
            "is_2line": False
        },
        {
            "start": 14.20,
            "end": 17.10,
            "lines": ["Tere warga koi na hona ae!"],
            "font": font_lyric_1line,
            "is_2line": False
        },
        {
            "start": 17.20,
            "end": 20.00,
            "lines": ["Tu te taareyan ton vi sohna ae..."],
            "font": font_lyric_1line,
            "is_2line": False
        }
    ]
    
    # 3. Pre-render each lyric segment template for zero jitter & high FPS
    y_center = 380 # Completely Rock-solid
    for item in lyrics_schedule:
        lyric_img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        d_lyric = ImageDraw.Draw(lyric_img)
        f = item["font"]
        lines = item["lines"]
        
        # Shadow pass
        sh_img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        d_sh = ImageDraw.Draw(sh_img)
        if item["is_2line"]:
            d_sh.text((width // 2, y_center - 36), lines[0], font=f, fill=(2, 4, 10, 240), anchor="mm")
            d_sh.text((width // 2, y_center + 38), lines[1], font=f, fill=(2, 4, 10, 240), anchor="mm")
        else:
            d_sh.text((width // 2, y_center), lines[0], font=f, fill=(2, 4, 10, 240), anchor="mm")
        sh_blur = sh_img.filter(ImageFilter.GaussianBlur(radius=5))
        
        # Text pass
        txt_img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        d_txt = ImageDraw.Draw(txt_img)
        if item["is_2line"]:
            d_txt.text((width // 2, y_center - 38), lines[0], font=f, fill=(255, 255, 255, 255), anchor="mm")
            d_txt.text((width // 2, y_center + 36), lines[1], font=f, fill=(255, 255, 255, 255), anchor="mm")
        else:
            d_txt.text((width // 2, y_center - 2), lines[0], font=f, fill=(255, 255, 255, 255), anchor="mm")
            
        combined = Image.alpha_composite(sh_blur, txt_img)
        item["arr"] = np.array(combined, dtype=np.float32)

    # Ping-pong loop cycle length: 2 * (n_raw - 1)
    cycle = 2 * (n_raw - 1)
    
    print("Rendering 480 frames (20 seconds)...")
    for f in range(total_frames):
        t = f / fps
        
        # Ping-pong frame index
        pos = f % cycle
        if pos < n_raw:
            frame_idx = pos
        else:
            frame_idx = cycle - pos
            
        raw_bgr = raw_frames[frame_idx]
        frame_rgb = cv2.cvtColor(raw_bgr, cv2.COLOR_BGR2RGB)
        im = Image.fromarray(frame_rgb).convert('RGBA')
        
        # Blend bottom branding tag (fade in over 1.0s)
        tag_fade = ease_in_out(min(1.0, t / 1.0))
        if tag_fade > 0.01:
            cur_tag = tag_arr.copy()
            cur_tag[:, :, 3] *= tag_fade
            im = Image.alpha_composite(im, Image.fromarray(np.uint8(cur_tag), 'RGBA'))
            
        # Determine active lyric item and its dissolve alpha
        for item in lyrics_schedule:
            st = item["start"]
            et = item["end"]
            if st <= t <= et:
                # 0.45s smooth fade in, 0.45s smooth fade out
                dur = et - st
                fade_in_time = 0.45
                fade_out_time = 0.45
                
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
                break # Only one lyric block at a time
                
        # Write final BGR frame
        final_bgr = cv2.cvtColor(np.array(im.convert('RGB')), cv2.COLOR_RGB2BGR)
        out.write(final_bgr)
        
    out.release()
    print("Video frames generated. Muxing 20-second audio...")
    
    # Mux with exact 20-second audio slice from 5.76s to 25.76s
    cmd = [
        "ffmpeg", "-y",
        "-ss", "00:00:05.76", "-t", "20.0", "-i", audio_in,
        "-i", temp_video,
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
        "-c:a", "aac", "-b:a", "192k",
        "-map", "1:v:0", "-map", "0:a:0",
        "-shortest", final_output
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if os.path.exists(temp_video):
        os.remove(temp_video)
        
    print("20-second final video rendered successfully:", final_output)
    return final_output

if __name__ == "__main__":
    render_alfaaz_20s()
