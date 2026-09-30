# YouTube upload setup + the API audit (read this before you wonder why everything is private)

## 1. Google Cloud project

1. <https://console.cloud.google.com/> → **New Project** (name it anything, e.g. `factshorts-bot`).
2. **APIs & Services → Library** → search **YouTube Data API v3** → **Enable**.
3. **APIs & Services → OAuth consent screen**
   - User type: **External**.
   - App name, your email. Publishing status will stay **Testing** for personal use — that's fine.
   - **Scopes**: add `https://www.googleapis.com/auth/youtube.upload` and
     `https://www.googleapis.com/auth/youtube.force-ssl` (the second one lets the bot post your first/pinned comment).
   - **Test users**: add the Google account that owns your YouTube channel. (In Testing mode refresh tokens
     expire after 7 days — see §5 for the fix.)
4. **APIs & Services → Credentials → Create credentials → OAuth client ID**
   - Application type: **Desktop app**.
   - Download the JSON → save as `credentials/client_secret.json` in the project.
5. Run the consent flow once:
   ```bash
   python main.py --auth
   ```
   A browser opens, you approve, and `credentials/token.json` is written.
   Check it worked: `python -m factshorts.uploader --status`

## 2. The audit requirement (the important part)

> "All videos uploaded using the `videos.insert` endpoint from **unverified API projects created after 28 July 2020**
> will be **restricted to private** viewing mode. To lift this restriction, each API project must undergo an audit."

What that means in practice:

- Until the audit clears, your bot's uploads appear on the channel as **private**. Nothing is broken.
- Two workflows are fine while you wait:
  1. **Bot uploads to private** (`YOUTUBE_PRIVACY_STATUS=private`), you open YouTube Studio and flip to public.
  2. **Skip API uploads**: let the bot render + send the preview to Telegram, download it there, upload manually
     (copy title/description/tags straight from the preview message).
- Apply for the audit from the **YouTube API Services – Audit and Quota Extension form**:
  <https://support.google.com/youtube/contact/yt_api_form>
  What the form asks, roughly:
  - Project number, API client details.
  - What your app does (automated publishing of your own educational Shorts from your own machine).
  - **Your own channel(s)** and confirmation you own them. Audits for your own channel are routine.
  - Screencast/screenshots of the app + the review flow (your Telegram preview/approve screenshots are perfect).
  - The ToS compliance questions: no data resale, no third-party channels, respect the quota, honour user deletes.
- Common rejection reasons: uploading to **someone else's** channel, no visible app, unclear data handling,
  and (fatal) misrepresenting content — e.g. claiming AI narration is a real human voice.
  Honest answers + a real screencast clear the audit.

## 3. Synthetic-content disclosure

The narration is synthetic (edge-tts). YouTube's policy for *altered or synthetic* content expects disclosure
where the content could be mistaken for real. The API field is:

```python
body["status"]["containsSyntheticMedia"] = True    # factshorts/uploader.py sets this by default
```

Also add a line in the description (the bot's SEO module already writes one), e.g.:
*"Voice: synthetic narration, disclosed as altered or synthetic content."*

Keep `YOUTUBE_SYNTHETIC_DISCLOSURE=true`. It costs you nothing and protects the channel.

## 4. Quota math

| Operation | Units |
|---|---|
| `videos.insert` (one upload) | ~1600 |
| `commentThreads.insert` | 50 |
| `videos.list` / read calls | 1 |

Default daily quota = **10,000 units** → about **6 uploads/day** (minus a little for comments).
If the bot hits the ceiling it stops, logs it, and keeps the video pending — no half-broken state.
`MAX_UPLOADS_PER_DAY` (default 5) is your safety brake. A quota increase needs the same audit form.

## 5. Token expiry / "invalid_grant"

- **Testing** mode OAuth apps: Google expires refresh tokens after ~7 days. Re-run `python main.py --auth`.
- To stop the weekly dance: in the OAuth consent screen, **Publish** the app (still External, "unverified" is fine
  for personal use with your own account). Refresh tokens then stop expiring.
- Re-authenticate any time with `python main.py --auth` or by deleting `credentials/token.json`.
- **Never** commit `credentials/` — it holds your tokens. It's in `.gitignore` for a reason; on servers keep the
  directory `chmod 700`.

## 6. After publishing

- Shorts need: 9:16 vertical, up to 3 minutes. The bot renders **9.5-14.5 s** (`VIDEO_MIN/MAX_DURATION`) — safe.
- Keep `#shorts` in the description (the SEO module always includes it).
- The bot posts your "pinned comment" text as the **first comment**. The API cannot pin it — open the video and pin
  it manually for the engagement bump.
- Check the first 3-4 videos' retention in Studio; when a hook style underperforms, change `HOOK_TEMPLATES` /
  your niche and keep the rest.
