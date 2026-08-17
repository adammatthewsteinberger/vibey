"""Adapter between BUILD application events (raw EngineAdapter output) and
the durable event ledger. Translation lives here, not in application/,
because infrastructure/engines/tailer.py is off-limits to application/ under
the onion contract."""

from uuid import UUID

from vibey.application.dto import EngineEvent
from vibey.domain.engine import EngineId
from vibey.domain.phase import Phase
from vibey.infrastructure.db.ledger_repository import PostgresLedgerRepository
from vibey.infrastructure.engines.tailer import translate_event


class PostgresBuildLedger:
    def __init__(self, ledger: PostgresLedgerRepository) -> None:
        self._ledger = ledger

    async def record(
        self,
        *,
        project_id: UUID,
        cycle: int,
        job_id: UUID,
        engine_id: EngineId | None,
        correlation_id: UUID,
        event: EngineEvent,
    ) -> None:
        draft = translate_event(
            event,
            project_id=project_id,
            cycle=cycle,
            phase=Phase.BUILD,
            engine_id=engine_id,
            job_id=job_id,
            correlation_id=correlation_id,
        )
        if draft is not None:
            await self._ledger.append(draft)
