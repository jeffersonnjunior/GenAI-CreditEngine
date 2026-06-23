from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from core.config import settings
from services.rag.indexer import ComplianceIndexer


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    engine: AsyncEngine = create_async_engine(
        settings.database.url,
        echo=settings.debug,
        pool_pre_ping=True,
    )
    session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )
    app.state.db_engine = engine
    app.state.db_session_factory = session_factory
    app.state.settings = settings

    settings.chroma.persist_dir.mkdir(parents=True, exist_ok=True)
    indexer = ComplianceIndexer(settings.chroma)
    if not indexer.is_indexed():
        indexer.index_manual(settings.compliance_manual_path)

    app.state.compliance_indexer = indexer

    yield
    await engine.dispose()
