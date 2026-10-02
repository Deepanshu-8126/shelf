# 🎬 Vox Autonomous Video Production Studio

A production-grade, 5-Agent automated video production system engineered to rival Vox and Johnny Harris documentary shorts.

---

## ⚡ Key Highlights

1. **🎙️ Cinematic Human Voice:** Uses ElevenLabs **`Brian`** with `eleven_multilingual_v2` (calibrated stability `0.32` & style `0.45` for natural human breathing, suspense pauses, and broadcast 80Hz/3.5kHz mastering).
2. **📜 Real Historical & Archival Crawling:** Zero synthetic placeholder shapes. Extracts authentic 1945 navigation charts, declassified logbooks, and archival photographs via Wikimedia Commons and DuckDuckGo.
3. **🎥 HD Video Clip B-Roll Extractor:** Live searches and streams 1080p open atmospheric video footage (ocean waves, dark clouds, cockpits) and embeds them directly into 2.5D GSAP layers.
4. **✨ Dynamic Glowing Pop-up Captions:** Word-by-word active word highlighting with scale-up pop (`scale: 1.15`).
5. **☁️ 100% Zero-Local-Load Cloud Execution:** Run everything entirely in the cloud via **GitHub Actions**, VPS, or Docker without consuming your local CPU.
6. **🧹 Automatic Storage Pruning:** Temporary render frames are auto-purged immediately, heavy assets are ignored in `.gitignore`, and older files follow a 10-day retention schedule.

---

## 🚀 Usage

### 1. Run in Cloud (GitHub Actions - Zero Local CPU Load)
Go to your GitHub repo -> **Actions** -> **Vox Studio Cloud Production** -> Click **Run workflow** -> Enter topic (e.g. `Bermuda Triangle`) -> Download finished 1080x1920 60fps MP4 from Artifacts.

### 2. Run Locally / VPS CLI
```bash
# Produce video for any topic
python -m vox_studio.cli create "Bermuda Triangle"

# Monitor Google Trends and auto-produce for top breakout
python -m vox_studio.cli trends --limit 3 --auto-produce
```

### 3. Run with Docker / VPS
```bash
docker build -t vox-studio -f vox_studio/Dockerfile .
docker run --rm -v $(pwd)/vox_studio/output:/app/vox_studio/output vox-studio create "Bermuda Triangle"
```
