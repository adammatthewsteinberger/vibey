"""Accepts a synthesized DESIGN spec using real ledger-derived guard evidence."""

from typing import Protocol
from uuid import UUID

from vibey.application.design_handler import DesignLedger
from vibey.application.design_spec import (
    build_design_evidence,
    count_open_blocking_questions,
)
from vibey.application.design_synthesis_handler import DesignSpecRepository
from vibey.application.dto import ProjectRecord
from vibey.domain.phase import ALLOWED, Phase, PhaseState, TransitionRequest, evaluate_transition


class ProjectStore(Protocol):
    async def get(self, project_id: UUID) -> ProjectRecord | None: ...

    async def transition(
        self, project_id: UUID, *, expected: Phase, to: Phase
    ) -> ProjectRecord: ...


class DesignAcceptanceService:
    def __init__(
        self,
        *,
        projects: ProjectStore,
        ledger: DesignLedger,
        specs: DesignSpecRepository,
    ) -> None:
        self._projects = projects
        self._ledger = ledger
        self._specs = specs

    async def accept(self, project_id: UUID) -> ProjectRecord:
        project = await self._projects.get(project_id)
        if project is None:
            raise ValueError(f"unknown project {project_id}")
        spec = await self._specs.load(project_id, project.cycle)
        if spec is None:
            raise ValueError("no synthesized design spec exists")
        events = await self._ledger.all_for_project(project_id)
        evidence = build_design_evidence(
            spec,
            open_blocking_questions=count_open_blocking_questions(events),
            accepted=True,
        )
        state = PhaseState(project.phase, project.cycle, project.max_cycles, project.updated_at)
        outcome = evaluate_transition(
            state, TransitionRequest(Phase.BUILD, "design accepted", evidence)
        )
        if outcome != ALLOWED:
            raise ValueError("; ".join(outcome.violations))
        await self._specs.publish(project_id, project.cycle, spec)
        return await self._projects.transition(project_id, expected=Phase.DESIGN, to=Phase.BUILD)
