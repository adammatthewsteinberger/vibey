# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
from __future__ import annotations

from types import SimpleNamespace
from typing import Any

from cursorloop.domain.completion import StructuredVerdict
from cursorloop.infrastructure.agent.translate import (
    TeeStream,
    outcome_from_run,
    signals_from_exception,
    signals_from_run,
)
from tests.fixtures import sdk_payloads


def test_exception_fields_are_captured_verbatim_for_classification() -> None:
    exc = sdk_payloads.fake_rate_limit_error(
        code="usage_limit_reached", is_retryable=False, retry_after=None, request_id="req_123"
    )
    signals = signals_from_exception(exc)
    assert signals.error_type == "RateLimitError"
    assert signals.error_code == "usage_limit_reached"
    assert signals.is_retryable is False
    assert signals.request_id == "req_123"


def test_errored_run_without_an_exception_still_produces_signals() -> None:
    """The non-thrown channel. run.wait() returning status='error' is a real,
    first-class outcome — not an absence of failure."""
    run = sdk_payloads.fake_run(status="error", result="Usage limit reached for this month.")
    signals = signals_from_run(run)
    assert signals.run_status == "error"
    assert "usage limit" in signals.result_text.lower()


def test_request_id_is_always_carried_for_support_escalation() -> None:
    exc = sdk_payloads.fake_network_error(request_id="req_abc")
    assert signals_from_exception(exc).request_id == "req_abc"


def test_stream_is_consumed_exactly_once() -> None:
    """messages(), events(), and iter_text() all advance the same underlying
    stream. Any adapter that both streams for the UI and re-reads for
    classification gets an empty second pass — so we tee on a single pass."""
    run = sdk_payloads.fake_streaming_run(["hello ", "world"])
    tee = TeeStream(run)
    text = tee.drain()
    assert text == "hello world"
    assert run.consume_count == 1


def test_missing_sdk_attributes_do_not_crash_the_run() -> None:
    """An SDK version that lacks a field must not take the turn down with it."""
    signals = signals_from_exception(RuntimeError("no sdk fields"))
    assert signals.error_type == "RuntimeError"
    assert signals.error_code is None
    assert signals.proto_error_code is None
    assert signals.http_status is None
    assert signals.is_retryable is None
    assert signals.retry_after is None
    assert signals.request_id is None
    assert signals.error_message == "no sdk fields"


def test_status_code_maps_to_http_status() -> None:
    exc = sdk_payloads.fake_rate_limit_error(status_code=429, code="rate_limited")
    signals = signals_from_exception(exc)
    assert signals.http_status == 429
    assert signals.proto_error_code is None


def test_proto_error_code_and_message_are_captured() -> None:
    exc = sdk_payloads.fake_rate_limit_error(
        proto_error_code="usage_limit_reached",
        message="You have reached your monthly usage limit.",
        retry_after="60",
        is_retryable=True,
    )
    signals = signals_from_exception(exc)
    assert signals.proto_error_code == "usage_limit_reached"
    assert signals.error_message == "You have reached your monthly usage limit."
    assert signals.retry_after == "60"
    assert signals.is_retryable is True


def test_finished_cancelled_and_expired_run_statuses_are_propagated() -> None:
    assert signals_from_run(sdk_payloads.fake_run(status="finished", result="done")).run_status == (
        "finished"
    )
    assert signals_from_run(sdk_payloads.fake_run(status="cancelled")).run_status == "cancelled"
    assert signals_from_run(sdk_payloads.fake_run(status="expired")).run_status == "expired"
    assert signals_from_run(sdk_payloads.fake_run(status="running")).run_status == "running"


def test_unsettled_cost_stays_none_and_pending() -> None:
    """cost_usd is None means UNKNOWN, never 0.0. Unsettled cost stays pending."""
    run = sdk_payloads.fake_run(status="finished", result="done")
    outcome = outcome_from_run(run, "done", 0, None)
    assert outcome.cost_usd is None
    assert outcome.cost_pending is True


def test_settled_cost_is_recorded_and_not_pending() -> None:
    run = sdk_payloads.fake_run(status="finished", result="ok")
    outcome = outcome_from_run(run, "ok", 3, 0.12)
    assert outcome.cost_usd == 0.12
    assert outcome.cost_pending is False


def test_tokens_come_from_run_usage_when_present() -> None:
    run = sdk_payloads.fake_run(status="finished", result="done", total_tokens=42)
    outcome = outcome_from_run(run, "done", 0, None)
    assert outcome.tokens == 42


def test_tokens_argument_is_used_when_run_has_no_usage() -> None:
    run = sdk_payloads.fake_run(status="finished", result="done")
    outcome = outcome_from_run(run, "done", 7, None)
    assert outcome.tokens == 7


def test_verdict_fence_is_parsed_from_buffered_text() -> None:
    text = 'prose\n```cursorloop-verdict\n{"complete": true, "summary": "shipped"}\n```\n'
    run = sdk_payloads.fake_run(status="finished", result=text)
    outcome = outcome_from_run(run, text, 10, None)
    assert outcome.verdict == StructuredVerdict(complete=True, summary="shipped")
    assert outcome.output_text == text
    assert outcome.agent_id == "agent_1"
    assert outcome.run_id == "run_1"


