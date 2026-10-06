"""Local LLM Writer: Primary Ollama (Qwen3/Qwen2.5) with graceful zero-fail fallback."""
from __future__ import annotations

import json
import os
import re
import httpx
from typing import Any

from factshorts.llm import LLM, extract_json


class LocalWriter:
    def __init__(
        self,
        ollama_host: str = "http://localhost:11434",
        model: str = "qwen2.5:7b",
        fallback_llm: LLM | None = None,
    ) -> None:
        self.ollama_host = ollama_host.rstrip("/")
        self.model = model
        self.fallback = fallback_llm or LLM()

    async def is_ollama_available(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(2.0)) as client:
                resp = await client.get(f"{self.ollama_host}/api/tags")
                return resp.status_code == 200
        except Exception:
            return False

    async def generate_json(self, prompt: str, system: str = "") -> dict[str, Any]:
        """Try Ollama first; if unavailable or error, seamlessly fallback to Gemini cascade."""
        # 1. Try Local Ollama
        if await self.is_ollama_available():
            try:
                payload = {
                    "model": self.model,
                    "prompt": f"{system}\n\n{prompt}\n\nReply with a single valid JSON object only. No conversational preamble.",
                    "stream": False,
                    "format": "json",
                    "options": {
                        "temperature": 0.8,
                        "num_predict": 1200,
                    }
                }
                async with httpx.AsyncClient(timeout=httpx.Timeout(90.0)) as client:
                    resp = await client.post(f"{self.ollama_host}/api/generate", json=payload)
                    if resp.status_code == 200:
                        data = resp.json()
                        raw_text = data.get("response", "")
                        if raw_text:
                            return extract_json(raw_text)
            except Exception:
                pass  # Fall through to cloud cascade

        # 2. Resilient Cloud Cascade (Gemini 3.5 Flash / Groq)
        return await self.fallback.json(prompt, system, max_tokens=1400, temperature=0.85)
