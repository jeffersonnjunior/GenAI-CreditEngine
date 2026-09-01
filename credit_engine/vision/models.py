"""Structured CNH / document vision outputs."""

from __future__ import annotations

from pydantic import BaseModel, Field


class CnhExtract(BaseModel):
    """Fields read from a CNH (stub OCR or future real OCR)."""

    applicant_name: str = Field(min_length=1, max_length=200)
    cpf: str = Field(min_length=11, max_length=14)


class VisionCheckResult(BaseModel):
    """Outcome of cross-checking CNH data against the proposal payload."""

    checked: bool = False
    """Whether a document/extract was evaluated."""
    matched: bool = True
    """Whether CNH fields match the proposal."""
    message: str = ""
    extracted: CnhExtract | None = None
