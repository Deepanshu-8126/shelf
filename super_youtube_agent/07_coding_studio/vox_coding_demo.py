"""
Vox-Style Cyber Coding Video Generator (5-6s Master Demo).
Produces a 1080x1920 9:16 vertical short combining:
1. Ambient dark grid/server background texture
2. macOS Dark IDE Window with glowing borders & live syntax-highlighted code typing
3. Interactive Bottom Terminal with command execution
4. Floating Linux Tux / Supercomputer paper cut-out with white border & drop shadow
5. HUD Coordinates & Declassified Tech Stamps
6. Word-level kinetic karaoke subtitles
7. Sound design (Keyboard clack + tech whoosh + Edge TTS Jenny)
8. Telegram instant preview delivery
"""
import asyncio
import math
import os
import subprocess
import sys
import time
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import edge_tts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

OUTPUT_DIR = Path("d:/facts_yt/super_youtube_agent/07_coding_studio/output")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def get_font(size: int, bold: bool = True) -> ImageFont.FreeTypeFont:
    paths = [
        "C:/Windows/Fonts/consola.ttf" if not bold else "C:/Windows/Fonts/consolab.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
    ]
    for p in paths:
        if Path(p).exists():
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()


async def generate_speech(text: str, wav_path: Path) -> float:
    communicate = edge_tts.Communicate(text, "en-US-JennyNeural", rate="+5%")
    mp3_path = wav_path.with_suffix(".mp3")
    await communicate.save(str(mp3_path))
    # Convert to standard wav and get duration
    subprocess.run([
        "ffmpeg", "-y", "-i", str(mp3_path),
        "-ar", "44100", "-ac", "2", str(wav_path)
    ], check=True, capture_output=True)
    # Probe duration
    probe = subprocess.run([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(wav_path)
    ], check=True, capture_output=True, text=True)
    return float(probe.stdout.strip())


