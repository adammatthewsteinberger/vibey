# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Fakes implementing application ports. Never wall-clock sleep."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from datetime import datetime, timedelta

from codexloop.application.dto import ProbeResult, TurnOutcome
from codexloop.application.ports import Logger, PermissionMode
from codexloop.domain.capacity import Available
from codexloop.domain.control import ControlCommand
from codexloop.domain.model_profile import ModelEffortProfile
from codexloop.domain.session import ThreadRef


class FakeClock:
    def __init__(self, now: datetime) -> None:
        self._now = now

    def now(self) -> datetime:
        return self._now

    def advance(self, delta: timedelta) -> None:
        self._now = self._now + delta


class FakeSleeper:
    """Jump the paired FakeClock to ``when`` instead of blocking."""

    def __init__(self, clock: FakeClock, *, call_log: list[str] | None = None) -> None:
        self._clock = clock
        self._call_log = call_log
        self.requested: list[datetime] = []

    async def sleep_until(self, when: datetime) -> None:
        self.requested.append(when)
        if self._call_log is not None:
            self._call_log.append("sleep_until")
        current = self._clock.now()
        if when > current:
            self._clock.advance(when - current)


class FakeAgentGateway:
    def __init__(
        self,
        outcomes: Sequence[TurnOutcome] | None = None,
        *,
        clock: FakeClock | None = None,
        turn_elapsed: timedelta | None = None,
        call_log: list[str] | None = None,
    ) -> None:
        self._outcomes = None if outcomes is None else list(outcomes)
        self._index = 0
        self._clock = clock
        self._turn_elapsed = turn_elapsed
        self._call_log = call_log
        self.sent_prompts: list[str] = []
        self.closed = False
        self.profiles: list[ModelEffortProfile] = []
        self.permission_modes: list[PermissionMode] = []
        self.cwds: list[str] = []
        self.resource_updates: list[Mapping[str, object]] = []
        self.tool_resolutions: list[tuple[str, bool, str]] = []

    async def send_turn(self, prompt: str) -> TurnOutcome:
        self.sent_prompts.append(prompt)
        if self._call_log is not None:
            self._call_log.append("send_turn")
        if self._clock is not None and self._turn_elapsed is not None:
            self._clock.advance(self._turn_elapsed)
        if self._outcomes is None:
            return TurnOutcome()
        if self._index >= len(self._outcomes):
            raise AssertionError("FakeAgentGateway: no more scripted turns")
        outcome = self._outcomes[self._index]
        self._index += 1
        return outcome

    async def close(self) -> None:
        self.closed = True
        if self._call_log is not None:
            self._call_log.append("close")

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


class FakeCapacityProbe:
    def __init__(
        self,
        result: ProbeResult | Sequence[ProbeResult] | None = None,
        *,
        call_log: list[str] | None = None,
    ) -> None:
        self.calls = 0
        self._call_log = call_log
        if result is None:
            self._results = [ProbeResult(outcome=Available())]
        elif isinstance(result, ProbeResult):
            self._results = [result]
        else:
            self._results = list(result)

    async def probe(self) -> ProbeResult:
        self.calls += 1
        if self._call_log is not None:
            self._call_log.append("probe")
        index = min(self.calls - 1, len(self._results) - 1)
        return self._results[index]


class FakeThreadCatalog:
    def __init__(self) -> None:
        self._threads: dict[str, ThreadRef] = {}

    def list_threads(self) -> Sequence[ThreadRef]:
        return list(self._threads.values())

    def get(self, thread_id: str) -> ThreadRef | None:
        return self._threads.get(thread_id)

    def record(self, ref: ThreadRef) -> None:
        self._threads[ref.thread_id] = ref


class FakeProgressReporter:
    def __init__(self) -> None:
        self.events: list[tuple[str, dict[str, object]]] = []

    def report(self, event: str, **detail: object) -> None:
        self.events.append((event, dict(detail)))


class FakeAuditLog:
    def __init__(self) -> None:
        self.entries: list[tuple[str, Mapping[str, object]]] = []

    def append(self, event_type: str, payload: Mapping[str, object]) -> None:
        self.entries.append((event_type, payload))


class FakeNotifier:
    def __init__(self) -> None:
        self.messages: list[tuple[str, str]] = []

    def notify(self, title: str, body: str) -> None:
        self.messages.append((title, body))


