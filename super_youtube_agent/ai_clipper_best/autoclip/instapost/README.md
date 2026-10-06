# instapost — DKX ke Reels automatic Instagram pe

**Faisla ho chuka hai: BAN NAHI CHAHIYE. Isliye sirf official API chalega.**

instagrapi wala driver code mein hai par **band hai** — galti se bhi nahi
chalega. Chalane ke liye `INSTAPOST_I_ACCEPT_BAN_RISK=yes` jaan boojh kar
set karna padega. Mat karna.

| | `graph` (official API) | `private` (instagrapi) |
|---|---|---|
| Account | Business zaroori | koi bhi, personal bhi |
| App Review | 2-4 hafte | nahi |
| Video kaise jaata hai | Meta public URL se khud download karta hai | local file seedha upload |
| Story | haan (Business pe) | haan, stickers/polls ke saath bhi |
| Limit | 25/24h (Meta ka) | humne 8/din rakha hai, jaan boojh kar |
| Ban risk | **zero** | **asli hai** — isliye BAND hai |
| Chahiye | `IG_USER_ID`, `IG_ACCESS_TOKEN` | `IG_USERNAME`, `IG_PASSWORD` |

Default hamesha official hai. Agar official set up nahi hai to bhi code
chupke se private pe nahi jaayega — wo account ko convenience ke badle
bech dena hota.

instagrapi wala driver defensive banaya hai: session save karke reuse karta hai
(baar baar fresh login hi sabse bada ban trigger hai), har action ke beech
25-70 second ka random gap daalta hai, aur din ke 8 se zyada nahi.


Dashboard mein har clip ke neeche do button hain:

- **Instagram Reel** — reel post karta hai, title hi caption banta hai
- **Reel + Story** — wahi reel, plus Story pe bhi push

Ek baar setup karo, phir roz sirf button dabana hai.

---

## Pehle ye jaan lo (ye Meta ke rules hain, mere nahi)

| Cheez | Haqeeqat |
|---|---|
| Account | **Business account chahiye.** Personal se API chalti hi nahi. Creator account feed/reel ke liye chalta hai par **Story ke liye Business zaroori hai**. |
| App Review | `instagram_business_content_publish` permission ke liye Meta ka review lagta hai — **2-5 din se 2-4 hafte**. Review se pehle sirf aapke apne test user post kar sakte hain. |
| Video ka URL | Meta **aapki file khud download karta hai** ek public HTTPS link se. Seedha file upload ka option hi nahi hai. |
| Limit | **25 post / 24 ghante** per account. Reel aur Story dono isi 25 mein ginte hain — matlab "Reel + Story" = 2. |
| Reel specs | 9:16, 3-90 sec, H.264 + AAC, 100 MB tak. Apne clips pehle se theek hain. |

Wo "video ka URL" wali baat sabse important hai — neeche dekho.

---

## Setup — 20 minute, aaj ho jayega

**App Review ki zaroorat NAHI hai.** Review sirf tab lagta hai jab app doosron
ke accounts pe post kare. Apne account pe post karne ke liye Development mode
kaafi hai — bas apna account "Instagram Tester" bana do.

**1. Account ko Business karo (2 min, free)**
Instagram app → Settings and privacy → **Account type and tools** →
Switch to professional account → category chuno → **Business**.

Ye company wala "brand account" nahi hai. Free hai, Facebook Page nahi chahiye,
followers/posts kuch nahi badalta, aur kabhi bhi wapas personal kar sakte ho.
Business isliye chahiye kyunki Story API sirf Business pe chalti hai (Creator
pe Reels to chalti hai, Story nahi).

**2. Meta app banao (5 min, free)**
[developers.facebook.com](https://developers.facebook.com) → My Apps →
Create App → use case **Business** → Add Product → **Instagram**.
App ko **Development mode mein hi rehne do**. Live mode mat karo.

**3. Apna account Tester banao (3 min) — ye step sabse important hai**
App Dashboard → **App roles → Roles** → Add People → **Instagram Tester** →
apna IG username daalo.
Phir Instagram app mein: Settings → **Apps and websites** → **Tester invites**
→ invite **accept** karo.

Ye accept karna hi wo cheez hai jo App Review ko bypass karti hai.

**4. Token lo (5 min)**
App Dashboard → Instagram → **API setup with Instagram login** →
"Generate token" → apna account chuno. Wahin **Instagram user ID** bhi milega.

Token 1 ghante ka hota hai. 60 din wala banane ke liye:

```
curl -s "https://graph.instagram.com/access_token?grant_type=ig_exchange_token&client_secret=APP_SECRET&access_token=SHORT_TOKEN"
```

**5. Daal do**

```
python3 /home/user/instapost/setup.py
```

Screen pe kuch nahi dikhega. Dashboard restart karo — button chalu.

## Public URL wali baat — isko mat chhodna

Meta **aapke computer se file nahi leta**. Wo ek public HTTPS link maangta hai
aur khud us link se video download karta hai. Iska matlab:

- Dashboard jis URL pe khula hai, **wahi URL Instagram ko bhejta hai** code.
  Browser ka `Host` header use hota hai, isliye alag se kuch set nahi karna.
- **Agar dashboard sirf `localhost` pe chal raha hai to post fail hoga** —
  Meta localhost tak pahunch hi nahi sakta. Error aayega "media URL not
  accessible".
- Is sandbox ka preview URL public hai, to yahan se chalega — par sandbox band
  hote hi link marr jaata hai.
- **Rozana chalane ke liye**: isko apne VPS/PC pe rakho aur dashboard ko ek
  public address pe laao (Cloudflare Tunnel sabse aasaan aur free hai:
  `cloudflared tunnel --url http://localhost:7860`).

Post ho jaane ke baad link ki zaroorat nahi — Meta video apne paas copy kar leta hai.

---

## Command line se

```
cd /home/user/instapost
python3 -m instapost.cli \
  --video-url "https://your-host/video?p=<clip-id>" \
  --caption "Mary Kom vs Mahhi 😳 #biggboss #shorts" \
  --clip-id biggboss-01 --story
```

## Dobara post nahi hoga

Har post `~/Shorts/instagram_posted.json` mein likha jaata hai. Wahi clip
dubara bhejoge to skip ho jayega. Reel aur Story alag-alag ginte hain, to
pehle reel daal ke baad mein story daalna chalega.

## Tests

```
cd /home/user/instapost && python3 tests/test_offline.py
```

7 test, bina internet aur bina account ke chalte hain — poora
container → poll → publish flow fake HTTP layer pe test hota hai, aur ek test
ye bhi check karta hai ki error message mein token kabhi leak na ho.
