import asyncio
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from tests.application.fakes import FakeHumanGateRepository, FakeJobRepository, make_job
from vibey.application.dto import HumanGateRequest, JobRecord
from vibey.application.worker import CapacityDeferred, Failure, Outcome, Park, Success, WorkerLoop
from vibey.domain.job import FailureClass, JobState

PROJECT_ID = uuid4()


class _FixedHandler:
    def __init__(self, outcome: Outcome | Exception) -> None:
        self._outcome = outcome
        self.received: JobRecord | None = None

    async def handle(self, job: JobRecord) -> Outcome:
        self.received = job
        if isinstance(self._outcome, Exception):
            raise self._outcome
        return self._outcome


class _SlowHandler:
    def __init__(self, delay: float, outcome: Outcome) -> None:
        self._delay = delay
        self._outcome = outcome

    async def handle(self, job: JobRecord) -> Outcome:
        await asyncio.sleep(self._delay)
        return self._outcome


async def test_run_once_returns_false_when_nothing_claimable() -> None:
    jobs = FakeJobRepository([])
    gates = FakeHumanGateRepository()
    loop = WorkerLoop(jobs=jobs, gates=gates, handler=_FixedHandler(Success()), owner="w1")

    claimed = await loop.run_once(PROJECT_ID)

    assert claimed is False


async def test_success_outcome_acks_the_job() -> None:
    job = make_job(PROJECT_ID)
    jobs = FakeJobRepository([job])
    gates = FakeHumanGateRepository()
    handler = _FixedHandler(Success())
    loop = WorkerLoop(jobs=jobs, gates=gates, handler=handler, owner="w1")

    claimed = await loop.run_once(PROJECT_ID)

    assert claimed is True
    assert handler.received is not None
    assert handler.received.id == job.id
    record = await jobs.get(job.id)
    assert record is not None
    assert record.state is JobState.SUCCEEDED


async def test_failure_outcome_nacks_with_class_and_detail() -> None:
    job = make_job(PROJECT_ID)
    jobs = FakeJobRepository([job])
    gates = FakeHumanGateRepository()
    handler = _FixedHandler(Failure(FailureClass.WORK, "assertion failed"))
    loop = WorkerLoop(jobs=jobs, gates=gates, handler=handler, owner="w1")

    await loop.run_once(PROJECT_ID)

    record = await jobs.get(job.id)
    assert record is not None
    assert record.state is JobState.READY
    assert record.last_error == {"class": "work", "detail": "assertion failed"}


async def test_failure_marks_failed_once_max_attempts_reached() -> None:
    job = make_job(PROJECT_ID, max_attempts=1)
    jobs = FakeJobRepository([job])
    gates = FakeHumanGateRepository()
    handler = _FixedHandler(Failure(FailureClass.WORK, "boom"))
    loop = WorkerLoop(jobs=jobs, gates=gates, handler=handler, owner="w1")

    await loop.run_once(PROJECT_ID)

    record = await jobs.get(job.id)
    assert record is not None
    assert record.state is JobState.FAILED


async def test_handler_exception_becomes_a_vibey_class_failure() -> None:
    job = make_job(PROJECT_ID)
    jobs = FakeJobRepository([job])
    gates = FakeHumanGateRepository()
    handler = _FixedHandler(RuntimeError("unexpected"))
    loop = WorkerLoop(jobs=jobs, gates=gates, handler=handler, owner="w1")

    await loop.run_once(PROJECT_ID)

    record = await jobs.get(job.id)
    assert record is not None
    assert record.last_error == {"class": "vibey", "detail": "unexpected"}


async def test_capacity_exception_defers_without_consuming_an_attempt() -> None:
    job = make_job(PROJECT_ID, attempts=2)
    jobs = FakeJobRepository([job])
    retry_at = datetime(2026, 8, 14, 20, 10, tzinfo=UTC)
    loop = WorkerLoop(
        jobs=jobs,
        gates=FakeHumanGateRepository(),
        handler=_FixedHandler(CapacityDeferred(retry_at, "five-hour window exhausted")),
        owner="w1",
    )

    await loop.run_once(PROJECT_ID)

    record = await jobs.get(job.id)
    assert record is not None
    assert record.state is JobState.READY
    assert record.attempts == 2
    assert record.run_after == retry_at
    assert record.last_error == {
        "class": "capacity",
        "detail": "five-hour window exhausted",
    }


async def test_park_outcome_raises_the_gate_before_parking_the_job() -> None:
    job = make_job(PROJECT_ID)
    jobs = FakeJobRepository([job])
    gates = FakeHumanGateRepository()
    request = HumanGateRequest(kind="approval", prompt="proceed?")
    handler = _FixedHandler(Park(request))
    loop = WorkerLoop(jobs=jobs, gates=gates, handler=handler, owner="w1")

    await loop.run_once(PROJECT_ID)

    assert gates.calls == ["raise_gate"]
    assert jobs.calls[-1] == "park"
    assert gates.raised[0].job_id == job.id
    assert gates.raised[0].prompt == "proceed?"

    record = await jobs.get(job.id)
    assert record is not None
    assert record.state is JobState.AWAITING_HUMAN


