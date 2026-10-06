"""Telegram control bot.

Commands
--------
/generate [niche]     build a video now (shows live progress)
/approve [id]         upload the pending video to YouTube
/reject [id]          discard it
/regenerate [id]      discard and build a fresh one
/upload <id> [privacy]  upload an older render (public|unlisted|private)
/schedule HH:MM       daily posting time (also used by the scheduler)
/niche <name>         space | psychology | history | science | animals
/auto on|off          upload without waiting for approval
/voice [name|list]    pick the edge-tts voice (or list English voices)
/queue                pending / scheduled queue
/stats                upload history
/status               config + quota summary
/whoami               your Telegram user id (for TELEGRAM_ALLOWED_USER_IDS)

Access is restricted to TELEGRAM_ALLOWED_USER_IDS (or TELEGRAM_CHAT_ID).
"""
from __future__ import annotations

import asyncio
import html
from pathlib import Path

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
)

from . import db
from .config import NICHES, get_config
from .pipeline import generate_and_render, pipeline_summary
from .publish import platform_health, platforms_from_setting, publish_video, summary_text
from .trends import TrendClient
from .uploader import credentials_present, is_authenticated, quota_left, uploads_today
from .voice import usage_report
from .utils import human_bytes, module_logger, setup_logging

log = module_logger("bot")

GEN_LOCK = asyncio.Lock()  # one render at a time (ffmpeg is CPU hungry)


# ------------------------------------------------------------------ settings io
def setting_niche() -> str:
    cfg = get_config()
    return (db.get_setting("niche") or cfg.niche or "space").lower()


def setting_schedule() -> list[str]:
    cfg = get_config()
    stored = db.get_setting("schedule_times")
    if stored:
        times = [t.strip() for t in stored.split(",") if t.strip()]
        if times:
            return times
    return list(cfg.schedule_times)


def platform_list() -> list[str]:
    return platforms_from_setting()


def setting_auto() -> bool:
    cfg = get_config()
    return db.get_bool_setting("auto_mode", cfg.auto_mode)


def setting_mode() -> str:
    return (db.get_setting("video_mode") or get_config().video_mode or "facts").lower()


def setting_voice() -> str:
    return db.get_setting("voice") or get_config().voice or ""


# ---------------------------------------------------------------------- helpers
def _authorised(update: Update) -> bool:
    cfg = get_config()
    user = update.effective_user
    if not user:
        return False
    allowed = set(cfg.telegram_allowed_user_ids)
    if cfg.telegram_chat_id:
        allowed.add(cfg.telegram_chat_id)
    if not allowed:  # nothing configured -> allow the first user and tell them
        return True
    return user.id in allowed


async def _guard(update: Update) -> bool:
    if _authorised(update):
        return True
    user = update.effective_user
    log.warning("unauthorised access attempt by %s (%s)", user.full_name if user else "?", user.id if user else "?")
    if update.effective_message:
        await update.effective_message.reply_text(
            f"⛔ This bot is private.\nYour Telegram user id: `{user.id if user else 'unknown'}`\n"
            "Add it to TELEGRAM_ALLOWED_USER_IDS in .env",
            parse_mode=ParseMode.MARKDOWN,
        )
    return False


def _keyboard(video_id: int, uploaded: bool = False) -> InlineKeyboardMarkup:
    if uploaded:
        return InlineKeyboardMarkup(
            [[InlineKeyboardButton("📈 Open on YouTube", url=f"https://youtube.com/shorts/{db.get_video(video_id).get('yt_video_id')}")]]
        )
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("✅ Approve & upload", callback_data=f"approve:{video_id}"),
                InlineKeyboardButton("♻️ Regenerate", callback_data=f"regen:{video_id}"),
            ],
            [InlineKeyboardButton("🗑 Reject", callback_data=f"reject:{video_id}")],
        ]
    )


async def _send_preview(chat_id: int, context: ContextTypes.DEFAULT_TYPE, result, header: str = "") -> None:
    caption = (header + "\n\n" if header else "") + pipeline_summary(result)
    sent_video = False
    try:
        with open(result.path, "rb") as fh:
            try:
                await context.bot.send_video(
                    chat_id=chat_id,
                    video=fh,
                    caption=caption[:1024],
                    parse_mode=ParseMode.MARKDOWN,
                    supports_streaming=True,
                    width=1080,
                    height=1920,
                    read_timeout=120,
                    write_timeout=600,
                )
                sent_video = True
            except Exception:
                # Retry without markdown parse mode (fixes Telegram entity errors)
                fh.seek(0)
                await context.bot.send_video(
                    chat_id=chat_id,
                    video=fh,
                    caption=caption[:1024],
                    supports_streaming=True,
                    width=1080,
                    height=1920,
                    read_timeout=120,
                    write_timeout=600,
                )
                sent_video = True
    except Exception as exc:  # noqa: BLE001
        log.error("send_video failed: %s", exc)
        try:
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"{caption[:3500]}\n\n⚠️ Preview upload failed ({exc}). File: {result.path}",
            )
        except Exception:
            pass

    full = f"Title: {result.seo['title']}\n\n{result.seo['description']}"
    try:
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"📦 {Path(result.path).name} ({human_bytes(Path(result.path).stat().st_size)})\n\nDescription preview:\n{full[:2500]}",
        )
    except Exception:
        pass

    try:
        await context.bot.send_message(
            chat_id=chat_id,
            text="Approve kar dein to upload ho jayega 👇",
            reply_markup=_keyboard(result.video_id),
        )
    except Exception as exc:
        log.warning("Keyboard send failed: %s", exc)


