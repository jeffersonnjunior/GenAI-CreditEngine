"""LangGraph definition for the credit proposal pipeline."""

from __future__ import annotations

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, StateGraph

from credit_engine.agents.checkpointer import get_checkpointer
from credit_engine.agents.nodes import (
    evaluate_node,
    finalize_persist_node,
    heal_node,
    hitl_gate_node,
    persist_node,
)
from credit_engine.agents.state import ProposalGraphState
from credit_engine.clients.bureau.protocol import BureauClient
from credit_engine.llm.protocol import Healer


def build_proposal_graph(
    *,
    healer: Healer | None = None,
    bureau: BureauClient | None = None,
    checkpointer: BaseCheckpointSaver | None = None,
):
    """Compile heal → evaluate → persist → HITL → finalize as a StateGraph."""

    async def _heal(state: ProposalGraphState) -> dict:
        return await heal_node(state, healer=healer)

    async def _evaluate(state: ProposalGraphState) -> dict:
        return await evaluate_node(state, bureau=bureau)

    graph = StateGraph(ProposalGraphState)
    graph.add_node("heal", _heal)
    graph.add_node("evaluate", _evaluate)
    graph.add_node("persist", persist_node)
    graph.add_node("hitl_gate", hitl_gate_node)
    graph.add_node("finalize", finalize_persist_node)
    graph.add_edge(START, "heal")
    graph.add_edge("heal", "evaluate")
    graph.add_edge("evaluate", "persist")
    graph.add_edge("persist", "hitl_gate")
    graph.add_edge("hitl_gate", "finalize")
    graph.add_edge("finalize", END)
    saver = checkpointer if checkpointer is not None else get_checkpointer()
    return graph.compile(checkpointer=saver)
