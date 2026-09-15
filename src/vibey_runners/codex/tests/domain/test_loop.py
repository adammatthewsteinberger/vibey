# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Run-loop state machine: transition table, exhaustiveness, terminals."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from itertools import product

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from codexloop.domain.budget import Budget, BudgetLedger
from codexloop.domain.capacity import (
    AuthFailed,
    Available,
    CapacityState,
    QuotaExhausted,
    ThrottleExhausted,
    TransientBackendError,
    WindowExhausted,
)
from codexloop.domain.completion import Blocked, Continue, Done
from codexloop.domain.control import Prompt, PromptTiming, Snapshot, Stop
from codexloop.domain.forecast import CapacityForecast, Headroom, WindDown
from codexloop.domain.loop import (
    BackoffUntil,
    Decision,
    Drain,
    Finish,
    LoopOutcome,
    Probe,
    RunLoopStateMachine,
    RunState,
    SendTurn,
    WaitUntil,
    WindDownAndFinish,
)

NOW = datetime(2026, 8, 13, 12, 0, tzinfo=UTC)
MACHINE = RunLoopStateMachine()
BLOCKED = Blocked(reason="needs human")
CONTINUE = Continue(remaining=["wire the runner"])

AVAILABLE = LoopOutcome(capacity=Available())
AUTH = LoopOutcome(capacity=AuthFailed(reason="invalid_api_key"))
THROTTLE = LoopOutcome(capacity=ThrottleExhausted())
WINDOW = LoopOutcome(capacity=WindowExhausted())
QUOTA = LoopOutcome(capacity=QuotaExhausted(reason="insufficient_quota"))
TRANSIENT = LoopOutcome(capacity=TransientBackendError())

CAPACITY_SAMPLES: tuple[CapacityState, ...] = (
    Available(),
    ThrottleExhausted(),
    WindowExhausted(),
    QuotaExhausted(reason="insufficient_quota"),
    AuthFailed(reason="invalid_api_key"),
    TransientBackendError(),
)

NON_TERMINAL: tuple[RunState, ...] = (
    RunState.Preflight,
    RunState.Running,
    RunState.Evaluating,
    RunState.ThrottleBackoff,
    RunState.Waiting,
    RunState.Probing,
    RunState.Stopping,
)

AUTH_STATES: tuple[RunState, ...] = tuple(
    state for state in NON_TERMINAL if state is not RunState.Stopping
)

DEADLINE_STATES: tuple[RunState, ...] = (
    RunState.Preflight,
    RunState.Waiting,
    RunState.Probing,
    RunState.ThrottleBackoff,
)

DRAIN_STATES: tuple[RunState, ...] = tuple(
    state for state in NON_TERMINAL if state is not RunState.Stopping
)


def _unlimited() -> BudgetLedger:
    return BudgetLedger(Budget(max_turns=None, max_dollars=None, max_wall_clock=None))


def _advance(
    state: RunState,
    outcome: LoopOutcome,
    *,
    ledger: BudgetLedger | None = None,
    controls: tuple[object, ...] = (),
) -> tuple[RunState, Decision]:
    return MACHINE.advance(
        state,
        outcome,
        NOW,
        _unlimited() if ledger is None else ledger,
        controls,  # type: ignore[arg-type]
    )


def _done(capacity: CapacityState) -> LoopOutcome:
    return LoopOutcome(capacity=capacity, completion=Done())


def _continue(capacity: CapacityState) -> LoopOutcome:
    return LoopOutcome(capacity=capacity, completion=CONTINUE)


# --- Transition table (architecture §4 arrows) -----------------------------

