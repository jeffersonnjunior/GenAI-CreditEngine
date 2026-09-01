from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI

from credit_engine.agents.checkpointer import close_checkpointer, init_checkpointer
from credit_engine.core.config import Settings
from credit_engine.dao import init_db


def lifespan_factory(
    settings: Settings,
) -> Callable[[FastAPI], AsyncIterator[None]]:
    """Create an application lifespan context manager."""

    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
        _ = settings
        await init_db()
        await init_checkpointer()
        yield
        await close_checkpointer()

    return lifespan
