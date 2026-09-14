# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Tests for infrastructure/api/registry.py — command path registry."""

from __future__ import annotations

from claudeloop.infrastructure.api.registry import (
    REGISTERED_COMMAND_PATHS,
    clear_registry,
    register_command_path,
)


def test_register_and_clear() -> None:
    clear_registry()
    assert len(REGISTERED_COMMAND_PATHS) == 0
    register_command_path("messages.create")
    register_command_path("models.list")
    assert "messages.create" in REGISTERED_COMMAND_PATHS
    assert len(REGISTERED_COMMAND_PATHS) == 2
    clear_registry()
    assert len(REGISTERED_COMMAND_PATHS) == 0


def test_register_idempotent() -> None:
    clear_registry()
    register_command_path("messages.create")
    register_command_path("messages.create")
    assert len(REGISTERED_COMMAND_PATHS) == 1
    clear_registry()
