"""
Master Multi-Channel Telegram Mission Control & Stepper Engine for Super YouTube Agent.
Enables full remote monitoring, real-time disk analytics, GitHub runner quota tracking,
interactive script and duration previews, YouTube metadata/tags curation, and on-demand rendering
across all 7 automated YouTube channels directly from Telegram.
"""
from __future__ import annotations
import asyncio
import html
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
import httpx

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

CURRENT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(CURRENT_DIR))

from master_channel_registry import (
    scan_all_channels,
    scan_channel_real_metrics,
    get_live_matrix_markdown,
    CHANNELS_CONFIG
)
from cloud_and_youtube_controller import (
    get_github_quota_summary,
    get_youtube_token_status,
    generate_interactive_script_preview,
    format_full_telemetry_card,
    record_workflow_execution,
    AVG_RENDER_MINS_PER_VIDEO
)

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8809830963:AAG22CFChal-D13uSkNLUmCoyHD3FGvgWjY").strip()
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "6486771356").strip()
API_BASE = f"https://api.telegram.org/bot{BOT_TOKEN}"

# Interactive Stepper Drafts per chat
USER_DRAFTS: Dict[str, Dict[str, Any]] = {}


def build_master_menu_keyboard() -> Dict[str, Any]:
    """Top-level 7-channel navigation keyboard with quota & publishing controls."""
    return {
        "inline_keyboard": [
            [
                {"text": "🎬 1. Facts Shorts", "callback_data": "menu_ch_1"},
                {"text": "🕹️ 2. Story Studio", "callback_data": "menu_ch_2"}
            ],
            [
                {"text": "🌐 3. Vox Geopolitics", "callback_data": "menu_ch_3"},
                {"text": "☕ 4. Lofi Ambient", "callback_data": "menu_ch_4"}
            ],
            [
                {"text": "🕵️ 5. Dark Sutra Crime", "callback_data": "menu_ch_5"},
                {"text": "✂️ 6. AI Clipper", "callback_data": "menu_ch_6"}
            ],
            [
                {"text": "💻 7. Coding & Tech Studio", "callback_data": "menu_ch_7"}
            ],
            [
                {"text": "📊 Live 7-Channel Matrix", "callback_data": "cmd_matrix"},
                {"text": "⚙️ Cloud Quota & GitHub Mins", "callback_data": "cmd_quota"}
            ],
            [
                {"text": "📺 YouTube Upload Status", "callback_data": "cmd_yt_status"},
                {"text": "🔄 Refresh All Channels", "callback_data": "cmd_refresh"}
            ]
        ]
    }


def build_channel_action_keyboard(chan_num: int) -> Dict[str, Any]:
    """Action buttons specific to a selected channel."""
    cfg = CHANNELS_CONFIG.get(chan_num, {})
    name = cfg.get("name", f"Channel {chan_num}")
    
    if chan_num == 7:
        return {
            "inline_keyboard": [
                [
                    {"text": "🚀 Render Next Day in Series", "callback_data": "run_ch7_next"},
                    {"text": "🤖 Auto AI Viral Pick", "callback_data": "run_ch7_auto"}
                ],
                [
                    {"text": "☕ Java 21 Backend", "callback_data": "run_ch7_java"},
                    {"text": "🧠 AI Tools & Local LLMs", "callback_data": "run_ch7_ai"}
                ],
                [
                    {"text": "📊 Series Status", "callback_data": "status_ch7_series"},
                    {"text": "⬅️ Back to Fleet Menu", "callback_data": "cmd_matrix"}
                ]
            ]
        }
    elif chan_num == 1:
        return {
            "inline_keyboard": [
                [
                    {"text": "🚀 Render Facts Demo Short", "callback_data": "run_ch1_demo"},
                    {"text": "🎲 Random Viral Fact", "callback_data": "run_ch1_random"}
                ],
                [
                    {"text": "⬅️ Back to Fleet Menu", "callback_data": "cmd_matrix"}
                ]
            ]
        }
    elif chan_num == 5:
        return {
            "inline_keyboard": [
                [
                    {"text": "🕵️ Render Dark Crime Case", "callback_data": "run_ch5_case"}
                ],
                [
                    {"text": "⬅️ Back to Fleet Menu", "callback_data": "cmd_matrix"}
                ]
            ]
        }
    elif chan_num == 3:
        return {
            "inline_keyboard": [
                [
                    {"text": "🌐 Render Vox Map Explainer", "callback_data": "run_ch3_demo"}
                ],
                [
                    {"text": "⬅️ Back to Fleet Menu", "callback_data": "cmd_matrix"}
                ]
            ]
        }
    else:
        return {
            "inline_keyboard": [
                [
                    {"text": f"▶️ Trigger {name[:18]}", "callback_data": f"run_generic_{chan_num}"}
                ],
                [
                    {"text": "⬅️ Back to Fleet Menu", "callback_data": "cmd_matrix"}
                ]
            ]
        }


