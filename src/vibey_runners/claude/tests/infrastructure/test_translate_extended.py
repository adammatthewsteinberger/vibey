# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Extended tests for translate.py to reach 100% coverage."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

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

from claudeloop.infrastructure.agent.translate import (
    TurnAccumulator,
    _stream_delta_text,
)


def _make_stream_event(session_id: str, event_dict: dict) -> object:
    """Create a mock StreamEvent."""
    msg = MagicMock(spec=StreamEvent)
    msg.__class__.__name__ = "StreamEvent"
    msg.session_id = session_id
    msg.uuid = "test-uuid"
    msg.event = event_dict
    return msg


def _make_rate_limit_event(session_id: str, **kwargs: object) -> object:
    """Create a mock RateLimitEvent."""
    msg = MagicMock(spec=RateLimitEvent)
    msg.__class__.__name__ = "RateLimitEvent"
    msg.session_id = session_id
    msg.uuid = "test-uuid"
    # Ensure all rate_limit_info attributes exist
    info = SimpleNamespace(
        status=kwargs.get("status"),
        rate_limit_type=kwargs.get("rate_limit_type"),
        resets_at=kwargs.get("resets_at"),
        utilization=kwargs.get("utilization"),
        overage_status=kwargs.get("overage_status"),
        overage_resets_at=kwargs.get("overage_resets_at"),
        overage_disabled_reason=kwargs.get("overage_disabled_reason"),
    )
    msg.rate_limit_info = info
    return msg


def _make_assistant_message(session_id: str, content: list, error: str | None = None) -> object:
    """Create a mock AssistantMessage."""
    msg = MagicMock(spec=AssistantMessage)
    msg.__class__.__name__ = "AssistantMessage"
    msg.session_id = session_id
    msg.content = content
    msg.error = error
    return msg


def _make_result_message(session_id: str, **kwargs: object) -> object:
    """Create a mock ResultMessage."""
    msg = MagicMock(spec=ResultMessage)
    msg.__class__.__name__ = "ResultMessage"
    msg.session_id = session_id
    msg.api_error_status = kwargs.get("api_error_status")
    msg.total_cost_usd = kwargs.get("total_cost_usd")
    msg.result = kwargs.get("result")
    msg.structured_output = kwargs.get("structured_output")
    msg.errors = kwargs.get("errors", [])
    return msg


def _make_text_block(text: str) -> object:
    """Create a mock TextBlock."""
    block = MagicMock(spec=TextBlock)
    block.text = text
    return block


def _make_thinking_block(thinking: str | None = None, text: str | None = None) -> object:
    """Create a mock ThinkingBlock."""
    block = MagicMock(spec=ThinkingBlock)
    if thinking is not None:
        block.thinking = thinking
    else:
        # getattr returns None if attribute doesn't exist
        block.thinking = None
    if text is not None:
        block.text = text
    else:
        block.text = None
    return block


def _make_tool_use_block(name: str, tool_id: str, input_data: dict) -> object:
    """Create a mock ToolUseBlock."""
    block = MagicMock(spec=ToolUseBlock)
    block.name = name
    block.id = tool_id
    block.input = input_data
    return block


def _make_tool_result_block(content: str, tool_use_id: str) -> object:
    """Create a mock ToolResultBlock."""
    block = MagicMock(spec=ToolResultBlock)
    block.content = content
    block.tool_use_id = tool_use_id
    return block


# Test properties
def test_thinking_text_property() -> None:
    acc = TurnAccumulator()
    msg = _make_assistant_message("s1", [_make_thinking_block(thinking="first")])
    acc.feed(msg)
    assert acc.thinking_text == "first"


def test_tool_events_property() -> None:
    acc = TurnAccumulator()
    msg = _make_assistant_message("s1", [_make_tool_use_block("tool1", "t1", {})])
    acc.feed(msg)
    events = acc.tool_events
    assert len(events) == 1
    assert events[0]["name"] == "tool1"


def test_on_event_callback() -> None:
    events: list = []
    acc = TurnAccumulator(on_event=lambda e: events.append(e))
    acc.feed(object())
    assert len(events) == 1


# Test StreamEvent
def test_feed_stream_event() -> None:
    acc = TurnAccumulator()
    msg = _make_stream_event("s1", {"type": "test"})
    acc.feed(msg)
    assert acc.build().session_id == "s1"


# Test RateLimitEvent
def test_feed_rate_limit_event() -> None:
    acc = TurnAccumulator()
    msg = _make_rate_limit_event(
        "s1",
        status="limited",
        rate_limit_type="five_hour",
        resets_at=1786328953,
        utilization=0.9,
        overage_status="active",
        overage_resets_at=1786329000,
        overage_disabled_reason="spend_limit",
    )
    acc.feed(msg)
    outcome = acc.build()
    assert outcome.signals.rate_limit_status == "limited"
    assert outcome.signals.utilization == 0.9


