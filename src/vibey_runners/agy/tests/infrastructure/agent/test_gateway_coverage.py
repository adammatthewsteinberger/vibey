# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

from agyloop.domain.model_profile import ModelEffortProfile
from agyloop.infrastructure.agent.gateway import (
    AntigravityAgentGateway,
    _usage_tokens,
)


def test_usage_tokens_variants() -> None:
    assert _usage_tokens(None, "prompt") == 0
    assert _usage_tokens(object(), "prompt") == 0

    # usage as object with prompt_tokens
    class UsageObj:
        prompt_tokens = 10
        candidates_token_count = 20

    class RespObj:
        usage_metadata = UsageObj()

    assert _usage_tokens(RespObj(), "prompt") == 10
    assert _usage_tokens(RespObj(), "completion") == 20

    # usage as dict
    class RespDict:
        usage = {"input_tokens": 15, "output_tokens": 25}

    assert _usage_tokens(RespDict(), "prompt") == 15
    assert _usage_tokens(RespDict(), "completion") == 25


async def test_gateway_methods_and_reconnect() -> None:
    events = []
    gateway = AntigravityAgentGateway(
        cwd="/tmp/dir1",
        model="gemini-2.5-flash",
        add_dirs=["/tmp/extra"],
        system_prompt_append="extra prompt",
        on_event=lambda e: events.append(e),
    )

    assert gateway.resolve_tool_approval("req1", allow=True) is False

    # Every mutator reconnects through _reconnect, which tears the session down
    # only when one is live. Without this the assertions below would pass for
    # the wrong reason -- close() is never reached on a gateway that never
    # connected, so "did not reconnect" and "had nothing to reconnect" look
    # identical. close is patched throughout, so the sentinel survives.
    gateway._agent = object()

    # set_profile: same model (no reconnect) vs new model (reconnect)
    await gateway.set_profile(ModelEffortProfile(model="gemini-2.5-flash", effort="high"))
    with patch.object(gateway, "close", new_callable=AsyncMock) as mock_close:
        await gateway.set_profile(ModelEffortProfile(model="gemini-2.5-pro", effort="high"))
        assert mock_close.called

    # set_permission_mode: same mode vs new mode
    with patch.object(gateway, "close", new_callable=AsyncMock) as mock_close:
        await gateway.set_permission_mode("autonomous")
        assert not mock_close.called
        await gateway.set_permission_mode("scoped")
        assert mock_close.called

    # set_cwd: same cwd vs new cwd
    with patch.object(gateway, "close", new_callable=AsyncMock) as mock_close:
        await gateway.set_cwd("/tmp/dir1")
        assert not mock_close.called
        await gateway.set_cwd("/tmp/dir2")
        assert mock_close.called

    # set_session_resources: no changes vs changes
    with patch.object(gateway, "close", new_callable=AsyncMock) as mock_close:
        await gateway.set_session_resources(
            add_dirs=["/tmp/extra"], system_prompt_append="extra prompt"
        )
        assert not mock_close.called
        await gateway.set_session_resources(add_dirs=["/tmp/new_extra"])
        assert mock_close.called
        mock_close.reset_mock()
        await gateway.set_session_resources(system_prompt_append="new prompt")
        assert mock_close.called


async def test_gateway_send_turn_returns_response_text_and_emits_one_event() -> None:
    mock_agent = MagicMock()
    mock_agent.conversation_id = "c123"
    mock_response = MagicMock()
    mock_response.text = AsyncMock(return_value="the model reply")
    mock_response.structured_output = AsyncMock(return_value=None)
    mock_response.usage_metadata = None
    mock_agent.chat = AsyncMock(return_value=mock_response)

    events = []
    gateway = AntigravityAgentGateway(
        cwd="/tmp/dir1",
        on_event=lambda e: events.append(e),
    )

    with patch("agyloop.infrastructure.agent.gateway.Agent") as mock_agent_cls:
        mock_agent_instance = AsyncMock()
        mock_agent_instance.__aenter__.return_value = mock_agent
        mock_agent_cls.return_value = mock_agent_instance

        outcome = await gateway.send_turn("do something")
        # The reply text lands on outcome.output_text. signals carries the capacity
        # evidence (status, quota, retry) that classify() reads, and a clean
        # turn leaves all of it unset -- an empty signals set is what makes a
        # turn classify as Available rather than as an exhaustion.
        assert outcome.output_text == "the model reply"
        assert outcome.signals.message is None
        assert outcome.signals.http_status is None
        assert len(events) == 1
        assert events[0]["event"] == "turn_complete"
        assert events[0]["session_id"] == "c123"


