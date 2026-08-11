import uvicorn

from credit_engine.core.config import settings


def main() -> None:
    """Entrypoint of the application."""
    uvicorn.run(
        "credit_engine.core.setup.app:get_app",
        workers=settings.WORKERS_COUNT,
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
        log_level=settings.LOG_LEVEL.value.lower(),
        factory=True,
    )


if __name__ == "__main__":
    main()
