# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""File-based RunControl — operator commands land in inbox/*.cmd.json."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, assert_never

from agyloop.domain.control import (
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
    match command:
        case StopCommand():
            return {"type": "stop"}
        case PromptNowCommand(text=text):
            return {"type": "prompt_now", "text": text}
        case PromptDeferredCommand(text=text):
            return {"type": "prompt_deferred", "text": text}
        case SetModelCommand(model=model):
            return {"type": "set_model", "model": model}
        case SetEffortCommand(effort=effort):
            return {"type": "set_effort", "effort": effort}
        case SetPresetCommand(preset=preset):
            return {"type": "set_preset", "preset": preset}
        case SetPermissionModeCommand(mode=mode):
            return {"type": "set_permission_mode", "mode": mode}
        case SetCwdCommand(path=path):
            return {"type": "set_cwd", "path": path}
        case SlashCommand(text=text):
            return {"type": "slash", "text": text}
        case ApproveToolCommand(request_id=request_id):
            return {"type": "approve_tool", "request_id": request_id}
        case DenyToolCommand(request_id=request_id, reason=reason):
            return {"type": "deny_tool", "request_id": request_id, "reason": reason}
        case ResourceMutateCommand(action=action, kind=kind, value=value, name=name):
            return {
                "type": "resource_mutate",
                "action": action,
                "kind": kind,
                "value": value,
                "name": name,
            }
        case ResponseFeedbackCommand(verdict=verdict, note=note):
            return {"type": "response_feedback", "verdict": verdict, "note": note}
        case ResponseRetryCommand():
            return {"type": "response_retry"}
        case _:
            assert_never(command)


def _payload_to_command(raw: dict[str, object]) -> ControlCommand:
    kind = str(raw["type"])
    if kind == "stop":
        return StopCommand()
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
