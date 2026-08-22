# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
"""In-memory fakes for application/ports.py, used to unit test worker.py
without a database (real-DB behavior is covered separately against
Postgres in tests/infrastructure/db/)."""

from collections.abc import Mapping
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from vibey.application.dto import EnqueueRequest, HumanGateRecord, HumanGateRequest, JobRecord
from vibey.domain.engine import EngineId
from vibey.domain.job import JobState
from vibey.domain.phase import Phase


class FakeJobRepository:
    def __init__(self, jobs: list[JobRecord] | None = None) -> None:
        self._jobs: dict[UUID, JobRecord] = {j.id: j for j in (jobs or [])}
        self.calls: list[str] = []

    async def enqueue(self, request: EnqueueRequest) -> JobRecord:
        job = JobRecord(
            id=uuid4(),
            project_id=request.project_id,
            cycle=request.cycle,
            phase=request.phase,
            kind=request.kind,
            state=JobState.READY,
            priority=request.priority,
            work_item_id=request.work_item_id,
            payload=request.payload,
            requirement=request.requirement,
            idempotency_key=request.idempotency_key,
            attempts=0,
            max_attempts=request.max_attempts,
            run_after=request.run_after or datetime.now(UTC),
            lease_owner=None,
            lease_expires_at=None,
            assigned_engine=None,
            last_error=None,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        self._jobs[job.id] = job
        return job

    async def claim(self, project_id: UUID, *, owner: str, lease: timedelta) -> JobRecord | None:
        self.calls.append("claim")
        for job in self._jobs.values():
            if job.project_id == project_id and job.state is JobState.READY:
                leased = _with(
                    job,
                    state=JobState.LEASED,
                    lease_owner=owner,
                    lease_expires_at=datetime.now(UTC) + lease,
                    attempts=job.attempts + 1,
                )
                self._jobs[job.id] = leased
                return leased
        return None

    async def heartbeat(self, job_id: UUID, *, owner: str, lease: timedelta) -> bool:
        self.calls.append("heartbeat")
        job = self._jobs.get(job_id)
        if job is None or job.lease_owner != owner:
            return False
        self._jobs[job_id] = _with(job, lease_expires_at=datetime.now(UTC) + lease)
        return True

    async def ack(self, job_id: UUID, *, owner: str) -> bool:
        self.calls.append("ack")
        job = self._jobs.get(job_id)
        if job is None or job.lease_owner != owner:
            return False
        self._jobs[job_id] = _with(
            job, state=JobState.SUCCEEDED, lease_owner=None, lease_expires_at=None
        )
        return True

    async def nack(self, job_id: UUID, *, owner: str, error: Mapping[str, object]) -> bool:
        self.calls.append("nack")
        job = self._jobs.get(job_id)
        if job is None or job.lease_owner != owner:
            return False
        state = JobState.FAILED if job.attempts >= job.max_attempts else JobState.READY
        self._jobs[job_id] = _with(
            job, state=state, lease_owner=None, lease_expires_at=None, last_error=dict(error)
        )
        return True

    async def park(self, job_id: UUID, *, owner: str) -> bool:
        self.calls.append("park")
        job = self._jobs.get(job_id)
        if job is None or job.lease_owner != owner:
            return False
        self._jobs[job_id] = _with(
            job,
            state=JobState.AWAITING_HUMAN,
            lease_owner=None,
            lease_expires_at=None,
            attempts=max(job.attempts - 1, 0),
        )
        return True

    async def defer(
        self,
        job_id: UUID,
        *,
        owner: str,
        retry_at: datetime,
        error: Mapping[str, object],
    ) -> bool:
        self.calls.append("defer")
        job = self._jobs.get(job_id)
        if job is None or job.lease_owner != owner:
            return False
        self._jobs[job_id] = _with(
            job,
            state=JobState.READY,
            lease_owner=None,
            lease_expires_at=None,
            attempts=max(job.attempts - 1, 0),
            run_after=retry_at,
            last_error=dict(error),
        )
        return True

    async def reap(self) -> int:
        return 0

    async def assign_engine(self, job_id: UUID, *, owner: str, engine_id: EngineId) -> bool:
        self.calls.append("assign_engine")
        job = self._jobs.get(job_id)
        if job is None or job.lease_owner != owner or job.state is not JobState.LEASED:
            return False
        self._jobs[job_id] = _with(job, assigned_engine=engine_id.value)
        return True

    async def count_unsettled(
        self, project_id: UUID, *, cycle: int, phase: Phase, exclude: UUID | None = None
    ) -> int:
        terminal = {JobState.SUCCEEDED, JobState.FAILED, JobState.CANCELLED}
        return sum(
            1
            for job in self._jobs.values()
            if job.project_id == project_id
            and job.cycle == cycle
            and job.phase is phase
            and job.state not in terminal
            and job.id != exclude
        )

    async def queue_depth(self, project_id: UUID) -> Mapping[str, int]:
        from collections import Counter

        counts: Counter[str] = Counter()
        for job in self._jobs.values():
            if job.project_id == project_id:
                counts[job.state] += 1
        return dict(counts)

    async def get(self, job_id: UUID) -> JobRecord | None:
        return self._jobs.get(job_id)


class FakeHumanGateRepository:
    def __init__(self) -> None:
        self.raised: list[HumanGateRecord] = []
        self.calls: list[str] = []

    async def raise_gate(
        self, project_id: UUID, job_id: UUID | None, request: HumanGateRequest
    ) -> HumanGateRecord:
        self.calls.append("raise_gate")
        record = HumanGateRecord(
            gate_id=uuid4(),
            project_id=project_id,
            job_id=job_id,
            kind=request.kind,
            prompt=request.prompt,
            options=request.options,
            default_answer=request.default_answer,
            answer=None,
            raised_at=datetime.now(UTC),
            timeout_at=request.timeout_at,
            answered_at=None,
            answered_by=None,
        )
        self.raised.append(record)
        return record

    async def answer(
        self, gate_id: UUID, *, answer: Mapping[str, object], answered_by: str
    ) -> HumanGateRecord:
        self.calls.append("answer")
        existing = next(r for r in self.raised if r.gate_id == gate_id)
        answered = HumanGateRecord(
            gate_id=existing.gate_id,
            project_id=existing.project_id,
            job_id=existing.job_id,
            kind=existing.kind,
            prompt=existing.prompt,
            options=existing.options,
            default_answer=existing.default_answer,
            answer=dict(answer),
            raised_at=existing.raised_at,
            timeout_at=existing.timeout_at,
            answered_at=datetime.now(UTC),
            answered_by=answered_by,
        )
        self.raised = [answered if r.gate_id == gate_id else r for r in self.raised]
        return answered

    async def latest_for_job(self, job_id: UUID) -> HumanGateRecord | None:
        matching = [record for record in self.raised if record.job_id == job_id]
        return matching[-1] if matching else None

    async def open_for_project(self, project_id: UUID) -> tuple[HumanGateRecord, ...]:
        return tuple(
            record
            for record in self.raised
            if record.project_id == project_id and record.answered_at is None
        )


def _with(job: JobRecord, **overrides: object) -> JobRecord:
    from dataclasses import replace

    return replace(job, **overrides)  # type: ignore[arg-type]


def make_job(
    project_id: UUID,
    *,
    state: JobState = JobState.READY,
    max_attempts: int = 7,
    attempts: int = 0,
) -> JobRecord:
    now = datetime.now(UTC)
    return JobRecord(
        id=uuid4(),
        project_id=project_id,
        cycle=1,
        phase=Phase.BUILD,
        kind="build.implement",
        state=state,
        priority=0,
        work_item_id=None,
        payload={},
        requirement={},
        idempotency_key=f"key-{uuid4()}",
        attempts=attempts,
        max_attempts=max_attempts,
        run_after=now,
        lease_owner=None,
        lease_expires_at=None,
        assigned_engine=None,
        last_error=None,
        created_at=now,
        updated_at=now,
    )
