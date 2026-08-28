# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://hire.adam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
"""Routes claimed jobs to kind-specific application handlers.

Two registries: `handlers` for kinds whose collaborators are worker-lifetime
(design/visual/review/deploy), and `factories` for kinds that need a fresh
handler per job (BUILD kinds: worktree/integration managers are bound to
`job.cycle`, and engine selection happens per attempt). A factory that raises
propagates into WorkerLoop.run_once's try block, where CapacityDeferred
becomes Defer and anything else a VIBEY-class Failure -- exactly the settle
semantics a failed construction should get.
"""

from collections.abc import Mapping

from vibey.application.dto import JobRecord
from vibey.application.interfaces import JobHandlerFactory
from vibey.application.worker import Failure, JobHandler, Outcome
from vibey.domain.job import FailureClass

_NO_FACTORIES: Mapping[str, JobHandlerFactory] = {}


class JobDispatcher:
    def __init__(
        self,
        handlers: Mapping[str, JobHandler],
        factories: Mapping[str, JobHandlerFactory] | None = None,
    ) -> None:
        self._handlers = handlers
        self._factories = factories if factories is not None else _NO_FACTORIES

    async def handle(self, job: JobRecord) -> Outcome:
        handler = self._handlers.get(job.kind)
        if handler is None:
            factory = self._factories.get(job.kind)
            if factory is None:
                return Failure(FailureClass.VIBEY, f"no handler registered for {job.kind!r}")
            handler = await factory.create(job)
        return await handler.handle(job)
