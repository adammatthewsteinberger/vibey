# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Budget guardrails for an unattended, potentially multi-hour/multi-day run.

Tokens are the enforceable hard cap. ``cost is None`` from ``get_usage()`` means
UNKNOWN, never zero: treating a settling None as ``$0.00`` would blow straight
through ``--max-cost``. Dollars are a best-effort secondary cap; ``cost_pending``
records that the billed total is incomplete.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timedelta


@dataclass(frozen=True, slots=True)
class Budget:
    max_turns: int | None = None
    max_tokens: int | None = None
    max_cost_usd: float | None = None
    max_attempts: int | None = None
    max_wall_clock: timedelta | None = None

    def __post_init__(self) -> None:
        for name, value in (
            ("max_turns", self.max_turns),
            ("max_tokens", self.max_tokens),
            ("max_cost_usd", self.max_cost_usd),
            ("max_attempts", self.max_attempts),
        ):
            if value is not None and value <= 0:
                raise ValueError(f"{name} must be positive when set")
        if self.max_wall_clock is not None and self.max_wall_clock <= timedelta(0):
            raise ValueError("max_wall_clock must be positive when set")


@dataclass(frozen=True, slots=True)
class BudgetLedger:
    """Tracks consumption against a Budget. Immutable — every spend returns a new
    ledger, so the run loop's state transitions stay pure and testable."""

    budget: Budget
    turns_spent: int = 0
    tokens_spent: int = 0
    dollars_spent: float = 0.0
    attempts_spent: int = 0
    cost_pending: bool = False

    def spend_turn(self, tokens: int, dollars: float | None) -> BudgetLedger:
        pending = self.cost_pending or dollars is None
        added = 0.0 if dollars is None else dollars
        return replace(
            self,
            turns_spent=self.turns_spent + 1,
            tokens_spent=self.tokens_spent + tokens,
            dollars_spent=self.dollars_spent + added,
            cost_pending=pending,
        )

    def spend_attempt(self) -> BudgetLedger:
        return replace(self, attempts_spent=self.attempts_spent + 1)

    def wall_clock_exhausted(self, *, now: datetime, started_at: datetime) -> bool:
        if self.budget.max_wall_clock is None:
            return False
        return (now - started_at) >= self.budget.max_wall_clock

    @property
    def turns_exhausted(self) -> bool:
        return self.budget.max_turns is not None and self.turns_spent >= self.budget.max_turns

    @property
    def tokens_exhausted(self) -> bool:
        return self.budget.max_tokens is not None and self.tokens_spent >= self.budget.max_tokens

    @property
    def dollars_exhausted(self) -> bool:
        return (
            self.budget.max_cost_usd is not None and self.dollars_spent >= self.budget.max_cost_usd
        )

    @property
    def attempts_exhausted(self) -> bool:
        return (
            self.budget.max_attempts is not None and self.attempts_spent >= self.budget.max_attempts
        )

    @property
    def any_exhausted(self) -> bool:
        return (
            self.turns_exhausted
            or self.tokens_exhausted
            or self.dollars_exhausted
            or self.attempts_exhausted
        )
