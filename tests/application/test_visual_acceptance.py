# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID, uuid4

import pytest

from tests.application.fakes import FakeJobRepository
from vibey.application.design import DesignEvent
from vibey.application.dto import ProjectRecord
from vibey.application.visual_acceptance import VisualAcceptanceService
from vibey.domain.ledger import EventKind, Provenance
from vibey.domain.phase import Phase, VisualDecision
from vibey.domain.visual import (
    MediaManifestEntry,
    MediaModality,
    ScreenSurface,
    SurfaceAction,
    VisualInventory,
)


def complete_inventory() -> VisualInventory:
    return VisualInventory(
        surfaces=(
            ScreenSurface(
                screen_id="home",
                name="Home",
                action=SurfaceAction.CREATE,
                responsive_states=("mobile",),
                accessibility_requirements=("keyboard navigable",),
                media_manifest=(MediaManifestEntry("hero", MediaModality.IMAGE, "a hero image"),),
            ),
        )
    )


class Projects:
    def __init__(self, project: ProjectRecord | None) -> None:
        self.project = project

    async def get(self, project_id: UUID) -> ProjectRecord | None:
        return self.project

    async def transition(self, project_id: UUID, *, expected: Phase, to: Phase) -> ProjectRecord:
        assert self.project is not None
        assert self.project.phase is expected
        self.project = replace(self.project, phase=to)
        return self.project


class Ledger:
    def __init__(self) -> None:
        self.appended: list[DesignEvent] = []

    async def all_for_project(self, project_id: UUID) -> tuple[DesignEvent, ...]:
        return ()

    async def append(self, project_id, cycle, job_id, engine_id, event):  # type: ignore[no-untyped-def]
        self.appended.append(event)


class Inventories:
    def __init__(self, value: VisualInventory | None) -> None:
        self.value = value

    async def save(self, project_id: UUID, cycle: int, value: VisualInventory) -> None:
        self.value = value

    async def load(self, project_id: UUID, cycle: int) -> VisualInventory | None:
        return self.value

    async def publish(self, project_id: UUID, cycle: int, value: VisualInventory) -> None:
        pass


class FixedClock:
    def now(self) -> datetime:
        return datetime(2026, 8, 14, tzinfo=UTC)


def project() -> ProjectRecord:
    now = datetime.now(UTC)
    return ProjectRecord(uuid4(), "demo", Path("."), Phase.VISUAL_DESIGN, 1, 10, {}, now, now)


def _service(
    *,
    projects: Projects,
    ledger: Ledger,
    inventories: Inventories,
    jobs: FakeJobRepository | None = None,
) -> VisualAcceptanceService:
    return VisualAcceptanceService(
        projects=projects,
        ledger=ledger,
        inventories=inventories,
        jobs=jobs or FakeJobRepository(),
        clock=FixedClock(),
    )


async def test_accept_transitions_to_build_with_a_complete_inventory() -> None:
    projects = Projects(project())
    ledger = Ledger()
    jobs = FakeJobRepository()
    settled = await _service(
        projects=projects, ledger=ledger, inventories=Inventories(complete_inventory()), jobs=jobs
    ).settle(projects.project.project_id, decision=VisualDecision.ACCEPTED)  # type: ignore[union-attr]

    assert settled.phase is Phase.BUILD
    assert [e.kind for e in ledger.appended] == [EventKind.VISUAL_DESIGN_ACCEPTED]
    assert ledger.appended[0].provenance is Provenance.TRUSTED
    enqueued = await jobs.claim(settled.project_id, owner="test", lease=timedelta(seconds=5))
    assert enqueued is not None
    assert enqueued.kind == "build.decompose"


async def test_waive_transitions_to_build_with_a_complete_inventory() -> None:
    projects = Projects(project())
    ledger = Ledger()
    settled = await _service(
        projects=projects, ledger=ledger, inventories=Inventories(complete_inventory())
    ).settle(projects.project.project_id, decision=VisualDecision.WAIVED)  # type: ignore[union-attr]

    assert settled.phase is Phase.BUILD
    assert [e.kind for e in ledger.appended] == [EventKind.VISUAL_DESIGN_WAIVED]


async def test_settle_rejects_an_incomplete_inventory() -> None:
    projects = Projects(project())
    ledger = Ledger()
    with pytest.raises(ValueError, match="complete screen/state inventory"):
        await _service(
            projects=projects, ledger=ledger, inventories=Inventories(VisualInventory(()))
        ).settle(projects.project.project_id, decision=VisualDecision.ACCEPTED)  # type: ignore[union-attr]


async def test_settle_rejects_missing_project_or_inventory() -> None:
    with pytest.raises(ValueError, match="unknown project"):
        await _service(
            projects=Projects(None), ledger=Ledger(), inventories=Inventories(None)
        ).settle(uuid4(), decision=VisualDecision.ACCEPTED)

    value = project()
    with pytest.raises(ValueError, match="no visual inventory"):
        await _service(
            projects=Projects(value), ledger=Ledger(), inventories=Inventories(None)
        ).settle(value.project_id, decision=VisualDecision.ACCEPTED)


async def test_settle_rejects_a_non_terminal_decision() -> None:
    value = project()
    with pytest.raises(ValueError, match="ACCEPTED or WAIVED"):
        await _service(
            projects=Projects(value),
            ledger=Ledger(),
            inventories=Inventories(complete_inventory()),
        ).settle(value.project_id, decision=VisualDecision.OPTED_IN)
