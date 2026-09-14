# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Operator control commands delivered mid-run via the control-plane inbox.

These are pure ADTs — the runner applies them; infrastructure only serializes
them to/from the run directory inbox.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Stop:
    """Request a soft stop: finish current turn or abort wait, write summary."""


@dataclass(frozen=True, slots=True)
class Prompt:
    """Replace or extend the next turn's prompt at the next operator boundary."""

    text: str

    def __post_init__(self) -> None:
        if not self.text.strip():
            raise ValueError("prompt text must not be blank")


@dataclass(frozen=True, slots=True)
class SetModel:
    """Change model (alias or raw id) at the next turn boundary."""

    model: str

    def __post_init__(self) -> None:
        if not self.model.strip():
            raise ValueError("model must not be blank")


@dataclass(frozen=True, slots=True)
class SetEffort:
    """Change effort level at the next turn boundary."""

    effort: str

    def __post_init__(self) -> None:
        if not self.effort.strip():
            raise ValueError("effort must not be blank")


@dataclass(frozen=True, slots=True)
class SetCwd:
    """Change working directory at the next turn boundary."""

    path: str

    def __post_init__(self) -> None:
        if not self.path.strip():
            raise ValueError("cwd path must not be blank")


@dataclass(frozen=True, slots=True)
class Snapshot:
    """Request a run snapshot at the next operator boundary."""


@dataclass(frozen=True, slots=True)
class SavePoint:
    """Request a git savepoint at the next operator boundary."""


@dataclass(frozen=True, slots=True)
class WindDown:
    """Request a wind-down: finish current turn, write handoff, exit 75."""

    reason: str = "operator wind-down"

    def __post_init__(self) -> None:
        if not self.reason.strip():
            raise ValueError("wind-down reason must not be blank")


ControlCommand = Stop | Prompt | SetModel | SetEffort | SetCwd | Snapshot | SavePoint | WindDown


def stop_outranks(commands: list[ControlCommand]) -> list[ControlCommand]:
    """Stop always wins; a pending wind-down is held (not dropped) if stop arrives.

    Ordering: stop first, then other commands (including wind-down).
    """
    stops = [c for c in commands if isinstance(c, Stop)]
    if stops:
        return [stops[0], *[c for c in commands if not isinstance(c, Stop)]]
    return commands
