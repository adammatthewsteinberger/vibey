# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://hire.adam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
"""Engine health service: wraps PostgresEngineHealthRepository with
business logic for updating health records based on conformance, capacity
states, and selection outcomes.
"""

from datetime import UTC, datetime
from uuid import UUID

from vibey.application.dto import EngineHealthRecord, PreflightResult
from vibey.application.interfaces.engines import EngineHealthRepository
from vibey.domain.capacity import (
    AuthenticationFailed,
    CapacityState,
    CreditsExhausted,
    WindowExhausted,
)
from vibey.domain.engine import EngineId


class EngineHealthService:
    """Application service for engine health records."""

    def __init__(self, repository: EngineHealthRepository) -> None:
        self._repository = repository

    async def get_or_create(self, project_id: UUID, engine_id: EngineId) -> EngineHealthRecord:
        """Get existing health record or create a new one with defaults."""
        existing = await self._repository.get(project_id, engine_id.value)
        if existing is not None:
            return existing

        # Create default record
        return EngineHealthRecord(
            project_id=project_id,
            engine_id=engine_id,
            installed=False,
            version=None,
            conformance_ok=False,
            conformance_at=None,
            auth_ok_at=None,
            circuit="closed",
            capacity_state=None,
            resets_at=None,
            probe_next_at=None,
            probe_attempt=0,
            consecutive_fail=0,
            ewma_failure=0.0,
            cost_usd_cycle=0.0,
            selected_count=0,
        )

    async def record_preflight(
        self,
        project_id: UUID,
        engine_id: EngineId,
        preflight: PreflightResult,
    ) -> EngineHealthRecord:
        """Worker-startup refresh: installed/version/auth from a fresh
        preflight, PRESERVING the conformance verdict -- conformance is
        doctor's to grant (update_from_preflight), and a routine startup
        sweep must never silently revoke or forge it."""
        record = await self.get_or_create(project_id, engine_id)
        now = datetime.now(UTC)
        updated = EngineHealthRecord(
            project_id=record.project_id,
            engine_id=record.engine_id,
            installed=preflight.installed,
            version=preflight.version,
            conformance_ok=record.conformance_ok,
            conformance_at=record.conformance_at,
            auth_ok_at=now if preflight.auth_ok else record.auth_ok_at,
            circuit=record.circuit,
            capacity_state=record.capacity_state,
            resets_at=record.resets_at,
            probe_next_at=record.probe_next_at,
            probe_attempt=record.probe_attempt,
            consecutive_fail=record.consecutive_fail,
            ewma_failure=record.ewma_failure,
            cost_usd_cycle=record.cost_usd_cycle,
            selected_count=record.selected_count,
        )
        return await self._repository.upsert(updated)

    async def update_from_preflight(
        self,
        project_id: UUID,
        engine_id: EngineId,
        preflight: PreflightResult,
        conformance_ok: bool,
    ) -> EngineHealthRecord:
        """Update health record based on preflight check results."""
        record = await self.get_or_create(project_id, engine_id)

        now = datetime.now(UTC)
        auth_ok_at = now if preflight.auth_ok else None

        updated = EngineHealthRecord(
            project_id=record.project_id,
            engine_id=record.engine_id,
            installed=preflight.installed,
            version=preflight.version,
            conformance_ok=conformance_ok,
            conformance_at=now if conformance_ok else record.conformance_at,
            auth_ok_at=auth_ok_at,
            circuit=record.circuit,
            capacity_state=record.capacity_state,
            resets_at=record.resets_at,
            probe_next_at=record.probe_next_at,
            probe_attempt=record.probe_attempt,
            consecutive_fail=record.consecutive_fail,
            ewma_failure=record.ewma_failure,
            cost_usd_cycle=record.cost_usd_cycle,
            selected_count=record.selected_count,
        )

        return await self._repository.upsert(updated)

    async def record_capacity_rejection(
        self,
        project_id: UUID,
        engine_id: EngineId,
        capacity_state: CapacityState,
    ) -> EngineHealthRecord:
        """Record a capacity rejection and update circuit state accordingly."""
        record = await self.get_or_create(project_id, engine_id)

        circuit_state = record.circuit
        capacity_state_str: str | None = None
        resets_at = None
        probe_next_at = None

        if isinstance(capacity_state, CreditsExhausted):
            circuit_state = "open"
            capacity_state_str = "CreditsExhausted"
            # No resets_at for credits exhausted (enforced by DB constraint)
            # Probe on exponential backoff
            from datetime import timedelta

            probe_attempt = record.probe_attempt + 1
            probe_next_at = datetime.now(UTC) + timedelta(minutes=min(5 * (2**probe_attempt), 30))

        elif isinstance(capacity_state, WindowExhausted):
            circuit_state = "open"
            capacity_state_str = "WindowExhausted"
            resets_at = capacity_state.resets_at
            probe_next_at = capacity_state.resets_at  # Probe when window resets

        elif isinstance(capacity_state, AuthenticationFailed):
            circuit_state = "open"
            capacity_state_str = "AuthenticationFailed"
            # Auth failures don't auto-probe - need manual intervention

        updated = EngineHealthRecord(
            project_id=record.project_id,
            engine_id=record.engine_id,
            installed=record.installed,
            version=record.version,
            conformance_ok=record.conformance_ok,
            conformance_at=record.conformance_at,
            auth_ok_at=record.auth_ok_at,
            circuit=circuit_state,
            capacity_state=capacity_state_str,
            resets_at=resets_at,
            probe_next_at=probe_next_at,
            probe_attempt=record.probe_attempt + 1,
            consecutive_fail=record.consecutive_fail + 1,
            ewma_failure=min(1.0, record.ewma_failure * 0.9 + 0.1),  # EWMA update
            cost_usd_cycle=record.cost_usd_cycle,
            selected_count=record.selected_count,
        )

        return await self._repository.upsert(updated)

    async def record_selection(
        self, project_id: UUID, engine_id: EngineId, cost_usd: float = 0.0
    ) -> EngineHealthRecord:
        """Record that an engine was selected for work."""
        record = await self.get_or_create(project_id, engine_id)

        updated = EngineHealthRecord(
            project_id=record.project_id,
            engine_id=record.engine_id,
            installed=record.installed,
            version=record.version,
            conformance_ok=record.conformance_ok,
            conformance_at=record.conformance_at,
            auth_ok_at=record.auth_ok_at,
            circuit=record.circuit,
            capacity_state=record.capacity_state,
            resets_at=record.resets_at,
            probe_next_at=record.probe_next_at,
            probe_attempt=record.probe_attempt,
            consecutive_fail=record.consecutive_fail,
            ewma_failure=record.ewma_failure,
            cost_usd_cycle=record.cost_usd_cycle + cost_usd,
            selected_count=record.selected_count + 1,
        )

        return await self._repository.upsert(updated)

    async def record_success(self, project_id: UUID, engine_id: EngineId) -> EngineHealthRecord:
        """Record a successful execution (clears consecutive failures)."""
        record = await self.get_or_create(project_id, engine_id)

        # Successful execution: reset consecutive failures, update EWMA
        updated = EngineHealthRecord(
            project_id=record.project_id,
            engine_id=record.engine_id,
            installed=record.installed,
            version=record.version,
            conformance_ok=record.conformance_ok,
            conformance_at=record.conformance_at,
            auth_ok_at=record.auth_ok_at,
            circuit="closed",  # Close circuit on success
            capacity_state=None,  # Clear capacity state
            resets_at=None,
            probe_next_at=None,
            probe_attempt=0,  # Reset probe attempt
            consecutive_fail=0,  # Reset consecutive failures
            ewma_failure=record.ewma_failure * 0.9,  # Decay EWMA toward 0
            cost_usd_cycle=record.cost_usd_cycle,
            selected_count=record.selected_count,
        )

        return await self._repository.upsert(updated)

    async def list_for_project(self, project_id: UUID) -> tuple[EngineHealthRecord, ...]:
        """List all health records for a project."""
        return await self._repository.list_for_project(project_id)


__all__ = ["EngineHealthService"]
