import asyncio
from datetime import timedelta
from uuid import UUID, uuid4

import asyncpg

from vibey.application.dto import EnqueueRequest
from vibey.domain.job import JobState
from vibey.domain.phase import Phase
from vibey.infrastructure.db.job_repository import PostgresJobRepository

LEASE = timedelta(seconds=30)


def _request(project_id: UUID, subject: str = "item-001", **overrides: object) -> EnqueueRequest:
    defaults: dict[str, object] = {
        "project_id": project_id,
        "cycle": 1,
        "phase": Phase.BUILD,
        "kind": "build.implement",
        "idempotency_key": f"key-{subject}",
        "payload": {"subject": subject},
    }
    defaults.update(overrides)
    return EnqueueRequest(**defaults)  # type: ignore[arg-type]


async def test_enqueue_creates_a_ready_job(migrated_pool: asyncpg.Pool, project_id: UUID) -> None:
    repo = PostgresJobRepository(migrated_pool)

    job = await repo.enqueue(_request(project_id))

    assert job.state is JobState.READY
    assert job.project_id == project_id
    assert job.kind == "build.implement"
    assert job.payload["subject"] == "item-001"


async def test_enqueue_is_idempotent(migrated_pool: asyncpg.Pool, project_id: UUID) -> None:
    repo = PostgresJobRepository(migrated_pool)
    request = _request(project_id)

    first = await repo.enqueue(request)
    second = await repo.enqueue(request)

    assert first.id == second.id

    async with migrated_pool.acquire() as conn:
        count = await conn.fetchval(
            "SELECT count(*) FROM job WHERE project_id = $1 AND idempotency_key = $2",
            project_id,
            request.idempotency_key,
        )
    assert count == 1


async def test_claim_leases_the_highest_priority_ready_job(
    migrated_pool: asyncpg.Pool, project_id: UUID
) -> None:
    repo = PostgresJobRepository(migrated_pool)
    await repo.enqueue(_request(project_id, subject="low", priority=0))
    high = await repo.enqueue(_request(project_id, subject="high", priority=10))

    claimed = await repo.claim(project_id, owner="worker-1", lease=LEASE)

    assert claimed is not None
    assert claimed.id == high.id
    assert claimed.state is JobState.LEASED
    assert claimed.lease_owner == "worker-1"
    assert claimed.attempts == 1


async def test_claim_returns_none_when_nothing_ready(
    migrated_pool: asyncpg.Pool, project_id: UUID
) -> None:
    repo = PostgresJobRepository(migrated_pool)
    assert await repo.claim(project_id, owner="worker-1", lease=LEASE) is None


async def test_two_workers_never_claim_the_same_job(
    migrated_pool: asyncpg.Pool, project_id: UUID
) -> None:
    repo = PostgresJobRepository(migrated_pool)
    job = await repo.enqueue(_request(project_id))

    results = await asyncio.gather(
        repo.claim(project_id, owner="worker-1", lease=LEASE),
        repo.claim(project_id, owner="worker-2", lease=LEASE),
    )

    non_none = [r for r in results if r is not None]
    assert len(non_none) == 1
    assert non_none[0].id == job.id


async def test_heartbeat_extends_the_lease(migrated_pool: asyncpg.Pool, project_id: UUID) -> None:
    repo = PostgresJobRepository(migrated_pool)
    job = await repo.enqueue(_request(project_id))
    claimed = await repo.claim(project_id, owner="worker-1", lease=LEASE)
    assert claimed is not None

    ok = await repo.heartbeat(job.id, owner="worker-1", lease=LEASE)

    assert ok is True


async def test_heartbeat_fails_for_wrong_owner(
    migrated_pool: asyncpg.Pool, project_id: UUID
) -> None:
    repo = PostgresJobRepository(migrated_pool)
    job = await repo.enqueue(_request(project_id))
    await repo.claim(project_id, owner="worker-1", lease=LEASE)

    ok = await repo.heartbeat(job.id, owner="worker-2", lease=LEASE)

    assert ok is False


