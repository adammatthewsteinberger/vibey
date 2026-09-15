# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Translates raw claude_agent_sdk messages into the typed TurnSignals /
StructuredVerdict / TurnOutcome shapes domain/ and application/ operate on.

Reads THREE independent SDK signals — RateLimitEvent, ResultMessage, and
AssistantMessage — never RateLimitEvent alone. See
docs/architecture/decisions/0002-agent-sdk-over-subprocess.md."""

from __future__ import annotations

import json
from collections.abc import Callable, Sequence
from datetime import datetime, timezone
from typing import Any

from claude_agent_sdk import (
    AssistantMessage,
    RateLimitEvent,
    ResultMessage,
    StreamEvent,
    TextBlock,
    ThinkingBlock,
    ToolResultBlock,
    ToolUseBlock,
)

from claudeloop.application.dto import TurnOutcome
from claudeloop.domain.classify import TurnSignals
from claudeloop.domain.completion import StructuredVerdict

EventListener = Callable[[dict[str, object]], None]


class TurnAccumulator:
    """Collects one turn's worth of SDK messages (everything from a prompt send
    to the terminating ResultMessage) and reduces them to a TurnOutcome."""

    def __init__(self, *, on_event: EventListener | None = None) -> None:
        self._on_event = on_event
        self._rate_limit_status: str | None = None
        self._rate_limit_type: str | None = None
        self._resets_at: int | None = None  # unix timestamp; converted in build()
        self._utilization: float | None = None
        self._overage_status: str | None = None
        self._overage_resets_at: int | None = None  # unix timestamp; converted in build()
        self._overage_disabled_reason: str | None = None
        self._api_error_status: int | None = None
        self._assistant_error: str | None = None
        self._error_code: str | None = None
        self._disabled_reason: str | None = None
        self._can_purchase: bool | None = None
        self._text_parts: list[str] = []
        self._thinking_parts: list[str] = []
        self._tool_events: list[dict[str, object]] = []
        self._session_id: str | None = None
        self._cost_usd: float = 0.0
        self._structured: dict[str, object] | None = None
        self._raw_events: list[dict[str, object]] = []
        self._result_text: str | None = None

    @property
    def thinking_text(self) -> str:
        return "\n".join(self._thinking_parts)

    @property
    def tool_events(self) -> tuple[dict[str, object], ...]:
        return tuple(self._tool_events)

    def feed(self, message: object) -> None:
        event = _message_to_event(message)
        self._raw_events.append(event)
        if self._on_event is not None:
            self._on_event(event)

        if isinstance(message, StreamEvent):
            self._session_id = message.session_id or self._session_id
            return
        if isinstance(message, RateLimitEvent):
            info = message.rate_limit_info
            self._rate_limit_status = info.status
            self._rate_limit_type = info.rate_limit_type
            self._resets_at = info.resets_at
            self._utilization = info.utilization
            self._overage_status = info.overage_status
            self._overage_resets_at = info.overage_resets_at
            self._overage_disabled_reason = info.overage_disabled_reason
            self._session_id = message.session_id or self._session_id
        elif isinstance(message, AssistantMessage):
            self._session_id = message.session_id or self._session_id
            if message.error is not None:
                self._assistant_error = str(message.error)
            for block in message.content:
                if isinstance(block, TextBlock):
                    self._text_parts.append(block.text)
                elif isinstance(block, ThinkingBlock):
                    thinking = getattr(block, "thinking", None) or getattr(block, "text", None)
                    if thinking is not None:
                        self._thinking_parts.append(str(thinking))
                elif isinstance(block, ToolUseBlock):
                    tool_ev = {
                        "name": block.name,
                        "input": getattr(block, "input", None),
                        "id": getattr(block, "id", None),
                    }
                    self._tool_events.append(tool_ev)
                elif isinstance(block, ToolResultBlock):
                    self._tool_events.append(
                        {
                            "name": "tool_result",
                            "content": getattr(block, "content", None),
                            "tool_use_id": getattr(block, "tool_use_id", None),
                        }
                    )
        elif isinstance(message, ResultMessage):
            self._session_id = message.session_id or self._session_id
            if message.api_error_status is not None:
                self._api_error_status = message.api_error_status
            if message.total_cost_usd is not None:
                self._cost_usd = message.total_cost_usd
            if message.result:
                self._result_text = message.result
                self._text_parts.append(message.result)
            if isinstance(message.structured_output, dict):
                self._structured = message.structured_output
            self._ingest_credit_signals_from_errors(message.errors or [])
            self._ingest_credit_signals_from_error_details(message)

    def _ingest_credit_signals_from_errors(self, errors: Sequence[object]) -> None:
        for err in errors:
            err_str = str(err)
            if "credits_required" in err_str:
                self._error_code = "credits_required"
            if "out_of_credits" in err_str:
                self._disabled_reason = "out_of_credits"
            self._scan_credit_blob(err)

    def _ingest_credit_signals_from_error_details(self, message: ResultMessage) -> None:
        details = getattr(message, "error_details", None) or getattr(message, "errorDetails", None)
        if details is None:
            return
        self._scan_credit_blob(details)

    def _scan_credit_blob(self, blob: object) -> None:
        if isinstance(blob, dict):
            code = blob.get("error_code") or blob.get("errorCode")
            if code is not None and str(code) == "credits_required":
                self._error_code = "credits_required"
            disabled = blob.get("disabled_reason") or blob.get("disabledReason")
            if disabled is not None and str(disabled) == "out_of_credits":
                self._disabled_reason = "out_of_credits"
            can_purchase = blob.get("can_user_purchase_credits")
            if can_purchase is None:
                can_purchase = blob.get("canUserPurchaseCredits")
            if isinstance(can_purchase, bool):
                self._can_purchase = can_purchase
            for value in blob.values():
                self._scan_credit_blob(value)
            return
        if isinstance(blob, list):
            for item in blob:
                self._scan_credit_blob(item)
            return
        if isinstance(blob, str):
            if "credits_required" in blob:
                self._error_code = "credits_required"
            if "out_of_credits" in blob:
                self._disabled_reason = "out_of_credits"
            try:
                parsed: Any = json.loads(blob)
            except (json.JSONDecodeError, TypeError):
                return
            self._scan_credit_blob(parsed)

    def build(self) -> TurnOutcome:
        # Prefer ResultMessage.result; fall back to joined assistant text so
        # spend-limit copy is visible even when RateLimitEvent was dropped.
        result_text = self._result_text
        if not result_text and self._text_parts:
            result_text = "\n".join(self._text_parts)
        signals = TurnSignals(
            rate_limit_status=self._rate_limit_status,
            rate_limit_type=self._rate_limit_type,
            resets_at=_to_datetime(self._resets_at),
            utilization=self._utilization,
            overage_status=self._overage_status,
            overage_resets_at=_to_datetime(self._overage_resets_at),
            overage_disabled_reason=self._overage_disabled_reason,
            api_error_status=self._api_error_status,
            assistant_error=self._assistant_error,
            error_code=self._error_code,
            disabled_reason=self._disabled_reason,
            can_purchase=self._can_purchase,
            result_text=result_text,
        )
        verdict = None
        if self._structured is not None:
            raw_remaining = self._structured.get("remaining_work")
            items: list[object] = list(raw_remaining) if isinstance(raw_remaining, list) else []
            remaining_work = tuple(str(item) for item in items)
            raw_blocked_on = self._structured.get("blocked_on")
            blocked_on = str(raw_blocked_on) if raw_blocked_on is not None else None
            verdict = StructuredVerdict(
                complete=bool(self._structured.get("complete", False)),
                remaining_work=remaining_work,
                blocked_on=blocked_on,
                summary=str(self._structured.get("summary", "")),
            )
        return TurnOutcome(
            signals=signals,
            verdict=verdict,
            output_text="\n".join(self._text_parts),
            session_id=self._session_id,
            cost_usd=self._cost_usd,
            raw_events=tuple(self._raw_events),
        )


def _stream_delta_text(event: dict[str, Any]) -> str | None:
    """Extract assistant text from an Anthropic-style stream event dict."""
    etype = event.get("type")
    if etype == "content_block_delta":
        delta = event.get("delta")
        if isinstance(delta, dict):
            text = delta.get("text")
            if isinstance(text, str):
                return text
            thinking = delta.get("thinking")
            if isinstance(thinking, str):
                return thinking
    if etype == "content_block_start":
        block = event.get("content_block")
        if isinstance(block, dict) and block.get("type") == "text":
            text = block.get("text")
            if isinstance(text, str) and text:
                return text
    return None


def _message_to_event(message: object) -> dict[str, object]:
    """Serialize an SDK message into a JSON-friendly event dict for audit/raw_events."""
    type_name = type(message).__name__
    payload: dict[str, object] = {"type": type_name}
    if isinstance(message, StreamEvent):
        payload["session_id"] = message.session_id
        payload["uuid"] = message.uuid
        payload["event"] = message.event
        delta = _stream_delta_text(message.event if isinstance(message.event, dict) else {})
        if delta is not None:
            payload["delta_text"] = delta
        return payload
    if isinstance(message, RateLimitEvent):
        info = message.rate_limit_info
        payload["session_id"] = message.session_id
        payload["status"] = info.status
        payload["rate_limit_type"] = info.rate_limit_type
        payload["resets_at"] = info.resets_at
        payload["utilization"] = info.utilization
        payload["overage_status"] = info.overage_status
        payload["overage_resets_at"] = info.overage_resets_at
        payload["overage_disabled_reason"] = info.overage_disabled_reason
        return payload
    if isinstance(message, AssistantMessage):
        payload["session_id"] = message.session_id
        payload["error"] = str(message.error) if message.error is not None else None
        texts = [block.text for block in message.content if isinstance(block, TextBlock)]
        payload["text"] = "\n".join(texts)
        tools = [
            {"name": block.name, "id": getattr(block, "id", None)}
            for block in message.content
            if isinstance(block, ToolUseBlock)
        ]
        if tools:
            payload["tools"] = tools
        return payload
    if isinstance(message, ResultMessage):
        payload["session_id"] = message.session_id
        payload["api_error_status"] = message.api_error_status
        payload["total_cost_usd"] = message.total_cost_usd
        payload["result"] = message.result
        payload["errors"] = list(message.errors or [])
        payload["structured_output"] = message.structured_output
        return payload
    payload["repr"] = repr(message)
    return payload


def _to_datetime(unix_timestamp: int | None) -> datetime | None:
    """Live testing found SDKSessionInfo.last_modified is milliseconds, not
    seconds, despite being documented only as "unix timestamp" (see
    infrastructure/agent/catalog.py). RateLimitInfo.resets_at carries the same
    vague documentation, so rather than assume a fixed unit here too, use the
    same digit-count heuristic the legacy script already needed for its
    resetsAt handling: ~10 digits is seconds, ~13 digits is milliseconds.

    Always returns aware UTC. ``SystemClock.now()`` is aware UTC, and
    ``next_probe_instant`` compares ``resets_at`` against ``now`` — mixing a
    naive local ``fromtimestamp`` with aware UTC raises TypeError and aborts
    the autonomous wait path on every real rate-limit rejection.
    """
    if unix_timestamp is None:
        return None
    seconds = unix_timestamp / 1000 if unix_timestamp >= 10_000_000_000 else unix_timestamp
    return datetime.fromtimestamp(seconds, tz=timezone.utc)


COMPLETION_OUTPUT_SCHEMA: dict[str, object] = {
    "type": "object",
    "description": (
        "Per-turn completion verdict for the autonomous runner. "
        "A non-null blocked_on immediately stops the run as failed — "
        "use it only for true external or human blockers, never for "
        "waitable work you started yourself."
    ),
    "properties": {
        "complete": {
            "type": "boolean",
            "description": (
                "True only when the ENTIRE task is finished with nothing left "
                "to do. False if any work remains, including waiting on a "
                "background job, test suite, or build you started."
            ),
        },
        "remaining_work": {
            "type": "array",
            "items": {"type": "string"},
            "description": (
                "Concrete unfinished items. Include waitable work you can "
                "resume later (background Agent/Bash tasks, pending suite "
                "runs, in-flight builds). Leave empty only when complete is "
                "true."
            ),
        },
        "blocked_on": {
            "type": ["string", "null"],
            "description": (
                "Set ONLY for a true external or human blocker that cannot be "
                "resolved by waiting or continuing (missing credentials, unpaid "
                "billing, required human decision, unavailable MCP auth). MUST "
                "be null when waiting on work you started yourself — background "
                "tasks, pending tests, builds, or other waitable progress. "
                "Putting waitable work here stops the autonomous run "
                "permanently; put those items in remaining_work instead and "
                "keep working or poll until they finish."
            ),
        },
        "summary": {
            "type": "string",
            "description": ("Short status of what this turn accomplished and what remains."),
        },
    },
    "required": ["complete"],
}
