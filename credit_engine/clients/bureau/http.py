"""HTTP credit-bureau client."""

from __future__ import annotations

import httpx

from credit_engine.clients.bureau.exc import BureauUnavailableError
from credit_engine.core.config import settings


class HttpBureauClient:
    """Fetches scores from ``GET {BASE_URL}/score/{cpf}``."""

    def __init__(
        self,
        *,
        base_url: str | None = None,
        timeout_seconds: float | None = None,
    ) -> None:
        self._base_url = (base_url if base_url is not None else settings.BASE_URL).rstrip(
            "/"
        )
        self._timeout = (
            timeout_seconds
            if timeout_seconds is not None
            else settings.TIMEOUT_SECONDS
        )

    async def fetch_credit_score(self, cpf: str) -> int:
        """Return the bureau score or raise BureauUnavailableError."""
        if not self._base_url:
            msg = "BUREAU_BASE_URL is not configured"
            raise BureauUnavailableError(msg)

        url = f"{self._base_url}/score/{cpf}"
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.get(url)
                response.raise_for_status()
                payload = response.json()
                return int(payload["credit_score"])
        except (
            httpx.HTTPError,
            KeyError,
            TypeError,
            ValueError,
        ) as exc:
            raise BureauUnavailableError(str(exc)) from exc
