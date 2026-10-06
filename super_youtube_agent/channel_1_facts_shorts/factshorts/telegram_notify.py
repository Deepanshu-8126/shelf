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

    @staticmethod
    def detect_channel(video_path: str | Path) -> str:
        """Identify the originating channel to prevent confusion."""
        s = str(video_path).lower().replace("\\", "/")
        if "03_dark" in s or "dark_sutra" in s or "/dark" in s:
            return "chan3 (Dark Sutra)"
        if "05_vox" in s or "vox_ledger" in s or "vox_studio" in s or "/vox" in s:
            return "chan5 (The Global Ledger)"
        if "02_story" in s or "story_studio" in s or "/story" in s:
            return "chan2 (Story Studio)"
        if "04_lofi" in s or "lofi" in s:
            return "chan4 (Lofi Studio)"
        if "06_ai_clipper" in s or "autoclip" in s or "clipper" in s:
            return "chan6 (AI Clipper)"
        return "chan1 (FactShorts)"

    async def send_video(self, video_path: str | Path, caption: str = "", chat_id: int | None = None, channel: str | None = None) -> dict:
        if not self.enabled:
            log.info("[telegram disabled] video %s", video_path)
            return {}
        path = Path(video_path)
        if not path.exists():
            return await self.send_message(f"⚠️ Video file missing: {path}")

        # Ensure channel identifier is appended to eliminate confusion
        chan_badge = channel or self.detect_channel(video_path)
        if "chan" not in caption.lower() and "channel" not in caption.lower():
            if caption:
                caption = f"{caption}\n\n📺 Channel: {chan_badge}"
            else:
                caption = f"🎬 Video Ready\n\n📺 Channel: {chan_badge}"

        # Telegram Bot API enforces a hard 50 MB limit for /sendVideo
        send_path = path
        temp_compressed = None
        if path.stat().st_size > 48 * 1024 * 1024:
            log.info("Video %s is %.1f MB (>48MB Telegram limit) -> compressing for delivery",
                     path.name, path.stat().st_size / (1024 * 1024))
            temp_compressed = path.parent / f"tg_{path.stem}.mp4"
            import subprocess
            cmd = [
                "ffmpeg", "-y", "-i", str(path),
                "-c:v", "libx264", "-crf", "24", "-preset", "veryfast",
                "-c:a", "copy",
                str(temp_compressed)
            ]
            try:
                subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                if temp_compressed.exists() and temp_compressed.stat().st_size > 1000:
                    send_path = temp_compressed
            except Exception as exc:
                log.warning("Fast compression for Telegram failed: %s", exc)

        client = await self.client()
        data = {
            "chat_id": str(chat_id or self.chat_id),
            "supports_streaming": "true",
        }
        if caption:
            data["caption"] = caption[:1024]
        for attempt in range(1, 4):
            try:
                with open(send_path, "rb") as fh:
                    files = {"video": (path.name, fh, "video/mp4")}
                    resp = await client.post("/sendVideo", data=data, files=files)
                if resp.status_code == 200:
                    if temp_compressed and temp_compressed.exists():
                        try:
                            temp_compressed.unlink()
                        except Exception:
                            pass
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
