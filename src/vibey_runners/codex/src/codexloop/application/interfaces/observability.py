# Made with ❤️ by [Vibey](https://the-vibey-project.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Observability seams specific to codexloop's own design.

``Logger`` moved to ``vibey_runners.common.application.interfaces.observability``
(it converges verbatim across the runner family). ``ProgressReporter``,
``AuditLog``, ``Notifier``, and ``RunEventSink`` stay here: this runner
collapses/reshapes each of them (a single ``report`` method rather than
``turn_sent``/``waiting``/``finished``; ``append`` rather than ``record``;
a ``title``+``body`` ``notify`` rather than a single ``message``; no
``bind`` on the event sink at all) -- a genuine redesign, not a naming or
typing difference.

``StateBus`` extends the shared base with ``subscribe``, which only this
runner's concrete adapter implements -- the other three runners' StateBus
adapters do not implement it, so it cannot live on the shared Protocol
itself without breaking their conformance.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Protocol, runtime_checkable

from vibey_runners.common.application.interfaces.observability import (
    StateBus as _SharedStateBus,
)


@runtime_checkable
class ProgressReporter(Protocol):
    def report(self, event: str, **detail: object) -> None: ...


@runtime_checkable
class AuditLog(Protocol):
    def append(self, event_type: str, payload: Mapping[str, object]) -> None: ...


@runtime_checkable
class Notifier(Protocol):
    def notify(self, title: str, body: str) -> None: ...


@runtime_checkable
class RunEventSink(Protocol):
    def emit(self, event: Mapping[str, object]) -> None: ...


@runtime_checkable
class StateBus(_SharedStateBus, Protocol):
    def subscribe(self, callback: Callable[[str, Mapping[str, object]], None]) -> None: ...
