# GitHub par push

Repo yahan commit ho chuka hai. Mere paas aapka GitHub token nahi hai, isliye
last step aap chalayein — 30 second ka kaam hai.

## Option A — gh CLI (sabse aasan)

```bash
cd autoclip
gh auth login                       # browser kholega, ek baar
gh repo create autoclip --public --source=. --remote=origin --push
```

## Option B — token se

1. https://github.com/new → naam `autoclip` → **Create repository**
   (README/licence add mat karein, yahan already hain)
2. Phir:

```bash
cd autoclip
git remote add origin https://github.com/<aapka-username>/autoclip.git
git branch -M main
git push -u origin main
```

## Push se pehle — secrets check

`.env` gitignored hai aur history mein kabhi nahi gaya. Khud confirm kar lein:

```bash
git ls-files | grep -c '\.env$'        # 0 aana chahiye
git grep -I -nE "gsk_|IGQ[A-Za-z0-9]{20}" $(git rev-list --all) | head
```

Doosri command kuch na de to history saaf hai. (`password="hunter2"`
test file ka nakli password hai, wo theek hai.)

## Clone karne ke baad apne PC/VPS par

```bash
git clone https://github.com/<username>/autoclip.git
cd autoclip
pip install -r requirements.txt           # ya: pip install yt-dlp faster-whisper pillow imageio-ffmpeg
cp .env.example .env                      # phir apni keys bharein
python3 -m autoclip.dashboard --outdir ~/Shorts --port 7860
```

`instapost/` isi repo ke andar hai, alag se clone karne ki zaroorat nahi —
dashboard use khud dhundh leta hai.

### Instagram posting ke liye public URL

Meta video khud download karta hai, isliye dashboard ek public https address
par hona chahiye:

```bash
cloudflared tunnel --url http://localhost:7860
# jo URL mile use yahan daalein:
INSTAPOST_PUBLIC_BASE=https://<jo-url-mila>.trycloudflare.com \
  python3 -m autoclip.dashboard --outdir ~/Shorts --port 7860
```

Apne VPS par domain ho to tunnel ki zaroorat nahi — seedha wahi URL daal dein,
aur phir wo kabhi badlega bhi nahi.
