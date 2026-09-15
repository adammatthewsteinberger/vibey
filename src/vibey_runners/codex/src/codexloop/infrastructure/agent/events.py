# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Forgiving parser for ``codex exec --json`` JSONL events (R3, R4)."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from codexloop.domain.capacity import PlanWindows, RateLimitWindow

_ERROR_PATHS: tuple[tuple[str, ...], ...] = (
    ("error",),
    ("payload", "error"),
    ("item", "error"),
    ("turn", "error"),
)


@dataclass(frozen=True, slots=True)
class Usage:
    input_tokens: int | None = None
    cached_input_tokens: int | None = None
    output_tokens: int | None = None
    reasoning_output_tokens: int | None = None


@dataclass(frozen=True, slots=True)
class ErrorPayload:
    code: str | None
    type: str | None
    message: str | None
    status: int | None


@dataclass(frozen=True, slots=True)
class ThreadStarted:
    thread_id: str | None


@dataclass(frozen=True, slots=True)
class TurnStarted:
    pass


@dataclass(frozen=True, slots=True)
class TurnCompleted:
    usage: Usage | None


@dataclass(frozen=True, slots=True)
class TurnFailed:
    error: ErrorPayload | None


@dataclass(frozen=True, slots=True)
class ItemStarted:
    item: Mapping[str, object] | None


@dataclass(frozen=True, slots=True)
class ItemCompleted:
    item: Mapping[str, object] | None


@dataclass(frozen=True, slots=True)
class RateLimitsUpdated:
    plan_windows: PlanWindows | None


@dataclass(frozen=True, slots=True)
class ErrorEvent:
    error: ErrorPayload | None


@dataclass(frozen=True, slots=True)
class UnknownEvent:
    type: str


CodexEvent = (
    ThreadStarted
    | TurnStarted
    | TurnCompleted
    | TurnFailed
    | ItemStarted
    | ItemCompleted
    | RateLimitsUpdated
    | ErrorEvent
    | UnknownEvent
)


class JsonlParser:
    """Parse one JSONL line at a time. Unknown and malformed input never raises."""

    def __init__(self, *, now: datetime | None = None) -> None:
        self._now = now
        self.malformed_count = 0

    def parse_line(self, line: str) -> CodexEvent | None:
        stripped = line.strip()
        if not stripped:
            return None
        try:
            decoded: object = json.loads(stripped)
        except json.JSONDecodeError:
            self.malformed_count += 1
            return None
        if not isinstance(decoded, dict):
            self.malformed_count += 1
            return None
        return self._parse_obj(decoded)

    def _parse_obj(self, obj: dict[str, Any]) -> CodexEvent | None:
        event_type = obj.get("type")
        if not isinstance(event_type, str) or not event_type:
            return None
        match event_type:
            case "thread.started":
                return ThreadStarted(thread_id=_opt_str(obj.get("thread_id")))
            case "turn.started":
                return TurnStarted()
            case "turn.completed":
                return TurnCompleted(usage=_usage(obj.get("usage")))
            case "turn.failed":
                return TurnFailed(error=_extract_error(obj))
            case "item.started":
                return ItemStarted(item=_item(obj.get("item")))
            case "item.completed":
                return ItemCompleted(item=_item(obj.get("item")))
            case "rate_limits.updated":
                return RateLimitsUpdated(plan_windows=self._plan_windows(obj))
            case "event_msg":
                payload = obj.get("payload")
                if isinstance(payload, Mapping) and payload.get("type") == "token_count":
                    return RateLimitsUpdated(plan_windows=self._plan_windows(obj))
                return UnknownEvent(type=event_type)
            case "error":
                return ErrorEvent(error=_extract_error(obj))
            case _:
                return UnknownEvent(type=event_type)

    def _plan_windows(self, obj: Mapping[str, Any]) -> PlanWindows | None:
        blob = _rate_limits_blob(obj)
        if blob is None:
            return None
        if not isinstance(blob, Mapping):
            return None
        now = self._now if self._now is not None else datetime.now(UTC)
        return PlanWindows(
            primary=_window(blob.get("primary"), now=now),
            secondary=_window(blob.get("secondary"), now=now),
            plan_type=_opt_str(blob.get("plan_type")),
            limit_reached=_opt_str(blob.get("rate_limit_reached_type")),
        )


def _rate_limits_blob(obj: Mapping[str, Any]) -> object:
    if "rate_limits" in obj:
        return obj["rate_limits"]
    payload = obj.get("payload")
    if isinstance(payload, Mapping) and "rate_limits" in payload:
        return payload["rate_limits"]
    return None


def _window(value: object, *, now: datetime) -> RateLimitWindow | None:
    if not isinstance(value, Mapping):
        return None
    try:
        minutes = _opt_int(value.get("window_minutes"))
        if minutes is None:
            return None
        return RateLimitWindow(
            used_percent=_opt_float(value.get("used_percent")),
            window_minutes=minutes,
            resets_at=_resets_at(value, now=now),
        )
    except (TypeError, ValueError, OverflowError, OSError):
        return None


def _resets_at(window: Mapping[str, Any], *, now: datetime) -> datetime | None:
    raw_at = window.get("resets_at")
    if isinstance(raw_at, bool):
        raw_at = None
    if isinstance(raw_at, int | float):
        try:
            return datetime.fromtimestamp(float(raw_at), tz=UTC)
        except (OSError, OverflowError, ValueError):
            return None
    raw_in = window.get("resets_in_seconds")
    if isinstance(raw_in, bool):
        raw_in = None
    if isinstance(raw_in, int | float):
        try:
            return now + timedelta(seconds=float(raw_in))
        except (OverflowError, ValueError):
            return None
    return None


def _usage(value: object) -> Usage | None:
    if not isinstance(value, Mapping):
        return None
    return Usage(
        input_tokens=_opt_int(value.get("input_tokens")),
        cached_input_tokens=_opt_int(value.get("cached_input_tokens")),
        output_tokens=_opt_int(value.get("output_tokens")),
        reasoning_output_tokens=_opt_int(value.get("reasoning_output_tokens")),
    )


def _item(value: object) -> dict[str, object] | None:
    if not isinstance(value, Mapping):
        return None
    return dict(value)


def _extract_error(obj: Mapping[str, Any]) -> ErrorPayload | None:
    for path in _ERROR_PATHS:
        found = _dig(obj, path)
        if found is None:
            continue
        payload = _error_payload(found)
        if payload is not None:
            return payload
    return None


def _dig(obj: Mapping[str, Any], path: tuple[str, ...]) -> object | None:
    current: object = obj
    for key in path:
        if not isinstance(current, Mapping) or key not in current:
            return None
        current = current[key]
    return current


def _error_payload(value: object) -> ErrorPayload | None:
    if isinstance(value, str):
        return ErrorPayload(code=None, type=None, message=value, status=None)
    if not isinstance(value, Mapping):
        return None
    return ErrorPayload(
        code=_opt_str(value.get("code")),
        type=_opt_str(value.get("type")),
        message=_opt_str(value.get("message")),
        status=_opt_int(value.get("status")),
    )


def _opt_str(value: object) -> str | None:
    if isinstance(value, str):
        return value
    return None


def _opt_int(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return None


def _opt_float(value: object) -> float | None:
    if isinstance(value, bool) or not isinstance(value, int | float):
        return None
    return float(value)
