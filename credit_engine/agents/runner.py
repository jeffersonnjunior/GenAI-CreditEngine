"""Execute the compiled proposal LangGraph."""

from __future__ import annotations

from typing import Any
from uuid import UUID, uuid4

from langgraph.types import Command

from credit_engine.agents.graph import build_proposal_graph
from credit_engine.clients.bureau.protocol import BureauClient
from credit_engine.llm.protocol import Healer
from credit_engine.models.proposal import CreditDecision, OverrideRequest


def _graph_config(thread_id: str) -> dict:
    return {"configurable": {"thread_id": thread_id}}


def _extract_decision(result: dict[str, Any]) -> CreditDecision:
    decision = result.get("decision")
    if decision is None:
        msg = "proposal graph finished without a decision"
        raise RuntimeError(msg)
    return decision


async def run_proposal_graph(
    payload: dict[str, Any],
    *,
    healer: Healer | None = None,
    bureau: BureauClient | None = None,
) -> CreditDecision:
    """Run heal → evaluate → persist → HITL gate and return the decision."""
    thread_id = str(uuid4())
    graph = build_proposal_graph(healer=healer, bureau=bureau)
    result = await graph.ainvoke(
        {
            "thread_id": thread_id,
            "raw_payload": payload,
            "proposal": None,
            "decision": None,
        },
        _graph_config(thread_id),
    )
    return _extract_decision(result)


async def resume_proposal_graph(
    proposal_id: UUID,
    override: OverrideRequest,
) -> CreditDecision:
    """Resume a paused graph after analyst override (Command resume)."""
    thread_id = str(proposal_id)
    graph = build_proposal_graph()
    result = await graph.ainvoke(
        Command(resume=override.model_dump()),
        _graph_config(thread_id),
    )
    return _extract_decision(result)
