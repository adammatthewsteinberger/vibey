# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Operator use cases for mid-run control — port-shaped, no infrastructure imports."""

from __future__ import annotations

from dataclasses import dataclass

from claudeloop.application.interfaces import ControlInbox
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
)


@dataclass(frozen=True, slots=True)
class EnqueueResult:
    run_id: str
    command_type: str


def request_wind_down(
    inbox: ControlInbox, *, reason: str = "operator", run_id: str
) -> EnqueueResult:
    inbox.enqueue(WindDownCommand(reason=reason))
    return EnqueueResult(run_id=run_id, command_type="wind_down")


def request_stop(inbox: ControlInbox, *, run_id: str) -> EnqueueResult:
    inbox.enqueue(StopCommand())
    return EnqueueResult(run_id=run_id, command_type="stop")


def request_prompt(
    inbox: ControlInbox, text: str, *, immediate: bool, run_id: str
) -> EnqueueResult:
    command: ControlCommand = (
        PromptNowCommand(text=text) if immediate else PromptDeferredCommand(text=text)
    )
    inbox.enqueue(command)
    return EnqueueResult(
        run_id=run_id,
        command_type="prompt_now" if immediate else "prompt_deferred",
    )


def request_set_model(inbox: ControlInbox, model: str, *, run_id: str) -> EnqueueResult:
    inbox.enqueue(SetModelCommand(model=model))
    return EnqueueResult(run_id=run_id, command_type="set_model")


def request_set_effort(inbox: ControlInbox, effort: str, *, run_id: str) -> EnqueueResult:
    inbox.enqueue(SetEffortCommand(effort=effort))
    return EnqueueResult(run_id=run_id, command_type="set_effort")


def request_set_preset(inbox: ControlInbox, preset: str, *, run_id: str) -> EnqueueResult:
    inbox.enqueue(SetPresetCommand(preset=preset))
    return EnqueueResult(run_id=run_id, command_type="set_preset")


def request_set_permission_mode(inbox: ControlInbox, mode: str, *, run_id: str) -> EnqueueResult:
    inbox.enqueue(SetPermissionModeCommand(mode=mode))
    return EnqueueResult(run_id=run_id, command_type="set_permission_mode")


def request_set_cwd(inbox: ControlInbox, path: str, *, run_id: str) -> EnqueueResult:
    inbox.enqueue(SetCwdCommand(path=path))
    return EnqueueResult(run_id=run_id, command_type="set_cwd")


def request_slash(inbox: ControlInbox, text: str, *, run_id: str) -> EnqueueResult:
    inbox.enqueue(SlashCommand(text=text))
    return EnqueueResult(run_id=run_id, command_type="slash")


def request_tool_decision(
    inbox: ControlInbox,
    request_id: str,
    *,
    allow: bool,
    reason: str = "",
    run_id: str,
) -> EnqueueResult:
    if allow:
        inbox.enqueue(ApproveToolCommand(request_id=request_id))
        return EnqueueResult(run_id=run_id, command_type="approve_tool")
    inbox.enqueue(DenyToolCommand(request_id=request_id, reason=reason or "denied by operator"))
    return EnqueueResult(run_id=run_id, command_type="deny_tool")


def request_resource_mutate(
    inbox: ControlInbox,
    *,
    action: str,
    kind: str,
    value: str,
    name: str | None = None,
    run_id: str,
) -> EnqueueResult:
    inbox.enqueue(ResourceMutateCommand(action=action, kind=kind, value=value, name=name))
    return EnqueueResult(run_id=run_id, command_type="resource_mutate")


def request_response_feedback(
    inbox: ControlInbox, verdict: str, *, note: str = "", run_id: str
) -> EnqueueResult:
    inbox.enqueue(ResponseFeedbackCommand(verdict=verdict, note=note))
    return EnqueueResult(run_id=run_id, command_type="response_feedback")


def request_response_retry(inbox: ControlInbox, *, run_id: str) -> EnqueueResult:
    inbox.enqueue(ResponseRetryCommand())
    return EnqueueResult(run_id=run_id, command_type="response_retry")
