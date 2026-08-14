"""Routes claimed jobs to kind-specific application handlers."""

from collections.abc import Mapping

from vibey.application.dto import JobRecord
from vibey.application.worker import Failure, JobHandler, Outcome
from vibey.domain.job import FailureClass


class JobDispatcher:
    def __init__(self, handlers: Mapping[str, JobHandler]) -> None:
        self._handlers = handlers

    async def handle(self, job: JobRecord) -> Outcome:
        handler = self._handlers.get(job.kind)
        if handler is None:
            return Failure(FailureClass.VIBEY, f"no handler registered for {job.kind!r}")
        return await handler.handle(job)
