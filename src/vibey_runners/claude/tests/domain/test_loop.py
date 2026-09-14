# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
from datetime import datetime, timedelta, timezone

from claudeloop.domain.budget import Budget, BudgetLedger
from claudeloop.domain.capacity import (
    AuthenticationFailed,
    Available,
    CreditsExhausted,
    WindowExhausted,
)
from claudeloop.domain.completion import Blocked, Continue, Done
from claudeloop.domain.loop import (
    Finish,
    Phase,
    RunState,
    ScheduleProbe,
    SendTurn,
    decide_after_probe,
    decide_after_turn,
    decide_preflight,
    start,
)
from claudeloop.domain.waiting import WaitPolicyConfig

NOW = datetime(2026, 8, 9, 12, 0, tzinfo=timezone.utc)
_DEFAULT_BUDGET = Budget()


def fresh_state(budget: Budget = _DEFAULT_BUDGET) -> RunState:
    return start(BudgetLedger(budget=budget))


def test_start_phase_is_preflight():
    state = fresh_state()
    assert state.phase == Phase.PREFLIGHT
    assert state.ledger.turns_spent == 0


# --- preflight ---


def test_preflight_available_transitions_to_running_and_sends_turn():
    state, decision = decide_preflight(fresh_state(), Available(), now=NOW)
    assert state.phase == Phase.RUNNING
    assert isinstance(decision, SendTurn)


def test_preflight_authentication_failed_is_terminal():
    state, decision = decide_preflight(fresh_state(), AuthenticationFailed(detail="bad"), now=NOW)
    assert state.phase == Phase.FAILED
    assert isinstance(decision, Finish)
    assert decision.success is False


def test_preflight_window_exhausted_enters_waiting():
    state, decision = decide_preflight(
        fresh_state(), WindowExhausted(rate_limit_type="five_hour", resets_at=NOW), now=NOW
    )
    assert state.phase == Phase.WAITING
    assert isinstance(decision, ScheduleProbe)


def test_preflight_credits_exhausted_enters_waiting():
    state, decision = decide_preflight(fresh_state(), CreditsExhausted(), now=NOW)
    assert state.phase == Phase.WAITING
    assert isinstance(decision, ScheduleProbe)


# --- after a real turn ---


def test_after_turn_done_verdict_completes():
    state = fresh_state()
    state = start(state.ledger)
    state, decision = decide_after_turn(
        state, capacity=Available(), verdict=Done(summary="finished"), now=NOW
    )
    assert state.phase == Phase.COMPLETE
    assert decision == Finish(success=True, reason="finished")
    assert state.ledger.turns_spent == 1


def test_after_turn_blocked_verdict_fails():
    state, decision = decide_after_turn(
        fresh_state(), capacity=Available(), verdict=Blocked(reason="need MCP auth"), now=NOW
    )
    assert state.phase == Phase.FAILED
    assert state.failure_reason == "need MCP auth"
    assert decision == Finish(success=False, reason="need MCP auth")


def test_after_turn_continue_verdict_sends_another_turn():
    state, decision = decide_after_turn(
        fresh_state(), capacity=Available(), verdict=Continue(remaining_work=("x",)), now=NOW
    )
    assert state.phase == Phase.RUNNING
    assert isinstance(decision, SendTurn)


def test_after_turn_limit_outranks_completion_claim():
    """A truncated limit message could coincidentally contain marker-like text —
    hitting a real limit must always win over a Done verdict."""
    state, decision = decide_after_turn(
        fresh_state(),
        capacity=WindowExhausted(rate_limit_type="five_hour", resets_at=NOW),
        verdict=Done(summary="looks done but actually limited"),
        now=NOW,
    )
    assert state.phase == Phase.WAITING
    assert isinstance(decision, ScheduleProbe)


def test_after_turn_authentication_failed_is_terminal_even_with_done_verdict():
    state, decision = decide_after_turn(
        fresh_state(), capacity=AuthenticationFailed(detail="bad"), verdict=Done(), now=NOW
    )
    assert state.phase == Phase.FAILED
    assert decision.success is False


def test_after_turn_continue_but_budget_exhausted_fails():
    state = start(BudgetLedger(budget=Budget(max_turns=1)))
    state, decision = decide_after_turn(state, capacity=Available(), verdict=Continue(), now=NOW)
    assert state.phase == Phase.FAILED
    assert decision == Finish(success=False, reason="budget exhausted")


def test_after_turn_continue_under_budget_keeps_running():
    state = start(BudgetLedger(budget=Budget(max_turns=5)))
    state, decision = decide_after_turn(state, capacity=Available(), verdict=Continue(), now=NOW)
    assert state.phase == Phase.RUNNING
    assert isinstance(decision, SendTurn)


# --- probing while waiting ---


def test_after_probe_available_resumes_running():
    state, decision = decide_after_probe(fresh_state(), Available(), now=NOW)
    assert state.phase == Phase.RUNNING
    assert isinstance(decision, SendTurn)


def test_after_probe_still_exhausted_reschedules():
    state, decision = decide_after_probe(fresh_state(), CreditsExhausted(), now=NOW)
    assert state.phase == Phase.WAITING
    assert isinstance(decision, ScheduleProbe)


def test_after_probe_authentication_failed_terminal():
    state, decision = decide_after_probe(fresh_state(), AuthenticationFailed(detail="x"), now=NOW)
    assert state.phase == Phase.FAILED


# --- credit top-up mid-wait: the scenario the plan calls out explicitly ---


def test_credit_topup_sequence_resumes_after_several_failed_probes():
    """Five CreditsExhausted probes, then Available on the sixth — the runner must
    resume rather than continue waiting or give up."""
    state, decision = decide_preflight(fresh_state(), CreditsExhausted(), now=NOW)
    assert state.phase == Phase.WAITING
    t = NOW
    for i in range(4):
        t = t + timedelta(minutes=5 * (i + 1))
        state, decision = decide_after_probe(state, CreditsExhausted(), now=t)
        assert state.phase == Phase.WAITING
        assert isinstance(decision, ScheduleProbe)
    t = t + timedelta(minutes=30)
    state, decision = decide_after_probe(state, Available(), now=t)
    assert state.phase == Phase.RUNNING
    assert isinstance(decision, SendTurn)


def test_max_wait_exceeded_gives_up_rather_than_waiting_forever():
    config = WaitPolicyConfig(
        max_wait=timedelta(minutes=10), credits_probe_interval=timedelta(minutes=1)
    )
    state, decision = decide_preflight(fresh_state(), CreditsExhausted(), now=NOW)
    state, decision = decide_after_probe(
        state, CreditsExhausted(), now=NOW + timedelta(hours=1), config=config
    )
    assert state.phase == Phase.FAILED
    assert decision == Finish(success=False, reason="max wait exceeded")
