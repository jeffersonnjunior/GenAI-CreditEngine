from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from credit_engine.clients.bureau.exc import BureauUnavailableError
from credit_engine.clients.bureau.factory import get_bureau
from credit_engine.clients.bureau.http import HttpBureauClient
from credit_engine.core.config import settings


def _mock_async_client(response: httpx.Response | Exception) -> MagicMock:
    client = MagicMock()
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=None)
    if isinstance(response, Exception):
        client.get = AsyncMock(side_effect=response)
    else:
        client.get = AsyncMock(return_value=response)
    return client


async def test_http_bureau_parses_score(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "BASE_URL", "http://bureau.test")
    monkeypatch.setattr(settings, "TIMEOUT_SECONDS", 1.0)

    response = httpx.Response(
        200,
        json={"credit_score": 720},
        request=httpx.Request("GET", "http://bureau.test/score/12345678901"),
    )
    with patch(
        "credit_engine.clients.bureau.http.httpx.AsyncClient",
        return_value=_mock_async_client(response),
    ):
        score = await HttpBureauClient().fetch_credit_score("12345678901")

    assert score == 720


async def test_http_bureau_timeout_raises_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "BASE_URL", "http://bureau.test")

    with patch(
        "credit_engine.clients.bureau.http.httpx.AsyncClient",
        return_value=_mock_async_client(httpx.TimeoutException("timed out")),
    ):
        with pytest.raises(BureauUnavailableError):
            await HttpBureauClient().fetch_credit_score("12345678901")


async def test_http_bureau_missing_base_url_raises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "BASE_URL", "")
    with pytest.raises(BureauUnavailableError):
        await HttpBureauClient().fetch_credit_score("12345678901")


def test_factory_resolves_http(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "CLIENT", "http")
    monkeypatch.setattr(settings, "BASE_URL", "http://bureau.test")
    client = get_bureau()
    assert isinstance(client, HttpBureauClient)
