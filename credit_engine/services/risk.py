from decimal import ROUND_HALF_UP, Decimal

from credit_engine.core.common.enums.proposal import ProposalStatus
from credit_engine.core.common.enums.risk import RiskBand
from credit_engine.core.config import settings
from credit_engine.models.proposal import CreditDecision, ProposalCreate

_MONEY = Decimal("0.01")


def compute_limit(score: int, monthly_income: Decimal) -> Decimal:
    """
    Deterministic limit from score bands.

    - score < 300 → R$ 0
    - 300 ≤ score < 700 → monthly_income * 10%
    - score ≥ 700 → monthly_income * 30%
    """
    band = RiskBand.from_score(score)
    raw = monthly_income * band.income_ratio()
    return raw.quantize(_MONEY, rounding=ROUND_HALF_UP)


async def evaluate_proposal(payload: ProposalCreate) -> CreditDecision:
    """Evaluate a proposal and return a strict CreditDecision."""
    limit = compute_limit(payload.credit_score, payload.monthly_income)
    band = RiskBand.from_score(payload.credit_score)

    if band is RiskBand.DENIED:
        return CreditDecision(
            applicant_name=payload.applicant_name,
            status=ProposalStatus.DENIED,
            credit_limit=limit,
            credit_score=payload.credit_score,
            reason=(
                f"Score {payload.credit_score} abaixo do mínimo "
                f"{settings.MIN_SCORE_TO_APPROVE}"
            ),
        )

    percent = int(band.income_ratio() * 100)
    return CreditDecision(
        applicant_name=payload.applicant_name,
        status=ProposalStatus.APPROVED,
        credit_limit=limit,
        credit_score=payload.credit_score,
        reason=(
            f"Score {payload.credit_score} aprovado com "
            f"{percent}% da renda"
        ),
    )
