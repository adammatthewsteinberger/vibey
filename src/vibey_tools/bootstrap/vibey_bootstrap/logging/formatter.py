"""v2 log formatter: appends extra={} fields as `key=repr(value)` pairs.

Distinct from the v1 ``ExtraFieldsFormatter`` at
``vibey_bootstrap.services.bootstrap_logging``, which uses a JSON-with-pipe
layout for backwards compatibility.  ``configure_logging()`` installs the v2
formatter; the v1 import path is preserved unchanged.
"""

from __future__ import annotations

import logging
import os

_STDLIB_LOG_RECORD_KEYS: frozenset[str] = frozenset(
    {
        "name",
        "msg",
        "args",
        "levelname",
        "levelno",
        "pathname",
        "filename",
        "module",
        "exc_info",
        "exc_text",
        "stack_info",
        "lineno",
        "funcName",
        "created",
        "msecs",
        "relativeCreated",
        "thread",
        "threadName",
        "processName",
        "process",
        "message",
        "asctime",
        "taskName",
    }
)


class LoggingExtraConflictError(Exception):
    """Raised in DEBUG when a caller's ``extra={}`` collides with a reserved key."""


def _debug_strict_check_enabled() -> bool:
    raw = os.environ.get("DEBUG_LOGGING_ENABLED", "")
    return raw.strip().lower() in {"1", "true", "yes", "on"}


class ExtraFieldsFormatter(logging.Formatter):
    """Render structured extras after the base format string.

    Output: ``<base>  key1='value1' key2=42 key3=<MyObj>``.  Two-space gap is
    intentional so ``grep ' key='`` finds field hits without matching the
    message body.
    """

    def __init__(
        self,
        fmt: str | None = "%(asctime)s %(levelname)s %(name)s %(message)s",
        datefmt: str | None = None,
        style: str = "%",
        validate: bool = True,
    ) -> None:
        super().__init__(fmt=fmt, datefmt=datefmt, style=style, validate=validate)  # type: ignore[arg-type]

    def format(self, record: logging.LogRecord) -> str:
        base = super().format(record)
        extras: list[str] = []
        for key, value in record.__dict__.items():
            if key in _STDLIB_LOG_RECORD_KEYS or key.startswith("_"):
                continue
            extras.append(f"{key}={value!r}")
        if not extras:
            return base
        return f"{base}  " + " ".join(extras)
