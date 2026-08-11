from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI

from credit_engine.core.config import Settings


def lifespan_factory(
    settings: Settings,
) -> Callable[[FastAPI], AsyncIterator[None]]:
    """Create an application lifespan context manager."""

    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
        # Boot hooks (DB, Redis, Taskiq, Chroma…) land here in later sprints.
        _ = settings
        yield

    return lifespan