TRANSITION_CASES: list[tuple[str, RunState, LoopOutcome, RunState, Decision]] = [
    (
        "preflight_available",
        RunState.Preflight,
        AVAILABLE,
        RunState.Running,
        SendTurn(),
    ),
    (
        "preflight_throttle",
        RunState.Preflight,
        THROTTLE,
        RunState.ThrottleBackoff,
        BackoffUntil(until=NOW),
    ),
    (
        "preflight_window",
        RunState.Preflight,
        WINDOW,
        RunState.Waiting,
        WaitUntil(until=NOW),
    ),
    (
        "preflight_quota",
        RunState.Preflight,
        QUOTA,
        RunState.Waiting,
        WaitUntil(until=NOW),
    ),
    (
        "preflight_transient",
        RunState.Preflight,
        TRANSIENT,
        RunState.Waiting,
        WaitUntil(until=NOW),
    ),
    (
        "preflight_auth",
        RunState.Preflight,
        AUTH,
        RunState.Failed,
        Finish(success=False, reason="auth"),
    ),
    (
        "running_turn_ended_without_verdict",
        RunState.Running,
        AVAILABLE,
        RunState.Evaluating,
        Probe(),
    ),
    (
        "running_done",
        RunState.Running,
        _done(Available()),
        RunState.Complete,
        Finish(success=True, reason="done"),
    ),
    (
        "running_continue",
        RunState.Running,
        _continue(Available()),
        RunState.Running,
        SendTurn(),
    ),
    (
        "running_blocked",
        RunState.Running,
        LoopOutcome(capacity=Available(), completion=BLOCKED),
        RunState.Failed,
        Finish(success=False, reason="needs human"),
    ),
    (
        "running_throttle_outranks_done",
        RunState.Running,
        _done(ThrottleExhausted()),
        RunState.ThrottleBackoff,
        BackoffUntil(until=NOW),
    ),
    (
        "running_window_outranks_done",
        RunState.Running,
        _done(WindowExhausted()),
        RunState.Waiting,
        WaitUntil(until=NOW),
    ),
    (
        "running_quota",
        RunState.Running,
        QUOTA,
        RunState.Waiting,
        WaitUntil(until=NOW),
    ),
    (
        "running_transient",
        RunState.Running,
        TRANSIENT,
        RunState.Waiting,
        WaitUntil(until=NOW),
    ),
    (
        "running_auth_outranks_done",
        RunState.Running,
        _done(AuthFailed(reason="invalid_api_key")),
        RunState.Failed,
        Finish(success=False, reason="auth"),
    ),
    (
        "evaluating_done",
        RunState.Evaluating,
        _done(Available()),
        RunState.Complete,
        Finish(success=True, reason="done"),
    ),
    (
        "evaluating_continue",
        RunState.Evaluating,
        _continue(Available()),
        RunState.Running,
        SendTurn(),
    ),
    (
        "evaluating_blocked",
        RunState.Evaluating,
        LoopOutcome(capacity=Available(), completion=BLOCKED),
        RunState.Failed,
        Finish(success=False, reason="needs human"),
    ),
    (
        "evaluating_none_probes",
        RunState.Evaluating,
        AVAILABLE,
        RunState.Evaluating,
        Probe(),
    ),
    (
        "evaluating_window",
        RunState.Evaluating,
        WINDOW,
        RunState.Waiting,
        WaitUntil(until=NOW),
    ),
    (
        "evaluating_throttle",
        RunState.Evaluating,
        THROTTLE,
        RunState.ThrottleBackoff,
        BackoffUntil(until=NOW),
    ),
    (
        "waiting_wake_available",
        RunState.Waiting,
        AVAILABLE,
        RunState.Probing,
        Probe(),
    ),
    (
        "waiting_wake_window",
        RunState.Waiting,
        WINDOW,
        RunState.Probing,
        Probe(),
    ),
    (
        "waiting_wake_throttle",
        RunState.Waiting,
        THROTTLE,
        RunState.Probing,
        Probe(),
    ),
    (
        "waiting_wake_quota",
        RunState.Waiting,
        QUOTA,
        RunState.Probing,
        Probe(),
    ),
    (
        "waiting_wake_transient",
        RunState.Waiting,
        TRANSIENT,
        RunState.Probing,
        Probe(),
    ),
    (
        "waiting_auth",
        RunState.Waiting,
        AUTH,
        RunState.Failed,
        Finish(success=False, reason="auth"),
    ),
    (
        "throttle_backoff_wake_available",
        RunState.ThrottleBackoff,
        AVAILABLE,
        RunState.Probing,
        Probe(),
    ),
    (
        "throttle_backoff_wake_throttle",
        RunState.ThrottleBackoff,
        THROTTLE,
        RunState.Probing,
        Probe(),
    ),
    (
        "throttle_backoff_wake_window",
        RunState.ThrottleBackoff,
        WINDOW,
        RunState.Probing,
        Probe(),
    ),
    (
        "throttle_backoff_auth",
        RunState.ThrottleBackoff,
        AUTH,
        RunState.Failed,
        Finish(success=False, reason="auth"),
    ),
    (
        "probing_available",
        RunState.Probing,
        AVAILABLE,
        RunState.Running,
        SendTurn(),
    ),
    (
        "probing_window",
        RunState.Probing,
        WINDOW,
        RunState.Waiting,
        WaitUntil(until=NOW),
    ),
    (
        "probing_quota",
        RunState.Probing,
        QUOTA,
        RunState.Waiting,
        WaitUntil(until=NOW),
    ),
    (
        "probing_transient",
        RunState.Probing,
        TRANSIENT,
        RunState.Waiting,
        WaitUntil(until=NOW),
    ),
    (
        "probing_throttle",
        RunState.Probing,
        THROTTLE,
        RunState.ThrottleBackoff,
        BackoffUntil(until=NOW),
    ),
    (
        "probing_auth",
        RunState.Probing,
        AUTH,
        RunState.Failed,
        Finish(success=False, reason="auth"),
    ),
    (
        "complete_stays",
        RunState.Complete,
        AVAILABLE,
        RunState.Complete,
        Finish(success=True, reason="done"),
    ),
    (
        "complete_ignores_auth",
        RunState.Complete,
        AUTH,
        RunState.Complete,
        Finish(success=True, reason="done"),
    ),
    (
        "failed_stays",
        RunState.Failed,
        AVAILABLE,
        RunState.Failed,
        Finish(success=False, reason="failed"),
    ),
    (
        "failed_ignores_auth",
        RunState.Failed,
        AUTH,
        RunState.Failed,
        Finish(success=False, reason="failed"),
    ),
    (
        "stopping_finishes_stop",
        RunState.Stopping,
        AVAILABLE,
        RunState.Failed,
        Finish(success=False, reason="stop"),
    ),
]


