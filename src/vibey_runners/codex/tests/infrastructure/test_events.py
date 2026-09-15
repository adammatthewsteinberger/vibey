# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""JSONL event parser: fixture streams, forgiving edge cases, rate_limits (R3)."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from codexloop.infrastructure.agent.events import (
    ErrorEvent,
    ErrorPayload,
    ItemCompleted,
    ItemStarted,
    JsonlParser,
    RateLimitsUpdated,
    ThreadStarted,
    TurnCompleted,
    TurnFailed,
    TurnStarted,
    UnknownEvent,
)

JSONL = Path(__file__).resolve().parents[1] / "fixtures" / "jsonl"

CLEAN_THREAD_ID = "0199a213-81c0-7800-8aa1-bbab2a035a53"

WINDOW_ERROR = {
    "message": "You have reached your usage limit. Try again later.",
    "code": "usage_limit_reached",
    "type": "usage_limit_reached",
    "status": 429,
}


def _parse_fixture(name: str, parser: JsonlParser | None = None) -> list[object]:
    parser = parser or JsonlParser()
    path = JSONL / f"{name}.jsonl"
    events: list[object] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        events.append(parser.parse_line(line))
    return events


# --- Fixture streams ----------------------------------------------------------


def test_clean_completion_stream_yields_documented_sequence() -> None:
    events = _parse_fixture("clean_completion")
    assert [type(e) for e in events] == [
        ThreadStarted,
        TurnStarted,
        ItemCompleted,
        TurnCompleted,
    ]


def test_clean_completion_thread_started_surfaces_thread_id() -> None:
    events = _parse_fixture("clean_completion")
    started = events[0]
    assert isinstance(started, ThreadStarted)
    assert started.thread_id == CLEAN_THREAD_ID


def test_clean_completion_turn_completed_surfaces_usage() -> None:
    events = _parse_fixture("clean_completion")
    completed = events[-1]
    assert isinstance(completed, TurnCompleted)
    assert completed.usage is not None
    assert completed.usage.input_tokens == 24763
    assert completed.usage.cached_input_tokens == 24448
    assert completed.usage.output_tokens == 122
    assert completed.usage.reasoning_output_tokens == 0


def test_tool_heavy_stream_yields_documented_sequence() -> None:
    events = _parse_fixture("tool_heavy")
    assert [type(e) for e in events] == [
        ThreadStarted,
        TurnStarted,
        ItemStarted,
        ItemCompleted,
        ItemStarted,
        ItemCompleted,
        ItemStarted,
        ItemCompleted,
        ItemCompleted,
        TurnCompleted,
    ]
    first_item = events[2]
    assert isinstance(first_item, ItemStarted)
    assert first_item.item is not None
    assert first_item.item["id"] == "item_1"
    last = events[-1]
    assert isinstance(last, TurnCompleted)
    assert last.usage is not None
    assert last.usage.input_tokens == 1000


def test_turn_failed_429_window_stream_surfaces_error() -> None:
    events = _parse_fixture("turn_failed_429_window")
    assert [type(e) for e in events] == [ThreadStarted, TurnStarted, TurnFailed]
    failed = events[-1]
    assert isinstance(failed, TurnFailed)
    assert failed.error is not None
    assert failed.error.code == "usage_limit_reached"
    assert failed.error.type == "usage_limit_reached"
    assert failed.error.status == 429


def test_turn_failed_429_quota_stream_surfaces_error() -> None:
    events = _parse_fixture("turn_failed_429_quota")
    assert [type(e) for e in events] == [ThreadStarted, TurnStarted, TurnFailed]
    failed = events[-1]
    assert isinstance(failed, TurnFailed)
    assert failed.error is not None
    assert failed.error.code == "insufficient_quota"
    assert failed.error.message is not None
    assert "quota" in failed.error.message.lower()


def test_malformed_line_fixture_yields_none_and_increments_counter() -> None:
    parser = JsonlParser()
    events = _parse_fixture("malformed_line", parser)
    assert isinstance(events[0], ThreadStarted)
    assert events[1] is None
    assert isinstance(events[2], TurnStarted)
    assert parser.malformed_count == 1


def test_truncated_stream_has_no_turn_completed() -> None:
    events = _parse_fixture("truncated_stream")
    assert [type(e) for e in events] == [ThreadStarted, TurnStarted]
    assert not any(isinstance(e, TurnCompleted) for e in events)


