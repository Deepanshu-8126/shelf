"""
Interactive Web Studio Dashboard for Vox Production Studio.
Provides a modern dark-mode control room for topic analysis, script inspection,
and 1-click cloud/local video generation.
"""
from __future__ import annotations

import json
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from typing import Any
import urllib.parse

from channel_5_vox_studio.channel_trainer import ChannelTrainer, CHANNEL_PROFILES
from channel_5_vox_studio.gemini_rag_scriptwriter import GeminiRAGScriptWriter
from channel_5_vox_studio.director import StudioDirector
from channel_5_vox_studio.config import OUTPUT_DIR

PORT = 8989


class StudioHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/" or parsed.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(self._render_dashboard().encode("utf-8"))
        elif parsed.path == "/api/preview_script":
            query = urllib.parse.parse_qs(parsed.query)
            topic = query.get("topic", ["Bermuda Triangle"])[0]
            niche = query.get("niche", ["dark_mystery"])[0]
            pkg = GeminiRAGScriptWriter.generate_script_package(topic, niche=niche)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(pkg).encode("utf-8"))
        elif parsed.path.startswith("/output/"):
            file_name = parsed.path.replace("/output/", "")
            file_path = OUTPUT_DIR / file_name
            if file_path.exists():
                self.send_response(200)
                mime = "video/mp4" if file_path.suffix == ".mp4" else "image/jpeg"
                self.send_header("Content-Type", mime)
                self.end_headers()
                self.wfile.write(file_path.read_bytes())
            else:
                self.send_error(404)
        else:
            super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/api/render":
            length = int(self.headers.get("content-length", 0))
            body = self.rfile.read(length).decode("utf-8")
            data = json.loads(body)
            topic = data.get("topic", "Bermuda Triangle")
            niche = data.get("niche", "dark_mystery")
            
            director = StudioDirector()
            master_mp4 = director.create_video(topic, niche=niche)
            
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "success",
                "video_url": f"/output/{master_mp4.name}",
                "topic": topic
            }).encode("utf-8"))

    def _render_dashboard(self) -> str:
        return """<!doctype html>
<html>
<head>
  <meta charset="UTF-8">
  <title>Vox Production Studio | Control Room</title>
  <link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@600;700;900&family=JetBrains+Mono:wght@500;700&display=block" rel="stylesheet">
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { background: #07090e; color: #ffffff; font-family: 'Space Grotesk', sans-serif; padding: 40px; }
    .header { display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid rgba(255,255,255,0.1); padding-bottom: 24px; margin-bottom: 36px; }
    .logo { font-size: 32px; font-weight: 900; letter-spacing: -0.02em; }
    .logo span { color: #ff3b30; }
    .badge { font-family: 'JetBrains Mono'; background: rgba(255,59,48,0.2); border: 1px solid #ff3b30; color: #ff3b30; padding: 6px 16px; border-radius: 4px; font-size: 14px; }
    .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 32px; }
    .card { background: #0e121a; border: 1px solid rgba(255,255,255,0.12); border-radius: 12px; padding: 28px; }
    .card h2 { font-size: 22px; margin-bottom: 20px; color: #ffd60a; font-family: 'JetBrains Mono'; }
    input, select, textarea { width: 100%; background: #06080c; border: 1px solid rgba(255,255,255,0.2); color: #fff; padding: 14px 18px; border-radius: 8px; font-size: 16px; font-family: inherit; margin-bottom: 16px; }
    button { background: #ff3b30; color: #fff; border: none; padding: 16px 28px; border-radius: 8px; font-weight: 800; font-size: 16px; cursor: pointer; transition: all 0.2s; }
    button:hover { background: #ff5247; transform: translateY(-2px); }
    .beat-card { background: #080a0f; border-left: 4px solid #00f0ff; padding: 16px 20px; margin-bottom: 12px; border-radius: 4px; }
    .beat-title { font-family: 'JetBrains Mono'; font-size: 13px; color: #00f0ff; margin-bottom: 6px; }
    .beat-text { font-size: 15px; color: #e0e0e0; line-height: 1.4; }
  </style>
</head>
<body>
  <div class="header">
    <div class="logo">VOX <span>STUDIO</span> AI</div>
    <div class="badge">5-AGENT PRODUCTION MATRIX ACTIVE</div>
  </div>

  <div class="grid">
    <div class="card">
      <h2>1. TOPIC & CHANNEL PERSONA</h2>
      <label style="display:block; margin-bottom: 8px; color: #888;">Channel Niche:</label>
      <select id="nicheSelect">
        <option value="dark_mystery">🕵️ Dark Case Files (Unsolved Mysteries & Crime)</option>
        <option value="space_science">🌌 Cosmic Curiosities (Black Holes & Relativity)</option>
        <option value="dark_web">💻 Deep Web Archive (Cyphers & Lost Tech)</option>
        <option value="bizarre_history">📜 Forbidden History (Ancient Maps & Anomalies)</option>
      </select>

      <label style="display:block; margin-bottom: 8px; color: #888;">Documentary Topic:</label>
      <input type="text" id="topicInput" value="The Bermuda Triangle Mystery">

      <button onclick="previewScript()">⚡ ANALYZE STORY BEATS (RAG)</button>
      <button style="background: #00f0ff; color: #000; margin-left: 12px;" onclick="renderVideo()">🎬 1-CLICK RENDER</button>
      <div id="renderStatus" style="margin-top: 16px; color: #ffd60a; font-family: 'JetBrains Mono';"></div>
    </div>

    <div class="card">
      <h2>2. PSYCHOLOGICAL BEAT BREAKDOWN</h2>
      <div id="beatsContainer">
        <div class="beat-card">
          <div class="beat-title">BEAT 1: THE SHOCK HOOK (0.0s - 4.5s)</div>
          <div class="beat-text" id="b1">In 1945... five US Navy bombers took off into clear blue skies over Florida...</div>
        </div>
        <div class="beat-card" style="border-color: #ffd60a;">
          <div class="beat-title" style="color: #ffd60a;">BEAT 2: FORENSIC PROOF (4.5s - 8.5s)</div>
          <div class="beat-text" id="b2">Leader's final transmission: 'Everything is wrong... even the ocean doesn't look right.'</div>
        </div>
        <div class="beat-card" style="border-color: #ff3b30;">
          <div class="beat-title" style="color: #ff3b30;">BEAT 3: REAL VIDEO CUTOUT (8.5s - 12.0s)</div>
          <div class="beat-text" id="b3">Minutes later, they vanished. Then the rescue plane disappeared too.</div>
        </div>
        <div class="beat-card" style="border-color: #39ff14;">
          <div class="beat-title" style="color: #39ff14;">BEAT 4: THE CLIFFHANGER (12.0s - 15.0s)</div>
          <div class="beat-text" id="b4">80 years later... zero wreckage has ever been found.</div>
        </div>
      </div>
    </div>
  </div>

  <script>
    async function previewScript() {
      const topic = document.getElementById("topicInput").value;
      const niche = document.getElementById("nicheSelect").value;
      document.getElementById("renderStatus").innerText = "Analyzing story intelligence...";
      const res = await fetch(`/api/preview_script?topic=${encodeURIComponent(topic)}&niche=${niche}`);
      const data = await res.json();
      document.getElementById("renderStatus").innerText = "Script beats analyzed successfully!";
      if (data.subtitles && data.subtitles.length >= 4) {
        document.getElementById("b1").innerText = data.subtitles[0];
        document.getElementById("b2").innerText = data.subtitles[1];
        document.getElementById("b3").innerText = data.subtitles[2];
        document.getElementById("b4").innerText = data.subtitles[3];
      }
    }

    async function renderVideo() {
      const topic = document.getElementById("topicInput").value;
      const niche = document.getElementById("nicheSelect").value;
      document.getElementById("renderStatus").innerText = "⏳ Rendering 1080x1920 60fps Master Video (Please wait ~60s)...";
      const res = await fetch("/api/render", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ topic, niche })
      });
      const data = await res.json();
      document.getElementById("renderStatus").innerHTML = `🎉 Video Rendered! <a href="${data.video_url}" target="_blank" style="color:#00f0ff;">Download MP4</a>`;
    }
  </script>
</body>
</html>
"""


def start_studio_server():
    server = HTTPServer(("0.0.0.0", PORT), StudioHandler)
    print(f"🎬 [VoxStudio Web Control Room] Running live at http://localhost:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    start_studio_server()
