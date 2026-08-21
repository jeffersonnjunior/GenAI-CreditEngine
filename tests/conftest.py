import pytest


@pytest.fixture(autouse=True)
def _disable_rag_unless_injected(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep default decision tests free of Chroma I/O; RAG tests inject a store."""
    monkeypatch.setattr("credit_engine.rag.retrieve.settings.ENABLED", False)