def build_script_preview_keyboard(chat_id: str) -> Dict[str, Any]:
    """Interactive stepper buttons: duration selectors, YouTube toggle, confirm & cancel."""
    draft = USER_DRAFTS.get(chat_id, {})
    cur_dur = draft.get("duration", 45)
    upload_yt = draft.get("upload_yt", False)

    dur_30 = "🔘 30s" if cur_dur == 30 else "⚪ 30s"
    dur_45 = "🔘 45s" if cur_dur == 45 else "⚪ 45s"
    dur_60 = "🔘 60s" if cur_dur == 60 else "⚪ 60s"
    yt_toggle = "✅ Auto-Upload to YT: ON" if upload_yt else "⭕ Auto-Upload to YT: OFF"

    return {
        "inline_keyboard": [
            [
                {"text": dur_30, "callback_data": "draft_dur_30"},
                {"text": dur_45, "callback_data": "draft_dur_45"},
                {"text": dur_60, "callback_data": "draft_dur_60"}
            ],
            [
                {"text": yt_toggle, "callback_data": "draft_toggle_yt"}
            ],
            [
                {"text": "🚀 Confirm & Render Video", "callback_data": "draft_confirm_render"},
                {"text": "❌ Cancel", "callback_data": "draft_cancel"}
            ]
        ]
    }


def format_script_stepper_card(draft: Dict[str, Any]) -> str:
    """Formats full pedagogical script breakdown & YouTube SEO preview."""
    topic = draft.get("topic", "Python High-Performance Generators")
    duration = draft.get("duration", 45)
    upload_yt = draft.get("upload_yt", False)
    chan_num = draft.get("chan_num", 7)
    cfg = CHANNELS_CONFIG.get(chan_num, {})
    chan_name = cfg.get("name", f"Channel {chan_num}")

    preview = generate_interactive_script_preview(topic, duration)
    tags_str = " ".join([f"#{t}" for t in preview["youtube_tags"][:6]])

    card = (
        f"🎬 *STEPPER: SCRIPT & DURATION PREVIEW*\n"
        f"📺 Channel: *{chan_name}*\n"
        f"📝 Topic: *{topic}*\n"
        f"⏱️ Target Duration: *{duration}s*\n\n"
        f"🧠 *Pedagogical Spoken Script Breakdown*:\n"
        f"  • {preview['spoken_summary'][0]}\n"
        f"  • {preview['spoken_summary'][1]}\n"
        f"  • {preview['spoken_summary'][2]}\n\n"
        f"🏷️ *YouTube Auto-Generated Metadata*:\n"
        f"  • *Title*: `{preview['youtube_title']}`\n"
        f"  • *Tags*: `{tags_str}`\n"
        f"  • *Voice*: `{preview['voice_lang']}`\n\n"
        f"📤 *Publishing Target*: `{'Direct YouTube Upload (Unlisted)' if upload_yt else 'Telegram Only (Review First)'}`\n\n"
        f"👇 _Duration change karne ya YouTube toggle karne ke liye niche tap karein, phir Confirm karein:_"
    )
    return card


async def send_telegram_msg(
    chat_id: str,
    text: str,
    reply_markup: Optional[Dict[str, Any]] = None,
    parse_mode: str = "Markdown"
) -> Optional[int]:
    """Sends Telegram message with markdown & inline buttons. Returns message_id."""
    url = f"{API_BASE}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode
    }
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)
        
    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            resp = await client.post(url, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                return data.get("result", {}).get("message_id")
        except Exception as e:
            print(f"⚠️ [Telegram] Send error: {e}")
    return None


async def edit_telegram_msg(
    chat_id: str,
    message_id: int,
    text: str,
    reply_markup: Optional[Dict[str, Any]] = None,
    parse_mode: str = "Markdown"
) -> bool:
    """Edits an existing Telegram message in place for smooth interactive UX."""
    url = f"{API_BASE}/editMessageText"
    payload = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": text,
        "parse_mode": parse_mode
    }
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)
        
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.post(url, json=payload)
            return resp.status_code == 200
        except Exception:
            return False


