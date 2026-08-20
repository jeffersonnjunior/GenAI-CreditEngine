"""External HTTP clients (bureau, card gateway)."""

from credit_engine.clients.bureau.factory import get_bureau

__all__ = ["get_bureau"]
