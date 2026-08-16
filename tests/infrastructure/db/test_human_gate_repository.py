from uuid import UUID

import asyncpg

from vibey.application.dto import HumanGateRequest, JobRecord
from vibey.application.worker import Outcome, Park, WorkerLoop
from vibey.domain.job import JobState
from vibey.infrastructure.db.human_gate_repository import PostgresHumanGateRepository
from vibey.infrastructure.db.job_repository import PostgresJobRepository

from .test_job_repository import LEASE, _request


class _ParkingHandler:
    async def handle(self, job: JobRecord) -> Outcome:
        return Park(HumanGateRequest(kind="approval", prompt="proceed with deploy?"))


async def test_raise_and_answer_round_trip(migrated_pool: asyncpg.Pool, project_id: UUID) -> None:
    jobs = PostgresJobRepository(migrated_pool)
    gates = PostgresHumanGateRepository(migrated_pool)
    job = await jobs.enqueue(_request(project_id))
    claimed = await jobs.claim(project_id, owner="w1", lease=LEASE)
    assert claimed is not None
    assert await jobs.park(job.id, owner="w1")

    raised = await gates.raise_gate(
        project_id,
        job.id,
        HumanGateRequest(kind="approval", prompt="proceed?", options=("yes", "no")),
    )

    assert raised.answered_at is None
    assert raised.prompt == "proceed?"
    assert raised.options == ("yes", "no")

    answered = await gates.answer(raised.gate_id, answer={"choice": "yes"}, answered_by="adam")

    assert answered.answered_at is not None
    assert answered.answered_by == "adam"
    assert answered.answer == {"choice": "yes"}

    fetched = await gates.get(raised.gate_id)
    assert fetched is not None
    assert fetched.answer == {"choice": "yes"}
    requeued = await jobs.get(job.id)
    assert requeued is not None
    assert requeued.state is JobState.READY


async def test_parked_job_releases_lease_immediately_and_worker_is_free(
    migrated_pool: asyncpg.Pool, project_id: UUID
) -> None:
    jobs = PostgresJobRepository(migrated_pool)
    gates = PostgresHumanGateRepository(migrated_pool)
    job = await jobs.enqueue(_request(project_id))
    other = await jobs.enqueue(_request(project_id, subject="other"))

    loop = WorkerLoop(jobs=jobs, gates=gates, handler=_ParkingHandler(), owner="w1", lease=LEASE)
    claimed = await loop.run_once(project_id)
    assert claimed is True

    record = await jobs.get(job.id)
    assert record is not None
    assert record.state is JobState.AWAITING_HUMAN
    assert record.lease_owner is None
    assert record.lease_expires_at is None

    # The worker is free within one loop iteration -- it can immediately
    # claim the next ready job rather than waiting out any lease.
    next_claim = await jobs.claim(project_id, owner="w1", lease=LEASE)
    assert next_claim is not None
    assert next_claim.id == other.id
