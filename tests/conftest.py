import pytest

from credit_engine.agents.checkpointer import reset_checkpointer
from credit_engine.core.config import settings
from credit_engine.dao import init_db, reset_engine


@pytest.fixture(autouse=True)
def _disable_rag_unless_injected(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep default decision tests free of Chroma I/O; RAG tests inject a store."""
    monkeypatch.setattr("credit_engine.rag.retrieve.settings.ENABLED", False)


@pytest.fixture(autouse=True)
def _memory_graph_checkpointer(monkeypatch: pytest.MonkeyPatch) -> None:
    """Use in-memory LangGraph checkpoints in tests."""
    monkeypatch.setattr(settings, "CHECKPOINT_BACKEND", "memory")
    reset_checkpointer()


@pytest.fixture(autouse=True)
async def _memory_db(monkeypatch: pytest.MonkeyPatch) -> None:
    """Isolate each test on an in-memory SQLite database."""
    monkeypatch.setattr(settings, "URL", "sqlite+aiosqlite:///:memory:")
    reset_engine()
    await init_db()
    yield
    reset_engine()
