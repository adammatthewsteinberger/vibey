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
from datetime import timedelta
from uuid import uuid4

from vibey.application.build_engine_run import BuildLedger, run_and_record
from vibey.application.dto import EngineEvent, EnqueueRequest, HumanGateRequest, JobRecord, RunSpec
from vibey.application.interfaces import (
    GateResult,
    GateRunner,
    LedgerReader,
    VerifyWorktrees,
)
from vibey.application.ports import Clock, EngineAdapter, HumanGateRepository, JobRepository
from vibey.application.worker import Defer, Failure, Outcome, Park, Success
from vibey.domain.effort import Effort
from vibey.domain.engine import IsolationLevel
from vibey.domain.job import FailureClass, idempotency_key
from vibey.domain.ledger import EventKind
from vibey.domain.phase import Phase
from vibey.domain.review import Severity


def gate_output_tail(result: GateResult, *, limit: int = 1500) -> str:
    """Both streams, tail-capped. pytest and most runners print the actual
    failure to stdout while stderr carries only warnings -- caught live
    when a failing gate's last_error showed nothing but a deprecation
    warning and the real assertion failure was silently discarded."""
    parts: list[str] = []
    stderr = result.stderr.strip()
    stdout = result.stdout.strip()
    if stderr:
        parts.append(stderr[-limit:])
    if stdout:
        parts.append(f"[stdout] {stdout[-limit:]}")
    return "\n".join(parts) or "(no output)"


def granted_limit(answer: Mapping[str, object], key: str) -> int | None:
    """A human's limit-grant from an answered exhausted gate:
    ``--raw '{"<key>": 6}'`` or the positional-pair form ``<key>=6``.
    Without this contract an exhausted park was a dead end -- answering
    un-parked the job, the bound re-tripped, and it parked again forever
    unless the human fixed the underlying state by hand."""
    sources: list[Mapping[str, object]] = [answer]
    nested = answer.get("answers")
    if isinstance(nested, Mapping):
        sources.append(nested)
    for source in sources:
        raw = source.get(key)
        if isinstance(raw, bool):
            continue
        if isinstance(raw, int):
            return raw
        if isinstance(raw, str) and raw.isdigit():
            return int(raw)
    return None


def granted_max_rounds(answer: Mapping[str, object]) -> int | None:
    """The exhausted-repair gates' grant key (see granted_limit)."""
    return granted_limit(answer, "max_rounds")


def granted_amount(answer: Mapping[str, object], key: str) -> float | None:
    """Like granted_limit, for fractional grants (budget dollars)."""
    sources: list[Mapping[str, object]] = [answer]
    nested = answer.get("answers")
    if isinstance(nested, Mapping):
        sources.append(nested)
    for source in sources:
        raw = source.get(key)
        if isinstance(raw, bool):
            continue
        if isinstance(raw, int | float):
            return float(raw)
        if isinstance(raw, str):
            try:
                return float(raw)
            except ValueError:
                continue
    return None


@dataclass(frozen=True, slots=True)
class VerifyRepairPolicy:
    """What turns a deterministic gate failure into a repair loop instead
    of a burned escalation ladder. Caught live: build.verify retries
    re-ran the same failing command with nothing in between able to
    change the code, so seven attempts burned to a terminal failure in
    minutes while the fix needed one engine session on the item branch."""

    ledger_reader: LedgerReader
    clock: Clock
    max_rounds: int = 3
    backoff: timedelta = timedelta(minutes=10)
    gates: HumanGateRepository | None = None
    """When present, an answered exhausted-gate for this job can raise
    the round bound (see granted_max_rounds)."""


