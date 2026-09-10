# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""JSONL events + process result → TurnSignals."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import datetime
from typing import assert_never

from codexloop.domain.capacity import PlanWindows
from codexloop.domain.signals import TurnSignals
from codexloop.infrastructure.agent.events import (
    CodexEvent,
    ErrorEvent,
    ErrorPayload,
    ItemCompleted,
    ItemStarted,
    RateLimitsUpdated,
    ThreadStarted,
    TurnCompleted,
    TurnFailed,
    TurnStarted,
    UnknownEvent,
)


def to_turn_signals(
    events: Iterable[CodexEvent | None],
    *,
    exit_code: int,
    stderr_tail: str,
    now: datetime,
) -> TurnSignals:
    """Fold a parsed event stream plus process result into classification signals.

    ``exit_code`` and ``stderr_tail`` are always taken from the process result so a
    malformed or truncated JSONL stream still yields a classifiable outcome.
    """
    _ = now
    error_code: str | None = None
    error_type: str | None = None
    http_status: int | None = None
    retry_after_s: float | None = None
    plan_windows: PlanWindows | None = None
    completed = False
    failed = False
    final_message: str | None = None
    usage: object | None = None

    for event in events:
        if event is None:
            continue
        match event:
            case TurnCompleted(usage=turn_usage):
                completed = True
                usage = turn_usage
            case TurnFailed(error=error):
                failed = True
                error_code, error_type, http_status, retry_after_s = _merge_error(
                    error, error_code, error_type, http_status, retry_after_s
                )
            case ErrorEvent(error=error):
                error_code, error_type, http_status, retry_after_s = _merge_error(
                    error, error_code, error_type, http_status, retry_after_s
                )
            case RateLimitsUpdated(plan_windows=windows):
                if windows is not None:
                    plan_windows = windows
            case ItemCompleted(item=item):
                text = _agent_message_text(item)
                if text is not None:
                    final_message = text
            case ThreadStarted() | TurnStarted() | ItemStarted() | UnknownEvent():
                continue
            case _:  # pragma: no cover — exhaustive CodexEvent union
                assert_never(event)

    return TurnSignals(
        error_code=error_code,
        error_type=error_type,
        http_status=http_status,
        retry_after_s=retry_after_s,
        plan_windows=plan_windows,
        completed=completed,
        failed=failed,
        final_message=final_message,
        usage=usage,
        exit_code=exit_code,
        stderr_tail=stderr_tail,
    )


def _merge_error(
    error: ErrorPayload | None,
    error_code: str | None,
    error_type: str | None,
    http_status: int | None,
    retry_after_s: float | None,
) -> tuple[str | None, str | None, int | None, float | None]:
    if error is None:
        return error_code, error_type, http_status, retry_after_s
    extra = getattr(error, "retry_after_s", None)
    if isinstance(extra, int | float) and not isinstance(extra, bool):
        retry_after_s = float(extra)
    return (
        error.code if error.code is not None else error_code,
        error.type if error.type is not None else error_type,
        error.status if error.status is not None else http_status,
        retry_after_s,
    )


def _agent_message_text(item: Mapping[str, object] | None) -> str | None:
    if item is None:
        return None
    if item.get("type") != "agent_message":
        return None
    text = item.get("text")
    if isinstance(text, str):
        return text
    return None
