# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Real fakes (not unittest.mock.Mock) implementing application/ports.py's
Protocols, so no test ever waits on a human or calls time.sleep() for real.
"""

from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from threading import Event
from typing import Any

from cursorloop.application.dto import TurnOutcome
from cursorloop.application.ports import (
    AgentGateway,
    AuditLog,
    CapacityProbe,
    Clock,
    HookManager,
    Logger,
    Notifier,
    ProgressReporter,
    RunControl,
    RunStateStore,
    Sleeper,
)
from cursorloop.application.runner import AutonomousRunner, RunnerContext
from cursorloop.domain.budget import Budget
from cursorloop.domain.capacity import (
    AuthenticationFailed,
    Available,
    CapacityState,
    CreditsExhausted,
    WindowExhausted,
)
from cursorloop.domain.classify import TurnSignals
from cursorloop.domain.completion import StructuredVerdict
from cursorloop.domain.control import ControlCommand
from cursorloop.domain.faults import Busy, ConfigFault, Fault, TransientFault
from cursorloop.domain.forecast import WindDownPolicy
from cursorloop.domain.model_profile import ModelProfile
from cursorloop.domain.plan import WorkPlan
from cursorloop.domain.waiting import DEFAULT_PROGRESS_WAIT_CONFIG, DEFAULT_WAIT_POLICY_CONFIG

_DEFAULT_START = datetime(2026, 8, 13, 12, 0, tzinfo=UTC)


class FakeClock:
    """Settable, monotonic clock. Refuses to run backwards."""

    def __init__(self, start: datetime | None = None) -> None:
        self._now = start if start is not None else _DEFAULT_START

    def now(self) -> datetime:
        return self._now

    def advance_to(self, instant: datetime) -> None:
        if instant < self._now:
            raise ValueError("FakeClock is monotonic")
        self._now = instant

    def advance(self, delta: timedelta) -> None:
        """Advance by a timedelta. Refuses to run backwards (negative delta)."""
        self.advance_to(self._now + delta)


class FakeSleeper:
    """sleep_until() jumps the paired FakeClock to the target instant.

    Never calls a real sleep primitive — a simulated seven-day wait runs in
    microseconds of wall-clock time.
    """

    def __init__(self, clock: FakeClock) -> None:
        self._clock = clock
        self.total_simulated_seconds = 0.0
        self.real_sleep_calls = 0
        self.wait_log: list[datetime] = []

    async def sleep_until(self, instant: datetime) -> None:
        self.wait_log.append(instant)
        current = self._clock.now()
        delta = (instant - current).total_seconds()
        if delta <= 0:
            return
        self.total_simulated_seconds += delta
        self._clock.advance_to(instant)


class FakeRun:
    """Synthetic Run handle for the stall watchdog. Not unittest.mock.

    ``block_until_cancel=True`` makes ``messages()`` wait until ``cancel()``,
    so a hung stream is testable without a live SDK.
    """

    def __init__(self, status: str = "running", *, block_until_cancel: bool = False) -> None:
        self.status = status
        self.cancel_calls = 0
        self._block_until_cancel = block_until_cancel
        self._released = Event()
        self.block_entered = Event()
        if not block_until_cancel:
            self._released.set()

    def cancel(self) -> None:
        self.cancel_calls += 1
        if self.status == "running":
            self.status = "cancelled"
        self._released.set()

    def messages(self) -> Iterator[object]:
        if self._block_until_cancel:
            self.block_entered.set()
            self._released.wait()
        yield from ()

    def wait(self) -> FakeRun:
        if self._block_until_cancel:
            self.block_entered.set()
            self._released.wait()
        return self


class FakeAgentGateway:
    """Replays a scripted list of TurnOutcome, one per send_turn() call.

    Raises IndexError if more turns are requested than were scripted — a
    runaway loop should fail loudly, not hang.
    """

    def __init__(self, script: list[TurnOutcome], *, agent_id: str = "fake-agent") -> None:
        self._script = list(script)
        self._agent_id = agent_id
        self.sent_prompts: list[str] = []
        self.force_flags: list[bool] = []
        self.profiles: list[ModelProfile] = []
        self.cwds: list[str] = []
        self.closed = False
        self.cancel_calls = 0
        self.send_calls = 0

    async def send_turn(self, prompt_text: str, *, force: bool = False) -> TurnOutcome:
        self.sent_prompts.append(prompt_text)
        self.force_flags.append(force)
        self.send_calls += 1
        return self._script.pop(0)

    async def close(self) -> None:
        self.closed = True

    async def set_profile(self, profile: ModelProfile) -> None:
        self.profiles.append(profile)

    async def set_cwd(self, cwd: str) -> None:
        self.cwds.append(cwd)

    async def cancel_active_run(self) -> bool:
        self.cancel_calls += 1
        return True

    def agent_id(self) -> str:
        return self._agent_id


class FakeCapacityProbe:
    """Replays a scripted list of TurnSignals, one per probe() call."""

    def __init__(self, script: list[TurnSignals]) -> None:
        self._script = list(script)
        self.calls = 0

    async def probe(self) -> TurnOutcome:
        self.calls += 1
        signals = self._script.pop(0)
        return TurnOutcome(
            signals=signals,
            verdict=None,
            output_text="",
            cost_usd=None,
            cost_pending=True,
        )


class FakeHookManager:
    def __init__(self) -> None:
        self._installed = False
        self._restored_after_install = False

    def install(self) -> None:
        self._installed = True
        self._restored_after_install = False

    def restore(self) -> bool:
        if not self._installed:
            return False
        self._installed = False
        self._restored_after_install = True
        return True

    def is_installed(self) -> bool:
        return self._installed

    @property
    def installed_then_restored(self) -> bool:
        return self._restored_after_install


class FakeNotifier:
    def __init__(self) -> None:
        self.messages: list[str] = []

    def notify(self, message: str) -> None:
        self.messages.append(message)


class FakeAuditLog:
    def __init__(self) -> None:
        self.events: list[tuple[str, dict[str, Any]]] = []

    def record(self, event_type: str, payload: dict[str, Any]) -> None:
        self.events.append((event_type, payload))


class FakeRunStateStore:
    def __init__(self) -> None:
        self.saved: dict[str, dict[str, Any]] = {}

    def save(self, run_id: str, state: dict[str, Any]) -> None:
        self.saved[run_id] = dict(state)

    def load(self, run_id: str) -> dict[str, Any] | None:
        return self.saved.get(run_id)


class FakeAgentLock:
    def __init__(self) -> None:
        self.held: set[str] = set()

    def acquire(self, agent_id: str) -> bool:
        if agent_id in self.held:
            return False
        self.held.add(agent_id)
        return True

    def release(self, agent_id: str) -> None:
        self.held.discard(agent_id)


class FakeUsageReader:
    """``billed_cost_usd`` defaults to None — unknown, never zero."""

    def __init__(self, *, tokens: int = 0, billed_cost_usd: float | None = None) -> None:
        self._tokens = tokens
        self._billed_cost_usd = billed_cost_usd

    async def turn_tokens(self, run_id: str) -> int:
        del run_id
        return self._tokens

    async def billed_cost_usd(self) -> float | None:
        return self._billed_cost_usd


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


class FakeLogger:
    def __init__(self) -> None:
        self.events: list[tuple[str, str, dict[str, Any]]] = []

    def bind(self, **kwargs: Any) -> FakeLogger:
        del kwargs
        return self

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


def signals_for(capacity_or_fault: CapacityState | Fault) -> TurnSignals:
    """TurnSignals that ``classify()`` maps to the given ADT."""
    if isinstance(capacity_or_fault, CreditsExhausted):
        return TurnSignals(http_status=402)
    if isinstance(capacity_or_fault, Available):
        return TurnSignals(run_status="finished")
    if isinstance(capacity_or_fault, WindowExhausted):
        retry_after = None if capacity_or_fault.resets_at is None else "60"
        return TurnSignals(
            error_type="RateLimitError",
            is_retryable=True,
            retry_after=retry_after,
            http_status=429,
        )
    if isinstance(capacity_or_fault, AuthenticationFailed):
        return TurnSignals(
            error_type="AuthenticationError",
            error_message=capacity_or_fault.detail,
            http_status=401,
        )
    if isinstance(capacity_or_fault, Busy):
        return TurnSignals(error_type="AgentBusyError")
    if isinstance(capacity_or_fault, TransientFault):
        return TurnSignals(error_type="NetworkError", is_retryable=True)
    if isinstance(capacity_or_fault, ConfigFault):
        return TurnSignals(error_type="ConfigurationError", error_message=capacity_or_fault.detail)
    raise TypeError(f"unsupported capacity/fault: {type(capacity_or_fault)!r}")


def turn(
    *,
    capacity: CapacityState | Fault | None = None,
    done: bool = False,
    summary: str = "",
    remaining_work: tuple[str, ...] = (),
    blocked_on: str | None = None,
    output_text: str = "",
    tokens: int = 0,
    cost_usd: float | None = None,
) -> TurnOutcome:
    """Scripted TurnOutcome whose signals/verdict match the requested ADT."""
    signals = signals_for(capacity) if capacity is not None else signals_for(Available())
    verdict: StructuredVerdict | None = None
    if done:
        verdict = StructuredVerdict(complete=True, summary=summary, remaining_work=remaining_work)
        if not output_text:
            output_text = summary
    elif blocked_on is not None:
        verdict = StructuredVerdict(complete=False, blocked_on=blocked_on, summary=summary)
        if not output_text:
            output_text = blocked_on
    elif remaining_work:
        verdict = StructuredVerdict(complete=False, remaining_work=remaining_work, summary=summary)
    pending = cost_usd is None
    return TurnOutcome(
        signals=signals,
        verdict=verdict,
        output_text=output_text,
        tokens=tokens,
        cost_usd=cost_usd,
        cost_pending=pending,
    )


def busy_turn() -> TurnOutcome:
    return turn(capacity=Busy(agent_id="", active_run_id=None))


def transient_turn() -> TurnOutcome:
    return turn(capacity=TransientFault(kind="network", attempt_hint=1))


def blocked_turn(reason: str) -> TurnOutcome:
    return turn(blocked_on=reason)


def config_fault_turn(detail: str = "unknown model") -> TurnOutcome:
    return turn(capacity=ConfigFault(detail=detail))


def _available_script(n: int = 32) -> list[TurnSignals]:
    return [signals_for(Available())] * n


def build_runner(
    *,
    gateway: AgentGateway | None = None,
    probe: CapacityProbe | None = None,
    clock: Clock | None = None,
    sleeper: Sleeper | None = None,
    reporter: ProgressReporter | None = None,
    audit: AuditLog | None = None,
    notifier: Notifier | None = None,
    logger: Logger | None = None,
    hooks: HookManager | None = None,
    lock: FakeAgentLock | None = None,
    store: RunStateStore | None = None,
    control: RunControl | None = None,
    max_transient_retries: int = 8,
    run_id: str = "test-run",
    plan: WorkPlan | None = None,
    budget: Budget | None = None,
    continue_prompt: str = "Continue exactly where you left off.",
    handoff_marker_writer: object | None = None,
    wind_down_policy: WindDownPolicy | None = None,
) -> AutonomousRunner:
    """Wire an AutonomousRunner with fakes for every port it needs."""
    clock = clock if clock is not None else FakeClock()
    sleeper = sleeper if sleeper is not None else FakeSleeper(clock)  # type: ignore[arg-type]
    ctx = RunnerContext(
        gateway=gateway
        if gateway is not None
        else FakeAgentGateway([turn(done=True, summary="finished")]),
        probe=probe if probe is not None else FakeCapacityProbe(_available_script()),
        clock=clock,
        sleeper=sleeper,
        reporter=reporter if reporter is not None else FakeProgressReporter(),
        audit=audit if audit is not None else FakeAuditLog(),
        notifier=notifier if notifier is not None else FakeNotifier(),
        logger=logger if logger is not None else FakeLogger(),
        hooks=hooks if hooks is not None else FakeHookManager(),
        lock=lock if lock is not None else FakeAgentLock(),
        store=store if store is not None else FakeRunStateStore(),
        control=control if control is not None else FakeRunControl(),
        budget=budget if budget is not None else Budget(),
        wait_policy=DEFAULT_WAIT_POLICY_CONFIG,
        progress_wait=DEFAULT_PROGRESS_WAIT_CONFIG,
        max_transient_retries=max_transient_retries,
        run_id=run_id,
        plan=plan,
        continue_prompt=continue_prompt,
        handoff_marker_writer=handoff_marker_writer,  # type: ignore[arg-type]
        wind_down_policy=wind_down_policy or WindDownPolicy(),
    )
    return AutonomousRunner(ctx)