async def send_telegram_video(
    chat_id: str,
    video_path: Path,
    caption: str = "",
    reply_markup: Optional[Dict[str, Any]] = None
) -> bool:
    """Uploads and delivers real rendered MP4 video directly to Telegram."""
    if not video_path.exists():
        return False
    url = f"{API_BASE}/sendVideo"
    async with httpx.AsyncClient(timeout=180.0) as client:
        try:
            with open(video_path, "rb") as f:
                files = {"video": (video_path.name, f, "video/mp4")}
                data = {
                    "chat_id": chat_id,
                    "caption": caption[:1024],
                    "parse_mode": "Markdown"
                }
                if reply_markup:
                    data["reply_markup"] = json.dumps(reply_markup)
                resp = await client.post(url, data=data, files=files)
                return resp.status_code == 200
        except Exception as e:
            print(f"⚠️ [Telegram Video Upload Error]: {e}")
            return False


async def answer_cb(cq_id: str, text: str = "") -> None:
    """Answers inline button callback query."""
    url = f"{API_BASE}/answerCallbackQuery"
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            await client.post(url, json={"callback_query_id": cq_id, "text": text})
        except Exception:
            pass


async def start_draft_stepper(
    chat_id: str,
    chan_num: int,
    topic: str,
    extra_args: List[str],
    label: str,
    duration: int = 45
) -> None:
    """Launches interactive script preview stepper card in Telegram."""
    preview = generate_interactive_script_preview(topic, duration)
    draft = {
        "chan_num": chan_num,
        "topic": topic,
        "duration": duration,
        "upload_yt": False,
        "extra_args": extra_args,
        "label": label,
        "preview": preview,
        "message_id": None
    }
    USER_DRAFTS[chat_id] = draft
    card_text = format_script_stepper_card(draft)
    kb = build_script_preview_keyboard(chat_id)
    msg_id = await send_telegram_msg(chat_id, card_text, reply_markup=kb)
    draft["message_id"] = msg_id


async def execute_channel_render(
    chat_id: str,
    chan_num: int,
    extra_args: List[str],
    label: str,
    upload_yt: bool = False,
    preview_meta: Optional[Dict[str, Any]] = None
) -> None:
    """Spawns channel rendering process, calculates quota, and delivers video."""
    cfg = CHANNELS_CONFIG.get(chan_num, {})
    
    # Deduct estimated GitHub Actions compute minutes
    record_workflow_execution(AVG_RENDER_MINS_PER_VIDEO)
    gh_left = get_github_quota_summary()

    await send_telegram_msg(
        chat_id,
        f"⏳ *[Fleet Execution Started]*\n"
        f"📺 Target: *{cfg.get('name')}*\n"
        f"🎯 Task: `{label}`\n\n"
        f"⚙️ *Live Pipeline Activity*:\n"
        f"  • Generating AST highlights & character typing\n"
        f"  • Synthesizing narration audio & mechanical clicks\n"
        f"  • Deducting ~1.5m GitHub runner compute\n"
        f"  • Remaining Cloud Quota: *{gh_left['remaining_mins']} mins* (~{gh_left['renders_left']} videos left)\n\n"
        f"_The video will be delivered right to your chat as soon as complete!_"
    )
    
    loop = asyncio.get_running_loop()
    cmd = cfg["runner_cmd"] + extra_args
    cwd = CURRENT_DIR.parent
    
    print(f"🚀 [Master Dispatcher] Executing Ch {chan_num}: {' '.join(cmd)}")
    
    def _run():
        res = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True)
        return res
        
    res = await loop.run_in_executor(None, _run)
    
    if res.returncode == 0:
        metrics = scan_channel_real_metrics(chan_num)
        latest = metrics.get("latest_video")
        
        caption = (
            f"🎬 *{label}*\n"
            f"📺 Channel: {cfg.get('name')}\n"
            f"🕒 Rendered & Delivered via Telegram Hub\n"
        )
        if preview_meta:
            tags_str = " ".join([f"#{t}" for t in preview_meta.get("youtube_tags", [])[:6]])
            caption += f"🏷️ {tags_str}\n"

        sent_video = False
        if latest and "path" in latest:
            vpath = Path(latest["path"])
            if vpath.exists():
                sent_video = await send_telegram_video(chat_id, vpath, caption=caption)

        yt_note = ""
        if upload_yt:
            yt_status = get_youtube_token_status()
            if yt_status["can_upload"]:
                yt_note = "\n📺 *YouTube Status*: Upload queued with SEO tags (Unlisted mode)."
            else:
                yt_note = "\n⚠️ *YouTube Notice*: Token pending (`token.json`), video delivered for manual review."

        gh_fresh = get_github_quota_summary()
        delivery_note = "📦 *Master Video Delivered Above* 👆" if sent_video else "📦 *Master Video Saved to Disk*"

        await send_telegram_msg(
            chat_id,
            f"✅ *[Render Succeeded!]*\n"
            f"📺 Channel: *{cfg.get('name')}*\n"
            f"🎯 Action: `{label}`\n"
            f"{delivery_note}\n\n"
            f"🐙 *GitHub Actions Quota Remaining*: *{gh_fresh['remaining_mins']} mins* (`{gh_fresh['percent_left']}%`)\n"
            f"🎬 *Videos You Can Still Render*: *~{gh_fresh['renders_left']} Shorts*{yt_note}",
            reply_markup=build_master_menu_keyboard()
        )
    else:
        err_msg = (res.stderr or res.stdout or "Process exited with error")[:180]
        await send_telegram_msg(
            chat_id,
            f"⚠️ *[Render Notice]* (Exit code {res.returncode}):\n"
            f"`{err_msg}`",
            reply_markup=build_channel_action_keyboard(chan_num)
        )


