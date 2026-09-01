from decimal import Decimal
from uuid import UUID

import pytest

from credit_engine.agents.checkpointer import get_checkpointer, reset_checkpointer
from credit_engine.agents.runner import resume_proposal_graph, run_proposal_graph
from credit_engine.core.common.enums.proposal import ProposalStatus
from credit_engine.models.proposal import OverrideRequest, ProposalCreate
from credit_engine.services.proposal import create_proposal, override_proposal


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


async def test_run_proposal_graph_interrupts_on_pending_review() -> None:
    reset_checkpointer()
    _ = get_checkpointer()
    decision = await run_proposal_graph(
        {
            "applicant_name": "Carlos Lima",
            "cpf": "12345678901",
            "monthly_income": "50000.00",
            "credit_score": 720,
        },
        bureau=FixedScoreBureau(720),
    )
    assert decision.status is ProposalStatus.PENDING_REVIEW
    assert decision.credit_limit == Decimal("15000.00")


async def test_resume_proposal_graph_after_override_approve() -> None:
    reset_checkpointer()
    _ = get_checkpointer()
    decision = await run_proposal_graph(
        {
            "applicant_name": "Carlos Lima",
            "cpf": "12345678901",
            "monthly_income": "50000.00",
            "credit_score": 720,
        },
        bureau=FixedScoreBureau(720),
    )
    assert decision.status is ProposalStatus.PENDING_REVIEW
    proposal_id = decision.proposal_id

    final = await resume_proposal_graph(
        proposal_id,
        OverrideRequest(
            decision="approve",
            analyst="Ana Analista",
            note="renda ok",
        ),
    )
    assert final.status is ProposalStatus.APPROVED
    assert final.analyst == "Ana Analista"
    assert final.credit_limit == Decimal("15000.00")


async def test_override_proposal_resumes_graph(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    reset_checkpointer()
    _ = get_checkpointer()
    monkeypatch.setattr(
        "credit_engine.services.proposal.settings.ORCHESTRATOR",
        "graph",
    )
    created = await create_proposal(
        {
            "applicant_name": "Carlos Lima",
            "cpf": "12345678901",
            "monthly_income": "50000.00",
            "credit_score": 720,
        },
        bureau=FixedScoreBureau(720),
    )
    assert created.status is ProposalStatus.PENDING_REVIEW
    proposal_id = UUID(str(created.proposal_id))

    denied = await override_proposal(
        proposal_id,
        OverrideRequest(decision="deny", analyst="Ana Analista"),
    )
    assert denied.status is ProposalStatus.DENIED
    assert denied.credit_limit == Decimal("0.00")


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
