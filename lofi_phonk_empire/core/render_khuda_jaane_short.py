"""
Khuda Jaane Viral Short / Reel Engine (9:16 Vertical & 16:9 Lyrical Mode)
--------------------------------------------------------------------------
- Audio: Sourced from official YRF audio, sliced at viral drop hook (44.5s).
- Visuals: Untouched Dreamina cinematic video plate with seamless ping-pong loop.
- Typography: Rock-solid Dancing Script white calligraphy with localized Gaussian drop-shadow.
- Stability: Fixed coordinates, zero jitter, zero shake, zero dark overlay boxes.
- Transitions: Hermite ease-in-out (t*t*(3-2*t)) cross-dissolves.
- Output:
    * Vertical 9:16 (1080x1920) for YouTube Shorts & Instagram Reels.
    * Horizontal 16:9 (1280x720) for YouTube Lyrical Mode Short cut.
"""

import os
import sys
import time
import subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def ease_in_out(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)

def render_short(mode="9x16"):
    start_time = time.time()
    
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    if not os.path.exists(os.path.join(repo_root, "lofi_phonk_empire")):
        repo_root = os.getcwd()
        
    audio_path = os.path.join(repo_root, "lofi_phonk_empire", "raw_stems", "audio", "khuda_jaane_viral_hook_44s.mp3")
    video_stem_path = os.path.join(repo_root, "lofi_phonk_empire", "dreamina-seedance-2.0-720p_b_Create_a_premium_cin.mp4")
    
    font_lyric_path = os.path.join(repo_root, "lofi_phonk_empire", "assets", "fonts_en", "DancingScript.ttf")
    font_tag_path = os.path.join(repo_root, "lofi_phonk_empire", "assets", "fonts_en", "BebasNeue.ttf")
    
    if mode == "9x16":
        width, height = 1080, 1920
        font_size_lyric = 72
        font_size_tag = 36
        y_center = 960
        y_tag = 1750
        out_dir = os.path.join(repo_root, "lofi_phonk_empire", "output", "reels_9x16")
        final_output = os.path.join(out_dir, "khuda_jaane_viral_short_9x16.mp4")
    else:
        width, height = 1280, 720
        font_size_lyric = 54
        font_size_tag = 24
        y_center = 380
        y_tag = 665
        out_dir = os.path.join(repo_root, "lofi_phonk_empire", "output", "youtube_16x9")
        final_output = os.path.join(out_dir, "khuda_jaane_viral_hook_16x9.mp4")
        
    os.makedirs(out_dir, exist_ok=True)
    
    print("=" * 70, flush=True)
    print(f"  KHUDA JAANE VIRAL HOOK ({mode.upper()}) - KK & SHILPA RAO", flush=True)
    print("=" * 70, flush=True)

    # 1. Probe Audio Duration
    ffprobe_cmd = [
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", audio_path
    ]
    res = subprocess.run(ffprobe_cmd, capture_output=True, text=True, check=True)
    audio_duration = float(res.stdout.strip())
    
    fps = 24.0
    total_frames = int(audio_duration * fps)
    print(f"[OK] Audio Duration: {audio_duration:.2f}s | Target Frames: {total_frames} @ {fps} fps ({width}x{height})", flush=True)

    # 2. Extract and crop/scale background video frames
    print("[INIT] Loading background video plate frames...", flush=True)
    # Read raw 1280x720 frames from video
    ffmpeg_read_cmd = [
        "ffmpeg", "-v", "error", "-i", video_stem_path,
        "-f", "image2pipe", "-pix_fmt", "rgb24", "-vcodec", "rawvideo", "-"
    ]
    pipe_read = subprocess.Popen(ffmpeg_read_cmd, stdout=subprocess.PIPE, bufsize=1280 * 720 * 3 * 10)
    
    raw_w, raw_h = 1280, 720
    frame_bytes = raw_w * raw_h * 3
    bg_frames = []
    
    while True:
        raw_b = pipe_read.stdout.read(frame_bytes)
        if len(raw_b) < frame_bytes:
            break
        img_arr = np.frombuffer(raw_b, dtype=np.uint8).reshape((raw_h, raw_w, 3))
        
        if mode == "9x16":
            # Scale so height = 1920, then center crop width to 1080
            pil_img = Image.fromarray(img_arr)
            # scale factor: 1920 / 720 = 2.6667 -> new_w = int(1280 * 2.6667) = 3413
            new_w = int(raw_w * (height / raw_h))
            pil_scaled = pil_img.resize((new_w, height), Image.Resampling.BILINEAR)
            left = (new_w - width) // 2
            pil_cropped = pil_scaled.crop((left, 0, left + width, height))
            bg_frames.append(np.array(pil_cropped))
        else:
            # 1280x720 native
            bg_frames.append(img_arr)
            
    pipe_read.stdout.close()
    pipe_read.wait()
    
    num_bg = len(bg_frames)
    cycle_len = 2 * (num_bg - 1)
    print(f"[OK] Cached {num_bg} background frames. Ping-pong cycle: {cycle_len} frames", flush=True)

    # 3. Lyrics Schedule (Ground-Truth Whisper Aligned)
    lyrics_schedule = [
        {"start": 0.50, "end": 3.80, "text": "Sajde mein yun hi jhukta hoon"},
        {"start": 3.80, "end": 6.90, "text": "Tum pe hi aa ke rukta hoon"},
        {"start": 6.90, "end": 9.90, "text": "Kya yeh sab ko hota hai"},
        {"start": 9.90, "end": 12.90, "text": "Hum ko kya lena hai sab se"},
        {"start": 12.90, "end": 15.90, "text": "Tum se hi sab batein ab se"},
        {"start": 15.90, "end": 20.60, "text": "Ban gaye ho tum meri dua..."},
        {"start": 20.60, "end": 26.60, "text": "Khuda Jaane ke mein fida hun"},
        {"start": 26.60, "end": 32.60, "text": "Khuda Jaane mein mit gaya"},
        {"start": 32.60, "end": 39.20, "text": "Khuda jaane yeh kyun huwa hai"},
        {"start": 39.20, "end": 44.20, "text": "Ke ban gaye ho tum mere khuda!"}
    ]

    # 4. Pre-render Typography & Shadows
    print("[INIT] Pre-rendering calligraphy typography masks...", flush=True)
    font_lyric = ImageFont.truetype(font_lyric_path, font_size_lyric)
    font_tag = ImageFont.truetype(font_tag_path, font_size_tag)
    
    brand_tag = "KHUDA JAANE  •  KK & SHILPA RAO"
    
    # Tag Template
    tag_sh = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    d_tsh = ImageDraw.Draw(tag_sh)
    d_tsh.text((width // 2, y_tag + 2), brand_tag, font=font_tag, fill=(2, 4, 10, 200), anchor="mm")
    tag_sh_arr = np.array(tag_sh.filter(ImageFilter.GaussianBlur(radius=5)), dtype=np.float32)
    
    tag_txt = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    d_ttx = ImageDraw.Draw(tag_txt)
    d_ttx.text((width // 2, y_tag), brand_tag, font=font_tag, fill=(255, 255, 255, 220), anchor="mm")
    tag_txt_arr = np.array(tag_txt, dtype=np.float32)

    pre_rendered_lyrics = []
    for item in lyrics_schedule:
        text = item["text"]
        
        # Shadow
        sh_img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        d_sh = ImageDraw.Draw(sh_img)
        d_sh.text((width // 2, y_center + 3), text, font=font_lyric, fill=(2, 4, 10, 240), anchor="mm")
        sh_arr = np.array(sh_img.filter(ImageFilter.GaussianBlur(radius=6)), dtype=np.float32)
        
        # Text
        txt_img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        d_tx = ImageDraw.Draw(txt_img)
        d_tx.text((width // 2, y_center), text, font=font_lyric, fill=(255, 255, 255, 255), anchor="mm")
        txt_arr = np.array(txt_img, dtype=np.float32)
        
        pre_rendered_lyrics.append({
            "start": item["start"],
            "end": item["end"],
            "sh_rgb": sh_arr[:, :, :3],
            "sh_a": sh_arr[:, :, 3] / 255.0,
            "txt_rgb": txt_arr[:, :, :3],
            "txt_a": txt_arr[:, :, 3] / 255.0
        })

    # 5. FFmpeg Streaming Process
    print(f"[FFMPEG] Streaming to {final_output}...", flush=True)
    ffmpeg_out_cmd = [
        "ffmpeg", "-y",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{width}x{height}", "-r", str(fps),
        "-i", "-",
        "-i", audio_path,
        "-c:v", "libx264", "-preset", "fast", "-crf", "17", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "320k",
        "-map", "0:v:0", "-map", "1:a:0",
        "-shortest", final_output
    ]
    proc = subprocess.Popen(ffmpeg_out_cmd, stdin=subprocess.PIPE)

    ts_rgb = tag_sh_arr[:, :, :3]
    ts_a = tag_sh_arr[:, :, 3] / 255.0
    tt_rgb = tag_txt_arr[:, :, :3]
    tt_a = tag_txt_arr[:, :, 3] / 255.0

    fade_duration = 0.40
    last_print = time.time()
    
    for f in range(total_frames):
        t = f / fps
        
        # Ping-pong index
        c_idx = f % cycle_len
        bg_idx = c_idx if c_idx < num_bg else (cycle_len - c_idx)
        frame_rgb = bg_frames[bg_idx].astype(np.float32)
        
        # Bottom tag
        frame_rgb = frame_rgb * (1.0 - ts_a[:, :, None]) + ts_rgb * ts_a[:, :, None]
        frame_rgb = frame_rgb * (1.0 - tt_a[:, :, None]) + tt_rgb * tt_a[:, :, None]
        
        # Active lyric
        for item in pre_rendered_lyrics:
            st = item["start"]
            en = item["end"]
            if st <= t <= en:
                if t - st < fade_duration:
                    fade = ease_in_out((t - st) / fade_duration)
                elif en - t < fade_duration:
                    fade = ease_in_out((en - t) / fade_duration)
                else:
                    fade = 1.0
                    
                if fade > 0.01:
                    cur_sh_a = (item["sh_a"] * fade)[:, :, None]
                    frame_rgb = frame_rgb * (1.0 - cur_sh_a) + item["sh_rgb"] * cur_sh_a
                    
                    cur_txt_a = (item["txt_a"] * fade)[:, :, None]
                    frame_rgb = frame_rgb * (1.0 - cur_txt_a) + item["txt_rgb"] * cur_txt_a
                break
                
        proc.stdin.write(np.clip(frame_rgb, 0, 255).astype(np.uint8).tobytes())
        
        if time.time() - last_print >= 5.0 or f == total_frames - 1:
            pct = ((f + 1) / total_frames) * 100.0
            fps_speed = (f + 1) / max(0.001, time.time() - start_time)
            print(f"[{mode.upper()} RENDER] {pct:5.1f}% | Frame {f+1}/{total_frames} | Speed: {fps_speed:.1f} fps", flush=True)
            last_print = time.time()

    proc.stdin.close()
    proc.wait()
    
    total_time = time.time() - start_time
    size_mb = os.path.getsize(final_output) / (1024 * 1024)
    print("=" * 70, flush=True)
    print(f"[SUCCESS] {mode.upper()} Render completed in {total_time:.1f}s ({total_frames/total_time:.1f} fps)!")
    print(f"Path: {final_output} ({size_mb:.2f} MB)")
    print("=" * 70, flush=True)
    return final_output

if __name__ == "__main__":
    mode_arg = sys.argv[1] if len(sys.argv) > 1 else "9x16"
    render_short(mode_arg)
