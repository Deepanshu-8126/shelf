# Deployment — running FactShorts Bot for ₹0

Three realistic options, from "runs on the machine you already have" to "always-on free cloud VM".
Pick one. All expect `ffmpeg` present and `.env` filled in.

---

## 0. Common prep (any host)

```bash
git clone <your-repo> factshorts-bot && cd factshorts-bot
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
sudo apt install -y ffmpeg fonts-dejavu-core          # Debian/Ubuntu
cp .env.example .env && nano .env                     # keys + your Telegram id
python main.py --check
python main.py --selftest
python main.py --auth                                 # YouTube OAuth (needs a browser once)
```

Copy `credentials/token.json` to the server if you authenticated on your laptop (or port-forward and run
`--auth` on the server itself). On a headless box, `--auth` falls back to a console flow asking you to paste a code.

**Resource notes:** each render is CPU-bound (2-4 CPU cores is comfortable). The **free voice** runs on your
CPU too: Kokoro-82M holds ~1 GB while loaded (that is why `TTS_ISOLATE=true` runs it in a short-lived child
process and releases it before whisper/ffmpeg start) and Piper needs only a few hundred MB. With 1 GB RAM or
less, set `VOICE_PROVIDER=piper` and `WHISPER_MODEL=tiny.en`. First run downloads the model into
`TTS_MODEL_DIR` (Kokoro ~350 MB, Piper ~63 MB) — after that the voice needs no network at all.
RAM: ~500 MB for ffmpeg, more if you enable `CAPTION_SOURCE=whisper` (faster-whisper `small` ≈ 1 GB;
`base.en` is the default and much lighter). Disk: stock clips cache at up to ~90 MB each —
`make clean` or the built-in nightly `cleanup` job keeps it in check.

---

## 1. Your own PC / laptop (simplest)

```bash
python main.py --bot        # Telegram bot + daily scheduler in one process
```

**Windows — run it in the background:**
- *Task Scheduler*: Create Task → Trigger **At log on** (or "At startup") → Action → Start a program →
  `C:\...\factshorts-bot\.venv\Scripts\python.exe`, arguments `main.py --bot`, Start in `C:\...\factshorts-bot`.
  Check *Run whether user is logged on or not* and enable *Restart on failure*.
- Or use **NSSM** to install it as a Windows service:
  `nssm install FactShorts "C:\...\.venv\Scripts\python.exe" "main.py --bot"`

**Linux/macOS — systemd user service:** see §3, just drop `User=`/sudo parts.
**Weaker laptop tip:** lower `VIDEO_PRESET=veryfast` (or `superfast`) and `VIDEO_FPS=30`; renders get faster with
barely any visible difference at 1080×1920.

---

## 2. Docker (any VPS, NAS, or your PC)

```bash
docker compose up -d --build
docker compose logs -f            # watch the first run
```
Volume layout (already in `docker-compose.yml`): `data/` (SQLite), `cache/` (clips + temp), `output/` (finals),
`logs/`, `credentials/`, `assets/music`, `assets/stock`. Backups = copy `data/` and `credentials/`.

Scheduler-only container (no bot polling) if you prefer Telegram on your laptop and rendering on the server:
```bash
docker compose run --rm bot python main.py --daemon
```

---

## 3. Oracle Cloud Free Tier (always-on, free forever, controls via Telegram)

Oracle's Always Free tier includes an Arm Ampere A1 instance (up to 4 OCPU / 24 GB RAM) — plenty for this bot.

1. Sign up → **Compute → Instances → Create**. Shape: **VM.Standard.A1.Flex** (e.g. 2 OCPU / 12 GB).
   Image: Ubuntu 22.04/24.04. Add your SSH key.
2. Open the default security list for SSH (port 22). The bot makes only **outbound** connections, so nothing else
   needs opening — do **not** expose ports you don't need.
3. Install and set up:
   ```bash
   sudo apt update && sudo apt install -y python3-venv python3-pip ffmpeg git espeak-ng
   git clone <your-repo> ~/factshorts-bot && cd ~/factshorts-bot
   python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt
   cp .env.example .env && nano .env     # SCHEDULE_TIMES=08:30,19:30 · PLATFORMS=youtube,instagram
   python main.py --check && python main.py --selftest
   python main.py --auth                 # YouTube
   python -m factshorts.instagram --check   # Instagram (optional)
   python main.py --auth            # console flow: paste the URL into your laptop browser
   ```
   (If Arm ffmpeg seems slow, `sudo apt install -y ffmpeg` is the ARM build — fine at 1080×1920.)
