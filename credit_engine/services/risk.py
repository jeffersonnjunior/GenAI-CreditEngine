from decimal import ROUND_HALF_UP, Decimal

from credit_engine.core.common.enums.proposal import ProposalStatus
from credit_engine.core.config import settings
from credit_engine.models.proposal import CreditDecision, ProposalCreate

_MONEY = Decimal("0.01")


def compute_limit(score: int, monthly_income: Decimal) -> Decimal:
    """
    Simplest risk rule (Sprint 1 baseline).

    - score < MIN_SCORE_TO_APPROVE → R$ 0
    - otherwise → monthly_income * INCOME_LIMIT_RATIO (10%)
    """
    if score < settings.MIN_SCORE_TO_APPROVE:
        return Decimal("0.00")
    raw = monthly_income * Decimal(str(settings.INCOME_LIMIT_RATIO))
    return raw.quantize(_MONEY, rounding=ROUND_HALF_UP)


async def evaluate_proposal(payload: ProposalCreate) -> CreditDecision:
    """Evaluate a proposal and return a strict CreditDecision."""
    limit = compute_limit(payload.credit_score, payload.monthly_income)

    if limit == 0:
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

    return CreditDecision(
        applicant_name=payload.applicant_name,
        status=ProposalStatus.APPROVED,
        credit_limit=limit,
        credit_score=payload.credit_score,
        reason=(
            f"Score {payload.credit_score} aprovado com "
            f"{int(settings.INCOME_LIMIT_RATIO * 100)}% da renda"
        ),
    )
