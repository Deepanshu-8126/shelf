"""
Master Multi-Channel Telegram Mission Control for Super YouTube Agent.
Enables full remote monitoring, real-time disk analytics, and on-demand
rendering across all 7 automated YouTube channels directly from Telegram.
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

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8809830963:AAG22CFChal-D13uSkNLUmCoyHD3FGvgWjY").strip()
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "6486771356").strip()
API_BASE = f"https://api.telegram.org/bot{BOT_TOKEN}"


def build_master_menu_keyboard() -> Dict[str, Any]:
    """Top-level 7-channel navigation keyboard."""
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
                    {"text": "🚀 Render Next Day (Day N)", "callback_data": "run_ch7_next"},
                    {"text": "🤖 Auto AI Viral Pick", "callback_data": "run_ch7_auto"}
                ],
                [
                    {"text": "☕ Render Java / Backend", "callback_data": "run_ch7_java"},
                    {"text": "🧠 Render AI Tools / LLMs", "callback_data": "run_ch7_ai"}
                ],
                [
                    {"text": "⬅️ Back to Main Fleet Menu", "callback_data": "cmd_matrix"}
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
                    {"text": "⬅️ Back to Main Fleet Menu", "callback_data": "cmd_matrix"}
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
                    {"text": "⬅️ Back to Main Fleet Menu", "callback_data": "cmd_matrix"}
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
                    {"text": "⬅️ Back to Main Fleet Menu", "callback_data": "cmd_matrix"}
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
                    {"text": "⬅️ Back to Main Fleet Menu", "callback_data": "cmd_matrix"}
                ]
            ]
        }


async def send_telegram_msg(
    chat_id: str,
    text: str,
    reply_markup: Optional[Dict[str, Any]] = None,
    parse_mode: str = "Markdown"
) -> None:
    """Sends Telegram message with markdown & inline buttons."""
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
            await client.post(url, json=payload)
        except Exception as e:
            print(f"⚠️ [Telegram] Send error: {e}")


async def answer_cb(cq_id: str, text: str = "") -> None:
    """Answers inline button callback query."""
    url = f"{API_BASE}/answerCallbackQuery"
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            await client.post(url, json={"callback_query_id": cq_id, "text": text})
        except Exception:
            pass


async def execute_channel_render(chat_id: str, chan_num: int, extra_args: List[str], label: str) -> None:
    """Spawns channel rendering process and alerts progress."""
    cfg = CHANNELS_CONFIG.get(chan_num, {})
    await send_telegram_msg(
        chat_id,
        f"⏳ *[Fleet Execution Triggered]*\n"
        f"📺 Target: *{cfg.get('name')}*\n"
        f"🎯 Task: `{label}`\n\n"
        f"⚙️ Running rendering pipeline in background...\n"
        f"_The video will be delivered right here once complete!_"
    )
    
    # Run in thread pool to not block asyncio
    loop = asyncio.get_running_loop()
    cmd = cfg["runner_cmd"] + extra_args
    cwd = CURRENT_DIR.parent
    
    print(f"🚀 [Master Dispatcher] Executing Ch {chan_num}: {' '.join(cmd)}")
    
    def _run():
        res = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True)
        return res
        
    res = await loop.run_in_executor(None, _run)
    
    if res.returncode == 0:
        # Check newly rendered video from channel metrics
        metrics = scan_channel_real_metrics(chan_num)
        latest = metrics.get("latest_video")
        video_note = f"\n📦 Latest Master: `{latest['name']}` ({latest['size_mb']}MB)" if latest else ""
        
        await send_telegram_msg(
            chat_id,
            f"✅ *[Render Succeeded!]*\n"
            f"📺 Channel: *{cfg.get('name')}*\n"
            f"🎯 Action: `{label}`{video_note}\n\n"
            f"Video file has been sent to your Telegram chat!",
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
    """Dispatches button clicks."""
    cq_id = cq["id"]
    data = cq.get("data", "")
    chat_id = str(cq["message"]["chat"]["id"])
    await answer_cb(cq_id, "Processing...")

    # Main Matrix / Refresh
    if data in ("cmd_matrix", "cmd_refresh"):
        matrix_text = get_live_matrix_markdown()
        await send_telegram_msg(chat_id, matrix_text, reply_markup=build_master_menu_keyboard())
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
            f"Select an action below to render or control this channel:"
        )
        await send_telegram_msg(chat_id, detail_text, reply_markup=build_channel_action_keyboard(ch_num))
        return

    # Channel 7 Specific
    if data == "run_ch7_next":
        await execute_channel_render(chat_id, 7, ["--next"], "Core Series Day N Advance")
    elif data == "run_ch7_auto":
        await execute_channel_render(chat_id, 7, ["--auto"], "Autonomous AI Viral Pick")
    elif data == "run_ch7_java":
        await execute_channel_render(chat_id, 7, ["--niche", "java"], "Java 21 Backend Architecture")
    elif data == "run_ch7_ai":
        await execute_channel_render(chat_id, 7, ["--niche", "ai_tools"], "AI Tools & Local LLMs")
    # Channel 1
    elif data == "run_ch1_demo":
        await execute_channel_render(chat_id, 1, ["--demo"], "Viral Facts Short Demo")
    elif data == "run_ch1_random":
        await execute_channel_render(chat_id, 1, [], "Random Trending Fact")
    # Channel 5
    elif data == "run_ch5_case":
        await execute_channel_render(chat_id, 5, ["--case"], "Dark Sutra True Crime Dossier")
    # Channel 3
    elif data == "run_ch3_demo":
        await execute_channel_render(chat_id, 3, ["--generate"], "Vox Geopolitical Map Short")
    elif data.startswith("run_generic_"):
        ch_num = int(data.split("_")[-1])
        await execute_channel_render(chat_id, ch_num, [], f"Channel {ch_num} Trigger")


async def handle_user_text_command(msg: Dict[str, Any]) -> None:
    """Handles text commands and custom topic inputs across all channels."""
    chat_id = str(msg["chat"]["id"])
    text = msg.get("text", "").strip()

    if text in ("/start", "/help", "/channels", "/fleet"):
        welcome = (
            "👋 *Welcome to Super YouTube Agent // Fleet Mission Control!*\n\n"
            "Aap yahan se apne saare **7 Channels** ko dynamically monitor aur control kar sakte hain:\n\n"
            "• Tap *Live 7-Channel Matrix* to inspect real videos count across all folders.\n"
            "• Tap any Channel (1 to 7) to trigger renders or switch series.\n"
            "• Or send quick commands:\n"
            "   - `/status` -> Full 7-channel storage & video matrix\n"
            "   - `/c7 <topic>` -> Render custom coding topic (Channel 7)\n"
            "   - `/c1 <topic>` -> Render custom fact short (Channel 1)\n"
            "   - `/c5 <case>` -> Render crime case dossier (Channel 5)\n"
            "   - `/c3 <topic>` -> Render Vox geopolitics explainer (Channel 3)\n"
        )
        await send_telegram_msg(chat_id, welcome, reply_markup=build_master_menu_keyboard())
        return

    if text in ("/status", "/matrix"):
        matrix_text = get_live_matrix_markdown()
        await send_telegram_msg(chat_id, matrix_text, reply_markup=build_master_menu_keyboard())
        return

    # Prefixed Channel Commands
    if text.startswith("/c7 ") or text.startswith("/coding "):
        q = text.split(" ", 1)[1].strip()
        await execute_channel_render(chat_id, 7, ["--topic", q], f"Custom Coding Topic: {q}")
        return

    if text.startswith("/c1 ") or text.startswith("/facts "):
        q = text.split(" ", 1)[1].strip()
        await execute_channel_render(chat_id, 1, ["--topic", q], f"Custom Fact Topic: {q}")
        return

    if text.startswith("/c5 ") or text.startswith("/dark "):
        q = text.split(" ", 1)[1].strip()
        await execute_channel_render(chat_id, 5, ["--topic", q], f"Custom Crime Case: {q}")
        return

    if text.startswith("/c3 ") or text.startswith("/vox "):
        q = text.split(" ", 1)[1].strip()
        await execute_channel_render(chat_id, 3, ["--topic", q], f"Custom Vox Topic: {q}")
        return

    # Fallback to Channel 7 if raw topic sent without prefix
    await execute_channel_render(chat_id, 7, ["--topic", text], f"Topic: {text}")


async def run_master_hub_listener() -> None:
    """Long polling listener for master fleet control."""
    print("=" * 70)
    print("🌐 [Super YouTube Agent] Master Telegram Mission Control Online!")
    print(f"🔑 Bot Token: {BOT_TOKEN[:8]}...{BOT_TOKEN[-4:]}")
    print(f"💬 Target Chat: {CHAT_ID}")
    print("=" * 70)

    # Initial Broadcast Matrix to phone
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
    elif "--alert" in sys.argv:
        matrix_text = get_live_matrix_markdown()
        asyncio.run(send_telegram_msg(CHAT_ID, matrix_text, reply_markup=build_master_menu_keyboard()))
        print("✓ Master 7-Channel Live Matrix broadcasted to Telegram.")
    else:
        asyncio.run(run_master_hub_listener())
