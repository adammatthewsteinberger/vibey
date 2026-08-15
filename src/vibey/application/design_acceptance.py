"""Accepts a synthesized DESIGN spec using real ledger-derived guard evidence.

`vibey design accept` is also the explicit `DESIGN -> VISUAL_DESIGN` / `DESIGN
-> BUILD` choice gate from phase-protocols.md section 1.5: the caller states
`visual_choice` up front (there is no interactive park/answer round trip yet
-- see the CLI's `--visual/--no-visual` flag), the choice is ledgered as
`VisualDesignOptedIn`/`VisualDesignDeclined` before the phase transitions, and
silence is never treated as consent because the default is DECLINED, not
OPTED_IN.
"""

from datetime import datetime
from typing import Protocol
from uuid import UUID

from vibey.application.design import DesignEvent
from vibey.application.design_handler import DesignLedger
from vibey.application.design_spec import (
    build_design_evidence,
    count_open_blocking_questions,
)
from vibey.application.design_synthesis_handler import DesignSpecRepository
from vibey.application.dto import EnqueueRequest, JobRecord, ProjectRecord
from vibey.application.ports import Clock, JobRepository
from vibey.domain.effort import Effort
from vibey.domain.job import idempotency_key
from vibey.domain.ledger import EventKind, Provenance
from vibey.domain.phase import (
    ALLOWED,
    Phase,
    PhaseState,
    TransitionRequest,
    VisualDecision,
    evaluate_transition,
)


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
        jobs: JobRepository,
        clock: Clock,
    ) -> None:
        self._projects = projects
        self._ledger = ledger
        self._specs = specs
        self._jobs = jobs
        self._clock = clock

    async def accept(
        self, project_id: UUID, *, visual_choice: VisualDecision = VisualDecision.DECLINED
    ) -> ProjectRecord:
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
            visual_decision=visual_choice,
        )
        state = PhaseState(project.phase, project.cycle, project.max_cycles, project.updated_at)
        target = Phase.VISUAL_DESIGN if visual_choice is VisualDecision.OPTED_IN else Phase.BUILD
        outcome = evaluate_transition(state, TransitionRequest(target, "design accepted", evidence))
        if outcome != ALLOWED:
            raise ValueError("; ".join(outcome.violations))

        await self._specs.publish(project_id, project.cycle, spec)
        now = self._clock.now()
        await self._ledger.append(
            project_id, project.cycle, None, None, _choice_event(visual_choice, now)
        )
        accepted = await self._projects.transition(project_id, expected=Phase.DESIGN, to=target)
        if visual_choice is VisualDecision.OPTED_IN:
            await self._enqueue_visual_inventory(accepted)
        return accepted

    async def _enqueue_visual_inventory(self, project: ProjectRecord) -> JobRecord:
        return await self._jobs.enqueue(
            EnqueueRequest(
                project_id=project.project_id,
                cycle=project.cycle,
                phase=Phase.VISUAL_DESIGN,
                kind="visual.inventory",
                idempotency_key=idempotency_key(
                    project.project_id, project.cycle, "visual.inventory", "interactive"
                ),
                requirement={"effort": Effort.HIGH.name.lower()},
            )
        )


def _choice_event(visual_choice: VisualDecision, now: datetime) -> DesignEvent:
    kind = (
        EventKind.VISUAL_DESIGN_OPTED_IN
        if visual_choice is VisualDecision.OPTED_IN
        else EventKind.VISUAL_DESIGN_DECLINED
    )
    return DesignEvent(kind=kind, provenance=Provenance.TRUSTED, produced_at=now, payload={})
