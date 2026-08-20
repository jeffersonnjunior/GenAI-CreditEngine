"""Gemini-backed payload healer (Google GenAI SDK)."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from pydantic import ValidationError

from credit_engine.core.config import settings
from credit_engine.llm.prompts import (
    SYSTEM_PROMPT,
    build_repair_user_prompt,
    extract_json_object,
)

CompleteFn = Callable[[str, str], Awaitable[str]]


class GeminiHealer:
    """Repairs invalid payloads using Gemini.

    Pass ``complete`` in tests to avoid real network calls.
    """

    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str | None = None,
        complete: CompleteFn | None = None,
    ) -> None:
        self._api_key = api_key if api_key is not None else settings.API_KEY
        default_model = settings.MODEL or "gemini-2.0-flash"
        self._model = model if model is not None else default_model
        self._complete = complete

    async def repair(
        self,
        payload: dict[str, Any],
        error: ValidationError,
    ) -> dict[str, Any]:
        """Ask Gemini to rewrite the payload; parse the JSON object reply."""
        user_prompt = build_repair_user_prompt(payload, error)
        text = await self._generate(SYSTEM_PROMPT, user_prompt)
        return extract_json_object(text)

    async def _generate(self, system: str, user: str) -> str:
        if self._complete is not None:
            return await self._complete(system, user)

        if not self._api_key:
            msg = "LLM_API_KEY is required when LLM_BACKEND=gemini"
            raise RuntimeError(msg)

        from google import genai
        from google.genai import types

        client = genai.Client(api_key=self._api_key)
        response = await client.aio.models.generate_content(
            model=self._model,
            contents=user,
            config=types.GenerateContentConfig(
                system_instruction=system,
                response_mime_type="application/json",
                temperature=0.0,
            ),
        )
        text = getattr(response, "text", None) or ""
        if not text.strip():
            msg = "Gemini returned an empty response"
            raise RuntimeError(msg)
        return text
