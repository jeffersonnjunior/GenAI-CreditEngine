"""LangGraph state for the credit proposal pipeline."""

from __future__ import annotations

from typing import Any, TypedDict

from credit_engine.models.proposal import CreditDecision, ProposalCreate


class ProposalGraphState(TypedDict):
    """In-memory state passed between proposal graph nodes."""

    raw_payload: dict[str, Any]
    proposal: ProposalCreate | None
    decision: CreditDecision | None
