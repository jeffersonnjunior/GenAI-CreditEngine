from fastapi import APIRouter

from credit_engine.core.common.schemas import MessageResponse

misc_router = APIRouter(tags=["misc"])


@misc_router.get("/ping")
async def ping() -> MessageResponse:
    """Liveness probe."""
    return MessageResponse(message="PONG")


@misc_router.get("/health")
async def health() -> MessageResponse:
    """Health check."""
    return MessageResponse(message="OK")
