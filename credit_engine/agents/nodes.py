"""LangGraph node functions for proposal ingestion."""

from __future__ import annotations

from decimal import Decimal
from typing import Any
from uuid import UUID

from langgraph.types import interrupt

from credit_engine.agents.state import ProposalGraphState
from credit_engine.clients.bureau.factory import get_bureau
from credit_engine.clients.bureau.protocol import BureauClient
from credit_engine.core.common.enums.proposal import ProposalStatus
from credit_engine.dao import get_proposal, save_decision, session_scope, update_proposal
from credit_engine.llm.healing import heal_to_schema
from credit_engine.llm.protocol import Healer
from credit_engine.models.proposal import CreditDecision, OverrideRequest, ProposalCreate
from credit_engine.services import risk as risk_service
from credit_engine.vision.verify import apply_vision_to_decision


def apply_override_to_decision(
    decision: CreditDecision,
    override_payload: dict[str, Any],
) -> CreditDecision:
    """Apply analyst approve/deny onto a pending_review decision."""
    override = OverrideRequest.model_validate(override_payload)
    if override.decision == "approve":
        return decision.model_copy(
            update={
                "status": ProposalStatus.APPROVED,
                "reason": (
                    f"{decision.reason}. Override APPROVE by {override.analyst}"
                ),
                "analyst": override.analyst,
                "override_note": override.note,
            }
        )
    return decision.model_copy(
        update={
            "status": ProposalStatus.DENIED,
            "credit_limit": Decimal("0.00"),
            "reason": (
                f"{decision.reason}. Override DENY by {override.analyst}"
            ),
            "analyst": override.analyst,
            "override_note": override.note,
        }
    )


async def heal_node(
    state: ProposalGraphState,
    *,
    healer: Healer | None = None,
) -> dict[str, ProposalCreate]:
    """Validate or self-heal the inbound proposal payload."""
    proposal = await heal_to_schema(
        state["raw_payload"],
        ProposalCreate,
        healer=healer,
    )
    return {"proposal": proposal}


async def evaluate_node(
    state: ProposalGraphState,
    *,
    bureau: BureauClient | None = None,
) -> dict:
    """Fetch bureau score, apply risk rules, and attach compliance excerpts."""
    proposal = state["proposal"]
    if proposal is None:
        msg = "evaluate_node requires a validated proposal"
        raise RuntimeError(msg)
    client = bureau or get_bureau()
    decision = await risk_service.evaluate_proposal(proposal, bureau=client)
    decision = decision.model_copy(
        update={"proposal_id": UUID(state["thread_id"])},
    )
    return {"decision": decision}


async def vision_node(state: ProposalGraphState) -> dict:
    """Cross-check CNH identity against the proposal (antifraude)."""
    proposal = state["proposal"]
    decision = state["decision"]
    if proposal is None or decision is None:
        msg = "vision_node requires proposal and decision"
        raise RuntimeError(msg)
    updated = apply_vision_to_decision(
        proposal,
        decision,
        state["raw_payload"],
    )
    if updated is decision:
        return {}
    return {"decision": updated}


async def persist_node(state: ProposalGraphState) -> dict:
    """Persist the decision snapshot to SQLite."""
    proposal = state["proposal"]
    decision = state["decision"]
    if proposal is None or decision is None:
        msg = "persist_node requires proposal and decision"
        raise RuntimeError(msg)
    async with session_scope() as session:
        await save_decision(session, decision, proposal=proposal)
    return {}


async def hitl_gate_node(state: ProposalGraphState) -> dict:
    """Pause the graph when human override is required (autonomous cap)."""
    decision = state["decision"]
    if decision is None:
        msg = "hitl_gate_node requires a decision"
        raise RuntimeError(msg)
    if decision.status is not ProposalStatus.PENDING_REVIEW:
        return {}
    override_payload = interrupt(
        {
            "proposal_id": str(decision.proposal_id),
            "status": decision.status.value,
            "message": "Awaiting analyst override",
        }
    )
    updated = apply_override_to_decision(decision, override_payload)
    return {"decision": updated}


async def finalize_persist_node(state: ProposalGraphState) -> dict:
    """Write analyst override results back to SQLite after graph resume."""
    decision = state["decision"]
    if decision is None or decision.analyst is None:
        return {}
    async with session_scope() as session:
        record = await get_proposal(session, decision.proposal_id)
        if record is None:
            msg = f"Proposal {decision.proposal_id} not found for finalize"
            raise RuntimeError(msg)
        record.status = decision.status.value
        record.credit_limit = decision.credit_limit
        record.reason = decision.reason
        record.analyst = decision.analyst
        record.override_note = decision.override_note
        await update_proposal(session, record)
    return {}
