# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""JSONL events → TurnSignals, plus fixture → classify() e2e."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace

import pytest

from codexloop.domain.capacity import Available, PlanWindows, QuotaExhausted, WindowExhausted
from codexloop.domain.classify import classify
from codexloop.domain.signals import TurnSignals
from codexloop.infrastructure.agent.events import (
    ErrorEvent,
    ErrorPayload,
    ItemCompleted,
    JsonlParser,
    RateLimitsUpdated,
    TurnCompleted,
    TurnFailed,
    Usage,
)
from codexloop.infrastructure.agent.schema import write_output_schema
from codexloop.infrastructure.agent.translate import to_turn_signals

JSONL = Path(__file__).resolve().parents[1] / "fixtures" / "jsonl"
NOW = datetime(2026, 8, 13, 12, 0, tzinfo=UTC)

FIXTURES = (
    "clean_completion",
    "tool_heavy",
    "turn_failed_429_quota",
    "turn_failed_429_window",
    "malformed_line",
    "truncated_stream",
    "huge_line",
)

CLEAN_USAGE = Usage(
    input_tokens=24763,
    cached_input_tokens=24448,
    output_tokens=122,
    reasoning_output_tokens=0,
)


def _parse(name: str) -> list[object]:
    parser = JsonlParser(now=NOW)
    path = JSONL / f"{name}.jsonl"
    events: list[object] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        events.append(parser.parse_line(line))
    return events


def _signals(name: str, *, exit_code: int = 0, stderr_tail: str = "stderr-tail") -> TurnSignals:
    return to_turn_signals(_parse(name), exit_code=exit_code, stderr_tail=stderr_tail, now=NOW)


# --- Seven fixtures -----------------------------------------------------------


@pytest.mark.parametrize("name", FIXTURES)
def test_exit_code_and_stderr_tail_always_populated(name: str) -> None:
    signals = _signals(name, exit_code=7, stderr_tail="captured-stderr")
    assert signals.exit_code == 7
    assert signals.stderr_tail == "captured-stderr"


def test_clean_completion_signals() -> None:
    signals = _signals("clean_completion")
    assert signals.completed is True
    assert signals.failed is False
    assert signals.error_code is None
    assert signals.error_type is None
    assert signals.http_status is None
    assert signals.final_message == "Repo contains docs, sdk, and examples directories."
    assert signals.usage == CLEAN_USAGE
    assert signals.plan_windows is None


def test_tool_heavy_final_message_is_last_agent_message() -> None:
    signals = _signals("tool_heavy")
    assert signals.completed is True
    assert signals.failed is False
    assert signals.final_message == "Listed files, printed cwd, and showed git status."
    assert signals.usage == Usage(
        input_tokens=1000,
        cached_input_tokens=800,
        output_tokens=50,
        reasoning_output_tokens=0,
    )


def test_turn_failed_quota_maps_error_fields() -> None:
    signals = _signals("turn_failed_429_quota")
    assert signals.completed is False
    assert signals.failed is True
    assert signals.error_code == "insufficient_quota"
    assert signals.error_type == "insufficient_quota"
    assert signals.http_status == 429
    assert signals.final_message is None
    assert signals.usage is None


def test_turn_failed_window_maps_error_fields() -> None:
    signals = _signals("turn_failed_429_window")
    assert signals.completed is False
    assert signals.failed is True
    assert signals.error_code == "usage_limit_reached"
    assert signals.error_type == "usage_limit_reached"
    assert signals.http_status == 429


def test_malformed_stream_is_still_classifiable() -> None:
    signals = _signals("malformed_line", exit_code=1, stderr_tail="parse noise")
    assert signals.completed is False
    assert signals.failed is False
    assert signals.exit_code == 1
    assert signals.stderr_tail == "parse noise"


def test_truncated_stream_has_no_completion() -> None:
    signals = _signals("truncated_stream")
    assert signals.completed is False
    assert signals.failed is False
    assert signals.usage is None
    assert signals.final_message is None


def test_huge_line_placeholder_has_no_turn_outcome_flags() -> None:
    signals = _signals("huge_line")
    assert signals.completed is False
    assert signals.failed is False
    assert signals.error_code is None


def test_error_event_maps_code_type_and_status() -> None:
    events = [
        ErrorEvent(
            error=ErrorPayload(
                code="invalid_api_key",
                type="invalid_request_error",
                message="bad key",
                status=401,
            )
        )
    ]
    signals = to_turn_signals(events, exit_code=1, stderr_tail="", now=NOW)
    assert signals.error_code == "invalid_api_key"
    assert signals.error_type == "invalid_request_error"
    assert signals.http_status == 401
    assert signals.failed is False


