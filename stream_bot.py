"""
stream_bot.py - 24/7 YouTube Live Streaming Controller Telegram Bot
Cross-Platform: Runs on Windows local machine or 24/7 Cloud Docker (Render / Hugging Face).
Features: Multi-stream support (Bollywood Lo-Fi + Late Night Coder simultaneously), Auto-start on boot, Auto-reconnect watchdog, HTTP Health API.
"""

import os
import sys
import time
import json
import requests
import threading
from urllib.parse import urlparse, parse_qs
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
        "key": "8yru-fhqt-2xku-pwjw-bwru",
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

active_procs = {
    "bollywood": None,
    "coding": None
}
start_times = {
    "bollywood": None,
    "coding": None
}
seek_offsets = {
    "bollywood": 0.0,
    "coding": 0.0
}

SONGS = [
    {"id": 0, "name": "Tum Se Hi", "movie": "Jab We Met", "artist": "Mohit Chauhan", "seek": 0.0, "start": 0.0, "end": 50.2},
    {"id": 1, "name": "Agar Tum Saath Ho", "movie": "Tamasha", "artist": "Arijit Singh & Alka Yagnik", "seek": 50.2, "start": 50.2, "end": 93.4},
    {"id": 2, "name": "Pee Loon", "movie": "OUATIM", "artist": "Mohit Chauhan", "seek": 93.4, "start": 93.4, "end": 143.6},
    {"id": 3, "name": "Humsafar", "movie": "Badrinath Ki Dulhania", "artist": "Akhil Sachdeva", "seek": 143.6, "start": 143.6, "end": 187.8},
    {"id": 4, "name": "Kabira", "movie": "YJHD", "artist": "Tochi Raina & Rekha Bhardwaj", "seek": 187.8, "start": 187.8, "end": 237.8},
]
TOTAL_CYCLE_SEC = 237.8

def format_uptime(st):
    if not st:
        return "Offline"
    total_sec = int(time.time() - st)
    hours = total_sec // 3600
    minutes = (total_sec % 3600) // 60
    seconds = total_sec % 60
    if hours > 0:
        return f"{hours}h {minutes:02d}m {seconds:02d}s"
    elif minutes > 0:
        return f"{minutes}m {seconds:02d}s"
    else:
        return f"{seconds}s"

def get_now_playing():
    if not active_procs["bollywood"] or active_procs["bollywood"].poll() is not None:
        return None, None
    st = start_times.get("bollywood")
    if not st:
        return None, None
    elapsed = (time.time() - st) + seek_offsets.get("bollywood", 0.0)
    cycle_pos = elapsed % TOTAL_CYCLE_SEC
    for idx, s in enumerate(SONGS):
        if s["start"] <= cycle_pos < s["end"]:
            next_idx = (idx + 1) % len(SONGS)
            return s, SONGS[next_idx]
    return SONGS[0], SONGS[1]

def send_message(chat_id, text, reply_markup=None):
    if not chat_id:
        return
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
                {"text": "🌧️ Start Bollywood", "callback_data": "start_bollywood"},
                {"text": "💻 Start Coder", "callback_data": "start_coding"}
            ],
            [
                {"text": "🛑 Stop Bollywood", "callback_data": "stop_bollywood"},
                {"text": "🛑 Stop Coder", "callback_data": "stop_coding"}
            ],
            [
                {"text": "🚀 Start BOTH", "callback_data": "start_both"},
                {"text": "🛑 Stop ALL", "callback_data": "stop_all"}
            ],
            [
                {"text": "📊 Live Status & Uptime", "callback_data": "check_status"},
                {"text": "🎛️ Song DJ Control", "callback_data": "song_info"}
            ]
        ]
    }

