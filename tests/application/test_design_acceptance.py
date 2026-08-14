from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID, uuid4

import pytest

from vibey.application.design import DesignEvent
from vibey.application.design_acceptance import DesignAcceptanceService
from vibey.application.dto import ProjectRecord
from vibey.domain.ledger import EventKind, Provenance
from vibey.domain.phase import Phase
from vibey.domain.spec import AcceptanceCriterion, DesignSpec


def spec() -> DesignSpec:
    return DesignSpec(
        "Ship",
        (),
        (),
        (AcceptanceCriterion("AC-1", "input", "run", "output", "test passes"),),
        (),
        "one path",
    )


class Projects:
    def __init__(self, project: ProjectRecord | None) -> None:
        self.project = project

    async def get(self, project_id: UUID) -> ProjectRecord | None:
        return self.project

    async def transition(self, project_id: UUID, *, expected: Phase, to: Phase) -> ProjectRecord:
        assert self.project is not None
        assert self.project.phase is expected
        from dataclasses import replace

        self.project = replace(self.project, phase=to)
        return self.project


class Ledger:
    def __init__(self, events: tuple[DesignEvent, ...] = ()) -> None:
        self.events = events

    async def all_for_project(self, project_id: UUID) -> tuple[DesignEvent, ...]:
        return self.events


class Specs:
    def __init__(self, value: DesignSpec | None) -> None:
        self.value = value
        self.published = False

    async def save(self, project_id: UUID, cycle: int, value: DesignSpec) -> None:
        self.value = value

    async def load(self, project_id: UUID, cycle: int) -> DesignSpec | None:
        return self.value

    async def publish(self, project_id: UUID, cycle: int, value: DesignSpec) -> None:
        self.published = True


def project() -> ProjectRecord:
    now = datetime.now(UTC)
    return ProjectRecord(uuid4(), "demo", Path("."), Phase.DESIGN, 1, 10, {}, now, now)


async def test_accept_publishes_and_transitions_to_build() -> None:
    projects = Projects(project())
    specs = Specs(spec())
    accepted = await DesignAcceptanceService(
        projects=projects, ledger=Ledger(), specs=specs
    ).accept(
        projects.project.project_id  # type: ignore[union-attr]
    )
    assert accepted.phase is Phase.BUILD
    assert specs.published


async def test_accept_rejects_missing_project_or_spec() -> None:
    with pytest.raises(ValueError, match="unknown project"):
        await DesignAcceptanceService(
            projects=Projects(None), ledger=Ledger(), specs=Specs(spec())
        ).accept(uuid4())
    value = project()
    with pytest.raises(ValueError, match="no synthesized"):
        await DesignAcceptanceService(
            projects=Projects(value), ledger=Ledger(), specs=Specs(None)
        ).accept(value.project_id)


async def test_accept_rejects_open_blocking_question() -> None:
    value = project()
    event = DesignEvent(
        EventKind.QUESTION_ASKED,
        Provenance.AGENT,
        datetime.now(UTC),
        {"item_id": "q-1", "blocking": True},
    )
    with pytest.raises(ValueError, match="blocking question"):
        await DesignAcceptanceService(
            projects=Projects(value), ledger=Ledger((event,)), specs=Specs(spec())
        ).accept(value.project_id)
