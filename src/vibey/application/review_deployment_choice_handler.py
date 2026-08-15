"""Durable ``review.deployment_choice`` handler (M7 task 7.7 & 7.8).

Presents the explicit deployment opt-in / opt-out choice gate:
- Default is explicitly ``local_only`` (silence / no default is never treated as consent).
- If opted out: records ``DeploymentDeclined``, transitions project to ``Phase.DONE``
  with ``completion_mode = "local"``, and enqueues zero deployment jobs.
- If opted in: records ``DeploymentOptedIn`` and hands off to Phase 4 (``deploy.design``).
"""

from collections.abc import Mapping, Sequence
from typing import Any, Protocol
from uuid import UUID

from vibey.application.dto import HumanGateRequest, JobRecord
from vibey.application.ports import Clock, HumanGateRepository, JobRepository
from vibey.application.worker import Failure, Outcome, Park, Success
from vibey.domain.job import FailureClass
from vibey.domain.ledger import EventKind, LedgerEvent
from vibey.domain.phase import Phase


class ReviewDeploymentLedger(Protocol):
    async def all_for_project(self, project_id: UUID) -> Sequence[LedgerEvent]: ...

    async def append_event(
        self,
        project_id: UUID,
        cycle: int,
        job_id: UUID,
        kind: EventKind,
        payload: Mapping[str, object],
    ) -> None: ...


class ProjectTransitioner(Protocol):
    async def transition(
        self,
        project_id: UUID,
        *,
        expected: Phase,
        to: Phase,
        cycle: int | None = None,
    ) -> Any: ...


class ReviewDeploymentChoiceHandler:
    def __init__(
        self,
        *,
        ledger: ReviewDeploymentLedger,
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