# Test AssistantMessage variants
def test_feed_assistant_with_text() -> None:
    acc = TurnAccumulator()
    msg = _make_assistant_message("s1", [_make_text_block("Hello")])
    acc.feed(msg)
    assert acc.build().output_text == "Hello"


def test_feed_assistant_with_error() -> None:
    acc = TurnAccumulator()
    msg = _make_assistant_message("s1", [], error="Oops")
    acc.feed(msg)
    assert acc.build().signals.assistant_error == "Oops"


def test_feed_assistant_with_thinking_text_fallback() -> None:
    acc = TurnAccumulator()
    msg = _make_assistant_message("s1", [_make_thinking_block(text="thought")])
    acc.feed(msg)
    assert "thought" in acc.thinking_text


def test_feed_assistant_with_thinking_block_neither_attr() -> None:
    """Cover branch where ThinkingBlock has neither 'thinking' nor 'text' attr."""
    acc = TurnAccumulator()
    block = MagicMock(spec=ThinkingBlock)
    # Both getattr calls return None
    block.thinking = None
    block.text = None
    msg = _make_assistant_message("s1", [block])
    acc.feed(msg)
    # Should not add to thinking_parts when both are None
    assert acc.thinking_text == ""


def test_feed_assistant_with_tool_result() -> None:
    acc = TurnAccumulator()
    msg = _make_assistant_message("s1", [_make_tool_result_block("data", "t1")])
    acc.feed(msg)
    events = acc.tool_events
    assert events[0]["name"] == "tool_result"
    assert events[0]["content"] == "data"


def test_feed_assistant_with_tool_result_and_text() -> None:
    """Cover loop continuation after ToolResultBlock (branch 105->91)."""
    acc = TurnAccumulator()
    msg = _make_assistant_message(
        "s1",
        [
            _make_tool_result_block("result", "t1"),
            _make_text_block("More text"),
        ],
    )
    acc.feed(msg)
    events = acc.tool_events
    assert len(events) == 1
    assert events[0]["name"] == "tool_result"
    assert acc.build().output_text == "More text"


# Test ResultMessage
def test_feed_result_message_basic() -> None:
    acc = TurnAccumulator()
    msg = _make_result_message("s1", api_error_status=429, total_cost_usd=1.5, result="Done")
    acc.feed(msg)
    outcome = acc.build()
    assert outcome.cost_usd == 1.5
    assert outcome.signals.api_error_status == 429


def test_feed_result_with_structured_output() -> None:
    acc = TurnAccumulator()
    structured = {
        "complete": True,
        "remaining_work": ["task"],
        "blocked_on": "creds",
        "summary": "OK",
    }
    msg = _make_result_message("s1", structured_output=structured)
    acc.feed(msg)
    verdict = acc.build().verdict
    assert verdict is not None
    assert verdict.complete is True
    assert verdict.blocked_on == "creds"


def test_feed_result_with_errors_list() -> None:
    acc = TurnAccumulator()
    msg = _make_result_message("s1", errors=["credits_required error"])
    acc.feed(msg)
    assert acc.build().signals.error_code == "credits_required"


def test_feed_result_with_out_of_credits_only() -> None:
    """Test out_of_credits without credits_required to cover line 133."""
    acc = TurnAccumulator()
    msg = _make_result_message("s1", errors=["Error: out_of_credits limit reached"])
    acc.feed(msg)
    outcome = acc.build()
    assert outcome.signals.disabled_reason == "out_of_credits"


def test_feed_result_with_error_details_camel() -> None:
    acc = TurnAccumulator()
    msg = _make_result_message("s1")
    msg.errorDetails = {"errorCode": "credits_required", "canUserPurchaseCredits": True}
    acc.feed(msg)
    outcome = acc.build()
    assert outcome.signals.error_code == "credits_required"
    assert outcome.signals.can_purchase is True


def test_feed_result_with_error_details_snake() -> None:
    acc = TurnAccumulator()
    msg = _make_result_message("s1")
    msg.error_details = {
        "error_code": "credits_required",
        "disabled_reason": "out_of_credits",
        "can_user_purchase_credits": False,
    }
    acc.feed(msg)
    outcome = acc.build()
    assert outcome.signals.error_code == "credits_required"
    assert outcome.signals.disabled_reason == "out_of_credits"
    assert outcome.signals.can_purchase is False


# Test credit scanning
def test_scan_nested_dict() -> None:
    acc = TurnAccumulator()
    acc._scan_credit_blob({"outer": {"error_code": "credits_required"}})
    assert acc._error_code == "credits_required"


def test_scan_list() -> None:
    acc = TurnAccumulator()
    acc._scan_credit_blob([{"disabled_reason": "out_of_credits"}])
    assert acc._disabled_reason == "out_of_credits"


