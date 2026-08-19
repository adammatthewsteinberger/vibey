"""Per-job engine selection: the first production caller of the rotation
stack (EngineSelector / EngineHealthService), invoked by the composition
root's BUILD factories at dispatch time -- rotation happens only at job
boundaries, never mid-turn (ADR-0007).

Three pieces:

- ``selection_inputs_for_job`` -- pure: derives the JobRequirement,
  forced-rotation exclusion, and WORK-retry affinity from the claimed job's
  own durable state (attempt number, ``assigned_engine`` from the previous
  attempt, the verify job's ``implementer_engine_id``).
- ``SelectingEngineProvider`` -- selects via SWRR, records the selection,
  and durably assigns the engine to the job; ``NoEligibleEngine`` becomes
  ``CapacityDeferred`` so an empty/unhealthy engine table defers the job
  instead of burning an attempt.
- ``RotationRecordingHandler`` -- wraps the constructed handler so the
  selected engine's health record sees the outcome: Success closes the
  circuit, a capacity Defer opens it (which is what makes the *next* claim
  rotate away automatically).
"""

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import timedelta
from uuid import UUID

from vibey.application.dto import JobRecord
from vibey.application.engine_health_service import EngineHealthService
from vibey.application.engine_selector import EngineSelector
from vibey.application.interfaces import Clock, EngineAdapter, JobHandler
from vibey.application.ports import JobRepository
from vibey.application.worker import CapacityDeferred, Defer, Outcome, Success
from vibey.domain.capacity import WindowExhausted
from vibey.domain.effort import (
    BUILD_LADDER_EXHAUSTED,
    PHASE_BASE_EFFORT,
    Effort,
    effort_for_attempt,
    forces_rotation,
)
from vibey.domain.engine import EngineId, JobRequirement
from vibey.domain.errors import EscalationExhausted, NoEligibleEngine
from vibey.domain.phase import Phase


@dataclass(frozen=True, slots=True)
class SelectionInputs:
    requirement: JobRequirement
    affinity: EngineId | None


def selection_inputs_for_job(job: JobRecord) -> SelectionInputs:
    """Pure derivation of what this job's engine selection must honor."""
    excluded: set[EngineId] = set()
    affinity: EngineId | None = None

    # A durable per-job exclusion list -- the wind-down follow-up's "must
    # not go back to the engine that wound down" constraint rides here.
    raw_excluded = job.requirement.get("excluded_engine_ids")
    if isinstance(raw_excluded, list | tuple):
        excluded.update(EngineId(str(entry)) for entry in raw_excluded)

    if job.kind == "build.verify":
        # The diff review runs at LOW and must come from a different engine
        # than the implementer (phase-protocols.md 2.3).
        implementer = str(job.requirement.get("implementer_engine_id", "") or "")
        if implementer:
            excluded.add(EngineId(implementer))
        effort = Effort.LOW
    else:
        base = PHASE_BASE_EFFORT[Phase.BUILD]
        attempt = max(job.attempts, 1)
        try:
            effort = effort_for_attempt(base, attempt)
        except EscalationExhausted:
            # Selection must never raise here: the handler owns the
            # exhausted-ladder Park. Select as if HIGH so a needless
            # nack/crash can't preempt the human gate.
            effort = Effort.HIGH
        previous = EngineId(job.assigned_engine) if job.assigned_engine else None
        if attempt > 1 and previous is not None:
            previous_effort = effort_for_attempt(base, min(attempt - 1, BUILD_LADDER_EXHAUSTED))
            if forces_rotation(previous_effort, effort):
                # Tier crossing: the escalated attempt must rotate away.
                excluded.add(previous)
            elif previous not in excluded:
                # Same-tier WORK retry: stickiness (affinity_factor 2.0).
                # An engine the requirement excludes never gets affinity.
                affinity = previous

    return SelectionInputs(
        requirement=JobRequirement(effort=effort, excluded=frozenset(excluded)),
        affinity=affinity,
    )


class SelectingEngineProvider:
    def __init__(
        self,
        *,
        selector: EngineSelector,
        health: EngineHealthService,
        adapters: Mapping[EngineId, EngineAdapter],
        jobs: JobRepository,
        clock: Clock,
        owner: str,
        allow_list: frozenset[EngineId] | None = None,
        backoff: timedelta = timedelta(minutes=5),
    ) -> None:
        self._selector = selector
        self._health = health
        self._adapters = adapters
        self._jobs = jobs
        self._clock = clock
        self._owner = owner
        self._allow_list = allow_list
        self._backoff = backoff

    async def select_for(self, job: JobRecord) -> EngineAdapter:
        inputs = selection_inputs_for_job(job)
        try:
            engine_id, _selection = await self._selector.select_engine(
                job.project_id,
                inputs.requirement,
                allow_list=self._allow_list,
                affinity_engine=inputs.affinity,
            )
        except NoEligibleEngine as exc:
            raise CapacityDeferred(self._clock.now() + self._backoff, str(exc)) from exc
        adapter = self._adapters.get(engine_id)
        if adapter is None:
            # Selected from health records but not configured in this worker
            # (e.g. an --engines allow-list narrower than the health table
            # should prevent this; defend anyway).
            raise CapacityDeferred(
                self._clock.now() + self._backoff,
                f"selected engine {engine_id.value} has no configured adapter",
            )
        await self._health.record_selection(job.project_id, engine_id)
        await self._jobs.assign_engine(job.id, owner=self._owner, engine_id=engine_id)
        return adapter


class RotationRecordingHandler:
    """Feeds the selected engine's outcome back into its health record.

    Success closes the circuit; a capacity Defer records a rejection whose
    probe deadline is the Defer's own retry_at (vibey's scheduling state,
    not a fabricated vendor payload) -- opening the circuit is what makes
    the next claim's selection rotate to a different engine.
    """

    def __init__(
        self,
        *,
        inner: JobHandler,
        health: EngineHealthService,
        project_id: UUID,
        engine_id: EngineId,
    ) -> None:
        self._inner = inner
        self._health = health
        self._project_id = project_id
        self._engine_id = engine_id

    async def handle(self, job: JobRecord) -> Outcome:
        outcome = await self._inner.handle(job)
        if isinstance(outcome, Success):
            await self._health.record_success(self._project_id, self._engine_id)
        elif isinstance(outcome, Defer):
            await self._health.record_capacity_rejection(
                self._project_id,
                self._engine_id,
                WindowExhausted(resets_at=outcome.retry_at),
            )
        return outcome
