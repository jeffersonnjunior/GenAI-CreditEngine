from decimal import Decimal

import pytest
from httpx import ASGITransport, AsyncClient

from credit_engine.core.config import settings
from credit_engine.core.setup.app import get_app


async def test_health() -> None:
    app = get_app()
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"message": "OK"}


async def test_create_proposal_approved_standard_band() -> None:
    app = get_app()
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/api/v1/proposals",
            json={
                "applicant_name": "Maria Silva",
                "cpf": "123.456.789-01",
                "monthly_income": "8000.00",
                "credit_score": 650,
            },
        )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "approved"
    assert Decimal(body["credit_limit"]) == Decimal("800.00")


async def test_create_proposal_approved_premium_band(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "STUB_DEFAULT_SCORE", 720)
    app = get_app()
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/api/v1/proposals",
            json={
                "applicant_name": "Maria Silva",
                "cpf": "123.456.789-01",
                "monthly_income": "8000.00",
                "credit_score": 720,
            },
        )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "approved"
    assert Decimal(body["credit_limit"]) == Decimal("2400.00")


async def test_create_proposal_invalid_payload_returns_422() -> None:
    app = get_app()
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/api/v1/proposals",
            json={"applicant_name": "Maria Silva"},
        )
    assert response.status_code == 422
    body = response.json()
    assert "healing attempts" in body["detail"]["message"]
    assert body["detail"]["errors"]


async def test_create_proposal_bureau_unavailable_emergency_limit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "CLIENT", "unavailable")
    app = get_app()
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/api/v1/proposals",
            json={
                "applicant_name": "Ana Costa",
                "cpf": "123.456.789-01",
                "monthly_income": "20000.00",
                "credit_score": 900,
            },
        )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "approved"
    assert Decimal(body["credit_limit"]) == Decimal("500.00")
    assert body["degradation_mode"] == "bureau_unavailable"
    assert body["degradation_log"] is not None


async def test_hitl_pending_get_and_override_approve(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Premium income above autonomous cap → pending_review → analyst approve."""
    monkeypatch.setattr(settings, "STUB_DEFAULT_SCORE", 720)
    app = get_app()
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        created = await client.post(
            "/api/v1/proposals",
            json={
                "applicant_name": "Carlos Lima",
                "cpf": "123.456.789-01",
                "monthly_income": "50000.00",
                "credit_score": 720,
            },
        )
        assert created.status_code == 200
        body = created.json()
        assert body["status"] == "pending_review"
        assert Decimal(body["credit_limit"]) == Decimal("15000.00")
        proposal_id = body["proposal_id"]

        fetched = await client.get(f"/api/v1/proposals/{proposal_id}")
        assert fetched.status_code == 200
        assert fetched.json()["status"] == "pending_review"

        overridden = await client.post(
            f"/api/v1/proposals/{proposal_id}/override",
            json={
                "decision": "approve",
                "analyst": "Ana Analista",
                "note": "renda comprovada",
            },
        )
        assert overridden.status_code == 200
        out = overridden.json()
        assert out["status"] == "approved"
        assert Decimal(out["credit_limit"]) == Decimal("15000.00")
        assert out["analyst"] == "Ana Analista"
        assert out["override_note"] == "renda comprovada"

        conflict = await client.post(
            f"/api/v1/proposals/{proposal_id}/override",
            json={"decision": "deny", "analyst": "Outro"},
        )
        assert conflict.status_code == 409


async def test_hitl_override_deny(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "STUB_DEFAULT_SCORE", 720)
    app = get_app()
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        created = await client.post(
            "/api/v1/proposals",
            json={
                "applicant_name": "Carlos Lima",
                "cpf": "123.456.789-01",
                "monthly_income": "50000.00",
                "credit_score": 720,
            },
        )
        proposal_id = created.json()["proposal_id"]
        denied = await client.post(
            f"/api/v1/proposals/{proposal_id}/override",
            json={"decision": "deny", "analyst": "Ana Analista"},
        )
    assert denied.status_code == 200
    body = denied.json()
    assert body["status"] == "denied"
    assert Decimal(body["credit_limit"]) == Decimal("0.00")


async def test_get_proposal_not_found() -> None:
    app = get_app()
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get(
            "/api/v1/proposals/00000000-0000-0000-0000-000000000001"
        )
    assert response.status_code == 404
