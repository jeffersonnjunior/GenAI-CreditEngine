from decimal import Decimal

from credit_engine.core.common.enums.proposal import ProposalStatus
from credit_engine.core.common.enums.risk import RiskBand
from credit_engine.models.proposal import ProposalCreate
from credit_engine.services.risk import compute_limit, evaluate_proposal


def test_risk_band_boundaries() -> None:
    assert RiskBand.from_score(299) is RiskBand.DENIED
    assert RiskBand.from_score(300) is RiskBand.STANDARD
    assert RiskBand.from_score(699) is RiskBand.STANDARD
    assert RiskBand.from_score(700) is RiskBand.PREMIUM


def test_compute_limit_denied_below_min_score() -> None:
    assert compute_limit(299, Decimal("5000.00")) == Decimal("0.00")


def test_compute_limit_standard_ten_percent() -> None:
    assert compute_limit(300, Decimal("5000.00")) == Decimal("500.00")
    assert compute_limit(699, Decimal("5000.00")) == Decimal("500.00")


def test_compute_limit_premium_thirty_percent() -> None:
    assert compute_limit(700, Decimal("5000.00")) == Decimal("1500.00")


def test_compute_limit_premium_rounds_half_up() -> None:
    assert compute_limit(700, Decimal("3333.33")) == Decimal("1000.00")


async def test_evaluate_proposal_approved_standard() -> None:
    decision = await evaluate_proposal(
        ProposalCreate(
            applicant_name="Maria Silva",
            cpf="12345678901",
            monthly_income=Decimal("10000.00"),
            credit_score=650,
        )
    )
    assert decision.status is ProposalStatus.APPROVED
    assert decision.credit_limit == Decimal("1000.00")
    assert "10%" in decision.reason


async def test_evaluate_proposal_approved_premium() -> None:
    decision = await evaluate_proposal(
        ProposalCreate(
            applicant_name="Maria Silva",
            cpf="12345678901",
            monthly_income=Decimal("10000.00"),
            credit_score=700,
        )
    )
    assert decision.status is ProposalStatus.APPROVED
    assert decision.credit_limit == Decimal("3000.00")
    assert "30%" in decision.reason


async def test_evaluate_proposal_denied() -> None:
    decision = await evaluate_proposal(
        ProposalCreate(
            applicant_name="Joao Souza",
            cpf="12345678901",
            monthly_income=Decimal("10000.00"),
            credit_score=100,
        )
    )
    assert decision.status is ProposalStatus.DENIED
    assert decision.credit_limit == Decimal("0.00")
