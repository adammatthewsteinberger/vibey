"""Accepts or waives the VISUAL_DESIGN interstitial (M5 task 5.13).

`vibey visual accept` / `vibey visual waive` are the `VISUAL_DESIGN -> BUILD`
guard from phase-protocols.md: build cannot consume an incomplete or
unreviewed visual plan. The decision is ledgered as VisualDesignAccepted or
VisualDesignWaived before the phase transitions, mirroring how
DesignAcceptanceService ledgers the DESIGN choice gate.
"""

from datetime import datetime
from typing import Protocol
from uuid import UUID

from vibey.application.design import DesignEvent
from vibey.application.design_handler import DesignLedger
from vibey.application.dto import ProjectRecord
from vibey.application.ports import Clock
from vibey.application.visual_handler import VisualInventoryRepository
from vibey.domain.ledger import EventKind, Provenance
from vibey.domain.phase import (
    ALLOWED,
    Phase,
    PhaseState,
    TransitionEvidence,
    TransitionRequest,
    VisualDecision,
    evaluate_transition,
)


class ProjectStore(Protocol):
    async def get(self, project_id: UUID) -> ProjectRecord | None: ...

    async def transition(
        self, project_id: UUID, *, expected: Phase, to: Phase
    ) -> ProjectRecord: ...


class VisualAcceptanceService:
    def __init__(
        self,
        *,
        projects: ProjectStore,
        ledger: DesignLedger,
        inventories: VisualInventoryRepository,
        clock: Clock,
    ) -> None:
        self._projects = projects
        self._ledger = ledger
        self._inventories = inventories
        self._clock = clock

    async def settle(self, project_id: UUID, *, decision: VisualDecision) -> ProjectRecord:
        if decision not in (VisualDecision.ACCEPTED, VisualDecision.WAIVED):
            raise ValueError("decision must be ACCEPTED or WAIVED")
        project = await self._projects.get(project_id)
        if project is None:
            raise ValueError(f"unknown project {project_id}")
        inventory = await self._inventories.load(project_id, project.cycle)
        if inventory is None:
            raise ValueError("no visual inventory exists")
        violations = inventory.is_complete()

        state = PhaseState(project.phase, project.cycle, project.max_cycles, project.updated_at)
        evidence = TransitionEvidence(
            visual_decision=decision, visual_inventory_complete=not violations
        )
        outcome = evaluate_transition(
            state, TransitionRequest(Phase.BUILD, "visual design settled", evidence)
        )
        if outcome != ALLOWED:
            raise ValueError("; ".join(outcome.violations))

        now = self._clock.now()
        event = _settle_event(decision, now)
        await self._ledger.append(project_id, project.cycle, None, None, event)
        return await self._projects.transition(
            project_id, expected=Phase.VISUAL_DESIGN, to=Phase.BUILD
        )


def _settle_event(decision: VisualDecision, now: datetime) -> DesignEvent:
    kind = (
        EventKind.VISUAL_DESIGN_ACCEPTED
        if decision is VisualDecision.ACCEPTED
        else EventKind.VISUAL_DESIGN_WAIVED
    )
    return DesignEvent(kind=kind, provenance=Provenance.TRUSTED, produced_at=now, payload={})
