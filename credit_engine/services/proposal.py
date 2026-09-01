from decimal import Decimal
from typing import Any
from uuid import UUID

from credit_engine.agents.runner import resume_proposal_graph, run_proposal_graph
from credit_engine.clients.bureau.factory import get_bureau
from credit_engine.clients.bureau.protocol import BureauClient
from credit_engine.core.common.enums.proposal import ProposalStatus
from credit_engine.core.common.exc import Conflict, NotFound
from credit_engine.core.config import settings
from credit_engine.dao import (
    get_proposal,
    record_to_decision,
    save_decision,
    session_scope,
    update_proposal,
)
from credit_engine.llm.healing import heal_to_schema
from credit_engine.llm.protocol import Healer
from credit_engine.models.proposal import CreditDecision, OverrideRequest, ProposalCreate
from credit_engine.services import risk as risk_service


async def _create_proposal_linear(
    payload: dict[str, Any],
    *,
    healer: Healer | None = None,
    bureau: BureauClient | None = None,
) -> CreditDecision:
    """Legacy sequential path (heal → evaluate → persist)."""
    proposal = await heal_to_schema(payload, ProposalCreate, healer=healer)
    client = bureau or get_bureau()
    decision = await risk_service.evaluate_proposal(proposal, bureau=client)
    async with session_scope() as session:
        await save_decision(session, decision, proposal=proposal)
    return decision


async def create_proposal(
    payload: dict[str, Any],
    healer: Healer | None = None,
    bureau: BureauClient | None = None,
) -> CreditDecision:
    """Validate (and optionally heal) a proposal, then evaluate and persist."""
    if settings.ORCHESTRATOR == "linear":
        return await _create_proposal_linear(
            payload,
            healer=healer,
            bureau=bureau,
        )
    return await run_proposal_graph(payload, healer=healer, bureau=bureau)


async def get_proposal_decision(proposal_id: UUID) -> CreditDecision:
    """Load a persisted proposal decision by id."""
    async with session_scope() as session:
        record = await get_proposal(session, proposal_id)
        if record is None:
            raise NotFound(detail=f"Proposal {proposal_id} not found")
        return record_to_decision(record)


async def override_proposal(
    proposal_id: UUID,
    override: OverrideRequest,
) -> CreditDecision:
    """Apply analyst approve/deny on a pending_review proposal."""
    async with session_scope() as session:
        record = await get_proposal(session, proposal_id)
        if record is None:
            raise NotFound(detail=f"Proposal {proposal_id} not found")
        if record.status != ProposalStatus.PENDING_REVIEW.value:
            raise Conflict(
                detail=(
                    f"Proposal {proposal_id} is '{record.status}'; "
                    "only pending_review can be overridden"
                )
            )

    if settings.ORCHESTRATOR == "graph":
        return await resume_proposal_graph(proposal_id, override)

    async with session_scope() as session:
        record = await get_proposal(session, proposal_id)
        assert record is not None
        if override.decision == "approve":
            record.status = ProposalStatus.APPROVED.value
            record.reason = (
                f"{record.reason}. Override APPROVE by {override.analyst}"
            )
        else:
            record.status = ProposalStatus.DENIED.value
            record.credit_limit = Decimal("0.00")
            record.reason = (
                f"{record.reason}. Override DENY by {override.analyst}"
            )

        record.analyst = override.analyst
        record.override_note = override.note
        await update_proposal(session, record)
        return record_to_decision(record)
