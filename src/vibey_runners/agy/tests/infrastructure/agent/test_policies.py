# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Tests for agyloop.infrastructure.agent.policies."""

from __future__ import annotations

from unittest.mock import MagicMock

from google.antigravity.hooks.policy import Decision, Policy
from google.antigravity.utils.interactive import AskQuestionHook, ToolConfirmationHook

from agyloop.infrastructure.agent.policies import (
    _policies_of,
    config_has_allow_all,
    config_has_nonblocking_policies,
)


def test_policies_of_and_config_has_allow_all() -> None:
    from google.antigravity.hooks.policy import allow_all

    cfg = MagicMock()
    assert _policies_of(None) == []
    assert not config_has_allow_all(None)

    allow_policy = allow_all()
    cfg.policies = [allow_policy, "not_a_policy"]
    assert _policies_of(cfg) == [allow_policy]
    assert config_has_allow_all(cfg) is True


def test_config_has_nonblocking_policies_with_blocking_ask_user() -> None:
    cfg = MagicMock()
    # 1. Ask user without handler -> blocking
    p1 = Policy("ask_user_policy", when=lambda _: True, decision=Decision.ASK_USER, ask_user=None)
    cfg.policies = [p1]
    cfg.hooks = []
    assert config_has_nonblocking_policies(cfg) is False

    # 2. Ask user with interactive module handler -> blocking
    def mock_interactive_handler() -> None:
        pass

    mock_interactive_handler.__module__ = "google.antigravity.utils.interactive"
    p2 = Policy(
        "ask_user_interactive",
        when=lambda _: True,
        decision=Decision.ASK_USER,
        ask_user=mock_interactive_handler,
    )
    cfg.policies = [p2]
    assert config_has_nonblocking_policies(cfg) is False

    # 3. Ask user with custom non-interactive handler -> nonblocking
    def mock_custom_handler() -> None:
        pass

    mock_custom_handler.__module__ = "custom.module"
    p3 = Policy(
        "ask_user_custom",
        when=lambda _: True,
        decision=Decision.ASK_USER,
        ask_user=mock_custom_handler,
    )
    cfg.policies = [p3]
    assert config_has_nonblocking_policies(cfg) is True


def test_config_has_nonblocking_policies_with_interactive_hooks() -> None:
    cfg = MagicMock()
    cfg.policies = []
    cfg.hooks = [ToolConfirmationHook()]
    assert config_has_nonblocking_policies(cfg) is False

    cfg.hooks = [AskQuestionHook()]
    assert config_has_nonblocking_policies(cfg) is False

    class MockCustomHook:
        pass

    MockCustomHook.__module__ = "google.antigravity.utils.interactive.something"
    cfg.hooks = [MockCustomHook()]
    assert config_has_nonblocking_policies(cfg) is False
