from fastapi import APIRouter, status

from credit_engine.models.proposal import CreditDecision, ProposalCreate
from credit_engine.services import proposal as proposal_service

proposals_router = APIRouter()


@proposals_router.post(
    "",
    response_model=CreditDecision,
    status_code=status.HTTP_200_OK,
)
async def create_proposal(payload: ProposalCreate) -> CreditDecision:
    """Ingest a proposal and return a structured credit decision."""
    return await proposal_service.create_proposal(payload)
