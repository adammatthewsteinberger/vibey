# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Everything the run emits outward: logs, audit records, progress, events,
state publications, usage reads, and operator notifications."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class UsageReader(Protocol):
    """Per-turn tokens and billed dollars. ``billed_cost_usd`` is None when unknown."""

    async def turn_tokens(self, run_id: str) -> int: ...
    async def billed_cost_usd(self) -> float | None: ...


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
class Logger(Protocol):
    """Structured event log. bind() returns a child logger with extra context."""

    def bind(self, **kwargs: Any) -> Logger: ...
    def debug(self, event: str, **kwargs: Any) -> None: ...
    def info(self, event: str, **kwargs: Any) -> None: ...
    def warning(self, event: str, **kwargs: Any) -> None: ...
    def error(self, event: str, **kwargs: Any) -> None: ...


@runtime_checkable
class RunEventSink(Protocol):
    """Structured run events for watchers. bind() sets the ambient context."""

    def emit(self, event_type: str, payload: dict[str, Any] | None = None) -> None: ...
    def bind(
        self,
        *,
        agent_id: str | None = None,
        attempt: int | None = None,
        phase: str | None = None,
        trace_id: str | None = None,
        turn_id: str | None = None,
    ) -> None: ...


@runtime_checkable
class StateBus(Protocol):
    """Publish run state changes for external pollers / subscribers."""

    def publish(self, event_type: str, state: dict[str, Any]) -> None: ...
