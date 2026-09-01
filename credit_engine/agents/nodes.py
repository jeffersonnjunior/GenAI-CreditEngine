"""LangGraph node functions for proposal ingestion."""

from __future__ import annotations

from credit_engine.agents.state import ProposalGraphState
from credit_engine.clients.bureau.factory import get_bureau
from credit_engine.clients.bureau.protocol import BureauClient
from credit_engine.dao import save_decision, session_scope
from credit_engine.llm.healing import heal_to_schema
from credit_engine.llm.protocol import Healer
from credit_engine.models.proposal import ProposalCreate
from credit_engine.services import risk as risk_service


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
    return {"decision": decision}


async def persist_node(state: ProposalGraphState) -> dict:
    """Persist the final decision to SQLite."""
    proposal = state["proposal"]
    decision = state["decision"]
    if proposal is None or decision is None:
        msg = "persist_node requires proposal and decision"
        raise RuntimeError(msg)
    async with session_scope() as session:
        await save_decision(session, decision, proposal=proposal)
    return {}
