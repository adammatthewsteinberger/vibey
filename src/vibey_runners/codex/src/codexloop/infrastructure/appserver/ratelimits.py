# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Map app-server ``account/rateLimits/read`` results onto ``PlanWindows``.

Field names match the exec JSONL rate-limit blob already parsed in
``infrastructure.agent.events`` (``primary`` / ``secondary`` / ``plan_type`` /
``rate_limit_reached_type``, ``used_percent`` / ``window_minutes`` /
``resets_at`` / ``resets_in_seconds``). Helpers are duplicated here so this
package does not depend on agent internals.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime, timedelta
from typing import Any

from codexloop.domain.capacity import PlanWindows, RateLimitWindow


def plan_windows_from_rpc(result: object, *, now: datetime) -> PlanWindows | None:
    """Return ``PlanWindows`` from an RPC ``result`` payload, or ``None``."""
    if not isinstance(result, Mapping):
        return None
    blob = _rate_limits_blob(result)
    if blob is None or not isinstance(blob, Mapping):
        return None
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
    if any(key in obj for key in ("primary", "secondary", "plan_type", "rate_limit_reached_type")):
        return obj
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
    except (TypeError, ValueError, OverflowError, OSError):  # pragma: no cover
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
        except (OverflowError, ValueError):  # pragma: no cover
            return None
    return None


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
