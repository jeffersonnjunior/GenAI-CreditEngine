"""OpenAI-compatible payload healer (Ollama, vLLM, etc.)."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

import httpx
from pydantic import ValidationError

from credit_engine.core.config import settings
from credit_engine.llm.prompts import (
    SYSTEM_PROMPT,
    build_repair_user_prompt,
    extract_json_object,
)

CompleteFn = Callable[[str, str], Awaitable[str]]


class OpenAICompatibleHealer:
    """Repairs invalid payloads via an OpenAI-style chat completions API.

    Pass ``complete`` in tests to avoid real network calls.
    """

    def __init__(
        self,
        *,
        base_url: str | None = None,
        model: str | None = None,
        api_key: str | None = None,
        timeout_seconds: float | None = None,
        complete: CompleteFn | None = None,
    ) -> None:
        self._base_url = (
            base_url if base_url is not None else settings.OPENAI_BASE_URL
        ).rstrip("/")
        self._model = model if model is not None else settings.MODEL
        self._api_key = api_key if api_key is not None else settings.API_KEY
        self._timeout = (
            timeout_seconds
            if timeout_seconds is not None
            else settings.OPENAI_TIMEOUT_SECONDS
        )
        self._complete = complete

    async def repair(
        self,
        payload: dict[str, Any],
        error: ValidationError,
    ) -> dict[str, Any]:
        """Ask the local/remote model to rewrite the payload; parse JSON."""
        user_prompt = build_repair_user_prompt(payload, error)
        text = await self._generate(SYSTEM_PROMPT, user_prompt)
        return extract_json_object(text)

    async def _generate(self, system: str, user: str) -> str:
        if self._complete is not None:
            return await self._complete(system, user)

        if not self._base_url:
            msg = (
                "LLM_BASE_URL is required when "
                "LLM_BACKEND=openai_compatible or llama"
            )
            raise RuntimeError(msg)

        headers: dict[str, str] = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"

        body = {
            "model": self._model,
            "temperature": 0,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
        url = f"{self._base_url}/chat/completions"

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(url, headers=headers, json=body)
                response.raise_for_status()
                payload = response.json()
        except httpx.HTTPError as exc:
            msg = f"OpenAI-compatible healer request failed: {exc}"
            raise RuntimeError(msg) from exc

        try:
            text = payload["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            msg = "OpenAI-compatible healer returned an unexpected response shape"
            raise RuntimeError(msg) from exc

        if not isinstance(text, str) or not text.strip():
            msg = "OpenAI-compatible healer returned an empty response"
            raise RuntimeError(msg)
        return text
