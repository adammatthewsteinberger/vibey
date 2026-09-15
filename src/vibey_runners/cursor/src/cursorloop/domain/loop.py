# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""The autonomous run loop's pure state machine.

``application.runner`` executes the Decisions this module produces against real
ports (agent gateway, clock, sleeper, ...). Nothing here performs I/O; every
transition is a function of (RunState, an event, now).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum, auto

from cursorloop.domain.budget import BudgetLedger
from cursorloop.domain.capacity import (
    AuthenticationFailed,
    Available,
    CapacityState,
    CreditsExhausted,
    WindowExhausted,
)
from cursorloop.domain.completion import Blocked, CompletionVerdict, Continue, Done
from cursorloop.domain.forecast import CapacityForecast, WindDown
from cursorloop.domain.waiting import (
    DEFAULT_PROGRESS_WAIT_CONFIG,
    DEFAULT_WAIT_POLICY_CONFIG,
    ProgressWaitConfig,
    WaitPolicyConfig,
    is_wait_only_remaining_work,
    next_probe_instant,
    next_progress_wait_instant,
    wait_exceeded,
)


class Phase(Enum):
    PREFLIGHT = auto()
    RUNNING = auto()
    WAITING = auto()
    PROBING = auto()
    COMPLETE = auto()
    FAILED = auto()
    HANDOFF = auto()


@dataclass(frozen=True, slots=True)
class RunState:
    phase: Phase
    ledger: BudgetLedger
    started_waiting_at: datetime | None = None
    probe_count: int = 0
    failure_reason: str | None = None


@dataclass(frozen=True, slots=True)
class SendTurn:
    """Spend a real turn against the live session."""


@dataclass(frozen=True, slots=True)
class RunProbe:
    """Spend a cheap, throwaway turn purely to re-check capacity."""


@dataclass(frozen=True, slots=True)
class ScheduleProbe:
    at: datetime


@dataclass(frozen=True, slots=True)
class Finish:
    success: bool
    reason: str = ""


@dataclass(frozen=True, slots=True)
class DelayThenSend:
    """Wait until ``at`` (interruptible) then spend another real turn."""

    at: datetime


@dataclass(frozen=True, slots=True)
class WindDownAndFinish:
    """Stop cleanly *before* capacity runs out, so the handoff artifacts can
    still be produced with room to spare.

    Distinct from Finish: the work is not done and not blocked, it is being
    handed over. A supervisor reads this as "resume me elsewhere", not "this
    failed".
    """

    reason: str
    forecast: CapacityForecast


Decision = SendTurn | RunProbe | ScheduleProbe | DelayThenSend | WindDownAndFinish | Finish


def decide_progress_delay(
    *,
    verdict: Continue,
    tree_changed: bool,
    now: datetime,
    streak: int,
    config: ProgressWaitConfig = DEFAULT_PROGRESS_WAIT_CONFIG,
) -> DelayThenSend | None:
    """When remaining_work is wait-only and the tree did not change, back off."""
    if tree_changed or not is_wait_only_remaining_work(verdict.remaining_work):
        return None
    return DelayThenSend(at=next_progress_wait_instant(now=now, streak=streak, config=config))


def start(ledger: BudgetLedger) -> RunState:
    return RunState(phase=Phase.PREFLIGHT, ledger=ledger)


def decide_preflight(
    state: RunState,
    capacity: CapacityState,
    *,
    now: datetime,
    config: WaitPolicyConfig = DEFAULT_WAIT_POLICY_CONFIG,
) -> tuple[RunState, Decision]:
    """The very first thing a run does: check whether we're already mid-cooldown
    before spending a real attempt."""
    if isinstance(capacity, AuthenticationFailed):
        return _fail(state, "authentication failed"), Finish(
            success=False, reason="authentication failed"
        )
    if isinstance(capacity, Available):
        return RunState(phase=Phase.RUNNING, ledger=state.ledger), SendTurn()
    return _enter_waiting(state, capacity, now=now, config=config)


