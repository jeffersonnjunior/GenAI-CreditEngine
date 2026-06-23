from typing import Literal

from pydantic import BaseModel, Field, field_validator


class CreditProposal(BaseModel):
    full_name: str = Field(min_length=2, description="Nome completo do titular")
    cpf: str = Field(description="CPF com 11 dígitos numéricos")
    monthly_income: float = Field(gt=0, description="Renda mensal comprovada em reais")
    region: Literal["Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul"]
    credit_score: int | None = Field(default=None, ge=0, le=1000)
    account_type: Literal["corrente", "poupanca"] = "corrente"

    @field_validator("cpf")
    @classmethod
    def validate_cpf(cls, value: str) -> str:
        digits = "".join(c for c in value if c.isdigit())
        if len(digits) != 11:
            raise ValueError("CPF must contain exactly 11 digits")
        return digits

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, value: str) -> str:
        return " ".join(value.split())


class ComplianceRuleHit(BaseModel):
    rule_text: str
    relevance_score: float
    chunk_type: str
    source: str = "compliance_manual"


class IngestionResponse(BaseModel):
    proposal: CreditProposal
    healing_attempts: int
    compliance_rules: list[ComplianceRuleHit]
