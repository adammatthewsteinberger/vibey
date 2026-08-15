from pathlib import Path
from uuid import uuid4

import asyncpg

from vibey.domain.ledger import EventKind
from vibey.domain.phase import Phase
from vibey.infrastructure.db.ledger_repository import PostgresLedgerRepository
from vibey.infrastructure.db.project_repository import PostgresProjectRepository
from vibey.infrastructure.db.review_ledger import PostgresReviewLedger


async def test_postgres_review_ledger(migrated_pool: asyncpg.Pool, tmp_path: Path) -> None:
    projects = PostgresProjectRepository(migrated_pool)
    project = await projects.create("review-proj", tmp_path, max_cycles=5, config={})
    ledger_repo = PostgresLedgerRepository(migrated_pool)
    review_ledger = PostgresReviewLedger(ledger_repo)

    job_id = uuid4()
    await review_ledger.append_event(
        project.project_id,
        1,
        job_id,
        EventKind.ARTIFACT_PRODUCED,
        {"artifact_id": "review-demo", "cycle": 1},
    )

    events = await review_ledger.all_for_project(project.project_id)
    assert len(events) == 1
    assert events[0].kind == EventKind.ARTIFACT_PRODUCED
    assert events[0].phase == Phase.REVIEW
