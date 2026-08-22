# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
"""Phase ④ DEPLOY DESIGN interview and synthesis handlers (Milestone 10 task 10.3).

The `jobs` collaborators are keyword-only with a None default on both
handlers: when absent the handlers behave exactly as before (the protected
system test drives each stage manually), and when present -- as the full
worker wires them -- each stage enqueues its successor so the deploy design
chain advances unattended: interview -> synthesize -> spec.
"""

from collections.abc import Mapping
from uuid import UUID

from vibey.application.dto import EnqueueRequest, HumanGateRequest, JobRecord
from vibey.application.interfaces import (
    DeploymentSpecStore,
    PhaseLedger,
)
from vibey.application.ports import Clock, HumanGateRepository, JobRepository
from vibey.application.worker import Failure, Outcome, Park, Success
from vibey.domain.deployment import (
    AzureTargetScope,
    CostBoundary,
    DeploymentSpec,
    IdentityAuthority,
    RecoveryPolicy,
    TopologyConfig,
    VerificationContract,
)
from vibey.domain.effort import Effort
from vibey.domain.job import FailureClass, idempotency_key
from vibey.domain.ledger import EventKind
from vibey.domain.phase import Phase


def build_deployment_spec(
    *, project_id: UUID, cycle: int, answers: Mapping[str, object]
) -> DeploymentSpec:
    """Synthesizes the DeploymentSpec from the elicitation answers.

    "accept_defaults" supplies none of the Azure identifiers, so the
    defaults below are deliberately visible placeholders -- fine for the
    in-memory Azure adapter (and the faked harness), and exactly the values
    a real `az`-backed run must override by answering the interview with
    the real tenant/subscription/resource-group keys.
    """

    def _get(key: str, default: str) -> str:
        return str(answers.get(key, default))

    return DeploymentSpec(
        spec_id=f"dep-{project_id.hex[:8]}-c{cycle}",
        version="1",
        target_scope=AzureTargetScope(
            tenant_id=_get("tenant_id", "default-tenant"),
            subscription_id=_get("subscription_id", "default-subscription"),
            resource_group=_get("resource_group", f"rg-vibey-{project_id.hex[:8]}"),
            environment=_get("environment", "dev"),
            region=_get("region", "eastus"),
        ),
        identity=IdentityAuthority(
            identity_type=_get("identity_type", "managed_identity"),
            principal_id=_get("principal_id", "default-principal"),
        ),
        topology=TopologyConfig(
            service_type=_get("service_type", "container_app"),
            iac_provider=_get("iac_provider", "bicep"),
            sku=_get("sku", "consumption"),
        ),
        recovery_policy=RecoveryPolicy(progressive_exposure=_get("progressive_exposure", "canary")),
        verification=VerificationContract(),
        cost_boundary=CostBoundary(
            max_monthly_budget_usd=float(str(answers.get("max_monthly_budget_usd", 100.0))),
            max_deployment_cost_usd=float(str(answers.get("max_deployment_cost_usd", 10.0))),
        ),
    )


class DeployInterviewHandler:
    def __init__(
        self,
        *,
        ledger: PhaseLedger,
        gates: HumanGateRepository,
        clock: Clock,
        jobs: JobRepository | None = None,
    ) -> None:
        self._ledger = ledger
        self._gates = gates
        self._clock = clock
        self._jobs = jobs

    async def handle(self, job: JobRecord) -> Outcome:
        if job.kind != "deploy.interview":
            return Failure(FailureClass.VIBEY, "expected deploy.interview job")

        gate = await self._gates.latest_for_job(job.id)
        if gate is None:
            request = HumanGateRequest(
                kind="deploy_interview",
                prompt=(
                    "Deployment Elicitation: Please provide Azure target, "
                    "topology, and recovery parameters."
                ),
                options=("accept_defaults", "custom"),
                default_answer="accept_defaults",
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

        # Record answer to ledger
        await self._ledger.append_event(
            project_id=job.project_id,
            cycle=job.cycle,
            job_id=job.id,
            kind=EventKind.QUESTION_ASKED,
            payload={"stage": "deploy_elicitation", "prompt": gate.prompt},
        )
        await self._ledger.append_event(
            project_id=job.project_id,
            cycle=job.cycle,
            job_id=job.id,
            kind=EventKind.ANSWER_GIVEN,
            payload={"stage": "deploy_elicitation", "answer": gate.answer},
        )

        if self._jobs is not None:
            await self._jobs.enqueue(
                EnqueueRequest(
                    project_id=job.project_id,
                    cycle=job.cycle,
                    phase=Phase.DEPLOY_DESIGN,
                    kind="deploy.synthesize",
                    idempotency_key=idempotency_key(
                        job.project_id, job.cycle, "deploy.synthesize", str(job.id)
                    ),
                    requirement={"effort": Effort.HIGH.name.lower()},
                )
            )

        return Success({"status": "interview_completed", "answer": gate.answer})


class DeploySynthesizeHandler:
    def __init__(
        self,
        *,
        ledger: PhaseLedger,
        clock: Clock,
        jobs: JobRepository | None = None,
        spec_store: DeploymentSpecStore | None = None,
    ) -> None:
        self._ledger = ledger
        self._clock = clock
        self._jobs = jobs
        self._spec_store = spec_store

    async def handle(self, job: JobRecord) -> Outcome:
        if job.kind != "deploy.synthesize":
            return Failure(FailureClass.VIBEY, "expected deploy.synthesize job")

        if self._spec_store is not None:
            events = await self._ledger.all_for_project(job.project_id)
            answers: Mapping[str, object] = {}
            for event in events:
                if (
                    event.kind == EventKind.ANSWER_GIVEN
                    and event.payload.get("stage") == "deploy_elicitation"
                ):
                    answer = event.payload.get("answer")
                    if isinstance(answer, Mapping):
                        answers = answer
            spec = build_deployment_spec(
                project_id=job.project_id, cycle=job.cycle, answers=answers
            )
            errors = spec.validate()
            if errors:
                return Failure(
                    FailureClass.WORK, f"synthesized deployment spec invalid: {'; '.join(errors)}"
                )
            await self._spec_store.save_spec(job.project_id, spec)

        # Synthesize deployment artifacts
        await self._ledger.append_event(
            project_id=job.project_id,
            cycle=job.cycle,
            job_id=job.id,
            kind=EventKind.ARTIFACT_PRODUCED,
            payload={
                "artifact_type": "deployment_spec",
                "path": ".vibey/context/deploy/deployment-spec.md",
                "provenance": "trusted",
            },
        )

        if self._jobs is not None:
            await self._jobs.enqueue(
                EnqueueRequest(
                    project_id=job.project_id,
                    cycle=job.cycle,
                    phase=Phase.DEPLOY_DESIGN,
                    kind="deploy.spec",
                    idempotency_key=idempotency_key(
                        job.project_id, job.cycle, "deploy.spec", str(job.id)
                    ),
                    requirement={"effort": Effort.HIGH.name.lower()},
                )
            )

        return Success({"status": "synthesized", "artifacts": ["deployment-spec.md"]})
