from credit_engine.clients.bureau.exc import BureauUnavailableError
from credit_engine.core.config import settings


class StubBureauClient:
    """Placeholder bureau until a real HTTP client is wired."""

    async def fetch_credit_score(self, cpf: str) -> int:
        """Return a deterministic stub score (ignores CPF for now)."""
        _ = cpf
        return settings.STUB_DEFAULT_SCORE


class UnavailableBureauClient:
    """Simulates bureau timeout/outage for contingency-path tests."""

    async def fetch_credit_score(self, cpf: str) -> int:
        """Always fail as if the bureau timed out."""
        _ = cpf
        msg = "credit bureau timeout"
        raise BureauUnavailableError(msg)