class BuildVerifyHandler:
    def __init__(
        self,
        *,
        worktrees: VerifyWorktrees,
        gates: GateRunner,
        reviewer: EngineAdapter,
        ledger: BuildLedger,
        jobs: JobRepository,
        repair: VerifyRepairPolicy | None = None,
    ) -> None:
        self._worktrees = worktrees
        self._gates = gates
        self._reviewer = reviewer
        self._ledger = ledger
        self._jobs = jobs
        self._repair = repair

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
                detail = f"gate failed: {command}: {gate_output_tail(result)}"
                if self._repair is None:
                    return Failure(FailureClass.WORK, detail)
                return await self._repair_or_park(job, job.work_item_id, detail, self._repair)

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

        if self._repair is not None:
            # A passing verify closes its own earlier repair findings, or
            # they stay open in the ledger and poison review.triage into a
            # needless loop-back long after the code was fixed.
            await self._resolve_open_findings(job, job.work_item_id, self._repair)

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

    async def _verify_findings(
        self, job: JobRecord, item_id: str, repair: VerifyRepairPolicy
    ) -> tuple[list[str], list[str]]:
        """(all f_verify finding ids for this item+cycle, the open subset)."""
        prefix = f"f_verify_{item_id}_"
        raised: list[str] = []
        resolved: set[str] = set()
        for event in await repair.ledger_reader.all_for_project(job.project_id):
            if event.cycle != job.cycle:
                continue
            finding_id = str(event.payload.get("finding_id", ""))
            if not finding_id.startswith(prefix):
                continue
            if event.kind is EventKind.FINDING_RAISED:
                raised.append(finding_id)
            elif event.kind is EventKind.FINDING_RESOLVED:
                resolved.add(finding_id)
        return raised, [finding_id for finding_id in raised if finding_id not in resolved]

    async def _repair_or_park(
        self, job: JobRecord, item_id: str, detail: str, repair: VerifyRepairPolicy
    ) -> Outcome:
        raised, open_findings = await self._verify_findings(job, item_id, repair)
        retry_at = repair.clock.now() + repair.backoff

        if open_findings:
            # A repair for this item is already in flight; raising another
            # would double-spend an engine session on the same failure.
            return Defer(
                retry_at=retry_at,
                detail=f"verify gates failing for {item_id!r}; repair in flight",
            )
        allowed = repair.max_rounds
        if repair.gates is not None:
            gate = await repair.gates.latest_for_job(job.id)
            if gate is not None and gate.answer is not None:
                granted = granted_max_rounds(gate.answer)
                if granted is not None and granted > allowed:
                    allowed = granted
        if len(raised) >= allowed:
            return Park(
                HumanGateRequest(
                    kind="verify_repair_exhausted",
                    prompt=(
                        f"work item {item_id!r} failed verification after "
                        f"{len(raised)} repair rounds; latest: {detail[:500]}. "
                        "Grant more repair rounds by answering "
                        f"--raw '{{\"max_rounds\": {len(raised) + 3}}}', or fix the "
                        "branch by hand and answer anything to retry."
                    ),
                )
            )

        finding_id = f"f_verify_{item_id}_{uuid4().hex[:8]}"
        await self._ledger.record(
            project_id=job.project_id,
            cycle=job.cycle,
            job_id=job.id,
            engine_id=None,
            correlation_id=uuid4(),
            event=EngineEvent(
                kind=EventKind.FINDING_RAISED.value,
                at=repair.clock.now(),
                payload={
                    "finding_id": finding_id,
                    "severity": Severity.HIGH.value,
                    "text": detail,
                },
            ),
        )
        await self._jobs.enqueue(
            EnqueueRequest(
                project_id=job.project_id,
                cycle=job.cycle,
                phase=Phase.BUILD,
                kind="build.implement",
                idempotency_key=idempotency_key(
                    job.project_id, job.cycle, "build.implement", f"verify-repair-{finding_id}"
                ),
                work_item_id=item_id,
                payload={
                    **job.payload,
                    "repair_finding_id": finding_id,
                    "repair_detail": detail[:2000],
                },
            )
        )
        return Defer(
            retry_at=retry_at,
            detail=f"verify gates failed for {item_id!r}; repair {finding_id} enqueued",
        )

    async def _resolve_open_findings(
        self, job: JobRecord, item_id: str, repair: VerifyRepairPolicy
    ) -> None:
        _, open_findings = await self._verify_findings(job, item_id, repair)
        for finding_id in open_findings:
            await self._ledger.record(
                project_id=job.project_id,
                cycle=job.cycle,
                job_id=job.id,
                engine_id=None,
                correlation_id=uuid4(),
                event=EngineEvent(
                    kind=EventKind.FINDING_RESOLVED.value,
                    at=repair.clock.now(),
                    payload={
                        "finding_id": finding_id,
                        "resolution": "verification now passes for this work item",
                    },
                ),
            )


def _render_review_prompt(item_id: str, criteria_checked: Iterable[object], diff: str) -> str:
    items = list(criteria_checked)
    criteria = ", ".join(str(c) for c in items) if items else "(none)"
    return (
        f"Review work item {item_id} against acceptance criteria: {criteria}\n\n"
        f"Diff:\n{diff or '(no diff)'}\n"
    )


# Re-exported for the same reason `application/ports.py` re-exports the
# interfaces package: the seam moved, the import path should not break.
__all__ = [
    "GateResult",
    "GateRunner",
    "VerifyWorktrees",
]
