# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
"""Durable ``review.collect`` handler (M7 task 7.2).

Holds the review conversation:
- Captures user verdicts (accept, changes, cancel)
- Turns free-text change requests into durable ``FindingRaised`` events
- Answers "why did you do X" questions by reading the ledger rather than
  re-asking the model.
- On accept or changes, enqueues ``review.triage`` to classify open findings.
"""

from uuid import uuid4

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
from vibey.domain.projections import answer_why_question
from vibey.domain.review import Ambiguity, Severity, UserVerdict


class ReviewCollectHandler:
    def __init__(
        self,
        *,
        ledger: PhaseLedger,
        gates: HumanGateRepository,
        jobs: JobRepository,
        clock: Clock,
    ) -> None:
        self._ledger = ledger
        self._gates = gates
        self._jobs = jobs
        self._clock = clock

    async def handle(self, job: JobRecord) -> Outcome:
        if job.kind != "review.collect":
            return Failure(FailureClass.VIBEY, "expected review.collect job")

        gate = await self._gates.latest_for_job(job.id)
        if gate is None:
            request = HumanGateRequest(
                kind="approval",
                prompt=(
                    f"Review artifacts ready for cycle {job.cycle}. "
                    "Accept, request changes, or ask questions."
                ),
                options=(
                    UserVerdict.ACCEPT.value,
                    UserVerdict.CHANGES.value,
                    UserVerdict.CANCEL.value,
                ),
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
        if "question" in answer_data:
            question_text = str(answer_data["question"])
            events = await self._ledger.all_for_project(job.project_id)
            explanation = answer_why_question(events, question_text)
            return Success({"question": question_text, "answer": explanation})

        verdict_str = str(answer_data.get("verdict", "")).lower()

        if verdict_str == UserVerdict.CANCEL.value:
            return Success({"verdict": UserVerdict.CANCEL.value, "cancelled": True})

        findings_count = 0
        if verdict_str == UserVerdict.CHANGES.value:
            feedback = answer_data.get("feedback") or answer_data.get("changes") or ()
            items: list[str] = (
                [str(f) for f in feedback]
                if isinstance(feedback, list | tuple)
                else [str(feedback)]
                if str(feedback).strip()
                else []
            )

            for item_text in items:
                findings_count += 1
                fid = f"f_user_{job.cycle}_{uuid4().hex[:8]}"
                await self._ledger.append_event(
                    project_id=job.project_id,
                    cycle=job.cycle,
                    job_id=job.id,
                    kind=EventKind.FINDING_RAISED,
                    payload={
                        "finding_id": fid,
                        "text": item_text,
                        "severity": Severity.MEDIUM.value,
                        "ambiguity": Ambiguity.NEEDS_CLARIFICATION.value,
                    },
                )

        # On accept or changes, advance to triage
        await self._jobs.enqueue(
            EnqueueRequest(
                project_id=job.project_id,
                cycle=job.cycle,
                phase=Phase.REVIEW,
                kind="review.triage",
                idempotency_key=idempotency_key(
                    job.project_id, job.cycle, "review.triage", str(job.id)
                ),
                requirement={"effort": Effort.HIGH.name.lower()},
            )
        )

        return Success(
            {
                "verdict": verdict_str,
                "findings_raised": findings_count,
            }
        )
