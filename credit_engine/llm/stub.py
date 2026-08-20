from typing import Any

from pydantic import ValidationError


class StubHealer:
    """No-op healer for tests/CI (does not call a model)."""

    async def repair(
        self,
        payload: dict[str, Any],
        error: ValidationError,
    ) -> dict[str, Any]:
        """Return the payload unchanged."""
        _ = error
        return dict(payload)
