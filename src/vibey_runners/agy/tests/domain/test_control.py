# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
from __future__ import annotations

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
    stop_outranks,
)
from agyloop.domain.permission import (
    DEFAULT_USER_PERMISSION_MODE,
    parse_user_permission_mode,
)
from agyloop.domain.slash import parse_slash, slash_to_prompt


def test_permission_mode_default_is_autonomous() -> None:
    assert DEFAULT_USER_PERMISSION_MODE == "autonomous"
    assert parse_user_permission_mode("autonomous") == "autonomous"


def test_permission_mode_aliases() -> None:
    assert parse_user_permission_mode("bypass") == "autonomous"
    assert parse_user_permission_mode("workspace_only") == "scoped"
    assert parse_user_permission_mode("nondestructive") == "safe"
    assert parse_user_permission_mode("YOLO") == "yolo"
    assert parse_user_permission_mode("scoped") == "scoped"
    assert parse_user_permission_mode("safe") == "safe"


def test_invalid_permission_mode() -> None:
    with pytest.raises(ValueError):
        parse_user_permission_mode("escalate")


def test_slash_allowlist() -> None:
    parsed = parse_slash("/help")
    assert parsed.name == "help"
    assert "Execute the /help command" in slash_to_prompt(parsed)
    with_args = parse_slash("/model gemini-2.5-pro")
    assert with_args.args == "gemini-2.5-pro"
    assert "arguments" in slash_to_prompt(with_args)


def test_slash_unknown_rejected() -> None:
    with pytest.raises(ValueError):
        parse_slash("/rm -rf /")
    with pytest.raises(ValueError):
        parse_slash("help")
    with pytest.raises(ValueError):
        parse_slash("/")


def test_stop_outranks_new_commands() -> None:
    result = stop_outranks(
        [
            SetPermissionModeCommand(mode="scoped"),
            SetCwdCommand(path="/tmp"),
            SlashCommand(text="/status"),
            StopCommand(),
            ResponseRetryCommand(),
        ]
    )
    assert result == [StopCommand()]


def test_latest_permission_and_cwd_win() -> None:
    result = stop_outranks(
        [
            SetPermissionModeCommand(mode="scoped"),
            SetPermissionModeCommand(mode="autonomous"),
            SetCwdCommand(path="/a"),
            SetCwdCommand(path="/b"),
            PromptNowCommand(text="x"),
        ]
    )
    assert SetPermissionModeCommand(mode="autonomous") in result
    assert SetCwdCommand(path="/b") in result
    assert PromptNowCommand(text="x") in result


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


def test_blank_cwd_rejected() -> None:
    with pytest.raises(ValueError):
        SetCwdCommand(path="  ")


def test_blank_tool_ids_rejected() -> None:
    with pytest.raises(ValueError):
        ApproveToolCommand(request_id="  ")
    with pytest.raises(ValueError):
        DenyToolCommand(request_id="")


def test_resource_mutate_validation() -> None:
    with pytest.raises(ValueError):
        ResourceMutateCommand(action="nope", kind="skill", value="s")
    with pytest.raises(ValueError):
        ResourceMutateCommand(action="add", kind="  ", value="s")
    with pytest.raises(ValueError):
        ResourceMutateCommand(action="add", kind="skill", value="  ")
    ok = ResourceMutateCommand(action="rm", kind="skill", value="")
    assert ok.action == "rm"


def test_feedback_validation() -> None:
    with pytest.raises(ValueError):
        ResponseFeedbackCommand(verdict="meh")
    assert ResponseFeedbackCommand(verdict="good").verdict == "good"


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


def test_deny_and_resource_preserved_in_order() -> None:
    result = stop_outranks(
        [
            ApproveToolCommand(request_id="a"),
            DenyToolCommand(request_id="b"),
            ResourceMutateCommand(action="add", kind="skill", value="s"),
            ResourceMutateCommand(action="rm", kind="skill", value="s"),
            ResponseFeedbackCommand(verdict="bad"),
            ResponseRetryCommand(),
        ]
    )
    names = [type(c).__name__ for c in result]
    assert names[:2] == ["ResponseRetryCommand", "ResponseFeedbackCommand"]
    assert "ApproveToolCommand" in names
    assert "DenyToolCommand" in names
