import json
from typing import Any

import pytest
from pydantic import ValidationError

from credit_engine.llm.factory import get_healer
from credit_engine.llm.gemini import GeminiHealer
from credit_engine.llm.openai_compatible import OpenAICompatibleHealer
from credit_engine.llm.prompts import extract_json_object
from credit_engine.llm.stub import StubHealer
from credit_engine.models.proposal import ProposalCreate


def test_extract_json_object_plain() -> None:
    data = extract_json_object('{"applicant_name": "Maria", "credit_score": 650}')
    assert data["applicant_name"] == "Maria"
    assert data["credit_score"] == 650


def test_extract_json_object_markdown_fence() -> None:
    raw = '```json\n{"cpf": "12345678901", "monthly_income": "10000.00"}\n```'
    data = extract_json_object(raw)
    assert data["cpf"] == "12345678901"


def test_extract_json_object_rejects_non_object() -> None:
    with pytest.raises(TypeError):
        extract_json_object("[1, 2, 3]")


def test_get_healer_stub_by_default() -> None:
    healer = get_healer()
    assert isinstance(healer, StubHealer)


def test_get_healer_gemini(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "credit_engine.llm.factory.settings.BACKEND",
        "gemini",
    )
    monkeypatch.setattr(
        "credit_engine.llm.factory.settings.API_KEY",
        "test-key",
    )
    healer = get_healer()
    assert isinstance(healer, GeminiHealer)


def test_get_healer_openai_compatible(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "credit_engine.llm.factory.settings.BACKEND",
        "openai_compatible",
    )
    healer = get_healer()
    assert isinstance(healer, OpenAICompatibleHealer)


def test_get_healer_llama_alias(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "credit_engine.llm.factory.settings.BACKEND",
        "llama",
    )
    healer = get_healer()
    assert isinstance(healer, OpenAICompatibleHealer)


def test_get_healer_unknown_backend(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "credit_engine.llm.factory.settings.BACKEND",
        "not-a-backend",
    )
    with pytest.raises(NotImplementedError, match="not supported"):
        get_healer()


async def test_gemini_healer_repair_with_injected_complete() -> None:
    repaired = {
        "applicant_name": "Maria Silva",
        "cpf": "12345678901",
        "monthly_income": "10000.00",
        "credit_score": 650,
    }

    async def fake_complete(system: str, user: str) -> str:
        assert "repair" in system.lower() or "Repair" in system or "JSON" in system
        assert "Broken payload" in user
        return json.dumps(repaired)

    healer = GeminiHealer(complete=fake_complete)
    broken: dict[str, Any] = {"applicant_name": "Maria Silva"}
    try:
        ProposalCreate.model_validate(broken)
    except ValidationError as exc:
        result = await healer.repair(broken, exc)
    else:
        raise AssertionError("expected ValidationError")

    assert result == repaired
    assert ProposalCreate.model_validate(result).credit_score == 650


async def test_gemini_healer_requires_api_key_without_complete() -> None:
    healer = GeminiHealer(api_key="", complete=None)
    broken: dict[str, Any] = {"applicant_name": "X"}
    try:
        ProposalCreate.model_validate(broken)
    except ValidationError as exc:
        with pytest.raises(RuntimeError, match="LLM_API_KEY"):
            await healer.repair(broken, exc)
    else:
        raise AssertionError("expected ValidationError")


async def test_openai_healer_repair_with_injected_complete() -> None:
    repaired = {
        "applicant_name": "Maria Silva",
        "cpf": "12345678901",
        "monthly_income": "10000.00",
        "credit_score": 650,
    }

    async def fake_complete(system: str, user: str) -> str:
        assert "Broken payload" in user
        return json.dumps(repaired)

    healer = OpenAICompatibleHealer(complete=fake_complete)
    broken: dict[str, Any] = {"applicant_name": "Maria Silva"}
    try:
        ProposalCreate.model_validate(broken)
    except ValidationError as exc:
        result = await healer.repair(broken, exc)
    else:
        raise AssertionError("expected ValidationError")

    assert result == repaired


async def test_openai_healer_requires_base_url() -> None:
    healer = OpenAICompatibleHealer(base_url="", complete=None)
    broken: dict[str, Any] = {"applicant_name": "X"}
    try:
        ProposalCreate.model_validate(broken)
    except ValidationError as exc:
        with pytest.raises(RuntimeError, match="LLM_BASE_URL"):
            await healer.repair(broken, exc)
    else:
        raise AssertionError("expected ValidationError")
