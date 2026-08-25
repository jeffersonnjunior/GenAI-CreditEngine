from typing import Any

from fastapi import HTTPException, status


class _BaseHTTPException(HTTPException):
    """Base HTTP exception for typed API errors."""

    STATUS_CODE = status.HTTP_500_INTERNAL_SERVER_ERROR
    DETAIL: str | dict[str, Any] = "Internal server error"

    def __init__(self, detail: str | dict[str, Any] | None = None) -> None:
        super().__init__(
            status_code=self.STATUS_CODE,
            detail=detail if detail is not None else self.DETAIL,
        )


class UnprocessableEntity(_BaseHTTPException):
    """Request payload could not be processed (HTTP 422)."""

    STATUS_CODE = status.HTTP_422_UNPROCESSABLE_CONTENT
    DETAIL = "Unprocessable entity"


class HealingExhausted(UnprocessableEntity):
    """Payload stayed invalid after the maximum self-healing attempts."""

    def __init__(self, errors: list[Any] | None = None) -> None:
        super().__init__(
            detail={
                "message": "Payload could not be repaired after healing attempts",
                "errors": errors or [],
            }
        )


class NotFound(_BaseHTTPException):
    """Resource was not found (HTTP 404)."""

    STATUS_CODE = status.HTTP_404_NOT_FOUND
    DETAIL = "Not found"


class Conflict(_BaseHTTPException):
    """Request conflicts with current resource state (HTTP 409)."""

    STATUS_CODE = status.HTTP_409_CONFLICT
    DETAIL = "Conflict"
