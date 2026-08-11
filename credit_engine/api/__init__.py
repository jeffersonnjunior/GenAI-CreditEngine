"""HTTP controllers (thin)."""

from fastapi import APIRouter

from credit_engine.api.misc import misc_router

api_router = APIRouter(prefix="/api")
api_router.include_router(misc_router)
