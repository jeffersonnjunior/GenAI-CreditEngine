from decimal import Decimal
from enum import StrEnum

from credit_engine.core.config import settings


class RiskBand(StrEnum):
    """Deterministic credit band derived from score."""

    DENIED = "denied"
    STANDARD = "standard"
    PREMIUM = "premium"

    @classmethod
    def from_score(cls, score: int) -> "RiskBand":
        """Map a bureau score onto a risk band."""
        if score < settings.MIN_SCORE_TO_APPROVE:
            return cls.DENIED
        if score < settings.HIGH_SCORE_THRESHOLD:
            return cls.STANDARD
        return cls.PREMIUM

    def income_ratio(self) -> Decimal:
        """Share of monthly income granted as credit limit."""
        if self is RiskBand.DENIED:
            return Decimal("0")
        if self is RiskBand.STANDARD:
            return Decimal(str(settings.INCOME_LIMIT_RATIO))
        return Decimal(str(settings.HIGH_INCOME_LIMIT_RATIO))
