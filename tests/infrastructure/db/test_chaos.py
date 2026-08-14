"""The single most important test in M2 (implementation-plan.md 2.8).

The plan calls for 8 workers processing 500 jobs while a random worker is
SIGKILLed every 2 seconds. Reaching for `docker`/testcontainers to spin up
separate OS processes and kill -9 them is out of reach in this environment
(no docker daemon available), so this is a scoped-down but still real
chaos test: 8 concurrent asyncio workers against a real local Postgres,
each of which randomly abandons a claimed job mid-flight -- exactly the
observable effect of a SIGKILLed worker, since the worker never gets to
ack, nack, or heartbeat again and the lease is left to expire. A
concurrent reaper reclaims those expired leases, same as production.

What's verified is the property the real chaos test exists to protect:
zero double-execution, zero lost jobs, every job reaches a terminal state.
"""

import asyncio
import random
from datetime import timedelta
from uuid import UUID

import asyncpg
import pytest

from vibey.application.dto import EnqueueRequest
from vibey.domain.job import JobState
from vibey.domain.phase import Phase
from vibey.infrastructure.db.job_repository import PostgresJobRepository

JOB_COUNT = 500
WORKER_COUNT = 8
LEASE = timedelta(milliseconds=150)
CRASH_PROBABILITY = 0.2
TEST_TIMEOUT_SECONDS = 45.0


@pytest.mark.slow
async def test_chaos_zero_double_execution_zero_lost_jobs(
    migrated_pool: asyncpg.Pool, project_id: UUID
) -> None:
    repo = PostgresJobRepository(migrated_pool)

    for i in range(JOB_COUNT):
        await repo.enqueue(
            EnqueueRequest(
                project_id=project_id,
                cycle=1,
                phase=Phase.BUILD,
                kind="build.implement",
                idempotency_key=f"chaos-{i}",
                payload={"i": i},
                max_attempts=1000,
            )
        )

    execution_log: list[UUID] = []
    log_lock = asyncio.Lock()
    stop = asyncio.Event()
    rng = random.Random(1234)

    async def worker(name: str) -> None:
        while not stop.is_set():
            job = await repo.claim(project_id, owner=name, lease=LEASE)
            if job is None:
                await asyncio.sleep(0.01)
                continue

            if rng.random() < CRASH_PROBABILITY:
                # Simulate SIGKILL: the process dies here. No ack, no nack,
                # no further heartbeat -- the lease is simply abandoned and
                # must expire on its own.
                continue

            async with log_lock:
                execution_log.append(job.id)
            await repo.ack(job.id, owner=name)

    async def reaper() -> None:
        while not stop.is_set():
            await repo.reap()
            await asyncio.sleep(0.05)

    async def wait_until_all_terminal() -> None:
        while True:
            async with migrated_pool.acquire() as conn:
                remaining = await conn.fetchval(
                    "SELECT count(*) FROM job WHERE project_id = $1 "
                    "AND state NOT IN ('succeeded', 'failed')",
                    project_id,
                )
            if remaining == 0:
                return
            await asyncio.sleep(0.05)

    worker_tasks = [asyncio.ensure_future(worker(f"worker-{i}")) for i in range(WORKER_COUNT)]
    reaper_task = asyncio.ensure_future(reaper())

    try:
        await asyncio.wait_for(wait_until_all_terminal(), timeout=TEST_TIMEOUT_SECONDS)
    finally:
        stop.set()
        for t in worker_tasks:
            t.cancel()
        reaper_task.cancel()
        await asyncio.gather(*worker_tasks, reaper_task, return_exceptions=True)

    # Zero double-execution: every job id that reached the "about to ack"
    # log appears at most once.
    assert len(execution_log) == len(set(execution_log)), "a job was executed more than once"

    async with migrated_pool.acquire() as conn:
        states = await conn.fetch(
            "SELECT state, count(*) AS n FROM job WHERE project_id = $1 GROUP BY state",
            project_id,
        )
        succeeded = await conn.fetchval(
            "SELECT count(*) FROM job WHERE project_id = $1 AND state = 'succeeded'",
            project_id,
        )
        leased_or_ready = await conn.fetchval(
            "SELECT count(*) FROM job WHERE project_id = $1 AND state IN ('ready', 'leased')",
            project_id,
        )

    state_counts = {row["state"]: row["n"] for row in states}
    assert leased_or_ready == 0, f"jobs stuck non-terminal: {state_counts}"
    assert succeeded == JOB_COUNT, f"expected all {JOB_COUNT} to succeed, got {state_counts}"
    assert JobState.FAILED.value not in state_counts, f"unexpected failures: {state_counts}"
