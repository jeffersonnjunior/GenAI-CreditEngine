from typing import Protocol


class BureauClient(Protocol):
    """Fetches a bureau credit score for a normalized CPF."""

    async def fetch_credit_score(self, cpf: str) -> int:
        """Return the applicant score from the bureau."""
        ...
