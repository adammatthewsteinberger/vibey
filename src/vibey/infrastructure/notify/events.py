# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://hire.adam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
"""Typed notification events for human gates, phase changes, and budget thresholds."""

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID


class NotificationKind(StrEnum):
    HUMAN_GATE_RAISED = "human_gate_raised"
    PHASE_TRANSITIONED = "phase_transitioned"
    BUDGET_EXCEEDED = "budget_exceeded"
    RUN_COMPLETED = "run_completed"


@dataclass(slots=True, frozen=True)
class NotificationEvent:
    kind: NotificationKind
    project_id: UUID
    title: str
    message: str
    payload: Mapping[str, object] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self) -> dict[str, object]:
        return {
            "kind": self.kind.value,
            "project_id": str(self.project_id),
            "title": self.title,
            "message": self.message,
            "payload": dict(self.payload),
            "timestamp": self.timestamp.isoformat(),
        }
