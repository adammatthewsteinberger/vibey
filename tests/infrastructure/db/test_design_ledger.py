# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
from datetime import UTC, datetime
from uuid import UUID, uuid4

import asyncpg

from vibey.application.design import DesignEvent
from vibey.domain.engine import EngineId
from vibey.domain.ledger import EventKind, Provenance
from vibey.infrastructure.db.design_ledger import PostgresDesignLedger
from vibey.infrastructure.db.ledger_repository import PostgresLedgerRepository


async def test_design_events_round_trip_through_real_append_only_ledger(
    migrated_pool: asyncpg.Pool, project_id: UUID
) -> None:
    ledger = PostgresDesignLedger(PostgresLedgerRepository(migrated_pool))
    job_id = uuid4()
    event = DesignEvent(
        EventKind.QUESTION_ASKED,
        Provenance.AGENT,
        datetime(2026, 8, 14, tzinfo=UTC),
        {
            "item_id": "q-1",
            "text": "Who uses it?",
            "default": "A developer",
            "blocking": True,
            "stage": "context_free",
        },
    )
    await ledger.append(project_id, 1, job_id, EngineId.CLAUDELOOP, event)

    replayed = await ledger.all_for_project(project_id)
    assert replayed == (event,)
