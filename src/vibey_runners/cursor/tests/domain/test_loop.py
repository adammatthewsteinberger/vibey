# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
from __future__ import annotations

from datetime import UTC, datetime, timedelta

from cursorloop.domain.budget import Budget, BudgetLedger
from cursorloop.domain.capacity import (
    AuthenticationFailed,
    Available,
    CreditsExhausted,
    WindowExhausted,
)
from cursorloop.domain.completion import Blocked, Continue, Done
from cursorloop.domain.loop import (
    DelayThenSend,
    Finish,
    Phase,
    RunProbe,
    ScheduleProbe,
    SendTurn,
    decide_after_probe,
    decide_after_turn,
    decide_preflight,
    decide_progress_delay,
    start,
)
from cursorloop.domain.waiting import WaitPolicyConfig

NOW = datetime(2026, 8, 13, 12, 0, 0, tzinfo=UTC)
LEDGER = BudgetLedger(budget=Budget(max_turns=100))


def test_after_turn_limit_outranks_completion_claim() -> None:
    """THE single most important invariant in the codebase: capacity is
    checked BEFORE the verdict, always. A Done verdict on a turn that also hit
    a rejection is discarded — a truncated limit message can coincidentally
    contain marker-like text, and hitting a real limit is never 'done'.
    NEVER reorder this check."""
    state, decision = decide_after_turn(
        start(LEDGER),
        capacity=CreditsExhausted(),
        verdict=Done(summary="all finished!"),
        now=NOW,
    )
    assert state.phase is Phase.WAITING
    assert isinstance(decision, ScheduleProbe)


def test_credits_exhaustion_schedules_a_probe_never_a_deadline_sleep() -> None:
    _, decision = decide_after_turn(
        start(LEDGER), capacity=CreditsExhausted(), verdict=Continue(), now=NOW
    )
    assert isinstance(decision, ScheduleProbe)
    assert NOW < decision.at <= NOW + timedelta(seconds=600)


def test_authentication_failure_is_terminal_from_every_phase() -> None:
    for decide in (
        lambda: decide_preflight(start(LEDGER), AuthenticationFailed("bad key"), now=NOW),
        lambda: decide_after_turn(
            start(LEDGER), capacity=AuthenticationFailed("bad key"), verdict=Continue(), now=NOW
        ),
        lambda: decide_after_probe(start(LEDGER), AuthenticationFailed("bad key"), now=NOW),
    ):
        state, decision = decide()
        assert state.phase is Phase.FAILED
        assert decision == Finish(success=False, reason="authentication failed")


def test_preflight_probes_before_spending_a_real_turn_when_exhausted() -> None:
    state, decision = decide_preflight(
        start(LEDGER), WindowExhausted("rate_limit", NOW + timedelta(minutes=5)), now=NOW
    )
    assert state.phase is Phase.WAITING
    assert isinstance(decision, ScheduleProbe)


def test_probe_finding_capacity_resumes_the_run() -> None:
    waiting, _ = decide_after_turn(
        start(LEDGER), capacity=CreditsExhausted(), verdict=Continue(), now=NOW
    )
    state, decision = decide_after_probe(waiting, Available(), now=NOW + timedelta(minutes=2))
    assert state.phase is Phase.RUNNING
    assert decision == SendTurn()


def test_repeated_probes_increment_the_count_and_keep_the_original_start() -> None:
    state, _ = decide_after_turn(
        start(LEDGER), capacity=CreditsExhausted(), verdict=Continue(), now=NOW
    )
    for i in range(1, 4):
        state, _ = decide_after_probe(state, CreditsExhausted(), now=NOW + timedelta(minutes=2 * i))
        assert state.probe_count == i
        assert state.started_waiting_at == NOW


def test_blocked_verdict_terminates_the_run() -> None:
    state, decision = decide_after_turn(
        start(LEDGER),
        capacity=Available(),
        verdict=Blocked(reason="needs prod credentials"),
        now=NOW,
    )
    assert state.phase is Phase.FAILED
    assert decision == Finish(success=False, reason="needs prod credentials")


