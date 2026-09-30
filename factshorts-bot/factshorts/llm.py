"""Free-LLM layer: Gemini API (free tier) with Groq fallback.

Both providers are called over plain HTTP with httpx so we depend on nothing heavy.
If no key is configured the callers fall back to the built-in offline fact bank /
templates, so the whole pipeline stays testable without any API key.
"""
from __future__ import annotations

import asyncio
import json
import re
from typing import Any

import httpx

from .config import Config, get_config
from .utils import module_logger

log = module_logger("llm")

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


class LLMError(RuntimeError):
    pass


def extract_json(raw: str) -> dict[str, Any]:
    """Best-effort JSON extraction from an LLM answer."""
    if not raw:
        raise LLMError("empty response")
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\s*", "", text)
        text = re.sub(r"```\s*$", "", text).strip()
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            return data
        if isinstance(data, list) and data and isinstance(data[0], dict):
            return data[0]
    except json.JSONDecodeError:
        pass
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end > start:
        candidate = text[start : end + 1]
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            # tolerate trailing commas
            candidate = re.sub(r",\s*([}\]])", r"\1", candidate)
            try:
                return json.loads(candidate)
            except json.JSONDecodeError as exc:
                raise LLMError(f"could not parse JSON: {exc}") from exc
    raise LLMError("no JSON object found in response")


class LLM:
    """Async LLM client with provider fallback chain."""

    def __init__(self, cfg: Config | None = None) -> None:
        self.cfg = cfg or get_config()
        self._client: httpx.AsyncClient | None = None
        self.last_provider: str | None = None

    # ------------------------------------------------------------------ plumbing
    async def client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.cfg.llm_timeout),
                headers={"User-Agent": "FactShortsBot/1.0"},
            )
        return self._client

    async def aclose(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    @property
    def providers(self) -> list[str]:
        order = self.cfg.llm_provider
        chain: list[str] = []
        if order == "gemini":
            chain = ["gemini"]
        elif order == "groq":
            chain = ["groq"]
        elif order == "offline":
            chain = []
        else:  # auto
            if self.cfg.gemini_api_key:
                chain.append("gemini")
            if self.cfg.groq_api_key:
                chain.append("groq")
        return chain

    @property
    def available(self) -> bool:
        return bool(self.providers)

    # ------------------------------------------------------------------ public API
    async def text(self, prompt: str, system: str = "", max_tokens: int = 900, temperature: float = 0.9) -> str:
        errors: list[str] = []
        for provider in self.providers:
            for attempt in range(1, 3):
                try:
                    if provider == "gemini":
                        out = await self._gemini(prompt, system, max_tokens, temperature)
                    else:
                        out = await self._groq(prompt, system, max_tokens, temperature)
                    self.last_provider = provider
                    return out
                except Exception as exc:  # noqa: BLE001 - fall through to next provider
                    errors.append(f"{provider}[{attempt}]: {exc}")
                    log.warning("LLM %s attempt %d failed: %s", provider, attempt, exc)
                    await asyncio.sleep(1.5 * attempt)
        raise LLMError("all LLM providers failed -> " + " | ".join(errors[:4]))

    async def json(self, prompt: str, system: str = "", max_tokens: int = 900, temperature: float = 0.9) -> dict[str, Any]:
        system_json = (system + "\n" if system else "") + (
            "Reply with a single valid JSON object and nothing else. No markdown fences."
        )
        raw = await self.text(prompt, system_json, max_tokens, temperature)
        return extract_json(raw)

    # ------------------------------------------------------------------ providers
    async def _gemini(self, prompt: str, system: str, max_tokens: int, temperature: float) -> str:
        url = GEMINI_URL.format(model=self.cfg.gemini_model)
        body: dict[str, Any] = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
                "responseMimeType": "application/json",
            },
        }
        if system:
            body["systemInstruction"] = {"parts": [{"text": system}]}
        client = await self.client()
        resp = await client.post(url, params={"key": self.cfg.gemini_api_key}, json=body)
        if resp.status_code >= 400:
            raise LLMError(f"gemini HTTP {resp.status_code}: {resp.text[:300]}")
        data = resp.json()
        candidates = data.get("candidates") or []
        if not candidates:
            raise LLMError(f"gemini returned no candidates: {str(data)[:200]}")
        parts = candidates[0].get("content", {}).get("parts", [])
        out = "".join(p.get("text", "") for p in parts).strip()
        if not out:
            raise LLMError("gemini returned empty text")
        return out

    async def _groq(self, prompt: str, system: str, max_tokens: int, temperature: float) -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        body = {
            "model": self.cfg.groq_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "response_format": {"type": "json_object"},
        }
        client = await self.client()
        resp = await client.post(
            GROQ_URL, json=body, headers={"Authorization": f"Bearer {self.cfg.groq_api_key}"}
        )
        if resp.status_code >= 400:
            raise LLMError(f"groq HTTP {resp.status_code}: {resp.text[:300]}")
        data = resp.json()
        out = (data.get("choices") or [{}])[0].get("message", {}).get("content", "").strip()
        if not out:
            raise LLMError("groq returned empty text")
        return out
