from typing import Any
from uuid import UUID

from fastapi import APIRouter, status

from credit_engine.models.proposal import CreditDecision, OverrideRequest
from credit_engine.services import proposal as proposal_service

proposals_router = APIRouter()


@proposals_router.post(
    "",
    response_model=CreditDecision,
    status_code=status.HTTP_200_OK,
)
async def create_proposal(payload: dict[str, Any]) -> CreditDecision:
    """Ingest a proposal, heal invalid shape up to 3 times, then decide."""
    return await proposal_service.create_proposal(payload)


@proposals_router.get(
    "/{proposal_id}",
    response_model=CreditDecision,
    status_code=status.HTTP_200_OK,
)
async def get_proposal(proposal_id: UUID) -> CreditDecision:
    """Fetch a persisted proposal decision by id."""
    return await proposal_service.get_proposal_decision(proposal_id)


@proposals_router.post(
    "/{proposal_id}/override",
    response_model=CreditDecision,
    status_code=status.HTTP_200_OK,
)
async def override_proposal(
    proposal_id: UUID,
    body: OverrideRequest,
) -> CreditDecision:
    """Human-in-the-loop override for pending_review proposals."""
    return await proposal_service.override_proposal(proposal_id, body)
