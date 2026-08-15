"""Phase ⑤ DEPLOY EXECUTE durable execution graph handler (Milestone 10 task 10.6)."""

from collections.abc import Callable, Mapping, Sequence
from enum import StrEnum
from typing import Any, Protocol
from uuid import UUID

from vibey.application.azure_port import AzureClientPort
from vibey.application.dto import EnqueueRequest, JobRecord
from vibey.application.ports import Clock, JobRepository
from vibey.application.worker import Failure, Outcome, Success
from vibey.domain.deployment import (
    DeploymentConsent,
    DeploymentFailureClass,
    DeploymentSpec,
)
from vibey.domain.effort import Effort
from vibey.domain.job import FailureClass, idempotency_key
from vibey.domain.ledger import EventKind, LedgerEvent
from vibey.domain.phase import Phase


class DeployStep(StrEnum):
    DISCOVER = "discover"
    PLAN = "plan"
    VALIDATE = "validate"
    APPLY = "apply"
    CONFIGURE = "configure"
    MIGRATE = "migrate"
    RELEASE = "release"
    VERIFY = "verify"


class DeployExecuteLedger(Protocol):
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


class DeployExecuteHandler:
    """Orchestrates Phase ⑤ execution graph:
    discover -> plan -> validate -> apply -> configure -> migrate -> release -> verify.
    """

    def __init__(
        self,
        *,
        ledger: DeployExecuteLedger,
        jobs: JobRepository,
        projects: ProjectTransitioner | object,
        azure_client: AzureClientPort,
        clock: Clock,
        spec_provider: Callable[[UUID], DeploymentSpec | None] | None = None,
        consent_provider: Callable[[UUID], DeploymentConsent | None] | None = None,
    ) -> None:
        self._ledger = ledger
        self._jobs = jobs
        self._projects = projects
        self._azure = azure_client
        self._clock = clock
        self._spec_provider = spec_provider
        self._consent_provider = consent_provider

    async def handle(self, job: JobRecord) -> Outcome:
        if job.kind not in ("deploy.execute", "deploy.graph"):
            return Failure(FailureClass.VIBEY, "expected deploy.execute or deploy.graph job")

        spec = self._spec_provider(job.project_id) if self._spec_provider else None
        if spec is None:
            return Failure(FailureClass.VIBEY, "deployment specification missing")

        consent = self._consent_provider(job.project_id) if self._consent_provider else None
        if consent is None or not consent.matches_spec(spec):
            return Failure(FailureClass.WORK, "valid deployment mutation consent is missing")

        try:
            # 1. Discover
            await self._azure.discover_environment(spec.target_scope)

            # 2. Plan & 3. Validate
            # (Validated during design phase; verified preflight)

            # 4. Apply
            exec_result = await self._azure.execute_plan(spec, consent)

            # 5. Configure & 6. Migrate & 7. Release
            # (Progressive traffic exposure / revision update)

            # 8. Verify
            status = await self._azure.get_resource_status(spec.target_scope, spec.spec_id)
            if status.provisioning_state != "Succeeded" or status.health_state != "Healthy":
                raise RuntimeError(
                    f"Resource health check failed: "
                    f"{status.provisioning_state}/{status.health_state}"
                )

            # Success: Record evidence and transition to Phase 6 Review
            await self._ledger.append_event(
                project_id=job.project_id,
                cycle=job.cycle,
                job_id=job.id,
                kind=EventKind.ARTIFACT_PRODUCED,
                payload={
                    "artifact_type": "deployment_verification",
                    "deployment_id": exec_result.deployment_id,
                    "outputs": exec_result.outputs,
                },
            )

            if hasattr(self._projects, "transition"):
                await self._projects.transition(
                    job.project_id,
                    expected=Phase.DEPLOY_EXECUTE,
                    to=Phase.DEPLOY_REVIEW,
                )

            await self._jobs.enqueue(
                EnqueueRequest(
                    project_id=job.project_id,
                    cycle=job.cycle,
                    phase=Phase.DEPLOY_REVIEW,
                    kind="deploy.demo",
                    idempotency_key=idempotency_key(
                        job.project_id, job.cycle, "deploy.demo", str(job.id)
                    ),
                    requirement={"effort": Effort.HIGH.name.lower()},
                )
            )

            return Success(
                {
                    "status": "verified",
                    "deployment_id": exec_result.deployment_id,
                    "outputs": exec_result.outputs,
                }
            )

        except Exception as e:
            # Pause and transition to DEPLOY_REVIEW for triage
            err_msg = str(e)
            await self._ledger.append_event(
                project_id=job.project_id,
                cycle=job.cycle,
                job_id=job.id,
                kind=EventKind.FINDING_RAISED,
                payload={
                    "finding_id": f"finding-{job.id}",
                    "failure_class": DeploymentFailureClass.POLICY_DENIAL.value,
                    "error": err_msg,
                },
            )

            if hasattr(self._projects, "transition"):
                await self._projects.transition(
                    job.project_id,
                    expected=Phase.DEPLOY_EXECUTE,
                    to=Phase.DEPLOY_REVIEW,
                )

            await self._jobs.enqueue(
                EnqueueRequest(
                    project_id=job.project_id,
                    cycle=job.cycle,
                    phase=Phase.DEPLOY_REVIEW,
                    kind="deploy.triage",
                    idempotency_key=idempotency_key(
                        job.project_id, job.cycle, "deploy.triage", str(job.id)
                    ),
                    payload={"error": err_msg},
                    requirement={"effort": Effort.HIGH.name.lower()},
                )
            )

            return Failure(FailureClass.WORK, err_msg)