async def test_ack_marks_succeeded_and_releases_lease(
    migrated_pool: asyncpg.Pool, project_id: UUID
) -> None:
    repo = PostgresJobRepository(migrated_pool)
    job = await repo.enqueue(_request(project_id))
    await repo.claim(project_id, owner="worker-1", lease=LEASE)

    ok = await repo.ack(job.id, owner="worker-1")

    assert ok is True
    record = await repo.get(job.id)
    assert record is not None
    assert record.state is JobState.SUCCEEDED
    assert record.lease_owner is None


async def test_nack_reschedules_as_ready_when_attempts_remain(
    migrated_pool: asyncpg.Pool, project_id: UUID
) -> None:
    repo = PostgresJobRepository(migrated_pool)
    job = await repo.enqueue(_request(project_id, max_attempts=7))
    await repo.claim(project_id, owner="worker-1", lease=LEASE)

    ok = await repo.nack(job.id, owner="worker-1", error={"message": "boom"})

    assert ok is True
    record = await repo.get(job.id)
    assert record is not None
    assert record.state is JobState.READY
    assert record.last_error == {"message": "boom"}


async def test_nack_marks_failed_once_max_attempts_reached(
    migrated_pool: asyncpg.Pool, project_id: UUID
) -> None:
    repo = PostgresJobRepository(migrated_pool)
    job = await repo.enqueue(_request(project_id, max_attempts=1))
    await repo.claim(project_id, owner="worker-1", lease=LEASE)

    await repo.nack(job.id, owner="worker-1", error={"message": "boom"})

    record = await repo.get(job.id)
    assert record is not None
    assert record.state is JobState.FAILED


async def test_park_sets_awaiting_human_and_releases_lease(
    migrated_pool: asyncpg.Pool, project_id: UUID
) -> None:
    repo = PostgresJobRepository(migrated_pool)
    job = await repo.enqueue(_request(project_id))
    await repo.claim(project_id, owner="worker-1", lease=LEASE)

    ok = await repo.park(job.id, owner="worker-1")

    assert ok is True
    record = await repo.get(job.id)
    assert record is not None
    assert record.state is JobState.AWAITING_HUMAN
    assert record.lease_owner is None

    # A parked job is not claimable -- it is not 'ready'.
    assert await repo.claim(project_id, owner="worker-2", lease=LEASE) is None


async def test_reap_reclaims_expired_leases(migrated_pool: asyncpg.Pool, project_id: UUID) -> None:
    repo = PostgresJobRepository(migrated_pool)
    job = await repo.enqueue(_request(project_id))
    await repo.claim(project_id, owner="worker-1", lease=timedelta(seconds=-1))

    reclaimed = await repo.reap()

    assert reclaimed == 1
    record = await repo.get(job.id)
    assert record is not None
    assert record.state is JobState.READY
    assert record.lease_owner is None


async def test_dependency_gating_blocks_claim_until_dependency_succeeds(
    migrated_pool: asyncpg.Pool, project_id: UUID
) -> None:
    repo = PostgresJobRepository(migrated_pool)
    upstream = await repo.enqueue(_request(project_id, subject="upstream"))
    downstream = await repo.enqueue(
        _request(project_id, subject="downstream", depends_on=(upstream.id,))
    )

    # Only the upstream job is claimable; downstream must never be offered.
    first_claim = await repo.claim(project_id, owner="worker-1", lease=LEASE)
    assert first_claim is not None
    assert first_claim.id == upstream.id

    second_claim = await repo.claim(project_id, owner="worker-1", lease=LEASE)
    assert second_claim is None

    await repo.ack(upstream.id, owner="worker-1")

    third_claim = await repo.claim(project_id, owner="worker-1", lease=LEASE)
    assert third_claim is not None
    assert third_claim.id == downstream.id


async def test_get_returns_none_for_unknown_job(migrated_pool: asyncpg.Pool) -> None:
    repo = PostgresJobRepository(migrated_pool)
    assert await repo.get(uuid4()) is None
