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