4. **systemd service** (`sudo nano /etc/systemd/system/factshorts.service`):
   ```ini
   [Unit]
   Description=FactShorts Bot
   After=network-online.target
   Wants=network-online.target

   [Service]
   Type=simple
   User=ubuntu
   WorkingDirectory=/home/ubuntu/factshorts-bot
   Environment=PYTHONUNBUFFERED=1
   ExecStart=/home/ubuntu/factshorts-bot/.venv/bin/python main.py --bot
   Restart=always
   RestartSec=15
   # a little hardening
   NoNewPrivileges=true
   PrivateTmp=true

   [Install]
   WantedBy=multi-user.target
   ```
   ```bash
   sudo systemctl daemon-reload && sudo systemctl enable --now factshorts
   systemctl status factshorts -n 30
   journalctl -u factshorts -f
   ```
5. Optional but smart: a 1 GB swap file on small shapes, and `TIMEZONE=Asia/Kolkata` in `.env` so
   `/schedule 19:30` means what you think it means.

---

## 4. GitHub Actions (recommended: nothing runs on your PC)

Twice-daily publishing with zero server: the workflow at `.github/workflows/daily.yml` runs at
**08:30 and 19:30 IST** (edit the two `cron:` lines — GitHub cron is UTC), renders a video, and
publishes it to YouTube and (optionally) Instagram. You can also trigger it manually from the
Actions tab and choose the platforms.

Setup:

1. Push this repo to GitHub (public repos get unlimited Actions minutes; private repos get 2,000/month — a ~3-minute job twice a day fits easily).
2. **Settings → Secrets and variables → Actions**, add:
   `GEMINI_API_KEY`, `PEXELS_API_KEY`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_ALLOWED_USER_IDS`,
   `TELEGRAM_CHAT_ID` (optional), `VIDEO_MODE=facts|story`, `VOICE_PROVIDER=auto|kokoro|piper|edge`,
   `TTS_MODEL_DIR` (optional: point it at a cached folder so the Actions runner does not re-download
   the voice model every run; e.g. `${{ github.workspace }}/.models` with a cache step),
   `IG_USER_ID` + `IG_ACCESS_TOKEN` (optional, for Reels).
3. YouTube credentials as base64 secrets (they are files, so encode them):
   ```bash
   base64 -w0 credentials/client_secret.json > client.b64     # paste into YT_CLIENT_B64
   base64 -w0 credentials/token.json        > token.b64       # paste into YT_TOKEN_B64
   ```
4. Run the workflow once from the Actions tab (`workflow_dispatch`) to confirm it publishes.
5. Want different times or a different niche per run? Edit the `cron:` lines and the
   `env:` block (`NICHE_ROTATE`, `SCHEDULE_TIMES`, `TRENDS_GEO`, `PLATFORMS`).

Trade-offs:
- The runner is fresh every time → **`data/factshorts.db` resets**, so "never repeat a topic" loses memory.
  Fix: commit the DB back to the repo after each run (the example workflow below does that), or keep the bot
  on a real host.
- `credentials/token.json` must live in **repository secrets** (base64). Rotate it if the repo ever leaks.
- Cron can drift by a few minutes under load — fine for social posting; not a scheduler replacement.
- Each run is a clean machine: the workflow commits `data/factshorts.db` back to the repo so the
  "never repeat a topic" memory survives. (Prefer no DB in git? Download the artifact instead.)
- No Telegram **bot** in this mode (nothing is listening). You still get Telegram *messages*:
  previews, publish confirmations and failure alerts — you just can't reply `/approve`.
  Auto-publish is therefore switched on for this mode (`--upload`).
- For manual control (preview → `/approve`), use §3 Oracle instead, or keep a local `--bot`
  and let CI handle the unattended runs.

**Instagram in CI:** set `IG_USER_ID` + `IG_ACCESS_TOKEN` as secrets and run the workflow with
`platforms: youtube,instagram` (the manual trigger has a dropdown for it). Instagram publishing
from a GitHub runner works because it is a plain HTTPS API — no IP allow-listing involved.

---

## 5. Backups, monitoring, hygiene

- **Back up** `data/factshorts.db` (topic history + queue + stats) and `credentials/`. That's all the state there is.
- **Logs** rotate automatically in `logs/factshorts.log` (2 MB × 3).
- You get a **Telegram notification on every failure** — that's your monitoring. If Telegram goes quiet for days,
  check the service: `systemctl status factshorts`.
- **Stay inside YouTube's rules:** keep topic variety high, don't increase to 20 uploads/day of the same template,
  and keep the synthetic-content disclosure on.
- **Two posts a day** (`SCHEDULE_TIMES=08:30,19:30`) with `NICHE_ROTATE=true` gives you morning + night
  uploads that don't look like reruns of each other.
- **Instagram tokens expire every ~60 days** — calendar reminder, or move to §4 CI where you just
  update the secret.
- If you scale to multiple channels: one `.env` + one `credentials/` (one Google account/channel) per instance,
  separate SQLite DBs, and stagger the schedules.
