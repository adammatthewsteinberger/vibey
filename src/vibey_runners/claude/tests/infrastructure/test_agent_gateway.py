# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Tests for infrastructure/agent/gateway.py — ClaudeAgentGateway + ClaudeCapacityProbe.

Uses mocked ClaudeSDKClient to test gateway logic without a live SDK connection.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from claudeloop.infrastructure.agent.gateway import (
    ClaudeAgentGateway,
    ClaudeCapacityProbe,
)


def _make_gateway(**kwargs):
    defaults = {"cwd": "/tmp/test"}
    defaults.update(kwargs)
    return ClaudeAgentGateway(**defaults)


class TestClaudeAgentGatewayInit:
    def test_defaults(self) -> None:
        gw = _make_gateway()
        assert gw._cwd == "/tmp/test"
        assert gw._client is None
        assert gw._session_id is None
        assert gw._resume is None
        assert gw._model is None
        assert gw._effort is None
        assert gw._add_dirs == []
        assert gw._plugins == []
        assert gw._mcp_servers == {}
        assert gw._allowed_tools == []
        assert gw._delta_seq == 0

    def test_with_all_params(self) -> None:
        gw = _make_gateway(
            session_id="s1",
            resume="r1",
            continue_conversation=True,
            max_turns=10,
            max_budget_usd=5.0,
            retry_watchdog=True,
            model="claude-sonnet",
            effort="high",
            on_event=lambda e: None,
            max_buffer_size=1024,
            include_partial_messages=True,
            add_dirs=["/a", "/b"],
            skills=["sk1"],
            plugins=["p1"],
            mcp_servers={"s": {"url": "http://x"}},
            system_prompt_append="extra",
            allowed_tools=["Bash"],
            tool_approval_timeout=60.0,
        )
        assert gw._session_id == "s1"
        assert gw._resume == "r1"
        assert gw._continue_conversation is True
        assert gw._max_turns == 10
        assert gw._model == "claude-sonnet"
        assert gw._effort == "high"
        assert gw._add_dirs == ["/a", "/b"]
        assert gw._plugins == ["p1"]
        assert gw._mcp_servers == {"s": {"url": "http://x"}}
        assert gw._allowed_tools == ["Bash"]


class TestSetEventListener:
    def test_set_listener(self) -> None:
        gw = _make_gateway()

        def fn(e):
            return None

        gw.set_event_listener(fn)
        assert gw._on_event is fn

    def test_set_none(self) -> None:
        gw = _make_gateway(on_event=lambda e: None)
        gw.set_event_listener(None)
        assert gw._on_event is None


class TestResolveToolApproval:
    def test_delegates_to_gate(self) -> None:
        gw = _make_gateway()
        result = gw.resolve_tool_approval("req-1", allow=True)
        assert isinstance(result, bool)


class TestSetProfile:
    @pytest.mark.asyncio
    async def test_no_op_when_same(self) -> None:
        gw = _make_gateway(model="claude-sonnet", effort="high")
        from claudeloop.domain.model_profile import ModelEffortProfile

        profile = ModelEffortProfile(model="claude-sonnet", effort="high")
        gw._client = MagicMock()
        await gw.set_profile(profile)
        # Client should still be set (not reconnected)
        assert gw._client is not None

    @pytest.mark.asyncio
    async def test_reconnects_when_changed(self) -> None:
        gw = _make_gateway(model="claude-sonnet", effort="high")
        from claudeloop.domain.model_profile import ModelEffortProfile

        profile = ModelEffortProfile(model="claude-opus", effort="max")
        mock_client = AsyncMock()
        gw._client = mock_client
        await gw.set_profile(profile)
        assert gw._model == "claude-opus"
        assert gw._effort == "max"
        mock_client.disconnect.assert_awaited_once()
        assert gw._client is None


class TestSetPermissionMode:
    @pytest.mark.asyncio
    async def test_no_op_when_same(self) -> None:
        gw = _make_gateway(permission_mode="bypass")
        gw._client = MagicMock()
        await gw.set_permission_mode("bypass")
        assert gw._client is not None

    @pytest.mark.asyncio
    async def test_reconnects_when_changed(self) -> None:
        gw = _make_gateway(permission_mode="bypass")
        mock_client = AsyncMock()
        gw._client = mock_client
        await gw.set_permission_mode("plan")
        mock_client.disconnect.assert_awaited_once()
        assert gw._client is None


