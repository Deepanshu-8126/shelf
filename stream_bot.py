"""
stream_bot.py - 24/7 YouTube Live Streaming Controller Telegram Bot
Cross-Platform: Runs on Windows local machine or 24/7 Cloud Docker (Hugging Face / Render).
"""

import os
import sys
import time
import json
import requests
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import subprocess as sp
from pathlib import Path

BOT_TOKEN = "8385121620:AAFcUYUR5qP5W3q7EOLNN5kBiSFpdPuYFqs"
ALLOWED_USER_ID = 6486771356
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

BASE_DIR = Path(__file__).resolve().parent

# Universal Video Codec for Windows QSV or Linux Cloud
if sys.platform == "win32":
    V_CODEC = "-c:v h264_qsv -low_power 1 -preset veryfast"
else:
    # Zero-CPU video passthrough for cloud containers
    V_CODEC = "-c:v copy"

STREAMS = {
    "bollywood": {
        "name": "24/7 Bollywood Lo-Fi Radio (Rainy Cat)",
        "video": BASE_DIR / "clean_rainy_cat_lofi_1080p30.mp4",
        "audio": BASE_DIR / "BOLLYWOOD_LOFI_MASHUP_30MIN_LOOP.mp3",
        "key": "eexq-82kw-v9ky-upgj-8e32",
        "bitrate": "2200k"
    },
    "coding": {
        "name": "3:00 AM Late Night Coder Lo-Fi (Coder Desk)",
        "video": BASE_DIR / "stream_visual_3am.mp4",
        "audio": BASE_DIR / "coding_lofi_master_audio.mp3",
        "key": "uv4p-6jbs-kmj3-jtuy-ce6e",
        "bitrate": "2000k"
    }
}

active_proc = None
active_stream_type = None
start_time = None

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        uptime_sec = int(time.time() - start_time) if start_time else 0
        resp = {
            "status": "healthy",
            "bot": "@Lofi_banda_bot",
            "active_stream": active_stream_type,
            "running": active_proc is not None and active_proc.poll() is None,
            "uptime_seconds": uptime_sec
        }
        self.wfile.write(json.dumps(resp).encode("utf-8"))

    def log_message(self, format, *args):
        pass

def start_health_server():
    port = int(os.environ.get("PORT", 10000))
    print(f"Starting Health Server on port {port}...")
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    server.serve_forever()


def send_message(chat_id, text, reply_markup=None):
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    try:
        requests.post(f"{API_URL}/sendMessage", json=payload, timeout=10)
    except Exception as e:
        print(f"Error sending message: {e}")

def get_menu_keyboard():
    return {
        "inline_keyboard": [
            [
                {"text": "🌧️ Start Bollywood Lo-Fi", "callback_data": "start_bollywood"},
                {"text": "💻 Start Late Night Coder", "callback_data": "start_coding"}
            ],
            [
                {"text": "📊 Check Status / Health", "callback_data": "check_status"},
                {"text": "🛑 Stop Stream", "callback_data": "stop_stream"}
            ]
        ]
    }

def start_stream(stream_type, chat_id):
    global active_proc, active_stream_type, start_time
    if active_proc and active_proc.poll() is None:
        send_message(chat_id, f"⚠️ *Warning:* A stream is already running (*{STREAMS[active_stream_type]['name']}*).\nPehele /stop karo fir naya start karna.", get_menu_keyboard())
        return

    cfg = STREAMS[stream_type]
    video_path = cfg["video"]
    audio_path = cfg["audio"]

    # Fallback to local paths if in local dev
    if not video_path.exists():
        if stream_type == "bollywood":
            video_path = Path(r"d:\facts_yt\lofi_phonk_empire\indian_aspirant_lofi\clean_rainy_cat_lofi_1080p30.mp4")
            audio_path = Path(r"d:\facts_yt\lofi_phonk_empire\indian-lofi-converter\output\BOLLYWOOD_LOFI_MASHUP_30MIN_LOOP.mp3")
        else:
            video_path = Path(r"d:\facts_yt\lofi_phonk_empire\ytstream\stream_visual_3am.mp4")
            audio_path = Path(r"d:\facts_yt\lofi_phonk_empire\ytstream\coding_lofi_master_audio.mp3")

    if sys.platform == "win32":
        v_opts = f"{V_CODEC} -b:v {cfg['bitrate']} -maxrate 2600k -bufsize 5000k -r 30 -g 60 -keyint_min 60"
    else:
        v_opts = "-c:v copy"

    cmd = (
        f'ffmpeg -re -stream_loop -1 -i "{video_path}" -re -stream_loop -1 -i "{audio_path}" '
        f'-map 0:v -map 1:a {v_opts} -c:a aac -b:a 128k -ar 44100 '
        f'-fflags +genpts -flvflags no_duration_filesize -f flv "rtmp://a.rtmp.youtube.com/live2/{cfg["key"]}"'
    )

    
    try:
        active_proc = sp.Popen(cmd, shell=True)
        active_stream_type = stream_type
        start_time = time.time()
        msg = (
            f"🚀 *LIVE STREAM STARTED!*\n\n"
            f"🎵 *Channel:* {cfg['name']}\n"
            f"🔑 *Key:* `{cfg['key']}`\n"
            f"⚡ *Host:* {'Windows Laptop' if sys.platform == 'win32' else '24/7 Cloud Server'}\n\n"
            f"YouTube Studio par stream live ho chuki hai! 🔴"
        )
        send_message(chat_id, msg, get_menu_keyboard())
    except Exception as e:
        send_message(chat_id, f"❌ *Error starting stream:* {e}", get_menu_keyboard())

