"""Optional NVIDIA Gemma provider with a deterministic no-LLM fallback."""

from __future__ import annotations

import json
import os
import re
from typing import Any

import httpx


class LLMError(RuntimeError):
    """Raised when an LLM response cannot be safely consumed."""


def extract_json(text: str) -> dict[str, Any]:
    value = text.strip()
    if value.startswith("```"):
        match = re.fullmatch(r"```(?:json)?\s*(\{.*\})\s*```", value, re.S | re.I)
        if not match:
            raise LLMError("invalid JSON wrapper")
        value = match.group(1)
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as exc:
        raise LLMError("LLM returned invalid JSON") from exc
    if not isinstance(parsed, dict):
        raise LLMError("LLM response must be a JSON object")
    return parsed


class NoopLLM:
    async def complete(self, prompt: str) -> dict[str, Any]:
        return {}


class NvidiaGemmaLLM:
    endpoint = "https://integrate.api.nvidia.com/v1/chat/completions"

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.api_key = api_key or os.getenv("NVIDIA_API_KEY")
        self.model = model or os.getenv("NVIDIA_MODEL", "google/gemma-4-31b-it")
        self.client = client

    async def complete(self, prompt: str) -> dict[str, Any]:
        if not self.api_key:
            return {}
        own = self.client is None
        client = self.client or httpx.AsyncClient(timeout=30)
        try:
            response = await client.post(
                self.endpoint,
                headers={
                    "Authorization": "Bearer " + self.api_key,
                    "Accept": "application/json",
                },
                json={
                    "model": self.model,
                    "max_tokens": 1024,
                    "stream": False,
                    "temperature": 0,
                    "messages": [{"role": "user", "content": prompt}],
                    "response_format": {"type": "json_object"},
                },
            )
            response.raise_for_status()
            data = response.json()
            return extract_json(data["choices"][0]["message"]["content"])
        except (httpx.HTTPError, KeyError, IndexError, TypeError, LLMError) as exc:
            raise LLMError("LLM request failed") from exc
        finally:
            if own:
                await client.aclose()


def get_llm() -> NvidiaGemmaLLM | NoopLLM:
    return NvidiaGemmaLLM() if os.getenv("NVIDIA_API_KEY") else NoopLLM()