async def _run_generation(chat_id: int, context: ContextTypes.DEFAULT_TYPE, niche: str, note: str = "") -> None:
    if GEN_LOCK.locked():
        await context.bot.send_message(chat_id=chat_id, text="⏳ Ek render already chal raha hai, thoda wait karein…")
        return
    async with GEN_LOCK:
        status = await context.bot.send_message(chat_id=chat_id, text=f"🚀 Starting: {note or niche}…")
        last = {"text": ""}

        async def progress(stage: str) -> None:
            if stage == last["text"]:
                return
            last["text"] = stage
            try:
                await status.edit_text(f"⚙️ [{niche}] {stage}")
            except Exception:  # noqa: BLE001 - edits can race/flood
                pass

        try:
            result = await generate_and_render(niche=niche, progress=progress)
        except Exception as exc:  # noqa: BLE001
            log.exception("generation failed")
            await status.edit_text(f"❌ Generation failed:\n`{html.escape(str(exc))[:900]}`", parse_mode=ParseMode.MARKDOWN)
            return
        await status.edit_text(f"✅ Rendered in {result.elapsed:.0f}s. Sending preview…")
        if setting_auto():
            await status.edit_text("🤖 Auto mode ON → uploading now…")
            await _do_upload(chat_id, context, result.video_id)
        else:
            await _send_preview(chat_id, context, result)


async def _do_upload(
    chat_id: int,
    context: ContextTypes.DEFAULT_TYPE,
    video_id: int,
    privacy: str | None = None,
    platforms: list[str] | None = None,
) -> None:
    row = db.get_video(video_id)
    if not row:
        await context.bot.send_message(chat_id=chat_id, text=f"Video #{video_id} mila nahi.")
        return
    targets = platforms or platform_list()
    health = platform_health()
    blocked = [p for p in targets if health.get(p) != "ready"]
    if blocked:
        await context.bot.send_message(
            chat_id=chat_id,
            text=(
                "🔑 Setup pending for: " + ", ".join(f"`{p}` ({health.get(p)})" for p in blocked) + "\n"
                + ("YouTube: `python main.py --auth` chalayein\n" if "youtube" in blocked else "")
                + ("Instagram: `docs/INSTAGRAM_SETUP.md` follow karein\n" if "instagram" in blocked else "")
                + f"\nBaki platforms pe upload ho jayega: `{', '.join(p for p in targets if p not in blocked) or 'none'}`"
            ),
            parse_mode=ParseMode.MARKDOWN,
        )
        if not [p for p in targets if p not in blocked]:
            return
        targets = [p for p in targets if p not in blocked]

    db.update_video(video_id, status="approved")
    msg = await context.bot.send_message(
        chat_id=chat_id, text=f"⬆️ Publishing #{video_id} to {', '.join(targets)}…"
    )
    results = await publish_video(video_id, platforms=targets, privacy=privacy)
    text = f"🎉 #{video_id} publish result:\n{summary_text(results)}"
    if any(r.get("error") for r in results.values()):
        text += "\n\n⚠️ Jo fail hua wo queue mein pending hai — `/queue` dekhein, dobara `/approve` kar sakte hain."
    if "youtube" in results and not results["youtube"].get("error"):
        text += "\n\n📌 Tip: YouTube par pinned comment manually pin karein (API se pin nahi hota)."
    await msg.edit_text(text)
    if results.get("instagram", {}).get("url"):
        await context.bot.send_message(chat_id=chat_id, text="🔗 " + results["instagram"]["url"])


