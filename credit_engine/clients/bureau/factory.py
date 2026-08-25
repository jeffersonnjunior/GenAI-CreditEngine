from credit_engine.clients.bureau.http import HttpBureauClient
from credit_engine.clients.bureau.protocol import BureauClient
from credit_engine.clients.bureau.stub import StubBureauClient, UnavailableBureauClient
from credit_engine.core.config import settings


def get_bureau() -> BureauClient:
    """Resolve the configured bureau client."""
    client = settings.CLIENT
    if client == "stub":
        return StubBureauClient()
    if client == "unavailable":
        return UnavailableBureauClient()
    if client == "http":
        return HttpBureauClient()
    msg = (
        f"Unknown bureau client '{client}'; "
        "use BUREAU_CLIENT=stub, unavailable, or http"
    )
    raise NotImplementedError(msg)