def test_huge_line_placeholder_ignores_unknown_extra_fields() -> None:
    events = _parse_fixture("huge_line")
    assert len(events) == 1
    started = events[0]
    assert isinstance(started, ThreadStarted)
    assert started.thread_id == "synthetic-huge-line-placeholder"


# --- Forgiving parser ---------------------------------------------------------


def test_unknown_type_becomes_unknown_event_and_never_raises() -> None:
    parser = JsonlParser()
    event = parser.parse_line('{"type":"definitely.not.a.real.event","extra":1}')
    assert isinstance(event, UnknownEvent)
    assert event.type == "definitely.not.a.real.event"
    assert parser.malformed_count == 0


def test_malformed_line_returns_none_and_increments_counter() -> None:
    parser = JsonlParser()
    assert parser.malformed_count == 0
    assert parser.parse_line("this is not json") is None
    assert parser.malformed_count == 1
    assert parser.parse_line("{") is None
    assert parser.malformed_count == 2
    event = parser.parse_line('{"type":"turn.started"}')
    assert isinstance(event, TurnStarted)
    assert parser.malformed_count == 2


def test_missing_type_returns_none() -> None:
    parser = JsonlParser()
    assert parser.parse_line('{"thread_id":"abc"}') is None
    assert parser.malformed_count == 0


def test_non_object_json_returns_none_and_increments() -> None:
    parser = JsonlParser()
    assert parser.parse_line("[1, 2]") is None
    assert parser.malformed_count == 1


@pytest.mark.parametrize(
    "payload",
    [
        pytest.param({"type": "turn.failed", "error": WINDOW_ERROR}, id="error"),
        pytest.param(
            {"type": "turn.failed", "payload": {"error": WINDOW_ERROR}},
            id="payload.error",
        ),
        pytest.param(
            {"type": "turn.failed", "item": {"error": WINDOW_ERROR}},
            id="item.error",
        ),
        pytest.param(
            {"type": "turn.failed", "turn": {"error": WINDOW_ERROR}},
            id="turn.error",
        ),
    ],
)
def test_turn_failed_finds_error_at_candidate_paths(payload: dict[str, object]) -> None:
    parser = JsonlParser()
    event = parser.parse_line(json.dumps(payload))
    assert isinstance(event, TurnFailed)
    assert event.error == ErrorPayload(
        code="usage_limit_reached",
        type="usage_limit_reached",
        message="You have reached your usage limit. Try again later.",
        status=429,
    )


def test_turn_failed_prefers_error_over_nested_candidates() -> None:
    parser = JsonlParser()
    event = parser.parse_line(
        json.dumps(
            {
                "type": "turn.failed",
                "error": WINDOW_ERROR,
                "payload": {"error": {"code": "other", "message": "nope"}},
            }
        )
    )
    assert isinstance(event, TurnFailed)
    assert event.error is not None
    assert event.error.code == "usage_limit_reached"


def test_error_event_parses_error_payload() -> None:
    parser = JsonlParser()
    event = parser.parse_line(
        json.dumps(
            {
                "type": "error",
                "error": {
                    "message": "boom",
                    "code": "server_error",
                    "type": "server_error",
                    "status": 500,
                },
            }
        )
    )
    assert isinstance(event, ErrorEvent)
    assert event.error == ErrorPayload(
        code="server_error",
        type="server_error",
        message="boom",
        status=500,
    )


# --- rate_limits (R3) ---------------------------------------------------------


def test_rate_limits_null_yields_none_plan_windows() -> None:
    parser = JsonlParser()
    event = parser.parse_line('{"type":"rate_limits.updated","rate_limits":null}')
    assert isinstance(event, RateLimitsUpdated)
    assert event.plan_windows is None


def test_rate_limits_resets_in_seconds_converted_against_injected_now() -> None:
    now = datetime(2026, 8, 13, 12, 0, tzinfo=UTC)
    parser = JsonlParser(now=now)
    event = parser.parse_line(
        json.dumps(
            {
                "type": "rate_limits.updated",
                "rate_limits": {
                    "primary": {
                        "used_percent": 0.0,
                        "window_minutes": 299,
                        "resets_in_seconds": 17940,
                    },
                    "secondary": {
                        "used_percent": 6.0,
                        "window_minutes": 10079,
                        "resets_in_seconds": 275281,
                    },
                    "plan_type": "plus",
                    "rate_limit_reached_type": None,
                },
            }
        )
    )
    assert isinstance(event, RateLimitsUpdated)
    windows = event.plan_windows
    assert windows is not None
    assert windows.plan_type == "plus"
    assert windows.limit_reached is None
    assert windows.primary is not None
    assert windows.primary.used_percent == 0.0
    assert windows.primary.window_minutes == 299
    assert windows.primary.resets_at == now + timedelta(seconds=17940)
    assert windows.secondary is not None
    assert windows.secondary.resets_at == now + timedelta(seconds=275281)


