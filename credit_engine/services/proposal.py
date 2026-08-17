from typing import Any

from credit_engine.llm.healing import heal_to_schema
from credit_engine.llm.protocol import Healer
from credit_engine.models.proposal import CreditDecision, ProposalCreate
from credit_engine.services import risk as risk_service


async def create_proposal(
    payload: dict[str, Any],
    healer: Healer | None = None,
) -> CreditDecision:
    """Validate (and optionally heal) a proposal, then evaluate credit risk."""
    proposal = await heal_to_schema(payload, ProposalCreate, healer=healer)
    return await risk_service.evaluate_proposal(proposal)
