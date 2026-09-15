"""``@traced`` decorator: auto-async, latency recording, slow alerts, error alerts.

Lazy-imports ``vibey_bootstrap.alerts`` so apps without the alerts extra still
get tracing + latency tracking (the ``alert_on_error=`` path silently falls
back to a log-only emit).
"""

from __future__ import annotations

import asyncio
import functools
import inspect
import logging
import time
import traceback
import uuid
from collections.abc import Callable
from typing import Any, TypeVar, cast

from vibey_bootstrap.logging.masking import _looks_sensitive, _safe_repr
from vibey_bootstrap.tracing.latency import _record_latency
from vibey_bootstrap.tracing.slow_thresholds import default_slow_threshold

F = TypeVar("F", bound=Callable[..., Any])


def _resolve_threshold(operation: str, override: float | None) -> float | None:
    if override is not None:
        return override
    return default_slow_threshold(operation)


def _mask_args_for_log(
    func: Callable[..., Any],
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
    sensitive: tuple[str, ...],
) -> dict[str, str]:
    try:
        sig = inspect.signature(func)
        bound = sig.bind_partial(*args, **kwargs)
        bound.apply_defaults()
        out: dict[str, str] = {}
        for name, value in bound.arguments.items():
            if name in ("self", "cls"):
                continue
            if name in sensitive or _looks_sensitive(name):
                out[name] = "***"
            else:
                out[name] = _safe_repr(value)
        return out
    except Exception:
        return {}


def _build_entry_extra(
    operation: str,
    trace_id: str,
    masked_args: dict[str, str] | None,
) -> dict[str, Any]:
    extra: dict[str, Any] = {"operation": operation, "trace_id": trace_id}
    if masked_args is not None:
        extra["call_args"] = masked_args
    return extra


def _maybe_alert_error(
    operation: str,
    exc: BaseException,
    alert_on_error: str | None,
    logger: logging.Logger,
) -> None:
    if alert_on_error is None:
        return
    try:
        from vibey_bootstrap.alerts import AlertSeverity, alert_dev_team
        from vibey_bootstrap.logging.correlation import _VARS

        context_vars: dict[str, Any] = {}
        for name, var in _VARS.items():
            context_vars[name] = var.get() or "(none)"

        alert_dev_team(
            AlertSeverity(alert_on_error),
            subject=f"{operation} failed: {type(exc).__name__}",
            context={
                "operation": operation,
                "exception_type": type(exc).__name__,
                "error": str(exc)[:500],
                "traceback": traceback.format_exc()[-2000:],
                **context_vars,
            },
            dedup_key=f"{operation}:{type(exc).__name__}",
        )
    except Exception:
        # Alert dispatch must never break the raising path.
        pass


def _slow_alert(operation: str, elapsed: float, threshold: float) -> None:
    try:
        from vibey_bootstrap.alerts import AlertSeverity, alert_dev_team

        alert_dev_team(
            AlertSeverity.WARN,
            subject=f"{operation} slow: {elapsed:.2f}s > {threshold}s budget",
            context={"operation": operation, "elapsed_seconds": elapsed, "threshold": threshold},
            dedup_key=f"slow:{operation}",
        )
    except Exception:
        pass


def traced(
    *,
    operation: str | None = None,
    alert_on_error: str | None = None,
    sensitive_args: tuple[str, ...] = (),
    log_result: bool = False,
    slow_threshold_seconds: float | None = None,
) -> Callable[[F], F]:
    """Trace sync or async functions.

    Records latency on every call (success + exception). Logs entry/exit at
    DEBUG only. When DEBUG is off, ``inspect.signature`` is skipped so the
    hot path stays cheap.
    """

    def decorator(func: F) -> F:
        op = operation or f"{func.__module__}.{func.__qualname__}"
        is_async = asyncio.iscoroutinefunction(func)
        logger = logging.getLogger(func.__module__)

        if is_async:

            @functools.wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                trace_id = uuid.uuid4().hex[:12]
                debug_on = logger.isEnabledFor(logging.DEBUG)
                masked_args: dict[str, str] | None = None
                if debug_on:
                    masked_args = _mask_args_for_log(func, args, kwargs, sensitive_args)
                    logger.debug("→ %s", op, extra=_build_entry_extra(op, trace_id, masked_args))
                start = time.monotonic()
                try:
                    result = await func(*args, **kwargs)
                except BaseException as exc:
                    elapsed = round(time.monotonic() - start, 3)
                    _record_latency(op, elapsed, error=True, slow=False)
                    logger.exception(
                        "✗ %s raised %s after %ss",
                        op,
                        type(exc).__name__,
                        elapsed,
                        extra={
                            "operation": op,
                            "trace_id": trace_id,
                            "elapsed_seconds": elapsed,
                            "exception_type": type(exc).__name__,
                        },
                    )
                    _maybe_alert_error(op, exc, alert_on_error, logger)
                    raise
                elapsed = round(time.monotonic() - start, 3)
                threshold = _resolve_threshold(op, slow_threshold_seconds)
                is_slow = threshold is not None and elapsed > threshold
                _record_latency(op, elapsed, error=False, slow=is_slow)
                if debug_on:
                    exit_extra: dict[str, Any] = {
                        "operation": op,
                        "trace_id": trace_id,
                        "elapsed_seconds": elapsed,
                    }
                    if log_result:
                        exit_extra["result"] = _safe_repr(result)
                    logger.debug("✓ %s ok in %.3fs", op, elapsed, extra=exit_extra)
                if is_slow and threshold is not None:
                    _slow_alert(op, elapsed, threshold)
                return result

            return cast(F, async_wrapper)

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            trace_id = uuid.uuid4().hex[:12]
            debug_on = logger.isEnabledFor(logging.DEBUG)
            masked_args: dict[str, str] | None = None
            if debug_on:
                masked_args = _mask_args_for_log(func, args, kwargs, sensitive_args)
                logger.debug("→ %s", op, extra=_build_entry_extra(op, trace_id, masked_args))
            start = time.monotonic()
            try:
                result = func(*args, **kwargs)
            except BaseException as exc:
                elapsed = round(time.monotonic() - start, 3)
                _record_latency(op, elapsed, error=True, slow=False)
                logger.exception(
                    "✗ %s raised %s after %ss",
                    op,
                    type(exc).__name__,
                    elapsed,
                    extra={
                        "operation": op,
                        "trace_id": trace_id,
                        "elapsed_seconds": elapsed,
                        "exception_type": type(exc).__name__,
                    },
                )
                _maybe_alert_error(op, exc, alert_on_error, logger)
                raise
            elapsed = round(time.monotonic() - start, 3)
            threshold = _resolve_threshold(op, slow_threshold_seconds)
            is_slow = threshold is not None and elapsed > threshold
            _record_latency(op, elapsed, error=False, slow=is_slow)
            if debug_on:
                exit_extra = {
                    "operation": op,
                    "trace_id": trace_id,
                    "elapsed_seconds": elapsed,
                }
                if log_result:
                    exit_extra["result"] = _safe_repr(result)
                logger.debug("✓ %s ok in %.3fs", op, elapsed, extra=exit_extra)
            if is_slow and threshold is not None:
                _slow_alert(op, elapsed, threshold)
            return result

        return cast(F, sync_wrapper)

    return decorator


def traced_async(**kwargs: Any) -> Callable[[F], F]:
    """Alias for ``@traced``. The decorator auto-detects async."""
    return traced(**kwargs)
