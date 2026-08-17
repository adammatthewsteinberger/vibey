"""Rotation handoff: handles capacity rejections and wind-downs, producing
no-loss handoff briefs and selecting the next engine.

On wind-down (exit code 75): settle work item as Success (not Failure), build
handoff brief, select next engine. Bound livelock at 3 wind-downs per item.
"""

from dataclasses import dataclass
from uuid import UUID

from vibey.application.engine_selector import EngineSelector
from vibey.domain.capacity import CapacityState
from vibey.domain.engine import EngineId, JobRequirement
from vibey.domain.errors import VibeyError


class TooManyWindDowns(VibeyError):
    """Raised when a work item has rotated 3+ times due to wind-down."""

    pass


@dataclass(frozen=True, slots=True)
class HandoffDecision:
    """Result of a wind-down or capacity rejection."""

    next_engine: EngineId
    reason: str
    handoff_brief: dict[str, object]
    wind_down_count: int


class RotationHandoffService:
    """Handles engine rotation on capacity rejection or wind-down."""

    MAX_WIND_DOWNS = 3

    def __init__(self, engine_selector: EngineSelector) -> None:
        self._selector = engine_selector

    async def handle_wind_down(
        self,
        project_id: UUID,
        work_item_id: str,
        current_engine: EngineId,
        requirement: JobRequirement,
        wind_down_count: int,
        ledger_snapshot: dict[str, object],
    ) -> HandoffDecision:
        """Handle wind-down (exit code 75): select next engine, build brief.

        Wind-down is NOT a failure - it means the engine exhausted its capacity
        window gracefully and is handing off to another engine. The work item
        should be marked as Success (not Failure) to avoid burning the escalation
        ladder.

        Args:
            project_id: Project UUID
            work_item_id: Work item being rotated
            current_engine: Engine that is winding down
            requirement: Job requirements (updated to exclude current engine)
            wind_down_count: How many times this item has already rotated
            ledger_snapshot: Current ledger state for building handoff brief

        Returns:
            HandoffDecision with next engine and brief

        Raises:
            TooManyWindDowns: If wind_down_count >= MAX_WIND_DOWNS
        """
        if wind_down_count >= self.MAX_WIND_DOWNS:
            raise TooManyWindDowns(
                f"Work item {work_item_id} has rotated {wind_down_count} times "
                f"(max {self.MAX_WIND_DOWNS}). Needs human attention."
            )

        # Update requirement to exclude the engine that wound down
        updated_requirement = JobRequirement(
            effort=requirement.effort,
            capabilities=requirement.capabilities,
            excluded=requirement.excluded | {current_engine},
        )

        next_engine, _ = await self._selector.select_engine(
            project_id=project_id,
            requirement=updated_requirement,
        )

        # Build handoff brief (simplified for now - real implementation would
        # run the full no-loss gate from handoff_orchestration.py)
        brief = {
            "reason": "wind_down",
            "from_engine": current_engine.value,
            "to_engine": next_engine.value,
            "work_item_id": work_item_id,
            "wind_down_count": wind_down_count + 1,
            "ledger_snapshot": ledger_snapshot,
            "remaining_work": ledger_snapshot.get("remaining_work", []),
        }

        return HandoffDecision(
            next_engine=next_engine,
            reason=f"Wind-down from {current_engine.value}",
            handoff_brief=brief,
            wind_down_count=wind_down_count + 1,
        )

    async def handle_capacity_rejection(
        self,
        project_id: UUID,
        current_engine: EngineId,
        capacity_state: CapacityState,
        requirement: JobRequirement,
        ledger_snapshot: dict[str, object],
    ) -> HandoffDecision:
        """Handle capacity rejection: select next engine excluding the one that failed.

        Args:
            project_id: Project UUID
            current_engine: Engine that rejected due to capacity
            capacity_state: The capacity state (for logging/metrics)
            requirement: Job requirements
            ledger_snapshot: Current ledger state for building brief

        Returns:
            HandoffDecision with next engine and brief
        """
        # Update requirement to exclude the engine that had capacity issues
        updated_requirement = JobRequirement(
            effort=requirement.effort,
            capabilities=requirement.capabilities,
            excluded=requirement.excluded | {current_engine},
        )

        # Select next engine
        next_engine, selection = await self._selector.select_engine(
            project_id=project_id,
            requirement=updated_requirement,
        )

        # Build handoff brief
        brief = {
            "reason": "capacity_rejection",
            "from_engine": current_engine.value,
            "to_engine": next_engine.value,
            "capacity_state": str(type(capacity_state).__name__),
            "ledger_snapshot": ledger_snapshot,
            "remaining_work": ledger_snapshot.get("remaining_work", []),
        }

        return HandoffDecision(
            next_engine=next_engine,
            reason=f"Capacity rejection from {current_engine.value}",
            handoff_brief=brief,
            wind_down_count=0,  # Capacity rejections don't count toward wind-down limit
        )


__all__ = ["RotationHandoffService", "HandoffDecision", "TooManyWindDowns"]
