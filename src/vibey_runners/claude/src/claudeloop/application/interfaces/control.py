# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""The out-of-band control plane: commands an operator drops for a live run."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from claudeloop.domain.control import ControlCommand


@runtime_checkable
class RunControl(Protocol):
    def poll(self) -> list[ControlCommand]: ...


@runtime_checkable
class ControlInbox(Protocol):
    """Where an out-of-band command is dropped for a live run to pick up."""

    def enqueue(self, command: ControlCommand) -> object: ...
