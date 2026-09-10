# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Everything the run emits outward: logs, audit records, progress, events,
state publications, usage reads, and operator notifications."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Protocol, runtime_checkable


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
class Logger(Protocol):
    def bind(self, **kwargs: object) -> Logger: ...
    def debug(self, event: str, **kwargs: object) -> None: ...
    def info(self, event: str, **kwargs: object) -> None: ...
    def warning(self, event: str, **kwargs: object) -> None: ...
    def error(self, event: str, **kwargs: object) -> None: ...


@runtime_checkable
class RunEventSink(Protocol):
    def emit(self, event: Mapping[str, object]) -> None: ...


@runtime_checkable
class StateBus(Protocol):
    def publish(self, event_type: str, payload: Mapping[str, object]) -> None: ...
    def subscribe(self, callback: Callable[[str, Mapping[str, object]], None]) -> None: ...
