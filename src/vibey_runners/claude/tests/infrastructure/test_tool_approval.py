# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Tests for infrastructure/tool_approval.py — ToolApprovalGate."""

from __future__ import annotations

import asyncio

import pytest
from claude_agent_sdk.types import (
    PermissionResultAllow,
    PermissionResultDeny,
    ToolPermissionContext,
)

from claudeloop.infrastructure.tool_approval import (
    ToolApprovalGate,
    _summarize_input,
)


def _context() -> ToolPermissionContext:
    # tool_name/tool_input are separate positional args to can_use_tool();
    # ToolPermissionContext itself carries only request metadata (signal,
    # tool_use_id, etc.), none of it required here.
    return ToolPermissionContext()


class TestSummarizeInput:
    def test_short_input(self) -> None:
        result = _summarize_input({"key": "value"})
        assert result == "{'key': 'value'}"

    def test_long_input_truncated(self) -> None:
        data = {"key": "x" * 300}
        result = _summarize_input(data)
        assert len(result) == 200
        assert result.endswith("...")


class TestToolApprovalGate:
    def test_resolve_pre_decision(self) -> None:
        gate = ToolApprovalGate(timeout_seconds=1.0)
        result = gate.resolve("req-1", allow=True)
        assert result is True

    def test_drain_events_initially_empty(self) -> None:
        gate = ToolApprovalGate()
        assert gate.drain_events() == []

    @pytest.mark.asyncio
    async def test_can_use_tool_approved(self) -> None:
        gate = ToolApprovalGate(timeout_seconds=5.0)
        gate.resolve("will-be-overridden", allow=True)

        async def approve_after_short_delay():
            await asyncio.sleep(0.05)
            events = gate.drain_events()
            assert len(events) >= 1
            req_id = events[0]["request_id"]
            gate.resolve(req_id, allow=True)

        task = asyncio.create_task(approve_after_short_delay())
        result = await gate.can_use_tool("test", {"cmd": "echo"}, _context())
        await task
        assert isinstance(result, PermissionResultAllow)

    @pytest.mark.asyncio
    async def test_can_use_tool_denied(self) -> None:
        gate = ToolApprovalGate(timeout_seconds=5.0)

        async def deny_after_short_delay():
            await asyncio.sleep(0.05)
            events = gate.drain_events()
            req_id = events[0]["request_id"]
            gate.resolve(req_id, allow=False, reason="not allowed")

        task = asyncio.create_task(deny_after_short_delay())
        result = await gate.can_use_tool("test", {}, _context())
        await task
        assert isinstance(result, PermissionResultDeny)
        assert "not allowed" in result.message

    @pytest.mark.asyncio
    async def test_can_use_tool_timeout(self) -> None:
        gate = ToolApprovalGate(timeout_seconds=0.2)
        result = await gate.can_use_tool("slow_tool", {}, _context())
        assert isinstance(result, PermissionResultDeny)
        assert "timed out" in result.message
        events = gate.drain_events()
        assert any(e["type"] == "tool.approval_timeout" for e in events)

    @pytest.mark.asyncio
    async def test_pre_resolved_decision_picked_up(self) -> None:
        gate = ToolApprovalGate(timeout_seconds=5.0)

        async def pre_approve():
            await asyncio.sleep(0.02)
            events = gate.drain_events()
            req_id = events[0]["request_id"]
            gate.resolve(req_id, allow=True)

        task = asyncio.create_task(pre_approve())
        result = await gate.can_use_tool("tool", {}, _context())
        await task
        assert isinstance(result, PermissionResultAllow)

    def test_resolve_deny_with_empty_reason(self) -> None:
        gate = ToolApprovalGate()
        gate.resolve("r1", allow=False)