class TestSetCwd:
    @pytest.mark.asyncio
    async def test_no_op_when_same(self) -> None:
        gw = _make_gateway(cwd="/tmp/test")
        gw._client = MagicMock()
        await gw.set_cwd("/tmp/test")
        assert gw._client is not None

    @pytest.mark.asyncio
    async def test_reconnects_when_changed(self) -> None:
        gw = _make_gateway(cwd="/tmp/test")
        mock_client = AsyncMock()
        gw._client = mock_client
        await gw.set_cwd("/tmp/other")
        assert gw._cwd == "/tmp/other"
        mock_client.disconnect.assert_awaited_once()
        assert gw._client is None


class TestSetSessionResources:
    @pytest.mark.asyncio
    async def test_no_change(self) -> None:
        gw = _make_gateway(add_dirs=["/a"], plugins=["p1"])
        gw._client = MagicMock()
        await gw.set_session_resources(add_dirs=["/a"], plugins=["p1"])
        # No reconnect if nothing changed
        assert gw._client is not None

    @pytest.mark.asyncio
    async def test_add_dirs_changed(self) -> None:
        gw = _make_gateway(add_dirs=["/a"])
        mock_client = AsyncMock()
        gw._client = mock_client
        await gw.set_session_resources(add_dirs=["/a", "/b"])
        assert gw._add_dirs == ["/a", "/b"]
        mock_client.disconnect.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_skills_changed(self) -> None:
        gw = _make_gateway(skills=["s1"])
        mock_client = AsyncMock()
        gw._client = mock_client
        await gw.set_session_resources(skills=["s1", "s2"])
        assert gw._skills == ["s1", "s2"]
        mock_client.disconnect.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_plugins_changed(self) -> None:
        gw = _make_gateway(plugins=["p1"])
        mock_client = AsyncMock()
        gw._client = mock_client
        await gw.set_session_resources(plugins=["p1", "p2"])
        assert gw._plugins == ["p1", "p2"]
        mock_client.disconnect.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_mcp_servers_changed(self) -> None:
        gw = _make_gateway()
        mock_client = AsyncMock()
        gw._client = mock_client
        await gw.set_session_resources(mcp_servers={"new": {"url": "http://x"}})
        assert gw._mcp_servers == {"new": {"url": "http://x"}}
        mock_client.disconnect.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_system_prompt_changed(self) -> None:
        gw = _make_gateway(system_prompt_append="old")
        mock_client = AsyncMock()
        gw._client = mock_client
        await gw.set_session_resources(system_prompt_append="new")
        assert gw._system_prompt_append == "new"
        mock_client.disconnect.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_allowed_tools_changed(self) -> None:
        gw = _make_gateway(allowed_tools=["Bash"])
        mock_client = AsyncMock()
        gw._client = mock_client
        await gw.set_session_resources(allowed_tools=["Bash", "Read"])
        assert gw._allowed_tools == ["Bash", "Read"]
        mock_client.disconnect.assert_awaited_once()


class TestReconnect:
    @pytest.mark.asyncio
    async def test_reconnect_with_session_id(self) -> None:
        gw = _make_gateway(session_id="s1")
        mock_client = AsyncMock()
        gw._client = mock_client
        await gw._reconnect()
        assert gw._resume == "s1"
        assert gw._continue_conversation is False
        mock_client.disconnect.assert_awaited_once()
        assert gw._client is None

    @pytest.mark.asyncio
    async def test_reconnect_without_session_id(self) -> None:
        gw = _make_gateway()
        mock_client = AsyncMock()
        gw._client = mock_client
        await gw._reconnect()
        assert gw._continue_conversation is True
        mock_client.disconnect.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_reconnect_no_client(self) -> None:
        gw = _make_gateway()
        await gw._reconnect()
        # No error when _client is None


class TestClose:
    @pytest.mark.asyncio
    async def test_close_with_client(self) -> None:
        gw = _make_gateway()
        mock_client = AsyncMock()
        gw._client = mock_client
        await gw.close()
        mock_client.disconnect.assert_awaited_once()
        assert gw._client is None

    @pytest.mark.asyncio
    async def test_close_without_client(self) -> None:
        gw = _make_gateway()
        await gw.close()


