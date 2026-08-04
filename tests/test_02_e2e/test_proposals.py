from decimal import Decimal

from httpx import ASGITransport, AsyncClient

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


async def test_create_proposal_approved() -> None:
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
    assert Decimal(body["credit_limit"]) == Decimal("800.00")
