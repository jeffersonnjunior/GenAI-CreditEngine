from decimal import ROUND_HALF_UP, Decimal

from credit_engine.clients.bureau.exc import BureauUnavailableError
from credit_engine.clients.bureau.factory import get_bureau
from credit_engine.clients.bureau.protocol import BureauClient
from credit_engine.core.common.enums.degradation import DegradationMode
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


def _decision_from_score(payload: ProposalCreate, score: int) -> CreditDecision:
    limit = compute_limit(score, payload.monthly_income)
    band = RiskBand.from_score(score)

    if band is RiskBand.DENIED:
        return CreditDecision(
            applicant_name=payload.applicant_name,
            status=ProposalStatus.DENIED,
            credit_limit=limit,
            credit_score=score,
            reason=(
                f"Score {score} abaixo do mínimo "
                f"{settings.MIN_SCORE_TO_APPROVE}"
            ),
        )

    percent = int(band.income_ratio() * 100)
    return CreditDecision(
        applicant_name=payload.applicant_name,
        status=ProposalStatus.APPROVED,
        credit_limit=limit,
        credit_score=score,
        reason=(
            f"Score {score} aprovado com "
            f"{percent}% da renda"
        ),
    )


def _emergency_decision(
    payload: ProposalCreate,
    *,
    cause: str,
) -> CreditDecision:
    """Immutable contingency: fixed limit when the bureau is down."""
    limit = Decimal(str(settings.EMERGENCY_LIMIT)).quantize(
        _MONEY,
        rounding=ROUND_HALF_UP,
    )
    log = (
        f"Degradação estrutural: birô indisponível ({cause}). "
        f"Limite emergencial imutável de R$ {limit} aplicado; "
        "score do payload não foi consultado no birô."
    )
    return CreditDecision(
        applicant_name=payload.applicant_name,
        status=ProposalStatus.APPROVED,
        credit_limit=limit,
        credit_score=payload.credit_score,
        reason=(
            f"Aprovado com limite emergencial de R$ {limit} "
            "(birô de crédito indisponível)"
        ),
        degradation_mode=DegradationMode.BUREAU_UNAVAILABLE,
        degradation_log=log,
    )


async def evaluate_proposal(
    payload: ProposalCreate,
    *,
    bureau: BureauClient | None = None,
) -> CreditDecision:
    """Fetch bureau score when possible; otherwise apply the contingency limit."""
    client = bureau or get_bureau()
    try:
        score = await client.fetch_credit_score(payload.cpf)
    except BureauUnavailableError as exc:
        return _emergency_decision(payload, cause=str(exc))
    return _decision_from_score(payload, score)