@pytest.mark.parametrize(
    ("state", "outcome", "expected_state", "expected_decision"),
    [case[1:] for case in TRANSITION_CASES],
    ids=[case[0] for case in TRANSITION_CASES],
)
def test_transition_table(
    state: RunState,
    outcome: LoopOutcome,
    expected_state: RunState,
    expected_decision: Decision,
) -> None:
    next_state, decision = _advance(state, outcome)
    assert next_state is expected_state
    assert decision == expected_decision


# --- Exhaustiveness --------------------------------------------------------

_STATE_CAPACITY_PAIRS = tuple(product(list(RunState), CAPACITY_SAMPLES))


@pytest.mark.parametrize(
    ("state", "capacity"),
    _STATE_CAPACITY_PAIRS,
    ids=[f"{state.name}-{type(capacity).__name__}" for state, capacity in _STATE_CAPACITY_PAIRS],
)
def test_every_state_capacity_pair_produces_a_decision(
    state: RunState, capacity: CapacityState
) -> None:
    next_state, decision = _advance(state, LoopOutcome(capacity=capacity))
    assert isinstance(next_state, RunState)
    assert isinstance(decision, Decision)


@given(pair=st.sampled_from(_STATE_CAPACITY_PAIRS))
@settings(max_examples=len(_STATE_CAPACITY_PAIRS) * 2)
def test_hypothesis_enumerates_state_capacity_product_without_raising(
    pair: tuple[RunState, CapacityState],
) -> None:
    state, capacity = pair
    next_state, decision = _advance(state, LoopOutcome(capacity=capacity))
    assert isinstance(next_state, RunState)
    assert isinstance(decision, Decision)


# --- Terminals: auth, max-wait, stop, budget --------------------------------


@pytest.mark.parametrize("state", AUTH_STATES, ids=lambda s: s.name)
def test_auth_failed_from_any_non_terminal_fails(state: RunState) -> None:
    next_state, decision = _advance(state, AUTH)
    assert next_state is RunState.Failed
    assert decision == Finish(success=False, reason="auth")


@pytest.mark.parametrize("state", DEADLINE_STATES, ids=lambda s: s.name)
def test_max_wait_exceeded_fails_with_reason(state: RunState) -> None:
    outcome = LoopOutcome(capacity=Available(), deadline_exceeded=True)
    next_state, decision = _advance(state, outcome)
    assert next_state is RunState.Failed
    assert decision == Finish(success=False, reason="max_wait")


