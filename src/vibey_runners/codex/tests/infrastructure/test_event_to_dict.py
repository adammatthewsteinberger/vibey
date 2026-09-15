# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""_event_to_dict conversion — every CodexEvent variant → dict payload."""

from __future__ import annotations

from datetime import UTC, datetime

from codexloop.domain.capacity import PlanWindows, RateLimitWindow
from codexloop.infrastructure.agent.events import (
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
    Usage,
)
from codexloop.infrastructure.agent.gateway import _event_to_dict


def test_thread_started_with_id() -> None:
    event = ThreadStarted(thread_id="abc-123")
    result = _event_to_dict(event)
    assert result is not None
    assert result["type"] == "thread.started"
    assert result["thread_id"] == "abc-123"


def test_thread_started_without_id() -> None:
    event = ThreadStarted(thread_id=None)
    result = _event_to_dict(event)
    assert result is not None
    assert result["type"] == "thread.started"
    assert "thread_id" not in result


def test_turn_started() -> None:
    event = TurnStarted()
    result = _event_to_dict(event)
    assert result == {"type": "turn.started"}


def test_turn_completed_with_full_usage() -> None:
    usage = Usage(
        input_tokens=100,
        cached_input_tokens=50,
        output_tokens=25,
        reasoning_output_tokens=10,
    )
    event = TurnCompleted(usage=usage)
    result = _event_to_dict(event)
    assert result is not None
    assert result["type"] == "turn.completed"
    assert result["usage"] == {
        "input_tokens": 100,
        "cached_input_tokens": 50,
        "output_tokens": 25,
        "reasoning_output_tokens": 10,
    }


def test_turn_completed_with_partial_usage() -> None:
    usage = Usage(input_tokens=100, output_tokens=25)
    event = TurnCompleted(usage=usage)
    result = _event_to_dict(event)
    assert result is not None
    assert result["usage"] == {
        "input_tokens": 100,
        "output_tokens": 25,
    }


def test_turn_completed_without_usage() -> None:
    event = TurnCompleted(usage=None)
    result = _event_to_dict(event)
    assert result == {"type": "turn.completed"}


def test_turn_completed_with_inverse_partial_usage() -> None:
    """Complements test_turn_completed_with_partial_usage: exercises
    input_tokens/output_tokens being None while the other two are set."""
    usage = Usage(cached_input_tokens=50, reasoning_output_tokens=10)
    event = TurnCompleted(usage=usage)
    result = _event_to_dict(event)
    assert result is not None
    assert result["usage"] == {
        "cached_input_tokens": 50,
        "reasoning_output_tokens": 10,
    }


def test_turn_failed_with_error() -> None:
    error = ErrorPayload(
        code="insufficient_quota",
        type="quota_error",
        message="Out of credits",
        status=429,
    )
    event = TurnFailed(error=error)
    result = _event_to_dict(event)
    assert result is not None
    assert result["type"] == "turn.failed"
    assert result["error"] == {
        "code": "insufficient_quota",
        "type": "quota_error",
        "message": "Out of credits",
        "status": 429,
    }


def test_turn_failed_without_error() -> None:
    event = TurnFailed(error=None)
    result = _event_to_dict(event)
    assert result == {"type": "turn.failed"}


def test_turn_failed_with_error_all_fields_none() -> None:
    """error is present but every one of its fields is None -- exercises
    the False branch of all four inner `is not None` checks at once."""
    error = ErrorPayload(code=None, type=None, message=None, status=None)
    event = TurnFailed(error=error)
    result = _event_to_dict(event)
    assert result == {"type": "turn.failed", "error": {}}


def test_item_started_with_item() -> None:
    event = ItemStarted(item={"id": "item_1", "type": "tool_use"})
    result = _event_to_dict(event)
    assert result is not None
    assert result["type"] == "item.started"
    assert result["item"] == {"id": "item_1", "type": "tool_use"}


def test_item_started_without_item() -> None:
    event = ItemStarted(item=None)
    result = _event_to_dict(event)
    assert result == {"type": "item.started"}


def test_item_completed_with_item() -> None:
    event = ItemCompleted(item={"id": "item_2", "status": "ok"})
    result = _event_to_dict(event)
    assert result is not None
    assert result["type"] == "item.completed"
    assert result["item"] == {"id": "item_2", "status": "ok"}


def test_item_completed_without_item() -> None:
    event = ItemCompleted(item=None)
    result = _event_to_dict(event)
    assert result == {"type": "item.completed"}


