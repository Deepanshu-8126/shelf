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
NVIDIA_URL = "https://integrate.api.nvidia.com/v1/chat/completions"


class LLMError(RuntimeError):
    pass


def extract_json(raw: str) -> dict[str, Any]:
    """Best-effort JSON extraction from an LLM answer."""
    if not raw:
        raise LLMError("empty response")
    text = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()
    
    # 1. Search for fenced ```json ... ``` blocks anywhere in the text
    fence_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL | re.IGNORECASE)
    if fence_match:
        candidate = fence_match.group(1).strip()
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass

    # 2. Direct json.loads if entire string is valid JSON
    cleaned = re.sub(r"^```[a-zA-Z]*\s*", "", text)
    cleaned = re.sub(r"```\s*$", "", cleaned).strip()
    try:
        data = json.loads(cleaned)
        if isinstance(data, dict):
            return data
        if isinstance(data, list) and data and isinstance(data[0], dict):
            return data[0]
    except json.JSONDecodeError:
        pass

    # 3. Scan for outermost { ... }
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end > start:
        candidate = text[start : end + 1]
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            # Clean common LLM formatting quirks: trailing commas, single quotes, unescaped newlines
            sanitized = re.sub(r",\s*([}\]])", r"\1", candidate)
            try:
                return json.loads(sanitized)
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
        if order == "nvidia":
            chain = ["nvidia"]
        elif order == "gemini":
            chain = ["gemini"]
        elif order == "groq":
            chain = ["groq"]
        elif order == "offline":
            chain = []
        else:  # auto
            if self.cfg.nvidia_api_key:
                chain.append("nvidia")
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
                    if provider == "nvidia":
                        out = await self._nvidia(prompt, system, max_tokens, temperature, is_json=False)
                    elif provider == "gemini":
                        out = await self._gemini(prompt, system, max_tokens, temperature, is_json=False)
                    else:
                        out = await self._groq(prompt, system, max_tokens, temperature, is_json=False)
                    self.last_provider = provider
                    return out
                except Exception as exc:  # noqa: BLE001 - fall through to next provider
                    errors.append(f"{provider}[{attempt}]: {exc}")
                    log.warning("LLM %s attempt %d failed: %s", provider, attempt, exc)
                    if "429" in str(exc):
                        log.warning("LLM %s rate limited (429), switching provider immediately", provider)
                        break
                    await asyncio.sleep(1.0 * attempt)
        raise LLMError("all LLM providers failed -> " + " | ".join(errors[:4]))

    async def json(self, prompt: str, system: str = "", max_tokens: int = 900, temperature: float = 0.9) -> dict[str, Any]:
        system_json = (system + "\n" if system else "") + (
            "Reply with a single valid JSON object and nothing else. No markdown fences."
        )
        errors: list[str] = []
        for provider in self.providers:
            for attempt in range(1, 3):
                try:
                    if provider == "nvidia":
                        raw = await self._nvidia(prompt, system_json, max_tokens, temperature, is_json=True)
                    elif provider == "gemini":
                        raw = await self._gemini(prompt, system_json, max_tokens, temperature, is_json=True)
                    else:
                        raw = await self._groq(prompt, system_json, max_tokens, temperature, is_json=True)
                    self.last_provider = provider
                    return extract_json(raw)
                except Exception as exc:  # noqa: BLE001
                    errors.append(f"{provider}[{attempt}]: {exc}")
                    if "429" in str(exc) or "503" in str(exc):
                        log.warning("LLM %s unavailable (429/503), switching provider immediately", provider)
                        break
                    await asyncio.sleep(1.0 * attempt)
        raise LLMError("all LLM providers failed -> " + " | ".join(errors[:4]))

    # ------------------------------------------------------------------ providers
    async def _gemini(
        self, prompt: str, system: str, max_tokens: int, temperature: float, is_json: bool = False
    ) -> str:
        # Verified active working models for this API key:
        models = [
            self.cfg.gemini_model,
            "gemini-2.5-flash",
            "gemini-2.0-flash",
            "gemini-1.5-flash",
            "gemini-2.0-flash-lite",
            "gemini-flash-latest",
        ]
        # Deduplicate preserving order
        models = list(dict.fromkeys(m for m in models if m))

        client = await self.client()
        last_exc: Exception | None = None

        for model in models:
            url = GEMINI_URL.format(model=model)
            gen_config: dict[str, Any] = {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            }
            if is_json:
                gen_config["responseMimeType"] = "application/json"

            body: dict[str, Any] = {
                "contents": [{"role": "user", "parts": [{"text": prompt}]}],
                "generationConfig": gen_config,
            }
            if system:
                body["systemInstruction"] = {"parts": [{"text": system}]}

            try:
                resp = await client.post(url, params={"key": self.cfg.gemini_api_key}, json=body)
                if resp.status_code >= 400:
                    log.warning("Gemini %s HTTP %d: %s", model, resp.status_code, resp.text[:150])
                    last_exc = LLMError(f"gemini {model} HTTP {resp.status_code}: {resp.text[:150]}")
                    if resp.status_code == 429:
                        log.warning("Gemini 429 quota/rate limit encountered. Breaking early to trigger instant fallback.")
                        break
                    if resp.status_code == 503:
                        await asyncio.sleep(1.0)
                    continue

                data = resp.json()
                candidates = data.get("candidates") or []
                if not candidates:
                    last_exc = LLMError(f"gemini {model} returned no candidates")
                    continue
                parts = candidates[0].get("content", {}).get("parts", [])
                out = "".join(p.get("text", "") for p in parts).strip()
                if out:
                    return out
            except Exception as exc:
                last_exc = exc
                continue

        raise last_exc or LLMError("All Gemini models failed")

    async def _groq(
        self, prompt: str, system: str, max_tokens: int, temperature: float, is_json: bool = False
    ) -> str:
        models = [
            self.cfg.groq_model,
            "openai/gpt-oss-120b",
            "openai/gpt-oss-20b",
            "allam-2-7b",
        ]
        models = list(dict.fromkeys(m for m in models if m))

        client = await self.client()
        last_exc: Exception | None = None

        for model in models:
            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})

            body: dict[str, Any] = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            if is_json:
                body["response_format"] = {"type": "json_object"}

            try:
                resp = await client.post(
                    GROQ_URL,
                    json=body,
                    headers={"Authorization": f"Bearer {self.cfg.groq_api_key}"},
                )
                if resp.status_code >= 400:
                    log.warning("Groq %s HTTP %d: %s", model, resp.status_code, resp.text[:150])
                    last_exc = LLMError(f"groq {model} HTTP {resp.status_code}: {resp.text[:150]}")
                    continue
                data = resp.json()
                out = (data.get("choices") or [{}])[0].get("message", {}).get("content", "").strip()
                if out:
                    return out
            except Exception as exc:
                last_exc = exc
                continue

        raise last_exc or LLMError("All Groq models failed")

    async def _nvidia(
        self, prompt: str, system: str, max_tokens: int, temperature: float, is_json: bool = False
    ) -> str:
        models = [
            self.cfg.nvidia_model,
            "deepseek-ai/deepseek-r1",
            "meta/llama-3.3-70b-instruct",
            "deepseek-ai/deepseek-v3",
        ]
        models = list(dict.fromkeys(m for m in models if m))

        client = await self.client()
        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        last_exc: Exception | None = None
        for model in models:
            body: dict[str, Any] = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            if is_json and "deepseek-r1" not in model.lower():
                body["response_format"] = {"type": "json_object"}

            try:
                resp = await client.post(
                    NVIDIA_URL,
                    json=body,
                    headers={
                        "Authorization": f"Bearer {self.cfg.nvidia_api_key}",
                        "Accept": "application/json",
                    },
                )
                if resp.status_code >= 400:
                    log.warning("NVIDIA %s HTTP %d: %s", model, resp.status_code, resp.text[:150])
                    last_exc = LLMError(f"nvidia {model} HTTP {resp.status_code}: {resp.text[:150]}")
                    continue
                data = resp.json()
                content = (data.get("choices") or [{}])[0].get("message", {}).get("content", "").strip()
                cleaned = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()
                if cleaned:
                    return cleaned
            except Exception as exc:
                last_exc = exc
                continue

        raise last_exc or LLMError("All NVIDIA models failed")