# ------------------------------------------------------------------- commands
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _guard(update):
        return
    cfg = get_config()
    text = (
        "👋 *FactShorts Bot*\n\n"
        f"Niche: `{setting_niche()}`  •  slots: `{', '.join(setting_schedule())}`  •  auto: `{setting_auto()}`\n"
        f"Platforms: `{', '.join(platform_list())}`  •  voice: `{setting_voice() or 'auto-rotate'}`\n"
        f"Mode: `{setting_mode()}` (facts = 10-15s · story = ~60s)\n\n"
        "*Commands*\n"
        "`/generate [niche]` – banao abhi\n"
        "`/clip <url> [genre]` – YouTube link se viral short banao\n"
        "`/instagram` – Instagram status aur posting setup\n"
        "`/approve [id]` – YouTube pe upload\n"
        "`/reject [id]` – phenko\n"
        "`/regenerate [id]` – naya version\n"
        "`/upload <id> [public|unlisted|private]`\n"
        "`/schedule 08:30,19:30` · `/niche <name>` · `/auto on|off`\n"
        "`/mode facts|story` – 10s fact ya ~60s story\n"
        "`/voice <name|list>` · `/voiceprovider auto|kokoro|piper|edge`\n"
        "`/platforms youtube,instagram` · `/trends [IN|US]`\n"
        "`/queue` · `/stats` · `/status` · `/whoami`\n\n"
        f"NICHES: {', '.join(NICHES)}"
    )
    await update.effective_message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
    cfg_ok = credentials_present()
    await update.effective_message.reply_text(
        f"Health: topics_used={len(db.topic_fingerprints())} · "
        f"YouTube client secret={'✅' if cfg_ok else '❌'} · "
        f"token={'✅' if is_authenticated() else '❌'} · "
        f"uploads_today={uploads_today()}/{cfg.yt_max_uploads_per_day}"
    )


async def cmd_whoami(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    chat = update.effective_chat
    await update.effective_message.reply_text(
        f"user_id: `{user.id}`\nchat_id: `{chat.id}`\nTour `TELEGRAM_ALLOWED_USER_IDS={user.id}`",
        parse_mode=ParseMode.MARKDOWN,
    )


async def cmd_generate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _guard(update):
        return
    niche = (context.args[0].lower() if context.args else setting_niche())
    if niche not in NICHES:
        await update.effective_message.reply_text(f"Unknown niche. Options: {', '.join(NICHES)}")
        return
    await _run_generation(update.effective_chat.id, context, niche, note=f"/generate {niche}")


async def cmd_clip(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _guard(update):
        return
    if not context.args:
        await update.effective_message.reply_text(
            "⚡ *AutoClip Usage:*\n`/clip <youtube_url> [genre]`\n\n"
            "Genres: `vlog` (default), `gaming`, `reality`, `news`\n"
            "Example: `/clip https://youtu.be/XYZ gaming`",
            parse_mode=ParseMode.MARKDOWN,
        )
        return
    url = context.args[0].strip()
    genre = context.args[1].lower() if len(context.args) > 1 else "vlog"
    chat_id = update.effective_chat.id

    msg = await update.effective_message.reply_text(
        f"⚡ *AutoClip processing video...*\n`{url}`\n"
        f"• Genre: `{genre}`\n"
        f"• Captions: 2s Devanagari/English word timings\n"
        f"• Style: Hormozi kinetic karaoke\n"
        "Wait 1-2 minutes...",
        parse_mode=ParseMode.MARKDOWN,
    )

    def _run_autoclip():
        root_dir = Path(__file__).resolve().parents[2]
        autoclip_dir = root_dir / "ai clipper best" / "autoclip"
        import sys
        if str(autoclip_dir) not in sys.path and autoclip_dir.is_dir():
            sys.path.insert(0, str(autoclip_dir))
        from autoclip.pipeline import run as run_pipeline
        return run_pipeline(url, clips=1, genre=genre, safe_level=1)

    try:
        results = await asyncio.to_thread(_run_autoclip)
        if not results:
            await msg.edit_text("❌ AutoClip could not find suitable clips. Try another link or check video captions.")
            return

        await msg.edit_text(f"✅ AutoClip finished! Sending {len(results)} short(s)...")
        for r in results:
            vpath = r.get("out")
            if vpath and Path(vpath).is_file():
                title = r.get("title", "Viral Clip")
                hook = r.get("hook", "")
                caption = f"🎬 *{title}*\n\n🔥 *Hook:* {hook}\n⚡ *9:16 Vertical Short*\n\n📺 Channel: chan6 (AI Clipper)"
                keyboard = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("🚀 Post to Instagram Reel", callback_data=f"ig_post:{Path(vpath).name}"),
                    ]
                ])
                try:
                    with open(vpath, "rb") as fh:
                        await context.bot.send_video(
                            chat_id=chat_id,
                            video=fh,
                            caption=caption[:1024],
                            reply_markup=keyboard,
                            parse_mode=ParseMode.MARKDOWN,
                            supports_streaming=True,
                            width=1080,
                            height=1920,
                            read_timeout=120,
                            write_timeout=600,
                        )
                except Exception:
                    with open(vpath, "rb") as fh:
                        await context.bot.send_video(
                            chat_id=chat_id,
                            video=fh,
                            caption=caption[:1024],
                            reply_markup=keyboard,
                            supports_streaming=True,
                            width=1080,
                            height=1920,
                            read_timeout=120,
                            write_timeout=600,
                        )
    except Exception as exc:
        log.error("cmd_clip error: %s", exc)
        await msg.edit_text(f"❌ Error during clipping: {str(exc)[:400]}")


