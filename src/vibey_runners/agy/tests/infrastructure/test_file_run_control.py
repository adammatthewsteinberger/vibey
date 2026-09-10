# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""File-based RunControl inbox under .agyloop/runs/<id>/inbox/."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from agyloop.domain.control import (
    ApproveToolCommand,
    DenyToolCommand,
    PromptDeferredCommand,
    PromptNowCommand,
    ResourceMutateCommand,
    ResponseFeedbackCommand,
    ResponseRetryCommand,
    SetCwdCommand,
    SetEffortCommand,
    SetModelCommand,
    SetPermissionModeCommand,
    SetPresetCommand,
    SlashCommand,
    StopCommand,
)
from agyloop.infrastructure.control import (
    FileRunControl,
    _command_to_payload,
    _payload_to_command,
)


def test_file_run_control_prompt_roundtrip(tmp_path: Path) -> None:
    control = FileRunControl(tmp_path / "inbox")
    control.enqueue(PromptNowCommand(text="hello"))
    assert control.poll() == [PromptNowCommand(text="hello")]
    assert control.poll() == []


def test_file_run_control_stop_outranks_prompt(tmp_path: Path) -> None:
    control = FileRunControl(tmp_path / "inbox")
    control.enqueue(PromptNowCommand(text="hello"))
    control.enqueue(StopCommand())
    assert control.poll() == [StopCommand()]


def test_file_run_control_model_and_preset_roundtrip(tmp_path: Path) -> None:
    control = FileRunControl(tmp_path / "inbox")
    control.enqueue(SetModelCommand(model="gemini-2.5-pro"))
    control.enqueue(SetPresetCommand(preset="high"))
    polled = control.poll()
    assert SetPresetCommand(preset="high") in polled
    assert SetModelCommand(model="gemini-2.5-pro") in polled


def test_all_control_command_roundtrips(tmp_path: Path) -> None:
    commands = [
        PromptNowCommand(text="now"),
        PromptDeferredCommand(text="later"),
        SetModelCommand(model="gemini-2.5-flash"),
        SetEffortCommand(effort="high"),
        SetPresetCommand(preset="medium"),
        SetPermissionModeCommand(mode="scoped"),
        SetCwdCommand(path="/tmp"),
        SlashCommand(text="/help"),
        ApproveToolCommand(request_id="req1"),
        DenyToolCommand(request_id="req2", reason="no"),
        ResourceMutateCommand(action="add", kind="attachment", value="/tmp/a", name="a"),
        ResponseFeedbackCommand(verdict="good", note="great work"),
        ResponseRetryCommand(),
    ]

    for cmd in commands:
        control = FileRunControl(tmp_path / f"inbox_{type(cmd).__name__}")
        control.enqueue(cmd)
        polled = control.poll()
        assert polled == [cmd]

    # Test deny_tool without reason default
    deny_default = _payload_to_command({"type": "deny_tool", "request_id": "req3"})
    assert isinstance(deny_default, DenyToolCommand)
    assert deny_default.reason == "denied by operator"

    # Test resource_mutate without name
    mutate_no_name = _payload_to_command(
        {"type": "resource_mutate", "action": "rm", "kind": "folder", "value": "/tmp"}
    )
    assert isinstance(mutate_no_name, ResourceMutateCommand)
    assert mutate_no_name.name is None

    # Test response_feedback without note
    fb_no_note = _payload_to_command({"type": "response_feedback", "verdict": "bad"})
    assert isinstance(fb_no_note, ResponseFeedbackCommand)
    assert fb_no_note.note == ""

    # Test unknown command type
    with pytest.raises(ValueError, match="unknown control command type"):
        _payload_to_command({"type": "unknown_cmd"})

    # Test unknown command in _command_to_payload
    class UnknownCommand:
        pass

    with pytest.raises(AssertionError):
        _command_to_payload(UnknownCommand())  # type: ignore[arg-type]


def test_file_run_control_ignores_corrupt_files(tmp_path: Path) -> None:
    inbox = tmp_path / "inbox"
    inbox.mkdir(parents=True)
    (inbox / "bad1.cmd.json").write_text("invalid json", encoding="utf-8")
    (inbox / "bad2.cmd.json").write_text(json.dumps({"type": "unknown"}), encoding="utf-8")

    control = FileRunControl(inbox)
    control.enqueue(PromptNowCommand(text="good"))

    polled = control.poll()
    assert polled == [PromptNowCommand(text="good")]
