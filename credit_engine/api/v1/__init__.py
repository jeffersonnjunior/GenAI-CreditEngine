from fastapi import APIRouter

from credit_engine.api.v1.proposals import proposals_router

v1_router = APIRouter()
v1_router.include_router(proposals_router, prefix="/proposals", tags=["proposals"])
