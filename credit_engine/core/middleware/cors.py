from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from credit_engine.core.config import CORSSettings


def cors_middleware(app: FastAPI, settings: CORSSettings) -> None:
    """Attach CORS middleware to the application."""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ALLOW_ORIGINS,
        allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
        allow_methods=settings.CORS_ALLOW_METHODS,
        allow_headers=settings.CORS_ALLOW_HEADERS,
        expose_headers=settings.CORS_EXPOSE_HEADERS,
        max_age=settings.CORS_MAX_AGE,
    )
