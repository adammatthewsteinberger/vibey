# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
"""Diagnostics the application emits. Distinct from the event ledger, which is
durable domain history rather than something you can turn down with a flag."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class Logger(Protocol):
    """Structured application logging -- implemented by infrastructure/logging."""

    def bind(self, **kwargs: Any) -> Logger: ...
    def debug(self, event: str, **kwargs: Any) -> None: ...
    def info(self, event: str, **kwargs: Any) -> None: ...
    def warning(self, event: str, **kwargs: Any) -> None: ...
    def error(self, event: str, **kwargs: Any) -> None: ...
