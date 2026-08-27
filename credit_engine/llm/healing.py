from typing import Any

from pydantic import BaseModel, ValidationError

from credit_engine.core.common.exc import HealingExhausted
from credit_engine.core.config import settings
from credit_engine.llm.factory import get_healer
from credit_engine.llm.protocol import Healer


async def heal_to_schema[SchemaT: BaseModel](
    payload: dict[str, Any],
    schema: type[SchemaT],
    healer: Healer | None = None,
) -> SchemaT:
    """Validate payload against schema, repairing up to MAX_ATTEMPTS times.

    The first parse is free. Each ValidationError triggers one heal attempt
    (backend from ``LLM_BACKEND``). After exhausting attempts, fail typed.
    """
    active_healer = healer or get_healer()
    current = payload
    last_error: ValidationError | None = None

    for attempt in range(settings.MAX_ATTEMPTS + 1):
        try:
            return schema.model_validate(current)
        except ValidationError as exc:
            last_error = exc
            if attempt >= settings.MAX_ATTEMPTS:
                break
            current = await active_healer.repair(current, exc)

    errors = last_error.errors() if last_error is not None else []
    raise HealingExhausted(errors=errors)
