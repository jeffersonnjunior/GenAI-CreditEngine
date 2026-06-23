import uvicorn

from core.config import settings
from core.setup.app import get_app


def main() -> None:
    uvicorn.run(
        get_app,
        factory=True,
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )


if __name__ == "__main__":
    main()