def test_budget_exhaustion_stops_the_loop() -> None:
    tight = BudgetLedger(budget=Budget(max_turns=1))
    state, decision = decide_after_turn(
        start(tight), capacity=Available(), verdict=Continue(), now=NOW, tokens=10
    )
    assert state.phase is Phase.FAILED
    assert decision == Finish(success=False, reason="budget exhausted")


def test_start_phase_is_preflight() -> None:
    state = start(LEDGER)
    assert state.phase is Phase.PREFLIGHT
    assert state.ledger.turns_spent == 0
    assert state.probe_count == 0
    assert state.started_waiting_at is None
    assert state.failure_reason is None


def test_preflight_available_transitions_to_running_and_sends_turn() -> None:
    state, decision = decide_preflight(start(LEDGER), Available(), now=NOW)
    assert state.phase is Phase.RUNNING
    assert decision == SendTurn()


def test_preflight_credits_exhausted_enters_waiting_without_spending_a_turn() -> None:
    state, decision = decide_preflight(start(LEDGER), CreditsExhausted(), now=NOW)
    assert state.phase is Phase.WAITING
    assert isinstance(decision, ScheduleProbe)
    assert state.ledger.turns_spent == 0
    assert state.probe_count == 0
    assert state.started_waiting_at == NOW


def test_after_turn_done_verdict_completes() -> None:
    state, decision = decide_after_turn(
        start(LEDGER), capacity=Available(), verdict=Done(summary="finished"), now=NOW
    )
    assert state.phase is Phase.COMPLETE
    assert decision == Finish(success=True, reason="finished")
    assert state.ledger.turns_spent == 1


def test_after_turn_continue_under_budget_sends_another_turn() -> None:
    state, decision = decide_after_turn(
        start(LEDGER), capacity=Available(), verdict=Continue(remaining_work=("x",)), now=NOW
    )
    assert state.phase is Phase.RUNNING
    assert isinstance(decision, SendTurn)
    assert state.ledger.turns_spent == 1


def test_after_turn_window_exhaustion_enters_waiting() -> None:
    state, decision = decide_after_turn(
        start(LEDGER),
        capacity=WindowExhausted("rate_limit"),
        verdict=Continue(),
        now=NOW,
    )
    assert state.phase is Phase.WAITING
    assert isinstance(decision, ScheduleProbe)


def test_wall_clock_exhaustion_stops_the_loop() -> None:
    """any_exhausted does not include wall-clock; the loop must call
    wall_clock_exhausted itself or a max_wall_clock cap never fires."""
    ledger = BudgetLedger(budget=Budget(max_wall_clock=timedelta(hours=1)))
    state, decision = decide_after_turn(
        start(ledger),
        capacity=Available(),
        verdict=Continue(),
        now=NOW + timedelta(hours=2),
        started_at=NOW,
    )
    assert state.phase is Phase.FAILED
    assert decision == Finish(success=False, reason="budget exhausted")


def test_wall_clock_under_cap_does_not_stop_a_continue() -> None:
    ledger = BudgetLedger(budget=Budget(max_wall_clock=timedelta(hours=1)))
    state, decision = decide_after_turn(
        start(ledger),
        capacity=Available(),
        verdict=Continue(),
        now=NOW + timedelta(minutes=10),
        started_at=NOW,
    )
    assert state.phase is Phase.RUNNING
    assert isinstance(decision, SendTurn)


def test_omitted_dollars_is_unknown_cost_not_billed_zero() -> None:
    """spend_turn treats None as unknown (cost_pending); 0.0 is billed zero.
    Defaulting dollars to 0.0 reintroduces the settling-None-as-$0 footgun."""
    state, _ = decide_after_turn(start(LEDGER), capacity=Available(), verdict=Continue(), now=NOW)
    assert state.ledger.cost_pending is True
    assert state.ledger.dollars_spent == 0.0


