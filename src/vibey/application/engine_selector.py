"""Engine selector: the first production caller of domain/rotation.select().

Combines engine health records, rotation cursor state, and job requirements
to select the next engine using SWRR. Updates the rotation cursor atomically.
"""

from datetime import UTC, datetime, timedelta
from uuid import UUID

from vibey.application.dto import RotationCursor
from vibey.application.engine_health_service import EngineHealthService
from vibey.application.interfaces.engines import RotationCursorRepository
from vibey.domain.capacity import Available
from vibey.domain.circuit import Circuit, CircuitState
from vibey.domain.engine import EngineDescriptor, EngineId, JobRequirement
from vibey.domain.errors import NoEligibleEngine
from vibey.domain.rotation import (
    Candidate,
    EngineRuntime,
    Selection,
    eligible,
    fidelity_factor,
    health_factor,
    select,
)

# Authentication TTL from architecture doc
AUTH_TTL = timedelta(hours=24)


class EngineSelector:
    """Selects engines using SWRR over eligible, healthy engines."""

    def __init__(
        self,
        health_service: EngineHealthService,
        cursor_repository: RotationCursorRepository,
        descriptors: dict[EngineId, EngineDescriptor],
    ) -> None:
        self._health_service = health_service
        self._cursor_repository = cursor_repository
        self._descriptors = descriptors

    async def select_engine(
        self,
        project_id: UUID,
        requirement: JobRequirement,
        allow_list: frozenset[EngineId] | None = None,
        cost_aware: bool = False,
        affinity_engine: EngineId | None = None,
    ) -> tuple[EngineId, Selection]:
        """Select next engine using SWRR.

        Returns (engine_id, Selection with updated cursor state).
        Raises NoEligibleEngine if no engines meet requirements.
        """
        # Get health records
        health_records = await self._health_service.list_for_project(project_id)

        # Build EngineRuntime objects
        now = datetime.now(UTC)
        runtimes = []
        for record in health_records:
            descriptor = self._descriptors.get(record.engine_id)
            if descriptor is None:
                continue

            # Check auth TTL
            auth_valid = record.auth_ok_at is not None and (now - record.auth_ok_at) < AUTH_TTL

            # Build circuit state
            circuit = Circuit(
                state=CircuitState(record.circuit),
                capacity=Available(),
                probe=None,
                consecutive_failures=record.consecutive_fail,
                ewma_failure=record.ewma_failure,
            )

            runtimes.append(
                EngineRuntime(
                    engine_id=record.engine_id,
                    descriptor=descriptor,
                    circuit=circuit,
                    installed=record.installed,
                    conformance_ok=record.conformance_ok,
                    auth_valid=auth_valid,
                )
            )

        # Filter to eligible engines
        eligible_runtimes = eligible(runtimes, requirement=requirement, allow_list=allow_list)
        if not eligible_runtimes:
            raise NoEligibleEngine(f"No engines meet requirements for project {project_id}")

        # Get rotation cursors
        cursors = await self._cursor_repository.list_for_project(project_id)
        cursor_map = {c.engine_id: c for c in cursors}

        # Initialize cursors for any missing engines
        if len(cursor_map) < len(eligible_runtimes):
            all_engine_ids = tuple(self._descriptors.keys())
            await self._cursor_repository.initialize_for_project(project_id, all_engine_ids)
            cursors = await self._cursor_repository.list_for_project(project_id)
            cursor_map = {c.engine_id: c for c in cursors}

        # Build candidates
        candidates: list[Candidate] = []
        for runtime in eligible_runtimes:
            cursor = cursor_map.get(runtime.engine_id)
            if cursor is None:
                # Shouldn't happen after initialization, but handle gracefully
                cursor = RotationCursor(
                    project_id=project_id,
                    engine_id=runtime.engine_id,
                    current=0,
                    order=len(candidates),
                )

            # Calculate factors
            h_factor = health_factor(runtime.circuit)
            f_factor = fidelity_factor(runtime.descriptor, requirement.effort)
            c_factor = 1.0  # Cost factor disabled by default
            a_factor = 2.0 if affinity_engine == runtime.engine_id else 1.0

            candidates.append(
                Candidate(
                    engine_id=runtime.engine_id,
                    base_weight=runtime.descriptor.base_weight,
                    current=cursor.current,
                    order=cursor.order,
                    health_factor=h_factor,
                    fidelity_factor=f_factor,
                    cost_factor=c_factor,
                    affinity_factor=a_factor,
                )
            )

        # Select using SWRR
        selection = select(candidates)

        # Update rotation cursors
        updated_cursors = tuple(
            RotationCursor(
                project_id=project_id,
                engine_id=c.engine_id,
                current=c.current,
                order=c.order,
            )
            for c in selection.candidates
        )
        await self._cursor_repository.update_many(project_id, updated_cursors)

        return selection.engine_id, selection


__all__ = ["EngineSelector"]
