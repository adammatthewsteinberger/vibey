"""Tenacity-backed retry wrappers with built-in counter bumps and logging.

The conventions baked in:

- Counters bumped at function ENTRY (``{namespace}.runs``) — not just on
  success. Apps want to know "how many times was this function called?", not
  "how many retry-eligible failures occurred?"
- Every retry attempt logs at WARNING via ``before_sleep_log`` — silent
  retry is a debugging nightmare.
- Default ``reraise=True`` — apps that want tenacity's RetryError wrapping
  opt in explicitly.
- Two presets covering the two dominant Azure use cases:
  - :func:`retry_azure_transient`: short bursts, 3 attempts, 2–10 s waits.
  - :func:`retry_ai_transient`: storm-class, 7 attempts, 2–120 s waits.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any, ParamSpec, TypeVar

from vibey_bootstrap.counters import bump_counter
from vibey_bootstrap.exceptions import NetworkError, RateLimitError

P = ParamSpec("P")
T = TypeVar("T")


def _is_rate_limit_or_http(exc: BaseException) -> bool:
    """True for RateLimitError or anything that looks like a 4xx/5xx HTTP error."""
    if isinstance(exc, RateLimitError):
        return True
    status = getattr(exc, "status_code", None) or getattr(exc, "status", None)
    if isinstance(status, int) and status >= 400:
        return True
    return False


def build_retry(
    *,
    operation: str,
    retry_on: (
        type[BaseException] | tuple[type[BaseException], ...] | Callable[[BaseException], bool]
    ),
    max_attempts: int = 5,
    wait_min_seconds: float = 1.0,
    wait_max_seconds: float = 60.0,
    counter_namespace: str | None = None,
    reraise: bool = True,
    rate_limit_callback: Callable[[BaseException], None] | None = None,
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """Build a tenacity ``@retry`` decorator with v2 conventions baked in."""
    try:
        from tenacity import (
            RetryError,
            Retrying,
            before_sleep_log,
            retry_if_exception,
            retry_if_exception_type,
            stop_after_attempt,
            wait_exponential,
        )
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            "build_retry requires the `retry` extra: pip install vibey-bootstrap[retry]"
        ) from exc

    logger = logging.getLogger(f"vibey_bootstrap.retry.{operation}")

    if callable(retry_on) and not (isinstance(retry_on, type) or isinstance(retry_on, tuple)):
        retry_predicate = retry_if_exception(retry_on)
    else:
        retry_predicate = retry_if_exception_type(retry_on)

    retrying = Retrying(
        retry=retry_predicate,
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=1, min=wait_min_seconds, max=wait_max_seconds),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=reraise,
    )

    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            if counter_namespace:
                bump_counter(f"{counter_namespace}.runs")
            try:
                for attempt in retrying:
                    with attempt:
                        try:
                            result = func(*args, **kwargs)
                        except BaseException as exc:
                            if rate_limit_callback and _is_rate_limit_or_http(exc):
                                try:
                                    rate_limit_callback(exc)
                                except Exception:
                                    pass
                            raise
                # retrying.__next__ exits when stop fires; result holds the last success
                if counter_namespace:
                    bump_counter(f"{counter_namespace}.calls.ok")
                return result  # type: ignore[return-value]
            except RetryError as exc:
                if counter_namespace:
                    label = (
                        "rate_limit_or_http_error"
                        if exc.last_attempt.exception() is not None
                        and _is_rate_limit_or_http(exc.last_attempt.exception())  # type: ignore[arg-type]
                        else "invalid_response"
                    )
                    bump_counter(f"{counter_namespace}.calls.{label}")
                raise
            except BaseException as exc:
                if counter_namespace:
                    label = (
                        "rate_limit_or_http_error"
                        if _is_rate_limit_or_http(exc)
                        else "unexpected_error"
                    )
                    bump_counter(f"{counter_namespace}.calls.{label}")
                raise

        wrapper.__wrapped__ = func  # type: ignore[attr-defined]
        wrapper.__name__ = getattr(func, "__name__", "wrapper")
        wrapper.__doc__ = getattr(func, "__doc__", None)
        return wrapper

    return decorator


def retry_azure_transient(
    *,
    operation: str,
    counter_namespace: str | None = None,
    max_attempts: int = 3,
    wait_min_seconds: float = 2.0,
    wait_max_seconds: float = 10.0,
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """Preset for Azure-SDK transient failures: NetworkError + RateLimitError."""
    return build_retry(
        operation=operation,
        retry_on=(NetworkError, RateLimitError),
        max_attempts=max_attempts,
        wait_min_seconds=wait_min_seconds,
        wait_max_seconds=wait_max_seconds,
        counter_namespace=counter_namespace,
    )


def retry_ai_transient(
    *,
    operation: str,
    counter_namespace: str | None = None,
    max_attempts: int = 7,
    wait_min_seconds: float = 2.0,
    wait_max_seconds: float = 120.0,
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """Preset for Azure OpenAI rate-limit storms — pair with ``AiUsageTracker.acquire``."""
    return build_retry(
        operation=operation,
        retry_on=RateLimitError,
        max_attempts=max_attempts,
        wait_min_seconds=wait_min_seconds,
        wait_max_seconds=wait_max_seconds,
        counter_namespace=counter_namespace,
    )


__all__ = ["build_retry", "retry_ai_transient", "retry_azure_transient"]
