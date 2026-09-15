# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Budget guardrails for an unattended, potentially multi-hour/multi-day run."""

from __future__ import annotations

from dataclasses import dataclass, replace


@dataclass(frozen=True, slots=True)
class Budget:
    max_turns: int | None = None
    max_dollars: float | None = None
    max_attempts: int | None = None

    def __post_init__(self) -> None:
        for name, value in (
            ("max_turns", self.max_turns),
            ("max_dollars", self.max_dollars),
            ("max_attempts", self.max_attempts),
        ):
            if value is not None and value <= 0:
                raise ValueError(f"{name} must be positive when set")


@dataclass(frozen=True, slots=True)
class BudgetLedger:
    """Tracks consumption against a Budget. Immutable — every spend returns a new
    ledger, so the run loop's state transitions stay pure and testable."""

    budget: Budget
    turns_spent: int = 0
    dollars_spent: float = 0.0
    attempts_spent: int = 0

    def spend_turn(self, *, dollars: float = 0.0) -> BudgetLedger:
        return replace(
            self,
            turns_spent=self.turns_spent + 1,
            dollars_spent=self.dollars_spent + dollars,
        )

    def spend_attempt(self) -> BudgetLedger:
        return replace(self, attempts_spent=self.attempts_spent + 1)

    @property
    def turns_exhausted(self) -> bool:
        return self.budget.max_turns is not None and self.turns_spent >= self.budget.max_turns

    @property
    def dollars_exhausted(self) -> bool:
        return self.budget.max_dollars is not None and self.dollars_spent >= self.budget.max_dollars

    @property
    def attempts_exhausted(self) -> bool:
        return (
            self.budget.max_attempts is not None and self.attempts_spent >= self.budget.max_attempts
        )

    @property
    def any_exhausted(self) -> bool:
        return self.turns_exhausted or self.dollars_exhausted or self.attempts_exhausted
