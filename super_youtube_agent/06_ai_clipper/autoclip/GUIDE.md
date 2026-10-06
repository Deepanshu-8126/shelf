# Kya bana sakte ho, aur daily flow kya rahega

Ye guide sirf **jo abhi chal raha hai** uske baare mein hai. Jo nahi bana, wo bhi
saaf-saaf likha hai — taaki aap us par channel plan na banayein.

---

## 1. Teen type ki videos — aur unka asli status

### ✅ Type A — Clip channel (YE POORA READY HAI)
Kisi bhi video ka link do → vertical shorts, hooks apne aap, captions apne aap, logo apne aap.

**Tested, dono languages:**

| Source | Result | Time |
|---|---|---|
| Hindi vlog (Sourav Joshi, 16 min) | 2 shorts, Devanagari captions | 85 s |
| Spanish vlog (Familia Carameluchi, 15 min) | 2 shorts, Spanish captions | 117 s |

```bash
autoclip "<video link>" --clips 2 --langs es en --profile profiles/spanish.json
```

**Shart:** source video par YouTube ke auto-captions hone chahiye (99% badi videos par hote hain).
Na ho to Whisper chalega — slow, aur Hindi mein kharab.

---

### ⚠️ Type B — Faceless Spanish video (script → AI voice → stock footage)
Aapki apni script, Spanish AI voice, Pexels ki stock clips. **Ye aadha setup hai.**

| Cheez | Status |
|---|---|
| Spanish voices (45 locales: es-ES, es-MX, es-AR, es-CO…) | ✅ tested, 6 voiceovers 3.5 s mein |
| MoneyPrinterTurbo clone + config | ✅ configured, tasks validate hote hain |
| Actual video render | ❌ **kabhi chala ke nahi dekha** — deps install nahi hain |

Chalane ke liye chahiye: `pip install -r requirements.txt` (MPT folder mein), ffmpeg,
aur ek **Pexels API key** (free) stock footage ke liye.

---

### ❌ Type C — Hindi/English video ka Spanish dubbing
"Sourav Joshi ka clip, upar Spanish voiceover" — **ye abhi nahi bana hai.**
`autoclip` mein TTS step hai hi nahi; wo original audio hi rakhta hai.
Banane mein ~1 ghanta lagega (Edge-TTS ka code `yt-clipper/batch.py` mein already hai).

---

## 2. Spanish channel ke liye sabse tez raasta

**Type A chuno, Spanish sources ke saath.** Kyun: aaj hi chal raha hai, koi API key nahi,
koi stock footage nahi chahiye.

```bash
cd autoclip

# ek video se
autoclip "https://youtube.com/watch?v=XXXX" --clips 3 \
         --langs es en --profile profiles/spanish.json --outdir Shorts/es

# poore channel se, 5 latest videos
autoclip "https://www.youtube.com/@CHANNEL" --limit 5 --clips 2 \
         --langs es en --profile profiles/spanish.json --outdir Shorts/es

# search se (trending topic)
autoclip "ytsearch5:pelea famosos españa" --genre reality \
         --langs es --profile profiles/spanish.json
```

**Niche ideas jahan hook lexicon strong hai** (`--genre reality` ya `news`):
reality TV / famosos drama, futbol reactions, true-crime, noticias.
Lexicon mein `pelea`, `gritando`, `policía`, `traición`, `mentira`, `increíble` jaise
shabd hain — ye hi clips ko score karte hain.

---

## 3. Daily flow (roz ka kaam, ~30 min)

```
1. SOURCE          2-3 channels chuno, unki nayi video check karo       2 min
2. RUN             autoclip "<link>" --clips 3 --profile ...            ~3 min/video
3. REVIEW          Shorts/ folder mein dekho, kachra clips delete karo  5 min
4. TITLE+DESC      clips.json mein hook likha hai, usse title banao     5 min
5. UPLOAD          manually (auto-upload abhi nahi bana)                10 min
```

**Ek machine, ek ghante mein ~20 shorts** ban sakte hain (2-core box par; GPU par 3-4×).

**Cadence:** din mein 2-3 shorts, 90 din. Isse kam par algorithm pick nahi karta.

---

