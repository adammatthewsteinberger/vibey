# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
"""Durable ``review.deployment_choice`` handler (M7 task 7.7 & 7.8).

Presents the explicit deployment opt-in / opt-out choice gate:
- Default is explicitly ``local_only`` (silence / no default is never treated as consent).
- If opted out: records ``DeploymentDeclined``, transitions project to ``Phase.DONE``
  with ``completion_mode = "local"``, and enqueues zero deployment jobs.
- If opted in: records ``DeploymentOptedIn`` and hands off to Phase 4 (``deploy.design``).
"""

from collections.abc import Sequence

from vibey.application.dto import EnqueueRequest, HumanGateRequest, JobRecord
from vibey.application.interfaces import (
    PhaseLedger,
    ProjectTransitioner,
)
from vibey.application.ports import Clock, HumanGateRepository, JobRepository
from vibey.application.worker import Failure, Outcome, Park, Success
from vibey.domain.effort import Effort
from vibey.domain.job import FailureClass, idempotency_key
from vibey.domain.ledger import EventKind, LedgerEvent
from vibey.domain.phase import Phase


def can_enqueue_deployment_design(events: Sequence[LedgerEvent]) -> bool:
    """Evaluates DEPLOY_DESIGN guard: only explicit DeploymentOptedIn allows
    enqueueing Phase 4 deployment jobs."""
    latest_decision: EventKind | None = None
    for e in sorted(events, key=lambda ev: ev.seq):
        if e.kind in (EventKind.DEPLOYMENT_OPTED_IN, EventKind.DEPLOYMENT_DECLINED):
            latest_decision = e.kind
    return latest_decision is EventKind.DEPLOYMENT_OPTED_IN


class ReviewDeploymentChoiceHandler:
    def __init__(
        self,
        *,
        ledger: PhaseLedger,
        gates: HumanGateRepository,
        jobs: JobRepository,
        projects: ProjectTransitioner | object,
        clock: Clock,
    ) -> None:
        self._ledger = ledger
        self._gates = gates
        self._jobs = jobs
        self._projects = projects
        self._clock = clock

    async def handle(self, job: JobRecord) -> Outcome:
        if job.kind != "review.deployment_choice":
            return Failure(FailureClass.VIBEY, "expected review.deployment_choice job")

        gate = await self._gates.latest_for_job(job.id)
        if gate is None:
            request = HumanGateRequest(
                kind="choice",
                prompt="Review accepted. Deploy to target infrastructure?",
                options=("local_only", "deploy"),
                default_answer="local_only",
            )
            await self._gates.raise_gate(job.project_id, job.id, request)
            return Park(request)

        if gate.answer is None:
            return Park(
                HumanGateRequest(
                    kind=gate.kind,
                    prompt=gate.prompt,
                    options=gate.options,
                    default_answer=gate.default_answer,
                )
            )

        answer_data = gate.answer
        choice = str(
            answer_data.get("choice")
            or answer_data.get("decision")
            or gate.default_answer
            or "local_only"
        ).lower()

        if choice == "deploy":
            await self._ledger.append_event(
                project_id=job.project_id,
                cycle=job.cycle,
                job_id=job.id,
                kind=EventKind.DEPLOYMENT_OPTED_IN,
                payload={"choice": "deploy"},
            )
            events = await self._ledger.all_for_project(job.project_id)
            if not can_enqueue_deployment_design(events):
                return Failure(
                    FailureClass.VIBEY,
                    "cannot enqueue deployment design without explicit opt-in",
                )

            if hasattr(self._projects, "transition"):
                await self._projects.transition(
                    job.project_id,
                    expected=Phase.REVIEW,
                    to=Phase.DEPLOY,
                )

            await self._jobs.enqueue(
                EnqueueRequest(
                    project_id=job.project_id,
                    cycle=job.cycle,
                    phase=Phase.DEPLOY,
                    kind="deploy.design",
                    idempotency_key=idempotency_key(
                        job.project_id, job.cycle, "deploy.design", str(job.id)
                    ),
                    requirement={"effort": Effort.HIGH.name.lower()},
                )
            )
            return Success({"decision": "opted_in", "completion_mode": "deploy"})

        # Opt-out: record decline and complete locally
        await self._ledger.append_event(
            project_id=job.project_id,
            cycle=job.cycle,
            job_id=job.id,
            kind=EventKind.DEPLOYMENT_DECLINED,
            payload={"choice": "local_only"},
        )

        if hasattr(self._projects, "transition"):
            await self._projects.transition(
                job.project_id,
                expected=Phase.REVIEW,
                to=Phase.DONE,
            )

        return Success({"decision": "declined", "completion_mode": "local"})