async def cmd_instagram(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _guard(update):
        return
    import os
    root_dir = Path(__file__).resolve().parents[2]
    instapost_dir = root_dir / "ai clipper best" / "instapost"
    import sys
    if str(instapost_dir) not in sys.path and instapost_dir.is_dir():
        sys.path.insert(0, str(instapost_dir))

    cfg = get_config()
    official_ok = bool(cfg.ig_user_id and cfg.ig_access_token)

    private_ok = False
    try:
        from instapost.private import PrivateInstagram
        p = PrivateInstagram()
        private_ok = p.configured()
    except Exception:
        pass

    text = "📸 *Instagram Publishing Status:*\n\n"
    if official_ok:
        text += f"• *Official Meta Graph API:* ✅ Configured (`IG_USER_ID: {cfg.ig_user_id}`)\n"
    else:
        text += "• *Official Meta Graph API:* ❌ Not set (`IG_USER_ID`, `IG_ACCESS_TOKEN`)\n"

    if private_ok:
        text += "• *Direct Phone API (instagrapi):* ✅ Ready to upload local MP4s\n"
    else:
        text += "• *Direct Phone API (instagrapi):* ❌ Needs `IG_USERNAME`, `IG_PASSWORD`, `INSTAPOST_I_ACCEPT_BAN_RISK=yes`\n"

    text += (
        "\n*Setup Options:*\n"
        "1. *Direct Phone API (Instant):* Set `IG_USERNAME` and `IG_PASSWORD` in `.env`\n"
        "2. *Official Meta API (Zero Risk):* Set `IG_USER_ID` and `IG_ACCESS_TOKEN` in `.env`"
    )
    await update.effective_message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


async def cmd_approve(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _guard(update):
        return
    video_id = _arg_id(context.args) or _latest_pending()
    if not video_id:
        await update.effective_message.reply_text("Koi pending video nahi hai. Pehle /generate karein.")
        return
    await _do_upload(update.effective_chat.id, context, video_id)


async def cmd_reject(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _guard(update):
        return
    video_id = _arg_id(context.args) or _latest_pending()
    if not video_id:
        await update.effective_message.reply_text("Koi pending video nahi hai.")
        return
    row = db.get_video(video_id) or {}
    db.update_video(video_id, status="rejected", error="rejected by user in Telegram")
    await update.effective_message.reply_text(f"🗑 #{video_id} rejected. File: `{row.get('video_path','')}`",
                                              parse_mode=ParseMode.MARKDOWN)


async def cmd_regenerate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _guard(update):
        return
    video_id = _arg_id(context.args) or _latest_pending()
    niche = setting_niche()
    if video_id:
        row = db.get_video(video_id) or {}
        niche = row.get("niche") or niche
    await _run_generation(update.effective_chat.id, context, niche, note=f"regenerate {video_id or ''}")


async def cmd_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _guard(update):
        return
    if not context.args:
        await update.effective_message.reply_text(
            f"Daily slots: `{', '.join(setting_schedule())}`\n"
            "Set one or more: `/schedule 08:30,19:30`  (morning + night)\n"
            "Single slot is fine too: `/schedule 19:30`",
            parse_mode=ParseMode.MARKDOWN,
        )
        return
    raw = " ".join(context.args).replace(" ", "")
    from .scheduler import _normalise_time  # local import avoids a cycle

    times: list[str] = []
    for chunk in raw.split(","):
        normalised = _normalise_time(chunk)
        if not normalised:
            await update.effective_message.reply_text(
                f"`{chunk}` galat hai. Example: `/schedule 08:30,19:30`", parse_mode=ParseMode.MARKDOWN
            )
            return
        if normalised not in times:
            times.append(normalised)
    db.set_setting("schedule_times", ",".join(times))
    db.set_setting("schedule_time", times[0])  # keep the legacy key in sync
    reschedule_note = ""
    try:
        from .scheduler import reschedule_jobs

        reschedule_jobs()
        reschedule_note = " (scheduler updated)"
    except Exception as exc:  # noqa: BLE001
        reschedule_note = f" (restart to apply: {exc})"
    await update.effective_message.reply_text(
        f"⏰ Daily slots: `{', '.join(times)}`{reschedule_note}\n"
        f"Rotation of niches: `{get_config().niche_rotate}` (NICHE_ROTATE in .env)",
        parse_mode=ParseMode.MARKDOWN,
    )


async def cmd_platforms(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Choose where videos go: /platforms youtube,instagram"""
    if not await _guard(update):
        return
    health = platform_health()
    if not context.args:
        current = ", ".join(platform_list())
        lines = [f"Platforms: `{current}`", ""]
        for name, state in health.items():
            lines.append(f"• {name}: {state}")
        lines.append("\nSet with `/platforms youtube` or `/platforms youtube,instagram`")
        await update.effective_message.reply_text("\n".join(lines), parse_mode=ParseMode.MARKDOWN)
        return
    wanted = [p.strip().lower() for p in " ".join(context.args).split(",") if p.strip()]
    valid = [p for p in wanted if p in {"youtube", "instagram"}]
    if not valid:
        await update.effective_message.reply_text("Options: `youtube`, `instagram` (comma separated)",
                                                  parse_mode=ParseMode.MARKDOWN)
        return
    db.set_setting("platforms", ",".join(valid))
    lines = [f"✅ Platforms set to `{', '.join(valid)}`"]
    for name in valid:
        if platform_health().get(name) != "ready":
            lines.append(f"⚠️ {name}: {platform_health().get(name)}")
    await update.effective_message.reply_text("\n".join(lines), parse_mode=ParseMode.MARKDOWN)


async def cmd_mode(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """facts (10-15 s single fact) or story (~60 s narrative)."""
    if not await _guard(update):
        return
    cfg = get_config()
    if context.args and context.args[0].lower() in {"story", "facts"}:
        db.set_setting("video_mode", context.args[0].lower())
    mode = setting_mode()
    profile = cfg.profile()
    if mode == "story":
        detail = (
            f"Target: ~{cfg.story_target_words} words ≈ {cfg.story_target_seconds:.0f}s "
            f"(limit {profile.max_duration:.0f}s, up to {profile.clip_count} shots).\n"
            "Har video ek kahani hogi: hook → setup → twist → payoff."
        )
    else:
        detail = (f"Target: {profile.min_words}-{profile.max_words} words ≈ 10-15s "
                  f"(limit {profile.max_duration:.0f}s, {profile.clip_count} shots).")
    await update.effective_message.reply_text(
        f"🎬 Video mode: `{mode}`\n{detail}\n\nSwitch: `/mode story` · `/mode facts`",
        parse_mode=ParseMode.MARKDOWN,
    )


async def cmd_voiceprovider(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Pick the narration engine: free local engines first, ElevenLabs optional."""
    if not await _guard(update):
        return
    cfg = get_config()
    if not context.args:
        await update.effective_message.reply_text(await usage_report(cfg), parse_mode=ParseMode.MARKDOWN)
        return
    choice = context.args[0].lower()
    if choice not in {"auto", "kokoro", "piper", "local", "edge", "elevenlabs"}:
        await update.effective_message.reply_text(
            "Options: `auto`, `kokoro`, `piper`, `local`, `edge`, `elevenlabs`", parse_mode=ParseMode.MARKDOWN)
        return
    db.set_setting("voice_provider", choice)
    cfg.voice_provider = choice
    from .voice import provider_for

    actual = provider_for(cfg)
    note = ""
    if actual in {"kokoro", "piper"}:
        note = ("\n✅ 100% free & local - no key, no quota. Model pehli baar download hoga, "
                "phir offline chalega.")
    elif choice == "elevenlabs" and not cfg.elevenlabs_api_key:
        note = f"\n⚠️ ELEVENLABS_API_KEY missing → `{actual}` will be used."
    elif choice == "elevenlabs" and cfg.elevenlabs_api_key:
        note = ("\nℹ️ ElevenLabs free tier = non-commercial + attribution. "
                "Monetized channel needs their paid plan.")
    await update.effective_message.reply_text(
        f"🎙 Voice provider: `{choice}` → running `{actual}`{note}", parse_mode=ParseMode.MARKDOWN)


async def cmd_trends(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show what is trending right now (Google Trends + Wikipedia) so you can pick a topic."""
    if not await _guard(update):
        return
    cfg = get_config()
    geo = (context.args[0].upper() if context.args else cfg.trends_geo)
    niche = setting_niche()
    msg = await update.effective_message.reply_text(f"🔎 Fetching trends ({geo}, niche `{niche}`)…",
                                                    parse_mode=ParseMode.MARKDOWN)
    client = TrendClient(cfg)
    try:
        google = await client.google_trends(geo, 8)
        mostread = await client.wikipedia_mostread(niche)
        onthisday = await client.wikipedia_onthisday(niche)
    except Exception as exc:  # noqa: BLE001
        await msg.edit_text(f"❌ Trends fetch failed: {exc}")
        return
    finally:
        await client.aclose()

    def fmt(items, label, limit=6):
        if not items:
            return f"*{label}*: nothing usable right now"
        body = "\n".join(
            f"• {html.escape(i.title[:70])}" + (f" _{i.extra.get('traffic')}_" if i.extra.get("traffic") else "")
            for i in items[:limit]
        )
        return f"*{label}*\n{body}"

    text = "\n\n".join([
        fmt(google, f"Google Trends ({geo})"),
        fmt(mostread, "Wikipedia most-read"),
        fmt(onthisday, "On this day"),
    ])
    text += "\n\nNext `/generate` automatically uses the best of these (USE_TRENDS=on)."
    await msg.edit_text(text[:3800], parse_mode=ParseMode.MARKDOWN)


async def cmd_niche(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _guard(update):
        return
    if not context.args:
        await update.effective_message.reply_text(f"Current niche: `{setting_niche()}`\nOptions: {', '.join(NICHES)}",
                                                  parse_mode=ParseMode.MARKDOWN)
        return
    niche = context.args[0].lower()
    if niche not in NICHES:
        await update.effective_message.reply_text(f"Options: {', '.join(NICHES)}")
        return
    db.set_setting("niche", niche)
    await update.effective_message.reply_text(f"✅ Niche set to `{niche}`", parse_mode=ParseMode.MARKDOWN)


async def cmd_auto(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _guard(update):
        return
    if not context.args:
        await update.effective_message.reply_text(f"Auto mode: `{setting_auto()}`")
        return
    value = context.args[0].lower() in {"on", "1", "true", "yes"}
    db.set_setting("auto_mode", "1" if value else "0")
    await update.effective_message.reply_text(
        f"🤖 Auto mode `{'ON' if value else 'OFF'}`"
        + (" — videos bina approval ke upload ho jayenge." if value else " — preview ke baad /approve chahiye."),
        parse_mode=ParseMode.MARKDOWN,
    )


async def cmd_voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _guard(update):
        return
    cfg = get_config()
    if not context.args or context.args[0].lower() == "list":
        from .voice import ELEVENLABS_VOICES, VOICES, provider_for

        provider = provider_for(cfg)
        txt = f"Provider: `{provider}` · current voice: `{setting_voice() or 'auto-rotate'}`\n\n"
        if provider in {"kokoro", "piper"}:
            from .tts_local import DEFAULT_KOKORO_VOICES, KOKORO_VOICES, PIPER_VOICES

            txt += ("*Free local voices* (no key, no quota)\n"
                    "*kokoro*: " + ", ".join(f"`{v}`" for v in DEFAULT_KOKORO_VOICES) + "\n")
            for niche, voices in KOKORO_VOICES.items():
                txt += f"  {niche}: " + ", ".join(f"`{v}`" for v in voices) + "\n"
            txt += "*piper*: " + ", ".join(f"`{v}`" for v in PIPER_VOICES) + "\n"
        if provider == "elevenlabs":
            txt += "ElevenLabs voices (name → id):\n"
            for name, vid in ELEVENLABS_VOICES.items():
                txt += f"• `{name}` — `{vid}`\n"
            txt += ("\nSet your own: `ELEVENLABS_VOICE_ID=` in .env (or `/voice <voice_id>`).\n"
                    "⚠️ Free tier is non-commercial; monetized use needs a paid plan.\n")
        for niche, voices in VOICES.items():
            txt += f"*{niche}*: " + ", ".join(f"`{v}`" for v in voices) + "\n"
        await update.effective_message.reply_text(txt[:3800] + "\n`/voice <name>` or `/voice auto`",
                                                  parse_mode=ParseMode.MARKDOWN)
        return
    choice = context.args[0]
    db.set_setting("voice", "" if choice.lower() == "auto" else choice)
    await update.effective_message.reply_text(f"🎙 Voice: `{setting_voice() or 'auto-rotate'}`",
                                              parse_mode=ParseMode.MARKDOWN)


async def cmd_queue(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _guard(update):
        return
    rows = db.list_videos("pending,approved,scheduled,upload_failed,rendering", 10)
    if not rows:
        await update.effective_message.reply_text("Queue khali hai.")
        return
    lines = []
    for r in rows:
        lines.append(f"#{r['id']} · {r['status']} · {r.get('niche')} · {r.get('title') or r.get('topic') or ''}"[:120])
    await update.effective_message.reply_text("📋 *Queue*\n" + "\n".join(lines), parse_mode=ParseMode.MARKDOWN)


async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _guard(update):
        return
    s = db.stats()
    by = "\n".join(f"• {k}: {v}" for k, v in sorted(s["by_status"].items()))
    last = s.get("last_upload") or {}
    text = (
        f"📊 *Stats*\n{by or '• nothing yet'}\n\n"
        f"Topics used: `{len(db.topic_fingerprints())}`\n"
        f"Uploads today: `{uploads_today()}/{get_config().yt_max_uploads_per_day}` "
        f"(quota left `{quota_left()}`)\n"
        f"Cached clips: `{db.clip_unused_count('pexels')} pexels, {db.clip_unused_count('wikimedia')} wikimedia unused`\n"
    )
    ig_rows = db.list_videos("uploaded", 5)
    ig_ok = [r for r in ig_rows if r.get("ig_media_id")]
    text += f"\nInstagram reels: `{len(ig_ok)}` (of the last {len(ig_rows)} uploads)"
    if last:
        text += f"\nLast upload: {last.get('title','')[:70]}\nhttps://youtube.com/shorts/{last.get('yt_video_id','')}"
    await update.effective_message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _guard(update):
        return
    cfg = get_config()
    voice_info = await usage_report(cfg)
    health = platform_health()
    text = (
        f"Niche: `{setting_niche()}` · slots `{', '.join(setting_schedule())}` · auto `{setting_auto()}`\n"
        f"Platforms: `{', '.join(platform_list())}`\n"
        f"YouTube: `{health.get('youtube')}` · privacy `{cfg.yt_privacy}` · disclosure `{cfg.yt_synthetic_disclosure}`\n"
        f"Instagram: `{health.get('instagram')}`\n"
        f"Music: `{cfg.music_enabled}` · CTA style `{cfg.cta_style}` · script `{cfg.script_style}`\n"
        f"Mode: `{setting_mode()}` · target `{cfg.profile().target_words}` words · "
        f"max `{cfg.profile().max_duration:.0f}s`\n\n"
        f"{voice_info}\n\n"
        f"```\n{cfg.describe()}\n```"
    )
    await update.effective_message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


async def cmd_upload(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _guard(update):
        return
    if not context.args:
        await update.effective_message.reply_text("Use: `/upload <id> [public|unlisted|private]`",
                                                  parse_mode=ParseMode.MARKDOWN)
        return
    video_id = _arg_id(context.args[:1])
    if not video_id:
        await update.effective_message.reply_text("Video id numeric hona chahiye.")
        return
    privacy = context.args[1].lower() if len(context.args) > 1 else None
    if privacy and privacy not in {"public", "unlisted", "private"}:
        privacy = None
    await _do_upload(update.effective_chat.id, context, video_id, privacy=privacy)


async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if not query:
        return
    if not await _guard(update):
        await query.answer("Unauthorised", show_alert=True)
        return
    action, _, raw_id = (query.data or "").partition(":")
    video_id = int(raw_id) if raw_id.isdigit() else 0
    await query.answer()
    if action == "approve" and video_id:
        await query.edit_message_reply_markup(reply_markup=None)
        await _do_upload(query.message.chat_id, context, video_id)
    elif action == "reject" and video_id:
        db.update_video(video_id, status="rejected", error="rejected in Telegram")
        await query.edit_message_text(f"🗑 #{video_id} rejected. /generate se naya bana lein.",
                                      parse_mode=ParseMode.MARKDOWN)
    elif action == "regen" and video_id:
        await query.edit_message_text(f"♻️ #{video_id} regenerate kar raha hoon…")
        row = db.get_video(video_id) or {}
        await _run_generation(query.message.chat_id, context, row.get("niche") or setting_niche(),
                              note=f"regenerate {video_id}")
    elif action == "ig_post":
        filename = raw_id
        await query.answer("Posting to Instagram Reel...")
        root_dir = Path(__file__).resolve().parents[2]
        autoclip_dir = root_dir / "ai clipper best" / "autoclip"
        import sys
        if str(autoclip_dir) not in sys.path and autoclip_dir.is_dir():
            sys.path.insert(0, str(autoclip_dir))
        from autoclip.notify import post_to_instagram

        target_file = None
        for cand in root_dir.rglob(filename):
            if cand.is_file():
                target_file = cand
                break
        if not target_file:
            await query.message.reply_text(f"❌ File `{filename}` not found locally.")
            return

        caption = query.message.caption or "Viral Short #shorts #reels"
        res = await asyncio.to_thread(post_to_instagram, target_file, caption=caption[:500])
        if res.get("ok"):
            await query.message.reply_text(f"🎉 Successfully posted to Instagram Reel! ID: `{res.get('reel_id')}`")
        else:
            await query.message.reply_text(f"⚠️ Instagram post failed:\n{res.get('error')}\n\nUse `/instagram` for setup instructions.")


def _arg_id(args: list[str] | None) -> int:
    if args:
        token = args[0].lstrip("#")
        if token.isdigit():
            return int(token)
    return 0


def _latest_pending() -> int:
    rows = db.list_videos("pending", 1)
    return rows[0]["id"] if rows else 0


async def cmd_cloud(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Trigger the GitHub Action for cloud rendering."""
    if not await _guard(update):
        return
    if not update.message:
        return
    cfg = get_config()
    if not getattr(cfg, "github_token", None):
        await update.message.reply_text(
            "❌ <b>GITHUB_TOKEN</b> is missing in <code>.env</code>.\n\n"
            "To use /cloud, generate a classic Personal Access Token with 'repo' scope at "
            "https://github.com/settings/tokens and add it to your .env file.",
            parse_mode=ParseMode.HTML
        )
        return
    repo = getattr(cfg, "github_repo", "Deepanshu-8126/dk_hu")
    
    await update.message.reply_text(f"🚀 Triggering cloud rendering on <b>{repo}</b>...", parse_mode=ParseMode.HTML)
    import httpx
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"https://api.github.com/repos/{repo}/actions/workflows/youtube-automation.yml/dispatches",
                headers={
                    "Accept": "application/vnd.github+json",
                    "Authorization": f"Bearer {cfg.github_token}",
                    "X-GitHub-Api-Version": "2022-11-28"
                },
                json={"ref": "main"}
            )
            if resp.status_code == 204:
                await update.message.reply_text("✅ GitHub Action triggered successfully!\n\nIt will generate and upload the video in the cloud. You can close your laptop now.")
            else:
                await update.message.reply_text(f"❌ Failed to trigger Action: HTTP {resp.status_code}\n{resp.text[:200]}")
    except Exception as e:
        await update.message.reply_text(f"❌ Request failed: {e}")


# ------------------------------------------------------------------- app setup
def build_application() -> Application:
    cfg = get_config()
    if not cfg.telegram_token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN missing in .env - create a bot with @BotFather first")
    app = (
        Application.builder()
        .token(cfg.telegram_token)
        .read_timeout(120)
        .write_timeout(600)
        .connect_timeout(30)
        .pool_timeout(60)
        .build()
    )
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_start))
    app.add_handler(CommandHandler("cloud", cmd_cloud))
    app.add_handler(CommandHandler("generate", cmd_generate))
    app.add_handler(CommandHandler("clip", cmd_clip))
    app.add_handler(CommandHandler("instagram", cmd_instagram))
    app.add_handler(CommandHandler("approve", cmd_approve))
    app.add_handler(CommandHandler("reject", cmd_reject))
    app.add_handler(CommandHandler("regenerate", cmd_regenerate))
    app.add_handler(CommandHandler("schedule", cmd_schedule))
    app.add_handler(CommandHandler("niche", cmd_niche))
    app.add_handler(CommandHandler("auto", cmd_auto))
    app.add_handler(CommandHandler("voice", cmd_voice))
    app.add_handler(CommandHandler("mode", cmd_mode))
    app.add_handler(CommandHandler("voiceprovider", cmd_voiceprovider))
    app.add_handler(CommandHandler("platforms", cmd_platforms))
    app.add_handler(CommandHandler("trends", cmd_trends))
    app.add_handler(CommandHandler("queue", cmd_queue))
    app.add_handler(CommandHandler("stats", cmd_stats))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("upload", cmd_upload))
    app.add_handler(CommandHandler("whoami", cmd_whoami))
    app.add_handler(CallbackQueryHandler(on_callback))
    return app


async def _on_startup(app: Application) -> None:
    from .scheduler import start_scheduler

    start_scheduler()
    log.info("bot started")
    try:
        cfg = get_config()
        target = cfg.telegram_chat_id or (cfg.telegram_allowed_user_ids[0] if cfg.telegram_allowed_user_ids else 0)
        if target:
            await app.bot.send_message(
                chat_id=target,
                text=(f"🤖 FactShorts Bot online.\nNiche: `{setting_niche()}` · daily `{setting_schedule()}` · "
                      f"auto `{setting_auto()}`\nUse /generate to make a video now."),
                parse_mode=ParseMode.MARKDOWN,
            )
    except Exception as exc:  # noqa: BLE001
        log.warning("startup message failed: %s", exc)


async def _on_shutdown(app: Application) -> None:
    from .scheduler import stop_scheduler

    stop_scheduler()


def run() -> None:
    setup_logging()
    db.init_db()
    app = build_application()
    app.post_init = _on_startup
    app.post_shutdown = _on_shutdown
    log.info("polling for updates…")
    app.run_polling(drop_pending_updates=True, allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    run()
