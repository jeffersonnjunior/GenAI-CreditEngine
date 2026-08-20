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
    msg = (
        f"Bureau client '{client}' is pending; "
        "use BUREAU_CLIENT=stub or unavailable"
    )
    raise NotImplementedError(msg)
