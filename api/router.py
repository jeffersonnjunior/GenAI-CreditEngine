from fastapi import APIRouter

from api.proposals import router as proposals_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(proposals_router, prefix="/proposals", tags=["proposals"])
