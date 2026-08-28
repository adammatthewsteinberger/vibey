# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://hire.adam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
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


class _Factory:
    def __init__(self, handler: Handler) -> None:
        self._handler = handler
        self.created_for: list[str] = []

    async def create(self, job):  # type: ignore[no-untyped-def]
        self.created_for.append(job.kind)
        return self._handler


class _RaisingFactory:
    async def create(self, job):  # type: ignore[no-untyped-def]
        raise RuntimeError("factory exploded")


async def test_factory_builds_a_handler_per_job() -> None:
    job = make_job(uuid4())
    factory = _Factory(Handler())

    outcome = await JobDispatcher({}, factories={job.kind: factory}).handle(job)

    assert outcome == Success({"kind": job.kind})
    assert factory.created_for == [job.kind]


async def test_static_handler_takes_precedence_over_factory() -> None:
    job = make_job(uuid4())
    factory = _Factory(Handler())

    outcome = await JobDispatcher({job.kind: Handler()}, factories={job.kind: factory}).handle(job)

    assert outcome == Success({"kind": job.kind})
    assert factory.created_for == []


async def test_unknown_kind_with_factories_present_is_still_a_vibey_failure() -> None:
    job = make_job(uuid4())

    outcome = await JobDispatcher({}, factories={"some.other": _Factory(Handler())}).handle(job)

    assert outcome == Failure(FailureClass.VIBEY, f"no handler registered for {job.kind!r}")


async def test_factory_exceptions_propagate_to_the_worker_loop() -> None:
    """A raising factory must NOT be swallowed here -- WorkerLoop.run_once's
    try block owns the CapacityDeferred->Defer / Exception->Failure mapping."""
    import pytest

    job = make_job(uuid4())

    with pytest.raises(RuntimeError, match="factory exploded"):
        await JobDispatcher({}, factories={job.kind: _RaisingFactory()}).handle(job)