async def handle_callback_query(cq: Dict[str, Any]) -> None:
    """Dispatches button clicks across the entire hub."""
    cq_id = cq["id"]
    data = cq.get("data", "")
    chat_id = str(cq["message"]["chat"]["id"])
    await answer_cb(cq_id, "Processing...")

    # Main Matrix / Refresh
    if data in ("cmd_matrix", "cmd_refresh"):
        matrix_text = get_live_matrix_markdown()
        await send_telegram_msg(chat_id, matrix_text, reply_markup=build_master_menu_keyboard())
        return

    # Quota & GitHub Minutes
    if data == "cmd_quota":
        q_card = format_full_telemetry_card()
        await send_telegram_msg(chat_id, q_card, reply_markup=build_master_menu_keyboard())
        return

    # YouTube Status Card
    if data == "cmd_yt_status":
        yt = get_youtube_token_status()
        card = (
            f"📺 *YOUTUBE PUBLISHING INTELLIGENCE*\n\n"
            f"• Connection Status: {yt['icon']} *{yt['status_text']}*\n"
            f"• Can Auto-Upload: `{'YES (Direct API Ready)' if yt['can_upload'] else 'NO (Requires OAuth Token)'}`\n"
            f"• Default Privacy Mode: `Unlisted`\n"
            f"• Auto SEO Tagging: `Active (Multi-niche hashtags generated)`\n\n"
            f"💡 *Setup Tip*:\n"
            f"Jab aap video render confirm karte hain, 'Auto-Upload to YT' button toggle karke direct upload trigger kar sakte hain!"
        )
        await send_telegram_msg(chat_id, card, reply_markup=build_master_menu_keyboard())
        return

    # Interactive Draft Stepper Callbacks
    if data in ("draft_dur_30", "draft_dur_45", "draft_dur_60"):
        new_dur = int(data.split("_")[-1])
        if chat_id in USER_DRAFTS:
            USER_DRAFTS[chat_id]["duration"] = new_dur
            USER_DRAFTS[chat_id]["preview"] = generate_interactive_script_preview(
                USER_DRAFTS[chat_id]["topic"], new_dur
            )
            card_text = format_script_stepper_card(USER_DRAFTS[chat_id])
            kb = build_script_preview_keyboard(chat_id)
            mid = USER_DRAFTS[chat_id].get("message_id")
            if mid:
                await edit_telegram_msg(chat_id, mid, card_text, reply_markup=kb)
            else:
                await send_telegram_msg(chat_id, card_text, reply_markup=kb)
        return

    if data == "draft_toggle_yt":
        if chat_id in USER_DRAFTS:
            USER_DRAFTS[chat_id]["upload_yt"] = not USER_DRAFTS[chat_id].get("upload_yt", False)
            card_text = format_script_stepper_card(USER_DRAFTS[chat_id])
            kb = build_script_preview_keyboard(chat_id)
            mid = USER_DRAFTS[chat_id].get("message_id")
            if mid:
                await edit_telegram_msg(chat_id, mid, card_text, reply_markup=kb)
            else:
                await send_telegram_msg(chat_id, card_text, reply_markup=kb)
        return

    if data == "draft_confirm_render":
        if chat_id in USER_DRAFTS:
            d = USER_DRAFTS.pop(chat_id)
            extra_args = list(d.get("extra_args", []))
            await execute_channel_render(
                chat_id,
                d["chan_num"],
                extra_args,
                d["label"],
                upload_yt=d.get("upload_yt", False),
                preview_meta=d.get("preview")
            )
        else:
            await send_telegram_msg(chat_id, "⚠️ No active draft found. Please select an option from the menu.", reply_markup=build_master_menu_keyboard())
        return

    if data == "draft_cancel":
        USER_DRAFTS.pop(chat_id, None)
        await send_telegram_msg(chat_id, "🚫 Draft cancelled. Returned to main fleet menu.", reply_markup=build_master_menu_keyboard())
        return

    # Channel Menu Pickers
    if data.startswith("menu_ch_"):
        ch_num = int(data.split("_")[-1])
        m = scan_channel_real_metrics(ch_num)
        latest = m.get("latest_video")
        l_str = f"`{latest['name']}` ({latest['size_mb']}MB on {latest['modified']})" if latest else "_No renders yet_"
        
        extra_str = ""
        if ch_num == 7:
            extra_str = f"\n🎯 *Series Progression*: Day {m.get('extra_meta', {}).get('current_day', 1)} of 100"

        detail_text = (
            f"📺 *{m['name'].upper()}*\n"
            f"🔖 Format: `{m['format']}`\n"
            f"📁 Folder: `{m['folder']}`\n"
            f"📦 *Total Rendered*: `{m['total_videos']} videos` ({m['total_storage_mb']}MB)\n"
            f"🎬 *Latest Video*: {l_str}{extra_str}\n\n"
            f"Select an action below to preview script, adjust duration, or render:"
        )
        await send_telegram_msg(chat_id, detail_text, reply_markup=build_channel_action_keyboard(ch_num))
        return

    # Channel 7 Specific Stepper Launches
    if data == "run_ch7_next":
        m = scan_channel_real_metrics(7)
        cur_day = m.get("extra_meta", {}).get("current_day", 1)
        next_day = cur_day + 1
        topic = f"Day {next_day}: Yield Generators & Memory Streaming"
        await start_draft_stepper(chat_id, 7, topic, ["--next"], f"Core Series Day {next_day}")
    elif data == "run_ch7_auto":
        await start_draft_stepper(chat_id, 7, "AI Local LLMs vs Cloud APIs", ["--auto"], "Autonomous AI Viral Pick")
    elif data == "run_ch7_java":
        await start_draft_stepper(chat_id, 7, "Java 21 Virtual Threads Architecture", ["--niche", "java"], "Java 21 Backend Architecture")
    elif data == "run_ch7_ai":
        await start_draft_stepper(chat_id, 7, "Ollama DeepSeek Local Model Integration", ["--niche", "ai_tools"], "AI Tools & LLMs")
    elif data == "status_ch7_series":
        from series_progress_tracker import get_series_status_summary
        status_txt = get_series_status_summary()
        await send_telegram_msg(chat_id, f"📊 *[Channel 7 Progression Status]*\n\n`{status_txt}`", reply_markup=build_channel_action_keyboard(7))

    # Channel 1
    elif data == "run_ch1_demo":
        await start_draft_stepper(chat_id, 1, "Crazy Facts: Honey Never Spoils", ["--demo"], "Viral Facts Short Demo")
    elif data == "run_ch1_random":
        await start_draft_stepper(chat_id, 1, "Mind-Bending Psychology Facts", [], "Random Trending Fact")
    # Channel 5
    elif data == "run_ch5_case":
        await start_draft_stepper(chat_id, 5, "Dark Sutra: Mystery of Dyatlov Pass", ["--case"], "Dark Sutra Crime Dossier")
    # Channel 3
    elif data == "run_ch3_demo":
        await start_draft_stepper(chat_id, 3, "Vox Map: Why 90% of Australia is Empty", ["--generate"], "Vox Geopolitical Map Short")
    elif data.startswith("run_generic_"):
        ch_num = int(data.split("_")[-1])
        await execute_channel_render(chat_id, ch_num, [], f"Channel {ch_num} Trigger")


