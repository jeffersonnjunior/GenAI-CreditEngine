from fastapi import FastAPI

from core.config import settings
from core.lifespan import lifespan


def get_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        debug=settings.debug,
        lifespan=lifespan,
    )
    return app
