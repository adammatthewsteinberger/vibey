# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Classify TurnSignals into a CapacityState (body first, status second)."""

from __future__ import annotations

from datetime import datetime, timedelta

from codexloop.domain.capacity import (
    AuthFailed,
    Available,
    CapacityState,
    PlanWindows,
    QuotaExhausted,
    ThrottleExhausted,
    TransientBackendError,
    WindowExhausted,
)
from codexloop.domain.error_codes import ErrorClass, classify_code
from codexloop.domain.signals import TurnSignals


def classify(signals: TurnSignals) -> CapacityState:
    """Map turn signals to a capacity state using the documented ladder.

    Completion claims, Retry-After headers, and high ``used_percent`` never
    outrank a body-level billing or auth marker. HTTP 429 is consulted only
    after ``error.code`` / ``error.type``.
    """
    code_cls = classify_code(signals.error_code, None)
    type_cls = classify_code(None, signals.error_type)
    status = signals.http_status

    if _has(ErrorClass.AUTH, code_cls, type_cls) or status == 401:
        return AuthFailed(reason=_reason(signals, ErrorClass.AUTH, "unauthorized"))

    if _has(ErrorClass.QUOTA, code_cls, type_cls):
        return QuotaExhausted(reason=_reason(signals, ErrorClass.QUOTA, "quota"))

    if _has(ErrorClass.WINDOW, code_cls, type_cls):
        resets_at, window = _window_from_plan(signals.plan_windows)
        return WindowExhausted(resets_at=resets_at, window=window)

    if _has(ErrorClass.THROTTLE, code_cls, type_cls):
        return ThrottleExhausted(
            retry_after=_retry_after(signals.retry_after_s),
            aggressive=_is_slow_down(signals),
        )

    if _has(ErrorClass.TRANSIENT, code_cls, type_cls):
        return TransientBackendError(retry_after=_retry_after(signals.retry_after_s))

    if _has(ErrorClass.FATAL, code_cls, type_cls):
        return Available(plan_windows=signals.plan_windows)

    if status is not None and 500 <= status <= 599:
        return TransientBackendError(retry_after=_retry_after(signals.retry_after_s))

    if status == 429:
        return WindowExhausted(resets_at=None, window="unknown")

    return Available(plan_windows=signals.plan_windows)


def _has(target: ErrorClass, code_cls: ErrorClass, type_cls: ErrorClass) -> bool:
    return target is code_cls or target is type_cls


def _reason(signals: TurnSignals, wanted: ErrorClass, fallback: str) -> str:
    if classify_code(signals.error_code, None) is wanted and signals.error_code is not None:
        return signals.error_code
    if classify_code(None, signals.error_type) is wanted and signals.error_type is not None:
        return signals.error_type
    if signals.error_code is not None:
        return signals.error_code
    if signals.error_type is not None:
        return signals.error_type
    return fallback


def _retry_after(seconds: float | None) -> timedelta | None:
    if seconds is None:
        return None
    return timedelta(seconds=seconds)


def _is_slow_down(signals: TurnSignals) -> bool:
    return signals.error_code == "slow_down" or signals.error_type == "slow_down"


def _window_from_plan(plan: PlanWindows | None) -> tuple[datetime | None, str]:
    if plan is None:
        return None, "unknown"
    primary = plan.primary
    if primary is not None and primary.resets_at is not None:
        return primary.resets_at, "five_hour"
    secondary = plan.secondary
    if secondary is not None and secondary.resets_at is not None:
        return secondary.resets_at, "weekly"
    return None, "unknown"
