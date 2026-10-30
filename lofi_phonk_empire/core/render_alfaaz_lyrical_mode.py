"""
Lyrical Mode Style Lyric Video Renderer (Zero Black Overlays, Zero Jitter)
Matches exact aesthetic of https://youtu.be/JL6_VbpQRh4 (Lyrical Mode):
- 100% untouched video background (no dark overlay boxes, no letterbox strips)
- 100% ROCK-SOLID stationary text (Zero shaking, zero bobbing, zero jitter)
- Pure smooth opacity fade-in / fade-out transitions
- Crisp white typography with soft Gaussian drop shadow directly under glyphs
- Minimal bottom branding tag
"""

import os
import cv2
import numpy as np
from PIL import Image, ImageFont, ImageDraw, ImageFilter
import subprocess

def ease_in_out(t):
    # Smooth Hermite interpolation between 0 and 1
    return t * t * (3 - 2 * t)

def render_lyrical_mode_stable(font_choice="dancing_script"):
    video_in = "d:/facts_yt/lofi_phonk_empire/dreamina-seedance-2.0-720p_b_Create_a_premium_cin.mp4"
    audio_in = "d:/facts_yt/lofi_phonk_empire/raw_stems/audio/alfaaz_baaghan_vichon_viral_hook.mp3"
    
    if font_choice == "dancing_script":
        font_path = "d:/facts_yt/lofi_phonk_empire/assets/fonts_en/DancingScript.ttf"
        font_size = 56
        tag_suffix = "dancing_script"
    else:
        font_path = "d:/facts_yt/lofi_phonk_empire/assets/fonts_en/Playfair_Display.ttf"
        font_size = 46
        tag_suffix = "playfair"

    tag_font_path = "d:/facts_yt/lofi_phonk_empire/assets/fonts_en/BebasNeue.ttf"
    
    output_dir = "d:/facts_yt/lofi_phonk_empire/output/youtube_16x9"
    os.makedirs(output_dir, exist_ok=True)
    temp_video = f"d:/facts_yt/lofi_phonk_empire/temp_stable_{tag_suffix}_raw.mp4"
    final_output = os.path.join(output_dir, f"alfaaz_lyrical_mode_stable_{tag_suffix}_5s.mp4")
    
    cap = cv2.VideoCapture(video_in)
    fps = 24.0
    total_frames = 120 # 5.0 seconds
    width = 1280
    height = 720
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(temp_video, fourcc, fps, (width, height))
    
    font_lyric = ImageFont.truetype(font_path, font_size)
    font_tag = ImageFont.truetype(tag_font_path, 24)
    
    line1 = "Baaghan vichon main te tode"
    line2 = "tere layi gulab ve..."
    brand_tag = "ALFAAZ  •  HAMZA MALIK"
    
    # Pre-render static text and shadow templates once for maximum sharpness and zero jitter!
    # 1. Shadow template
    shadow_base = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    d_sh = ImageDraw.Draw(shadow_base)
    y_center = 380 # ROCK-SOLID FIXED Y-POSITION (NO JITTER, NO SINE WAVE)
    
    d_sh.text((width // 2, y_center - 36), line1, font=font_lyric, fill=(2, 4, 10, 240), anchor="mm")
    d_sh.text((width // 2, y_center + 38), line2, font=font_lyric, fill=(2, 4, 10, 240), anchor="mm")
    d_sh.text((width // 2, 667), brand_tag, font=font_tag, fill=(2, 4, 10, 200), anchor="mm")
    shadow_blurred_base = shadow_base.filter(ImageFilter.GaussianBlur(radius=5))
    
    # 2. Text template
    text_base = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    d_txt = ImageDraw.Draw(text_base)
    d_txt.text((width // 2, y_center - 38), line1, font=font_lyric, fill=(255, 255, 255, 255), anchor="mm")
    d_txt.text((width // 2, y_center + 36), line2, font=font_lyric, fill=(255, 255, 255, 255), anchor="mm")
    d_txt.text((width // 2, 665), brand_tag, font=font_tag, fill=(255, 255, 255, 220), anchor="mm")
    
    # Convert templates to numpy for ultra-fast alpha modulation
    shadow_arr = np.array(shadow_blurred_base, dtype=np.float32)
    text_arr = np.array(text_base, dtype=np.float32)
    
    for f in range(total_frames):
        ret, frame = cap.read()
        if not ret:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = cap.read()
            
        t = f / fps # 0.0 to 5.0 seconds
        
        # Smooth Fade-In (0.0s to 0.6s) and Fade-Out (4.4s to 5.0s)
        if t < 0.6:
            fade = ease_in_out(t / 0.6)
        elif t > 4.4:
            fade = ease_in_out((5.0 - t) / 0.6)
        else:
            fade = 1.0
            
        # 1. Natural Video Frame (100% natural colors - ZERO black overlay!)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        im = Image.fromarray(frame_rgb).convert('RGBA')
        
        if fade > 0.01:
            # Modulate alpha smoothly without moving a single pixel!
            cur_shadow = shadow_arr.copy()
            cur_shadow[:, :, 3] *= fade
            cur_shadow_img = Image.fromarray(np.uint8(cur_shadow), 'RGBA')
            
            cur_text = text_arr.copy()
            cur_text[:, :, 3] *= fade
            cur_text_img = Image.fromarray(np.uint8(cur_text), 'RGBA')
            
            # Composite shadow and text
            im = Image.alpha_composite(im, cur_shadow_img)
            im = Image.alpha_composite(im, cur_text_img)
            
        # Output frame
        final_bgr = cv2.cvtColor(np.array(im.convert('RGB')), cv2.COLOR_RGB2BGR)
        out.write(final_bgr)
        
    cap.release()
    out.release()
    
    # Mux with exact audio slice from 5.76s to 10.76s
    cmd = [
        "ffmpeg", "-y",
        "-ss", "00:00:05.76", "-t", "5.0", "-i", audio_in,
        "-i", temp_video,
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
        "-c:a", "aac", "-b:a", "192k",
        "-map", "1:v:0", "-map", "0:a:0",
        "-shortest", final_output
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if os.path.exists(temp_video):
        os.remove(temp_video)
        
    print(f"[{font_choice}] Stable render complete: {final_output}")
    return final_output

if __name__ == "__main__":
    render_lyrical_mode_stable("dancing_script")
    render_lyrical_mode_stable("playfair")
