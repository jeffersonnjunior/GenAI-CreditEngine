"""LangGraph definition for the credit proposal pipeline."""

from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from credit_engine.agents.nodes import evaluate_node, heal_node, persist_node
from credit_engine.agents.state import ProposalGraphState
from credit_engine.clients.bureau.protocol import BureauClient
from credit_engine.llm.protocol import Healer


def build_proposal_graph(
    *,
    healer: Healer | None = None,
    bureau: BureauClient | None = None,
):
    """Compile heal → evaluate → persist as a LangGraph StateGraph."""

    async def _heal(state: ProposalGraphState) -> dict:
        return await heal_node(state, healer=healer)

    async def _evaluate(state: ProposalGraphState) -> dict:
        return await evaluate_node(state, bureau=bureau)

    graph = StateGraph(ProposalGraphState)
    graph.add_node("heal", _heal)
    graph.add_node("evaluate", _evaluate)
    graph.add_node("persist", persist_node)
    graph.add_edge(START, "heal")
    graph.add_edge("heal", "evaluate")
    graph.add_edge("evaluate", "persist")
    graph.add_edge("persist", END)
    return graph.compile()
