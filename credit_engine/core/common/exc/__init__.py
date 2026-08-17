"""Typed HTTP and domain exceptions."""

from credit_engine.core.common.exc.base import (
    HealingExhausted,
    UnprocessableEntity,
    _BaseHTTPException,
)

__all__ = [
    "HealingExhausted",
    "UnprocessableEntity",
    "_BaseHTTPException",
]
