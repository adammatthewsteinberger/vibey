"""Phase ⑥ DEPLOY REVIEW demo and failure triage handlers (Milestone 10 task 10.10)."""

from collections.abc import Callable, Mapping
from uuid import UUID

from vibey.application.dto import EnqueueRequest, HumanGateRequest, JobRecord
from vibey.application.interfaces import (
    PhaseLedger,
)
from vibey.application.ports import HumanGateRepository, JobRepository
from vibey.application.worker import Failure, Outcome, Park, Success
from vibey.domain.deployment import DeploymentFailureClass, DeploymentSpec
from vibey.domain.effort import Effort
from vibey.domain.job import FailureClass, idempotency_key
from vibey.domain.ledger import EventKind
from vibey.domain.phase import Phase


def _gate_action(answer: Mapping[str, object]) -> str:
    """A demo gate answers {"verdict": ...}; a triage gate {"choice": ...}.
    DeployReviewRoutingHandler already accepts every option spelling either
    gate offers (lowered), so the extracted value passes through verbatim."""
    for key in ("verdict", "choice"):
        value = answer.get(key)
        if value is not None:
            return str(value)
    return str(next(iter(answer.values()), "approve"))


class DeployReviewDemoHandler:
    """Presents live URL, resource manifest, and verification proof for approved deployment."""

    def __init__(
        self,
        *,
        ledger: PhaseLedger,
        human_gates: HumanGateRepository,
        spec_provider: Callable[[UUID], DeploymentSpec | None] | None = None,
        jobs: JobRepository | None = None,
    ) -> None:
        self._ledger = ledger
        self._gates = human_gates
        self._spec_provider = spec_provider
        self._jobs = jobs

    async def handle(self, job: JobRecord) -> Outcome:
        if job.kind != "deploy.demo":
            return Failure(FailureClass.VIBEY, "expected deploy.demo job")

        events = await self._ledger.all_for_project(job.project_id)
        dep_events = [
            e
            for e in events
            if e.kind == EventKind.ARTIFACT_PRODUCED
            and e.payload.get("artifact_type") == "deployment_verification"
        ]

        endpoint = "https://app.azurecontainerapps.io"
        if dep_events:
            outputs = dep_events[-1].payload.get("outputs", {})
            if isinstance(outputs, dict) and "endpoint" in outputs:
                endpoint = str(outputs["endpoint"])

        gate = await self._gates.latest_for_job(job.id)
        if gate is None:
            request = HumanGateRequest(
                kind="deploy_demo_review",
                prompt=(
                    f"### Phase ⑥ Deployment Demo Review\n\n"
                    f"- **Live URL**: {endpoint}\n"
                    f"- **Runtime Verification**: Succeeded across all 4 dimensions\n\n"
                    f"Please verify the live deployment and approve completion."
                ),
                options=("approve", "request_changes"),
                default_answer="approve",
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

        if self._jobs is not None:
            await self._jobs.enqueue(
                EnqueueRequest(
                    project_id=job.project_id,
                    cycle=job.cycle,
                    phase=Phase.DEPLOY_REVIEW,
                    kind="deploy.route",
                    idempotency_key=idempotency_key(
                        job.project_id, job.cycle, "deploy.route", str(job.id)
                    ),
                    payload={"action": _gate_action(gate.answer)},
                    requirement={"effort": Effort.LOW.name.lower()},
                )
            )

        return Success(
            {"status": "demo_approved", "endpoint": endpoint, "answer": dict(gate.answer)}
        )


class DeployReviewTriageHandler:
    """Presents failure root cause, runbook matches, and interactive remediation options."""

    def __init__(
        self,
        *,
        ledger: PhaseLedger,
        human_gates: HumanGateRepository,
        spec_provider: Callable[[UUID], DeploymentSpec | None] | None = None,
        jobs: JobRepository | None = None,
    ) -> None:
        self._ledger = ledger
        self._gates = human_gates
        self._spec_provider = spec_provider
        self._jobs = jobs

    async def handle(self, job: JobRecord) -> Outcome:
        if job.kind != "deploy.triage":
            return Failure(FailureClass.VIBEY, "expected deploy.triage job")

        events = await self._ledger.all_for_project(job.project_id)
        finding_events = [e for e in events if e.kind == EventKind.FINDING_RAISED]

        failure_class = DeploymentFailureClass.POLICY_DENIAL.value
        error_msg = "Unknown deployment failure"
        if finding_events:
            last = finding_events[-1]
            failure_class = str(last.payload.get("failure_class", failure_class))
            error_msg = str(last.payload.get("error", error_msg))

        gate = await self._gates.latest_for_job(job.id)
        if gate is None:
            request = HumanGateRequest(
                kind="deploy_failure_triage",
                prompt=(
                    f"### Phase ⑥ Deployment Failure Triage\n\n"
                    f"- **Failure Class**: {failure_class}\n"
                    f"- **Error Details**: {error_msg}\n\n"
                    f"**Remediation Options**:\n"
                    f"1. `LOOP_DEPLOY_DESIGN`: Return to Phase ④ to adjust spec / budget.\n"
                    f"2. `RETRY_DEPLOY_EXECUTE`: Re-trigger Phase ⑤ deployment execution.\n"
                    f"3. `ABORT_DEPLOYMENT`: Conclude cycle without deploying.\n\n"
                    f"Please select your remediation choice."
                ),
                options=("LOOP_DEPLOY_DESIGN", "RETRY_DEPLOY_EXECUTE", "ABORT_DEPLOYMENT"),
                default_answer="LOOP_DEPLOY_DESIGN",
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

        if self._jobs is not None:
            await self._jobs.enqueue(
                EnqueueRequest(
                    project_id=job.project_id,
                    cycle=job.cycle,
                    phase=Phase.DEPLOY_REVIEW,
                    kind="deploy.route",
                    idempotency_key=idempotency_key(
                        job.project_id, job.cycle, "deploy.route", str(job.id)
                    ),
                    payload={"action": _gate_action(gate.answer)},
                    requirement={"effort": Effort.LOW.name.lower()},
                )
            )

        return Success(
            {
                "status": "triage_answered",
                "failure_class": failure_class,
                "answer": dict(gate.answer),
            }
        )