class FakeLogger:
    def __init__(self) -> None:
        self.events: list[tuple[str, str, dict[str, object]]] = []
        self._bound: dict[str, object] = {}

    def bind(self, **kwargs: object) -> Logger:
        child = FakeLogger()
        child.events = self.events
        child._bound = {**self._bound, **kwargs}
        return child

    def debug(self, event: str, **kwargs: object) -> None:
        self.events.append(("debug", event, kwargs))

    def info(self, event: str, **kwargs: object) -> None:
        self.events.append(("info", event, dict(kwargs)))

    def warning(self, event: str, **kwargs: object) -> None:
        self.events.append(("warning", event, dict(kwargs)))

    def error(self, event: str, **kwargs: object) -> None:
        self.events.append(("error", event, dict(kwargs)))


class FakeRunStateStore:
    def __init__(self, *, call_log: list[str] | None = None) -> None:
        self._states: dict[str, dict[str, object]] = {}
        self._call_log = call_log
        self.saves: list[tuple[str, dict[str, object]]] = []

    def load(self, run_id: str) -> dict[str, object] | None:
        state = self._states.get(run_id)
        return None if state is None else dict(state)

    def save(self, run_id: str, state: Mapping[str, object]) -> None:
        snapshot = dict(state)
        self._states[run_id] = snapshot
        self.saves.append((run_id, snapshot))
        if self._call_log is not None:
            self._call_log.append("save")


class FakeSessionLock:
    def __init__(self) -> None:
        self.held: set[str] = set()

    def acquire(self, thread_id: str) -> bool:
        if thread_id in self.held:
            return False
        self.held.add(thread_id)
        return True

    def release(self, thread_id: str) -> None:
        self.held.discard(thread_id)


class FakeRunControl:
    def __init__(
        self,
        commands: Sequence[ControlCommand] | None = None,
        *,
        script: Sequence[Sequence[ControlCommand]] | None = None,
        call_log: list[str] | None = None,
    ) -> None:
        self._commands = list(commands or ())
        self._script = [list(batch) for batch in script] if script is not None else None
        self._call_log = call_log
        self.polls = 0

    def poll(self) -> Sequence[ControlCommand]:
        self.polls += 1
        if self._call_log is not None:
            self._call_log.append("poll")
        if self._script is not None:
            if self._script:
                return self._script.pop(0)
            return []
        pending, self._commands = self._commands, []
        return pending


class FakeRunEventSink:
    def __init__(self) -> None:
        self.events: list[Mapping[str, object]] = []

    def emit(self, event: Mapping[str, object]) -> None:
        self.events.append(event)


class FakeStateBus:
    def __init__(self) -> None:
        self.published: list[tuple[str, Mapping[str, object]]] = []
        self._subscribers: list[Callable[[str, Mapping[str, object]], None]] = []

    def publish(self, event_type: str, payload: Mapping[str, object]) -> None:
        self.published.append((event_type, payload))
        for callback in self._subscribers:
            callback(event_type, payload)

    def subscribe(self, callback: Callable[[str, Mapping[str, object]], None]) -> None:
        self._subscribers.append(callback)


class FakeSavePointStore:
    def __init__(self) -> None:
        self._points: dict[str, list[str]] = {}

    def create(self, run_id: str, label: str) -> str:
        point_id = f"{run_id}:{label}:{len(self._points.get(run_id, ()))}"
        self._points.setdefault(run_id, []).append(point_id)
        return point_id

    def list(self, run_id: str) -> Sequence[str]:
        return list(self._points.get(run_id, ()))

    def unwind(self, run_id: str, to: str) -> None:
        points = self._points.get(run_id, [])
        if to in points:
            self._points[run_id] = points[: points.index(to) + 1]


class FakeRunSnapshotSink:
    def __init__(self) -> None:
        self.snapshots: list[Mapping[str, object]] = []

    def write(self, snapshot: Mapping[str, object]) -> None:
        self.snapshots.append(snapshot)


class FakeApiGateway:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, object]]] = []

    def invoke(self, method_path: str, **kwargs: object) -> object:
        self.calls.append((method_path, dict(kwargs)))
        return None


class FakeRunResources:
    def __init__(self, payload: Mapping[str, object] | None = None) -> None:
        self._payload = dict(payload or {})

    def as_payload(self) -> Mapping[str, object]:
        return dict(self._payload)
