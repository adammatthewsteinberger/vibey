# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
from __future__ import annotations

import pytest

from claudeloop.domain.control import (
    ApproveToolCommand,
    DenyToolCommand,
    PromptDeferredCommand,
    PromptNowCommand,
    ResourceMutateCommand,
    ResponseFeedbackCommand,
    SetCwdCommand,
    SetEffortCommand,
    SetModelCommand,
    SetPresetCommand,
    StopCommand,
    stop_outranks,
)


def test_stop_alone() -> None:
    assert stop_outranks([StopCommand()]) == [StopCommand()]


def test_latest_prompt_now_wins() -> None:
    result = stop_outranks([PromptNowCommand(text="a"), PromptNowCommand(text="b")])
    assert result == [PromptNowCommand(text="b")]


def test_now_and_deferred_both_kept() -> None:
    result = stop_outranks([PromptDeferredCommand(text="d"), PromptNowCommand(text="n")])
    assert result == [PromptNowCommand(text="n"), PromptDeferredCommand(text="d")]


def test_empty_batch() -> None:
    assert stop_outranks([]) == []


def test_blank_prompts_rejected() -> None:
    with pytest.raises(ValueError):
        PromptNowCommand(text="")
    with pytest.raises(ValueError):
        PromptDeferredCommand(text="   ")


def test_blank_model_rejected() -> None:
    with pytest.raises(ValueError):
        SetModelCommand(model="  ")


def test_profile_commands_latest_wins() -> None:
    result = stop_outranks(
        [
            SetPresetCommand(preset="low"),
            SetPresetCommand(preset="high"),
            SetModelCommand(model="medium"),
            SetEffortCommand(effort="max"),
        ]
    )
    assert result == [
        SetPresetCommand(preset="high"),
        SetModelCommand(model="medium"),
        SetEffortCommand(effort="max"),
    ]


def test_set_cwd_rejects_blank_path() -> None:
    assert SetCwdCommand(path="/tmp/x").path == "/tmp/x"
    with pytest.raises(ValueError, match="cwd path must not be blank"):
        SetCwdCommand(path="   ")


def test_approve_tool_rejects_blank_request_id() -> None:
    assert ApproveToolCommand(request_id="req-1").request_id == "req-1"
    with pytest.raises(ValueError, match="request_id must not be blank"):
        ApproveToolCommand(request_id="")


def test_deny_tool_rejects_blank_request_id() -> None:
    cmd = DenyToolCommand(request_id="req-1")
    assert cmd.reason == "denied by operator"
    with pytest.raises(ValueError, match="request_id must not be blank"):
        DenyToolCommand(request_id="  ")


class TestResourceMutateCommand:
    def test_valid_add(self) -> None:
        cmd = ResourceMutateCommand(action="add", kind="skill", value="research")
        assert cmd.name is None

    def test_rejects_invalid_action(self) -> None:
        with pytest.raises(ValueError, match="invalid resource action"):
            ResourceMutateCommand(action="delete", kind="skill", value="x")

    def test_rejects_blank_kind(self) -> None:
        with pytest.raises(ValueError, match="resource kind must not be blank"):
            ResourceMutateCommand(action="add", kind="  ", value="x")

    def test_rejects_blank_value_unless_removing(self) -> None:
        with pytest.raises(ValueError, match="resource value must not be blank"):
            ResourceMutateCommand(action="add", kind="skill", value="")

    def test_blank_value_allowed_for_remove(self) -> None:
        cmd = ResourceMutateCommand(action="rm", kind="skill", value="")
        assert cmd.value == ""


class TestResponseFeedbackCommand:
    def test_valid_verdicts(self) -> None:
        assert ResponseFeedbackCommand(verdict="good").note == ""
        assert ResponseFeedbackCommand(verdict="bad", note="too slow").note == "too slow"

    def test_rejects_invalid_verdict(self) -> None:
        with pytest.raises(ValueError, match="verdict must be good or bad"):
            ResponseFeedbackCommand(verdict="meh")