class TestSendTurn:
    @pytest.mark.asyncio
    async def test_send_turn_connects_and_returns_outcome(self) -> None:
        from claude_agent_sdk import ResultMessage

        gw = _make_gateway()
        mock_client = AsyncMock()

        result_msg = MagicMock(spec=ResultMessage)
        result_msg.cost_usd = 0.01
        result_msg.duration_ms = 1000
        result_msg.duration_api_ms = 800
        result_msg.is_error = False
        result_msg.session_id = "sess-123"
        result_msg.num_turns = 1
        result_msg.total_cost_usd = 0.01
        # translate.py falls back to message.result for the outcome text when
        # no TextBlock arrived; spec= restricts attributes but does not set
        # them, so an unset .result is a MagicMock, not a string.
        result_msg.result = "done"

        async def fake_receive():
            yield result_msg

        mock_client.receive_response = fake_receive
        mock_client.query = AsyncMock()
        mock_client.connect = AsyncMock()

        with patch(
            "claudeloop.infrastructure.agent.gateway.ClaudeSDKClient",
            return_value=mock_client,
        ):
            await gw.send_turn("hello")

        mock_client.connect.assert_awaited_once()
        mock_client.query.assert_awaited_once_with("hello")
        assert gw._session_id == "sess-123"

    @pytest.mark.asyncio
    async def test_send_turn_emits_delta_events_with_seq(self) -> None:
        """A StreamEvent whose payload carries delta_text is enriched with
        chatter='delta' and a monotonic seq before reaching the listener.

        Real SDK dataclass instances are used here (not MagicMock) because
        ``_message_to_event`` keys off ``type(message).__name__``, and a
        MagicMock's real type is always "MagicMock" regardless of ``spec=``
        — so a mocked message can never satisfy the gateway's
        ``event.get("type") == "StreamEvent"`` check.
        """
        from claude_agent_sdk import ResultMessage, StreamEvent

        gw = _make_gateway()
        events_received: list[dict[str, object]] = []
        gw._on_event = lambda e: events_received.append(e)

        stream_msg = StreamEvent(
            uuid="u1",
            session_id="sess-stream",
            event={"type": "content_block_delta", "delta": {"text": "hi"}},
        )
        result_msg = ResultMessage(
            subtype="success",
            duration_ms=1,
            duration_api_ms=1,
            is_error=False,
            num_turns=1,
            session_id="sess-stream",
            total_cost_usd=0.0,
            result="done",
        )

        mock_client = AsyncMock()

        async def fake_receive():
            yield stream_msg
            yield result_msg

        mock_client.receive_response = fake_receive
        mock_client.query = AsyncMock()
        mock_client.connect = AsyncMock()

        with patch(
            "claudeloop.infrastructure.agent.gateway.ClaudeSDKClient",
            return_value=mock_client,
        ):
            await gw.send_turn("hello")

        delta_events = [e for e in events_received if e.get("chatter") == "delta"]
        assert len(delta_events) == 1
        assert delta_events[0]["seq"] == 1
        assert delta_events[0]["delta_text"] == "hi"
        assert gw._delta_seq == 1

    @pytest.mark.asyncio
    async def test_send_turn_forwards_non_delta_events(self) -> None:
        """Events that aren't a StreamEvent-with-delta_text still reach the
        listener, just without the delta enrichment."""
        from claude_agent_sdk import ResultMessage

        gw = _make_gateway()
        events_received: list[dict[str, object]] = []
        gw._on_event = lambda e: events_received.append(e)

        result_msg = ResultMessage(
            subtype="success",
            duration_ms=1,
            duration_api_ms=1,
            is_error=False,
            num_turns=1,
            session_id="sess-plain",
            total_cost_usd=0.0,
            result="done",
        )

        mock_client = AsyncMock()

        async def fake_receive():
            yield result_msg

        mock_client.receive_response = fake_receive
        mock_client.query = AsyncMock()
        mock_client.connect = AsyncMock()

        with patch(
            "claudeloop.infrastructure.agent.gateway.ClaudeSDKClient",
            return_value=mock_client,
        ):
            await gw.send_turn("hello")

        assert len(events_received) == 1
        assert events_received[0]["type"] == "ResultMessage"
        assert events_received[0]["session_id"] == "sess-plain"

    @pytest.mark.asyncio
    async def test_send_turn_keeps_prior_session_id_when_outcome_has_none(self) -> None:
        """outcome.session_id falsy -> the gateway's existing _session_id
        (e.g. from a prior turn) must not be clobbered with None."""
        from claude_agent_sdk import ResultMessage

        gw = _make_gateway(session_id="preexisting")
        gw._resume = None
        gw._continue_conversation = False

        result_msg = ResultMessage(
            subtype="success",
            duration_ms=1,
            duration_api_ms=1,
            is_error=False,
            num_turns=1,
            session_id="",
            total_cost_usd=0.0,
            result="done",
        )

        mock_client = AsyncMock()

        async def fake_receive():
            yield result_msg

        mock_client.receive_response = fake_receive
        mock_client.query = AsyncMock()
        mock_client.connect = AsyncMock()

        with patch(
            "claudeloop.infrastructure.agent.gateway.ClaudeSDKClient",
            return_value=mock_client,
        ):
            await gw.send_turn("hello")

        assert gw._session_id == "preexisting"

    @pytest.mark.asyncio
    async def test_send_turn_drains_approval_events_mid_turn(self) -> None:
        """A tool.approval_needed event raised by can_use_tool() while a turn
        is streaming must reach the listener before the next message is fed,
        not just at connect time."""
        from claude_agent_sdk import ResultMessage

        gw = _make_gateway()
        events_received: list[dict[str, object]] = []
        gw._on_event = lambda e: events_received.append(e)
        gw._client = AsyncMock()  # already connected, so _ensure_connected does not
        # queue this event via its own (separate) drain at connect time.

        result_msg = ResultMessage(
            subtype="success",
            duration_ms=1,
            duration_api_ms=1,
            is_error=False,
            num_turns=1,
            session_id="sess-mid",
            total_cost_usd=0.0,
            result="done",
        )

        async def fake_receive():
            # Emulate can_use_tool() queuing an approval-needed event only
            # once the turn is already streaming — _ensure_connected's own
            # drain (called before this generator starts) must not be the
            # one that picks this up.
            gw._approval._events.append(
                {
                    "type": "tool.approval_needed",
                    "request_id": "req-mid",
                    "tool_name": "Bash",
                    "input_summary": "{}",
                    "timeout_seconds": 30.0,
                }
            )
            yield result_msg

        gw._client.receive_response = fake_receive
        gw._client.query = AsyncMock()

        await gw.send_turn("hello")

        approval_events = [e for e in events_received if e.get("type") == "tool.approval_needed"]
        assert len(approval_events) == 1
        assert approval_events[0]["request_id"] == "req-mid"