def decide_after_turn(
    state: RunState,
    *,
    capacity: CapacityState,
    verdict: CompletionVerdict,
    now: datetime,
    config: WaitPolicyConfig = DEFAULT_WAIT_POLICY_CONFIG,
    tokens: int = 0,
    dollars: float | None = None,
    started_at: datetime | None = None,
    wind_down: WindDown | None = None,
) -> tuple[RunState, Decision]:
    """Called once a real turn has completed. A capacity rejection always outranks a
    completion claim — a limit message truncating mid-response could coincidentally
    contain marker-like text, but hitting a real limit is never "done"."""
    new_ledger = state.ledger.spend_turn(tokens, dollars)

    if isinstance(capacity, AuthenticationFailed):
        return _fail(state, "authentication failed"), Finish(
            success=False, reason="authentication failed"
        )

    # Capacity is checked BEFORE the verdict. NEVER reorder this relative to
    # the Done/Blocked/Continue branches — see
    # test_after_turn_limit_outranks_completion_claim. A truncated limit
    # message can coincidentally contain marker-like text; hitting a real
    # limit is never "done".
    if not isinstance(capacity, Available):
        return _enter_waiting(
            RunState(phase=state.phase, ledger=new_ledger),
            capacity,
            now=now,
            config=config,
            started_at=started_at,
        )

    if isinstance(verdict, Done):
        return (
            RunState(phase=Phase.COMPLETE, ledger=new_ledger),
            Finish(success=True, reason=verdict.summary),
        )
    if isinstance(verdict, Blocked):
        return (
            RunState(phase=Phase.FAILED, ledger=new_ledger, failure_reason=verdict.reason),
            Finish(success=False, reason=verdict.reason),
        )
    # Precondition, not a security gate: CompletionVerdict is the closed union
    # {Done, Blocked, Continue} and both other members are handled above, so this
    # is exhaustive by construction — asserted here to fail loudly if a future
    # variant is added to the union without a matching branch here.
    assert isinstance(verdict, Continue)  # nosec B101

    running = RunState(phase=Phase.RUNNING, ledger=new_ledger)
    if _budget_exhausted(new_ledger, now=now, started_at=started_at):
        return _fail(running, "budget exhausted"), Finish(success=False, reason="budget exhausted")
    if wind_down is not None:
        return (
            RunState(phase=Phase.HANDOFF, ledger=new_ledger),
            WindDownAndFinish(reason=wind_down.reason, forecast=wind_down.forecast),
        )
    return running, SendTurn()


def decide_after_probe(
    state: RunState,
    capacity: CapacityState,
    *,
    now: datetime,
    config: WaitPolicyConfig = DEFAULT_WAIT_POLICY_CONFIG,
    started_at: datetime | None = None,
) -> tuple[RunState, Decision]:
    """Called once a throwaway probe turn has completed while waiting."""
    if isinstance(capacity, AuthenticationFailed):
        return _fail(state, "authentication failed"), Finish(
            success=False, reason="authentication failed"
        )
    if isinstance(capacity, Available):
        running = RunState(phase=Phase.RUNNING, ledger=state.ledger)
        if _budget_exhausted(state.ledger, now=now, started_at=started_at):
            return _fail(running, "budget exhausted"), Finish(
                success=False, reason="budget exhausted"
            )
        return running, SendTurn()
    return _enter_waiting(
        state, capacity, now=now, config=config, is_reprobe=True, started_at=started_at
    )


def _budget_exhausted(ledger: BudgetLedger, *, now: datetime, started_at: datetime | None) -> bool:
    if ledger.any_exhausted:
        return True
    if started_at is None:
        return False
    return ledger.wall_clock_exhausted(now=now, started_at=started_at)


def _enter_waiting(
    state: RunState,
    capacity: CapacityState,
    *,
    now: datetime,
    config: WaitPolicyConfig = DEFAULT_WAIT_POLICY_CONFIG,
    is_reprobe: bool = False,
    started_at: datetime | None = None,
) -> tuple[RunState, Decision]:
    # Precondition, not a security gate: every caller (decide_preflight,
    # decide_after_turn, decide_after_probe) only reaches _enter_waiting after
    # excluding Available and AuthenticationFailed, so this is exhaustive by
    # construction — asserted here to fail loudly if a future caller breaks that.
    assert isinstance(capacity, (WindowExhausted, CreditsExhausted))  # nosec B101
    started = state.started_waiting_at if is_reprobe and state.started_waiting_at else now
    probe_count = state.probe_count + 1 if is_reprobe else 0

    if _budget_exhausted(state.ledger, now=now, started_at=started_at):
        return _fail(state, "budget exhausted"), Finish(success=False, reason="budget exhausted")

    if wait_exceeded(started_waiting_at=started, now=now, config=config):
        failed = RunState(
            phase=Phase.FAILED,
            ledger=state.ledger,
            started_waiting_at=started,
            probe_count=probe_count,
            failure_reason="max wait exceeded",
        )
        return failed, Finish(success=False, reason="max wait exceeded")

    at = next_probe_instant(
        capacity, now=now, started_waiting_at=started, probe_count=probe_count, config=config
    )
    waiting = RunState(
        phase=Phase.WAITING,
        ledger=state.ledger,
        started_waiting_at=started,
        probe_count=probe_count,
    )
    return waiting, ScheduleProbe(at=at)


def _fail(state: RunState, reason: str) -> RunState:
    return RunState(phase=Phase.FAILED, ledger=state.ledger, failure_reason=reason)
