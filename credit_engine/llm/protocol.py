from typing import Any, Protocol

from pydantic import ValidationError


class Healer(Protocol):
    """Rewrites an invalid payload using validation errors as context."""

    async def repair(
        self,
        payload: dict[str, Any],
        error: ValidationError,
    ) -> dict[str, Any]:
        """Return a candidate payload that may pass schema validation."""
        ...