def test_drain_calls_wait_after_the_single_messages_pass() -> None:
    run = sdk_payloads.fake_streaming_run(["hello ", "world"])
    TeeStream(run).drain()
    assert run.consume_count == 1
    assert run.wait_count == 1


def test_tee_forwards_deltas_to_stream_ui() -> None:
    ui = FakeStreamUi()
    run = sdk_payloads.fake_streaming_run(["hello ", "world"])
    text = TeeStream(run, ui=ui, turn_id="t1").drain()
    assert text == "hello world"
    assert ui.deltas == [("hello ", "t1", 0), ("world", "t1", 1)]


def test_tee_forwards_tool_call_status_and_usage_to_the_event_sink() -> None:
    sink = FakeRunEventSink()
    run = sdk_payloads.fake_run(
        status="finished",
        result="done",
        messages=(
            sdk_payloads.fake_tool_call_message(name="read"),
            sdk_payloads.fake_status_message(status="running", message="working"),
            sdk_payloads.fake_usage_message(total_tokens=9),
        ),
    )
    TeeStream(run, sink=sink).drain()
    kinds = [event_type for event_type, _payload in sink.events]
    assert kinds == ["tool_call", "status", "usage"]
    assert sink.events[0][1] is not None
    assert sink.events[0][1]["name"] == "read"
    assert sink.events[1][1] is not None
    assert sink.events[1][1]["status"] == "running"
    assert sink.events[2][1] is not None
    assert sink.events[2][1]["total_tokens"] == 9


def test_empty_assistant_chunks_are_skipped() -> None:
    run = sdk_payloads.fake_streaming_run(["", "hello"])
    assert TeeStream(run).drain() == "hello"


def test_malformed_or_unknown_messages_do_not_crash_the_drain() -> None:
    """A missing stream method or a junk SDKMessage must not take the turn down."""
    assert TeeStream(object()).drain() == ""
    run = sdk_payloads.fake_run(
        status="finished",
        messages=(
            SimpleNamespace(type="assistant", message=SimpleNamespace(content=123)),
            SimpleNamespace(type="thinking", text="ignored"),
            sdk_payloads.FakeAssistantMessage(
                message=sdk_payloads.FakeAssistantContent(
                    content=(sdk_payloads.FakeTextBlock(text=""),)
                )
            ),
        ),
    )
    assert TeeStream(run).drain() == ""


def test_tee_forwards_tool_and_status_to_stream_ui_without_a_sink() -> None:
    ui = FakeStreamUi()
    run = sdk_payloads.fake_run(
        status="finished",
        messages=(
            sdk_payloads.fake_tool_call_message(name="read"),
            sdk_payloads.fake_status_message(status="running", message="working"),
        ),
    )
    TeeStream(run, ui=ui).drain()
    assert ui.tools == [("read", "completed")]
    assert ui.statuses == [{"status": "running", "message": "working"}]


def test_status_error_text_is_captured_for_classifier_fallback() -> None:
    run = sdk_payloads.fake_run(
        status="error",
        result="",
        messages=(
            sdk_payloads.fake_status_message(status="RUNNING", message=""),
            sdk_payloads.fake_status_message(
                status="ERROR",
                message="You're out of usage. Switch to Auto.",
            ),
        ),
    )
    tee = TeeStream(run)
    assert tee.drain() == ""
    assert tee.status_error_text == "You're out of usage. Switch to Auto."
    outcome = outcome_from_run(run, "", signals_fallback=tee.status_error_text)
    assert outcome.signals.run_status == "error"
    assert "out of usage" in outcome.signals.result_text.lower()
    assert outcome.output_text == ""


def test_drain_falls_back_to_run_result_when_stream_has_no_assistant_text() -> None:
    run = sdk_payloads.fake_run(status="finished", result="HELLO_SMOKE", messages=())
    assert TeeStream(run).drain() == "HELLO_SMOKE"


def test_signals_from_run_prefers_non_empty_result_over_fallback() -> None:
    run = sdk_payloads.fake_run(status="error", result="add credits please")
    signals = signals_from_run(run, fallback_text="You're out of usage")
    assert signals.result_text == "add credits please"


class FakeStreamUi:
    """Tiny StreamUi double — no infrastructure import from application."""

    def __init__(self) -> None:
        self.deltas: list[tuple[str, str, int]] = []
        self.tools: list[tuple[str, str]] = []
        self.statuses: list[dict[str, Any]] = []

    def on_delta(self, text: str, *, turn_id: str, seq: int) -> None:
        self.deltas.append((text, turn_id, seq))

    def on_turn_boundary(self, *, turn_id: str, attempt: int) -> None:
        return

    def on_prompt(self, text: str) -> None:
        return

    def on_assistant(self, text: str) -> None:
        return

    def on_tool(self, name: str, summary: str) -> None:
        self.tools.append((name, summary))

    def on_status(self, state: dict[str, Any]) -> None:
        self.statuses.append(state)

    def close(self) -> None:
        return


class FakeRunEventSink:
    def __init__(self) -> None:
        self.events: list[tuple[str, dict[str, Any] | None]] = []

    def emit(self, event_type: str, payload: dict[str, Any] | None = None) -> None:
        self.events.append((event_type, payload))

    def bind(
        self,
        *,
        agent_id: str | None = None,
        attempt: int | None = None,
        phase: str | None = None,
        trace_id: str | None = None,
        turn_id: str | None = None,
    ) -> None:
        del agent_id, attempt, phase, trace_id, turn_id
