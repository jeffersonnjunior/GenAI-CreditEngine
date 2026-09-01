"""LangGraph checkpointer lifecycle (SQLite or in-memory)."""

from __future__ import annotations

from pathlib import Path

import aiosqlite
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from credit_engine.core.config import EnvEnum, settings

_checkpointer: BaseCheckpointSaver | None = None
_sqlite_conn: aiosqlite.Connection | None = None


def get_checkpointer() -> BaseCheckpointSaver:
    """Return the process-wide LangGraph checkpointer."""
    global _checkpointer
    if _checkpointer is None:
        _checkpointer = InMemorySaver()
    return _checkpointer


async def init_checkpointer() -> None:
    """Bootstrap the checkpointer (SQLite in local/dev, memory in tests)."""
    global _checkpointer, _sqlite_conn
    if _checkpointer is not None:
        return
    if settings.ENV is EnvEnum.TEST or settings.CHECKPOINT_BACKEND == "memory":
        _checkpointer = InMemorySaver()
        return
    path = Path(settings.CHECKPOINT_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    _sqlite_conn = await aiosqlite.connect(str(path))
    _checkpointer = AsyncSqliteSaver(_sqlite_conn)


async def close_checkpointer() -> None:
    """Close SQLite connection and drop cached saver."""
    global _checkpointer, _sqlite_conn
    if _sqlite_conn is not None:
        await _sqlite_conn.close()
    _checkpointer = None
    _sqlite_conn = None


def reset_checkpointer() -> None:
    """Reset cached checkpointer (tests)."""
    global _checkpointer, _sqlite_conn
    _checkpointer = None
    _sqlite_conn = None
