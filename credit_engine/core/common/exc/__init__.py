"""Typed HTTP and domain exceptions."""

from credit_engine.core.common.exc.base import (
    Conflict,
    HealingExhausted,
    NotFound,
    UnprocessableEntity,
    _BaseHTTPException,
)

__all__ = [
    "Conflict",
    "HealingExhausted",
    "NotFound",
    "UnprocessableEntity",
    "_BaseHTTPException",
]
