# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""JSON-scripted AgentGateway / CapacityProbe for system-live tests.

Activated only via the composition-root test gate in ``bootstrap`` when both
``CLAUDELOOP_ALLOW_TEST_AGENT=1`` and ``CLAUDELOOP_TEST_AGENT_SCRIPT`` are set.
Not a user-facing feature.
"""

from __future__ import annotations

import json
import os
from collections.abc import Callable
from dataclasses import dataclass, field, fields
from datetime import datetime
from pathlib import Path
from typing import Any

from structlog.stdlib import BoundLogger

from claudeloop.application.dto import TurnOutcome
from claudeloop.domain.classify import TurnSignals
from claudeloop.domain.completion import StructuredVerdict
from claudeloop.domain.model_profile import ModelEffortProfile
from claudeloop.infrastructure.logging import get_logger

ALLOW_TEST_AGENT_ENV = "CLAUDELOOP_ALLOW_TEST_AGENT"
TEST_AGENT_SCRIPT_ENV = "CLAUDELOOP_TEST_AGENT_SCRIPT"

OnEvent = Callable[[dict[str, object]], None]


def _logger() -> BoundLogger:
    return get_logger(component="agent.scripted")


@dataclass(frozen=True, slots=True)
class ScriptedTurn:
    signals: TurnSignals = field(default_factory=TurnSignals)
    verdict: StructuredVerdict | None = None
    output_text: str = ""
    session_id: str = "scripted-session"
    cost_usd: float = 0.0
    raw_events: tuple[dict[str, object], ...] = ()


@dataclass(frozen=True, slots=True)
class AgentScript:
    probes: tuple[TurnSignals, ...]
    turns: tuple[ScriptedTurn, ...]


class ScriptedAgentGateway:
    """Replays scripted turns; optionally emits raw_events via on_event."""

    def __init__(
        self,
        script: list[ScriptedTurn],
        *,
        on_event: OnEvent | None = None,
    ) -> None:
        self._script = list(script)
        self._on_event = on_event
        self.sent_prompts: list[str] = []
        self.closed = False
        self.profiles: list[ModelEffortProfile] = []
        self.permission_modes: list[str] = []
        self.cwds: list[str] = []
        self.resource_updates: list[dict[str, Any]] = []
        self.tool_resolutions: list[tuple[str, bool, str]] = []

    async def set_profile(self, profile: ModelEffortProfile) -> None:
        self.profiles.append(profile)
        _logger().info(
            "model.profile_changed",
            model=profile.model,
            effort=profile.effort,
            preset=profile.preset,
        )

    async def set_permission_mode(self, mode: str) -> None:
        self.permission_modes.append(mode)

    async def set_cwd(self, cwd: str) -> None:
        self.cwds.append(cwd)

    async def set_session_resources(self, **kwargs: Any) -> None:
        self.resource_updates.append(dict(kwargs))

    def resolve_tool_approval(self, request_id: str, *, allow: bool, reason: str = "") -> bool:
        self.tool_resolutions.append((request_id, allow, reason))
        return True

    async def send_turn(self, prompt_text: str) -> TurnOutcome:
        self.sent_prompts.append(prompt_text)
        if not self._script:
            raise IndexError(
                f"ScriptedAgentGateway: no turns left in script (prompt={prompt_text!r})"
            )
        turn = self._script.pop(0)
        if self._on_event is not None:
            for event in turn.raw_events:
                self._on_event(dict(event))
        return TurnOutcome(
            signals=turn.signals,
            verdict=turn.verdict,
            output_text=turn.output_text,
            session_id=turn.session_id,
            cost_usd=turn.cost_usd,
            raw_events=turn.raw_events,
        )

    async def close(self) -> None:
        self.closed = True


class ScriptedCapacityProbe:
    def __init__(self, script: list[TurnSignals]) -> None:
        self._script = list(script)

    async def probe(self) -> TurnOutcome:
        if not self._script:
            raise IndexError("ScriptedCapacityProbe: no probes left in script")
        signals = self._script.pop(0)
        return TurnOutcome(signals=signals, verdict=None, output_text="", session_id=None)


def load_agent_script(path: Path | str) -> AgentScript:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("agent script root must be a JSON object")
    probes_raw = raw.get("probes", [{"signals": {}}])
    turns_raw = raw.get("turns", [])
    if not isinstance(probes_raw, list) or not isinstance(turns_raw, list):
        raise ValueError("agent script 'probes' and 'turns' must be arrays")
    if not turns_raw:
        raise ValueError("agent script must include at least one turn")
    probes = tuple(_parse_signals(item) for item in probes_raw)
    turns = tuple(_parse_turn(item) for item in turns_raw)
    return AgentScript(probes=probes, turns=turns)


def resolve_test_agent_from_env(
    *,
    on_event: OnEvent | None = None,
) -> tuple[ScriptedAgentGateway, ScriptedCapacityProbe] | None:
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
    _logger().warning(
        "test_agent.loading",
        script=script_path,
        detail="test-only scripted agent — not for production",
    )
    script = load_agent_script(script_path)
    gateway = ScriptedAgentGateway(list(script.turns), on_event=on_event)
    probe = ScriptedCapacityProbe(list(script.probes))
    return gateway, probe


def _parse_turn(item: object) -> ScriptedTurn:
    if not isinstance(item, dict):
        raise ValueError("each turn must be a JSON object")
    signals = _parse_signals(item.get("signals", {}))
    verdict_raw = item.get("verdict")
    verdict = _parse_verdict(verdict_raw) if verdict_raw is not None else None
    raw_events_raw = item.get("raw_events", [])
    if not isinstance(raw_events_raw, list):
        raise ValueError("raw_events must be an array")
    raw_events = tuple(
        {str(k): v for k, v in event.items()} for event in raw_events_raw if isinstance(event, dict)
    )
    return ScriptedTurn(
        signals=signals,
        verdict=verdict,
        output_text=str(item.get("output_text", "")),
        session_id=str(item.get("session_id", "scripted-session")),
        cost_usd=float(item.get("cost_usd", 0.0)),
        raw_events=raw_events,
    )


def _parse_signals(item: object) -> TurnSignals:
    if isinstance(item, dict) and "signals" in item and len(item) == 1:
        item = item["signals"]
    if not isinstance(item, dict):
        raise ValueError("signals must be a JSON object")
    data: dict[str, Any] = dict(item)
    for key in ("resets_at", "overage_resets_at"):
        if key in data and isinstance(data[key], str):
            data[key] = datetime.fromisoformat(data[key].replace("Z", "+00:00"))
    known = {f.name for f in fields(TurnSignals)}
    filtered = {k: v for k, v in data.items() if k in known}
    return TurnSignals(**filtered)


def _parse_verdict(item: object) -> StructuredVerdict:
    if not isinstance(item, dict):
        raise ValueError("verdict must be a JSON object")
    remaining = item.get("remaining_work", ())
    remaining_t = tuple(str(x) for x in remaining) if isinstance(remaining, list) else ()
    blocked = item.get("blocked_on")
    return StructuredVerdict(
        complete=bool(item.get("complete", False)),
        remaining_work=remaining_t,
        blocked_on=None if blocked is None else str(blocked),
        summary=str(item.get("summary", "")),
    )