async def handle_user_text_command(msg: Dict[str, Any]) -> None:
    """Handles text commands, duration adjustments, and custom topic inputs."""
    chat_id = str(msg["chat"]["id"])
    text = msg.get("text", "").strip()

    if text in ("/start", "/help", "/channels", "/fleet"):
        welcome = (
            "👋 *Welcome to Super YouTube Agent // Fleet Mission Control!*\n\n"
            "Aap yahan se apne saare **7 Channels** ko dynamically monitor aur control kar sakte hain:\n\n"
            "• Tap *Live 7-Channel Matrix* to inspect real videos across all folders.\n"
            "• Tap *⚙️ Cloud Quota* to see remaining GitHub minutes and video capacity.\n"
            "• Tap any Channel to adjust duration (`30s/45s/60s`) and preview spoken script!\n\n"
            "Quick Commands:\n"
            "   - `/quota` -> GitHub Actions minutes left & video render capacity\n"
            "   - `/status` -> Full 7-channel storage & video matrix\n"
            "   - `/c7 <topic>` -> Interactive Script preview for Channel 7\n"
            "   - `/c1 <topic>` -> Interactive Script preview for Channel 1\n"
            "   - `/c5 <case>` -> Crime dossier preview for Channel 5\n"
            "   - `/c3 <topic>` -> Vox geopolitics preview for Channel 3\n"
        )
        await send_telegram_msg(chat_id, welcome, reply_markup=build_master_menu_keyboard())
        return

    lower_text = text.lower()

    # 1. Analytics & Storage Matrix Intent
    if any(k in lower_text for k in ["analytics", "matrix", "status", "kitni video", "total video", "storage", "disk", "stats", "dikhao", "/status", "/matrix"]):
        matrix_text = get_live_matrix_markdown()
        await send_telegram_msg(chat_id, matrix_text, reply_markup=build_master_menu_keyboard())
        return

    # 2. GitHub Quota & Minutes Remaining Intent
    if any(k in lower_text for k in ["quota", "github", "minutes", "minute", "cloud", "kitna minute", "kitna time", "capacity", "/quota", "/github", "/minutes", "/cloud"]):
        q_card = format_full_telemetry_card()
        await send_telegram_msg(chat_id, q_card, reply_markup=build_master_menu_keyboard())
        return

    # 3. YouTube Publishing & Token Intent
    if any(k in lower_text for k in ["youtube", "yt", "upload", "token", "oauth", "/youtube", "/yt"]):
        yt = get_youtube_token_status()
        card = (
            f"📺 *YOUTUBE PUBLISHING INTELLIGENCE*\n\n"
            f"• Connection Status: {yt['icon']} *{yt['status_text']}*\n"
            f"• Can Auto-Upload: `{'YES (Direct API Ready)' if yt['can_upload'] else 'NO (Requires OAuth Token)'}`\n"
            f"• Default Privacy Mode: `Unlisted`\n"
            f"• Auto SEO Tagging: `Active (Multi-niche hashtags generated)`\n"
        )
        await send_telegram_msg(chat_id, card, reply_markup=build_master_menu_keyboard())
        return

    # 4. Series & Day Progression Intent
    if any(k in lower_text for k in ["day", "100 day", "progress", "series", "curriculum", "schedule"]):
        from series_progress_tracker import get_series_status_summary
        status_txt = get_series_status_summary()
        await send_telegram_msg(chat_id, f"📊 *[Channel 7 Progression Status]*\n\n`{status_txt}`", reply_markup=build_channel_action_keyboard(7))
        return

    # 5. Direct Channel Inquiry Intent (e.g. "ch 1", "channel 5", "vox", "lofi")
    channel_keywords = {
        1: ["ch 1", "ch1", "channel 1", "facts shorts"],
        2: ["ch 2", "ch2", "channel 2", "story studio"],
        3: ["ch 3", "ch3", "channel 3", "vox", "geopolitics"],
        4: ["ch 4", "ch4", "channel 4", "lofi", "ambient"],
        5: ["ch 5", "ch5", "channel 5", "dark sutra", "crime"],
        6: ["ch 6", "ch6", "channel 6", "clipper", "clips"],
        7: ["ch 7", "ch7", "channel 7", "coding", "python studio"]
    }
    for c_num, kws in channel_keywords.items():
        if any(kw == lower_text or lower_text.startswith(f"{kw} ") for kw in kws):
            m = scan_channel_real_metrics(c_num)
            latest = m.get("latest_video")
            l_str = f"`{latest['name']}` ({latest['size_mb']}MB)" if latest else "_No renders yet_"
            detail_text = (
                f"📺 *{m['name'].upper()}*\n"
                f"🔖 Format: `{m['format']}`\n"
                f"📦 Total Rendered: `{m['total_videos']} videos` ({m['total_storage_mb']}MB)\n"
                f"🎬 Latest: {l_str}\n\n"
                f"Action select karein:"
            )
            await send_telegram_msg(chat_id, detail_text, reply_markup=build_channel_action_keyboard(c_num))
            return

    # 6. Prefixed Channel Steppers
    if text.startswith("/c7 ") or text.startswith("/coding "):
        q = text.split(" ", 1)[1].strip()
        await start_draft_stepper(chat_id, 7, q, ["--topic", q], f"Custom Coding: {q}")
        return

    if text.startswith("/c1 ") or text.startswith("/facts "):
        q = text.split(" ", 1)[1].strip()
        await start_draft_stepper(chat_id, 1, q, ["--topic", q], f"Custom Fact: {q}")
        return

    if text.startswith("/c5 ") or text.startswith("/dark "):
        q = text.split(" ", 1)[1].strip()
        await start_draft_stepper(chat_id, 5, q, ["--topic", q], f"Custom Crime Case: {q}")
        return

    if text.startswith("/c3 ") or text.startswith("/vox "):
        q = text.split(" ", 1)[1].strip()
        await start_draft_stepper(chat_id, 3, q, ["--topic", q], f"Custom Vox Topic: {q}")
        return

    # 7. Fallback: treat any raw text/topic as Channel 7 interactive Stepper preview
    await start_draft_stepper(chat_id, 7, text, ["--topic", text], f"Topic: {text}")