async def test_worker_heartbeats_during_a_long_running_handler() -> None:
    job = make_job(PROJECT_ID)
    jobs = FakeJobRepository([job])
    gates = FakeHumanGateRepository()
    handler = _SlowHandler(delay=0.05, outcome=Success())
    loop = WorkerLoop(
        jobs=jobs, gates=gates, handler=handler, owner="w1", lease=timedelta(seconds=0.03)
    )

    await loop.run_once(PROJECT_ID)

    assert jobs.calls.count("heartbeat") >= 1


async def test_heartbeat_task_is_cancelled_cleanly_after_settling() -> None:
    job = make_job(PROJECT_ID)
    jobs = FakeJobRepository([job])
    gates = FakeHumanGateRepository()
    handler = _FixedHandler(Success())
    loop = WorkerLoop(
        jobs=jobs, gates=gates, handler=handler, owner="w1", lease=timedelta(seconds=10)
    )

    # Should return promptly rather than waiting out the (long) heartbeat interval.
    await asyncio.wait_for(loop.run_once(PROJECT_ID), timeout=1.0)


async def test_unknown_outcome_type_is_silently_ignored() -> None:
    """When _settle receives an outcome not matching any known type, the elif
    chain falls through without taking any action on the job."""

    class _UnknownOutcome:
        pass

    class _UnknownHandler:
        async def handle(self, job: JobRecord) -> object:
            return _UnknownOutcome()

    job = make_job(PROJECT_ID)
    jobs = FakeJobRepository([job])
    gates = FakeHumanGateRepository()
    loop = WorkerLoop(
        jobs=jobs,
        gates=gates,
        handler=_UnknownHandler(),  # type: ignore[arg-type]
        owner="w1",
    )

    await loop.run_once(PROJECT_ID)

    record = await jobs.get(job.id)
    assert record is not None
    assert record.state is JobState.LEASED


async def test_lease_for_kind_extends_the_lease_before_handling() -> None:
    """The kind isn't known until after the claim, so the loop claims at the
    short default and immediately heartbeats up to the kind's real lease."""
    job = make_job(PROJECT_ID)
    jobs = FakeJobRepository([job])
    gates = FakeHumanGateRepository()
    loop = WorkerLoop(
        jobs=jobs,
        gates=gates,
        handler=_FixedHandler(Success()),
        owner="w1",
        lease=timedelta(seconds=30),
        lease_for_kind=lambda kind: timedelta(hours=2),
    )

    claimed = await loop.run_once(PROJECT_ID)

    assert claimed is True
    # claim, then the immediate extension heartbeat, then ack
    assert jobs.calls[:2] == ["claim", "heartbeat"]
    record = await jobs.get(job.id)
    assert record is not None
    assert record.state is JobState.SUCCEEDED


async def test_lease_for_kind_matching_default_skips_the_extra_heartbeat() -> None:
    job = make_job(PROJECT_ID)
    jobs = FakeJobRepository([job])
    gates = FakeHumanGateRepository()
    loop = WorkerLoop(
        jobs=jobs,
        gates=gates,
        handler=_FixedHandler(Success()),
        owner="w1",
        lease=timedelta(seconds=30),
        lease_for_kind=lambda kind: timedelta(seconds=30),
    )

    await loop.run_once(PROJECT_ID)

    assert "heartbeat" not in jobs.calls


async def test_park_does_not_duplicate_a_handler_raised_gate() -> None:
    """Handlers like review.collect raise their gate themselves before
    returning Park; _settle raising again would leave a duplicate unanswered
    gate that latest_for_job returns forever, re-parking the job no matter
    what the human answered."""
    job = make_job(PROJECT_ID)
    jobs = FakeJobRepository([job])
    gates = FakeHumanGateRepository()

    class _SelfRaisingHandler:
        async def handle(self, handled: JobRecord) -> Outcome:
            request = HumanGateRequest(kind="approval", prompt="ok?", options=("yes",))
            await gates.raise_gate(handled.project_id, handled.id, request)
            return Park(request)

    loop = WorkerLoop(jobs=jobs, gates=gates, handler=_SelfRaisingHandler(), owner="w1")

    await loop.run_once(PROJECT_ID)

    assert len(gates.raised) == 1


async def test_park_raises_a_fresh_gate_when_the_last_one_is_answered() -> None:
    """A staged interview parks again for its next question batch after the
    previous gate was answered -- the answered gate must not suppress the
    new raise."""
    job = make_job(PROJECT_ID)
    jobs = FakeJobRepository([job])
    gates = FakeHumanGateRepository()
    request = HumanGateRequest(kind="question", prompt="q-1?", options=())
    first = await gates.raise_gate(PROJECT_ID, job.id, request)
    await gates.answer(first.gate_id, answer={"answers": {"q-1": "a"}}, answered_by="t")

    loop = WorkerLoop(
        jobs=jobs,
        gates=gates,
        handler=_FixedHandler(Park(HumanGateRequest(kind="question", prompt="q-2?", options=()))),
        owner="w1",
    )

    await loop.run_once(PROJECT_ID)

    assert len(gates.raised) == 2