def test_rate_limits_updated_with_full_windows() -> None:
    reset_time = datetime(2026, 8, 18, 12, 0, 0, tzinfo=UTC)
    windows = PlanWindows(
        primary=RateLimitWindow(used_percent=75.0, window_minutes=60, resets_at=reset_time),
        secondary=RateLimitWindow(used_percent=50.0, window_minutes=1440, resets_at=reset_time),
        plan_type="tier-1",
        limit_reached="primary",
    )
    event = RateLimitsUpdated(plan_windows=windows)
    result = _event_to_dict(event)
    assert result is not None
    assert result["type"] == "rate_limits.updated"
    rate_limits = result["rate_limits"]
    assert isinstance(rate_limits, dict)
    assert rate_limits["primary"]["used_percent"] == 75.0
    assert rate_limits["primary"]["window_minutes"] == 60
    assert rate_limits["primary"]["resets_at"] == reset_time.isoformat()
    assert rate_limits["secondary"]["used_percent"] == 50.0
    assert rate_limits["plan_type"] == "tier-1"
    assert rate_limits["rate_limit_reached_type"] == "primary"


def test_rate_limits_updated_with_partial_windows() -> None:
    windows = PlanWindows(
        primary=RateLimitWindow(used_percent=None, window_minutes=60, resets_at=None),
        secondary=None,
        plan_type=None,
        limit_reached=None,
    )
    event = RateLimitsUpdated(plan_windows=windows)
    result = _event_to_dict(event)
    assert result is not None
    rate_limits = result["rate_limits"]
    assert isinstance(rate_limits, dict)
    assert rate_limits["primary"]["window_minutes"] == 60
    assert "used_percent" not in rate_limits["primary"]
    assert "secondary" not in rate_limits
    assert "plan_type" not in rate_limits
    assert "rate_limit_reached_type" not in rate_limits


def test_rate_limits_updated_with_only_secondary() -> None:
    reset_time = datetime(2026, 8, 18, 13, 0, 0, tzinfo=UTC)
    windows = PlanWindows(
        primary=None,
        secondary=RateLimitWindow(used_percent=25.0, window_minutes=720, resets_at=reset_time),
        plan_type="free",
        limit_reached=None,
    )
    event = RateLimitsUpdated(plan_windows=windows)
    result = _event_to_dict(event)
    assert result is not None
    rate_limits = result["rate_limits"]
    assert isinstance(rate_limits, dict)
    assert "primary" not in rate_limits
    assert rate_limits["secondary"]["used_percent"] == 25.0
    assert rate_limits["secondary"]["window_minutes"] == 720
    assert rate_limits["plan_type"] == "free"


def test_rate_limits_updated_primary_without_window_minutes() -> None:
    """primary is present but window_minutes is None -- no existing test
    leaves window_minutes unset while primary itself is present."""
    windows = PlanWindows(
        primary=RateLimitWindow(used_percent=10.0, window_minutes=None, resets_at=None),
        secondary=None,
        plan_type=None,
        limit_reached=None,
    )
    event = RateLimitsUpdated(plan_windows=windows)
    result = _event_to_dict(event)
    assert result is not None
    rate_limits = result["rate_limits"]
    assert isinstance(rate_limits, dict)
    assert rate_limits["primary"]["used_percent"] == 10.0
    assert "window_minutes" not in rate_limits["primary"]


def test_rate_limits_updated_secondary_with_all_fields_none() -> None:
    """secondary is present but every one of its fields is None -- exercises
    the False branch of all three inner secondary `is not None` checks."""
    windows = PlanWindows(
        primary=None,
        secondary=RateLimitWindow(used_percent=None, window_minutes=None, resets_at=None),
        plan_type=None,
        limit_reached=None,
    )
    event = RateLimitsUpdated(plan_windows=windows)
    result = _event_to_dict(event)
    assert result is not None
    rate_limits = result["rate_limits"]
    assert isinstance(rate_limits, dict)
    assert rate_limits["secondary"] == {}


def test_rate_limits_updated_without_windows() -> None:
    event = RateLimitsUpdated(plan_windows=None)
    result = _event_to_dict(event)
    assert result == {"type": "rate_limits.updated"}


def test_error_event_with_error() -> None:
    error = ErrorPayload(code="timeout", type="network_error", message="Timed out", status=None)
    event = ErrorEvent(error=error)
    result = _event_to_dict(event)
    assert result is not None
    assert result["type"] == "error"
    assert result["error"]["code"] == "timeout"
    assert result["error"]["type"] == "network_error"
    assert result["error"]["message"] == "Timed out"
    assert "status" not in result["error"]


def test_error_event_with_only_status() -> None:
    """Complements test_error_event_with_error: code/type/message are None
    while status is set, exercising their False branches."""
    error = ErrorPayload(code=None, type=None, message=None, status=500)
    event = ErrorEvent(error=error)
    result = _event_to_dict(event)
    assert result == {"type": "error", "error": {"status": 500}}


def test_error_event_without_error() -> None:
    event = ErrorEvent(error=None)
    result = _event_to_dict(event)
    assert result == {"type": "error"}


def test_unknown_event() -> None:
    event = UnknownEvent(type="custom.event.type")
    result = _event_to_dict(event)
    assert result == {"type": "custom.event.type"}
