# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""structlog configuration with separate transports.

Transports (always, for run/resume once configure_logging is called):

1. **Human console** — stderr, ``ConsoleRenderer``
2. **JSON console** — stderr, one JSON object per line (``transport=console_json``)
3. **Optional file** — ``--log-file`` JSON lines only (does not replace console)

Per-run ``events.jsonl`` / ``audit.jsonl`` and ``ConsoleProgressReporter`` are
separate sinks owned elsewhere. All structlog payloads pass through
``redact``. See ``docs/guides/logging-and-observability.md``.
"""

from __future__ import annotations

import logging
import sys
from collections.abc import MutableMapping
from pathlib import Path
from typing import Any

import structlog
from structlog.stdlib import BoundLogger, LoggerFactory, ProcessorFormatter

from claudeloop.domain.verbosity import LogPlan
from claudeloop.infrastructure.redact import redact


def _redact_processor(
    _logger: object, _method_name: str, event_dict: dict[str, Any]
) -> dict[str, Any]:
    return redact(event_dict)


def _tag_console_json(
    _logger: object, _method_name: str, event_dict: dict[str, Any]
) -> dict[str, Any]:
    event_dict.setdefault("transport", "console_json")
    return event_dict


def _tag_file(_logger: object, _method_name: str, event_dict: dict[str, Any]) -> dict[str, Any]:
    event_dict.setdefault("transport", "file")
    return event_dict


def _json_console_renderer(
    logger: Any, method_name: str, event_dict: MutableMapping[str, Any]
) -> str:
    tagged = _tag_console_json(logger, method_name, dict(event_dict))
    rendered = structlog.processors.JSONRenderer()(logger, method_name, tagged)
    return str(rendered)


def _json_file_renderer(logger: Any, method_name: str, event_dict: MutableMapping[str, Any]) -> str:
    tagged = _tag_file(logger, method_name, dict(event_dict))
    rendered = structlog.processors.JSONRenderer()(logger, method_name, tagged)
    return str(rendered)


def configure_logging(
    *,
    log_file: Path | None,
    level: str = "INFO",
    human_console: bool = True,
) -> None:
    """Install dual stderr handlers (human + JSON) and optional file handler.

    When ``human_console`` is False (e.g. Textual ``--stream-ui`` owns the TTY),
    only the JSON console handler is installed on stderr.
    """
    level_value = getattr(logging, level.upper(), logging.INFO)

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
            processor=_json_console_renderer,
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
                processor=_json_file_renderer,
                foreign_pre_chain=shared,
            )
        )
        root.addHandler(file_handler)


def get_logger(**initial_context: Any) -> BoundLogger:
    logger: BoundLogger = structlog.get_logger(**initial_context)
    return logger


class StructlogAppLogger:
    """Adapter satisfying application.ports.Logger."""

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


# Chatty libraries that are noise unless the operator explicitly widened the
# net with -vv.
_THIRD_PARTY_LOGGERS = ("anthropic", "claude_agent_sdk", "httpx", "httpcore", "asyncio", "textual")


def apply_third_party_level(plan: LogPlan) -> None:
    """Raise third-party loggers' floor unless -vv asked for them.

    Raising the floor rather than removing their handlers keeps a genuine
    library error visible at any verbosity.
    """
    level_value = getattr(logging, plan.level, logging.INFO)
    target = level_value if plan.include_third_party else max(level_value, logging.WARNING)
    for name in _THIRD_PARTY_LOGGERS:
        logging.getLogger(name).setLevel(target)
