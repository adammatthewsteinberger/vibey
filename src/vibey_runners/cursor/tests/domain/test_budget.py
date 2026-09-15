# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from cursorloop.domain.budget import Budget, BudgetLedger


def test_unknown_cost_is_never_treated_as_zero() -> None:
    """agent.get_usage().cost is None until billing settles, and
    charged_cents is 0.0 for plan-included/BYOK usage. A ledger that reads a
    settling None as $0.00 will blow straight through --max-cost."""
    ledger = BudgetLedger(budget=Budget(max_cost_usd=1.0)).spend_turn(tokens=500, dollars=None)
    assert ledger.cost_pending is True
    assert ledger.dollars_spent == 0.0
    assert ledger.dollars_exhausted is False


def test_tokens_are_the_enforceable_hard_cap() -> None:
    ledger = BudgetLedger(budget=Budget(max_tokens=1000)).spend_turn(tokens=1200, dollars=None)
    assert ledger.tokens_exhausted is True
    assert ledger.any_exhausted is True


def test_ledger_is_immutable() -> None:
    first = BudgetLedger(budget=Budget(max_turns=5))
    second = first.spend_turn(tokens=10, dollars=0.01)
    assert first.turns_spent == 0
    assert second.turns_spent == 1


def test_unset_caps_are_never_exhausted() -> None:
    ledger = BudgetLedger(budget=Budget()).spend_turn(tokens=10**9, dollars=10**6)
    assert ledger.any_exhausted is False


@pytest.mark.parametrize(
    "field",
    ["max_turns", "max_tokens", "max_cost_usd", "max_attempts"],
)
def test_budget_rejects_nonpositive_numeric_caps(field: str) -> None:
    with pytest.raises(ValueError):
        Budget(**{field: 0})


def test_budget_rejects_nonpositive_wall_clock() -> None:
    with pytest.raises(ValueError):
        Budget(max_wall_clock=timedelta(0))
    with pytest.raises(ValueError):
        Budget(max_wall_clock=timedelta(seconds=-1))


def test_budget_all_none_is_valid() -> None:
    Budget()


def test_known_cost_accumulates_and_can_exhaust() -> None:
    ledger = BudgetLedger(budget=Budget(max_cost_usd=1.0)).spend_turn(tokens=10, dollars=0.4)
    assert ledger.cost_pending is False
    assert ledger.dollars_spent == 0.4
    assert ledger.dollars_exhausted is False
    ledger = ledger.spend_turn(tokens=10, dollars=0.6)
    assert ledger.dollars_spent == 1.0
    assert ledger.dollars_exhausted is True
    assert ledger.any_exhausted is True


def test_cost_pending_is_sticky_across_later_known_costs() -> None:
    ledger = BudgetLedger(budget=Budget(max_cost_usd=10.0)).spend_turn(tokens=1, dollars=None)
    ledger = ledger.spend_turn(tokens=1, dollars=0.5)
    assert ledger.cost_pending is True
    assert ledger.dollars_spent == 0.5
    assert ledger.dollars_exhausted is False


def test_turns_exhausted_at_cap() -> None:
    ledger = BudgetLedger(budget=Budget(max_turns=2))
    ledger = ledger.spend_turn(tokens=1, dollars=0.0).spend_turn(tokens=1, dollars=0.0)
    assert ledger.turns_exhausted is True
    assert ledger.any_exhausted is True


def test_turns_exhausted_false_below_cap_and_when_unset() -> None:
    below = BudgetLedger(budget=Budget(max_turns=2)).spend_turn(tokens=1, dollars=0.0)
    assert below.turns_exhausted is False
    unset = BudgetLedger(budget=Budget()).spend_turn(tokens=1, dollars=0.0)
    assert unset.turns_exhausted is False


def test_tokens_exhausted_false_below_cap_and_when_unset() -> None:
    below = BudgetLedger(budget=Budget(max_tokens=100)).spend_turn(tokens=99, dollars=None)
    assert below.tokens_spent == 99
    assert below.tokens_exhausted is False
    unset = BudgetLedger(budget=Budget()).spend_turn(tokens=10**9, dollars=None)
    assert unset.tokens_exhausted is False


def test_spend_attempt_exhausts_attempts_cap() -> None:
    ledger = BudgetLedger(budget=Budget(max_attempts=1)).spend_attempt()
    assert ledger.attempts_spent == 1
    assert ledger.attempts_exhausted is True
    assert ledger.any_exhausted is True


def test_attempts_exhausted_false_when_unset() -> None:
    ledger = BudgetLedger(budget=Budget()).spend_attempt()
    assert ledger.attempts_exhausted is False


def test_wall_clock_exhausted_only_when_elapsed_meets_cap() -> None:
    started = datetime(2026, 8, 13, 12, 0, tzinfo=UTC)
    ledger = BudgetLedger(budget=Budget(max_wall_clock=timedelta(hours=1)))
    assert ledger.wall_clock_exhausted(now=started + timedelta(minutes=59), started_at=started) is (
        False
    )
    assert ledger.wall_clock_exhausted(now=started + timedelta(hours=1), started_at=started) is True


def test_wall_clock_never_exhausted_when_unset() -> None:
    started = datetime(2026, 8, 13, 12, 0, tzinfo=UTC)
    ledger = BudgetLedger(budget=Budget())
    assert (
        ledger.wall_clock_exhausted(now=started + timedelta(days=365), started_at=started) is False
    )
