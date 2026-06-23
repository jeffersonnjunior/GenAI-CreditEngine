from fastapi import FastAPI

from api.router import api_router
from core.config import settings
from core.lifespan import lifespan


def get_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        debug=settings.debug,
        lifespan=lifespan,
    )
    app.include_router(api_router)
    return app
