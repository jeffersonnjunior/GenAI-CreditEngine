from typing import Any

from pydantic import ValidationError

from core.common.exceptions import IngestionValidationError
from core.config import LLMSettings
from core.llm.client import LLMClient
from schemas.proposal import CreditProposal


class SelfHealingValidator:
    def __init__(self, llm_client: LLMClient, settings: LLMSettings) -> None:
        self._llm = llm_client
        self._max_attempts = settings.max_healing_attempts
        self._schema = CreditProposal.model_json_schema()

    async def validate(self, raw: dict[str, Any]) -> tuple[CreditProposal, int]:
        current = dict(raw)

        for attempt in range(1, self._max_attempts + 1):
            try:
                return CreditProposal.model_validate(current), attempt
            except ValidationError as exc:
                if attempt >= self._max_attempts:
                    raise IngestionValidationError(
                        detail="Payload could not be healed within the allowed attempts.",
                        attempts=attempt,
                    ) from exc
                current = await self._llm.heal_json(current, self._schema, exc)

        raise IngestionValidationError(
            detail="Payload could not be healed within the allowed attempts.",
            attempts=self._max_attempts,
        )
