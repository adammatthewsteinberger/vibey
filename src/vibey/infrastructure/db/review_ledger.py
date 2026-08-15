"""Adapter between REVIEW application events and the durable event ledger."""

from collections.abc import Mapping
from datetime import UTC, datetime
from uuid import UUID, uuid4

from vibey.domain.ledger import EventKind, LedgerEvent, Provenance, digest_event
from vibey.domain.phase import Phase
from vibey.infrastructure.db.ledger_repository import PostgresLedgerRepository
from vibey.infrastructure.engines.tailer import LedgerEventDraft


class PostgresReviewLedger:
    def __init__(self, ledger: PostgresLedgerRepository) -> None:
        self._ledger = ledger

    async def all_for_project(self, project_id: UUID) -> tuple[LedgerEvent, ...]:
        return await self._ledger.all_for_project(project_id)

    async def append_event(
        self,
        project_id: UUID,
        cycle: int,
        job_id: UUID,
        kind: EventKind,
        payload: Mapping[str, object],
    ) -> None:
        p = dict(payload)
        await self._ledger.append(
            LedgerEventDraft(
                project_id=project_id,
                cycle=cycle,
                phase=Phase.REVIEW,
                kind=kind,
                engine_id=None,
                job_id=job_id,
                causation_id=None,
                correlation_id=uuid4(),
                provenance=Provenance.TRUSTED,
                produced_at=datetime.now(UTC),
                payload=p,
                digest=digest_event(p),
            )
        )
