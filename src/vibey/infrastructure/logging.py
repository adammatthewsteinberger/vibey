"""structlog configuration with separate transports.

Three sinks, so one operator's need does not crowd out another's:

1. **Human console** -- stderr, ``ConsoleRenderer``, for someone watching.
2. **JSON console** -- stderr, one object per line (``transport=console_json``),
   for whatever is capturing the process.
3. **Optional file** -- ``--log-file``, JSON lines, *in addition to* the
   console rather than instead of it.

Every payload passes through ``ledger.redact``, the same redactor the event
ledger uses: a secret must not be safe in one sink and leaked in another.

The per-project event ledger is a different thing entirely -- it is durable
domain history, not diagnostics. This module never writes to it.
"""

from __future__ import annotations

import logging
import sys
from collections.abc import Mapping, MutableMapping
from pathlib import Path
from typing import Any

import structlog
from structlog.stdlib import BoundLogger, LoggerFactory, ProcessorFormatter

from vibey.domain.verbosity import LogPlan
from vibey.infrastructure.ledger.redact import redact_payload

# Chatty libraries that are noise unless the operator explicitly widened the
# net with -vv. asyncpg in particular logs every statement at DEBUG.
_THIRD_PARTY_LOGGERS = ("asyncpg", "asyncio", "httpx", "httpcore", "urllib3", "textual")


def _redact_processor(
    _logger: object, _method_name: str, event_dict: MutableMapping[str, Any]
) -> Mapping[str, Any]:
    return redact_payload(dict(event_dict))


def _tagged_json(transport: str) -> Any:
    def render(logger: Any, method_name: str, event_dict: MutableMapping[str, Any]) -> str:
        payload = dict(event_dict)
        payload.setdefault("transport", transport)
        return str(structlog.processors.JSONRenderer()(logger, method_name, payload))

    return render


def configure_logging(
    plan: LogPlan,
    *,
    log_file: Path | None = None,
    human_console: bool = True,
) -> None:
    """Install the console handlers and, optionally, a file handler.

    ``human_console=False`` when the Textual dashboard owns the TTY -- a
    ConsoleRenderer writing to stderr underneath a full-screen app corrupts
    the display.
    """
    level_value = getattr(logging, plan.level, logging.INFO)

    shared: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        _redact_processor,
    ]

    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            *shared,
            ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=LoggerFactory(),
        wrapper_class=structlog.make_filtering_bound_logger(level_value),
        cache_logger_on_first_use=False,
    )

    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(level_value)

    if human_console:
        human = logging.StreamHandler(sys.stderr)
        human.setLevel(level_value)
        human.setFormatter(
            ProcessorFormatter(
                processor=structlog.dev.ConsoleRenderer(),
                foreign_pre_chain=shared,
            )
        )
        root.addHandler(human)

    json_console = logging.StreamHandler(sys.stderr)
    json_console.setLevel(level_value)
    json_console.setFormatter(
        ProcessorFormatter(
            processor=_tagged_json("console_json"),
            foreign_pre_chain=shared,
        )
    )
    root.addHandler(json_console)

    if log_file is not None:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(level_value)
        file_handler.setFormatter(
            ProcessorFormatter(
                processor=_tagged_json("file"),
                foreign_pre_chain=shared,
            )
        )
        root.addHandler(file_handler)

    # Third-party loggers stay quiet until -vv. Raising their floor rather
    # than removing their handlers keeps a genuine library error visible.
    third_party_level = (
        level_value if plan.include_third_party else max(level_value, logging.WARNING)
    )
    for name in _THIRD_PARTY_LOGGERS:
        logging.getLogger(name).setLevel(third_party_level)


def get_logger(**initial_context: Any) -> BoundLogger:
    logger: BoundLogger = structlog.get_logger(**initial_context)
    return logger


class StructlogAppLogger:
    """Adapter satisfying application.interfaces.Logger."""

    def __init__(self, bound: BoundLogger | None = None, **context: Any) -> None:
        self._log: BoundLogger = bound if bound is not None else get_logger(**context)

    def bind(self, **kwargs: Any) -> StructlogAppLogger:
        return StructlogAppLogger(self._log.bind(**kwargs))

    def debug(self, event: str, **kwargs: Any) -> None:
        self._log.debug(event, **kwargs)

    def info(self, event: str, **kwargs: Any) -> None:
        self._log.info(event, **kwargs)

    def warning(self, event: str, **kwargs: Any) -> None:
        self._log.warning(event, **kwargs)

    def error(self, event: str, **kwargs: Any) -> None:
        self._log.error(event, **kwargs)


class NullAppLogger:
    """The default, so nothing is obliged to configure logging to run."""

    def bind(self, **kwargs: Any) -> NullAppLogger:
        del kwargs
        return self

    def debug(self, event: str, **kwargs: Any) -> None:
        del event, kwargs

    def info(self, event: str, **kwargs: Any) -> None:
        del event, kwargs

    def warning(self, event: str, **kwargs: Any) -> None:
        del event, kwargs

    def error(self, event: str, **kwargs: Any) -> None:
        del event, kwargs
