from credit_engine.core.config import settings
from credit_engine.llm.gemini import GeminiHealer
from credit_engine.llm.protocol import Healer
from credit_engine.llm.stub import StubHealer


def get_healer() -> Healer:
    """Resolve the configured healer (stub for tests; gemini for real healing)."""
    backend = settings.BACKEND
    if backend == "stub":
        return StubHealer()
    if backend == "gemini":
        return GeminiHealer()
    msg = (
        f"LLM backend '{backend}' is not supported; "
        "use LLM_BACKEND=stub or gemini"
    )
    raise NotImplementedError(msg)