def get_songs_keyboard():
    return {
        "inline_keyboard": [
            [
                {"text": "▶️ 1. Tum Se Hi", "callback_data": "play_0"},
                {"text": "▶️ 2. Agar Tum Saath Ho", "callback_data": "play_1"}
            ],
            [
                {"text": "▶️ 3. Pee Loon", "callback_data": "play_2"},
                {"text": "▶️ 4. Humsafar", "callback_data": "play_3"}
            ],
            [
                {"text": "▶️ 5. Kabira (New!)", "callback_data": "play_4"}
            ],
            [
                {"text": "🔄 Refresh Playing Status", "callback_data": "song_info"},
                {"text": "🔙 Main Menu", "callback_data": "main_menu"}
            ]
        ]
    }

def send_song_info(chat_id):
    b_live = active_procs["bollywood"] is not None and active_procs["bollywood"].poll() is None
    lines = ["🎛️ *24/7 BOLLYWOOD LO-FI DJ & SONG CONTROLLER*\n"]
    
    if b_live:
        curr, nxt = get_now_playing()
        if curr:
            lines.append(f"🎧 *Currently Live Playing:*")
            lines.append(f"▶️ 🎵 *{curr['name']}* ({curr['movie']})")
            lines.append(f"🎤 {curr['artist']}")
            lines.append(f"⏭️ *Up Next:* {nxt['name']} ({nxt['movie']})\n")
    else:
        lines.append("⚠️ *Bollywood Stream abhi OFFLINE hai.*\n")

    lines.append("👇 *Kisi bhi gaane par click karo — stream turant usi gaane se live bajna shuru ho jayegi:*")
    send_message(chat_id, "\n".join(lines), get_songs_keyboard())

def start_stream(stream_type, chat_id=None, seek_sec=0):
    global active_procs, start_times, seek_offsets

    if seek_sec > 0:
        stop_stream(stream_type)
        time.sleep(0.5)
    elif active_procs[stream_type] and active_procs[stream_type].poll() is None:
        if chat_id:
            send_message(chat_id, f"⚠️ *{STREAMS[stream_type]['name']}* already live chal rahi hai!", get_menu_keyboard())
        return True

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

    seek_opt = f"-ss {seek_sec} " if seek_sec > 0 else ""
    cmd = (
        f'ffmpeg {seek_opt}-re -stream_loop -1 -i "{video_path}" {seek_opt}-re -stream_loop -1 -i "{audio_path}" '
        f'-map 0:v -map 1:a {v_opts} -c:a aac -b:a 128k -ar 44100 '
        f'-fflags +genpts -flvflags no_duration_filesize -f flv "rtmp://a.rtmp.youtube.com/live2/{cfg["key"]}"'
    )

    try:
        active_procs[stream_type] = sp.Popen(cmd, shell=True)
        if seek_sec > 0:
            seek_offsets[stream_type] = seek_sec
            start_times[stream_type] = time.time()
        else:
            seek_offsets[stream_type] = 0.0
            start_times[stream_type] = time.time()

        print(f"[{stream_type.upper()}] Stream started with PID {active_procs[stream_type].pid} (seek={seek_sec}s)")
        if chat_id:
            msg = (
                f"🚀 *LIVE STREAM STARTED!*\n\n"
                f"🎵 *Channel:* {cfg['name']}\n"
                f"🔑 *Key:* `{cfg['key']}`\n"
                f"⚡ *Host:* {'Windows Laptop' if sys.platform == 'win32' else '24/7 Cloud Server'}\n\n"
                f"YouTube Studio par stream live ho chuki hai! 🔴"
            )
            send_message(chat_id, msg, get_menu_keyboard())
        return True
    except Exception as e:
        print(f"Error starting {stream_type}: {e}")
        if chat_id:
            send_message(chat_id, f"❌ *Error starting {stream_type}:* {e}", get_menu_keyboard())
        return False

def start_both_streams(chat_id=None):
    res1 = start_stream("bollywood", chat_id)
    time.sleep(1)
    res2 = start_stream("coding", chat_id)
    if chat_id and (res1 or res2):
        send_message(chat_id, "🔥 *DONO STREAMS CLOUD PAR LIVE HO GAYI HAIN!* 🔴🔴\nYouTube Studio par dono check kar sakte ho.", get_menu_keyboard())

