# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://hire.adam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
from vibey.domain.budget import BudgetLedger


def _ledger(**overrides: object) -> BudgetLedger:
    defaults: dict[str, object] = {
        "turns_spent": 0,
        "dollars_spent": 0.0,
        "max_turns": 60,
        "max_dollars": 40.0,
    }
    defaults.update(overrides)
    return BudgetLedger(**defaults)  # type: ignore[arg-type]


def test_any_exhausted_false_when_under_caps() -> None:
    assert _ledger(turns_spent=1, dollars_spent=1.0).any_exhausted is False


def test_any_exhausted_true_when_turns_cap_hit() -> None:
    assert _ledger(turns_spent=60).any_exhausted is True


def test_any_exhausted_true_when_dollar_cap_hit() -> None:
    assert _ledger(dollars_spent=40.0).any_exhausted is True


def test_any_exhausted_false_when_caps_are_none() -> None:
    ledger = _ledger(turns_spent=10_000, dollars_spent=10_000.0, max_turns=None, max_dollars=None)
    assert ledger.any_exhausted is False


def test_would_exceed_true_when_projection_crosses_cap() -> None:
    ledger = _ledger(dollars_spent=35.0, max_dollars=40.0)
    assert ledger.would_exceed(10.0) is True
    assert ledger.would_exceed(4.0) is False


def test_would_exceed_false_when_no_dollar_cap() -> None:
    ledger = _ledger(max_dollars=None)
    assert ledger.would_exceed(1_000_000.0) is False


def test_spend_returns_a_new_ledger_with_accumulated_totals() -> None:
    ledger = _ledger(turns_spent=1, dollars_spent=1.0)
    spent = ledger.spend(turns=2, dollars=3.5)

    assert spent.turns_spent == 3
    assert spent.dollars_spent == 4.5
    # original is untouched (frozen/immutable update)
    assert ledger.turns_spent == 1
    assert ledger.dollars_spent == 1.0


def test_spend_defaults_to_zero() -> None:
    ledger = _ledger(turns_spent=5, dollars_spent=5.0)
    assert ledger.spend() == ledger
