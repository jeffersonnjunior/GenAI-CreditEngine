"""Document vision / CNH cross-check for antifraude."""

from credit_engine.vision.models import CnhExtract, VisionCheckResult
from credit_engine.vision.verify import apply_vision_to_decision, verify_cnh

__all__ = [
    "CnhExtract",
    "VisionCheckResult",
    "apply_vision_to_decision",
    "verify_cnh",
]
