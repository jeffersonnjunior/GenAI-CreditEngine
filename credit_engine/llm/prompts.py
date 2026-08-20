"""Shared prompts and JSON parsing for payload self-healing."""

from __future__ import annotations

import json
import re
from typing import Any

from pydantic import ValidationError

_FENCE_RE = re.compile(
    r"```(?:json)?\s*([\s\S]*?)\s*```",
    re.IGNORECASE,
)

SYSTEM_PROMPT = """\
You repair invalid JSON payloads for a bank credit-proposal API.
Return ONLY a single JSON object — no markdown, no commentary.

Rules:
- Fix structure and types so the payload can pass schema validation.
- Normalize CPF to 11 digits when digits are present.
- Normalize monetary strings to a plain decimal string (e.g. "10000.00").
- Map obvious alternate keys when clear
  (nome→applicant_name, renda→monthly_income).
- Do NOT invent credit_score, monthly_income, CPF, or applicant_name
  if those values are absent from the input.
- Prefer omitting a missing field over fabricating business data.
"""


def build_repair_user_prompt(
    payload: dict[str, Any],
    error: ValidationError,
) -> str:
    """Build the user message with the broken payload and Pydantic errors."""
    errors = error.errors()
    return (
        "Broken payload:\n"
        f"{json.dumps(payload, ensure_ascii=False, default=str)}\n\n"
        "Pydantic validation errors:\n"
        f"{json.dumps(errors, ensure_ascii=False, default=str)}\n\n"
        "Return the repaired JSON object only."
    )


def extract_json_object(text: str) -> dict[str, Any]:
    """Parse a JSON object from model output, stripping markdown fences if needed."""
    cleaned = text.strip()
    fence = _FENCE_RE.search(cleaned)
    if fence:
        cleaned = fence.group(1).strip()

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start < 0 or end <= start:
            msg = "healer response did not contain a JSON object"
            raise ValueError(msg) from None
        data = json.loads(cleaned[start : end + 1])

    if not isinstance(data, dict):
        msg = "healer response must be a JSON object"
        raise TypeError(msg)
    return data
