# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
from __future__ import annotations

import pytest

from cursorloop.domain.control import (
    ControlCommand,
    Prompt,
    SavePoint,
    SetCwd,
    SetEffort,
    SetModel,
    Snapshot,
    Stop,
    WindDown,
    stop_outranks,
)


def test_control_command_union_covers_the_eight_variants() -> None:
    commands: list[ControlCommand] = [
        Stop(),
        Prompt(text="continue with the next item"),
        SetModel(model="composer-2.5"),
        SetEffort(effort="high"),
        SetCwd(path="/tmp/work"),
        Snapshot(),
        SavePoint(),
        WindDown(reason="low credits"),
    ]
    assert [type(c).__name__ for c in commands] == [
        "Stop",
        "Prompt",
        "SetModel",
        "SetEffort",
        "SetCwd",
        "Snapshot",
        "SavePoint",
        "WindDown",
    ]


def test_blank_prompt_model_effort_and_cwd_are_rejected() -> None:
    with pytest.raises(ValueError, match="prompt"):
        Prompt(text="   ")
    with pytest.raises(ValueError, match="model"):
        SetModel(model="")
    with pytest.raises(ValueError, match="effort"):
        SetEffort(effort=" ")
    with pytest.raises(ValueError, match="cwd"):
        SetCwd(path="")


def test_blank_wind_down_reason_is_rejected() -> None:
    with pytest.raises(ValueError, match="wind-down reason"):
        WindDown(reason="   ")


def test_wind_down_defaults_to_operator_wind_down() -> None:
    cmd = WindDown()
    assert cmd.reason == "operator wind-down"


def test_stop_outranks_places_stop_first_and_preserves_others() -> None:
    commands = [
        Prompt(text="hello"),
        WindDown(reason="test"),
        Stop(),
        SetModel(model="test"),
    ]
    result = stop_outranks(commands)
    assert isinstance(result[0], Stop)
    assert len(result) == 4
    assert result[1:] == [
        Prompt(text="hello"),
        WindDown(reason="test"),
        SetModel(model="test"),
    ]


def test_stop_outranks_holds_wind_down_when_stop_arrives() -> None:
    """Wind-down is held (not dropped) when stop wins."""
    commands = [WindDown(reason="low headroom"), Stop()]
    result = stop_outranks(commands)
    assert isinstance(result[0], Stop)
    assert isinstance(result[1], WindDown)
    assert len(result) == 2


def test_stop_outranks_with_no_stop_returns_original_order() -> None:
    commands = [Prompt(text="hello"), WindDown(reason="test"), Snapshot()]
    result = stop_outranks(commands)
    assert result == commands