## 4. Profile = channel. Multiple channels ek hi system se

Har channel ke liye bas ek JSON copy karo:

```bash
cp profiles/spanish.json profiles/mi_canal.json
# usme badlo: channel, accent (colour), watermark (apna logo)
autoclip "<link>" --profile profiles/mi_canal.json
```

Abhi 3 profiles hain: `default.json` (DKX Hindi), `spanish.json` (DKX_ES, orange),
`biggboss.json` (BB, purple).

---

## 5. Zaroori sach — padh lo, baad mein channel band na ho

1. **Titles abhi kamzor hain.** Bina `OPENAI_API_KEY` ke title = transcript ka pehla
   line + 🔥, jaise *"profesional son las 4:37 er 🔥"*. Bekaar hai.
   Key daal do (`export OPENAI_API_KEY=sk-...`) → LLM proper hook title likhega.
   **Ya titles khud likh lo** — 30 second ka kaam, sabse zyada farak yahi padta hai.

2. **`--safe` sirf video fingerprint todta hai.** Audio alag se match hota hai aur
   usko todna mushkil hai. Background music wali clip phir bhi pakdi ja sakti hai.

3. **Content ID claim ≠ strike**, par **1-3 minute ke Short par active claim = video block**.
   Isliye clips 60 second se neeche rakho (system ab khud 58s par clamp karta hai).

4. **Reused content policy sabse bada risk hai** — poore channel par lagti hai, aur
   original creator ki permission se bhi nahi bachti. Bachav: har video par apni
   commentary/captions/edit ho. Sirf kaat ke upload karna = monetization reject.

5. **Credit do.** Description mein original channel ka naam + link. Isse takedown
   request ka chance kaafi kam ho jata hai.

---

## 6. Aage kya add karna chahiye (priority order)

| # | Feature | Faida | Mehnat |
|---|---|---|---|
| 1 | LLM titles/descriptions | Sabse bada CTR impact | key daalo, code ready |
| 2 | Spanish dubbing (Type C) | Hindi content → Spanish market | ~1 ghanta |
| 3 | Auto-upload (YouTube API) | Roz ke 10 min bachenge | ~2 ghante |
| 4 | Face-tracking crop | Centre punch-in ki jagah chehra follow kare | ~2 ghante |

---

# Paisa: Spanish channel ka asli math

## Pehle ek galatfehmi door karo
**Spanish bolne se audience USA ki nahi ho jaati.** YouTube paisa *viewer ki location* pe deta hai, channel ki language pe nahi. Spanish content ka 70-80% traffic Mexico/LatAm jaata hai, jahan RPM India se sirf thoda behtar hai.

Spanish ka **blended CPM ~$3.00, RPM ~$1.65** — isi wajah se ki zyadatar viewers LatAm ke hain.

| Audience | Shorts RPM | 1M Shorts views | Long-form RPM | 1M long views |
|---|---|---|---|---|
| English → USA | $0.12 | **$120** | $5.00 | **$5,000** |
| Spanish → US Hispanic | $0.10 | $100 | $3.50 | $3,500 |
| Spanish → Spain | $0.05 | $50 | $2.50 | $2,500 |
| Spanish → Mexico/LatAm | $0.03 | **$30** | $1.00 | $1,000 |
| Hindi → India | $0.02 | $20 | $0.60 | $600 |

**Do nateeje jo chubhte hain:**
1. **Shorts ka ad revenue har jagah bekaar hai.** 1M views = $30 (LatAm) se $120 (US). 1M views bahut badi cheez hai. Shorts se ameer nahi hote — Shorts se *audience banti hai*.
2. **Agar Spanish clips LatAm audience laaye, to India se farak sirf 1.5x hai** — 10x nahi. Sirf language badalne se kuch khaas nahi hoga.

## Agar sach mein USA ka paisa chahiye
Teen raaste, honest ranking:

**1. English content, US topics** — sabse zyada RPM ($5/1k long-form), par competition bhi sabse zyada.
**2. Spanish content US Hispanic ke liye** — $3.50 RPM, competition kam. Ye aapka best risk/reward hai.
**3. Generic Spanish (Spain/Mexico vlogs clip karna)** — $1 RPM. Ye wahi hai jo abhi `profiles/spanish.json` kar raha hai.

