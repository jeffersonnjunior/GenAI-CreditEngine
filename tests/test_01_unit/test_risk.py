from decimal import Decimal

import pytest

from credit_engine.clients.bureau.stub import UnavailableBureauClient
from credit_engine.core.common.enums.degradation import DegradationMode
from credit_engine.core.common.enums.proposal import ProposalStatus
from credit_engine.core.common.enums.risk import RiskBand
from credit_engine.core.config import settings
from credit_engine.models.proposal import ProposalCreate
from credit_engine.services.risk import compute_limit, evaluate_proposal


class FixedScoreBureau:
    """Test double that returns a predetermined bureau score."""

    def __init__(self, score: int) -> None:
        self._score = score

    async def fetch_credit_score(self, cpf: str) -> int:
        _ = cpf
        return self._score


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
        ),
        bureau=FixedScoreBureau(650),
    )
    assert decision.status is ProposalStatus.APPROVED
    assert decision.credit_limit == Decimal("1000.00")
    assert "10%" in decision.reason
    assert decision.degradation_mode is DegradationMode.NONE
    assert decision.degradation_log is None


async def test_evaluate_proposal_approved_premium() -> None:
    decision = await evaluate_proposal(
        ProposalCreate(
            applicant_name="Maria Silva",
            cpf="12345678901",
            monthly_income=Decimal("10000.00"),
            credit_score=700,
        ),
        bureau=FixedScoreBureau(700),
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
        ),
        bureau=FixedScoreBureau(100),
    )
    assert decision.status is ProposalStatus.DENIED
    assert decision.credit_limit == Decimal("0.00")


async def test_evaluate_proposal_bureau_unavailable_emergency_limit() -> None:
    decision = await evaluate_proposal(
        ProposalCreate(
            applicant_name="Ana Costa",
            cpf="12345678901",
            monthly_income=Decimal("20000.00"),
            credit_score=850,
        ),
        bureau=UnavailableBureauClient(),
    )
    assert decision.status is ProposalStatus.APPROVED
    assert decision.credit_limit == Decimal(str(settings.EMERGENCY_LIMIT))
    assert decision.degradation_mode is DegradationMode.BUREAU_UNAVAILABLE
    assert decision.degradation_log is not None
    assert "birô indisponível" in decision.degradation_log
    assert "emergencial" in decision.reason.lower()


async def test_evaluate_proposal_bureau_unavailable_still_approves_low_score() -> None:
    """Contingency path ignores score bands — fault tolerance, not denial."""
    decision = await evaluate_proposal(
        ProposalCreate(
            applicant_name="Pedro Lima",
            cpf="12345678901",
            monthly_income=Decimal("1000.00"),
            credit_score=50,
        ),
        bureau=UnavailableBureauClient(),
    )
    assert decision.status is ProposalStatus.APPROVED
    assert decision.credit_limit == Decimal("500.00")


@pytest.mark.parametrize("stub_score", [650, 720])
async def test_evaluate_proposal_uses_bureau_score_not_payload(
    stub_score: int,
) -> None:
    payload_score = 100 if stub_score >= 700 else 850
    decision = await evaluate_proposal(
        ProposalCreate(
            applicant_name="Carla Dias",
            cpf="12345678901",
            monthly_income=Decimal("10000.00"),
            credit_score=payload_score,
        ),
        bureau=FixedScoreBureau(stub_score),
    )
    assert decision.credit_score == stub_score
