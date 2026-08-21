"""Retrieve compliance excerpts for a credit decision context."""

from __future__ import annotations

from credit_engine.core.common.enums.proposal import ProposalStatus
from credit_engine.core.common.enums.risk import RiskBand
from credit_engine.core.config import settings
from credit_engine.rag.store import ComplianceStore, get_compliance_store


def build_retrieval_query(
    *,
    score: int,
    band: RiskBand,
    status: ProposalStatus,
    emergency: bool = False,
) -> str:
    """Build a natural-language query aligned with the decision context."""
    if emergency:
        return (
            "contingência birô indisponível limite emergencial "
            "degradação estrutural R$ 500"
        )
    if band is RiskBand.DENIED or status is ProposalStatus.DENIED:
        return (
            f"score {score} abaixo do mínimo negação limite zero "
            "faixas de score"
        )
    if band is RiskBand.PREMIUM:
        return (
            f"score {score} aprovação limite 30% da renda "
            "faixas de score premium"
        )
    return (
        f"score {score} aprovação limite 10% da renda "
        "faixas de score padrão"
    )


def retrieve_compliance_excerpts(
    *,
    score: int,
    band: RiskBand,
    status: ProposalStatus,
    emergency: bool = False,
    store: ComplianceStore | None = None,
) -> list[str]:
    """Fetch top-k policy excerpts for the decision, or [] if RAG is off."""
    if not settings.ENABLED and store is None:
        return []
    active = store or get_compliance_store()
    query = build_retrieval_query(
        score=score,
        band=band,
        status=status,
        emergency=emergency,
    )
    return active.query(query, top_k=settings.TOP_K)
