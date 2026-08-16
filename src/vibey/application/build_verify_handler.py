"""Durable ``build.verify`` handler (M6 task 6.5): the project's own gates,
acceptance-criterion coverage, and a diff review by an engine that must
differ from the implementer -- deliberately a separate job from a different
engine than the one that wrote the code (phase-protocols.md section 2.3).

Verification is not "the model says it's fine." In order:

1. The work item's own gate commands (``ruff``, ``mypy``, ``pytest``, ...
   from ``vibey.toml``/the decomposer's ``VerificationSpec``). A non-zero
   exit is a ``WORK`` failure, full stop -- mechanical, no judgment involved.
2. Acceptance-criterion coverage: the item's verification must actually
   name which criteria it checks. An item with no criteria_checked never
   silently passes.
3. Only then, a diff review by a rotated engine at LOW effort, judged by
   the same VerdictRendered.complete convention build.implement uses.

On success, enqueues build.integrate (task 6.8), keyed to this verify job's
own id so a repair verify job (a fresh row, not a retry of this one) always
gets its own integrate job rather than colliding with a prior attempt's
idempotency key.
"""

import shlex
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol
from uuid import uuid4

from vibey.application.build_engine_run import BuildLedger, run_and_record
from vibey.application.dto import EnqueueRequest, JobRecord, RunSpec
from vibey.application.ports import EngineAdapter, JobRepository
from vibey.application.worker import Failure, Outcome, Success
from vibey.domain.effort import Effort
from vibey.domain.engine import IsolationLevel
from vibey.domain.job import FailureClass, idempotency_key
from vibey.domain.phase import Phase


@dataclass(frozen=True, slots=True)
class GateResult:
    returncode: int
    stdout: str
    stderr: str


class GateRunner(Protocol):
    async def run(self, argv: tuple[str, ...], *, cwd: Path) -> GateResult: ...


class VerifyWorktrees(Protocol):
    def path_for(self, item_id: str) -> Path: ...


class BuildVerifyHandler:
    def __init__(
        self,
        *,
        worktrees: VerifyWorktrees,
        gates: GateRunner,
        reviewer: EngineAdapter,
        ledger: BuildLedger,
        jobs: JobRepository,
    ) -> None:
        self._worktrees = worktrees
        self._gates = gates
        self._reviewer = reviewer
        self._ledger = ledger
        self._jobs = jobs

    async def handle(self, job: JobRecord) -> Outcome:
        if job.kind != "build.verify":
            return Failure(FailureClass.VIBEY, "expected build.verify job")
        if job.work_item_id is None:
            return Failure(FailureClass.VIBEY, "build.verify job is missing work_item_id")

        implementer = job.requirement.get("implementer_engine_id")
        if implementer is not None and implementer == self._reviewer.descriptor.engine_id.value:
            return Failure(FailureClass.VIBEY, "verifier must differ from the implementer")

        worktree = self._worktrees.path_for(job.work_item_id)
        verification = job.payload.get("verification", {})
        commands = verification.get("commands", ()) if isinstance(verification, Mapping) else ()

        for command in commands:
            result = await self._gates.run(tuple(shlex.split(str(command))), cwd=worktree)
            if result.returncode != 0:
                return Failure(
                    FailureClass.WORK, f"gate failed: {command}: {result.stderr.strip()}"
                )

        criteria_checked = (
            verification.get("criteria_checked", ()) if isinstance(verification, Mapping) else ()
        )
        if not criteria_checked:
            return Failure(
                FailureClass.WORK,
                f"work item {job.work_item_id!r} has no acceptance criteria checked "
                "by its verification",
            )

        diff = await self._gates.run(("git", "diff", "HEAD"), cwd=worktree)

        handle = await self._reviewer.start(
            RunSpec(
                run_id=uuid4(),
                worktree_path=worktree,
                prompt=_render_review_prompt(job.work_item_id, criteria_checked, diff.stdout),
                effort=Effort.LOW,
                isolation=IsolationLevel.WORKTREE,
            )
        )
        run_outcome = await run_and_record(self._reviewer, self._ledger, job=job, handle=handle)

        if not run_outcome.complete:
            return Failure(FailureClass.WORK, "diff review did not approve this work item")

        await self._jobs.enqueue(
            EnqueueRequest(
                project_id=job.project_id,
                cycle=job.cycle,
                phase=Phase.BUILD,
                kind="build.integrate",
                idempotency_key=idempotency_key(
                    job.project_id, job.cycle, "build.integrate", str(job.id)
                ),
                work_item_id=job.work_item_id,
                payload=job.payload,
                depends_on=(job.id,),
            )
        )
        return Success({"work_item_id": job.work_item_id, "gates_run": len(commands)})


def _render_review_prompt(item_id: str, criteria_checked: Iterable[object], diff: str) -> str:
    items = list(criteria_checked)
    criteria = ", ".join(str(c) for c in items) if items else "(none)"
    return (
        f"Review work item {item_id} against acceptance criteria: {criteria}\n\n"
        f"Diff:\n{diff or '(no diff)'}\n"
    )