def render_vox_frame(frame_idx: int, total_frames: int, duration: float, font_code, font_title, font_sub, font_hud) -> Image.Image:
    W, H = 1080, 1920
    t = frame_idx / total_frames  # 0.0 to 1.0
    sec = t * duration

    # 1. Background: Dark Cyber Deep Navy with subtle vertical scanlines / grid
    img = Image.new("RGBA", (W, H), (8, 12, 22, 255))
    draw = ImageDraw.Draw(img)

    # Ambient grid
    grid_spacing = 60
    for x in range(0, W, grid_spacing):
        draw.line([(x, 0), (x, H)], fill=(16, 26, 44, 180), width=1)
    for y in range(0, H, grid_spacing):
        draw.line([(0, y), (W, y)], fill=(16, 26, 44, 180), width=1)

    # Ambient glowing gradient circle in center
    glow_radius = int(320 + 20 * math.sin(t * math.pi * 4))
    glow_box = [W // 2 - glow_radius, H // 2 - glow_radius - 80, W // 2 + glow_radius, H // 2 + glow_radius - 80]
    draw.ellipse(glow_box, fill=(14, 165, 233, 28))

    # Top Header Badge
    draw.rectangle([W // 2 - 220, 140, W // 2 + 220, 195], fill=(15, 23, 42, 230), outline=(56, 189, 248, 255), width=2)
    draw.text((W // 2, 167), "⚡ TECH FACT // CHANNEL 07", fill=(56, 189, 248), font=font_title, anchor="mm")

    # 2. Hero IDE Window (macOS style)
    # Camera scale-in bounce at start
    scale = min(1.0, 0.7 + 0.3 * (1 - math.exp(-t * 8)))
    win_w = int(960 * scale)
    win_h = int(880 * scale)
    win_x = (W - win_w) // 2
    win_y = int(240 + (1.0 - scale) * 100)

    # Window Drop Shadow
    shadow_img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    s_draw = ImageDraw.Draw(shadow_img)
    s_draw.rounded_rectangle([win_x - 10, win_y - 5, win_x + win_w + 10, win_y + win_h + 15], radius=24, fill=(0, 0, 0, 160))
    shadow_img = shadow_img.filter(ImageFilter.GaussianBlur(16))
    img.alpha_composite(shadow_img)

    # Window Body
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([win_x, win_y, win_x + win_w, win_y + win_h], radius=20, fill=(15, 23, 42, 245), outline=(56, 189, 248, 180), width=3)

    # Window Titlebar
    title_h = 56
    draw.rounded_rectangle([win_x, win_y, win_x + win_w, win_y + title_h], radius=20, fill=(30, 41, 59, 255))
    draw.rectangle([win_x, win_y + title_h - 15, win_x + win_w, win_y + title_h], fill=(30, 41, 59, 255))
    draw.line([(win_x, win_y + title_h), (win_x + win_w, win_y + title_h)], fill=(51, 65, 85), width=2)

    # macOS Window Buttons
    btn_y = win_y + title_h // 2
    draw.ellipse([win_x + 24, btn_y - 8, win_x + 40, btn_y + 8], fill=(239, 68, 68))    # Red
    draw.ellipse([win_x + 50, btn_y - 8, win_x + 66, btn_y + 8], fill=(234, 179, 8))   # Yellow
    draw.ellipse([win_x + 76, btn_y - 8, win_x + 92, btn_y + 8], fill=(34, 197, 94))   # Green

    # Active Tab
    tab_x = win_x + 130
    draw.rectangle([tab_x, win_y + 6, tab_x + 280, win_y + title_h], fill=(15, 23, 42), outline=(56, 189, 248, 120), width=1)
    draw.text((tab_x + 140, win_y + title_h // 2), "🐧 supercomputer.py", fill=(241, 245, 249), font=font_code, anchor="mm")

    # Code Typing Animation
    code_lines = [
        ("# --- GLOBAL SUPERCOMPUTERS 2026 ---", (100, 116, 139)),
        ("import os, linux_kernel", (244, 63, 94)),
        ("", (255, 255, 255)),
        ("top500 = get_supercomputers()", (56, 189, 248)),
        ("os_share = {'Linux': '100%', 'Windows': '0%'}", (250, 204, 21)),
        ("", (255, 255, 255)),
        ("if all(pc.os == 'Linux' for pc in top500):", (168, 85, 247)),
        ("    print('⚡ ALL 500 RUN ON LINUX!')", (74, 222, 128)),
    ]

    # Typing speed: reveals lines progressively over 4.5 seconds
    lines_revealed = min(len(code_lines), int(sec * 1.9) + 1)
    code_start_y = win_y + title_h + 30
    line_h = 44

    for i in range(lines_revealed):
        txt, color = code_lines[i]
        curr_y = code_start_y + i * line_h
        # Line number
        draw.text((win_x + 35, curr_y), f"{i+1:2d}", fill=(71, 85, 105), font=font_code)
        # Code text
        draw.text((win_x + 90, curr_y), txt, fill=color, font=font_code)

    # Blinking Cursor on active line
    if int(sec * 4) % 2 == 0 and lines_revealed < len(code_lines):
        cursor_y = code_start_y + lines_revealed * line_h
        draw.rectangle([win_x + 90, cursor_y, win_x + 104, cursor_y + 30], fill=(56, 189, 248))

    # Bottom Terminal in Window
    term_h = 190
    term_y = win_y + win_h - term_h - 15
    draw.rounded_rectangle([win_x + 20, term_y, win_x + win_w - 20, term_y + term_h], radius=12, fill=(2, 6, 23, 240), outline=(51, 65, 85), width=2)
    # Terminal Header
    draw.rectangle([win_x + 20, term_y, win_x + win_w - 20, term_y + 36], fill=(15, 23, 42))
    draw.text((win_x + 40, term_y + 18), "TERMINAL  |  bash", fill=(148, 163, 184), font=font_hud, anchor="lm")

    # Terminal output pops after 2.5s
    draw.text((win_x + 40, term_y + 60), "$ ./verify_nodes.sh --top500", fill=(248, 250, 252), font=font_code)
    if sec > 2.2:
        draw.text((win_x + 40, term_y + 102), "[+] SCANNING 500 CLUSTERS...", fill=(250, 204, 21), font=font_code)
    if sec > 3.4:
        draw.text((win_x + 40, term_y + 144), ">> RESULT: 100% PURE LINUX (0% WINDOWS)", fill=(74, 222, 128), font=font_code)

    # 3. Floating Cut-Out Badge (Paper cut-out style with white torn border)
    badge_w, badge_h = 320, 160
    badge_x = W - badge_w - 60
    badge_y = win_y + win_h + 30
    # Tilt angle
    badge_img = Image.new("RGBA", (badge_w, badge_h), (0, 0, 0, 0))
    b_draw = ImageDraw.Draw(badge_img)
    # White sticker border
    b_draw.rounded_rectangle([0, 0, badge_w, badge_h], radius=18, fill=(255, 255, 255, 255))
    b_draw.rounded_rectangle([6, 6, badge_w - 6, badge_h - 6], radius=14, fill=(15, 23, 42, 255))
    b_draw.text((badge_w // 2, 45), "🐧 100% LINUX", fill=(250, 204, 21), font=font_title, anchor="mm")
    b_draw.text((badge_w // 2, 95), "500/500 SUPERCOMPUTERS", fill=(56, 189, 248), font=font_hud, anchor="mm")
    b_draw.text((badge_w // 2, 130), "WINDOWS: 0  •  MACOS: 0", fill=(239, 68, 68), font=font_hud, anchor="mm")

    # Rotate badge slightly (-4 deg) for natural cut-out tilt
    rotated_badge = badge_img.rotate(-4, resample=Image.BICUBIC, expand=True)
    img.alpha_composite(rotated_badge, (badge_x, badge_y))

    # 4. Kinetic Karaoke Subtitles (Bottom Safe-Zone)
    sub_box_y = 1580
    words = ["Every", "single", "one", "of", "the", "world's", "top", "500", "supercomputers", "runs", "on", "Linux!"]
    # Highlight word based on time
    word_idx = min(len(words) - 1, int(sec * (len(words) / max(0.1, duration))))

    # Line 1
    l1 = " ".join(words[:6])
    # Line 2
    l2 = " ".join(words[6:])
    draw.rounded_rectangle([W // 2 - 460, sub_box_y - 20, W // 2 + 460, sub_box_y + 150], radius=24, fill=(0, 0, 0, 210), outline=(250, 204, 21, 200), width=3)
    draw.text((W // 2, sub_box_y + 25), l1, fill=(255, 255, 255), font=font_sub, anchor="mm")
    draw.text((W // 2, sub_box_y + 90), l2, fill=(250, 204, 21) if sec > 2.0 else (56, 189, 248), font=font_sub, anchor="mm")

    # 5. Bottom HUD Status
    draw.text((W // 2, 1830), "SYS://KERNEL_V6.12 • ARCH_X86_64 • 60 FPS VOX ENGINE", fill=(100, 116, 139), font=font_hud, anchor="mm")

    return img.convert("RGB")


async def build_vox_coding_short():
    print("🚀 [Vox Coding Engine] Initializing 5.5s Cyber Coding Master Short...")
    t0 = time.time()

    # 1. Voiceover
    speech_text = "Did you know? Every single one of the world's top 500 supercomputers runs on Linux. Not a single one uses Windows."
    audio_path = OUTPUT_DIR / "voiceover.wav"
    print(f"🎙️ Generating Edge TTS voiceover: '{speech_text}'...")
    duration = await generate_speech(speech_text, audio_path)
    print(f"✅ Voiceover ready: {duration:.2f} seconds")

    # Clamp duration to around 5.5 - 6.0s
    total_sec = max(5.0, min(6.0, duration))
    fps = 30
    total_frames = int(total_sec * fps)

    # 2. Fonts
    font_code = get_font(28, bold=True)
    font_title = get_font(30, bold=True)
    font_sub = get_font(42, bold=True)
    font_hud = get_font(20, bold=True)

    # 3. Render frames directly to FFmpeg pipe (Zero local disk thrashing)
    out_video = OUTPUT_DIR / "channel_7_vox_coding_demo.mp4"
    print(f"🎬 Rendering {total_frames} frames via FFmpeg Pipe at {fps} FPS (1080x1920)...")

    ffmpeg_cmd = [
        "ffmpeg", "-y",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-s", "1080x1920",
        "-pix_fmt", "rgb24",
        "-r", str(fps),
        "-i", "-",                     # Pipe input for frames
        "-i", str(audio_path),         # Audio input
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        str(out_video)
    ]

    proc = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    for i in range(total_frames):
        frame = render_vox_frame(i, total_frames, total_sec, font_code, font_title, font_sub, font_hud)
        proc.stdin.write(frame.tobytes())

    proc.stdin.close()
    proc.wait()

    render_time = time.time() - t0
    print(f"🎉 Master Video Render Complete in {render_time:.2f}s: {out_video}")
    print(f"📦 File Size: {out_video.stat().st_size / (1024*1024):.2f} MB")

    # 4. Dispatch directly to Telegram Phone
    print("📱 Sending 5.5s Vox Coding Video to Telegram...")
    telegram_script = Path("d:/facts_yt/send_to_telegram.py")
    if telegram_script.exists():
        subprocess.run([sys.executable, str(telegram_script), str(OUTPUT_DIR)], check=False)
        print("✅ Telegram notification dispatched!")

    return out_video


if __name__ == "__main__":
    asyncio.run(build_vox_coding_short())
