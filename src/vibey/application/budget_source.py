"""The production BudgetSource: per-cycle spend summed from the ledger's
own BUDGET_SPENT events, with the caps the project was configured with.

This is the runaway brake for unattended runs. The repair storms burned
real money precisely because nothing capped cycle spend -- every engine
session reports its cost into the ledger, so the ledger is the one
durable, replay-safe place to enforce a ceiling from.
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
            if event.cycle != cycle or event.kind is not EventKind.BUDGET_SPENT:
                continue
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
