# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Wind-down precedence: what a *predicted* stop must never beat.

The whole safety argument for adding a predictive branch to a mature state
machine is that it sits last. Each test below pins one rung of that order, so
a future reordering fails loudly rather than silently turning a completed run
into a handoff.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from claudeloop.domain.budget import Budget, BudgetLedger
from claudeloop.domain.capacity import (
    AuthenticationFailed,
    Available,
    CreditsExhausted,
    WindowExhausted,
)
from claudeloop.domain.completion import Blocked, Continue, Done
from claudeloop.domain.forecast import CapacityForecast, Headroom, WindDown
from claudeloop.domain.loop import (
    Finish,
    Phase,
    RunState,
    SendTurn,
    WindDownAndFinish,
    decide_after_turn,
)

NOW = datetime(2026, 8, 15, 12, 0, tzinfo=timezone.utc)


def _wind_down() -> WindDown:
    headroom = Headroom(0.05, "utilization", NOW)
    return WindDown(
        reason="headroom:utilization",
        forecast=CapacityForecast(
            binding=headroom,
            dimensions=(headroom,),
            turns_until_exhaustion=None,
            seconds_until_reset=None,
        ),
    )


def _state(**budget: object) -> RunState:
    return RunState(phase=Phase.RUNNING, ledger=BudgetLedger(budget=Budget(**budget)))  # type: ignore[arg-type]


def _decide(**kwargs: object) -> tuple[RunState, object]:
    params: dict[str, object] = {
        "capacity": Available(),
        "verdict": Continue(),
        "now": NOW,
        "wind_down": _wind_down(),
    }
    params.update(kwargs)
    return decide_after_turn(_state(), **params)  # type: ignore[arg-type]


def test_auth_failure_outranks_a_wind_down() -> None:
    """Waiting cannot fix credentials, and neither can handing off."""
    _, decision = _decide(capacity=AuthenticationFailed(detail="bad key"))
    assert isinstance(decision, Finish)
    assert decision.success is False


@pytest.mark.parametrize(
    "capacity",
    [WindowExhausted(rate_limit_type="tokens"), CreditsExhausted()],
    ids=["window", "credits"],
)
def test_a_real_rejection_outranks_a_predicted_one(capacity: object) -> None:
    """We are past forecasting: the limit already landed, so the existing
    waiting path owns it."""
    _, decision = _decide(capacity=capacity)
    assert not isinstance(decision, WindDownAndFinish)


def test_done_outranks_a_wind_down() -> None:
    """Never turn a completed run into a handoff -- there is nothing to hand."""
    state, decision = _decide(verdict=Done(summary="shipped"))
    assert isinstance(decision, Finish)
    assert decision.success is True
    assert state.phase is Phase.COMPLETE


def test_blocked_outranks_a_wind_down() -> None:
    state, decision = _decide(verdict=Blocked(reason="needs a human"))
    assert isinstance(decision, Finish)
    assert decision.success is False
    assert state.phase is Phase.FAILED


def test_an_exhausted_hard_cap_outranks_a_wind_down() -> None:
    """A cap is exact; a forecast is an estimate. The exact one wins."""
    state = RunState(
        phase=Phase.RUNNING,
        ledger=BudgetLedger(budget=Budget(max_turns=1)),
    )
    _, decision = decide_after_turn(
        state, capacity=Available(), verdict=Continue(), now=NOW, wind_down=_wind_down()
    )
    assert isinstance(decision, Finish)
    assert decision.reason == "budget exhausted"


def test_wind_down_fires_only_on_continue_available_and_not_exhausted() -> None:
    state, decision = _decide()
    assert isinstance(decision, WindDownAndFinish)
    assert decision.reason == "headroom:utilization"
    assert state.phase is Phase.HANDOFF


def test_no_wind_down_means_the_loop_behaves_exactly_as_before() -> None:
    """The predictive path is strictly additive; the reactive path is intact."""
    state, decision = _decide(wind_down=None)
    assert isinstance(decision, SendTurn)
    assert state.phase is Phase.RUNNING