def stop_stream(stream_type, chat_id=None):
    global active_procs, start_times
    proc = active_procs.get(stream_type)
    if proc and proc.poll() is None:
        try:
            if sys.platform == "win32":
                sp.run(f"taskkill /F /T /PID {proc.pid}", shell=True, stdout=sp.DEVNULL, stderr=sp.DEVNULL)
            else:
                sp.run(f"kill -9 {proc.pid}", shell=True, stdout=sp.DEVNULL, stderr=sp.DEVNULL)
        except Exception:
            pass
        active_procs[stream_type] = None
        start_times[stream_type] = None
        if chat_id:
            send_message(chat_id, f"🛑 *{STREAMS[stream_type]['name']}* band kar di gayi hai.", get_menu_keyboard())
    else:
        active_procs[stream_type] = None
        start_times[stream_type] = None
        if chat_id:
            send_message(chat_id, f"ℹ️ *{stream_type}* already stopped thi.", get_menu_keyboard())

def stop_all_streams(chat_id=None):
    for st in ["bollywood", "coding"]:
        stop_stream(st)
    if sys.platform != "win32":
        sp.run("pkill -9 ffmpeg", shell=True, stdout=sp.DEVNULL, stderr=sp.DEVNULL)
    if chat_id:
        send_message(chat_id, "🛑 *ALL STREAMS STOPPED:*\nSari live streams band kar di gayi hain.", get_menu_keyboard())

def check_status(chat_id=None):
    global active_procs, start_times
    lines = ["📊 *24/7 CLOUD LIVE STREAM TELEMETRY:*\n"]

    # 1. Bollywood Lo-Fi
    b_live = active_procs["bollywood"] is not None and active_procs["bollywood"].poll() is None
    lines.append(f"🌧️ *Bollywood Lo-Fi:* {'🟢 LIVE' if b_live else '🔴 OFFLINE'}")
    if b_live:
        lines.append(f"⏱️ *Live Uptime:* `{format_uptime(start_times.get('bollywood'))}`")
        curr, nxt = get_now_playing()
        if curr:
            lines.append(f"🎧 *Playing Right Now:* 🎵 *{curr['name']}* ({curr['movie']})")
            lines.append(f"⏭️ *Up Next:* {nxt['name']} ({nxt['movie']})")
    lines.append("")

    # 2. Coding Lo-Fi
    c_live = active_procs["coding"] is not None and active_procs["coding"].poll() is None
    lines.append(f"💻 *Coder Desk Lo-Fi:* {'🟢 LIVE' if c_live else '🔴 OFFLINE'}")
    if c_live:
        lines.append(f"⏱️ *Live Uptime:* `{format_uptime(start_times.get('coding'))}`")
        lines.append("🎧 *Music:* Deep Focus Analog Rhodes & Lo-Fi Beats")
    lines.append("")

    lines.append(f"☁️ *Server:* Render Cloud (Singapore 24/7)")
    lines.append("🛡️ *Copyright:* 100% Claim-Free Stealth Approved")

    msg = "\n".join(lines)
    if chat_id:
        send_message(chat_id, msg, get_menu_keyboard())
    return msg

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)

        if parsed.path == "/start":
            st = params.get("stream", ["both"])[0]
            if st == "both":
                start_both_streams(ALLOWED_USER_ID)
            elif st in STREAMS:
                start_stream(st, ALLOWED_USER_ID)

        elif parsed.path == "/stop":
            stop_all_streams(ALLOWED_USER_ID)

        elif parsed.path == "/diag":
            import subprocess
            ps_out = subprocess.getoutput("ps aux")
            processes = [line for line in ps_out.splitlines() if "ffmpeg" in line or "python" in line]
            diag_info = {
                "status": "healthy",
                "active_processes": processes,
                "bollywood_pid": active_procs["bollywood"].pid if active_procs["bollywood"] else None,
                "bollywood_poll": active_procs["bollywood"].poll() if active_procs["bollywood"] else "None",
                "coding_pid": active_procs["coding"].pid if active_procs["coding"] else None,
                "coding_poll": active_procs["coding"].poll() if active_procs["coding"] else "None",
                "start_times": start_times
            }
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(diag_info, indent=2).encode("utf-8"))
            return

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()

        status_info = {
            "status": "healthy",
            "bot": "@Lofi_banda_bot",
            "bollywood_live": active_procs["bollywood"] is not None and active_procs["bollywood"].poll() is None,
            "coding_live": active_procs["coding"] is not None and active_procs["coding"].poll() is None,
        }
        self.wfile.write(json.dumps(status_info).encode("utf-8"))

    def log_message(self, format, *args):
        pass

