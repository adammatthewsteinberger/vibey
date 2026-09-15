# Made with ❤️ by [Vibey](https://the-vibey-project.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Observability seams that converge across the runner family.

Only ``Logger`` and the ``publish``-only core of ``StateBus`` live here.
``ProgressReporter``, ``AuditLog``, and ``Notifier`` do NOT: codexloop
collapses them into differently named, differently shaped methods
(``report`` in place of ``turn_sent``/``waiting``/``finished``, ``append``
in place of ``record``, a ``title``+``body`` ``notify`` in place of a
single ``message``) -- a genuine redesign, not a naming or precision
difference, so they stay local to each runner. ``RunEventSink`` likewise
stays local: codexloop's has no ``bind`` at all, and cursorloop's ``bind``
takes a differently named keyword (``agent_id`` rather than ``session_id``)
that reflects its own domain vocabulary. codexloop's ``StateBus`` also adds
a ``subscribe`` method the other three runners' concrete adapters do not
implement; that stays as a local extension on codexloop's own ``StateBus``
(see codexloop's `application/interfaces/observability.py`), which
subclasses this module's ``StateBus`` rather than duplicating ``publish``.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Protocol, runtime_checkable


@runtime_checkable
class Logger(Protocol):
    """Structured event log. ``bind`` returns a child logger with extra context."""

    def bind(self, **kwargs: object) -> Logger: ...
    def debug(self, event: str, **kwargs: object) -> None: ...
    def info(self, event: str, **kwargs: object) -> None: ...
    def warning(self, event: str, **kwargs: object) -> None: ...
    def error(self, event: str, **kwargs: object) -> None: ...


@runtime_checkable
class StateBus(Protocol):
    """Publish run state changes for external pollers / subscribers."""

    def publish(self, event_type: str, payload: Mapping[str, object]) -> None: ...