class TestEnsureConnected:
    @pytest.mark.asyncio
    async def test_drains_approval_events(self) -> None:
        gw = _make_gateway()
        events_received = []
        gw._on_event = lambda e: events_received.append(e)
        gw._approval.resolve("pre-1", allow=True)

        mock_client = AsyncMock()
        mock_client.connect = AsyncMock()
        with patch(
            "claudeloop.infrastructure.agent.gateway.ClaudeSDKClient",
            return_value=mock_client,
        ):
            client = await gw._ensure_connected()
        assert client is mock_client

    @pytest.mark.asyncio
    async def test_reuses_existing_client(self) -> None:
        gw = _make_gateway()
        mock_client = AsyncMock()
        gw._client = mock_client
        result = await gw._ensure_connected()
        assert result is mock_client

    @pytest.mark.asyncio
    async def test_flushes_pending_approval_needed_events_to_listener(self) -> None:
        """A tool.approval_needed event queued by can_use_tool (unlike
        resolve(), which never queues anything) must reach the listener the
        first time the gateway connects."""
        gw = _make_gateway()
        events_received: list[dict[str, object]] = []
        gw._on_event = lambda e: events_received.append(e)
        # Simulate a pending approval-needed event already queued in the gate,
        # as can_use_tool() would leave behind.
        gw._approval._events.append(
            {
                "type": "tool.approval_needed",
                "request_id": "req-1",
                "tool_name": "Bash",
                "input_summary": "{}",
                "timeout_seconds": 30.0,
            }
        )

        mock_client = AsyncMock()
        mock_client.connect = AsyncMock()
        with patch(
            "claudeloop.infrastructure.agent.gateway.ClaudeSDKClient",
            return_value=mock_client,
        ):
            await gw._ensure_connected()

        assert len(events_received) == 1
        assert events_received[0]["type"] == "tool.approval_needed"
        # Drained, not re-delivered on a later connect.
        assert gw._approval.drain_events() == []


