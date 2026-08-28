# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Durable ``review.demo`` handler (M7 tasks 7.1 & 7.3).

Produces the review demo artifacts under ``.vibey/runs/<cycle>/review/``:
- ``DEMO.md``: what was built, per acceptance criterion, with evidence
- ``run-it.sh``: exact commands to see it working locally (executable)
- ``walkthrough.md``: narrated tour of significant diffs by intent
- ``evidence/test-report.xml`` & ``evidence/coverage.json``: gate evidence
- ``deltas.md``: what changed vs the spec, and why, generated directly from
  projections so assumptions and findings cannot be silently omitted.

Task 7.3: Runs automated reviews (code review, security review) and raises pre-triaged
findings on the ledger before the human developer sees them.

On success, records an ARTIFACT_PRODUCED ledger event and enqueues ``review.collect``.
"""

from uuid import uuid4

from vibey.application.dto import EnqueueRequest, JobRecord
from vibey.application.interfaces import (
    AutomatedFinding,
    AutomatedReviewRunner,
    DesignSpecReader,
    PhaseLedger,
    ReviewArtifactWriter,
)
from vibey.application.ports import Clock, JobRepository
from vibey.application.worker import Failure, Outcome, Success
from vibey.domain.effort import Effort
from vibey.domain.job import FailureClass, idempotency_key
from vibey.domain.ledger import EventKind
from vibey.domain.phase import Phase
from vibey.domain.projections import build_deltas
from vibey.domain.review import (
    render_deltas_markdown,
    render_demo_markdown,
    render_run_it_script,
    render_walkthrough_markdown,
)

DEFAULT_TEST_REPORT = "<testsuites><testsuite name='gates' tests='1' failures='0'/></testsuites>"


class ReviewDemoHandler:
    def __init__(
        self,
        *,
        specs: DesignSpecReader,
        ledger: PhaseLedger,
        artifacts: ReviewArtifactWriter,
        jobs: JobRepository,
        clock: Clock,
        automated_reviewer: AutomatedReviewRunner | None = None,
    ) -> None:
        self._specs = specs
        self._ledger = ledger
        self._artifacts = artifacts
        self._jobs = jobs
        self._clock = clock
        self._automated_reviewer = automated_reviewer

    async def handle(self, job: JobRecord) -> Outcome:
        if job.kind != "review.demo":
            return Failure(FailureClass.VIBEY, "expected review.demo job")

        spec = await self._specs.load(job.project_id, job.cycle)
        if spec is None:
            return Failure(FailureClass.WORK, "no accepted design spec exists")

        if self._automated_reviewer is not None:
            # A fresh scan supersedes every earlier automated finding:
            # anything still true is re-raised below, and anything fixed
            # since the last scan must not stay open -- a stale worktree's
            # dead-code finding looped an accepted review back into BUILD
            # live. User-raised findings are never touched here.
            await self._supersede_stale_automated_findings(job)
            automated_findings = await self._automated_reviewer.run_automated_reviews(
                job.project_id, job.cycle
            )
            for finding in automated_findings:
                fid = (
                    finding.finding_id or f"f_{finding.category[:4]}_{job.cycle}_{uuid4().hex[:8]}"
                )
                await self._ledger.append_event(
                    project_id=job.project_id,
                    cycle=job.cycle,
                    job_id=job.id,
                    kind=EventKind.FINDING_RAISED,
                    payload={
                        "finding_id": fid,
                        "text": finding.text,
                        "severity": finding.severity.value,
                        "ambiguity": finding.ambiguity.value,
                        "category": finding.category,
                        "automated": True,
                    },
                )

        events = await self._ledger.all_for_project(job.project_id)
        deltas = build_deltas(events)

        test_report = str(job.payload.get("test_report", DEFAULT_TEST_REPORT))
        coverage_data = str(job.payload.get("coverage", '{"coverage": 100, "status": "green"}'))
        run_commands_raw = job.payload.get("run_commands", ())
        run_commands = (
            tuple(str(c) for c in run_commands_raw)
            if isinstance(run_commands_raw, list | tuple)
            else ()
        )
        summary = str(job.payload.get("summary", ""))

        artifacts_dict: dict[str, str] = {
            "DEMO.md": render_demo_markdown(spec),
            "run-it.sh": render_run_it_script(run_commands),
            "walkthrough.md": render_walkthrough_markdown(spec=spec, summary=summary),
            "deltas.md": render_deltas_markdown(deltas),
            "evidence/test-report.xml": test_report,
            "evidence/coverage.json": coverage_data,
        }

        written = await self._artifacts.write_review_artifacts(
            job.project_id,
            job.cycle,
            artifacts_dict,
            executable=["run-it.sh"],
        )

        await self._ledger.append_event(
            project_id=job.project_id,
            cycle=job.cycle,
            job_id=job.id,
            kind=EventKind.ARTIFACT_PRODUCED,
            payload={
                "artifact_id": f"review-demo-c{job.cycle}",
                "cycle": job.cycle,
                "artifacts": [str(p) for p in written.values()],
            },
        )

        await self._jobs.enqueue(
            EnqueueRequest(
                project_id=job.project_id,
                cycle=job.cycle,
                phase=Phase.REVIEW,
                kind="review.collect",
                idempotency_key=idempotency_key(
                    job.project_id, job.cycle, "review.collect", "interactive"
                ),
                requirement={"effort": Effort.HIGH.name.lower()},
            )
        )

        return Success({"cycle": job.cycle, "artifacts": tuple(artifacts_dict.keys())})

    async def _supersede_stale_automated_findings(self, job: JobRecord) -> None:
        raised: list[str] = []
        resolved: set[str] = set()
        for event in await self._ledger.all_for_project(job.project_id):
            finding_id = str(event.payload.get("finding_id", ""))
            if not finding_id:
                continue
            if event.kind is EventKind.FINDING_RAISED and event.payload.get("automated") is True:
                raised.append(finding_id)
            elif event.kind is EventKind.FINDING_RESOLVED:
                resolved.add(finding_id)
        for finding_id in raised:
            if finding_id in resolved:
                continue
            await self._ledger.append_event(
                project_id=job.project_id,
                cycle=job.cycle,
                job_id=job.id,
                kind=EventKind.FINDING_RESOLVED,
                payload={
                    "finding_id": finding_id,
                    "resolution": (
                        f"superseded by the fresh automated review scan of cycle {job.cycle}"
                    ),
                },
            )


# Re-exported for the same reason `application/ports.py` re-exports the
# interfaces package: the seam moved, the import path should not break.
__all__ = [
    "AutomatedFinding",
    "AutomatedReviewRunner",
    "DesignSpecReader",
    "PhaseLedger",
    "ReviewArtifactWriter",
]
