# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Real fakes (not unittest.mock.Mock) implementing application/ports.py's
Protocols, so mypy --strict checks them against the port shape and no test
ever calls time.sleep() for real. See docs/contributing/testing.md."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any

from claudeloop.application.dto import TurnOutcome
from claudeloop.domain.classify import TurnSignals
from claudeloop.domain.completion import StructuredVerdict
from claudeloop.domain.control import ControlCommand
from claudeloop.domain.savepoint import SavePointRef, UnwindResult
from claudeloop.domain.snapshot import SnapshotReason, SnapshotRef


class FakeClock:
    def __init__(self, start: datetime) -> None:
        self._now = start

    def now(self) -> datetime:
        return self._now

    def advance_to(self, instant: datetime) -> None:
        self._now = instant


class FakeSleeper:
    """sleep_until() jumps the paired FakeClock straight to the target
    instant instead of blocking — this is what lets a test simulate a
    multi-day wait in microseconds of real wall-clock time."""

    def __init__(self, clock: FakeClock) -> None:
        self._clock = clock
        self.wait_log: list[datetime] = []

    async def sleep_until(self, instant: datetime) -> None:
        self.wait_log.append(instant)
        self._clock.advance_to(instant)


@dataclass(frozen=True, slots=True)
class ScriptedTurn:
    signals: TurnSignals = field(default_factory=TurnSignals)
    verdict: StructuredVerdict | None = None
    output_text: str = ""
    session_id: str | None = "fake-session-id"
    cost_usd: float = 0.0
    raw_events: tuple[dict[str, object], ...] = ()


class FakeAgentGateway:
    """Replays a scripted sequence of TurnOutcomes, one per send_turn() call.
    Raises IndexError (a clear test failure) if more turns are requested than
    were scripted — a runaway loop should fail loudly, not hang."""

    def __init__(self, script: list[ScriptedTurn]) -> None:
        self._script = list(script)
        self.sent_prompts: list[str] = []
        self.closed = False
        self.profiles: list[Any] = []
        self.permission_modes: list[str] = []
        self.cwds: list[str] = []
        self.resource_updates: list[dict[str, Any]] = []
        self.tool_resolutions: list[tuple[str, bool, str]] = []

    async def set_profile(self, profile: Any) -> None:
        self.profiles.append(profile)

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
        turn = self._script.pop(0)
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


class FakeCapacityProbe:
    """Replays a scripted sequence of TurnSignals, one per probe() call —
    including the preflight call, which is always the first one consumed."""

    def __init__(self, script: list[TurnSignals]) -> None:
        self._script = list(script)
        self.models: list[str] = []

    def set_model(self, model: str) -> None:
        """Mirror AgentCapacityProbe.set_model so profile changes stay sticky."""
        self.models.append(model)

    async def probe(self) -> TurnOutcome:
        signals = self._script.pop(0)
        return TurnOutcome(signals=signals, verdict=None, output_text="", session_id=None)


class FakeAuditLog:
    def __init__(self) -> None:
        self.events: list[tuple[str, dict[str, object]]] = []

    def record(self, event_type: str, payload: dict[str, object]) -> None:
        self.events.append((event_type, payload))


class FakeProgressReporter:
    def __init__(self) -> None:
        self.turns: list[int] = []
        self.waits: list[tuple[str, datetime]] = []
        self.finishes: list[tuple[bool, str]] = []

    def turn_sent(self, *, attempt: int) -> None:
        self.turns.append(attempt)

    def waiting(self, *, reason: str, until: datetime) -> None:
        self.waits.append((reason, until))

    def finished(self, *, success: bool, reason: str) -> None:
        self.finishes.append((success, reason))


class FakeNotifier:
    def __init__(self) -> None:
        self.messages: list[str] = []

    def notify(self, message: str) -> None:
        self.messages.append(message)


class FakeLogger:
    def __init__(self) -> None:
        self.events: list[tuple[str, str, dict[str, Any]]] = []

    def bind(self, **kwargs: Any) -> FakeLogger:
        child = FakeLogger()
        child.events = self.events
        child._bound = {**getattr(self, "_bound", {}), **kwargs}
        return child

    def debug(self, event: str, **kwargs: Any) -> None:
        self.events.append(("debug", event, kwargs))

    def info(self, event: str, **kwargs: Any) -> None:
        self.events.append(("info", event, kwargs))

    def warning(self, event: str, **kwargs: Any) -> None:
        self.events.append(("warning", event, kwargs))

    def error(self, event: str, **kwargs: Any) -> None:
        self.events.append(("error", event, kwargs))


