# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
"""Starting a project's DESIGN interview, in one place.

This used to live as a private helper inside the CLI, which was fine while
the CLI was the only way in. It is not: the Kubernetes operator creates
projects from a custom resource, and runbook 05 names the failure that
follows -- a second entry point growing its own copy of the transition and
enqueue logic, which then drifts. Both callers use this function.
"""

from uuid import UUID

from vibey.application.dto import EnqueueRequest, ProjectRecord
from vibey.application.interfaces.projects import ProjectStore
from vibey.application.interfaces.queue import JobRepository
from vibey.domain.errors import UnknownProject, WrongPhase
from vibey.domain.job import idempotency_key
from vibey.domain.phase import Phase


async def enqueue_design_interview(
    *,
    projects: ProjectStore,
    jobs: JobRepository,
    project_id: UUID,
    origin: str = "interactive",
) -> UUID:
    """Move a fresh project into DESIGN and enqueue its interview.

    Idempotent through the job's idempotency key: calling it twice for the
    same project and cycle yields the same job rather than a second
    interview. That matters more for the operator than the CLI, since a
    reconcile loop will call it again every time it is unsure.

    `origin` participates in the idempotency key, so a project started from
    a custom resource and one started from the CLI are distinguishable in
    the ledger without changing behaviour.
    """
    project: ProjectRecord | None = await projects.get(project_id)
    if project is None:
        raise UnknownProject(f"unknown project {project_id}")
    if project.phase is Phase.INTAKE:
        project = await projects.transition(project_id, expected=Phase.INTAKE, to=Phase.DESIGN)
    if project.phase is not Phase.DESIGN:
        raise WrongPhase(f"project is in {project.phase.value}, not design")
    job = await jobs.enqueue(
        EnqueueRequest(
            project_id=project_id,
            cycle=project.cycle,
            phase=Phase.DESIGN,
            kind="design.interview",
            idempotency_key=idempotency_key(project_id, project.cycle, "design.interview", origin),
            requirement={"effort": "high"},
        )
    )
    return job.id
