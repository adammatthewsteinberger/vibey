# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""structlog configuration: human console, optional JSON console, optional file."""

from __future__ import annotations

import logging
import sys
from collections.abc import MutableMapping
from pathlib import Path
from typing import Any

import structlog
from structlog.stdlib import BoundLogger, LoggerFactory, ProcessorFormatter

from codexloop.application.ports import Logger
from codexloop.domain.verbosity import LogPlan
from codexloop.infrastructure.redact import redact


class RedactionProcessor:
    """structlog processor that recursively redacts secrets in the event dict."""

    def __call__(
        self,
        _logger: object,
        _method_name: str,
        event_dict: MutableMapping[str, Any],
    ) -> MutableMapping[str, Any]:
        redacted = redact(dict(event_dict))
        if not isinstance(redacted, dict):
            return event_dict
        return redacted


def _json_renderer(logger: object, method_name: str, event_dict: MutableMapping[str, Any]) -> str:
    rendered = structlog.processors.JSONRenderer()(logger, method_name, event_dict)
    return str(rendered)


def configure_logging(
    *,
    level: str = "INFO",
    json_logs: bool = False,
    log_file: Path | None = None,
) -> None:
    """Install a human console handler, optional JSON console, and optional file."""
    level_value = getattr(logging, level.upper(), logging.INFO)
    shared: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        RedactionProcessor(),
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

    human = logging.StreamHandler(sys.stderr)
    human.setLevel(level_value)
    human.setFormatter(
        ProcessorFormatter(
            processor=structlog.dev.ConsoleRenderer(),
            foreign_pre_chain=shared,
        )
    )
    root.addHandler(human)

    if json_logs:
        json_console = logging.StreamHandler(sys.stderr)
        json_console.setLevel(level_value)
        json_console.setFormatter(
            ProcessorFormatter(
                processor=_json_renderer,
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
                processor=_json_renderer,
                foreign_pre_chain=shared,
            )
        )
        root.addHandler(file_handler)


def get_logger(**initial_context: Any) -> BoundLogger:
    logger: BoundLogger = structlog.get_logger(**initial_context)
    return logger


class StructlogAppLogger:
    """Adapter satisfying :class:`codexloop.application.ports.Logger`."""

    def __init__(self, bound: BoundLogger | None = None, **context: Any) -> None:
        self._log: BoundLogger = bound if bound is not None else get_logger(**context)

    def bind(self, **kwargs: object) -> Logger:
        return StructlogAppLogger(self._log.bind(**kwargs))

    def debug(self, event: str, **kwargs: object) -> None:
        self._log.debug(event, **kwargs)

    def info(self, event: str, **kwargs: object) -> None:
        self._log.info(event, **kwargs)

    def warning(self, event: str, **kwargs: object) -> None:
        self._log.warning(event, **kwargs)

    def error(self, event: str, **kwargs: object) -> None:
        self._log.error(event, **kwargs)


# Chatty libraries that are noise unless the operator explicitly widened the
# net with -vv.
_THIRD_PARTY_LOGGERS = ("openai", "httpx", "httpcore", "anyio", "asyncio", "textual")


def apply_third_party_level(plan: LogPlan) -> None:
    """Raise third-party loggers' floor unless -vv asked for them.

    Raising the floor rather than removing their handlers keeps a genuine
    library error visible at any verbosity.
    """
    level_value = getattr(logging, plan.level, logging.INFO)
    target = level_value if plan.include_third_party else max(level_value, logging.WARNING)
    for name in _THIRD_PARTY_LOGGERS:
        logging.getLogger(name).setLevel(target)