def test_max_wait_does_not_fail_a_running_turn() -> None:
    outcome = LoopOutcome(
        capacity=Available(),
        completion=CONTINUE,
        deadline_exceeded=True,
    )
    next_state, decision = _advance(RunState.Running, outcome)
    assert next_state is RunState.Running
    assert decision == SendTurn()


@pytest.mark.parametrize("state", DRAIN_STATES, ids=lambda s: s.name)
def test_stop_from_non_terminal_enters_stopping_and_drains(state: RunState) -> None:
    next_state, decision = _advance(state, AVAILABLE, controls=(Stop(),))
    assert next_state is RunState.Stopping
    assert decision == Drain()


def test_advance_from_stopping_finishes_with_stop_reason() -> None:
    next_state, decision = _advance(RunState.Stopping, AVAILABLE, controls=(Stop(),))
    assert next_state is RunState.Failed
    assert decision == Finish(success=False, reason="stop")


@pytest.mark.parametrize("state", (RunState.Complete, RunState.Failed), ids=lambda s: s.name)
def test_stop_is_ignored_on_terminal_states(state: RunState) -> None:
    next_state, decision = _advance(state, AVAILABLE, controls=(Stop(),))
    expected_success = state is RunState.Complete
    assert next_state is state
    assert decision == Finish(
        success=expected_success,
        reason="done" if expected_success else "failed",
    )


def test_stop_outranks_auth_failed() -> None:
    next_state, decision = _advance(RunState.Running, AUTH, controls=(Stop(),))
    assert next_state is RunState.Stopping
    assert decision == Drain()


def test_stop_outranks_deadline() -> None:
    outcome = LoopOutcome(capacity=Available(), deadline_exceeded=True)
    next_state, decision = _advance(RunState.Waiting, outcome, controls=(Stop(),))
    assert next_state is RunState.Stopping
    assert decision == Drain()


def test_non_stop_controls_are_ignored() -> None:
    controls = (
        Prompt(text="keep going", timing=PromptTiming.NOW),
        Snapshot(),
    )
    next_state, decision = _advance(RunState.Preflight, AVAILABLE, controls=controls)
    assert next_state is RunState.Running
    assert decision == SendTurn()


def test_stop_among_other_controls_still_drains() -> None:
    controls = (
        Prompt(text="keep going", timing=PromptTiming.NOW),
        Stop(),
        Snapshot(),
    )
    next_state, decision = _advance(RunState.Preflight, AVAILABLE, controls=controls)
    assert next_state is RunState.Stopping
    assert decision == Drain()


def test_budget_exceeded_on_continue_fails_with_turns() -> None:
    ledger = BudgetLedger(Budget(max_turns=1, max_dollars=None, max_wall_clock=None))
    ledger.record(turns=1)
    next_state, decision = _advance(RunState.Running, _continue(Available()), ledger=ledger)
    assert next_state is RunState.Failed
    assert decision == Finish(success=False, reason="turns")


def test_budget_exceeded_on_continue_fails_with_dollars() -> None:
    ledger = BudgetLedger(Budget(max_turns=None, max_dollars=1.0, max_wall_clock=None))
    ledger.record(dollars=1.0)
    next_state, decision = _advance(RunState.Evaluating, _continue(Available()), ledger=ledger)
    assert next_state is RunState.Failed
    assert decision == Finish(success=False, reason="dollars")


def test_budget_exceeded_on_continue_fails_with_wall_clock() -> None:
    cap = timedelta(seconds=10)
    ledger = BudgetLedger(Budget(max_turns=None, max_dollars=None, max_wall_clock=cap))
    ledger.record(elapsed=cap)
    next_state, decision = _advance(RunState.Running, _continue(Available()), ledger=ledger)
    assert next_state is RunState.Failed
    assert decision == Finish(success=False, reason="wall_clock")


def test_done_outranks_exceeded_budget() -> None:
    ledger = BudgetLedger(Budget(max_turns=1, max_dollars=None, max_wall_clock=None))
    ledger.record(turns=1)
    next_state, decision = _advance(RunState.Running, _done(Available()), ledger=ledger)
    assert next_state is RunState.Complete
    assert decision == Finish(success=True, reason="done")


