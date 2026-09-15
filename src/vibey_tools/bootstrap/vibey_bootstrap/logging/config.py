# Made with ❤️ by [Vibey](https://the-vibey-project.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Single entry-point for v2 logging setup.

``configure_logging()`` is idempotent and safe to re-run (the config_refresh
job calls it whenever ``LOG_LEVEL`` changes at runtime).
"""

from __future__ import annotations

import logging
import os

from vibey_bootstrap.logging.correlation import CorrelationFilter
from vibey_bootstrap.logging.formatter import (
    _STDLIB_LOG_RECORD_KEYS,
    ExtraFieldsFormatter,
    LoggingExtraConflictError,
)
from vibey_bootstrap.logging.noise import silence_noisy_loggers

_TRUTHY = {"1", "true", "yes", "on"}


def env_flag(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in _TRUTHY


def debug_logging_enabled() -> bool:
    """Second-factor gate on DEBUG output.

    ``LOG_LEVEL=DEBUG`` alone is not enough — ``DEBUG_LOGGING_ENABLED`` must
    also be truthy. Belt-and-suspenders against a stray manifest leaking
    DEBUG into prod.
    """
    return env_flag("DEBUG_LOGGING_ENABLED", default=False)


def effective_log_level() -> int:
    raw = os.environ.get("LOG_LEVEL", "INFO").strip().upper()
    level = getattr(logging, raw, None)
    if not isinstance(level, int):
        level = logging.INFO
    if level == logging.DEBUG and not debug_logging_enabled():
        level = logging.INFO
    return level


class _StrictLogger(logging.Logger):
    """Logger subclass that raises ``LoggingExtraConflictError`` in DEBUG.

    Wraps ``makeRecord`` so the standard ``KeyError`` from stdlib's collision
    check becomes our typed exception — easier to grep for in CI and easier
    to assert in tests.
    """

    def makeRecord(  # type: ignore[override]
        self,
        name: str,
        level: int,
        fn: str,
        lno: int,
        msg: object,
        args: object,
        exc_info: object,
        func: str | None = None,
        extra: dict[str, object] | None = None,
        sinfo: str | None = None,
    ) -> logging.LogRecord:
        if extra and debug_logging_enabled():
            for key in extra:
                if key in _STDLIB_LOG_RECORD_KEYS:
                    raise LoggingExtraConflictError(
                        f"extra[{key!r}] collides with a reserved LogRecord attribute"
                    )
        return super().makeRecord(
            name,
            level,
            fn,
            lno,
            msg,
            args,  # type: ignore[arg-type]
            exc_info,  # type: ignore[arg-type]
            func,
            extra,
            sinfo,
        )


def configure_logging(
    *,
    format_string: str = "%(asctime)s %(levelname)s %(name)s %(message)s",
    silence_defaults: bool = True,
    extra_noisy_loggers: tuple[str, ...] = (),
) -> None:
    """Install structured-logging defaults. Idempotent — replaces handlers."""
    logging.setLoggerClass(_StrictLogger)

    level = effective_log_level()
    handler = logging.StreamHandler()
    handler.setFormatter(ExtraFieldsFormatter(format_string))
    handler.addFilter(CorrelationFilter())

    logging.basicConfig(level=level, handlers=[handler], force=True)

    root = logging.getLogger()
    if not any(isinstance(f, CorrelationFilter) for f in root.filters):
        root.addFilter(CorrelationFilter())

    silence_noisy_loggers(*extra_noisy_loggers, include_defaults=silence_defaults)
