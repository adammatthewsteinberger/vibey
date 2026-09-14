# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""File-based RunControl — operator commands land in ``inbox/*.cmd.json``."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

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


class FileRunControl:
    def __init__(self, inbox: Path) -> None:
        self._inbox = inbox
        self._inbox.mkdir(parents=True, exist_ok=True)

    def enqueue(self, command: ControlCommand) -> Path:
        payload = _command_to_payload(command)
        name = f"{time.time_ns()}-{payload['type']}.cmd.json"
        path = self._inbox / name
        path.write_text(json.dumps(payload) + "\n", encoding="utf-8")
        return path

    def poll(self) -> list[ControlCommand]:
        files = sorted(self._inbox.glob("*.cmd.json"))
        commands: list[ControlCommand] = []
        for path in files:
            try:
                raw = json.loads(path.read_text(encoding="utf-8"))
                commands.append(_payload_to_command(raw))
            except (json.JSONDecodeError, KeyError, TypeError, ValueError):
                continue
            else:
                path.unlink(missing_ok=True)
        return stop_outranks(commands)


def _command_to_payload(command: ControlCommand) -> dict[str, Any]:
    if isinstance(command, Stop):
        return {"type": "stop"}
    if isinstance(command, Prompt):
        return {"type": "prompt", "text": command.text}
    if isinstance(command, SetModel):
        return {"type": "set_model", "model": command.model}
    if isinstance(command, SetEffort):
        return {"type": "set_effort", "effort": command.effort}
    if isinstance(command, SetCwd):
        return {"type": "set_cwd", "path": command.path}
    if isinstance(command, Snapshot):
        return {"type": "snapshot"}
    if isinstance(command, SavePoint):
        return {"type": "savepoint"}
    if isinstance(command, WindDown):
        return {"type": "wind_down", "reason": command.reason}
    raise TypeError(f"unsupported control command: {type(command)!r}")


def _payload_to_command(raw: dict[str, object]) -> ControlCommand:
    kind = str(raw["type"])
    if kind == "stop":
        return Stop()
    if kind == "prompt":
        return Prompt(text=str(raw["text"]))
    if kind == "set_model":
        return SetModel(model=str(raw["model"]))
    if kind == "set_effort":
        return SetEffort(effort=str(raw["effort"]))
    if kind == "set_cwd":
        return SetCwd(path=str(raw["path"]))
    if kind == "snapshot":
        return Snapshot()
    if kind == "savepoint":
        return SavePoint()
    if kind == "wind_down":
        return WindDown(reason=str(raw["reason"]))
    raise ValueError(f"unknown control command type: {kind}")
