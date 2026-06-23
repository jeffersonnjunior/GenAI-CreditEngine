from typing import Any

from fastapi import APIRouter, Depends, Request

from schemas.proposal import IngestionResponse
from services.ingestion.service import IngestionService, build_ingestion_service

router = APIRouter()


def get_ingestion_service(request: Request) -> IngestionService:
    return build_ingestion_service(request.app.state)


@router.post("/ingest", response_model=IngestionResponse)
async def ingest_proposal(
    payload: dict[str, Any],
    service: IngestionService = Depends(get_ingestion_service),
) -> IngestionResponse:
    return await service.ingest(payload)
