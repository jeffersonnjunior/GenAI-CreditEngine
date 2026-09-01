from decimal import Decimal

import pytest

from credit_engine.agents.runner import run_proposal_graph
from credit_engine.core.common.enums.proposal import ProposalStatus
from credit_engine.models.proposal import ProposalCreate
from credit_engine.services.proposal import create_proposal


class FixedScoreBureau:
    """Test double that returns a predetermined bureau score."""

    def __init__(self, score: int) -> None:
        self._score = score

    async def fetch_credit_score(self, cpf: str) -> int:
        _ = cpf
        return self._score


async def test_run_proposal_graph_approved_standard() -> None:
    decision = await run_proposal_graph(
        {
            "applicant_name": "Maria Silva",
            "cpf": "12345678901",
            "monthly_income": "10000.00",
            "credit_score": 650,
        },
        bureau=FixedScoreBureau(650),
    )
    assert decision.status is ProposalStatus.APPROVED
    assert decision.credit_limit == Decimal("1000.00")


async def test_create_proposal_uses_graph_by_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "credit_engine.services.proposal.settings.ORCHESTRATOR",
        "graph",
    )
    decision = await create_proposal(
        {
            "applicant_name": "Maria Silva",
            "cpf": "12345678901",
            "monthly_income": "10000.00",
            "credit_score": 650,
        },
        bureau=FixedScoreBureau(650),
    )
    assert decision.status is ProposalStatus.APPROVED


async def test_create_proposal_linear_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "credit_engine.services.proposal.settings.ORCHESTRATOR",
        "linear",
    )
    decision = await create_proposal(
        {
            "applicant_name": "Maria Silva",
            "cpf": "12345678901",
            "monthly_income": "10000.00",
            "credit_score": 650,
        },
        bureau=FixedScoreBureau(650),
    )
    assert decision.status is ProposalStatus.APPROVED
    assert ProposalCreate.model_validate(
        {
            "applicant_name": "Maria Silva",
            "cpf": "12345678901",
            "monthly_income": "10000.00",
            "credit_score": 650,
        }
    )
