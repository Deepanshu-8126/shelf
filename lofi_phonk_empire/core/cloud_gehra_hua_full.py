"""
Gehra Hua Full Master Cloud Renderer (GitHub Actions Cloud Engine)
-----------------------------------------------------------------
- Full-length official track (3:45) - 100% pure audio, ZERO movie dialogue, ZERO intro ads.
- Lyrical Mode Design Lock:
    * 100% untouched video background (ZERO dark overlay boxes, ZERO tinting).
    * Rock-solid fixed coordinates (y = 380, ZERO bobbing, ZERO jitter).
    * Localized Gaussian drop shadow (radius 5, dark alpha 240) beneath glyphs.
    * Hermite ease-in-out (t*t*(3-2*t)) cross-dissolves.
    * 193-frame ping-pong seamless loop (zero jump cuts).
- Streamed directly to FFmpeg stdin (no intermediate raw files).
- Designed for GitHub Actions cloud runners (Ubuntu 64-bit).
"""

import os
import sys
import time
import json
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

def main():
    print("=" * 70, flush=True)
    print("  GEHRA HUA - ARIJIT SINGH (FULL MASTER CLOUD RENDERER)", flush=True)
    print("=" * 70, flush=True)
    
    start_time = time.time()
    
    # Base paths (works both locally and in GitHub Actions)
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    audio_path = os.path.join(repo_root, "lofi_phonk_empire", "raw_stems", "audio", "gehra_hua_full_pure.mp3")
    video_stem_path = os.path.join(repo_root, "lofi_phonk_empire", "dreamina-seedance-2.0-720p_b_Create_a_premium_cin.mp4")
    schedule_path = os.path.join(repo_root, "lofi_phonk_empire", "raw_stems", "lyrics", "gehra_hua_full_schedule.json")
    
    font_lyric_path = os.path.join(repo_root, "lofi_phonk_empire", "assets", "fonts_en", "DancingScript.ttf")
    font_tag_path = os.path.join(repo_root, "lofi_phonk_empire", "assets", "fonts_en", "BebasNeue.ttf")
    
    output_dir = os.path.join(repo_root, "lofi_phonk_empire", "output", "youtube_16x9")
    os.makedirs(output_dir, exist_ok=True)
    final_output = os.path.join(output_dir, "gehra_hua_full_master.mp4")
    
    # 1. Verify Assets
    for p in [audio_path, video_stem_path, schedule_path, font_lyric_path, font_tag_path]:
        if not os.path.exists(p):
            raise FileNotFoundError(f"Missing required asset: {p}")
            
    print(f"[OK] Audio Source: {audio_path}", flush=True)
    print(f"[OK] Background Video: {video_stem_path}", flush=True)
    print(f"[OK] Lyrics Schedule: {schedule_path}", flush=True)

    # 2. Probe Audio Duration
    ffprobe_cmd = [
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", audio_path
    ]
    res = subprocess.run(ffprobe_cmd, capture_output=True, text=True, check=True)
    audio_duration = float(res.stdout.strip())
    
    fps = 24.0
    width = 1280
    height = 720
    total_frames = int(audio_duration * fps)
    print(f"[OK] Audio Duration: {audio_duration:.2f}s | Target Frames: {total_frames} @ {fps} fps", flush=True)

    # 3. Load Lyrics Schedule
    with open(schedule_path, "r", encoding="utf-8") as f:
        lyrics_schedule = json.load(f)
    print(f"[OK] Loaded {len(lyrics_schedule)} timed lyric events", flush=True)

    # 4. Pre-extract Background Video Frames into Memory (193 frames = ~520MB RAM)
    print("[INIT] Loading background video plate frames into memory...", flush=True)
    ffmpeg_read_cmd = [
        "ffmpeg", "-v", "error", "-i", video_stem_path,
        "-f", "image2pipe", "-pix_fmt", "rgb24", "-vcodec", "rawvideo", "-"
    ]
    pipe_read = subprocess.Popen(ffmpeg_read_cmd, stdout=subprocess.PIPE, bufsize=width * height * 3 * 10)
    bg_frames = []
    frame_bytes = width * height * 3
    while True:
        raw_b = pipe_read.stdout.read(frame_bytes)
        if len(raw_b) < frame_bytes:
            break
        bg_frames.append(np.frombuffer(raw_b, dtype=np.uint8).reshape((height, width, 3)))
    pipe_read.stdout.close()
    pipe_read.wait()
    
    num_bg = len(bg_frames)
    cycle_len = 2 * (num_bg - 1)
    print(f"[OK] Cached {num_bg} background frames. Ping-pong cycle length: {cycle_len} frames (~{cycle_len/fps:.1f}s)", flush=True)

    # 5. Pre-Render Lyric Templates & Localized Drop Shadows
    print("[INIT] Pre-rendering sharp lyric typography & Gaussian drop shadows...", flush=True)
    font_lyric = ImageFont.truetype(font_lyric_path, 52)
    font_tag = ImageFont.truetype(font_tag_path, 24)
    y_center = 380 # Rock-solid immutable vertical center
    
    brand_tag = "GEHRA HUA  •  ARIJIT SINGH"
    
    # Pre-render brand watermark template
    tag_shadow = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    d_ts = ImageDraw.Draw(tag_shadow)
    d_ts.text((width // 2, 667), brand_tag, font=font_tag, fill=(2, 4, 10, 200), anchor="mm")
    tag_shadow_blur = tag_shadow.filter(ImageFilter.GaussianBlur(radius=5))
    tag_shadow_arr = np.array(tag_shadow_blur, dtype=np.float32)
    
    tag_text = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    d_tt = ImageDraw.Draw(tag_text)
    d_tt.text((width // 2, 665), brand_tag, font=font_tag, fill=(255, 255, 255, 210), anchor="mm")
    tag_text_arr = np.array(tag_text, dtype=np.float32)

    # Pre-render each lyric line's text and shadow arrays
    pre_rendered_lyrics = []
    for item in lyrics_schedule:
        text = item["text"]
        
        # Shadow image
        sh_img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        d_sh = ImageDraw.Draw(sh_img)
        d_sh.text((width // 2, y_center + 2), text, font=font_lyric, fill=(2, 4, 10, 240), anchor="mm")
        sh_blur = sh_img.filter(ImageFilter.GaussianBlur(radius=5))
        sh_arr = np.array(sh_blur, dtype=np.float32)
        
        # Text image
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
    print(f"[OK] Pre-rendered {len(pre_rendered_lyrics)} lyric typography masks", flush=True)

    # 6. Launch FFmpeg Streaming Process (stdin rawvideo -> libx264 fast)
    print(f"[FFMPEG] Launching FFmpeg encoder: {final_output}", flush=True)
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

    # Tag arrays for alpha blending
    ts_rgb = tag_shadow_arr[:, :, :3]
    ts_a = tag_shadow_arr[:, :, 3] / 255.0
    tt_rgb = tag_text_arr[:, :, :3]
    tt_a = tag_text_arr[:, :, 3] / 255.0

    print("[RENDER] Rendering video stream...", flush=True)
    last_print = time.time()
    
    fade_duration = 0.45 # Smooth Hermite transition duration
    
    for f in range(total_frames):
        t = f / fps
        
        # 1. Seamless Ping-Pong Index
        c_idx = f % cycle_len
        bg_idx = c_idx if c_idx < num_bg else (cycle_len - c_idx)
        frame_rgb = bg_frames[bg_idx].astype(np.float32)
        
        # 2. Composite Stationary Bottom Tag (permanent subtle luxury watermark)
        # Apply shadow
        frame_rgb = frame_rgb * (1.0 - ts_a[:, :, None]) + ts_rgb * ts_a[:, :, None]
        # Apply text
        frame_rgb = frame_rgb * (1.0 - tt_a[:, :, None]) + tt_rgb * tt_a[:, :, None]
        
        # 3. Determine Active Lyric & Hermite Fade
        for item in pre_rendered_lyrics:
            st = item["start"]
            en = item["end"]
            
            if st <= t <= en:
                # Calculate fade multiplier
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
                
        # Send raw frame bytes to FFmpeg stdin
        proc.stdin.write(np.clip(frame_rgb, 0, 255).astype(np.uint8).tobytes())
        
        if time.time() - last_print >= 5.0 or f == total_frames - 1:
            fps_speed = (f + 1) / max(0.001, time.time() - start_time)
            pct = ((f + 1) / total_frames) * 100.0
            print(f"[CLOUD RENDER] {pct:5.1f}% | Frame {f+1}/{total_frames} | Speed: {fps_speed:.1f} fps", flush=True)
            last_print = time.time()

    proc.stdin.close()
    proc.wait()
    
    total_time = time.time() - start_time
    file_size_mb = os.path.getsize(final_output) / (1024 * 1024)
    print("=" * 70, flush=True)
    print(f"[SUCCESS] Gehra Hua Full Master Video rendered in {total_time:.1f}s ({total_frames/total_time:.1f} fps)!", flush=True)
    print(f"File Path: {final_output}", flush=True)
    print(f"File Size: {file_size_mb:.2f} MB", flush=True)
    print("=" * 70, flush=True)

if __name__ == "__main__":
    main()
