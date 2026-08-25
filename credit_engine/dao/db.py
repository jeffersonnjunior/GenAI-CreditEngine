"""SQLAlchemy async engine and session factory."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool

from credit_engine.core.config import settings

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def _ensure_sqlite_parent(url: str) -> None:
    if not url.startswith("sqlite"):
        return
    # sqlite+aiosqlite:///./data/file.db  or  sqlite+aiosqlite:///:memory:
    if ":memory:" in url:
        return
    raw = url.split("sqlite+aiosqlite:///", 1)[-1]
    path = Path(raw)
    if path.parent.as_posix() not in {"", "."}:
        path.parent.mkdir(parents=True, exist_ok=True)


def get_engine() -> AsyncEngine:
    """Return (and lazily create) the process-wide async engine."""
    global _engine, _session_factory
    if _engine is None:
        url = settings.URL
        _ensure_sqlite_parent(url)
        kwargs: dict[str, object] = {"future": True}
        if url.startswith("sqlite") and ":memory:" in url:
            kwargs["connect_args"] = {"check_same_thread": False}
            kwargs["poolclass"] = StaticPool
        _engine = create_async_engine(url, **kwargs)
        _session_factory = async_sessionmaker(
            _engine,
            expire_on_commit=False,
            class_=AsyncSession,
        )
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Return the async session factory."""
    get_engine()
    assert _session_factory is not None
    return _session_factory


async def init_db() -> None:
    """Create tables if they do not exist."""
    from credit_engine.dao.models import Base

    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@asynccontextmanager
async def session_scope() -> AsyncIterator[AsyncSession]:
    """Yield a short-lived session (caller commits)."""
    factory = get_session_factory()
    async with factory() as session:
        yield session


def reset_engine() -> None:
    """Drop cached engine (tests)."""
    global _engine, _session_factory
    _engine = None
    _session_factory = None
