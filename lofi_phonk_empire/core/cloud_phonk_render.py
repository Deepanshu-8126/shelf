"""
Production Cloud Gym Phonk Master Renderer (High-Speed Turbo Loop)
--------------------------------------------------------------------
- Full HD 1080p (1920x1080 @ 24fps) pristine master render.
- Seamless animated loop of gym warrior with crackling yellow electric lightning.
- Real-time FFT audio-reactive golden lightning frequency visualizer.
- Dynamic chapter title synchronization from spiderx_chapters.json.
- Zero-memory leak direct rawvideo streaming via dual FFmpeg pipes.
"""

import os
import sys
import time
import json
import argparse
import subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.io import wavfile

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

def find_font(bold=False, size=30):
    candidates = []
    if bold:
        candidates = [
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
            "C:\\Windows\\Fonts\\arialbd.ttf",
            "arialbd.ttf"
        ]
    else:
        candidates = [
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
            "C:\\Windows\\Fonts\\arial.ttf",
            "arial.ttf"
        ]
    for c in candidates:
        if os.path.exists(c):
            try:
                return ImageFont.truetype(c, size)
            except Exception:
                pass
    try:
        return ImageFont.truetype("arial.ttf", size)
    except Exception:
        return ImageFont.load_default()

def load_chapters(chapters_path):
    if os.path.exists(chapters_path):
        try:
            with open(chapters_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('chapters', [])
        except Exception:
            pass
    return []

def get_active_track_info(current_sec, chapters):
    if not chapters:
        return "TRACK 01", "MONTAGEM PEGADORA (SLOWED)"
    for i, ch in enumerate(chapters):
        st = ch.get('start_time', 0)
        et = ch.get('end_time', 999999)
        if st <= current_sec < et:
            title = ch.get('title', '').strip().upper()
            return f"TRACK {i+1:02d}", title
    last = chapters[-1]
    return f"TRACK {len(chapters):02d}", last.get('title', '').strip().upper()

def render_gym_phonk(duration_sec=1200):
    W, H = 1920, 1080
    FPS = 24

    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    video_bg = os.path.join(root_dir, "assets", "gym_warrior_loop.mp4")
    audio_file = os.path.join(root_dir, "audio_35m.webm")
    chapters_json = os.path.join(root_dir, "spiderx_chapters.json")
    out_dir = os.path.join(root_dir, "output")
    os.makedirs(out_dir, exist_ok=True)
    out_mp4 = os.path.join(out_dir, "AURA_VIRAL_PHONK_2026_MASTER.mp4")
    temp_wav = os.path.join(out_dir, "temp_phonk_audio.wav")

    print("=" * 70, flush=True)
    print("STARTING 1080P MASTER GYM PHONK VIDEO RENDER", flush=True)
    print(f"Background: {video_bg}", flush=True)
    print(f"Audio Source: {audio_file}", flush=True)
    print(f"Target Duration: {duration_sec:.1f}s ({duration_sec/60:.2f} mins)", flush=True)
    print("=" * 70, flush=True)

    if not os.path.exists(video_bg):
        raise FileNotFoundError(f"Template video missing: {video_bg}")
    if not os.path.exists(audio_file):
        raise FileNotFoundError(f"Audio file missing: {audio_file}")

    # 1. Extract temporary audio WAV for real-time FFT bass analysis
    if not os.path.exists(temp_wav) or os.path.getsize(temp_wav) < 1000000:
        print("[1/4] Extracting audio PCM WAV for audio-reactive analysis...", flush=True)
        cmd_wav = [
            "ffmpeg", "-y",
            "-i", audio_file,
            "-ss", "0",
            "-t", str(duration_sec),
            "-vn", "-ar", "44100", "-ac", "1",
            temp_wav
        ]
        subprocess.run(cmd_wav, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    sr, audio_mono = wavfile.read(temp_wav)
    audio_mono = audio_mono.astype(np.float32)
    max_amp = np.max(np.abs(audio_mono)) + 1e-6
    audio_mono /= max_amp

    total_frames = int(FPS * duration_sec)
    samples_per_frame = int(sr / FPS)
    chapters = load_chapters(chapters_json)

    print(f"[2/4] Audio analysis ready. Total Frames: {total_frames} @ {FPS} FPS", flush=True)

    # 2. Setup FFmpeg input pipe (loops video_bg continuously and scales to 1920x1080)
    in_cmd = [
        "ffmpeg",
        "-stream_loop", "-1",
        "-i", video_bg,
        "-f", "rawvideo",
        "-pix_fmt", "rgb24",
        "-s", f"{W}x{H}",
        "-r", str(FPS),
        "-v", "error",
        "-"
    ]
    in_proc = subprocess.Popen(in_cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)

    # 3. Setup FFmpeg output pipe (encodes high quality 1080p CRF 18 with 320k audio)
    out_cmd = [
        "ffmpeg", "-y",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-s", f"{W}x{H}",
        "-pix_fmt", "rgb24",
        "-r", str(FPS),
        "-i", "-",
        "-ss", "0",
        "-t", str(duration_sec),
        "-i", audio_file,
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "320k",
        "-shortest",
        out_mp4
    ]
    out_proc = subprocess.Popen(out_cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    font_main = find_font(bold=True, size=38)
    font_sub = find_font(bold=False, size=22)

    frame_bytes = W * H * 3
    start_time = time.time()
    last_print = start_time

    # Golden lightning visualizer constants
    num_bars = 52
    bar_w = 6
    gap = 6
    total_vis_w = num_bars * (bar_w + gap)
    start_x = (W - total_vis_w) // 2
    bar_base_y = H - 60

    print("[3/4] Streaming frames through dual FFmpeg render pipes...", flush=True)

    for f_idx in range(total_frames):
        raw = in_proc.stdout.read(frame_bytes)
        if not raw or len(raw) < frame_bytes:
            break

        cur_sec = f_idx / FPS
        idx_start = f_idx * samples_per_frame
        idx_end = min(len(audio_mono), idx_start + samples_per_frame * 2)
        chunk = audio_mono[idx_start:idx_end]

        rms = float(np.sqrt(np.mean(chunk**2))) if len(chunk) > 0 else 0.0
        bass_boost = min(2.2, 0.7 + rms * 3.2)

        # 808 Bass Micro-Shake
        shake_x = int(np.random.uniform(-2.5, 2.5) * (rms**1.6))
        shake_y = int(np.random.uniform(-2.5, 2.5) * (rms**1.6))

        img = Image.frombytes("RGB", (W, H), raw)
        draw = ImageDraw.Draw(img)

        # Header Badge
        track_num, track_title = get_active_track_info(cur_sec, chapters)
        badge_x = 65 + shake_x
        badge_y = 55 + shake_y

        draw.text((badge_x, badge_y), "// AURA PHONK 2026", font=font_main, fill=(255, 225, 60))
        draw.text((badge_x, badge_y + 46), f"{track_num}  •  {track_title}", font=font_sub, fill=(240, 240, 240))

        # Audio FFT Spectrum Calculation
        if len(chunk) >= 128:
            fft_vals = np.abs(np.fft.rfft(chunk, n=128))[:num_bars]
            fft_max = np.max(fft_vals) + 1e-6
            fft_norm = fft_vals / fft_max
        else:
            fft_norm = np.zeros(num_bars)

        # Draw Golden Lightning Audio Visualizer
        for b in range(num_bars):
            energy = fft_norm[b] * 0.75 + rms * 0.5
            bar_h = max(3, int(52 * energy * bass_boost))
            bx = start_x + b * (bar_w + gap) + shake_x
            by = bar_base_y + shake_y

            # Outer golden glow
            draw.line([(bx, by - bar_h), (bx, by + bar_h)], fill=(255, 215, 0), width=bar_w)
            # Inner white lightning core
            core_h = max(2, int(bar_h * 0.45))
            draw.line([(bx, by - core_h), (bx, by + core_h)], fill=(255, 255, 240), width=bar_w - 2)

        out_proc.stdin.write(img.tobytes())

        now = time.time()
        if now - last_print >= 5.0 or f_idx == total_frames - 1:
            elapsed = now - start_time
            fps_cur = (f_idx + 1) / (elapsed + 1e-6)
            eta_m = ((total_frames - (f_idx + 1)) / (fps_cur + 1e-6)) / 60
            pct = ((f_idx + 1) / total_frames) * 100.0
            print(f"[RENDER] {pct:5.1f}% | Frame {f_idx+1}/{total_frames} | Speed: {fps_cur:.1f} fps | ETA: {eta_m:.1f}m | {track_num}: {track_title[:24]}", flush=True)
            last_print = now

    in_proc.stdout.close()
    in_proc.kill()
    out_proc.stdin.close()
    out_proc.wait()

    # Clean up temporary WAV
    if os.path.exists(temp_wav):
        try:
            os.remove(temp_wav)
        except Exception:
            pass

    out_mb = os.path.getsize(out_mp4) / (1024 * 1024)
    total_time_m = (time.time() - start_time) / 60
    print("\n" + "=" * 70, flush=True)
    print(f"[4/4] MASTER VIDEO COMPLETED: {out_mp4}", flush=True)
    print(f"Total Size: {out_mb:.2f} MB", flush=True)
    print(f"Render Time: {total_time_m:.2f} minutes", flush=True)
    print("=" * 70, flush=True)
    return out_mp4

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cloud Phonk Master Renderer")
    parser.add_argument("--duration", type=float, default=1200.0, help="Duration in seconds (default: 1200s / 20 mins)")
    parser.add_argument("--limit", type=float, default=None, help="Optional duration limit")
    args = parser.parse_args()

    dur = args.limit if args.limit is not None else args.duration
    try:
        render_gym_phonk(duration_sec=dur)
    except Exception as e:
        import traceback
        err = traceback.format_exc()
        print(f"[FATAL] {e}\n{err}", flush=True)
        with open("render_error.log", "w", encoding="utf-8") as f:
            f.write(err)
        sys.exit(1)