class FakeRunControl:
    def __init__(self, script: list[list[ControlCommand]] | None = None) -> None:
        self._script = list(script or [])
        self.polls = 0

    def poll(self) -> list[ControlCommand]:
        self.polls += 1
        if self._script:
            return self._script.pop(0)
        return []


class FakeEventSink:
    def __init__(self) -> None:
        self.events: list[tuple[str, dict[str, object] | None]] = []

    def emit(self, event_type: str, payload: dict[str, object] | None = None) -> None:
        self.events.append((event_type, payload))

    def bind(
        self,
        *,
        session_id: str | None = None,
        attempt: int | None = None,
        phase: str | None = None,
        trace_id: str | None = None,
        turn_id: str | None = None,
    ) -> None:
        del session_id, attempt, phase, trace_id, turn_id


class FakeStateStore:
    def __init__(self) -> None:
        self.saved: dict[str, dict[str, Any]] = {}

    def save(self, run_id: str, state: dict[str, Any]) -> None:
        self.saved[run_id] = state

    def load(self, run_id: str) -> dict[str, Any] | None:
        return self.saved.get(run_id)


class FakeSessionLock:
    def __init__(self) -> None:
        self.held: set[str] = set()

    def acquire(self, session_id: str) -> bool:
        if session_id in self.held:
            return False
        self.held.add(session_id)
        return True

    def release(self, session_id: str) -> None:
        self.held.discard(session_id)


class FakeSavePointStore:
    def __init__(self, *, reuse_sha: bool = False) -> None:
        self.points: list[SavePointRef] = []
        self.unwinds: list[tuple[str, str, bool]] = []
        self._reuse_sha = reuse_sha

    def create(
        self,
        *,
        run_id: str,
        label: str,
        message: str = "",
        attempt: int | None = None,
        verdict_name: str = "Continue",
        summary: str = "",
        remaining_work: tuple[str, ...] = (),
    ) -> SavePointRef:
        del message, attempt, verdict_name, summary, remaining_work
        n = len(self.points) + 1
        if self._reuse_sha:
            # Simulate an unchanged tree (ref-only) from the first savepoint onward.
            sha = self.points[-1].sha if self.points else ("b" * 40)
            committed = False
        else:
            sha = f"{'a' * 39}{n}"
            committed = True
        point = SavePointRef(
            n=n,
            ref=f"refs/claudeloop/{run_id}/{n}",
            sha=sha,
            label=label,
            at=datetime(2026, 8, 12, tzinfo=timezone.utc),
            committed=committed,
        )
        self.points.append(point)
        return point

    def list_points(self, run_id: str) -> list[SavePointRef]:
        del run_id
        return list(self.points)

    def unwind(self, *, run_id: str, to: str, backup: bool) -> UnwindResult:
        self.unwinds.append((run_id, to, backup))
        target = self.points[int(to) - 1] if to.isdigit() else self.points[-1]
        return UnwindResult(to=target, backup_ref="refs/backup", restored_sha=target.sha)

    def changes_since(self, since_sha: str | None) -> str:
        del since_sha
        return "abc123 fake change"


class FakeSnapshotSink:
    def __init__(self) -> None:
        self.emits: list[tuple[SnapshotReason, dict[str, Any] | None, bool | None]] = []

    def emit(
        self,
        reason: SnapshotReason,
        *,
        context: dict[str, Any] | None = None,
        bundle: bool | None = None,
    ) -> SnapshotRef | None:
        self.emits.append((reason, context, bundle))
        return SnapshotRef(
            path=f"snapshots/{reason}.json",
            digest="0" * 64,
            reason=reason,
            immutable=reason != "status",
            bundle_path=None,
        )


def available_signals() -> TurnSignals:
    return TurnSignals()


def credits_exhausted_signals() -> TurnSignals:
    return TurnSignals(rate_limit_status="rejected", error_code="credits_required")


def window_exhausted_signals(*, resets_at: datetime | None = None) -> TurnSignals:
    return TurnSignals(
        rate_limit_status="rejected", rate_limit_type="five_hour", resets_at=resets_at
    )


DONE_VERDICT = StructuredVerdict(complete=True, summary="all done")
CONTINUE_VERDICT = StructuredVerdict(complete=False, remaining_work=("more work",))


def five_minutes(clock: FakeClock) -> datetime:
    return clock.now() + timedelta(minutes=5)
