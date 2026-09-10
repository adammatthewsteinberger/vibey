# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Turn / dollar / wall-clock budgets and a monotonic ledger."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

from codexloop.domain.errors import ConfigurationError

_ZERO = timedelta(0)


@dataclass(frozen=True, slots=True)
class Budget:
    max_turns: int | None
    max_dollars: float | None
    max_wall_clock: timedelta | None


class BudgetLedger:
    """Accumulates usage against a :class:`Budget`. Counters never decrease."""

    def __init__(self, budget: Budget) -> None:
        self._budget = budget
        self._turns = 0
        self._dollars = 0.0
        self._elapsed = _ZERO

    @property
    def turns(self) -> int:
        return self._turns

    @property
    def dollars(self) -> float:
        return self._dollars

    @property
    def elapsed(self) -> timedelta:
        return self._elapsed

    def record(self, turns: int = 0, dollars: float = 0.0, elapsed: timedelta = _ZERO) -> None:
        if turns < 0 or dollars < 0 or elapsed < _ZERO:
            raise ConfigurationError("budget ledger cannot decrease")
        self._turns += turns
        self._dollars += dollars
        self._elapsed += elapsed

    def exceeded(self) -> str | None:
        budget = self._budget
        if budget.max_turns is not None and self._turns >= budget.max_turns:
            return "turns"
        if budget.max_dollars is not None and self._dollars >= budget.max_dollars:
            return "dollars"
        if budget.max_wall_clock is not None and self._elapsed >= budget.max_wall_clock:
            return "wall_clock"
        return None
