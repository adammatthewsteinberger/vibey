# Made with ❤️ by [Vibey](https://the-vibey-project.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Observability seams specific to claudeloop's own design.

``Logger`` and ``StateBus`` moved to
``vibey_runners.common.application.interfaces.observability`` (they
converge verbatim across the runner family). ``ProgressReporter``,
``AuditLog``, ``Notifier``, and ``RunEventSink`` stay here: one of the
four runners in this family collapses/reshapes each of them (a single
``report`` method rather than ``turn_sent``/``waiting``/``finished``,
``append`` rather than ``record``, a ``title``+``body`` ``notify`` rather
than a single ``message``, no ``bind`` on the event sink at all) -- a
genuine redesign, not a naming or typing difference, so these four were
not pulled into the shared package.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class ProgressReporter(Protocol):
    """Operator-visible progress: a turn was sent, a wait began, or the run ended."""

    def turn_sent(self, *, attempt: int) -> None: ...
    def waiting(self, *, reason: str, until: datetime) -> None: ...
    def finished(self, *, success: bool, reason: str) -> None: ...


@runtime_checkable
class AuditLog(Protocol):
    """Append-only structured events for a single run."""

    def record(self, event_type: str, payload: dict[str, Any]) -> None: ...


@runtime_checkable
class Notifier(Protocol):
    """Fire-and-forget operator alert. Used when a human must act (credits)."""

    def notify(self, message: str) -> None: ...


@runtime_checkable
class RunEventSink(Protocol):
    """Structured run events for watchers. bind() sets the ambient context."""

    def emit(self, event_type: str, payload: dict[str, Any] | None = None) -> None: ...
    def bind(
        self,
        *,
        session_id: str | None = None,
        attempt: int | None = None,
        phase: str | None = None,
        trace_id: str | None = None,
        turn_id: str | None = None,
    ) -> None: ...
