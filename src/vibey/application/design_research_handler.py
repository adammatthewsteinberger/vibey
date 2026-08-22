# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
"""``design.research`` handler with forced untrusted provenance."""

from vibey.application.design import research_event
from vibey.application.design_handler import DesignLedger
from vibey.application.dto import JobRecord
from vibey.application.interfaces import (
    ResearchProvider,
)
from vibey.application.ports import Clock
from vibey.application.worker import Failure, Outcome, Success
from vibey.domain.engine import EngineId
from vibey.domain.job import FailureClass


class DesignResearchHandler:
    def __init__(
        self,
        *,
        ledger: DesignLedger,
        researcher: ResearchProvider,
        clock: Clock,
        engine_id: EngineId,
    ) -> None:
        self._ledger = ledger
        self._researcher = researcher
        self._clock = clock
        self._engine_id = engine_id

    async def handle(self, job: JobRecord) -> Outcome:
        if job.kind != "design.research":
            return Failure(FailureClass.VIBEY, "expected design.research job")
        topic = str(job.payload.get("topic", "")).strip()
        if not topic:
            return Failure(FailureClass.WORK, "design.research requires a topic")
        result = await self._researcher.research(topic)
        event = research_event(result, now=self._clock.now())
        await self._ledger.append(job.project_id, job.cycle, job.id, self._engine_id, event)
        return Success({"topic": topic, "source": result.source})


# Re-exported for the same reason `application/ports.py` re-exports the
# interfaces package: the seam moved, the import path should not break.
__all__ = [
    "ResearchProvider",
]
