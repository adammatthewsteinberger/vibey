from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID, uuid4

from tests.application.fakes import FakeJobRepository
from vibey.application.dto import JobRecord, ProjectRecord
from vibey.application.ports import Clock
from vibey.application.review_demo_handler import ReviewSpecRepository
from vibey.application.review_triage_handler import ReviewTriageHandler, ReviewTriageLedger
from vibey.application.worker import Success
from vibey.domain.effort import Effort
from vibey.domain.engine import EngineId
from vibey.domain.job import JobState
from vibey.domain.ledger import EventKind, LedgerEvent, Provenance
from vibey.domain.phase import Phase
from vibey.domain.spec import AcceptanceCriterion, DesignSpec

NOW = datetime(2026, 8, 15, tzinfo=UTC)


class FixedClock(Clock):
    def now(self) -> datetime:
        return NOW


class FakeReviewTriageLedger(ReviewTriageLedger):
    def __init__(self, events: Sequence[LedgerEvent] = ()) -> None:
        self._events: list[LedgerEvent] = list(events)
        self.appended: list[tuple[EventKind, Mapping[str, object]]] = []

    async def all_for_project(self, project_id: UUID) -> tuple[LedgerEvent, ...]:
        return tuple(self._events)

    async def append_event(
        self,
        project_id: UUID,
        cycle: int,
        job_id: UUID,
        kind: EventKind,
        payload: Mapping[str, object],
    ) -> None:
        self.appended.append((kind, payload))


class FakeSpecRepo(ReviewSpecRepository):
    def __init__(self, spec: DesignSpec | None = None) -> None:
        self.spec = spec

    async def load(self, project_id: UUID, cycle: int) -> DesignSpec | None:
        return self.spec


class FakeProjectRepo:
    def __init__(self, project: ProjectRecord) -> None:
        self.project = project
        self.transitions: list[tuple[Phase, Phase, int | None]] = []

    async def get(self, project_id: UUID) -> ProjectRecord | None:
        return self.project

    async def transition(
        self,
        project_id: UUID,
        *,
        expected: Phase,
        to: Phase,
        cycle: int | None = None,
    ) -> ProjectRecord:
        self.transitions.append((expected, to, cycle))
        self.project = ProjectRecord(
            project_id=self.project.project_id,
            name=self.project.name,
            repo_path=self.project.repo_path,
            phase=to,
            cycle=cycle if cycle is not None else self.project.cycle,
            max_cycles=self.project.max_cycles,
            config=self.project.config,
            created_at=self.project.created_at,
            updated_at=NOW,
        )
        return self.project


def _make_spec() -> DesignSpec:
    return DesignSpec(
        objective="Notes app",
        constraints=(),
        non_goals=(),
        criteria=(
            AcceptanceCriterion(
                criterion_id="AC-1",
                given="blank",
                when="save",
                then="saved",
                fit="row count 1",
            ),
        ),
        nfrs=(),
        walking_skeleton="skeleton",
    )


def _make_event(
    kind: EventKind,
    payload: dict[str, object],
    *,
    seq: int = 1,
) -> LedgerEvent:
    return LedgerEvent(
        event_id=uuid4(),
        project_id=uuid4(),
        cycle=1,
        phase=Phase.REVIEW,
        seq=seq,
        kind=kind,
        engine_id=EngineId.CLAUDELOOP,
        job_id=uuid4(),
        causation_id=None,
        correlation_id=uuid4(),
        provenance=Provenance.TRUSTED,
        produced_at=NOW,
        payload=payload,
        digest="abc",
    )


def _make_job(
    *,
    project_id: UUID,
    cycle: int = 1,
    kind: str = "review.triage",
    payload: dict[str, object] | None = None,
) -> JobRecord:
    return JobRecord(
        id=uuid4(),
        project_id=project_id,
        cycle=cycle,
        phase=Phase.REVIEW,
        kind=kind,
        state=JobState.READY,
        priority=0,
        work_item_id=None,
        payload=payload or {},
        requirement={"effort": Effort.HIGH.name.lower()},
        idempotency_key=f"key-{uuid4()}",
        attempts=0,
        max_attempts=7,
        run_after=NOW,
        lease_owner=None,
        lease_expires_at=None,
        assigned_engine=None,
        last_error=None,
        created_at=NOW,
        updated_at=NOW,
    )


async def test_review_loopback_fast_build_increments_cycle() -> None:
    project_id = uuid4()
    proj = ProjectRecord(
        project_id=project_id,
        name="test-proj",
        repo_path=Path("/tmp/repo"),
        phase=Phase.REVIEW,
        cycle=1,
        max_cycles=5,
        config={},
        created_at=NOW,
        updated_at=NOW,
    )
    events = (
        _make_event(
            EventKind.FINDING_RAISED,
            {
                "finding_id": "f-clear",
                "text": "Trim note title whitespace on save action.",
            },
            seq=1,
        ),
    )
    jobs = FakeJobRepository()
    ledger = FakeReviewTriageLedger(events=events)
    projects = FakeProjectRepo(proj)
    handler = ReviewTriageHandler(
        ledger=ledger,
        specs=FakeSpecRepo(spec=_make_spec()),
        jobs=jobs,
        clock=FixedClock(),
        projects=projects,
    )

    job = _make_job(project_id=project_id, cycle=1)
    outcome = await handler.handle(job)
    assert isinstance(outcome, Success)
    assert outcome.result.get("next_phase") == Phase.BUILD.value

    # Project was transitioned to BUILD with cycle 2
    assert len(projects.transitions) == 1
    assert projects.transitions[0] == (Phase.REVIEW, Phase.BUILD, 2)
    assert projects.project.cycle == 2
    assert projects.project.phase == Phase.BUILD

    # Enqueued build job is for cycle 2
    enqueued = list(jobs._jobs.values())
    build_job = next(j for j in enqueued if j.kind == "build.plan")
    assert build_job.cycle == 2


async def test_review_loopback_strict_mode_routes_to_design() -> None:
    project_id = uuid4()
    proj = ProjectRecord(
        project_id=project_id,
        name="test-proj",
        repo_path=Path("/tmp/repo"),
        phase=Phase.REVIEW,
        cycle=1,
        max_cycles=5,
        config={"strict_loopback": True},
        created_at=NOW,
        updated_at=NOW,
    )
    events = (
        _make_event(
            EventKind.FINDING_RAISED,
            {
                "finding_id": "f-clear",
                "text": "Trim note title whitespace on save action.",
            },
            seq=1,
        ),
    )
    jobs = FakeJobRepository()
    ledger = FakeReviewTriageLedger(events=events)
    projects = FakeProjectRepo(proj)
    handler = ReviewTriageHandler(
        ledger=ledger,
        specs=FakeSpecRepo(spec=_make_spec()),
        jobs=jobs,
        clock=FixedClock(),
        projects=projects,
    )

    job = _make_job(project_id=project_id, cycle=1, payload={"strict_loopback": True})
    outcome = await handler.handle(job)
    assert isinstance(outcome, Success)
    assert outcome.result.get("next_phase") == Phase.DESIGN.value

    # Project transitioned to DESIGN with cycle 2
    assert projects.transitions[0] == (Phase.REVIEW, Phase.DESIGN, 2)
    assert projects.project.cycle == 2

    # Enqueued design job is for cycle 2
    enqueued = list(jobs._jobs.values())
    design_job = next(j for j in enqueued if j.kind == "design.interview")
    assert design_job.cycle == 2
