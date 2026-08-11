from credit_engine.models.proposal import CreditDecision, ProposalCreate
from credit_engine.services import risk as risk_service


async def create_proposal(payload: ProposalCreate) -> CreditDecision:
    """Create/evaluate a credit proposal (in-memory for now)."""
    return await risk_service.evaluate_proposal(payload)
