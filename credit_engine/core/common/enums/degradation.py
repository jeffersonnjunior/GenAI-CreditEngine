from enum import StrEnum


class DegradationMode(StrEnum):
    """Structural degradation applied when an external dependency is unavailable."""

    NONE = "none"
    BUREAU_UNAVAILABLE = "bureau_unavailable"
