# Made with ❤️ by [Vibey](https://the-vibey-project.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""The out-of-band control plane: commands an operator drops for a live run.

Generic over the concrete command type: each runner defines its own
operator-command ADT in its domain layer (they are not shared -- see each
runner's own ``domain/control.py``), so this seam is parameterized rather
than importing any one runner's concrete type. A runner instantiates these
as e.g. ``RunControl[ControlCommand]`` / ``ControlInbox[ControlCommand]``
with its own domain type.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Protocol, TypeVar, runtime_checkable

CommandT_co = TypeVar("CommandT_co", covariant=True)
CommandT_contra = TypeVar("CommandT_contra", contravariant=True)


@runtime_checkable
class RunControl(Protocol[CommandT_co]):
    """Mid-run operator commands drained from the control-plane inbox."""

    def poll(self) -> Sequence[CommandT_co]: ...


@runtime_checkable
class ControlInbox(Protocol[CommandT_contra]):
    """Where an out-of-band command is dropped for a live run to pick up."""

    def enqueue(self, command: CommandT_contra) -> Path: ...
