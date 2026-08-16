"""Phase ④ DEPLOY DESIGN acceptance handler and consent guard (Milestone 10 task 10.3)."""

from collections.abc import Callable
from uuid import UUID

from vibey.application.dto import EnqueueRequest, HumanGateRequest, JobRecord
from vibey.application.interfaces import (
    PhaseLedger,
    ProjectTransitioner,
)
from vibey.application.ports import Clock, HumanGateRepository, JobRepository
from vibey.application.worker import Failure, Outcome, Park, Success
from vibey.domain.deployment import DeploymentConsent, DeploymentSpec
from vibey.domain.effort import Effort
from vibey.domain.job import FailureClass, idempotency_key
from vibey.domain.ledger import EventKind
from vibey.domain.phase import Phase


class DeployAcceptanceHandler:
    def __init__(
        self,
        *,
        ledger: PhaseLedger,
        gates: HumanGateRepository,
        jobs: JobRepository,
        projects: ProjectTransitioner | object,
        clock: Clock,
        spec_provider: Callable[[UUID], DeploymentSpec | None] | None = None,
    ) -> None:
        self._ledger = ledger
        self._gates = gates
        self._jobs = jobs
        self._projects = projects
        self._clock = clock
        self._spec_provider = spec_provider

    async def handle(self, job: JobRecord) -> Outcome:
        if job.kind not in ("deploy.spec", "deploy.accept"):
            return Failure(FailureClass.VIBEY, "expected deploy.spec or deploy.accept job")

        gate = await self._gates.latest_for_job(job.id)
        if gate is None:
            request = HumanGateRequest(
                kind="deploy_acceptance",
                prompt=(
                    "Please review the deployment specification "
                    "and grant explicit mutation consent."
                ),
                options=("accept", "reject"),
                default_answer="reject",
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
        verdict = str(answer_data.get("verdict") or answer_data.get("choice") or "reject").lower()
        explicit_consent = bool(answer_data.get("explicit_mutation_authorized", False))

        if verdict != "accept" or not explicit_consent:
            return Failure(
                FailureClass.WORK,
                "deployment specification was rejected or explicit mutation consent was denied",
            )

        spec = self._spec_provider(job.project_id) if self._spec_provider else None
        if spec is None:
            return Failure(FailureClass.VIBEY, "deployment specification not found")

        errors = spec.validate()
        if errors:
            return Failure(FailureClass.VIBEY, f"invalid deployment spec: {'; '.join(errors)}")

        digest = spec.scope_digest()
        consent = DeploymentConsent(
            consent_id=str(job.id),
            target_scope_digest=digest,
            granted_by="user",
            granted_at=self._clock.now(),
            explicit_mutation_authorized=True,
        )

        await self._ledger.append_event(
            project_id=job.project_id,
            cycle=job.cycle,
            job_id=job.id,
            kind=EventKind.DECISION_RECORDED,
            payload={
                "decision": "deployment_spec_accepted",
                "scope_digest": digest,
                "consent_id": consent.consent_id,
            },
        )

        if hasattr(self._projects, "transition"):
            await self._projects.transition(
                job.project_id,
                expected=Phase.DEPLOY_DESIGN,
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
                requirement={"effort": Effort.LOW.name.lower()},
            )
        )

        return Success(
            {
                "verdict": "accepted",
                "scope_digest": digest,
                "next_phase": Phase.DEPLOY_EXECUTE.value,
            }
        )
