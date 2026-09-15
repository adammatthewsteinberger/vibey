# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Operator control commands delivered mid-run via the control-plane inbox.

These are pure ADTs — the runner applies them; infrastructure only serializes
them to/from the run directory inbox."""

from __future__ import annotations

from dataclasses import dataclass

from claudeloop.domain.model_profile import parse_effort, parse_preset
from claudeloop.domain.permission import parse_user_permission_mode
from claudeloop.domain.slash import parse_slash


@dataclass(frozen=True, slots=True)
class StopCommand:
    """Request a soft stop: finish current turn or abort wait, write summary."""


@dataclass(frozen=True, slots=True)
class WindDownCommand:
    """Request a handoff at the next natural break.

    Deliberately weaker than StopCommand, which is honoured immediately. A
    wind-down lets the turn in flight finish so the handoff artifacts describe
    a consistent point -- that difference is the whole distinction between a
    stop and a soft stop.

    It also breaks an in-progress capacity wait: a supervisor that decides to
    rotate away from a runner sitting on a two-hour rate-limit window should
    not have to wait out the window to do it.
    """

    reason: str = "operator"


@dataclass(frozen=True, slots=True)
class PromptNowCommand:
    """Replace the next turn's prompt immediately (at the next operator boundary)."""

    text: str

    def __post_init__(self) -> None:
        if not self.text.strip():
            raise ValueError("prompt text must not be blank")


@dataclass(frozen=True, slots=True)
class PromptDeferredCommand:
    """Apply at a natural break: after a Continue verdict, before the next send."""

    text: str

    def __post_init__(self) -> None:
        if not self.text.strip():
            raise ValueError("prompt text must not be blank")


@dataclass(frozen=True, slots=True)
class SetModelCommand:
    """Change model (alias or raw id) at the next turn boundary."""

    model: str

    def __post_init__(self) -> None:
        if not self.model.strip():
            raise ValueError("model must not be blank")


@dataclass(frozen=True, slots=True)
class SetEffortCommand:
    """Change effort level at the next turn boundary."""

    effort: str

    def __post_init__(self) -> None:
        parse_effort(self.effort)


@dataclass(frozen=True, slots=True)
class SetPresetCommand:
    """Apply a low/medium/high preset at the next turn boundary."""

    preset: str

    def __post_init__(self) -> None:
        parse_preset(self.preset)


@dataclass(frozen=True, slots=True)
class SetPermissionModeCommand:
    """Change Agent SDK permission mode at the next turn boundary."""

    mode: str

    def __post_init__(self) -> None:
        parse_user_permission_mode(self.mode)


@dataclass(frozen=True, slots=True)
class SetCwdCommand:
    """Change working directory at the next turn boundary."""

    path: str

    def __post_init__(self) -> None:
        if not self.path.strip():
            raise ValueError("cwd path must not be blank")


@dataclass(frozen=True, slots=True)
class SlashCommand:
    """Inject a validated slash command as the next prompt."""

    text: str

    def __post_init__(self) -> None:
        parse_slash(self.text)


@dataclass(frozen=True, slots=True)
class ApproveToolCommand:
    """Approve a pending tool use (Manual permission mode)."""

    request_id: str

    def __post_init__(self) -> None:
        if not self.request_id.strip():
            raise ValueError("request_id must not be blank")


@dataclass(frozen=True, slots=True)
class DenyToolCommand:
    """Deny a pending tool use (Manual permission mode)."""

    request_id: str
    reason: str = "denied by operator"

    def __post_init__(self) -> None:
        if not self.request_id.strip():
            raise ValueError("request_id must not be blank")


@dataclass(frozen=True, slots=True)
class ResourceMutateCommand:
    """Generic mid-run resource mutation (attach, skill, plugin, …)."""

    action: str  # add|rm|set
    kind: str  # attachment|folder|skill|plugin|connector|github|memory|artifact
    value: str
    name: str | None = None

    def __post_init__(self) -> None:
        if self.action not in {"add", "rm", "set"}:
            raise ValueError(f"invalid resource action {self.action!r}")
        if not self.kind.strip():
            raise ValueError("resource kind must not be blank")
        if not self.value.strip() and self.action != "rm":
            raise ValueError("resource value must not be blank")


@dataclass(frozen=True, slots=True)
class ResponseFeedbackCommand:
    """Record good/bad feedback on the last assistant response."""

    verdict: str  # good|bad
    note: str = ""

    def __post_init__(self) -> None:
        if self.verdict not in {"good", "bad"}:
            raise ValueError("verdict must be good or bad")


@dataclass(frozen=True, slots=True)
class ResponseRetryCommand:
    """Re-queue the last prompt as PromptNow."""


ControlCommand = (
    StopCommand
    | WindDownCommand
    | PromptNowCommand
    | PromptDeferredCommand
    | SetModelCommand
    | SetEffortCommand
    | SetPresetCommand
    | SetPermissionModeCommand
    | SetCwdCommand
    | SlashCommand
    | ApproveToolCommand
    | DenyToolCommand
    | ResourceMutateCommand
    | ResponseFeedbackCommand
    | ResponseRetryCommand
)


def stop_outranks(commands: list[ControlCommand]) -> list[ControlCommand]:
    """Normalize a poll batch: if any Stop is present, only Stop remains.

    Latest of each other kind wins within the batch. A Stop also outranks a
    WindDown -- someone who asked to stop now should not be made to wait for a
    natural break because a wind-down happened to arrive in the same batch.
    """
    if any(isinstance(c, StopCommand) for c in commands):
        return [StopCommand()]
    wind_downs = [c for c in commands if isinstance(c, WindDownCommand)]
    if wind_downs:
        return [wind_downs[-1]]

    def _last(cls: type) -> list[ControlCommand]:
        items = [c for c in commands if isinstance(c, cls)]
        return [items[-1]] if items else []

    result: list[ControlCommand] = []
    result.extend(_last(PromptNowCommand))
    result.extend(_last(PromptDeferredCommand))
    result.extend(_last(SetPresetCommand))
    result.extend(_last(SetModelCommand))
    result.extend(_last(SetEffortCommand))
    result.extend(_last(SetPermissionModeCommand))
    result.extend(_last(SetCwdCommand))
    result.extend(_last(SlashCommand))
    result.extend(_last(ResponseRetryCommand))
    result.extend(_last(ResponseFeedbackCommand))
    # Keep all tool approve/deny and resource mutations in order (last-write still
    # applies per request_id / kind via runner application).
    for c in commands:
        if isinstance(c, (ApproveToolCommand, DenyToolCommand, ResourceMutateCommand)):
            result.append(c)
    return result
