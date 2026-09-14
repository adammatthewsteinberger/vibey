# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""File-based RunControl — operator commands land in inbox/*.cmd.json."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from claudeloop.domain.control import (
    ApproveToolCommand,
    ControlCommand,
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
    WindDownCommand,
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
                # Leave corrupt files for inspection; skip them.
                continue
            else:
                path.unlink(missing_ok=True)
        return stop_outranks(commands)


def _command_to_payload(command: ControlCommand) -> dict[str, Any]:
    if isinstance(command, StopCommand):
        return {"type": "stop"}
    if isinstance(command, WindDownCommand):
        return {"type": "wind_down", "reason": command.reason}
    if isinstance(command, PromptNowCommand):
        return {"type": "prompt_now", "text": command.text}
    if isinstance(command, PromptDeferredCommand):
        return {"type": "prompt_deferred", "text": command.text}
    if isinstance(command, SetModelCommand):
        return {"type": "set_model", "model": command.model}
    if isinstance(command, SetEffortCommand):
        return {"type": "set_effort", "effort": command.effort}
    if isinstance(command, SetPresetCommand):
        return {"type": "set_preset", "preset": command.preset}
    if isinstance(command, SetPermissionModeCommand):
        return {"type": "set_permission_mode", "mode": command.mode}
    if isinstance(command, SetCwdCommand):
        return {"type": "set_cwd", "path": command.path}
    if isinstance(command, SlashCommand):
        return {"type": "slash", "text": command.text}
    if isinstance(command, ApproveToolCommand):
        return {"type": "approve_tool", "request_id": command.request_id}
    if isinstance(command, DenyToolCommand):
        return {
            "type": "deny_tool",
            "request_id": command.request_id,
            "reason": command.reason,
        }
    if isinstance(command, ResourceMutateCommand):
        return {
            "type": "resource_mutate",
            "action": command.action,
            "kind": command.kind,
            "value": command.value,
            "name": command.name,
        }
    if isinstance(command, ResponseFeedbackCommand):
        return {
            "type": "response_feedback",
            "verdict": command.verdict,
            "note": command.note,
        }
    if isinstance(command, ResponseRetryCommand):
        return {"type": "response_retry"}
    raise TypeError(f"unsupported control command: {type(command)!r}")


def _payload_to_command(raw: dict[str, object]) -> ControlCommand:
    kind = str(raw["type"])
    if kind == "stop":
        return StopCommand()
    if kind == "wind_down":
        return WindDownCommand(reason=str(raw.get("reason", "operator")))
    if kind == "prompt_now":
        return PromptNowCommand(text=str(raw["text"]))
    if kind == "prompt_deferred":
        return PromptDeferredCommand(text=str(raw["text"]))
    if kind == "set_model":
        return SetModelCommand(model=str(raw["model"]))
    if kind == "set_effort":
        return SetEffortCommand(effort=str(raw["effort"]))
    if kind == "set_preset":
        return SetPresetCommand(preset=str(raw["preset"]))
    if kind == "set_permission_mode":
        return SetPermissionModeCommand(mode=str(raw["mode"]))
    if kind == "set_cwd":
        return SetCwdCommand(path=str(raw["path"]))
    if kind == "slash":
        return SlashCommand(text=str(raw["text"]))
    if kind == "approve_tool":
        return ApproveToolCommand(request_id=str(raw["request_id"]))
    if kind == "deny_tool":
        return DenyToolCommand(
            request_id=str(raw["request_id"]),
            reason=str(raw.get("reason") or "denied by operator"),
        )
    if kind == "resource_mutate":
        name = raw.get("name")
        return ResourceMutateCommand(
            action=str(raw["action"]),
            kind=str(raw["kind"]),
            value=str(raw.get("value") or ""),
            name=str(name) if name is not None else None,
        )
    if kind == "response_feedback":
        return ResponseFeedbackCommand(
            verdict=str(raw["verdict"]),
            note=str(raw.get("note") or ""),
        )
    if kind == "response_retry":
        return ResponseRetryCommand()
    raise ValueError(f"unknown control command type: {kind}")
