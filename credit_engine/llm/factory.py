from credit_engine.core.config import settings
from credit_engine.llm.protocol import Healer
from credit_engine.llm.stub import StubHealer


def get_healer() -> Healer:
    """Resolve the configured healer. Only stub is available for now."""
    backend = settings.BACKEND
    if backend == "stub":
        return StubHealer()
    msg = (
        f"LLM backend '{backend}' is pending; "
        "configure LLM_BACKEND=stub until a provider is chosen"
    )
    raise NotImplementedError(msg)
