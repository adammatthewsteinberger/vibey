# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Operator inbox commands: parse a JSON dict, never ignore unknown kinds."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import cast

from codexloop.domain.approval import ApprovalPolicy, SandboxMode
from codexloop.domain.errors import ConfigurationError
from codexloop.domain.model_profile import Effort


class PromptTiming(StrEnum):
    NOW = "now"
    NEXT_TURN = "next_turn"


@dataclass(frozen=True, slots=True)
class Stop:
    def to_dict(self) -> dict[str, object]:
        return {"kind": "stop"}


@dataclass(frozen=True, slots=True)
class Prompt:
    text: str
    timing: PromptTiming

    def to_dict(self) -> dict[str, object]:
        return {"kind": "prompt", "text": self.text, "timing": self.timing.value}


@dataclass(frozen=True, slots=True)
class SetModel:
    model: str

    def to_dict(self) -> dict[str, object]:
        return {"kind": "set_model", "model": self.model}


@dataclass(frozen=True, slots=True)
class SetEffort:
    effort: Effort

    def to_dict(self) -> dict[str, object]:
        return {"kind": "set_effort", "effort": self.effort.value}


@dataclass(frozen=True, slots=True)
class SetApproval:
    policy: ApprovalPolicy

    def to_dict(self) -> dict[str, object]:
        return {"kind": "set_approval", "policy": self.policy.value}


@dataclass(frozen=True, slots=True)
class SetSandbox:
    sandbox: SandboxMode

    def to_dict(self) -> dict[str, object]:
        return {"kind": "set_sandbox", "sandbox": self.sandbox.value}


@dataclass(frozen=True, slots=True)
class SetCwd:
    cwd: str

    def to_dict(self) -> dict[str, object]:
        return {"kind": "set_cwd", "cwd": self.cwd}


@dataclass(frozen=True, slots=True)
class Snapshot:
    def to_dict(self) -> dict[str, object]:
        return {"kind": "snapshot"}


@dataclass(frozen=True, slots=True)
class ResourceMutate:
    payload: dict[str, object]

    def __post_init__(self) -> None:
        object.__setattr__(self, "payload", dict(self.payload))

    def to_dict(self) -> dict[str, object]:
        return {"kind": "resource_mutate", "payload": dict(self.payload)}


@dataclass(frozen=True, slots=True)
class WindDownCommand:
    reason: str

    def __post_init__(self) -> None:
        if not self.reason.strip():
            raise ValueError("wind-down reason must be non-empty")

    def to_dict(self) -> dict[str, object]:
        return {"kind": "wind_down", "reason": self.reason}


ControlCommand = (
    Stop
    | Prompt
    | SetModel
    | SetEffort
    | SetApproval
    | SetSandbox
    | SetCwd
    | Snapshot
    | ResourceMutate
    | WindDownCommand
)


def parse_control(data: Mapping[str, object]) -> ControlCommand:
    kind = data.get("kind")
    if not isinstance(kind, str):
        raise ConfigurationError("control command missing kind")
    builder = _BUILDERS.get(kind)
    if builder is None:
        raise ConfigurationError(f"unknown control command kind: {kind!r}")
    try:
        return builder(data)
    except (KeyError, TypeError, ValueError) as exc:
        raise ConfigurationError(f"invalid control command {kind!r}: {exc}") from exc


def _parse_stop(_data: Mapping[str, object]) -> Stop:
    return Stop()


def _parse_prompt(data: Mapping[str, object]) -> Prompt:
    return Prompt(text=str(data["text"]), timing=PromptTiming(str(data["timing"])))


def _parse_set_model(data: Mapping[str, object]) -> SetModel:
    return SetModel(model=str(data["model"]))


def _parse_set_effort(data: Mapping[str, object]) -> SetEffort:
    return SetEffort(effort=Effort(str(data["effort"])))


def _parse_set_approval(data: Mapping[str, object]) -> SetApproval:
    return SetApproval(policy=ApprovalPolicy(str(data["policy"])))


def _parse_set_sandbox(data: Mapping[str, object]) -> SetSandbox:
    return SetSandbox(sandbox=SandboxMode(str(data["sandbox"])))


def _parse_set_cwd(data: Mapping[str, object]) -> SetCwd:
    return SetCwd(cwd=str(data["cwd"]))


def _parse_snapshot(_data: Mapping[str, object]) -> Snapshot:
    return Snapshot()


def _parse_resource_mutate(data: Mapping[str, object]) -> ResourceMutate:
    payload = data["payload"]
    if not isinstance(payload, Mapping):
        raise TypeError("resource_mutate payload must be a mapping")
    return ResourceMutate(payload=dict(cast(Mapping[str, object], payload)))


def _parse_wind_down(data: Mapping[str, object]) -> WindDownCommand:
    return WindDownCommand(reason=str(data["reason"]))


_BUILDERS: dict[str, Callable[[Mapping[str, object]], ControlCommand]] = {
    "stop": _parse_stop,
    "prompt": _parse_prompt,
    "set_model": _parse_set_model,
    "set_effort": _parse_set_effort,
    "set_approval": _parse_set_approval,
    "set_sandbox": _parse_set_sandbox,
    "set_cwd": _parse_set_cwd,
    "snapshot": _parse_snapshot,
    "resource_mutate": _parse_resource_mutate,
    "wind_down": _parse_wind_down,
}


@dataclass(frozen=True, slots=True)
class StopOutranksResult:
    """Result of stop_outranks: commands to execute and any held wind-down."""

    commands: Sequence[ControlCommand]
    held_wind_down: WindDownCommand | None


def stop_outranks(commands: Sequence[ControlCommand]) -> StopOutranksResult:
    """Stop always wins, but a pending wind-down is held, not dropped.

    When both Stop and WindDownCommand are present, Stop takes precedence
    and executes, but the WindDownCommand is preserved separately so it
    can be requeued or handled after the stop completes.
    """
    has_stop = any(isinstance(cmd, Stop) for cmd in commands)
    wind_down = next((cmd for cmd in commands if isinstance(cmd, WindDownCommand)), None)

    if has_stop and wind_down is not None:
        # Stop wins: filter out wind-down from commands, but hold it separately
        filtered = [cmd for cmd in commands if not isinstance(cmd, WindDownCommand)]
        return StopOutranksResult(commands=filtered, held_wind_down=wind_down)

    # No conflict: return everything as-is
    return StopOutranksResult(commands=list(commands), held_wind_down=None)