async def test_gateway_send_turn_operator_cancel_detected() -> None:
    mock_agent = MagicMock()
    mock_agent.conversation_id = None
    mock_agent.is_started = True
    mock_response = MagicMock()
    mock_response.text = AsyncMock(return_value="context canceled")
    mock_response.structured_output = AsyncMock(return_value=None)
    mock_response.usage_metadata = None
    mock_agent.chat = AsyncMock(return_value=mock_response)

    gateway = AntigravityAgentGateway(cwd="/tmp/dir1")
    with patch("agyloop.infrastructure.agent.gateway.Agent") as mock_agent_cls:
        mock_agent_instance = AsyncMock()
        mock_agent_instance.__aenter__.return_value = mock_agent
        mock_agent_cls.return_value = mock_agent_instance

        # First turn: operator cancel in output text
        outcome1 = await gateway.send_turn("turn 1")
        assert outcome1.signals.message == "context canceled"

        # Second turn: reuses already started agent without calling __aenter__ again
        mock_response.text = AsyncMock(return_value="normal turn 2")
        outcome2 = await gateway.send_turn("turn 2")
        assert outcome2.output_text == "normal turn 2"
        assert mock_agent_instance.__aenter__.call_count == 1

        await gateway.close()


async def test_gateway_empty_plan_seed_and_agent_none_error() -> None:
    gateway = AntigravityAgentGateway(cwd="/tmp/dir1", plan_seed="")
    assert gateway._seeded_prompt("my prompt") == "my prompt"


async def test_ensure_started_restarts_an_agent_the_harness_dropped() -> None:
    """The SDK can mark an agent not-started out from under us (harness crash,
    dropped socket). Reusing it would send a turn nothing is listening on, so
    `_ensure_started` has to notice and reconnect instead of trusting the
    cached reference."""
    stale_agent = MagicMock()
    stale_agent.is_started = False

    gateway = AntigravityAgentGateway(cwd="/tmp/dir1")
    gateway._agent = stale_agent

    with (
        patch.object(gateway, "close", new_callable=AsyncMock) as mock_close,
        patch("agyloop.infrastructure.agent.gateway.Agent") as mock_agent_cls,
    ):
        fresh_agent = MagicMock()
        mock_agent_instance = AsyncMock()
        mock_agent_instance.__aenter__.return_value = fresh_agent
        mock_agent_cls.return_value = mock_agent_instance

        # close() is mocked, so it won't actually clear _agent -- clear it the
        # way the real close() does, so _ensure_started reconnects.
        async def _clear_agent() -> None:
            gateway._agent = None

        mock_close.side_effect = _clear_agent

        result = await gateway._ensure_started()

    mock_close.assert_awaited_once()
    assert result is fresh_agent


async def test_send_turn_normalizes_transport_errors_to_connection_error() -> None:
    """A dropped socket surfaces as ConnectionResetError/BrokenPipeError/EOFError
    (or websockets' ConnectionClosed) depending on which layer notices first.
    All four have to collapse onto AntigravityConnectionError so classify()
    sees one capacity-adjacent signal instead of four vendor-specific ones."""
    mock_agent = MagicMock()
    mock_agent.conversation_id = None
    mock_agent.is_started = True
    mock_agent.chat = AsyncMock(side_effect=ConnectionResetError("peer reset"))

    gateway = AntigravityAgentGateway(cwd="/tmp/dir1")
    with patch("agyloop.infrastructure.agent.gateway.Agent") as mock_agent_cls:
        mock_agent_instance = AsyncMock()
        mock_agent_instance.__aenter__.return_value = mock_agent
        mock_agent_cls.return_value = mock_agent_instance

        outcome = await gateway.send_turn("do something")

    assert outcome.signals.exception_type == "AntigravityConnectionError"
    assert "peer reset" in (outcome.signals.exception_message or "")


def test_connection_closed_falls_back_to_a_local_shim_without_websockets() -> None:
    """`websockets` is an optional dependency of the SDK's transport, not of
    agyloop directly. If it is absent, the module must still import and the
    shim it builds must still satisfy `isinstance(exc, ConnectionClosed)` in
    `send_turn`'s except clause -- otherwise a transport drop on a host
    without websockets installed would propagate as an unhandled exception."""
    import importlib
    import sys

    real_websockets = sys.modules.pop("websockets", None)
    real_websockets_exceptions = sys.modules.pop("websockets.exceptions", None)
    sys.modules["websockets"] = None  # type: ignore[assignment]
    sys.modules["websockets.exceptions"] = None  # type: ignore[assignment]
    try:
        module = importlib.reload(importlib.import_module("agyloop.infrastructure.agent.gateway"))
        assert issubclass(module.ConnectionClosed, Exception)
        assert module.ConnectionClosed.__name__ == "ConnectionClosed"
    finally:
        del sys.modules["websockets"]
        del sys.modules["websockets.exceptions"]
        if real_websockets is not None:
            sys.modules["websockets"] = real_websockets
        if real_websockets_exceptions is not None:
            sys.modules["websockets.exceptions"] = real_websockets_exceptions
        importlib.reload(importlib.import_module("agyloop.infrastructure.agent.gateway"))
