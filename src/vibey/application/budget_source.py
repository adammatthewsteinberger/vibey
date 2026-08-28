# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""The production BudgetSource: per-cycle spend summed from the ledger,
with the caps the project was configured with.

This is the runaway brake for unattended runs. The repair storms burned
real money precisely because nothing capped cycle spend -- every engine
session reports its cost into the ledger, so the ledger is the one
durable, replay-safe place to enforce a ceiling from.

Two event shapes carry spend, and both must count:

- TURN_COMPLETED: what the engines actually write. Each completed turn
  is one turn spent, and claudeloop-family engines attach the turn's
  real ``cost_usd``. The greeter4 live run proved this is the ONLY
  place real dollars land -- the brake was blind until it read them.
- BUDGET_SPENT with explicit ``dollars``/``turns``: the vendor-neutral
  shape (grant adjustments, replays, synthetic corrections). Production
  engine translation also maps capacity/usage chatter to BUDGET_SPENT
  with neither key; those sum as zero rather than erroring.
"""

from uuid import UUID

from vibey.application.interfaces import LedgerReader
from vibey.domain.budget import BudgetLedger
from vibey.domain.ledger import EventKind


class LedgerBudgetSource:
    def __init__(
        self,
        ledger_reader: LedgerReader,
        *,
        max_turns: int | None = None,
        max_dollars: float | None = None,
    ) -> None:
        self._ledger_reader = ledger_reader
        self._max_turns = max_turns
        self._max_dollars = max_dollars

    async def current(self, project_id: UUID, cycle: int) -> BudgetLedger:
        dollars = 0.0
        turns = 0
        for event in await self._ledger_reader.all_for_project(project_id):
            if event.cycle != cycle:
                continue
            if event.kind is EventKind.TURN_COMPLETED:
                turns += 1
                raw_cost = event.payload.get("cost_usd", 0.0)
                if isinstance(raw_cost, int | float):
                    dollars += float(raw_cost)
            elif event.kind is EventKind.BUDGET_SPENT:
                raw_dollars = event.payload.get("dollars", 0.0)
                raw_turns = event.payload.get("turns", 0)
                if isinstance(raw_dollars, int | float):
                    dollars += float(raw_dollars)
                if isinstance(raw_turns, int):
                    turns += raw_turns
        return BudgetLedger(
            turns_spent=turns,
            dollars_spent=dollars,
            max_turns=self._max_turns,
            max_dollars=self._max_dollars,
        )
