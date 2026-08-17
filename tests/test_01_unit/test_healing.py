from decimal import Decimal
from typing import Any

from pydantic import ValidationError

from credit_engine.core.common.enums.proposal import ProposalStatus
from credit_engine.core.common.exc import HealingExhausted
from credit_engine.llm.healing import heal_to_schema
from credit_engine.llm.stub import StubHealer
from credit_engine.models.proposal import ProposalCreate
from credit_engine.services.proposal import create_proposal


class FakeHealer:
    """Test double that repairs a payload in one shot (stands in for the LLM)."""

    def __init__(self, repaired: dict[str, Any]) -> None:
        self.repaired = repaired
        self.calls = 0

    async def repair(
        self,
        payload: dict[str, Any],
        error: ValidationError,
    ) -> dict[str, Any]:
        _ = payload, error
        self.calls += 1
        return dict(self.repaired)


async def test_heal_valid_payload_skips_repair() -> None:
    payload = {
        "applicant_name": "Maria Silva",
        "cpf": "12345678901",
        "monthly_income": "10000.00",
        "credit_score": 650,
    }
    healer = FakeHealer(repaired=payload)
    result = await heal_to_schema(payload, ProposalCreate, healer=healer)
    assert result.applicant_name == "Maria Silva"
    assert healer.calls == 0


async def test_heal_repairs_invalid_payload_within_attempts() -> None:
    broken = {"applicant_name": "Maria Silva"}
    repaired = {
        "applicant_name": "Maria Silva",
        "cpf": "12345678901",
        "monthly_income": "10000.00",
        "credit_score": 650,
    }
    healer = FakeHealer(repaired=repaired)
    result = await heal_to_schema(broken, ProposalCreate, healer=healer)
    assert result.credit_score == 650
    assert healer.calls == 1


async def test_heal_stub_exhausts_attempts_and_raises() -> None:
    broken = {"applicant_name": "Maria"}
    try:
        await heal_to_schema(broken, ProposalCreate, healer=StubHealer())
    except HealingExhausted as exc:
        body = exc.detail
        assert isinstance(body, dict)
        assert "healing attempts" in body["message"]
        assert body["errors"]
    else:
        raise AssertionError("expected HealingExhausted")


async def test_create_proposal_heals_then_evaluates() -> None:
    broken = {"applicant_name": "Maria Silva"}
    repaired = {
        "applicant_name": "Maria Silva",
        "cpf": "12345678901",
        "monthly_income": "10000.00",
        "credit_score": 650,
    }
    decision = await create_proposal(broken, healer=FakeHealer(repaired=repaired))
    assert decision.status is ProposalStatus.APPROVED
    assert decision.credit_limit == Decimal("1000.00")