def test_blocked_outranks_exceeded_budget() -> None:
    ledger = BudgetLedger(Budget(max_turns=1, max_dollars=None, max_wall_clock=None))
    ledger.record(turns=1)
    outcome = LoopOutcome(capacity=Available(), completion=BLOCKED)
    next_state, decision = _advance(RunState.Evaluating, outcome, ledger=ledger)
    assert next_state is RunState.Failed
    assert decision == Finish(success=False, reason="needs human")


def test_preflight_budget_exceeded_fails_before_send_turn() -> None:
    ledger = BudgetLedger(Budget(max_turns=0, max_dollars=None, max_wall_clock=None))
    next_state, decision = _advance(RunState.Preflight, AVAILABLE, ledger=ledger)
    assert next_state is RunState.Failed
    assert decision == Finish(success=False, reason="turns")


def test_probing_budget_exceeded_fails_before_send_turn() -> None:
    ledger = BudgetLedger(Budget(max_turns=0, max_dollars=None, max_wall_clock=None))
    next_state, decision = _advance(RunState.Probing, AVAILABLE, ledger=ledger)
    assert next_state is RunState.Failed
    assert decision == Finish(success=False, reason="turns")


def test_completion_none_with_exceeded_budget_fails() -> None:
    ledger = BudgetLedger(Budget(max_turns=0, max_dollars=None, max_wall_clock=None))
    next_state, decision = _advance(RunState.Running, AVAILABLE, ledger=ledger)
    assert next_state is RunState.Failed
    assert decision == Finish(success=False, reason="turns")


# --- Value object shape ----------------------------------------------------


def test_run_state_members_match_the_closed_set() -> None:
    assert [member.name for member in RunState] == [
        "Preflight",
        "Running",
        "Evaluating",
        "ThrottleBackoff",
        "Waiting",
        "Probing",
        "Stopping",
        "Complete",
        "Failed",
        "Handoff",
    ]


def test_decision_is_the_closed_union() -> None:
    assert Decision == (
        SendTurn | Probe | WaitUntil | BackoffUntil | Finish | Drain | WindDownAndFinish
    )


def test_loop_outcome_is_frozen_slots() -> None:
    outcome = LoopOutcome(capacity=Available())
    assert outcome.__dataclass_params__.frozen is True
    assert outcome.__dataclass_params__.slots is True
    assert outcome.completion is None
    assert outcome.deadline_exceeded is False
    assert outcome.wind_down is None


def test_handoff_is_terminal_for_this_process() -> None:
    """Advancing out of Handoff would restart a run that has already handed
    its work over."""
    machine = RunLoopStateMachine()
    state, decision = machine.advance(
        RunState.Handoff,
        LoopOutcome(capacity=Available()),
        NOW,
        BudgetLedger(Budget(None, None, None)),
        [],
    )
    assert state is RunState.Handoff
    assert isinstance(decision, Finish)
    assert decision.success is False
    assert decision.reason == "handoff"


def test_a_wind_down_yields_the_handoff_decision_after_a_continue() -> None:
    machine = RunLoopStateMachine()
    headroom = Headroom(0.05, "window:primary", NOW)
    wind_down = WindDown(
        reason="headroom:window:primary",
        forecast=CapacityForecast(
            binding=headroom,
            dimensions=(headroom,),
            turns_until_exhaustion=None,
            seconds_until_reset=None,
        ),
    )
    state, decision = machine.advance(
        RunState.Running,
        LoopOutcome(capacity=Available(), completion=Continue(remaining=()), wind_down=wind_down),
        NOW,
        BudgetLedger(Budget(None, None, None)),
        [],
    )
    assert state is RunState.Handoff
    assert isinstance(decision, WindDownAndFinish)
    assert decision.reason == "headroom:window:primary"


def test_done_still_outranks_a_wind_down() -> None:
    """Never turn a completed run into a handoff."""
    machine = RunLoopStateMachine()
    headroom = Headroom(0.01, "window:primary", NOW)
    wind_down = WindDown(
        reason="headroom:window:primary",
        forecast=CapacityForecast(
            binding=headroom,
            dimensions=(headroom,),
            turns_until_exhaustion=None,
            seconds_until_reset=None,
        ),
    )
    state, decision = machine.advance(
        RunState.Running,
        LoopOutcome(capacity=Available(), completion=Done(), wind_down=wind_down),
        NOW,
        BudgetLedger(Budget(None, None, None)),
        [],
    )
    assert state is RunState.Complete
    assert isinstance(decision, Finish)
    assert decision.success is True
