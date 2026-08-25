"""ORM models for persisted credit proposals."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import DateTime, Integer, Numeric, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Declarative base for credit-engine tables."""


class ProposalRecord(Base):
    """Stored proposal decision (including HITL pending/override)."""

    __tablename__ = "proposals"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    applicant_name: Mapped[str] = mapped_column(String(200), nullable=False)
    cpf: Mapped[str] = mapped_column(String(11), nullable=False)
    monthly_income: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    credit_limit: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    credit_score: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    degradation_mode: Mapped[str] = mapped_column(String(64), nullable=False)
    degradation_log: Mapped[str | None] = mapped_column(Text, nullable=True)
    compliance_excerpts_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    analyst: Mapped[str | None] = mapped_column(String(200), nullable=True)
    override_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    @property
    def proposal_id(self) -> UUID:
        return UUID(self.id)
