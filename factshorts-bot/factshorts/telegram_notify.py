"""Minimal Telegram Bot API client (httpx) used by the worker/daemon and the bot itself.

Kept dependency-light on purpose: the scheduler must be able to notify you even if
python-telegram-bot fails to import for some reason.
"""
from __future__ import annotations

import asyncio
from pathlib import Path

import httpx

from .config import Config, get_config
from .utils import module_logger

log = module_logger("telegram")


class TelegramNotifier:
    def __init__(self, cfg: Config | None = None, token: str | None = None) -> None:
        self.cfg = cfg or get_config()
        self.token = token or self.cfg.telegram_token
        self.chat_id = self.cfg.telegram_chat_id or (
            self.cfg.telegram_allowed_user_ids[0] if self.cfg.telegram_allowed_user_ids else 0
        )
        self._client: httpx.AsyncClient | None = None

    @property
    def enabled(self) -> bool:
        return bool(self.token and self.chat_id)

    async def client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=f"https://api.telegram.org/bot{self.token}",
                timeout=httpx.Timeout(120.0, connect=15.0),
            )
        return self._client

    async def aclose(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def send_message(self, text: str, chat_id: int | None = None, parse_mode: str = "Markdown", disable_preview: bool = True) -> dict:
        if not self.enabled:
            log.info("[telegram disabled] %s", text[:200])
            return {}
        client = await self.client()
        payload = {
            "chat_id": chat_id or self.chat_id,
            "text": text[:4000],
            "parse_mode": parse_mode,
            "disable_web_page_preview": disable_preview,
        }
        for attempt in range(1, 4):
            resp = await client.post("/sendMessage", json=payload)
            if resp.status_code == 200:
                return resp.json()
            log.warning("sendMessage failed (%s): %s", resp.status_code, resp.text[:200])
            if "can't parse entities" in resp.text:
                payload.pop("parse_mode", None)
            await asyncio.sleep(1.5 * attempt)
        return {}

    async def send_video(self, video_path: str | Path, caption: str = "", chat_id: int | None = None) -> dict:
        if not self.enabled:
            log.info("[telegram disabled] video %s", video_path)
            return {}
        path = Path(video_path)
        if not path.exists():
            return await self.send_message(f"⚠️ Video file missing: {path}")
        client = await self.client()
        data = {
            "chat_id": str(chat_id or self.chat_id),
            "supports_streaming": "true",
        }
        if caption:
            data["caption"] = caption[:1000]
        for attempt in range(1, 4):
            try:
                with open(path, "rb") as fh:
                    files = {"video": (path.name, fh, "video/mp4")}
                    resp = await client.post("/sendVideo", data=data, files=files)
                if resp.status_code == 200:
                    return resp.json()
                log.warning("sendVideo failed (%s): %s", resp.status_code, resp.text[:200])
            except Exception as exc:  # noqa: BLE001
                log.warning("sendVideo error: %s", exc)
            await asyncio.sleep(2.0 * attempt)
        return await self.send_message(f"⚠️ Could not send the preview video. File: `{path}`")


async def notify(text: str) -> None:
    """Fire-and-forget helper used in except-blocks."""
    try:
        n = TelegramNotifier()
        await n.send_message(text)
        await n.aclose()
    except Exception as exc:  # noqa: BLE001
        log.error("notification failed: %s", exc)
