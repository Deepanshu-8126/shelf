"""
Interactive Telegram Bot Controller for Channel 7 (Coding & Tech Studio).
Enables remote control of the 100 Days Series, custom topic renders,
multi-language slot triggers, and real-time status alerts via Telegram buttons.
"""
from __future__ import annotations
import asyncio
import html
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
import httpx

CURRENT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(CURRENT_DIR))

from series_progress_tracker import (
    load_state,
    save_state,
    get_next_scheduled_slot,
    get_series_status_summary
)
from ai_curriculum_generator import curate_viral_topic
from videosynx_renderer import render_videosynx_short

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8809830963:AAG22CFChal-D13uSkNLUmCoyHD3FGvgWjY").strip()
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "6486771356").strip()
API_BASE = f"https://api.telegram.org/bot{BOT_TOKEN}"


def build_control_keyboard() -> Dict[str, Any]:
    """Builds interactive inline keyboard buttons for Telegram chat."""
    state = load_state()
    core_day = state["core_series"]["current_day"]
    sec_niche = state["secondary_series"]["active_niche"].upper()
    
    return {
        "inline_keyboard": [
            [
                {"text": f"🚀 Render Day {core_day} (Next)", "callback_data": "cmd_next"},
                {"text": "🤖 Auto AI Viral Pick", "callback_data": "cmd_auto"}
            ],
            [
                {"text": f"☕ Render {sec_niche} (Evening)", "callback_data": "cmd_secondary"},
                {"text": "🧠 Render AI Tools / LLMs", "callback_data": "cmd_ai"}
            ],
            [
                {"text": "📊 Series Brain Status", "callback_data": "cmd_status"},
                {"text": "🔄 Refresh Schedule", "callback_data": "cmd_refresh"}
            ]
        ]
    }


async def send_telegram_message(
    chat_id: str,
    text: str,
    reply_markup: Optional[Dict[str, Any]] = None,
    parse_mode: str = "Markdown"
) -> None:
    """Sends a text message with optional inline keyboard."""
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
            print(f"⚠️ [Telegram] Error sending message: {e}")


async def answer_callback_query(callback_query_id: str, text: str = "") -> None:
    """Acknowledges an inline button click to stop the loading spinner."""
    url = f"{API_BASE}/answerCallbackQuery"
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            await client.post(url, json={"callback_query_id": callback_query_id, "text": text})
        except Exception:
            pass


async def handle_render_request(chat_id: str, query: str, context_label: str) -> None:
    """Orchestrates video synthesis, status alert, and delivery to Telegram."""
    await send_telegram_message(
        chat_id,
        f"⏳ *[Coding Studio Initiated]*\n"
        f"🎯 Context: `{context_label}`\n"
        f"🔍 Query: `{query}`\n\n"
        f"⚙️ Synthesizing line-anchored lesson, Kokoro Hinglish voice, and Cherry MX Foley audio...\n"
        f"_Estimated render time: ~30-45 seconds._"
    )
    
    try:
        out_video = await render_videosynx_short(query)
        
        # After render completes (render_videosynx_short already sends the video via send_to_telegram.py)
        summary = get_series_status_summary()
        await send_telegram_message(
            chat_id,
            f"✅ *[Render Complete & Delivered!]*\n\n"
            f"{summary}",
            reply_markup=build_control_keyboard()
        )
    except Exception as e:
        await send_telegram_message(
            chat_id,
            f"❌ *[Render Error]*: `{str(e)[:150]}`\n"
            f"Please check console logs or try another topic.",
            reply_markup=build_control_keyboard()
        )