**US Hispanic audience topic se aati hai, language se nahi:**
- "vida en USA", trabajos/salarios en Estados Unidos, inmigración
- NFL / NBA / MLB en español
- US celebrity & reality drama en español
- Spanglish creators jo already US mein based hain

Matlab: **source videos US-based Spanish creators ke uthao**, Spain ya Mexico ke vlogs ke nahi. Yehi ek decision aapka RPM 3x kar deta hai.

## Sabse bada blocker — RPM nahi, eligibility
Non-monetized channel ka RPM **$0** hai, chahe audience USA ki ho.
Clip channel ko YouTube ki **reused content** policy clear karni padti hai — "significant original commentary ya substantive modification" chahiye, aur ye rule **poore channel pe** lagta hai. Sirf crop + captions + watermark isko पास nahi karta.

Isliye RPM ki chinta baad mein. Pehle ye: **har clip pe apni Spanish voiceover ya commentary daalo** (Type C dubbing/TTS). Isse do cheezein ek saath hoti hain — original input add hota hai, aur Content ID exposure bhi girti hai.


---

# Update: free LLM brain + caption styles

## LLM ab free mein chalega (Groq)
Pehle `OPENAI_API_KEY` chahiye tha. Ab **Groq** bhi chalta hai — credit card nahi, free tier:

1. console.groq.com pe sign up (email bas)
2. API key banao
3. `export GROQ_API_KEY=gsk_...`

Bas. `autoclip` khud detect kar lega aur `llama-3.3-70b-versatile` use karega.
Free limit: ~30 request/minute, 1000/day — ye roughly **1000 video/din** hai, aapse kahin zyada.

Isse do cheezein theek hoti hain: dhang ke titles, aur behtar clip selection.
Dusra provider chahiye to: `AUTOCLIP_LLM_BASE` + `AUTOCLIP_LLM_MODEL`.

## Caption styles
`--caption-style` ab 5 options deta hai:

| Style | Kaisa dikhta hai |
|---|---|
| `karaoke` | word-by-word colour fill (default) |
| `hormozi` | poora phrase upar, bolte hue word accent colour mein pop — Shorts pe sabse zyada chalta hai |
| `bounce` | springy ALL-CAPS pop |
| `glow` | neon soft edge |
| `plain` | bina animation |

```bash
autoclip "<link>" --caption-style hormozi
```
Profile JSON mein `"caption_style": "hormozi"` daal ke channel-wide bhi set kar sakte ho.

## Do bug jo is kaam ke dauraan mile
1. **Duplicate words** — YouTube ke rolling auto-captions tail dubara print karte hain, to transcript mein "it's it's almost almost" aata tha. Ek test video mein **24 duplicate words** the. `transcribe.dedupe()` ab inhe hata deta hai (sab languages mein).
2. **Caption lines overlap** — ek line gayab hone se pehle agli aa jaati thi, do lines stack ho jaati thi. Ab har line agli se pehle hat jaati hai.

Dhyan rahe: `"sandwi"` jaise adhoore words YouTube ke apne captions ki galti hai, hamari nahi. Behtar chahiye to `--whisper small` use karo.


---

# Review dashboard

Upload se pehle har clip dekhne, title theek karne aur approve/reject karne ke liye:

```bash
cd autoclip
python3 -m autoclip.dashboard --outdir /home/user/Shorts
```

Browser mein khulta hai. Har card pe:

- **Video player** — clip chala ke dekho, seek bhi hota hai
- **Title box** — seedha edit karo, apne aap save ho jaata hai
- **Approve / Reject** — dobara click karo to pending
- **"Naye title suggest karo"** — Groq se 3 alternative title, kisi pe click karke laga lo
- **Export approved CSV** — sirf approved clips ki list `Shorts/approved.csv` mein

Decisions har folder ke `review.json` mein save hote hain, to server band karke dobara
kholo to sab waapas aa jaata hai.

Sirf Python stdlib use karta hai — koi pip install nahi, sandbox wipe hone pe bhi chalta hai.
`--outdir` ke bahar ki koi file serve nahi hoti.
