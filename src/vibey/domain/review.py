from dataclasses import dataclass
from enum import StrEnum


class Severity(StrEnum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Ambiguity(StrEnum):
    CLEAR = "clear"
    NEEDS_CLARIFICATION = "needs_clarification"


class UserVerdict(StrEnum):
    ACCEPT = "accept"
    CHANGES = "changes"
    CANCEL = "cancel"


@dataclass(frozen=True, slots=True)
class FindingRef:
    """A pointer to a FindingRaised ledger event, carrying just enough to
    route the review loop-back decision without re-reading the ledger."""

    finding_id: str
    severity: Severity
    ambiguity: Ambiguity
