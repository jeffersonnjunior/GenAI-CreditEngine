"""CNH cross-check against proposal identity fields."""

from __future__ import annotations

import base64
import binascii
import re
from io import BytesIO
from typing import Any

from PIL import Image, UnidentifiedImageError

from credit_engine.core.common.enums.proposal import ProposalStatus
from credit_engine.core.config import settings
from credit_engine.models.proposal import CreditDecision, ProposalCreate
from credit_engine.vision.models import CnhExtract, VisionCheckResult

_CPF_RE = re.compile(r"\D")


def _normalize_cpf(value: str) -> str:
    return _CPF_RE.sub("", value)


def _normalize_name(value: str) -> str:
    return " ".join(value.lower().split())


def _parse_cnh_extract(raw: Any) -> CnhExtract | None:
    if raw is None:
        return None
    if isinstance(raw, CnhExtract):
        return raw
    if isinstance(raw, dict):
        return CnhExtract.model_validate(raw)
    return None


def _decode_document_image(document_image: str) -> None:
    """Validate that the payload is decodable image bytes (Pillow)."""
    try:
        raw = base64.b64decode(document_image, validate=True)
    except (binascii.Error, ValueError) as exc:
        msg = "document_image is not valid base64"
        raise ValueError(msg) from exc
    try:
        with Image.open(BytesIO(raw)) as img:
            img.verify()
    except (UnidentifiedImageError, OSError) as exc:
        msg = "document_image is not a supported image"
        raise ValueError(msg) from exc


def verify_cnh(
    proposal: ProposalCreate,
    raw_payload: dict[str, Any],
) -> VisionCheckResult:
    """Cross-check CNH extract (stub OCR) with proposal name/CPF."""
    if not settings.CNH_ENABLED:
        return VisionCheckResult(checked=False, matched=True, message="vision disabled")

    document_image = raw_payload.get("document_image")
    extract = _parse_cnh_extract(raw_payload.get("cnh_extract"))

    if not document_image and extract is None:
        if settings.CNH_REQUIRED:
            return VisionCheckResult(
                checked=True,
                matched=False,
                message="CNH document or cnh_extract required",
            )
        return VisionCheckResult(checked=False, matched=True, message="no document provided")

    if document_image:
        if settings.BACKEND == "pillow":
            _decode_document_image(str(document_image))
        elif settings.BACKEND != "stub":
            msg = f"Unknown vision backend '{settings.BACKEND}'"
            raise NotImplementedError(msg)

    if extract is None:
        return VisionCheckResult(
            checked=True,
            matched=False,
            message="CNH present but OCR/extract unavailable; manual review",
        )

    proposal_cpf = _normalize_cpf(proposal.cpf)
    extract_cpf = _normalize_cpf(extract.cpf)
    name_match = _normalize_name(proposal.applicant_name) == _normalize_name(
        extract.applicant_name
    )
    cpf_match = proposal_cpf == extract_cpf

    if name_match and cpf_match:
        return VisionCheckResult(
            checked=True,
            matched=True,
            message="CNH matches proposal identity",
            extracted=extract,
        )

    details: list[str] = []
    if not name_match:
        details.append(
            f"nome proposta='{proposal.applicant_name}' "
            f"vs CNH='{extract.applicant_name}'"
        )
    if not cpf_match:
        details.append(f"CPF proposta='{proposal_cpf}' vs CNH='{extract_cpf}'")
    return VisionCheckResult(
        checked=True,
        matched=False,
        message="; ".join(details),
        extracted=extract,
    )


def apply_vision_to_decision(
    proposal: ProposalCreate,
    decision: CreditDecision,
    raw_payload: dict[str, Any],
) -> CreditDecision:
    """Route mismatches to pending_review for analyst antifraude review."""
    if decision.status is ProposalStatus.DENIED:
        return decision
    result = verify_cnh(proposal, raw_payload)
    if not result.checked or result.matched:
        return decision
    return decision.model_copy(
        update={
            "status": ProposalStatus.PENDING_REVIEW,
            "reason": (
                f"{decision.reason}. Antifraude CNH: {result.message}"
            ),
        }
    )
