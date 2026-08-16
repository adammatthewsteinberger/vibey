import asyncio
from datetime import UTC, datetime
from uuid import UUID, uuid4

import asyncpg
import pytest

from vibey.domain.ledger import EventKind, Provenance, digest_event
from vibey.domain.phase import Phase
from vibey.infrastructure.db.ledger_repository import PostgresLedgerRepository
from vibey.infrastructure.engines.tailer import LedgerEventDraft

NOW = datetime(2026, 1, 1, tzinfo=UTC)


def _draft(project_id: UUID, **overrides: object) -> LedgerEventDraft:
    payload = {"prompt_digest": "abc"}
    defaults: dict[str, object] = {
        "project_id": project_id,
        "cycle": 1,
        "phase": Phase.BUILD,
        "kind": EventKind.TURN_REQUESTED,
        "engine_id": None,
        "job_id": None,
        "causation_id": None,
        "correlation_id": uuid4(),
        "provenance": Provenance.AGENT,
        "produced_at": NOW,
        "payload": payload,
        "digest": digest_event(payload),
    }
    defaults.update(overrides)
    return LedgerEventDraft(**defaults)  # type: ignore[arg-type]


async def test_append_assigns_seq_starting_at_one(
    migrated_pool: asyncpg.Pool, project_id: UUID
) -> None:
    repo = PostgresLedgerRepository(migrated_pool)

    event = await repo.append(_draft(project_id))

    assert event.seq == 1
    assert event.project_id == project_id
    assert event.produced_at == NOW


async def test_append_seq_increments_sequentially(
    migrated_pool: asyncpg.Pool, project_id: UUID
) -> None:
    repo = PostgresLedgerRepository(migrated_pool)

    e1 = await repo.append(_draft(project_id))
    e2 = await repo.append(_draft(project_id))
    e3 = await repo.append(_draft(project_id))

    assert [e1.seq, e2.seq, e3.seq] == [1, 2, 3]


async def test_seq_is_scoped_per_project(migrated_pool: asyncpg.Pool) -> None:
    repo = PostgresLedgerRepository(migrated_pool)
    async with migrated_pool.acquire() as conn:
        p1 = await conn.fetchval(
            "INSERT INTO project (name, repo_path, config) "
            "VALUES ('a','/a','{}'::jsonb) RETURNING id"
        )
        p2 = await conn.fetchval(
            "INSERT INTO project (name, repo_path, config) "
            "VALUES ('b','/b','{}'::jsonb) RETURNING id"
        )

    e1 = await repo.append(_draft(UUID(str(p1))))
    e2 = await repo.append(_draft(UUID(str(p2))))

    assert e1.seq == 1
    assert e2.seq == 1


async def test_range_returns_events_in_seq_order(
    migrated_pool: asyncpg.Pool, project_id: UUID
) -> None:
    repo = PostgresLedgerRepository(migrated_pool)
    for _ in range(5):
        await repo.append(_draft(project_id))

    events = await repo.range(project_id, from_seq=2, to_seq=4)

    assert [e.seq for e in events] == [2, 3, 4]


async def test_latest_seq_reflects_appends(migrated_pool: asyncpg.Pool, project_id: UUID) -> None:
    repo = PostgresLedgerRepository(migrated_pool)
    assert await repo.latest_seq(project_id) == 0

    await repo.append(_draft(project_id))
    await repo.append(_draft(project_id))

    assert await repo.latest_seq(project_id) == 2


async def test_planted_secret_never_reaches_the_column(
    migrated_pool: asyncpg.Pool, project_id: UUID
) -> None:
    repo = PostgresLedgerRepository(migrated_pool)
    planted = "sk-" + "z" * 20
    draft = _draft(project_id, payload={"summary": f"logged in with {planted}"})

    event = await repo.append(draft)

    assert planted not in str(event.payload)
    async with migrated_pool.acquire() as conn:
        raw = await conn.fetchval(
            "SELECT payload::text FROM event WHERE event_id = $1", event.event_id
        )
    assert planted not in raw


async def test_update_event_is_a_silent_no_op(
    migrated_pool: asyncpg.Pool, project_id: UUID
) -> None:
    repo = PostgresLedgerRepository(migrated_pool)
    event = await repo.append(_draft(project_id))

    async with migrated_pool.acquire() as conn:
        await conn.execute(
            "UPDATE event SET kind = 'PhaseTransitioned' WHERE event_id = $1", event.event_id
        )
        row = await conn.fetchrow("SELECT kind FROM event WHERE event_id = $1", event.event_id)

    assert row is not None
    assert row["kind"] == EventKind.TURN_REQUESTED.value


async def test_delete_event_is_a_silent_no_op(
    migrated_pool: asyncpg.Pool, project_id: UUID
) -> None:
    repo = PostgresLedgerRepository(migrated_pool)
    event = await repo.append(_draft(project_id))

    async with migrated_pool.acquire() as conn:
        await conn.execute("DELETE FROM event WHERE event_id = $1", event.event_id)
        count = await conn.fetchval(
            "SELECT count(*) FROM event WHERE event_id = $1", event.event_id
        )

    assert count == 1


@pytest.mark.slow
async def test_concurrent_appends_are_gapless_and_have_no_duplicates(
    migrated_pool: asyncpg.Pool, project_id: UUID
) -> None:
    """4.1's concurrency test: 100 parallel appends produce exactly the
    sequence 1..100 with no gaps and no duplicates."""
    repo = PostgresLedgerRepository(migrated_pool)

    results = await asyncio.gather(*(repo.append(_draft(project_id)) for _ in range(100)))

    seqs = sorted(e.seq for e in results)
    assert seqs == list(range(1, 101))
