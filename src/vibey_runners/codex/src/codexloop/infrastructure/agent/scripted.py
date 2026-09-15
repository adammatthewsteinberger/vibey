# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""JSON-scripted AgentGateway / CapacityProbe for system-live tests.

Activated only via the composition-root test gate in ``bootstrap`` when both
``CODEXLOOP_ALLOW_TEST_AGENT=1`` and ``CODEXLOOP_TEST_AGENT_SCRIPT`` are set.
Not a user-facing feature.
"""

from __future__ import annotations

import json
import os
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field, fields
from pathlib import Path
from typing import Any

from codexloop.application.dto import ProbeResult, TurnOutcome
from codexloop.application.ports import PermissionMode
from codexloop.domain.capacity import PlanWindows, RateLimitWindow
from codexloop.domain.classify import classify
from codexloop.domain.model_profile import ModelEffortProfile
from codexloop.domain.signals import TurnSignals

ALLOW_TEST_AGENT_ENV = "CODEXLOOP_ALLOW_TEST_AGENT"
TEST_AGENT_SCRIPT_ENV = "CODEXLOOP_TEST_AGENT_SCRIPT"


@dataclass(frozen=True, slots=True)
class ScriptedTurn:
    signals: TurnSignals = field(default_factory=TurnSignals)
    thread_id: str | None = "scripted-session"
    cost_dollars: float = 0.0


@dataclass(frozen=True, slots=True)
class AgentScript:
    probes: tuple[TurnSignals, ...]
    turns: tuple[ScriptedTurn, ...]


class ScriptedAgentGateway:
    """Replays scripted turns for system harnesses."""

    def __init__(self, script: Sequence[ScriptedTurn]) -> None:
        self._script = list(script)
        self.sent_prompts: list[str] = []
        self.closed = False
        self.profiles: list[ModelEffortProfile] = []
        self.permission_modes: list[PermissionMode] = []
        self.cwds: list[str] = []
        self.resource_updates: list[Mapping[str, object]] = []
        self.tool_resolutions: list[tuple[str, bool, str]] = []

    async def send_turn(self, prompt: str) -> TurnOutcome:
        self.sent_prompts.append(prompt)
        if not self._script:
            raise IndexError(f"ScriptedAgentGateway: no turns left (prompt={prompt!r})")
        turn = self._script.pop(0)
        return TurnOutcome(
            signals=turn.signals,
            thread_id=turn.thread_id,
            cost_dollars=turn.cost_dollars,
        )

    async def close(self) -> None:
        self.closed = True

    async def set_profile(self, profile: ModelEffortProfile) -> None:
        self.profiles.append(profile)

    async def set_permission_mode(self, mode: PermissionMode) -> None:
        self.permission_modes.append(mode)

    async def set_cwd(self, path: str) -> None:
        self.cwds.append(path)

    async def set_session_resources(self, resources: Mapping[str, object]) -> None:
        self.resource_updates.append(resources)

    def resolve_tool_approval(self, request_id: str, *, allow: bool, reason: str = "") -> bool:
        self.tool_resolutions.append((request_id, allow, reason))
        return allow


class ScriptedCapacityProbe:
    def __init__(self, script: Sequence[TurnSignals]) -> None:
        self._script = list(script)
        self.calls = 0

    async def probe(self) -> ProbeResult:
        self.calls += 1
        if not self._script:
            raise IndexError("ScriptedCapacityProbe: no probes left in script")
        signals = self._script.pop(0)
        return ProbeResult(outcome=classify(signals), snapshot=signals.plan_windows)


def load_agent_script(path: Path | str) -> AgentScript:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("agent script root must be a JSON object")
    probes_raw = raw.get("probes", [{}])
    turns_raw = raw.get("turns", [])
    if not isinstance(probes_raw, list) or not isinstance(turns_raw, list):
        raise ValueError("agent script 'probes' and 'turns' must be arrays")
    if not turns_raw:
        raise ValueError("agent script must include at least one turn")
    probes = tuple(_parse_signals(item) for item in probes_raw)
    turns = tuple(_parse_turn(item) for item in turns_raw)
    return AgentScript(probes=probes, turns=turns)


def resolve_test_agent_from_env() -> tuple[ScriptedAgentGateway, ScriptedCapacityProbe] | None:
    """Return scripted adapters when the test gate is fully enabled.

    Raises ``RuntimeError`` if the script path is set without the allow flag.
    """
    allow = os.environ.get(ALLOW_TEST_AGENT_ENV, "").strip()
    script_path = os.environ.get(TEST_AGENT_SCRIPT_ENV, "").strip()
    if script_path and allow not in {"1", "true", "TRUE", "yes", "YES"}:
        raise RuntimeError(
            f"{TEST_AGENT_SCRIPT_ENV} is set but {ALLOW_TEST_AGENT_ENV}=1 is "
            "required. The scripted agent is test-only and will not activate "
            "without the allow flag."
        )
    if not script_path:
        return None
    if allow not in {"1", "true", "TRUE", "yes", "YES"}:  # pragma: no cover — raised above
        return None
    script = load_agent_script(script_path)
    return ScriptedAgentGateway(script.turns), ScriptedCapacityProbe(script.probes)


def _parse_turn(item: object) -> ScriptedTurn:
    if not isinstance(item, dict):
        raise ValueError("each turn must be a JSON object")
    signals = _parse_signals(item.get("signals", {}))
    thread_id = item.get("thread_id", "scripted-session")
    return ScriptedTurn(
        signals=signals,
        thread_id=None if thread_id is None else str(thread_id),
        cost_dollars=float(item.get("cost_dollars", 0.0)),
    )


def _parse_signals(item: object) -> TurnSignals:
    if isinstance(item, dict) and "signals" in item and set(item) <= {"signals"}:
        item = item["signals"]
    if not isinstance(item, dict):
        raise ValueError("signals must be a JSON object")
    data: dict[str, Any] = dict(item)
    if "plan_windows" in data:
        data["plan_windows"] = _parse_plan_windows(data["plan_windows"])
    known = {f.name for f in fields(TurnSignals)}
    filtered = {k: v for k, v in data.items() if k in known}
    return TurnSignals(**filtered)


def _parse_plan_windows(raw: object) -> PlanWindows | None:
    if raw is None:
        return None
    if not isinstance(raw, dict):
        raise ValueError("plan_windows must be an object")
    return PlanWindows(
        primary=_parse_window(raw.get("primary")),
        secondary=_parse_window(raw.get("secondary")),
        plan_type=None if raw.get("plan_type") is None else str(raw["plan_type"]),
        limit_reached=(
            None
            if raw.get("rate_limit_reached_type") is None
            else str(raw["rate_limit_reached_type"])
        ),
    )


def _parse_window(raw: object) -> RateLimitWindow | None:
    if raw is None:
        return None
    if not isinstance(raw, dict):
        return None
    minutes = raw.get("window_minutes")
    if not isinstance(minutes, int):
        return None
    used = raw.get("used_percent")
    return RateLimitWindow(
        used_percent=float(used) if isinstance(used, int | float) else None,
        window_minutes=minutes,
        resets_at=None,
    )


__all__ = [
    "ALLOW_TEST_AGENT_ENV",
    "TEST_AGENT_SCRIPT_ENV",
    "AgentScript",
    "ScriptedAgentGateway",
    "ScriptedCapacityProbe",
    "ScriptedTurn",
    "load_agent_script",
    "resolve_test_agent_from_env",
]
