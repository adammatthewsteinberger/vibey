# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
"""Bridges the REVIEW-side deployment opt-in onto the deploy stage set.

``ReviewDeploymentChoiceHandler`` -- deliberately unchanged; the protected
system test pins its exact behavior -- transitions REVIEW to the legacy
single ``Phase.DEPLOY`` and enqueues kind ``deploy.design``, which no
stage-set handler accepts. This handler owns that kind: it completes the
legacy bridge (``DEPLOY -> DEPLOY_DESIGN``, a legal edge in the phase
machine) and enqueues the real ``deploy.interview`` job, replaying in
production exactly what the system test performs manually.
"""

import contextlib

from vibey.application.dto import EnqueueRequest, JobRecord
from vibey.application.interfaces import ProjectTransitioner
from vibey.application.ports import JobRepository
from vibey.application.worker import Failure, Outcome, Success
from vibey.domain.effort import Effort
from vibey.domain.job import FailureClass, idempotency_key
from vibey.domain.phase import Phase


class DeployDesignBridgeHandler:
    def __init__(
        self,
        *,
        jobs: JobRepository,
        projects: ProjectTransitioner | object,
    ) -> None:
        self._jobs = jobs
        self._projects = projects

    async def handle(self, job: JobRecord) -> Outcome:
        if job.kind != "deploy.design":
            return Failure(FailureClass.VIBEY, "expected deploy.design job")

        if hasattr(self._projects, "transition"):
            # A CAS miss (ValueError) means a replay or another worker
            # already moved the project past DEPLOY. The enqueue below is
            # idempotent, so "already bridged" settles as success, not a
            # poison nack.
            with contextlib.suppress(ValueError):
                await self._projects.transition(
                    job.project_id,
                    expected=Phase.DEPLOY,
                    to=Phase.DEPLOY_DESIGN,
                )

        await self._jobs.enqueue(
            EnqueueRequest(
                project_id=job.project_id,
                cycle=job.cycle,
                phase=Phase.DEPLOY_DESIGN,
                kind="deploy.interview",
                idempotency_key=idempotency_key(
                    job.project_id, job.cycle, "deploy.interview", "entry"
                ),
                requirement={"effort": Effort.HIGH.name.lower()},
            )
        )
        return Success({"status": "bridged", "target_phase": Phase.DEPLOY_DESIGN.value})
