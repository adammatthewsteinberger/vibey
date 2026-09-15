# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
import pytest

from claudeloop.domain.budget import Budget, BudgetLedger


@pytest.mark.parametrize("field", ["max_turns", "max_dollars", "max_attempts"])
def test_budget_rejects_nonpositive_values(field):
    with pytest.raises(ValueError):
        Budget(**{field: 0})


def test_budget_all_none_is_valid():
    Budget()


def test_ledger_spend_turn_increments_turns_and_dollars():
    ledger = BudgetLedger(budget=Budget())
    ledger = ledger.spend_turn(dollars=1.5)
    assert ledger.turns_spent == 1
    assert ledger.dollars_spent == 1.5


def test_ledger_immutable_spend_returns_new_instance():
    original = BudgetLedger(budget=Budget())
    spent = original.spend_turn()
    assert original.turns_spent == 0
    assert spent.turns_spent == 1


def test_ledger_spend_attempt():
    ledger = BudgetLedger(budget=Budget()).spend_attempt()
    assert ledger.attempts_spent == 1


def test_turns_exhausted_true_at_cap():
    ledger = BudgetLedger(budget=Budget(max_turns=2))
    ledger = ledger.spend_turn().spend_turn()
    assert ledger.turns_exhausted is True
    assert ledger.any_exhausted is True


def test_turns_exhausted_false_below_cap():
    ledger = BudgetLedger(budget=Budget(max_turns=2)).spend_turn()
    assert ledger.turns_exhausted is False


def test_turns_exhausted_false_when_unset():
    ledger = BudgetLedger(budget=Budget()).spend_turn()
    assert ledger.turns_exhausted is False


def test_dollars_exhausted():
    ledger = BudgetLedger(budget=Budget(max_dollars=10.0)).spend_turn(dollars=10.0)
    assert ledger.dollars_exhausted is True
    assert ledger.any_exhausted is True


def test_dollars_exhausted_false_when_unset():
    ledger = BudgetLedger(budget=Budget()).spend_turn(dollars=1_000_000.0)
    assert ledger.dollars_exhausted is False


def test_attempts_exhausted():
    ledger = BudgetLedger(budget=Budget(max_attempts=1)).spend_attempt()
    assert ledger.attempts_exhausted is True
    assert ledger.any_exhausted is True


def test_attempts_exhausted_false_when_unset():
    ledger = BudgetLedger(budget=Budget()).spend_attempt()
    assert ledger.attempts_exhausted is False


def test_no_budget_never_exhausted():
    ledger = BudgetLedger(budget=Budget())
    for _ in range(1000):
        ledger = ledger.spend_turn(dollars=1.0).spend_attempt()
    assert ledger.any_exhausted is False
