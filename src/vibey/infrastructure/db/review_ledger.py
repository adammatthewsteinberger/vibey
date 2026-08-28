# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Adapter between interactive-phase application events and the durable
event ledger. Defaults to REVIEW; the deploy stage set constructs additional
instances with their own phase so DEPLOY_* events are never mislabeled as
REVIEW in the append-only ledger."""

from collections.abc import Mapping
from datetime import UTC, datetime
from uuid import UUID, uuid4

from vibey.domain.ledger import EventKind, LedgerEvent, Provenance, digest_event
from vibey.domain.phase import Phase
from vibey.infrastructure.db.ledger_repository import PostgresLedgerRepository
from vibey.infrastructure.engines.tailer import LedgerEventDraft


class PostgresReviewLedger:
    def __init__(self, ledger: PostgresLedgerRepository, *, phase: Phase = Phase.REVIEW) -> None:
        self._ledger = ledger
        self._phase = phase

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
                phase=self._phase,
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
