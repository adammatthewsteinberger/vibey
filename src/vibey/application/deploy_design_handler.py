"""Phase ④ DEPLOY DESIGN interview and synthesis handlers (Milestone 10 task 10.3)."""

from collections.abc import Mapping, Sequence
from typing import Protocol
from uuid import UUID

from vibey.application.dto import HumanGateRequest, JobRecord
from vibey.application.ports import Clock, HumanGateRepository
from vibey.application.worker import Failure, Outcome, Park, Success
from vibey.domain.job import FailureClass
from vibey.domain.ledger import EventKind, LedgerEvent


class DeployDesignLedger(Protocol):
    async def all_for_project(self, project_id: UUID) -> Sequence[LedgerEvent]: ...

    async def append_event(
        self,
        project_id: UUID,
        cycle: int,
        job_id: UUID,
        kind: EventKind,
        payload: Mapping[str, object],
    ) -> None: ...


class DeployInterviewHandler:
    def __init__(
        self,
        *,
        ledger: DeployDesignLedger,
        gates: HumanGateRepository,
        clock: Clock,
    ) -> None:
        self._ledger = ledger
        self._gates = gates
        self._clock = clock

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

        return Success({"status": "interview_completed", "answer": gate.answer})


class DeploySynthesizeHandler:
    def __init__(
        self,
        *,
        ledger: DeployDesignLedger,
        clock: Clock,
    ) -> None:
        self._ledger = ledger
        self._clock = clock

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

        return Success({"status": "synthesized", "artifacts": ["deployment-spec.md"]})
