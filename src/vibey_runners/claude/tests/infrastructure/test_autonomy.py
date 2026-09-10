# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Tests for infrastructure/agent/autonomy.py — never-block-on-human hooks."""

from __future__ import annotations

import pytest

from claudeloop.infrastructure.agent.autonomy import (
    AUTONOMY_SYSTEM_PROMPT_FRAGMENT,
    _auto_allow_permission_request,
    _deny_ask_user_question,
    _log_notification,
    build_hooks,
)


class TestConstants:
    def test_autonomy_prompt_fragment_is_nonempty(self) -> None:
        assert len(AUTONOMY_SYSTEM_PROMPT_FRAGMENT) > 50
        assert "autonomously" in AUTONOMY_SYSTEM_PROMPT_FRAGMENT


class TestDenyAskUserQuestion:
    @pytest.mark.asyncio
    async def test_non_ask_tool_returns_empty(self) -> None:
        result = await _deny_ask_user_question(
            {"tool_name": "Bash"},
            None,
            {},
        )
        assert result == {}

    @pytest.mark.asyncio
    async def test_ask_user_question_returns_deny(self) -> None:
        result = await _deny_ask_user_question(
            {"tool_name": "AskUserQuestion"},
            None,
            {},
        )
        assert result["hookSpecificOutput"]["permissionDecision"] == "deny"
        assert "autonomously" in result["hookSpecificOutput"]["permissionDecisionReason"]


class TestAutoAllowPermissionRequest:
    @pytest.mark.asyncio
    async def test_returns_empty(self) -> None:
        result = await _auto_allow_permission_request({}, None, {})
        assert result == {}


class TestLogNotification:
    @pytest.mark.asyncio
    async def test_returns_empty(self) -> None:
        result = await _log_notification({"message": "hello"}, None, {})
        assert result == {}


class TestBuildHooks:
    def test_hook_structure(self) -> None:
        hooks = build_hooks()
        assert "PreToolUse" in hooks
        assert "PermissionRequest" in hooks
        assert "Notification" in hooks
        assert len(hooks["PreToolUse"]) == 1
        assert hooks["PreToolUse"][0].matcher == "AskUserQuestion"
