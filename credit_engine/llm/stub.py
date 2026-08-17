from typing import Any

from pydantic import ValidationError


class StubHealer:
    """Placeholder healer until a real LLM backend is chosen.

    Does not call a model and does not mutate the payload.
    """

    async def repair(
        self,
        payload: dict[str, Any],
        error: ValidationError,
    ) -> dict[str, Any]:
        """Return the payload unchanged (AI provider still pending)."""
        _ = error
        return dict(payload)
