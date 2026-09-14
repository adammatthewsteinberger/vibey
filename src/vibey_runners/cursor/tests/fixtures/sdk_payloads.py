# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Synthetic Cursor SDK payload builders for translate tests.

Each builder is **synthetic**, derived from documented dataclass shapes, and
must be replaced by a real captured payload the first time one is observed
in the wild.

Documented exception root is ``CursorAgentError`` (``message``, ``code``,
``status_code``, ``is_retryable``, ``proto_error_code``, ``request_id``,
``retry_after``). Run statuses: running | finished | error | cancelled |
expired. ``messages()``, ``events()``, and ``iter_text()`` share one stream.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator, Sequence
from dataclasses import dataclass, field
from typing import Any


class CursorAgentError(Exception):
    """Synthetic stand-in for documented ``cursor_sdk.errors.CursorAgentError``."""


class RateLimitError(CursorAgentError):
    """Synthetic stand-in for documented ``RateLimitError``."""


class NetworkError(CursorAgentError):
    """Synthetic stand-in for documented ``NetworkError``."""


@dataclass(frozen=True, slots=True)
class FakeTextBlock:
    """Synthetic: documented ``TextBlock`` shape (``type``, ``text``)."""

    text: str
    type: str = "text"


@dataclass(frozen=True, slots=True)
class FakeAssistantContent:
    """Synthetic: documented ``SDKAssistantMessageContent`` shape."""

    content: tuple[FakeTextBlock, ...] = ()
    role: str = "assistant"


@dataclass(frozen=True, slots=True)
class FakeAssistantMessage:
    """Synthetic: documented ``SDKAssistantMessage`` (``type == "assistant"``)."""

    message: FakeAssistantContent
    type: str = "assistant"
    agent_id: str = "agent_1"
    run_id: str = "run_1"


@dataclass(frozen=True, slots=True)
class FakeToolCallMessage:
    """Synthetic: documented ``SDKToolUseMessage`` (``type == "tool_call"``)."""

    name: str
    call_id: str = "call_1"
    status: str = "completed"
    args: dict[str, Any] | None = None
    result: Any = None
    type: str = "tool_call"
    agent_id: str = "agent_1"
    run_id: str = "run_1"


@dataclass(frozen=True, slots=True)
class FakeStatusMessage:
    """Synthetic: documented ``SDKStatusMessage`` (``type == "status"``)."""

    status: str
    message: str = ""
    type: str = "status"
    agent_id: str = "agent_1"
    run_id: str = "run_1"


@dataclass(frozen=True, slots=True)
class FakeUsageMessage:
    """Synthetic: documented ``SDKUsageMessage`` (``type == "usage"``)."""

    usage: FakeTokenUsage
    type: str = "usage"
    agent_id: str = "agent_1"
    run_id: str = "run_1"


@dataclass(frozen=True, slots=True)
class FakeTokenUsage:
    """Synthetic: documented ``TokenUsage`` shape."""

    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0
    total_tokens: int = 0
    reasoning_tokens: int | None = None


@dataclass
class FakeRun:
    """Synthetic: documented ``Run`` handle (status, result, usage, one-shot stream)."""

    status: str = "finished"
    result: str = ""
    usage: FakeTokenUsage | None = None
    id: str = "run_1"
    agent_id: str = "agent_1"
    consume_count: int = 0
    wait_count: int = 0
    _messages: tuple[object, ...] = field(default_factory=tuple)

    def messages(self) -> Iterator[object]:
        self.consume_count += 1
        yield from self._messages

    def wait(self) -> FakeRun:
        self.wait_count += 1
        return self


def fake_rate_limit_error(
    *,
    code: str | None = None,
    is_retryable: bool | None = None,
    retry_after: str | None = None,
    request_id: str | None = None,
    message: str = "rate limited",
    status_code: int | None = None,
    proto_error_code: str | None = None,
) -> RateLimitError:
    # Synthetic: derived from documented CursorAgentError field shapes.
    # Replace with a real captured payload the first time one is observed in the wild.
    exc = RateLimitError(message)
    exc.message = message
    exc.code = code
    exc.is_retryable = is_retryable
    exc.retry_after = retry_after
    exc.request_id = request_id
    exc.status_code = status_code
    exc.proto_error_code = proto_error_code
    return exc


def fake_network_error(
    *,
    request_id: str | None = None,
    message: str = "network failed",
    is_retryable: bool = True,
) -> NetworkError:
    # Synthetic: derived from documented CursorAgentError field shapes.
    # Replace with a real captured payload the first time one is observed in the wild.
    exc = NetworkError(message)
    exc.message = message
    exc.request_id = request_id
    exc.is_retryable = is_retryable
    return exc


def fake_run(
    *,
    status: str,
    result: str = "",
    total_tokens: int | None = None,
    run_id: str = "run_1",
    agent_id: str = "agent_1",
    messages: Sequence[object] = (),
) -> FakeRun:
    # Synthetic: derived from documented Run dataclass shapes.
    # Replace with a real captured payload the first time one is observed in the wild.
    usage = None if total_tokens is None else FakeTokenUsage(total_tokens=total_tokens)
    return FakeRun(
        status=status,
        result=result,
        usage=usage,
        id=run_id,
        agent_id=agent_id,
        _messages=tuple(messages),
    )


def fake_streaming_run(chunks: Iterable[str]) -> FakeRun:
    # Synthetic: derived from documented SDKAssistantMessage / Run stream shapes.
    # Replace with a real captured payload the first time one is observed in the wild.
    parts = tuple(chunks)
    messages = tuple(_assistant_message(chunk) for chunk in parts)
    return FakeRun(
        status="finished",
        result="".join(parts),
        _messages=messages,
    )


def fake_tool_call_message(
    *,
    name: str = "read",
    call_id: str = "call_1",
    status: str = "completed",
) -> FakeToolCallMessage:
    # Synthetic: derived from documented SDKToolUseMessage dataclass shapes.
    # Replace with a real captured payload the first time one is observed in the wild.
    return FakeToolCallMessage(name=name, call_id=call_id, status=status, args={})


def fake_status_message(*, status: str = "running", message: str = "working") -> FakeStatusMessage:
    # Synthetic: derived from documented SDKStatusMessage dataclass shapes.
    # Replace with a real captured payload the first time one is observed in the wild.
    return FakeStatusMessage(status=status, message=message)


def fake_usage_message(*, total_tokens: int = 9) -> FakeUsageMessage:
    # Synthetic: derived from documented SDKUsageMessage / TokenUsage shapes.
    # Replace with a real captured payload the first time one is observed in the wild.
    return FakeUsageMessage(usage=FakeTokenUsage(total_tokens=total_tokens))


def fake_model_catalog(ids: Sequence[str]) -> list[str]:
    """Synthetic live catalog of model ids. The catalog, not a constant, is
    the source of truth — Cursor ships models faster than we ship releases."""
    return list(ids)


def _assistant_message(text: str) -> FakeAssistantMessage:
    return FakeAssistantMessage(message=FakeAssistantContent(content=(FakeTextBlock(text=text),)))
