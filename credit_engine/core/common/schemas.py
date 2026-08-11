from typing import Any

from pydantic import BaseModel


class MessageResponse(BaseModel):
    """Generic message envelope."""

    message: str | dict[Any, Any]