def stop_stream(chat_id):
    global active_proc, active_stream_type, start_time
    if active_proc and active_proc.poll() is None:
        try:
            if sys.platform == "win32":
                sp.run(f"taskkill /F /T /PID {active_proc.pid}", shell=True, stdout=sp.DEVNULL, stderr=sp.DEVNULL)
                sp.run("taskkill /F /IM ffmpeg.exe", shell=True, stdout=sp.DEVNULL, stderr=sp.DEVNULL)
            else:
                sp.run(f"kill -9 {active_proc.pid}", shell=True, stdout=sp.DEVNULL, stderr=sp.DEVNULL)
                sp.run("pkill -9 ffmpeg", shell=True, stdout=sp.DEVNULL, stderr=sp.DEVNULL)

            name = STREAMS[active_stream_type]['name']
            active_proc = None
            active_stream_type = None
            start_time = None
            send_message(chat_id, f"🛑 *Stream Stopped:*\n*{name}* ko band kar diya gaya hai.", get_menu_keyboard())
        except Exception as e:
            send_message(chat_id, f"❌ Error stopping: {e}", get_menu_keyboard())
    else:
        active_proc = None
        send_message(chat_id, "ℹ️ Abhi koi stream active nahi hai.", get_menu_keyboard())

def check_status(chat_id):
    global active_proc, active_stream_type, start_time
    if active_proc and active_proc.poll() is None:
        elapsed = int(time.time() - start_time)
        hrs = elapsed // 3600
        mins = (elapsed % 3600) // 60
        secs = elapsed % 60
        uptime = f"{hrs:02d}h {mins:02d}m {secs:02d}s"
        cfg = STREAMS[active_stream_type]
        msg = (
            f"🟢 *STREAM STATUS: LIVE & ACTIVE*\n\n"
            f"📺 *Stream:* {cfg['name']}\n"
            f"⏱️ *Uptime:* {uptime}\n"
            f"⚙️ *Bitrate:* {cfg['bitrate']} @ 30 FPS\n"
            f"☁️ *Host:* {'Windows Laptop' if sys.platform == 'win32' else '24/7 Cloud Server'}\n"
            f"🛡️ *Copyright:* 100% Stealth Approved"
        )
    else:
        msg = "⚪ *STREAM STATUS: OFFLINE*\n\nAbhi koi live stream nahi chal rahi hai.\nNeeche button se chalu kar sakte ho."
    send_message(chat_id, msg, get_menu_keyboard())

def main():
    offset = None
    while True:
        try:
            params = {"timeout": 20}
            if offset:
                params["offset"] = offset
            r = requests.get(f"{API_URL}/getUpdates", params=params, timeout=25).json()
            
            if not r.get("ok"):
                time.sleep(2)
                continue
                
            for u in r.get("result", []):
                offset = u["update_id"] + 1
                
                # Handle Inline Button Clicks
                if "callback_query" in u:
                    cq = u["callback_query"]
                    sender_id = cq["from"]["id"]
                    chat_id = cq["message"]["chat"]["id"]
                    data = cq.get("data")
                    
                    if sender_id != ALLOWED_USER_ID:
                        send_message(chat_id, "⛔ Unauthorized user.")
                        continue
                        
                    if data == "start_bollywood":
                        start_stream("bollywood", chat_id)
                    elif data == "start_coding":
                        start_stream("coding", chat_id)
                    elif data == "stop_stream":
                        stop_stream(chat_id)
                    elif data == "check_status":
                        check_status(chat_id)
                    continue

                # Handle Text Messages
                if "message" in u:
                    m = u["message"]
                    sender_id = m["from"]["id"]
                    chat_id = m["chat"]["id"]
                    text = m.get("text", "").strip()
                    
                    if sender_id != ALLOWED_USER_ID:
                        send_message(chat_id, "⛔ Unauthorized. Only Deepanshu can control this bot.")
                        continue
                        
                    if text.startswith("/start"):
                        welcome_msg = (
                            f"👋 *Welcome Deepanshu!* 🎧\n\n"
                            f"Yeh tumhara personal *YouTube 24/7 Live Stream Controller Bot* hai.\n"
                            f"Neeche diye gaye buttons se kisi bhi stream ko direct phone se LIVE chalu ya band kar sakte ho:"
                        )
                        send_message(chat_id, welcome_msg, get_menu_keyboard())
                    elif text.startswith("/status"):
                        check_status(chat_id)
                    elif text.startswith("/stop"):
                        stop_stream(chat_id)
                    elif text.startswith("/stream1") or text.startswith("/bollywood"):
                        start_stream("bollywood", chat_id)
                    elif text.startswith("/stream2") or text.startswith("/coding"):
                        start_stream("coding", chat_id)
                    else:
                        send_message(chat_id, "ℹ️ Command samajh nahi aayi. Neeche buttons use karo 👇", get_menu_keyboard())
                        
        except Exception as e:
            time.sleep(3)

if __name__ == "__main__":
    health_thread = threading.Thread(target=start_health_server, daemon=True)
    health_thread.start()
    print("Health server thread started. Starting Telegram polling loop...")
    main()

