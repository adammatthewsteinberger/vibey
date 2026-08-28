# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://hire.adam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
"""Shared BUILD-entry trigger, used by both acceptance services once a
project lands in Phase.BUILD (DESIGN -> BUILD directly, or VISUAL_DESIGN ->
BUILD after the visual plan is settled)."""

from vibey.application.dto import EnqueueRequest, ProjectRecord
from vibey.application.ports import JobRepository
from vibey.domain.effort import Effort
from vibey.domain.job import idempotency_key
from vibey.domain.phase import Phase


async def enqueue_build_decompose(jobs: JobRepository, project: ProjectRecord) -> None:
    await jobs.enqueue(
        EnqueueRequest(
            project_id=project.project_id,
            cycle=project.cycle,
            phase=Phase.BUILD,
            kind="build.decompose",
            idempotency_key=idempotency_key(
                project.project_id, project.cycle, "build.decompose", "entry"
            ),
            requirement={"effort": Effort.STANDARD.name.lower()},
        )
    )