def test_rate_limits_updated_maps_plan_windows() -> None:
    windows = PlanWindows(primary=None, secondary=None, plan_type="plus", limit_reached=None)
    events = [RateLimitsUpdated(plan_windows=windows)]
    signals = to_turn_signals(events, exit_code=0, stderr_tail="", now=NOW)
    assert signals.plan_windows is windows


def test_rate_limits_updated_with_none_windows_is_skipped() -> None:
    events = [RateLimitsUpdated(plan_windows=None), TurnCompleted(usage=None)]
    signals = to_turn_signals(events, exit_code=0, stderr_tail="", now=NOW)
    assert signals.plan_windows is None
    assert signals.completed is True


def test_turn_failed_with_none_error_still_marks_failed() -> None:
    signals = to_turn_signals([TurnFailed(error=None)], exit_code=1, stderr_tail="x", now=NOW)
    assert signals.failed is True
    assert signals.error_code is None


def test_error_retry_after_seconds_is_merged() -> None:
    error = SimpleNamespace(code="x", type="y", status=429, retry_after_s=1.5)
    signals = to_turn_signals(
        [ErrorEvent(error=error)],  # type: ignore[arg-type]
        exit_code=1,
        stderr_tail="",
        now=NOW,
    )
    assert signals.retry_after_s == 1.5
    assert signals.error_code == "x"


def test_item_completed_none_and_non_string_text() -> None:
    events = [
        ItemCompleted(item=None),
        ItemCompleted(item={"type": "agent_message", "text": 12}),
        TurnCompleted(usage=None),
    ]
    signals = to_turn_signals(events, exit_code=0, stderr_tail="", now=NOW)
    assert signals.final_message is None


def test_non_agent_item_completed_is_not_final_message() -> None:
    events = [
        ItemCompleted(item={"id": "item_1", "type": "command_execution", "command": "ls"}),
        TurnCompleted(usage=None),
    ]
    signals = to_turn_signals(events, exit_code=0, stderr_tail="", now=NOW)
    assert signals.final_message is None
    assert signals.completed is True


# --- Fixture → parse → translate → classify() --------------------------------


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("clean_completion", Available()),
        ("tool_heavy", Available()),
        ("turn_failed_429_quota", QuotaExhausted(reason="insufficient_quota")),
        ("turn_failed_429_window", WindowExhausted(resets_at=None, window="unknown")),
        ("malformed_line", Available()),
        ("truncated_stream", Available()),
        ("huge_line", Available()),
    ],
)
def test_fixture_parse_translate_classify(name: str, expected: object) -> None:
    state = classify(_signals(name))
    assert state == expected


# --- Completion JSON Schema ---------------------------------------------------


def _schema_errors(instance: object, schema: dict[str, object]) -> list[str]:
    """Tiny required-keys / types checker driven by the emitted schema."""
    errors: list[str] = []
    if schema.get("type") != "object" or not isinstance(instance, dict):
        return ["not an object"]
    required = schema.get("required", [])
    properties = schema.get("properties", {})
    if not isinstance(required, list) or not isinstance(properties, dict):
        return ["schema missing required/properties"]
    for key in required:
        if not isinstance(key, str) or key not in instance:
            errors.append(f"missing {key}")
    if schema.get("additionalProperties") is False:
        for key in instance:
            if key not in properties:
                errors.append(f"extra {key}")
    for key, spec in properties.items():
        if key not in instance or not isinstance(spec, dict):
            continue
        allowed = spec.get("type")
        value = instance[key]
        if allowed == "boolean" and not isinstance(value, bool):
            errors.append(f"{key} not boolean")
        elif allowed == "string" and not isinstance(value, str):
            errors.append(f"{key} not string")
        elif allowed == ["string", "null"] and not isinstance(value, str | type(None)):
            errors.append(f"{key} not string|null")
        elif allowed == "array":
            if not isinstance(value, list):
                errors.append(f"{key} not array")
            else:
                items = spec.get("items")
                if (
                    isinstance(items, dict)
                    and items.get("type") == "string"
                    and any(not isinstance(item, str) for item in value)
                ):
                    errors.append(f"{key} items not string")
    return errors


def test_emitted_schema_accepts_conforming_verdict_and_rejects_nonconforming(
    tmp_path: Path,
) -> None:
    path = write_output_schema(tmp_path / "completion.schema.json")
    assert path.is_file()
    schema = json.loads(path.read_text(encoding="utf-8"))
    conforming = {
        "complete": True,
        "remaining_work": [],
        "blocked_on": None,
        "summary": "Implemented and tested the parser; all gates green.",
    }
    assert _schema_errors(conforming, schema) == []
    assert _schema_errors({"complete": True}, schema)
    assert _schema_errors("not-an-object", schema)
