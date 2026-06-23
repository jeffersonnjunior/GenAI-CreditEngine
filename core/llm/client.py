import json
import re
from typing import Any

import httpx
from pydantic import ValidationError

from core.config import LLMSettings


class LLMClient:
    def __init__(self, config: LLMSettings) -> None:
        self._config = config

    async def heal_json(
        self,
        payload: dict[str, Any],
        schema: dict[str, Any],
        validation_error: ValidationError,
    ) -> dict[str, Any]:
        if self._config.use_mock:
            return MockLLMClient.heal(payload, validation_error)

        system_prompt = (
            "You fix invalid JSON payloads for a credit onboarding API. "
            "Return ONLY a valid JSON object matching the provided schema. "
            "Do not include markdown fences or explanations."
        )
        user_prompt = json.dumps(
            {
                "invalid_payload": payload,
                "json_schema": schema,
                "validation_errors": validation_error.errors(include_url=False),
            },
            ensure_ascii=False,
            indent=2,
        )

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self._config.base_url.rstrip('/')}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self._config.api_key.get_secret_value()}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self._config.model,
                    "temperature": 0,
                    "response_format": {"type": "json_object"},
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                },
            )
            response.raise_for_status()

        content = response.json()["choices"][0]["message"]["content"]
        return json.loads(content)


class MockLLMClient:
    _FIELD_ALIASES: dict[str, str] = {
        "nome": "full_name",
        "name": "full_name",
        "nome_completo": "full_name",
        "renda": "monthly_income",
        "renda_mensal": "monthly_income",
        "income": "monthly_income",
        "regiao": "region",
        "score": "credit_score",
        "creditscore": "credit_score",
        "tipo_conta": "account_type",
    }

    _REGION_ALIASES: dict[str, str] = {
        "sul": "Sul",
        "sudeste": "Sudeste",
        "norte": "Norte",
        "nordeste": "Nordeste",
        "centro-oeste": "Centro-Oeste",
        "centro oeste": "Centro-Oeste",
    }

    @classmethod
    def heal(cls, payload: dict[str, Any], validation_error: ValidationError) -> dict[str, Any]:
        healed: dict[str, Any] = {}
        for key, value in payload.items():
            normalized_key = cls._FIELD_ALIASES.get(key.lower(), key)
            healed[normalized_key] = cls._coerce_value(normalized_key, value)

        for error in validation_error.errors(include_url=False):
            loc = error.get("loc", ())
            if not loc:
                continue
            field = str(loc[0])
            if field in healed:
                healed[field] = cls._coerce_value(field, healed[field])

        return healed

    @classmethod
    def _coerce_value(cls, field: str, value: Any) -> Any:
        if field == "region" and isinstance(value, str):
            return cls._REGION_ALIASES.get(value.strip().lower(), value.strip())

        if field == "monthly_income":
            return cls._parse_number(value)

        if field == "credit_score" and value is not None:
            parsed = cls._parse_number(value)
            return int(parsed) if parsed is not None else value

        if field == "cpf" and isinstance(value, str):
            return re.sub(r"\D", "", value)

        if field == "full_name" and isinstance(value, str):
            return " ".join(value.split())

        if field == "account_type" and isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"corrente", "poupanca"}:
                return normalized

        return value

    @staticmethod
    def _parse_number(value: Any) -> float | None:
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            cleaned = value.replace("R$", "").replace(".", "").replace(",", ".").strip()
            try:
                return float(cleaned)
            except ValueError:
                return None
        return None
