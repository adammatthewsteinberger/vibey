"""Rich exception logger for except-blocks that swallow the exception."""

from __future__ import annotations

import logging
from typing import Any

from vibey_bootstrap.logging.masking import _safe_repr


def log_exception_context(
    logger: logging.Logger,
    exc: BaseException,
    operation: str,
    **context: Any,
) -> None:
    fields: dict[str, Any] = {
        "operation": operation,
        "exception_type": type(exc).__name__,
        "exception_message": str(exc)[:500],
    }
    for key, value in context.items():
        fields[key] = _safe_repr(value)
    logger.exception("Exception in %s: %s", operation, exc, extra=fields)
