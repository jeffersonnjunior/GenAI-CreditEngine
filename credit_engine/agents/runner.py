"""Execute the compiled proposal LangGraph."""

from __future__ import annotations

from typing import Any

from credit_engine.agents.graph import build_proposal_graph
from credit_engine.clients.bureau.protocol import BureauClient
from credit_engine.llm.protocol import Healer
from credit_engine.models.proposal import CreditDecision


async def run_proposal_graph(
    payload: dict[str, Any],
    *,
    healer: Healer | None = None,
    bureau: BureauClient | None = None,
) -> CreditDecision:
    """Run heal → evaluate → persist and return the credit decision."""
    graph = build_proposal_graph(healer=healer, bureau=bureau)
    result = await graph.ainvoke(
        {
            "raw_payload": payload,
            "proposal": None,
            "decision": None,
        }
    )
    decision = result.get("decision")
    if decision is None:
        msg = "proposal graph finished without a decision"
        raise RuntimeError(msg)
    return decision
