# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Enqueue mid-run control commands into a run directory inbox."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

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
)
from cursorloop.infrastructure.control import FileRunControl
from cursorloop.infrastructure.rundir import resolve_run_directory


@dataclass(frozen=True, slots=True)
class EnqueueResult:
    run_id: str
    path: Path


def enqueue(cwd: Path, command: ControlCommand, run_id: str | None = None) -> EnqueueResult:
    directory = resolve_run_directory(cwd, run_id)
    path = FileRunControl(directory.inbox).enqueue(command)
    return EnqueueResult(run_id=directory.read_meta().run_id, path=path)


def enqueue_stop(cwd: Path, run_id: str | None = None) -> EnqueueResult:
    return enqueue(cwd, Stop(), run_id)


def enqueue_prompt(cwd: Path, text: str, run_id: str | None = None) -> EnqueueResult:
    return enqueue(cwd, Prompt(text=text), run_id)


def enqueue_model(cwd: Path, model: str, run_id: str | None = None) -> EnqueueResult:
    return enqueue(cwd, SetModel(model=model), run_id)


def enqueue_effort(cwd: Path, effort: str, run_id: str | None = None) -> EnqueueResult:
    return enqueue(cwd, SetEffort(effort=effort), run_id)


def enqueue_cwd(cwd: Path, path: str, run_id: str | None = None) -> EnqueueResult:
    return enqueue(cwd, SetCwd(path=path), run_id)


def enqueue_snapshot(cwd: Path, run_id: str | None = None) -> EnqueueResult:
    return enqueue(cwd, Snapshot(), run_id)


def enqueue_savepoint(cwd: Path, run_id: str | None = None) -> EnqueueResult:
    return enqueue(cwd, SavePoint(), run_id)


def enqueue_wind_down(cwd: Path, reason: str, run_id: str | None = None) -> EnqueueResult:
    return enqueue(cwd, WindDown(reason=reason), run_id)
