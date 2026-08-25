from enum import StrEnum


class ProposalStatus(StrEnum):
    """Lifecycle status of a credit proposal."""

    APPROVED = "approved"
    DENIED = "denied"
    PENDING_REVIEW = "pending_review"

    def can_emit_card(self) -> bool:
        """Whether the proposal is eligible for autonomous card issuance."""
        return self is ProposalStatus.APPROVED
