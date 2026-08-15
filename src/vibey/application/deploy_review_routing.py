"""Phase ⑥ DEPLOY REVIEW loop routing handler (Milestone 10 task 10.11)."""

from collections.abc import Callable, Mapping, Sequence
from enum import StrEnum
from typing import Any, Protocol
from uuid import UUID

from vibey.application.azure_port import AzureClientPort
from vibey.application.dto import EnqueueRequest, JobRecord
from vibey.application.ports import JobRepository
from vibey.application.worker import Failure, Outcome, Success
from vibey.domain.deployment import DeploymentConsent, DeploymentSpec
from vibey.domain.effort import Effort
from vibey.domain.job import FailureClass, idempotency_key
from vibey.domain.ledger import EventKind, LedgerEvent
from vibey.domain.phase import Phase


class DeployReviewAction(StrEnum):
    APPROVE = "approve"
    LOOP_DESIGN = "loop_deploy_design"
    RETRY_EXECUTE = "retry_deploy_execute"
    LOOP_CODE_FIX = "loop_code_fix"
    ABORT = "abort"


class DeployRoutingLedger(Protocol):
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


class DeployReviewRoutingHandler:
    """Routes Phase ⑥ review outcomes to DONE, DEPLOY_DESIGN, DEPLOY_EXECUTE, or PLAN."""

    def __init__(
        self,
        *,
        ledger: DeployRoutingLedger,
        jobs: JobRepository,
        projects: ProjectTransitioner | object,
        azure_client: AzureClientPort,
        spec_provider: Callable[[UUID], DeploymentSpec | None] | None = None,
        consent_provider: Callable[[UUID], DeploymentConsent | None] | None = None,
    ) -> None:
        self._ledger = ledger
        self._jobs = jobs
        self._projects = projects
        self._azure = azure_client
        self._spec_provider = spec_provider
        self._consent_provider = consent_provider

    async def handle(self, job: JobRecord) -> Outcome:
        if job.kind != "deploy.route":
            return Failure(FailureClass.VIBEY, "expected deploy.route job")

        payload = job.payload or {}
        raw_action = str(payload.get("action", "approve")).lower()

        spec = self._spec_provider(job.project_id) if self._spec_provider else None
        consent = self._consent_provider(job.project_id) if self._consent_provider else None

        if raw_action in (DeployReviewAction.APPROVE.value, "approve", "done"):
            await self._ledger.append_event(
                project_id=job.project_id,
                cycle=job.cycle,
                job_id=job.id,
                kind=EventKind.DECISION_RECORDED,
                payload={"decision": "deployment_approved", "next_phase": Phase.DONE.name},
            )
            if hasattr(self._projects, "transition"):
                await self._projects.transition(
                    job.project_id,
                    expected=Phase.DEPLOY_REVIEW,
                    to=Phase.DONE,
                )
            return Success({"status": "approved", "target_phase": Phase.DONE.name})

        if raw_action in (
            DeployReviewAction.LOOP_DESIGN.value,
            "loop_deploy_design",
            "loop_design",
            "request_changes",
        ):
            await self._ledger.append_event(
                project_id=job.project_id,
                cycle=job.cycle,
                job_id=job.id,
                kind=EventKind.DECISION_RECORDED,
                payload={"decision": "loop_deploy_design", "next_phase": Phase.DEPLOY_DESIGN.name},
            )
            if hasattr(self._projects, "transition"):
                await self._projects.transition(
                    job.project_id,
                    expected=Phase.DEPLOY_REVIEW,
                    to=Phase.DEPLOY_DESIGN,
                )
            await self._jobs.enqueue(
                EnqueueRequest(
                    project_id=job.project_id,
                    cycle=job.cycle,
                    phase=Phase.DEPLOY_DESIGN,
                    kind="deploy.interview",
                    idempotency_key=idempotency_key(
                        job.project_id, job.cycle, "deploy.interview", str(job.id)
                    ),
                    requirement={"effort": Effort.HIGH.name.lower()},
                )
            )
            return Success({"status": "loop_design", "target_phase": Phase.DEPLOY_DESIGN.name})

        if raw_action in (
            DeployReviewAction.RETRY_EXECUTE.value,
            "retry_deploy_execute",
            "retry_execute",
        ):
            await self._ledger.append_event(
                project_id=job.project_id,
                cycle=job.cycle,
                job_id=job.id,
                kind=EventKind.DECISION_RECORDED,
                payload={
                    "decision": "retry_deploy_execute",
                    "next_phase": Phase.DEPLOY_EXECUTE.name,
                },
            )
            if hasattr(self._projects, "transition"):
                await self._projects.transition(
                    job.project_id,
                    expected=Phase.DEPLOY_REVIEW,
                    to=Phase.DEPLOY_EXECUTE,
                )
            await self._jobs.enqueue(
                EnqueueRequest(
                    project_id=job.project_id,
                    cycle=job.cycle,
                    phase=Phase.DEPLOY_EXECUTE,
                    kind="deploy.execute",
                    idempotency_key=idempotency_key(
                        job.project_id, job.cycle, "deploy.execute", str(job.id)
                    ),
                    requirement={"effort": Effort.HIGH.name.lower()},
                )
            )
            return Success({"status": "retry_execute", "target_phase": Phase.DEPLOY_EXECUTE.name})

        # LOOP_CODE_FIX or ABORT
        if payload.get("cleanup_ephemeral") and spec is not None and consent is not None:
            await self._azure.delete_resource(spec.target_scope, spec.spec_id, consent)

        target_phase = (
            Phase.DESIGN if raw_action == DeployReviewAction.LOOP_CODE_FIX.value else Phase.DONE
        )

        await self._ledger.append_event(
            project_id=job.project_id,
            cycle=job.cycle,
            job_id=job.id,
            kind=EventKind.DECISION_RECORDED,
            payload={"decision": raw_action, "next_phase": target_phase.name},
        )
        if hasattr(self._projects, "transition"):
            await self._projects.transition(
                job.project_id,
                expected=Phase.DEPLOY_REVIEW,
                to=target_phase,
            )

        return Success({"status": raw_action, "target_phase": target_phase.name})
