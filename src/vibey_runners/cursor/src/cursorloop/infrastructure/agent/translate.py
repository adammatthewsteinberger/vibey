# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Translate Cursor SDK runs and errors into TurnSignals / TurnOutcome.

Duck-typed on purpose: every SDK attribute is read with ``getattr(..., None)``
so a version that lacks a field cannot crash the run. ``cursor_sdk`` types are
not imported here — the gateway (Task 13) owns that dependency.
"""

from __future__ import annotations

from typing import Any

from cursorloop.application.dto import TurnOutcome
from cursorloop.application.ports import RunEventSink, StreamUi
from cursorloop.domain.classify import TurnSignals
from cursorloop.domain.completion import parse_verdict_block


def signals_from_exception(exc: BaseException) -> TurnSignals:
    """Capture classifier inputs from a thrown CursorAgentError (or lookalike)."""
    raw_message = getattr(exc, "message", None)
    error_message = raw_message if isinstance(raw_message, str) else str(exc)
    return TurnSignals(
        error_type=type(exc).__name__,
        error_code=_optional_str(getattr(exc, "code", None)),
        proto_error_code=_optional_str(getattr(exc, "proto_error_code", None)),
        error_message=error_message,
        http_status=_optional_int(getattr(exc, "status_code", None)),
        is_retryable=_optional_bool(getattr(exc, "is_retryable", None)),
        retry_after=_optional_str(getattr(exc, "retry_after", None)),
        request_id=_optional_str(getattr(exc, "request_id", None)),
    )


def signals_from_run(run: object, *, fallback_text: str = "") -> TurnSignals:
    """Capture classifier inputs from a Run, including non-thrown ``status=error``.

    Live bridge errors often put the human-readable reason on a stream
    ``status`` message while leaving ``run.result`` empty. ``fallback_text``
    carries that status copy (or other tee-captured detail) into the
    billing/rate-limit lexicons.
    """
    status = getattr(run, "status", None)
    result = getattr(run, "result", None)
    result_text = result if isinstance(result, str) else ""
    if not result_text.strip() and fallback_text.strip():
        result_text = fallback_text
    return TurnSignals(
        run_status=status if isinstance(status, str) else None,
        result_text=result_text,
    )


def outcome_from_run(
    run: object,
    buffered_text: str,
    tokens: int = 0,
    cost: float | None = None,
    *,
    signals_fallback: str = "",
) -> TurnOutcome:
    """Build a TurnOutcome. ``cost is None`` means UNKNOWN (never coerced to 0.0)."""
    usage = getattr(run, "usage", None)
    usage_tokens = getattr(usage, "total_tokens", None) if usage is not None else None
    resolved_tokens = _optional_int(usage_tokens)
    if resolved_tokens is None:
        resolved_tokens = tokens
    agent_id = getattr(run, "agent_id", None)
    run_id = getattr(run, "id", None)
    return TurnOutcome(
        signals=signals_from_run(run, fallback_text=signals_fallback),
        verdict=parse_verdict_block(buffered_text),
        output_text=buffered_text,
        agent_id=agent_id if isinstance(agent_id, str) else None,
        run_id=run_id if isinstance(run_id, str) else None,
        tokens=resolved_tokens,
        cost_usd=cost,
        cost_pending=cost is None,
    )


class TeeStream:
    """Consume ``run.messages()`` exactly once, then ``run.wait()``.

    ``messages()``, ``events()``, and ``iter_text()`` share one stream. Teeing
    on a single pass is what lets the UI see deltas without emptying the
    classifier's second read.
    """

    def __init__(
        self,
        run: object,
        *,
        ui: StreamUi | None = None,
        sink: RunEventSink | None = None,
        turn_id: str = "",
    ) -> None:
        self._run = run
        self._ui = ui
        self._sink = sink
        self._turn_id = turn_id
        self._seq = 0
        self._parts: list[str] = []
        self.status_error_text: str = ""
        self.raw_events: list[dict[str, object]] = []

    def drain(self) -> str:
        stream = getattr(self._run, "messages", None)
        if callable(stream):
            for message in stream():
                self._consume(message)
        wait = getattr(self._run, "wait", None)
        if callable(wait):
            wait()
        buffered = "".join(self._parts)
        if buffered.strip():
            return buffered
        # Some finished runs leave the terminal string on ``run.result`` even
        # when the assistant stream was empty or already consumed.
        result = getattr(self._run, "result", None)
        return result if isinstance(result, str) else ""

    def _consume(self, message: object) -> None:
        kind = getattr(message, "type", None)
        if kind == "assistant":
            self._on_assistant(message)
            return
        if kind == "tool_call":
            self._on_tool_call(message)
            return
        if kind == "status":
            self._on_status(message)
            return
        if kind == "usage":
            self._on_usage(message)

    def _on_assistant(self, message: object) -> None:
        text = _assistant_text(message)
        if not text:
            return
        self._parts.append(text)
        if self._ui is not None:
            self._ui.on_delta(text, turn_id=self._turn_id, seq=self._seq)
            self._seq += 1

    def _on_tool_call(self, message: object) -> None:
        name = _optional_str(getattr(message, "name", None)) or ""
        payload: dict[str, Any] = {
            "name": name,
            "call_id": _optional_str(getattr(message, "call_id", None)) or "",
            "status": _optional_str(getattr(message, "status", None)) or "",
        }
        self._emit("tool_call", payload)
        if self._ui is not None:
            self._ui.on_tool(name, str(payload["status"]))

    def _on_status(self, message: object) -> None:
        status = _optional_str(getattr(message, "status", None)) or ""
        text = _optional_str(getattr(message, "message", None)) or ""
        payload: dict[str, Any] = {
            "status": status,
            "message": text,
        }
        if status.upper() == "ERROR" and text.strip():
            self.status_error_text = text
        self._emit("status", payload)
        if self._ui is not None:
            self._ui.on_status(payload)

    def _on_usage(self, message: object) -> None:
        usage = getattr(message, "usage", None)
        total = getattr(usage, "total_tokens", None) if usage is not None else None
        payload: dict[str, Any] = {"total_tokens": _optional_int(total) or 0}
        self._emit("usage", payload)

    def _emit(self, event_type: str, payload: dict[str, Any]) -> None:
        self.raw_events.append({"type": event_type, **payload})
        if self._sink is not None:
            self._sink.emit(event_type, payload)


def _assistant_text(message: object) -> str:
    inner = getattr(message, "message", None)
    content = getattr(inner, "content", ()) if inner is not None else ()
    try:
        blocks = list(content)
    except TypeError:
        return ""
    parts: list[str] = []
    for block in blocks:
        text = getattr(block, "text", "")
        if isinstance(text, str) and text:
            parts.append(text)
    return "".join(parts)


def _optional_str(value: object) -> str | None:
    return value if isinstance(value, str) else None


def _optional_int(value: object) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def _optional_bool(value: object) -> bool | None:
    return value if isinstance(value, bool) else None
