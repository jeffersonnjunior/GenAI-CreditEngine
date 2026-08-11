from decimal import Decimal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator

from credit_engine.core.common.enums.proposal import ProposalStatus


class ProposalCreate(BaseModel):
    """Inbound payload for a credit proposal."""

    applicant_name: str = Field(min_length=1, max_length=200)
    cpf: str = Field(min_length=11, max_length=14)
    monthly_income: Decimal = Field(gt=0, decimal_places=2)
    credit_score: int = Field(ge=0, le=1000)

    @field_validator("cpf")
    @classmethod
    def strip_cpf(cls, value: str) -> str:
        """Normalize CPF to digits only."""
        digits = "".join(ch for ch in value if ch.isdigit())
        if len(digits) != 11:
            msg = "CPF must contain exactly 11 digits"
            raise ValueError(msg)
        return digits


class CreditDecision(BaseModel):
    """Canonical structured output for a credit decision (Pydantic-strict)."""

    proposal_id: UUID = Field(default_factory=uuid4)
    applicant_name: str
    status: ProposalStatus
    credit_limit: Decimal = Field(ge=0, decimal_places=2)
    credit_score: int
    reason: str
