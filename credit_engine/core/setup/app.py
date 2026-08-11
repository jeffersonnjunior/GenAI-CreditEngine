from fastapi import FastAPI

from credit_engine.api import api_router
from credit_engine.core.config import settings
from credit_engine.core.lifespan import lifespan_factory
from credit_engine.core.middleware.cors import cors_middleware


def get_app() -> FastAPI:
    """Build and return the FastAPI application instance."""
    app = FastAPI(
        lifespan=lifespan_factory(settings),
        title=settings.NAME,
        description=settings.DESCRIPTION,
        version=settings.VERSION,
    )
    app.include_router(api_router)
    cors_middleware(app, settings)
    return app
