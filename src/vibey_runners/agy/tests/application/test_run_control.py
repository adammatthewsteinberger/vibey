# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Operator enqueue use cases — stop and prompt only (M4 polish)."""

from __future__ import annotations

from agyloop.application.usecases.run_control import request_prompt, request_stop
from agyloop.domain.control import PromptDeferredCommand, PromptNowCommand, StopCommand


class _FakeInbox:
    def __init__(self) -> None:
        self.commands: list[object] = []

    def enqueue(self, command: object) -> None:
        self.commands.append(command)


def test_request_stop_enqueues_stop_command() -> None:
    inbox = _FakeInbox()
    result = request_stop(inbox, run_id="run-1")
    assert result.run_id == "run-1"
    assert result.command_type == "stop"
    assert inbox.commands == [StopCommand()]


def test_request_prompt_now_enqueues_prompt_now() -> None:
    inbox = _FakeInbox()
    result = request_prompt(inbox, "hello", immediate=True, run_id="run-2")
    assert result.command_type == "prompt_now"
    assert inbox.commands == [PromptNowCommand(text="hello")]


def test_request_prompt_at_break_enqueues_deferred() -> None:
    inbox = _FakeInbox()
    result = request_prompt(inbox, "later", immediate=False, run_id="run-3")
    assert result.command_type == "prompt_deferred"
    assert inbox.commands == [PromptDeferredCommand(text="later")]
