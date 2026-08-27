from credit_engine.core.config import settings
from credit_engine.llm.gemini import GeminiHealer
from credit_engine.llm.openai_compatible import OpenAICompatibleHealer
from credit_engine.llm.protocol import Healer
from credit_engine.llm.stub import StubHealer


def get_healer() -> Healer:
    """Resolve the configured healer (stub, gemini, or OpenAI-compatible)."""
    backend = settings.BACKEND
    if backend == "stub":
        return StubHealer()
    if backend == "gemini":
        return GeminiHealer()
    if backend in {"openai_compatible", "llama"}:
        return OpenAICompatibleHealer()
    msg = (
        f"LLM backend '{backend}' is not supported; "
        "use LLM_BACKEND=stub, gemini, openai_compatible, or llama"
    )
    raise NotImplementedError(msg)
