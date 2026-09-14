# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""The soft stop: weaker than Stop, and outranked by it."""

from __future__ import annotations

from claudeloop.domain.control import (
    PromptNowCommand,
    StopCommand,
    WindDownCommand,
    stop_outranks,
)


def test_stop_outranks_a_wind_down_in_the_same_batch() -> None:
    """Someone who asked to stop now should not be made to wait for a natural
    break because a wind-down happened to arrive alongside it."""
    result = stop_outranks([WindDownCommand(reason="rotate"), StopCommand()])
    assert result == [StopCommand()]


def test_a_wind_down_outranks_ordinary_commands() -> None:
    result = stop_outranks([PromptNowCommand(text="hi"), WindDownCommand(reason="rotate")])
    assert result == [WindDownCommand(reason="rotate")]


def test_the_latest_wind_down_in_a_batch_wins() -> None:
    result = stop_outranks([WindDownCommand(reason="first"), WindDownCommand(reason="second")])
    assert result == [WindDownCommand(reason="second")]


def test_the_default_reason_is_recorded_not_blank() -> None:
    assert WindDownCommand().reason == "operator"