async def process_update(update: Dict[str, Any]) -> None:
    """Dispatches incoming messages and callback queries."""
    # 1. Handle Inline Button Callbacks
    if "callback_query" in update:
        cq = update["callback_query"]
        cq_id = cq["id"]
        from_id = str(cq["from"]["id"])
        data = cq.get("data", "")
        chat_id = str(cq["message"]["chat"]["id"])
        
        await answer_callback_query(cq_id, "Command received!")
        
        if data == "cmd_next":
            slot = get_next_scheduled_slot()
            q = slot.get("query", "day 1")
            await handle_render_request(chat_id, q, f"Core Series Day {slot.get('day', 1)}")
        elif data == "cmd_auto":
            topic = curate_viral_topic()
            await handle_render_request(chat_id, topic, "Autonomous AI Viral Pick")
        elif data == "cmd_secondary":
            state = load_state()
            niche = state["secondary_series"]["active_niche"]
            topic = curate_viral_topic(niche)
            await handle_render_request(chat_id, topic, f"Secondary Slot ({niche.upper()})")
        elif data == "cmd_ai":
            topic = curate_viral_topic("ai_tools")
            await handle_render_request(chat_id, topic, "AI Tools & Local LLMs")
        elif data in ("cmd_status", "cmd_refresh"):
            summary = get_series_status_summary()
            await send_telegram_message(chat_id, summary, reply_markup=build_control_keyboard())
        return

    # 2. Handle Text Messages
    if "message" in update and "text" in update["message"]:
        msg = update["message"]
        chat_id = str(msg["chat"]["id"])
        text = msg["text"].strip()
        
        if text.startswith("/start") or text.startswith("/help"):
            welcome = (
                "👋 *Welcome to Channel 7 Pedagogical Coding Studio Control!*\n\n"
                "Aap yahan se series progression aur multi-language shorts ko direct control kar sakte hain:\n\n"
                "• Tap *Render Day N* to produce the next sequential episode in the 100 Days playlist.\n"
                "• Tap *Auto AI Viral Pick* to let Gemini scout a trending topic.\n"
                "• Or *simply send any topic name* (e.g. `Java 21 Virtual Threads` or `Two Sum` or `FastAPI CRUD`)."
            )
            await send_telegram_message(chat_id, welcome, reply_markup=build_control_keyboard())
            return
            
        if text.startswith("/status"):
            summary = get_series_status_summary()
            await send_telegram_message(chat_id, summary, reply_markup=build_control_keyboard())
            return
            
        if text.startswith("/next"):
            slot = get_next_scheduled_slot()
            q = slot.get("query", "day 1")
            await handle_render_request(chat_id, q, f"Core Series Day {slot.get('day', 1)}")
            return
            
        if text.startswith("/auto"):
            topic = curate_viral_topic()
            await handle_render_request(chat_id, topic, "Autonomous AI Viral Pick")
            return

        if text.startswith("/niche"):
            parts = text.split(maxsplit=1)
            niche = parts[1] if len(parts) > 1 else "ai_tools"
            topic = curate_viral_topic(niche)
            await handle_render_request(chat_id, topic, f"Niche: {niche.upper()}")
            return

        # Any raw topic typed by user
        clean_topic = text.lstrip("/topic ").strip()
        if clean_topic:
            await handle_render_request(chat_id, clean_topic, "Custom User Topic")


async def run_bot_listener() -> None:
    """Long polling event loop for interactive Telegram control."""
    print("=" * 65)
    print("🤖 [Telegram Controller] Starting long-poll listener for Channel 7...")
    print(f"🔑 Bot Token: {BOT_TOKEN[:8]}...{BOT_TOKEN[-4:]}")
    print(f"💬 Target Chat ID: {CHAT_ID}")
    print("=" * 65)
    
    # Broadcast startup dashboard
    summary = get_series_status_summary()
    await send_telegram_message(
        CHAT_ID,
        f"🟢 *[Coding Studio Controller Online]*\n\n{summary}",
        reply_markup=build_control_keyboard()
    )
    
    offset = 0
    async with httpx.AsyncClient(timeout=30.0) as client:
        while True:
            try:
                resp = await client.get(f"{API_BASE}/getUpdates", params={"offset": offset, "timeout": 20})
                if resp.status_code == 200:
                    data = resp.json()
                    for upd in data.get("result", []):
                        offset = upd["update_id"] + 1
                        await process_update(upd)
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"⚠️ [Telegram Poll] Error: {e}")
                await asyncio.sleep(4.0)
            await asyncio.sleep(0.5)


if __name__ == "__main__":
    if "--status" in sys.argv:
        print(get_series_status_summary())
    elif "--alert" in sys.argv:
        summary = get_series_status_summary()
        asyncio.run(send_telegram_message(CHAT_ID, summary, reply_markup=build_control_keyboard()))
        print("✓ Alert broadcasted to Telegram.")
    else:
        asyncio.run(run_bot_listener())
