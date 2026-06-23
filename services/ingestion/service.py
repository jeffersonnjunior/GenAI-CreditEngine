from typing import Any

from core.llm.client import LLMClient
from schemas.proposal import IngestionResponse
from services.ingestion.self_healing import SelfHealingValidator
from services.rag.retriever import ComplianceRetriever


class IngestionService:
    def __init__(
        self,
        validator: SelfHealingValidator,
        retriever: ComplianceRetriever,
    ) -> None:
        self._validator = validator
        self._retriever = retriever

    async def ingest(self, raw: dict[str, Any]) -> IngestionResponse:
        proposal, attempts = await self._validator.validate(raw)
        rules = self._retriever.retrieve_for_proposal(proposal)
        return IngestionResponse(
            proposal=proposal,
            healing_attempts=attempts,
            compliance_rules=rules,
        )


def build_ingestion_service(app_state: Any) -> IngestionService:
    llm_client = LLMClient(app_state.settings.llm)
    validator = SelfHealingValidator(llm_client, app_state.settings.llm)
    retriever = ComplianceRetriever(app_state.settings.chroma)
    return IngestionService(validator, retriever)
