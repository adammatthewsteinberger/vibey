# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
import pytest

from agyloop.domain.budget import Budget, BudgetLedger


@pytest.mark.parametrize("field", ["max_turns", "max_tokens", "max_attempts", "max_dollars"])
def test_budget_rejects_nonpositive_values(field: str) -> None:
    with pytest.raises(ValueError):
        Budget(**{field: 0})


def test_budget_all_none_is_valid() -> None:
    Budget()


def test_budget_turns_and_tokens_are_first_class() -> None:
    budget = Budget(max_turns=10, max_tokens=50_000)
    assert budget.max_turns == 10
    assert budget.max_tokens == 50_000
    assert budget.max_dollars is None


def test_ledger_spend_turn_increments_turns_tokens_and_optional_dollars() -> None:
    ledger = BudgetLedger(budget=Budget())
    ledger = ledger.spend_turn(tokens=120, dollars=1.5)
    assert ledger.turns_spent == 1
    assert ledger.tokens_spent == 120
    assert ledger.dollars_spent == 1.5


def test_ledger_immutable_spend_returns_new_instance() -> None:
    original = BudgetLedger(budget=Budget())
    spent = original.spend_turn(tokens=5)
    assert original.turns_spent == 0
    assert original.tokens_spent == 0
    assert spent.turns_spent == 1
    assert spent.tokens_spent == 5


def test_ledger_spend_attempt() -> None:
    ledger = BudgetLedger(budget=Budget()).spend_attempt()
    assert ledger.attempts_spent == 1


def test_turns_exhausted_true_at_cap() -> None:
    ledger = BudgetLedger(budget=Budget(max_turns=2))
    ledger = ledger.spend_turn().spend_turn()
    assert ledger.turns_exhausted is True
    assert ledger.any_exhausted is True


def test_turns_exhausted_false_below_cap() -> None:
    ledger = BudgetLedger(budget=Budget(max_turns=2)).spend_turn()
    assert ledger.turns_exhausted is False


def test_turns_exhausted_false_when_unset() -> None:
    ledger = BudgetLedger(budget=Budget()).spend_turn()
    assert ledger.turns_exhausted is False


def test_tokens_exhausted() -> None:
    ledger = BudgetLedger(budget=Budget(max_tokens=100)).spend_turn(tokens=100)
    assert ledger.tokens_exhausted is True
    assert ledger.any_exhausted is True


def test_tokens_exhausted_false_below_cap() -> None:
    ledger = BudgetLedger(budget=Budget(max_tokens=100)).spend_turn(tokens=40)
    assert ledger.tokens_exhausted is False


def test_tokens_exhausted_false_when_unset() -> None:
    ledger = BudgetLedger(budget=Budget()).spend_turn(tokens=1_000_000)
    assert ledger.tokens_exhausted is False


def test_dollars_exhausted_when_optional_estimate_is_set() -> None:
    ledger = BudgetLedger(budget=Budget(max_dollars=10.0)).spend_turn(dollars=10.0)
    assert ledger.dollars_exhausted is True
    assert ledger.any_exhausted is True


def test_dollars_exhausted_false_when_unset() -> None:
    ledger = BudgetLedger(budget=Budget()).spend_turn(dollars=1_000_000.0)
    assert ledger.dollars_exhausted is False


def test_attempts_exhausted() -> None:
    ledger = BudgetLedger(budget=Budget(max_attempts=1)).spend_attempt()
    assert ledger.attempts_exhausted is True
    assert ledger.any_exhausted is True


def test_attempts_exhausted_false_when_unset() -> None:
    ledger = BudgetLedger(budget=Budget()).spend_attempt()
    assert ledger.attempts_exhausted is False


def test_no_budget_never_exhausted() -> None:
    ledger = BudgetLedger(budget=Budget())
    for _ in range(1000):
        ledger = ledger.spend_turn(tokens=1, dollars=1.0).spend_attempt()
    assert ledger.any_exhausted is False