def test_scan_json_string() -> None:
    acc = TurnAccumulator()
    acc._scan_credit_blob('{"error_code": "credits_required"}')
    assert acc._error_code == "credits_required"


def test_scan_string_with_keywords() -> None:
    acc = TurnAccumulator()
    acc._scan_credit_blob("Error: out_of_credits occurred")
    assert acc._disabled_reason == "out_of_credits"


def test_scan_invalid_json() -> None:
    acc = TurnAccumulator()
    acc._scan_credit_blob("not json {")  # Should not crash


# Test _stream_delta_text
def test_stream_delta_text_delta() -> None:
    result = _stream_delta_text({"type": "content_block_delta", "delta": {"text": "Hi"}})
    assert result == "Hi"


def test_stream_delta_thinking() -> None:
    result = _stream_delta_text({"type": "content_block_delta", "delta": {"thinking": "hmm"}})
    assert result == "hmm"


def test_stream_block_start() -> None:
    result = _stream_delta_text(
        {"type": "content_block_start", "content_block": {"type": "text", "text": "Start"}}
    )
    assert result == "Start"


def test_stream_delta_unknown() -> None:
    result = _stream_delta_text({"type": "unknown"})
    assert result is None


def test_stream_delta_text_delta_non_string_text() -> None:
    """Cover branch where delta.text exists but isn't a string."""
    result = _stream_delta_text({"type": "content_block_delta", "delta": {"text": 123}})
    assert result is None


def test_stream_delta_text_delta_non_string_thinking() -> None:
    """Cover branch where delta.thinking exists but isn't a string."""
    result = _stream_delta_text({"type": "content_block_delta", "delta": {"thinking": None}})
    assert result is None


def test_stream_delta_text_block_start_empty_text() -> None:
    """Cover branch where content_block.text is empty string."""
    result = _stream_delta_text(
        {"type": "content_block_start", "content_block": {"type": "text", "text": ""}}
    )
    assert result is None


def test_stream_delta_text_block_start_non_string() -> None:
    """Cover branch where content_block.text is not a string."""
    result = _stream_delta_text(
        {"type": "content_block_start", "content_block": {"type": "text", "text": None}}
    )
    assert result is None


def test_stream_delta_text_both_text_and_thinking_non_string() -> None:
    """Cover branch where both text and thinking are non-string, reaching line 229."""
    result = _stream_delta_text(
        {"type": "content_block_delta", "delta": {"text": None, "thinking": None}}
    )
    assert result is None


def test_stream_delta_text_content_block_non_text_type() -> None:
    """Cover branch where content_block is dict but type is not 'text'."""
    result = _stream_delta_text(
        {"type": "content_block_start", "content_block": {"type": "image", "url": "..."}}
    )
    assert result is None


def test_stream_delta_text_content_block_not_dict() -> None:
    """Cover branch where content_block is not a dict."""
    result = _stream_delta_text({"type": "content_block_start", "content_block": "string"})
    assert result is None


def test_stream_delta_fallthrough_to_content_block_start() -> None:
    """Cover branch 222->229: delta exists but both text/thinking are invalid,
    then check content_block_start."""
    # This event has type that would match content_block_delta first,
    # but delta has no valid text/thinking, so it should fall through
    # However, type is "mixed" not "content_block_start", so it returns None
    result = _stream_delta_text(
        {
            "type": "content_block_delta",
            "delta": {"other_field": "value"},  # delta exists but no text/thinking
        }
    )
    assert result is None


# Note: _message_to_event tests removed due to MagicMock.__class__.__name__ limitations
# The function is still covered through feed() tests which call _message_to_event internally


# Test build variants
def test_build_with_text_fallback() -> None:
    acc = TurnAccumulator()
    acc.feed(_make_assistant_message("s1", [_make_text_block("Fallback")]))
    assert acc.build().signals.result_text == "Fallback"


def test_build_with_none_remaining_work() -> None:
    acc = TurnAccumulator()
    msg = _make_result_message("s1", structured_output={"complete": False, "remaining_work": None})
    acc.feed(msg)
    assert acc.build().verdict.remaining_work == ()


def test_unrecognized_block_type_falls_through() -> None:
    """ServerToolUseBlock is not handled by if/elif chain → loop continues (105->91)."""
    from claude_agent_sdk import ServerToolUseBlock

    acc = TurnAccumulator()
    server_block = ServerToolUseBlock(id="st1", name="web_search", input={})
    text_block = TextBlock(text="after server tool")
    msg = AssistantMessage(
        session_id="s1",
        model="claude-sonnet",
        content=[server_block, text_block],
    )
    acc.feed(msg)
    outcome = acc.build()
    assert "after server tool" in outcome.output_text


def test_stream_delta_text_with_non_dict_delta() -> None:
    """content_block_delta where delta is not a dict → returns None (222->229)."""
    result = _stream_delta_text({"type": "content_block_delta", "delta": "not-a-dict"})
    assert result is None