def test_rate_limits_resets_at_epoch_converted() -> None:
    parser = JsonlParser()
    event = parser.parse_line(
        json.dumps(
            {
                "type": "rate_limits.updated",
                "rate_limits": {
                    "limit_id": "codex",
                    "primary": {
                        "used_percent": 13,
                        "window_minutes": 300,
                        "resets_at": 1780171524,
                    },
                    "secondary": {
                        "used_percent": 93,
                        "window_minutes": 10080,
                        "resets_at": 1780174809,
                    },
                    "plan_type": "plus",
                    "rate_limit_reached_type": None,
                },
            }
        )
    )
    assert isinstance(event, RateLimitsUpdated)
    windows = event.plan_windows
    assert windows is not None
    assert windows.primary is not None
    assert windows.primary.resets_at == datetime.fromtimestamp(1780171524, tz=UTC)
    assert windows.secondary is not None
    assert windows.secondary.resets_at == datetime.fromtimestamp(1780174809, tz=UTC)


def test_rate_limits_unknown_or_renamed_keys_none_for_that_window_only() -> None:
    parser = JsonlParser()
    event = parser.parse_line(
        json.dumps(
            {
                "type": "rate_limits.updated",
                "rate_limits": {
                    "primary": {
                        "used_pct": 13,
                        "window_mins": 300,
                        "reset_in": 100,
                    },
                    "secondary": {
                        "used_percent": 93,
                        "window_minutes": 10080,
                        "resets_at": 1780174809,
                    },
                    "tertiary": {
                        "used_percent": 1,
                        "window_minutes": 60,
                        "resets_at": 1780171524,
                    },
                },
            }
        )
    )
    assert isinstance(event, RateLimitsUpdated)
    windows = event.plan_windows
    assert windows is not None
    assert windows.primary is None
    assert windows.secondary is not None
    assert windows.secondary.used_percent == 93
    assert windows.secondary.window_minutes == 10080
    assert windows.secondary.resets_at == datetime.fromtimestamp(1780174809, tz=UTC)


def test_rate_limits_garbage_window_never_raises() -> None:
    parser = JsonlParser()
    event = parser.parse_line(
        json.dumps(
            {
                "type": "rate_limits.updated",
                "rate_limits": {
                    "primary": ["not", "a", "window"],
                    "secondary": None,
                },
            }
        )
    )
    assert isinstance(event, RateLimitsUpdated)
    assert event.plan_windows is not None
    assert event.plan_windows.primary is None
    assert event.plan_windows.secondary is None


def test_empty_line_and_empty_type_are_ignored() -> None:
    parser = JsonlParser()
    assert parser.parse_line("   ") is None
    assert parser.parse_line('{"type":""}') is None
    assert parser.malformed_count == 0


def test_event_msg_without_token_count_is_unknown() -> None:
    parser = JsonlParser()
    event = parser.parse_line('{"type":"event_msg","payload":{"type":"other"}}')
    assert isinstance(event, UnknownEvent)
    assert event.type == "event_msg"


def test_rate_limits_blob_missing_and_non_mapping() -> None:
    parser = JsonlParser()
    missing = parser.parse_line('{"type":"rate_limits.updated"}')
    assert isinstance(missing, RateLimitsUpdated)
    assert missing.plan_windows is None
    non_map = parser.parse_line('{"type":"rate_limits.updated","rate_limits":["x"]}')
    assert isinstance(non_map, RateLimitsUpdated)
    assert non_map.plan_windows is None


def test_usage_and_item_non_mapping_are_none() -> None:
    parser = JsonlParser()
    completed = parser.parse_line('{"type":"turn.completed","usage":"nope"}')
    assert isinstance(completed, TurnCompleted)
    assert completed.usage is None
    started = parser.parse_line('{"type":"item.started","item":"nope"}')
    assert isinstance(started, ItemStarted)
    assert started.item is None


