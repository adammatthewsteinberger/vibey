# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Durable ``review.triage`` handler (M7 task 7.4 & 7.5).

Performs severity x ambiguity classification on open findings:
- Severity: CRITICAL, HIGH, MEDIUM, LOW.
- Ambiguity: CLEAR (all 4 conjunctive conditions met) vs NEEDS_CLARIFICATION.
- Evaluates next_phase_after_review from domain/phase.py:
  - If no findings: routes to DONE and enqueues ``review.deployment_choice``.
  - If CLEAR findings only: fast loop-back to BUILD (enqueues ``build.plan``).
  - If any NEEDS_CLARIFICATION or strict: routes to DESIGN (enqueues ``design.interview``).
- Increments the cycle and updates project state on loop-back.
- Critical findings unconditionally require Effort.MAX.
"""

from vibey.application.dto import EnqueueRequest, JobRecord
from vibey.application.interfaces import (
    DesignSpecRepository,
    PhaseLedger,
    ProjectTransitioner,
)
from vibey.application.ports import Clock, JobRepository
from vibey.application.review_demo_handler import DesignSpecReader
from vibey.application.worker import Failure, Outcome, Success
from vibey.domain.effort import Effort, triage_required_effort
from vibey.domain.job import FailureClass, idempotency_key
from vibey.domain.phase import Phase, next_phase_after_review
from vibey.domain.projections import build_decision_log, build_deltas
from vibey.domain.review import (
    FindingRef,
    Severity,
    triage_finding,
)


class ReviewTriageHandler:
    def __init__(
        self,
        *,
        ledger: PhaseLedger,
        specs: DesignSpecReader,
        jobs: JobRepository,
        clock: Clock,
        projects: ProjectTransitioner | object = None,
        spec_store: DesignSpecRepository | None = None,
    ) -> None:
        self._ledger = ledger
        self._specs = specs
        self._jobs = jobs
        self._clock = clock
        self._projects = projects
        self._spec_store = spec_store

    async def handle(self, job: JobRecord) -> Outcome:
        if job.kind != "review.triage":
            return Failure(FailureClass.VIBEY, "expected review.triage job")

        events = await self._ledger.all_for_project(job.project_id)
        spec = await self._specs.load(job.project_id, job.cycle)
        deltas = build_deltas(events)
        decisions = build_decision_log(events)

        open_findings = [f for f in deltas.findings if not f.resolved]

        if not open_findings:
            # Route to DONE / deployment choice
            await self._jobs.enqueue(
                EnqueueRequest(
                    project_id=job.project_id,
                    cycle=job.cycle,
                    phase=Phase.REVIEW,
                    kind="review.deployment_choice",
                    idempotency_key=idempotency_key(
                        job.project_id, job.cycle, "review.deployment_choice", str(job.id)
                    ),
                    requirement={"effort": Effort.LOW.name.lower()},
                )
            )
            return Success(
                {
                    "triaged_count": 0,
                    "next_phase": Phase.DONE.value,
                    "has_critical": False,
                }
            )

        triaged_refs: list[FindingRef] = []
        for finding in open_findings:
            ref = triage_finding(
                finding.finding_id,
                finding.text,
                spec=spec,
                decisions=decisions,
            )
            triaged_refs.append(ref)

        effort = triage_required_effort(triaged_refs)
        has_critical = any(f.severity is Severity.CRITICAL for f in triaged_refs)
        strict_loopback = bool(job.payload.get("strict_loopback", False))
        next_phase = next_phase_after_review(triaged_refs, strict_loopback=strict_loopback)

        next_cycle = job.cycle + 1
        if self._projects is not None and hasattr(self._projects, "transition"):
            await self._projects.transition(
                job.project_id,
                expected=Phase.REVIEW,
                to=next_phase,
                cycle=next_cycle,
            )

        if next_phase is Phase.DESIGN:
            await self._jobs.enqueue(
                EnqueueRequest(
                    project_id=job.project_id,
                    cycle=next_cycle,
                    phase=Phase.DESIGN,
                    kind="design.interview",
                    idempotency_key=idempotency_key(
                        job.project_id, next_cycle, "design.interview", str(job.id)
                    ),
                    requirement={"effort": effort.name.lower()},
                )
            )
        else:
            # The earlier `if not open_findings:` branch already returns for
            # Phase.DONE, so by this point next_phase can only be DESIGN or
            # BUILD -- next_phase_after_review's DONE case is unreachable
            # here (findings is guaranteed non-empty).
            #
            # The fast loop-back re-decomposes at cycle+1, but the spec store
            # is cycle-scoped and cycle+1 has none -- carry the accepted spec
            # forward explicitly (an auditable save, never a silent loader
            # fallback). The DESIGN path deliberately does not carry: a
            # design re-run produces a new spec.
            if self._spec_store is not None and spec is not None:
                await self._spec_store.save(job.project_id, next_cycle, spec)
            await self._jobs.enqueue(
                EnqueueRequest(
                    project_id=job.project_id,
                    cycle=next_cycle,
                    phase=Phase.BUILD,
                    kind="build.plan",
                    idempotency_key=idempotency_key(
                        job.project_id, next_cycle, "build.plan", str(job.id)
                    ),
                    requirement={"effort": effort.name.lower()},
                )
            )

        return Success(
            {
                "triaged_count": len(triaged_refs),
                "next_phase": next_phase.value,
                "has_critical": has_critical,
            }
        )
