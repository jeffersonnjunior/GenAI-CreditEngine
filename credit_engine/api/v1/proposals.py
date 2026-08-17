from typing import Any

from fastapi import APIRouter, status

from credit_engine.models.proposal import CreditDecision
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
