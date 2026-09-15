"""Silence chatty third-party loggers.

The defaults are aggressively chosen for Azure-heavy applications. Apps can
add more via ``register_noisy_logger(name)``.
"""

from __future__ import annotations

import logging

_DEFAULT_NOISY_LOGGERS: list[str] = [
    "pdfminer",
    "pdfplumber",
    "azure.core.pipeline.policies.http_logging_policy",
    "azure.identity",
    "azure.servicebus",
    "azure.storage",
    "urllib3",
    "urllib3.connectionpool",
    "httpx",
    "httpcore",
    "asyncio",
    "msal",
    "apscheduler.scheduler",
]


def register_noisy_logger(name: str) -> None:
    """Append a logger name to the default registry for the lifetime of the process."""
    if name and name not in _DEFAULT_NOISY_LOGGERS:
        _DEFAULT_NOISY_LOGGERS.append(name)


def silence_noisy_loggers(
    *names: str,
    level: int = logging.WARNING,
    include_defaults: bool = True,
) -> None:
    """Clamp the named loggers to ``level``.

    Only the named loggers are affected — root is never touched, so callers
    can leave root at DEBUG while these stay quiet.
    """
    targets: list[str] = []
    if include_defaults:
        targets.extend(_DEFAULT_NOISY_LOGGERS)
    targets.extend(names)
    seen: set[str] = set()
    for name in targets:
        if not name or name in seen:
            continue
        seen.add(name)
        logging.getLogger(name).setLevel(level)
