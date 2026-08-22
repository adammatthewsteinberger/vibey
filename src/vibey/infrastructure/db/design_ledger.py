# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
"""Adapter between DESIGN application events and the durable event ledger."""

from uuid import UUID, uuid4

from vibey.application.design import DesignEvent
from vibey.domain.engine import EngineId
from vibey.domain.ledger import digest_event
from vibey.domain.phase import Phase
from vibey.infrastructure.db.ledger_repository import PostgresLedgerRepository
from vibey.infrastructure.engines.tailer import LedgerEventDraft


class PostgresDesignLedger:
    def __init__(self, ledger: PostgresLedgerRepository) -> None:
        self._ledger = ledger

    async def append(
        self,
        project_id: UUID,
        cycle: int,
        job_id: UUID | None,
        engine_id: EngineId | None,
        event: DesignEvent,
    ) -> None:
        payload = dict(event.payload)
        await self._ledger.append(
            LedgerEventDraft(
                project_id=project_id,
                cycle=cycle,
                phase=Phase.DESIGN,
                kind=event.kind,
                engine_id=engine_id,
                job_id=job_id,
                causation_id=None,
                correlation_id=uuid4(),
                provenance=event.provenance,
                produced_at=event.produced_at,
                payload=payload,
                digest=digest_event(payload),
            )
        )

    async def all_for_project(self, project_id: UUID) -> tuple[DesignEvent, ...]:
        events = await self._ledger.all_for_project(project_id)
        return tuple(
            DesignEvent(
                kind=event.kind,
                provenance=event.provenance,
                produced_at=event.produced_at,
                payload=event.payload,
            )
            for event in events
            if event.phase is Phase.DESIGN
        )
