# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class BudgetLedger:
    turns_spent: int
    dollars_spent: float
    max_turns: int | None
    max_dollars: float | None

    @property
    def any_exhausted(self) -> bool:
        if self.max_turns is not None and self.turns_spent >= self.max_turns:
            return True
        return self.max_dollars is not None and self.dollars_spent >= self.max_dollars

    def would_exceed(self, projected: float) -> bool:
        """Checked before an effort escalation, not after: the escalation
        ladder is the mechanism most likely to cause a cost snowball, so the
        cap is evaluated on the projection, not the outcome."""
        if self.max_dollars is None:
            return False
        return self.dollars_spent + projected > self.max_dollars

    def spend(self, *, turns: int = 0, dollars: float = 0.0) -> "BudgetLedger":
        return BudgetLedger(
            turns_spent=self.turns_spent + turns,
            dollars_spent=self.dollars_spent + dollars,
            max_turns=self.max_turns,
            max_dollars=self.max_dollars,
        )
