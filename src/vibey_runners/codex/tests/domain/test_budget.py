# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Budget caps and a ledger that only moves forward."""

from __future__ import annotations

from datetime import timedelta

import pytest

from codexloop.domain.budget import Budget, BudgetLedger
from codexloop.domain.errors import ConfigurationError


def _unlimited() -> Budget:
    return Budget(max_turns=None, max_dollars=None, max_wall_clock=None)


def test_turns_cap_trips_independently() -> None:
    ledger = BudgetLedger(Budget(max_turns=2, max_dollars=None, max_wall_clock=None))
    ledger.record(turns=1, dollars=999.0, elapsed=timedelta(days=9))
    assert ledger.exceeded() is None
    ledger.record(turns=1)
    assert ledger.exceeded() == "turns"


def test_dollars_cap_trips_independently() -> None:
    ledger = BudgetLedger(Budget(max_turns=None, max_dollars=1.5, max_wall_clock=None))
    ledger.record(turns=50, dollars=1.0, elapsed=timedelta(hours=3))
    assert ledger.exceeded() is None
    ledger.record(dollars=0.5)
    assert ledger.exceeded() == "dollars"


def test_wall_clock_cap_trips_independently() -> None:
    cap = timedelta(seconds=60)
    ledger = BudgetLedger(Budget(max_turns=None, max_dollars=None, max_wall_clock=cap))
    ledger.record(turns=50, dollars=999.0, elapsed=timedelta(seconds=59))
    assert ledger.exceeded() is None
    ledger.record(elapsed=timedelta(seconds=1))
    assert ledger.exceeded() == "wall_clock"


def test_none_caps_mean_unlimited() -> None:
    ledger = BudgetLedger(_unlimited())
    ledger.record(turns=10_000, dollars=1_000_000.0, elapsed=timedelta(days=365))
    assert ledger.exceeded() is None


def test_ledger_never_goes_backwards() -> None:
    ledger = BudgetLedger(_unlimited())
    ledger.record(turns=3, dollars=1.5, elapsed=timedelta(seconds=10))
    with pytest.raises(ConfigurationError):
        ledger.record(turns=-1)
    with pytest.raises(ConfigurationError):
        ledger.record(dollars=-0.01)
    with pytest.raises(ConfigurationError):
        ledger.record(elapsed=timedelta(seconds=-1))
    assert ledger.turns == 3
    assert ledger.dollars == 1.5
    assert ledger.elapsed == timedelta(seconds=10)


def test_zero_record_does_not_change_counters() -> None:
    ledger = BudgetLedger(_unlimited())
    ledger.record(turns=2, dollars=0.25, elapsed=timedelta(seconds=5))
    ledger.record()
    assert ledger.turns == 2
    assert ledger.dollars == 0.25
    assert ledger.elapsed == timedelta(seconds=5)


def test_budget_is_frozen_slots_value() -> None:
    budget = Budget(max_turns=1, max_dollars=2.0, max_wall_clock=timedelta(seconds=3))
    assert budget.__dataclass_params__.frozen is True
    assert budget.__dataclass_params__.slots is True
    assert hash(budget) == hash(budget)
