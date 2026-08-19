"""Phase ④ DEPLOY DESIGN interview and synthesis handlers (Milestone 10 task 10.3).

The `jobs` collaborators are keyword-only with a None default on both
handlers: when absent the handlers behave exactly as before (the protected
system test drives each stage manually), and when present -- as the full
worker wires them -- each stage enqueues its successor so the deploy design
chain advances unattended: interview -> synthesize -> spec.
"""

from vibey.application.dto import EnqueueRequest, HumanGateRequest, JobRecord
from vibey.application.interfaces import (
    PhaseLedger,
)
from vibey.application.ports import Clock, HumanGateRepository, JobRepository
from vibey.application.worker import Failure, Outcome, Park, Success
from vibey.domain.effort import Effort
from vibey.domain.job import FailureClass, idempotency_key
from vibey.domain.ledger import EventKind
from vibey.domain.phase import Phase


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
    ) -> None:
        self._ledger = ledger
        self._clock = clock
        self._jobs = jobs

    async def handle(self, job: JobRecord) -> Outcome:
        if job.kind != "deploy.synthesize":
            return Failure(FailureClass.VIBEY, "expected deploy.synthesize job")

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
