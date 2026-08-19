"""Durable ``build.decompose`` handler (M6 task 6.1).

Turns the accepted DESIGN spec into a dependency-ordered work-item graph and
fans it out as ``build.implement`` jobs. The producer's first returned
``WorkItem`` is the walking skeleton by contract -- it must have no
dependencies, matching phase-protocols.md 2.1's "goes first, alone" rule --
and items must be returned in an order where every dependency was already
enqueued (topologically valid), which this handler enforces at fan-out time
rather than trusting the producer.
"""

from collections.abc import Sequence
from dataclasses import asdict
from uuid import UUID

from vibey.application.dto import EnqueueRequest, JobRecord
from vibey.application.interfaces import (
    DesignSpecReader,
    WorkPlanProducer,
)
from vibey.application.ports import JobRepository
from vibey.application.worker import Failure, Outcome, Success
from vibey.domain.job import FailureClass, idempotency_key
from vibey.domain.phase import Phase
from vibey.domain.plan import WorkItem, validate_decomposition


class BuildDecomposeHandler:
    def __init__(
        self,
        *,
        specs: DesignSpecReader,
        decomposer: WorkPlanProducer,
        jobs: JobRepository,
    ) -> None:
        self._specs = specs
        self._decomposer = decomposer
        self._jobs = jobs

    async def handle(self, job: JobRecord) -> Outcome:
        # "build.plan" is the review fast loop-back's spelling of the same
        # work (review_triage_handler.py enqueues it at cycle+1); both kinds
        # decompose the cycle's accepted spec.
        if job.kind not in ("build.decompose", "build.plan"):
            return Failure(FailureClass.VIBEY, "expected build.decompose job")
        spec = await self._specs.load(job.project_id, job.cycle)
        if spec is None:
            return Failure(FailureClass.WORK, "no accepted design spec exists")

        items = await self._decomposer.decompose(spec)
        if not items:
            return Failure(FailureClass.WORK, "decomposition produced no work items")

        criteria_ids = tuple(criterion.criterion_id for criterion in spec.criteria)
        violations = validate_decomposition(
            items, criteria_ids=criteria_ids, walking_skeleton_item_id=items[0].item_id
        )
        if violations:
            return Failure(FailureClass.WORK, "; ".join(violations))

        enqueued = await self._fan_out(job.project_id, job.cycle, items)
        if enqueued is None:
            return Failure(
                FailureClass.VIBEY,
                "decomposition item order is not topologically valid "
                "(a dependency was not enqueued before its dependent)",
            )
        return Success({"work_items": len(items)})

    async def _fan_out(
        self, project_id: UUID, cycle: int, items: Sequence[WorkItem]
    ) -> dict[str, JobRecord] | None:
        job_by_item: dict[str, JobRecord] = {}
        for item in items:
            try:
                depends_on = tuple(job_by_item[dep].id for dep in item.depends_on)
            except KeyError:
                return None
            job_by_item[item.item_id] = await self._jobs.enqueue(
                EnqueueRequest(
                    project_id=project_id,
                    cycle=cycle,
                    phase=Phase.BUILD,
                    kind="build.implement",
                    idempotency_key=idempotency_key(
                        project_id, cycle, "build.implement", item.item_id
                    ),
                    work_item_id=item.item_id,
                    payload={"title": item.title, "verification": asdict(item.verification)},
                    requirement={"effort": item.est_effort.name.lower()},
                    depends_on=depends_on,
                )
            )
        return job_by_item


# Re-exported for the same reason `application/ports.py` re-exports the
# interfaces package: the seam moved, the import path should not break.
__all__ = [
    "DesignSpecReader",
    "WorkPlanProducer",
]