async def run_master_hub_listener() -> None:
    """Long polling listener for master fleet control."""
    print("=" * 70)
    print("🌐 [Super YouTube Agent] Master Telegram Mission Control Online!")
    print(f"🔑 Bot Token: {BOT_TOKEN[:8]}...{BOT_TOKEN[-4:]}")
    print(f"💬 Target Chat: {CHAT_ID}")
    print("=" * 70)

    # Initial Broadcast Matrix & Quota to Telegram
    matrix_text = get_live_matrix_markdown()
    await send_telegram_msg(CHAT_ID, matrix_text, reply_markup=build_master_menu_keyboard())

    offset = 0
    async with httpx.AsyncClient(timeout=30.0) as client:
        while True:
            try:
                resp = await client.get(f"{API_BASE}/getUpdates", params={"offset": offset, "timeout": 20})
                if resp.status_code == 200:
                    data = resp.json()
                    for upd in data.get("result", []):
                        offset = upd["update_id"] + 1
                        if "callback_query" in upd:
                            await handle_callback_query(upd["callback_query"])
                        elif "message" in upd and "text" in upd["message"]:
                            await handle_user_text_command(upd["message"])
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"⚠️ [Master Hub Poll] Error: {e}")
                await asyncio.sleep(4.0)
            await asyncio.sleep(0.5)


if __name__ == "__main__":
    if "--matrix" in sys.argv:
        print(get_live_matrix_markdown())
    elif "--quota" in sys.argv:
        print(format_full_telemetry_card())
    elif "--alert" in sys.argv:
        # Broadcast full status card + menu keyboard to Telegram
        asyncio.run(send_telegram_msg(CHAT_ID, format_full_telemetry_card(), reply_markup=build_master_menu_keyboard()))
        print("✓ Telemetry & Quota Card successfully broadcasted to Telegram.")
    else:
        asyncio.run(run_master_hub_listener())
