# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
from __future__ import annotations

import pytest

from claudeloop.domain.control import (
    ApproveToolCommand,
    DenyToolCommand,
    PromptNowCommand,
    ResourceMutateCommand,
    ResponseRetryCommand,
    SetCwdCommand,
    SetPermissionModeCommand,
    SlashCommand,
    StopCommand,
    stop_outranks,
)
from claudeloop.domain.permission import (
    SDK_TO_USER,
    parse_user_permission_mode,
    to_sdk_permission_mode,
)
from claudeloop.domain.slash import parse_slash, slash_to_prompt


def test_permission_mode_default_maps_to_bypass() -> None:
    assert to_sdk_permission_mode(parse_user_permission_mode("bypass")) == "bypassPermissions"


def test_permission_mode_manual_is_sdk_default() -> None:
    assert to_sdk_permission_mode(parse_user_permission_mode("manual")) == "default"


def test_permission_mode_aliases() -> None:
    assert parse_user_permission_mode("accept_edits") == "accept-edits"
    assert parse_user_permission_mode("AcceptEdits") == "accept-edits"


def test_invalid_permission_mode() -> None:
    with pytest.raises(ValueError):
        parse_user_permission_mode("escalate")


def test_slash_allowlist() -> None:
    parsed = parse_slash("/help")
    assert parsed.name == "help"
    assert "Execute the /help command" in slash_to_prompt(parsed)


def test_slash_unknown_rejected() -> None:
    with pytest.raises(ValueError):
        parse_slash("/rm -rf /")


def test_slash_requires_leading_slash() -> None:
    with pytest.raises(ValueError, match="must start with '/'"):
        parse_slash("help")


def test_slash_rejects_blank_body() -> None:
    with pytest.raises(ValueError, match="name must not be blank"):
        parse_slash("/   ")


def test_slash_to_prompt_includes_arguments() -> None:
    parsed = parse_slash("/model claude-opus")
    assert slash_to_prompt(parsed) == ("Execute the /model command with arguments: claude-opus")


def test_stop_outranks_new_commands() -> None:
    result = stop_outranks(
        [
            SetPermissionModeCommand(mode="plan"),
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
            SetPermissionModeCommand(mode="plan"),
            SetPermissionModeCommand(mode="auto"),
            SetCwdCommand(path="/a"),
            SetCwdCommand(path="/b"),
            PromptNowCommand(text="x"),
        ]
    )
    assert SetPermissionModeCommand(mode="auto") in result
    assert SetCwdCommand(path="/b") in result
    assert PromptNowCommand(text="x") in result


def test_permission_sdk_roundtrip_and_dontask() -> None:
    assert to_sdk_permission_mode("plan") == "plan"
    assert to_sdk_permission_mode("auto") == "auto"
    assert to_sdk_permission_mode("accept-edits") == "acceptEdits"
    assert SDK_TO_USER["dontAsk"] == "manual"


def test_deny_and_resource_preserved_in_order() -> None:
    result = stop_outranks(
        [
            ApproveToolCommand(request_id="a"),
            DenyToolCommand(request_id="b"),
            ResourceMutateCommand(action="add", kind="skill", value="s"),
            ResourceMutateCommand(action="rm", kind="skill", value="s"),
        ]
    )
    assert [type(c).__name__ for c in result] == [
        "ApproveToolCommand",
        "DenyToolCommand",
        "ResourceMutateCommand",
        "ResourceMutateCommand",
    ]
