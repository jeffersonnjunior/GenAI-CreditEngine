import base64
from io import BytesIO

import pytest
from PIL import Image

from credit_engine.core.common.enums.proposal import ProposalStatus
from credit_engine.models.proposal import ProposalCreate
from credit_engine.vision.verify import apply_vision_to_decision, verify_cnh
from credit_engine.services.risk import evaluate_proposal


def _tiny_png_base64() -> str:
    buf = BytesIO()
    Image.new("RGB", (8, 8), color="white").save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("ascii")


class FixedScoreBureau:
    def __init__(self, score: int) -> None:
        self._score = score

    async def fetch_credit_score(self, cpf: str) -> int:
        _ = cpf
        return self._score


def _proposal() -> ProposalCreate:
    return ProposalCreate(
        applicant_name="Maria Silva",
        cpf="12345678901",
        monthly_income="10000.00",
        credit_score=650,
    )


def test_verify_cnh_skips_when_no_document() -> None:
    result = verify_cnh(_proposal(), {})
    assert result.checked is False
    assert result.matched is True


def test_verify_cnh_matches_extract(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("credit_engine.vision.verify.settings.BACKEND", "stub")
    payload = {
        "document_image": _tiny_png_base64(),
        "cnh_extract": {
            "applicant_name": "Maria Silva",
            "cpf": "123.456.789-01",
        },
    }
    result = verify_cnh(_proposal(), payload)
    assert result.checked is True
    assert result.matched is True


def test_verify_cnh_mismatch_routes_to_pending_review(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("credit_engine.vision.verify.settings.BACKEND", "stub")
    payload = {
        "document_image": _tiny_png_base64(),
        "cnh_extract": {
            "applicant_name": "Outra Pessoa",
            "cpf": "12345678901",
        },
    }
    result = verify_cnh(_proposal(), payload)
    assert result.checked is True
    assert result.matched is False
    assert "nome" in result.message.lower() or "Outra" in result.message


async def test_apply_vision_on_graph_path_pending_review(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("credit_engine.vision.verify.settings.BACKEND", "stub")
    proposal = _proposal()
    base = await evaluate_proposal(proposal, bureau=FixedScoreBureau(650))
    assert base.status is ProposalStatus.APPROVED
    updated = apply_vision_to_decision(
        proposal,
        base,
        {
            "document_image": _tiny_png_base64(),
            "cnh_extract": {
                "applicant_name": "Maria Silva",
                "cpf": "99999999999",
            },
        },
    )
    assert updated.status is ProposalStatus.PENDING_REVIEW
    assert "Antifraude CNH" in updated.reason


def test_verify_cnh_required_without_document(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("credit_engine.vision.verify.settings.CNH_REQUIRED", True)
    result = verify_cnh(_proposal(), {})
    assert result.checked is True
    assert result.matched is False
