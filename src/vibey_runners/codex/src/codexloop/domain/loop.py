# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Pure run-loop state machine: (RunState, LoopOutcome, now) -> Decision."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from codexloop.domain.budget import BudgetLedger
from codexloop.domain.capacity import (
    AuthFailed,
    Available,
    CapacityState,
    QuotaExhausted,
    ThrottleExhausted,
    TransientBackendError,
    WindowExhausted,
)
from codexloop.domain.completion import Blocked, CompletionVerdict, Continue, Done
from codexloop.domain.control import ControlCommand, Stop
from codexloop.domain.forecast import CapacityForecast, WindDown


class RunState(StrEnum):
    Preflight = "Preflight"
    Running = "Running"
    Evaluating = "Evaluating"
    ThrottleBackoff = "ThrottleBackoff"
    Waiting = "Waiting"
    Probing = "Probing"
    Stopping = "Stopping"
    Complete = "Complete"
    Failed = "Failed"
    Handoff = "Handoff"


@dataclass(frozen=True, slots=True)
class SendTurn:
    pass


@dataclass(frozen=True, slots=True)
class Probe:
    pass


@dataclass(frozen=True, slots=True)
class WaitUntil:
    until: datetime


@dataclass(frozen=True, slots=True)
class BackoffUntil:
    until: datetime


@dataclass(frozen=True, slots=True)
class Finish:
    success: bool
    reason: str


@dataclass(frozen=True, slots=True)
class Drain:
    pass


@dataclass(frozen=True, slots=True)
class WindDownAndFinish:
    """Stop cleanly *before* capacity runs out, so the handoff artifacts can
    still be produced with room to spare.

    Distinct from Finish: the work is not done and not blocked, it is being
    handed over. A supervisor reads this as "resume me elsewhere".
    """

    reason: str
    forecast: CapacityForecast


Decision = SendTurn | Probe | WaitUntil | BackoffUntil | Finish | Drain | WindDownAndFinish

# Handoff is terminal for this process: the work continues elsewhere, so
# advancing out of it would restart a run that has already handed over.
_TERMINAL = frozenset({RunState.Complete, RunState.Failed, RunState.Handoff})
_DEADLINE_STATES = frozenset(
    {
        RunState.Preflight,
        RunState.Waiting,
        RunState.Probing,
        RunState.ThrottleBackoff,
    }
)
_WAKE_STATES = frozenset({RunState.Waiting, RunState.ThrottleBackoff})
_TURN_STATES = frozenset({RunState.Running, RunState.Evaluating})


@dataclass(frozen=True, slots=True)
class LoopOutcome:
    """Domain-side turn/probe result. Application TurnOutcome is not imported."""

    capacity: CapacityState
    completion: CompletionVerdict | None = None
    deadline_exceeded: bool = False
    wind_down: WindDown | None = None


class RunLoopStateMachine:
    """Total function over run state, capacity, completion, budget, and controls."""

    def advance(
        self,
        state: RunState,
        outcome: LoopOutcome,
        now: datetime,
        ledger: BudgetLedger,
        controls: Sequence[ControlCommand],
    ) -> tuple[RunState, Decision]:
        if state in _TERMINAL:
            return _stay_terminal(state)

        if state is RunState.Stopping:
            return RunState.Failed, Finish(success=False, reason="stop")

        if _has_stop(controls):
            return RunState.Stopping, Drain()

        if outcome.deadline_exceeded and state in _DEADLINE_STATES:
            return RunState.Failed, Finish(success=False, reason="max_wait")

        return _route_capacity(state, outcome, now, ledger)


def _stay_terminal(state: RunState) -> tuple[RunState, Decision]:
    if state is RunState.Complete:
        return RunState.Complete, Finish(success=True, reason="done")
    if state is RunState.Handoff:
        # Reported as a failure of *this* run, which is accurate: it did not
        # finish the work. The marker on disk is what says it can be resumed.
        return RunState.Handoff, Finish(success=False, reason="handoff")
    return RunState.Failed, Finish(success=False, reason="failed")


def _has_stop(controls: Sequence[ControlCommand]) -> bool:
    return any(isinstance(command, Stop) for command in controls)


def _route_capacity(
    state: RunState,
    outcome: LoopOutcome,
    now: datetime,
    ledger: BudgetLedger,
) -> tuple[RunState, Decision]:
    capacity = outcome.capacity
    if isinstance(capacity, AuthFailed):
        return RunState.Failed, Finish(success=False, reason="auth")

    if state in _WAKE_STATES:
        return RunState.Probing, Probe()

    if isinstance(capacity, ThrottleExhausted):
        return RunState.ThrottleBackoff, BackoffUntil(until=now)

    if isinstance(capacity, (WindowExhausted, QuotaExhausted, TransientBackendError)):
        return RunState.Waiting, WaitUntil(until=now)

    if isinstance(capacity, Available):
        return _route_available(state, outcome, ledger)

    # Closed-union exhaustiveness: CapacityState is a finite ADT. This assert is
    # a precondition on that union, not a security gate.
    assert False, f"unhandled capacity state: {capacity!r}"  # noqa: B011  # nosec B101  # pragma: no cover


def _route_available(
    state: RunState,
    outcome: LoopOutcome,
    ledger: BudgetLedger,
) -> tuple[RunState, Decision]:
    if state is RunState.Preflight or state is RunState.Probing:
        return _send_turn_or_budget(ledger)
    if state in _TURN_STATES:
        return _evaluate_completion(outcome, ledger)
    # Closed-union exhaustiveness: remaining RunState values are a finite ADT.
    # This assert is a precondition on that union, not a security gate.
    assert False, f"unhandled run state: {state!r}"  # noqa: B011  # nosec B101  # pragma: no cover


def _send_turn_or_budget(ledger: BudgetLedger) -> tuple[RunState, Decision]:
    exceeded = ledger.exceeded()
    if exceeded is not None:
        return RunState.Failed, Finish(success=False, reason=exceeded)
    return RunState.Running, SendTurn()


def _evaluate_completion(outcome: LoopOutcome, ledger: BudgetLedger) -> tuple[RunState, Decision]:
    completion = outcome.completion
    if isinstance(completion, Done):
        return RunState.Complete, Finish(success=True, reason="done")
    if isinstance(completion, Blocked):
        return RunState.Failed, Finish(success=False, reason=completion.reason)
    exceeded = ledger.exceeded()
    if exceeded is not None:
        return RunState.Failed, Finish(success=False, reason=exceeded)
    # Placement is the safety argument: Done, Blocked and an exact budget cap
    # all outrank a *predicted* stop, and a real capacity rejection never
    # reaches here at all -- _route_capacity handles those first.
    if outcome.wind_down is not None:
        return RunState.Handoff, WindDownAndFinish(
            reason=outcome.wind_down.reason, forecast=outcome.wind_down.forecast
        )
    if isinstance(completion, Continue):
        return RunState.Running, SendTurn()
    if completion is None:
        return RunState.Evaluating, Probe()
    # Closed-union exhaustiveness: CompletionVerdict | None is a finite ADT.
    # This assert is a precondition on that union, not a security gate.
    assert False, f"unhandled completion verdict: {completion!r}"  # noqa: B011  # nosec B101  # pragma: no cover