def test_wall_clock_exhaustion_stops_probe_resume() -> None:
    ledger = BudgetLedger(budget=Budget(max_wall_clock=timedelta(hours=1)))
    waiting, _ = decide_after_turn(
        start(ledger), capacity=CreditsExhausted(), verdict=Continue(), now=NOW
    )
    state, decision = decide_after_probe(
        waiting, Available(), now=NOW + timedelta(hours=2), started_at=NOW
    )
    assert state.phase is Phase.FAILED
    assert decision == Finish(success=False, reason="budget exhausted")


def test_wall_clock_exhaustion_stops_waiting_instead_of_rescheduling() -> None:
    ledger = BudgetLedger(budget=Budget(max_wall_clock=timedelta(hours=1)))
    waiting, _ = decide_after_turn(
        start(ledger), capacity=CreditsExhausted(), verdict=Continue(), now=NOW
    )
    state, decision = decide_after_probe(
        waiting, CreditsExhausted(), now=NOW + timedelta(hours=2), started_at=NOW
    )
    assert state.phase is Phase.FAILED
    assert decision == Finish(success=False, reason="budget exhausted")


def test_wall_clock_exhaustion_stops_entering_wait() -> None:
    ledger = BudgetLedger(budget=Budget(max_wall_clock=timedelta(hours=1)))
    state, decision = decide_after_turn(
        start(ledger),
        capacity=CreditsExhausted(),
        verdict=Continue(),
        now=NOW + timedelta(hours=2),
        started_at=NOW,
    )
    assert state.phase is Phase.FAILED
    assert decision == Finish(success=False, reason="budget exhausted")


def test_after_probe_still_exhausted_reschedules_from_fresh_state() -> None:
    state, decision = decide_after_probe(start(LEDGER), CreditsExhausted(), now=NOW)
    assert state.phase is Phase.WAITING
    assert isinstance(decision, ScheduleProbe)
    assert state.started_waiting_at == NOW
    assert state.probe_count == 1


def test_max_wait_exceeded_gives_up_rather_than_waiting_forever() -> None:
    config = WaitPolicyConfig(max_wait=timedelta(minutes=10))
    state, _ = decide_preflight(start(LEDGER), CreditsExhausted(), now=NOW)
    state, decision = decide_after_probe(
        state, CreditsExhausted(), now=NOW + timedelta(hours=1), config=config
    )
    assert state.phase is Phase.FAILED
    assert decision == Finish(success=False, reason="max wait exceeded")
    assert state.failure_reason == "max wait exceeded"


def test_decide_progress_delay_none_when_tree_changed() -> None:
    assert (
        decide_progress_delay(
            verdict=Continue(remaining_work=("Waiting for suite",)),
            tree_changed=True,
            now=NOW,
            streak=0,
        )
        is None
    )


def test_decide_progress_delay_none_when_remaining_work_is_not_wait_only() -> None:
    assert (
        decide_progress_delay(
            verdict=Continue(remaining_work=("Fix the login button",)),
            tree_changed=False,
            now=NOW,
            streak=0,
        )
        is None
    )


def test_decide_progress_delay_when_wait_only() -> None:
    delay = decide_progress_delay(
        verdict=Continue(remaining_work=("Waiting for suite",)),
        tree_changed=False,
        now=NOW,
        streak=0,
    )
    assert isinstance(delay, DelayThenSend)
    assert (delay.at - NOW).total_seconds() == 30


def test_run_probe_and_probing_phase_exist_as_declared_members() -> None:
    """RunProbe / Phase.PROBING are part of the closed unions; the runner
    folds probing into ScheduleProbe today, but the types must exist."""
    assert isinstance(RunProbe(), RunProbe)
    assert Phase.PROBING is not Phase.WAITING
    assert Phase.PROBING is not Phase.RUNNING