def start_health_server():
    port = int(os.environ.get("PORT", 10000))
    print(f"Starting Health Server on port {port}...")
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    server.serve_forever()

def watchdog_loop():
    """Auto-restart streams if they drop unexpectedly and ping self to keep Render awake 24/7."""
    ping_counter = 0
    while True:
        time.sleep(30)
        ping_counter += 1
        
        # Self-ping Render public URL every 3 minutes (6 * 30s)
        # This sends an incoming HTTP request through Render edge router, preventing idle spin-down!
        if ping_counter >= 6:
            ping_counter = 0
            try:
                r = requests.get("https://lofi-live-stream-bot.onrender.com/", timeout=10)
                print(f"[KEEPALIVE] Render self-ping success (status {r.status_code})")
            except Exception as e:
                print(f"[KEEPALIVE] Render self-ping error: {e}")

        for st in ["bollywood", "coding"]:
            proc = active_procs[st]
            # If was started before and dropped, auto-recover
            if start_times[st] is not None and (proc is None or proc.poll() is not None):
                print(f"[WATCHDOG] Reconnecting {st} stream...")
                start_stream(st)

def main():
    offset = None
    
    # Auto-start both streams on cloud boot!
    print("Auto-starting both live streams on boot...")
    start_both_streams(ALLOWED_USER_ID)

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
                    elif data == "stop_bollywood":
                        stop_stream("bollywood", chat_id)
                    elif data == "stop_coding":
                        stop_stream("coding", chat_id)
                    elif data == "start_both":
                        start_both_streams(chat_id)
                    elif data == "stop_all":
                        stop_all_streams(chat_id)
                    elif data == "check_status":
                        check_status(chat_id)
                    elif data == "song_info":
                        send_song_info(chat_id)
                    elif data == "main_menu":
                        send_message(chat_id, "📱 *Main Admin Control Menu:*", get_menu_keyboard())
                    elif data.startswith("play_"):
                        s_idx = int(data.split("_")[1])
                        target_song = SONGS[s_idx]
                        start_stream("bollywood", chat_id, seek_sec=target_song["seek"])
                        send_message(
                            chat_id,
                            f"🔀 *DJ SONG SWITCH!* 🎧\n\n"
                            f"Live stream turant jump ho kar chalu ho gayi hai:\n"
                            f"▶️ 🎵 *{target_song['name']}* ({target_song['movie']})\n"
                            f"🎤 *Artist:* {target_song['artist']}\n"
                            f"🔴 *YouTube Live par ab yahi gaana live baj raha hai!*",
                            get_songs_keyboard()
                        )
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
                        stop_all_streams(chat_id)
                    elif text.startswith("/both") or text.startswith("/all"):
                        start_both_streams(chat_id)
                    elif text.startswith("/stream1") or text.startswith("/bollywood"):
                        start_stream("bollywood", chat_id)
                    elif text.startswith("/stream2") or text.startswith("/coding"):
                        start_stream("coding", chat_id)
                    elif text.startswith("/songs") or text.startswith("/playlist"):
                        send_song_info(chat_id)
                    else:
                        send_message(chat_id, "ℹ️ Command samajh nahi aayi. Neeche buttons use karo 👇", get_menu_keyboard())
                        
        except Exception as e:
            time.sleep(3)

if __name__ == "__main__":
    health_thread = threading.Thread(target=start_health_server, daemon=True)
    health_thread.start()
    
    watchdog_thread = threading.Thread(target=watchdog_loop, daemon=True)
    watchdog_thread.start()
    
    print("Health server & Watchdog started. Starting main bot loop...")
    main()