class TestGatewayOnEventNonePartialBranches:
    """Cover partial branches where self._on_event is None."""

    @pytest.mark.asyncio
    async def test_ensure_connected_drains_without_listener(self) -> None:
        """Approval events drained in _ensure_connected with no listener (199->198)."""
        gw = _make_gateway()
        assert gw._on_event is None
        gw._approval._events.append({"type": "tool.approval_needed", "request_id": "r1"})
        mock_client = AsyncMock()
        mock_client.connect = AsyncMock()
        with patch(
            "claudeloop.infrastructure.agent.gateway.ClaudeSDKClient",
            return_value=mock_client,
        ):
            await gw._ensure_connected()
        assert gw._approval.drain_events() == []

    @pytest.mark.asyncio
    async def test_send_turn_no_listener_with_delta(self) -> None:
        """StreamEvent with delta_text but no listener → skip callback (237->239).
        Mid-turn approval drain also skipped (247->246)."""
        from claude_agent_sdk import ResultMessage, StreamEvent

        gw = _make_gateway()
        assert gw._on_event is None
        gw._client = AsyncMock()

        stream_msg = StreamEvent(
            uuid="u1",
            session_id="sess",
            event={"type": "content_block_delta", "delta": {"text": "hi"}},
        )
        result_msg = ResultMessage(
            subtype="success",
            duration_ms=1,
            duration_api_ms=1,
            is_error=False,
            num_turns=1,
            session_id="sess",
            total_cost_usd=0.0,
            result="done",
        )

        async def fake_receive():
            gw._approval._events.append({"type": "tool.approval_needed", "request_id": "mid"})
            yield stream_msg
            yield result_msg

        gw._client.receive_response = fake_receive
        gw._client.query = AsyncMock()

        await gw.send_turn("hello")
        assert gw._delta_seq == 1

    @pytest.mark.asyncio
    async def test_send_turn_stream_event_no_delta_text(self) -> None:
        """StreamEvent without delta_text falls through to outer dispatch (230->240)."""
        from claude_agent_sdk import ResultMessage, StreamEvent

        gw = _make_gateway()
        events_received: list[dict[str, object]] = []
        gw._on_event = lambda e: events_received.append(e)
        gw._client = AsyncMock()

        stream_msg = StreamEvent(
            uuid="u1",
            session_id="sess",
            event={"type": "message_start"},
        )
        result_msg = ResultMessage(
            subtype="success",
            duration_ms=1,
            duration_api_ms=1,
            is_error=False,
            num_turns=1,
            session_id="sess",
            total_cost_usd=0.0,
            result="done",
        )

        async def fake_receive():
            yield stream_msg
            yield result_msg

        gw._client.receive_response = fake_receive
        gw._client.query = AsyncMock()

        await gw.send_turn("hello")
        stream_events = [e for e in events_received if e.get("type") == "StreamEvent"]
        assert len(stream_events) >= 1


class TestClaudeCapacityProbe:
    def test_init(self) -> None:
        probe = ClaudeCapacityProbe(cwd="/tmp/test")
        assert probe._cwd == "/tmp/test"
        assert probe._model is None

    def test_set_model(self) -> None:
        probe = ClaudeCapacityProbe(cwd="/tmp/test")
        probe.set_model("claude-sonnet")
        assert probe._model == "claude-sonnet"

    @pytest.mark.asyncio
    async def test_probe_connects_queries_disconnects(self) -> None:
        from claude_agent_sdk import ResultMessage

        probe = ClaudeCapacityProbe(cwd="/tmp/test", model="claude-sonnet")

        result_msg = MagicMock(spec=ResultMessage)
        result_msg.cost_usd = 0.001
        result_msg.duration_ms = 500
        result_msg.duration_api_ms = 400
        result_msg.is_error = False
        result_msg.session_id = "probe-sess"
        result_msg.num_turns = 1
        result_msg.total_cost_usd = 0.001
        result_msg.result = "probe done"

        mock_client = AsyncMock()

        async def fake_receive():
            yield result_msg

        mock_client.receive_response = fake_receive
        mock_client.query = AsyncMock()
        mock_client.connect = AsyncMock()
        mock_client.disconnect = AsyncMock()

        with patch(
            "claudeloop.infrastructure.agent.gateway.ClaudeSDKClient",
            return_value=mock_client,
        ):
            await probe.probe()

        mock_client.connect.assert_awaited_once()
        mock_client.query.assert_awaited_once()
        mock_client.disconnect.assert_awaited_once()
