# Instagram Reels setup (official API — no bots, no browser automation)

The bot publishes Reels through Instagram's **Content Publishing API**. It is free, but Meta
requires a one-time setup. Budget ~20 minutes the first time.

---

## 0. What you need (checklist)

| Requirement | Why |
|---|---|
| Instagram **Business** or **Creator** account | the API cannot publish to personal accounts |
| A **Facebook Page** linked to that Instagram account | required by *Facebook Login for Business*, which is the only config that allows binary (resumable) uploads |
| A Meta app in **developers.facebook.com** | holds your permissions and tokens |
| `IG_USER_ID` + `IG_ACCESS_TOKEN` in `.env` | what the bot uses to publish |
| 9:16 vertical video, H.264, AAC ≤ 48 kHz, 3 s – 15 min, ≤ 300 MB | Instagram's Reel limits — the bot's renders are inside all of them |

> Personal accounts: switch in the Instagram app → *Settings → Account type → Switch to Professional → Creator/Business*.

---

## 1. Link the accounts

1. Create/choose a Facebook Page: <https://www.facebook.com/pages/create>.
2. Instagram app → *Settings → Account type → Professional → Business*.
3. Instagram → *Settings → Business → Connect a Facebook Page* (or Page → *Settings → Linked accounts → Instagram*).
4. In Meta Business Suite, confirm both assets sit in the **same Business Manager** (makes the token stable).

## 2. Create the Meta app

1. <https://developers.facebook.com/apps> → **Create app** → use case **Other → Business**.
2. Add the product **Instagram** (or "Instagram Graph API").
3. **App settings → Basic**: note the **App ID** and **App Secret**.
4. **App roles → Roles**: add your own Facebook account as **Administrator** (testers can publish to accounts that granted a role; the audit only matters for other people's accounts).

## 3. Get the Instagram user id

Easiest path (no code):

```bash
# 1) get a user token from the Graph API Explorer (select your app, add permissions, then "Get User Access Token")
#    permissions: instagram_basic, instagram_content_publish, pages_show_list, pages_read_engagement
# 2) exchange it for a long-lived token (60 days)
curl -s "https://graph.facebook.com/v21.0/oauth/access_token?grant_type=fb_exchange_token\
&client_id=<APP_ID>&client_secret=<APP_SECRET>&fb_exchange_token=<SHORT_TOKEN>"

# 3) find your Page, then the Instagram business account attached to it
curl -s "https://graph.facebook.com/v21.0/me/accounts?access_token=<LONG_TOKEN>"
curl -s "https://graph.facebook.com/v21.0/<PAGE_ID>?fields=instagram_business_account&access_token=<LONG_TOKEN>"
```

The `instagram_business_account.id` value (starts with `178…`) is your **IG_USER_ID**.
Put both into `.env`:

```ini
PLATFORMS=youtube,instagram
IG_USER_ID=17841400000000000
IG_ACCESS_TOKEN=EAAG...
IG_UPLOAD_MODE=resumable
IG_SHARE_TO_FEED=true
```

Verify:

```bash
python -m factshorts.instagram --check     # prints account info + publish quota
python main.py --platform-status           # shows readiness of every platform
```

## 4. Upload modes

| Mode | When to use | How it works |
|---|---|---|
| `resumable` (default) | normal case | bot creates a container with `upload_type=resumable` and pushes the mp4 bytes to `rupload.facebook.com`. Needs *Facebook Login for Business* (Facebook Page linked). |
| `url` | app configured with *Instagram Login* (no Facebook Page) | bot passes a public `video_url`; Instagram downloads it itself. Set `IG_PUBLIC_BASE_URL=https://your-host/videos` and serve `output/*.mp4` there (S3/R2/nginx/Vercel static). |

The bot polls the container status, then calls `media_publish` — exactly what the official
docs describe. Rate limit: **100 published posts per 24 h** (`/status` shows the current usage).

## 5. Tokens expire (the one thing that bites everyone)

- Long-lived user/page tokens last **~60 days**.
- When it expires, publishing fails with an auth error — the bot tells you in Telegram and marks the video `upload_failed`, keeping the file so you can re-publish.
- Refresh it: repeat step 3's `/oauth/access_token` call, paste the new token in `.env`, restart.
- Cheap insurance: put a calendar reminder for day 50, or keep `IG_ACCESS_TOKEN` in a password manager.

## 6. What the bot posts

- Video: your 1080×1920 render.
- Caption: hook + fact + hashtags (max `IG_HASHTAG_LIMIT`, default 8) + `Source: Wikipedia → <url>` when the fact came from a trend/source lookup + a synthetic-voice disclosure line.
- `share_to_feed` (default true) also shows the Reel in your feed grid.
- No links in captions — Instagram doesn't make them clickable, so the bot keeps the source URL as plain text.

## 7. Troubleshooting

| Error | Meaning / fix |
|---|---|
| `(#10) Application does not have permission for this action` | missing `instagram_content_publish`, or the account is not Business/Creator |
| `(#100) The parameter video_url is required` | you set `IG_UPLOAD_MODE=url` without a reachable `IG_PUBLIC_BASE_URL` |
| `Only photo or video can be accepted as media type` | the file is not a valid mp4 — re-render (`python main.py --generate`) |
| `ProcessingFailedError` / container `ERROR` | usually an unusual codec/bitrate; the bot's H.264 1080×1920 @30fps AAC 48 kHz renders are accepted, so re-render and retry |
| Publishing works manually but not from the server | datacenter IPs are fine for the Graph API, but check that the token in `.env` on the server is the same long-lived one |
| `publish limit reached` | 100 posts/24 h cap — wait it out; the bot reports quota in `/status` |

## 8. Same video, two platforms

`PLATFORMS=youtube,instagram` (or `/platforms youtube,instagram` in Telegram) makes one render
go to both. Publish results are reported per platform, so a YouTube quota problem never blocks
Instagram and vice-versa. Every published video keeps its `yt_video_id` **and** `ig_media_id`
in SQLite, so `/stats` shows both.
