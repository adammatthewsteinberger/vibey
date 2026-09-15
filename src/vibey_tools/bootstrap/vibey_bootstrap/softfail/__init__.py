"""Helpers for the "log + alert + continue with degraded result" pattern.

Apps wrap fragile code paths (AI summarization, optional enrichment, etc.)
in :func:`soft_fail_with` or the :func:`soft_fail` context manager so a
single sub-feature failure produces a degraded result rather than killing
the whole pipeline.

By default, both helpers re-raise exceptions that are unrecoverable per
:func:`vibey_bootstrap.exceptions.is_unrecoverable` — soft-failing an
``InvalidMessageError`` would break the dead-letter contract.
"""

from __future__ import annotations

import logging
from collections.abc import Callable, Generator
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Generic, TypeVar

from vibey_bootstrap.counters import bump_counter
from vibey_bootstrap.exceptions import is_unrecoverable

T = TypeVar("T")
_logger = logging.getLogger(__name__)


@dataclass
class SoftFailResult(Generic[T]):
    value: T
    degraded: bool
    reason: str | None = None
    exception: BaseException | None = None


def _fire_alert(severity: str, operation: str, exc: BaseException) -> None:
    try:
        from vibey_bootstrap.alerts import AlertSeverity, alert_dev_team

        alert_dev_team(
            AlertSeverity(severity),
            subject=f"{operation} soft-failed: {type(exc).__name__}",
            context={
                "operation": operation,
                "exception_type": type(exc).__name__,
                "error": str(exc)[:500],
            },
            dedup_key=f"{operation}:soft_fail:{type(exc).__name__}",
        )
    except Exception:
        pass


def soft_fail_with(
    fn: Callable[..., T],
    *args: Any,
    fallback: T,
    catch: type[BaseException] | tuple[type[BaseException], ...] = Exception,
    operation: str,
    alert_severity: str | None = "error",
    counter_name: str | None = None,
    fallback_fn: Callable[[BaseException], T] | None = None,
    re_raise_unrecoverable: bool = True,
    **kwargs: Any,
) -> SoftFailResult[T]:
    """Call ``fn(*args, **kwargs)``; soft-fail with ``fallback`` on caught error.

    Unrecoverable exceptions (per :func:`is_unrecoverable`) propagate by
    default — set ``re_raise_unrecoverable=False`` to explicitly suppress
    them too.
    """
    try:
        value = fn(*args, **kwargs)
    except catch as exc:
        if re_raise_unrecoverable and is_unrecoverable(exc):
            raise
        _logger.warning(
            "soft-fail in %s: %s",
            operation,
            type(exc).__name__,
            exc_info=True,
            extra={
                "operation": operation,
                "exception_type": type(exc).__name__,
                "error": str(exc)[:500],
            },
        )
        if counter_name:
            bump_counter(counter_name)
        if alert_severity:
            _fire_alert(alert_severity, operation, exc)
        resolved = fallback_fn(exc) if fallback_fn else fallback
        return SoftFailResult(
            value=resolved,
            degraded=True,
            reason=type(exc).__name__,
            exception=exc,
        )
    return SoftFailResult(value=value, degraded=False)


@contextmanager
def soft_fail(
    *,
    operation: str,
    catch: type[BaseException] | tuple[type[BaseException], ...] = Exception,
    alert_severity: str | None = "error",
    counter_name: str | None = None,
    re_raise_unrecoverable: bool = True,
) -> Generator[dict[str, Any], None, None]:
    """Context-manager form of :func:`soft_fail_with`.

    Yields a mutable dict the caller can inspect after the block::

        with soft_fail(operation='ai.summary', counter_name='ai.summary.failed') as ctx:
            summary = ai.summarize(text)
        if ctx['degraded']:
            summary = None  # caller handles the degraded case
    """
    state: dict[str, Any] = {"degraded": False, "reason": None, "exception": None}
    try:
        yield state
    except catch as exc:
        if re_raise_unrecoverable and is_unrecoverable(exc):
            raise
        state["degraded"] = True
        state["reason"] = type(exc).__name__
        state["exception"] = exc
        _logger.warning(
            "soft-fail in %s: %s",
            operation,
            type(exc).__name__,
            exc_info=True,
            extra={
                "operation": operation,
                "exception_type": type(exc).__name__,
                "error": str(exc)[:500],
            },
        )
        if counter_name:
            bump_counter(counter_name)
        if alert_severity:
            _fire_alert(alert_severity, operation, exc)


__all__ = ["SoftFailResult", "soft_fail", "soft_fail_with"]
