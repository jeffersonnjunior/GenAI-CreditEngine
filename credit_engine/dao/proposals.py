"""Proposal persistence helpers."""

from __future__ import annotations

import json
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from credit_engine.core.common.enums.degradation import DegradationMode
from credit_engine.core.common.enums.proposal import ProposalStatus
from credit_engine.dao.models import ProposalRecord
from credit_engine.models.proposal import CreditDecision, ProposalCreate


def decision_to_record(
    decision: CreditDecision,
    *,
    cpf: str,
    monthly_income: object,
) -> ProposalRecord:
    """Map a CreditDecision into an ORM row."""
    return ProposalRecord(
        id=str(decision.proposal_id),
        applicant_name=decision.applicant_name,
        cpf=cpf,
        monthly_income=monthly_income,  # type: ignore[arg-type]
        status=decision.status.value,
        credit_limit=decision.credit_limit,
        credit_score=decision.credit_score,
        reason=decision.reason,
        degradation_mode=decision.degradation_mode.value,
        degradation_log=decision.degradation_log,
        compliance_excerpts_json=json.dumps(
            decision.compliance_excerpts,
            ensure_ascii=False,
        ),
        analyst=decision.analyst,
        override_note=decision.override_note,
    )


def record_to_decision(record: ProposalRecord) -> CreditDecision:
    """Map an ORM row back to CreditDecision."""
    excerpts = json.loads(record.compliance_excerpts_json or "[]")
    return CreditDecision(
        proposal_id=UUID(record.id),
        applicant_name=record.applicant_name,
        status=ProposalStatus(record.status),
        credit_limit=record.credit_limit,
        credit_score=record.credit_score,
        reason=record.reason,
        degradation_mode=DegradationMode(record.degradation_mode),
        degradation_log=record.degradation_log,
        compliance_excerpts=list(excerpts),
        analyst=record.analyst,
        override_note=record.override_note,
    )


async def save_decision(
    session: AsyncSession,
    decision: CreditDecision,
    *,
    proposal: ProposalCreate,
) -> CreditDecision:
    """Insert a new proposal decision."""
    session.add(
        decision_to_record(
            decision,
            cpf=proposal.cpf,
            monthly_income=proposal.monthly_income,
        )
    )
    await session.commit()
    return decision


async def get_proposal(
    session: AsyncSession,
    proposal_id: UUID,
) -> ProposalRecord | None:
    """Load a proposal row by id."""
    result = await session.execute(
        select(ProposalRecord).where(ProposalRecord.id == str(proposal_id))
    )
    return result.scalar_one_or_none()


async def update_proposal(session: AsyncSession, record: ProposalRecord) -> None:
    """Persist mutations on an existing proposal row."""
    session.add(record)
    await session.commit()
    await session.refresh(record)
