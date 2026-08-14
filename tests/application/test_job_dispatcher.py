from uuid import uuid4

from tests.application.fakes import make_job
from vibey.application.job_dispatcher import JobDispatcher
from vibey.application.worker import Failure, Success
from vibey.domain.job import FailureClass


class Handler:
    async def handle(self, job):  # type: ignore[no-untyped-def]
        return Success({"kind": job.kind})


async def test_dispatches_by_job_kind() -> None:
    job = make_job(uuid4())
    outcome = await JobDispatcher({job.kind: Handler()}).handle(job)
    assert outcome == Success({"kind": job.kind})


async def test_unknown_kind_is_a_vibey_failure() -> None:
    job = make_job(uuid4())
    outcome = await JobDispatcher({}).handle(job)
    assert outcome == Failure(FailureClass.VIBEY, f"no handler registered for {job.kind!r}")