def test_error_string_and_non_mapping_payloads() -> None:
    parser = JsonlParser()
    as_str = parser.parse_line('{"type":"error","error":"boom"}')
    assert isinstance(as_str, ErrorEvent)
    assert as_str.error == ErrorPayload(code=None, type=None, message="boom", status=None)
    as_list = parser.parse_line('{"type":"turn.failed","error":[1]}')
    assert isinstance(as_list, TurnFailed)
    assert as_list.error is None
    missing = parser.parse_line('{"type":"turn.failed"}')
    assert isinstance(missing, TurnFailed)
    assert missing.error is None


def test_error_found_but_unusable_continues_to_next_path() -> None:
    parser = JsonlParser()
    event = parser.parse_line(
        json.dumps(
            {
                "type": "turn.failed",
                "error": [1],
                "payload": {"error": WINDOW_ERROR},
            }
        )
    )
    assert isinstance(event, TurnFailed)
    assert event.error is not None
    assert event.error.code == "usage_limit_reached"


def test_window_bool_resets_and_integer_float_tokens() -> None:
    now = datetime(2026, 8, 13, 12, 0, tzinfo=UTC)
    parser = JsonlParser(now=now)
    event = parser.parse_line(
        json.dumps(
            {
                "type": "rate_limits.updated",
                "rate_limits": {
                    "primary": {
                        "used_percent": True,
                        "window_minutes": 10.0,
                        "resets_at": True,
                        "resets_in_seconds": True,
                    },
                    "secondary": {
                        "used_percent": "nope",
                        "window_minutes": 5,
                    },
                },
            }
        )
    )
    assert isinstance(event, RateLimitsUpdated)
    windows = event.plan_windows
    assert windows is not None
    assert windows.primary is not None
    assert windows.primary.used_percent is None
    assert windows.primary.window_minutes == 10
    assert windows.primary.resets_at is None
    assert windows.secondary is not None
    assert windows.secondary.used_percent is None
    assert windows.secondary.resets_at is None


def test_window_overflow_resets_never_raise() -> None:
    parser = JsonlParser()
    event = parser.parse_line(
        json.dumps(
            {
                "type": "rate_limits.updated",
                "rate_limits": {
                    "primary": {
                        "used_percent": 1,
                        "window_minutes": 1,
                        "resets_at": 10**20,
                    },
                    "secondary": {
                        "used_percent": 1,
                        "window_minutes": 1,
                        "resets_in_seconds": 10**20,
                    },
                },
            }
        )
    )
    assert isinstance(event, RateLimitsUpdated)
    assert event.plan_windows is not None
    assert event.plan_windows.primary is not None
    assert event.plan_windows.primary.resets_at is None
    assert event.plan_windows.secondary is not None
    assert event.plan_windows.secondary.resets_at is None


def test_window_exception_path_returns_none(monkeypatch: pytest.MonkeyPatch) -> None:
    def _boom(_value: object) -> int:
        raise OverflowError

    monkeypatch.setattr("codexloop.infrastructure.agent.events._opt_int", _boom)
    parser = JsonlParser()
    event = parser.parse_line(
        json.dumps(
            {
                "type": "rate_limits.updated",
                "rate_limits": {"primary": {"window_minutes": 1}},
            }
        )
    )
    assert isinstance(event, RateLimitsUpdated)
    assert event.plan_windows is not None
    assert event.plan_windows.primary is None


def test_event_msg_token_count_parses_as_rate_limits_updated() -> None:
    now = datetime(2026, 1, 1, tzinfo=UTC)
    parser = JsonlParser(now=now)
    event = parser.parse_line(
        json.dumps(
            {
                "type": "event_msg",
                "payload": {
                    "type": "token_count",
                    "info": None,
                    "rate_limits": {
                        "primary": {
                            "used_percent": 0.0,
                            "window_minutes": 299,
                            "resets_in_seconds": 17940,
                        },
                        "secondary": {
                            "used_percent": 6.0,
                            "window_minutes": 10079,
                            "resets_in_seconds": 275281,
                        },
                    },
                },
            }
        )
    )
    assert isinstance(event, RateLimitsUpdated)
    assert event.plan_windows is not None
    assert event.plan_windows.primary is not None
    assert event.plan_windows.primary.resets_at == now + timedelta(seconds=17940)
