# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Capture harness logging around a turn and fail closed on empty+404."""

from __future__ import annotations

import logging
from collections.abc import Iterator, Sequence
from contextlib import contextmanager

from agyloop.domain.classify import looks_like_withdrawn_model
from agyloop.domain.errors import AgentConfigError

_HARNESS_LOGGERS = ("", "google", "google.antigravity")


class _ListHandler(logging.Handler):
    def __init__(self, records: list[str]) -> None:
        super().__init__(level=logging.DEBUG)
        self._records = records

    def emit(self, record: logging.LogRecord) -> None:
        try:
            self._records.append(self.format(record))
        except Exception:  # pragma: no cover - logging must not break the turn
            self._records.append(record.getMessage())


@contextmanager
def capture_harness_logs() -> Iterator[list[str]]:
    """Temporarily attach a handler to Antigravity / root loggers."""
    records: list[str] = []
    handler = _ListHandler(records)
    handler.setFormatter(logging.Formatter("%(message)s"))
    loggers = [logging.getLogger(name) for name in _HARNESS_LOGGERS]
    for logger in loggers:
        logger.addHandler(handler)
    try:
        yield records
    finally:
        for logger in loggers:
            logger.removeHandler(handler)


def raise_if_empty_withdrawn(*, output_text: str, logs: Sequence[str]) -> None:
    """Empty success plus withdrawn-model markers in harness logs is terminal.

    Non-empty assistant text with leftover sidecar 404 noise is ignored.
    """
    if output_text.strip():
        return
    blob = "\n".join(logs)
    if not looks_like_withdrawn_model(blob):
        return
    raise AgentConfigError(
        "Harness input-detection called a withdrawn model (404 / NOT_FOUND). "
        "Empty turn is terminal; this is not Available. Set "
        "ANTIGRAVITY_HARNESS_PATH to a patched localharness, or see "
        "docs/getting-started/configuration.md."
    )
