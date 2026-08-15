from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID, uuid4

from tests.application.fakes import FakeJobRepository
from vibey.application.dto import JobRecord
from vibey.application.ports import Clock
from vibey.application.review_demo_handler import (
    DesignSpecReader,
    PhaseLedger,
    ReviewArtifactWriter,
    ReviewDemoHandler,
)
from vibey.application.worker import Failure, Success
from vibey.domain.effort import Effort
from vibey.domain.engine import EngineId
from vibey.domain.job import FailureClass, JobState
from vibey.domain.ledger import EventKind, LedgerEvent, Provenance
from vibey.domain.phase import Phase
from vibey.domain.spec import AcceptanceCriterion, DesignSpec

NOW = datetime(2026, 8, 15, tzinfo=UTC)


class FixedClock(Clock):
    def now(self) -> datetime:
        return NOW


class FakeSpecRepository(DesignSpecReader):
    def __init__(self, spec: DesignSpec | None = None) -> None:
        self.spec = spec

    async def load(self, project_id: UUID, cycle: int) -> DesignSpec | None:
        return self.spec


class FakeReviewLedger(PhaseLedger):
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


class FakeReviewArtifactWriter(ReviewArtifactWriter):
    def __init__(self) -> None:
        self.written: dict[str, str] = {}
        self.executables: list[str] = []

    async def write_review_artifacts(
        self,
        project_id: UUID,
        cycle: int,
        artifacts: Mapping[str, str],
        *,
        executable: Sequence[str] = (),
    ) -> Mapping[str, Path]:
        self.written.update(artifacts)
        self.executables.extend(executable)
        return {k: Path(f"/mock/.vibey/runs/{cycle}/review/{k}") for k in artifacts}


def _make_job(
    *,
    kind: str = "review.demo",
    phase: Phase = Phase.REVIEW,
    work_item_id: str | None = None,
    payload: dict[str, object] | None = None,
) -> JobRecord:
    now = NOW
    return JobRecord(
        id=uuid4(),
        project_id=uuid4(),
        cycle=1,
        phase=phase,
        kind=kind,
        state=JobState.READY,
        priority=0,
        work_item_id=work_item_id,
        payload=payload or {},
        requirement={"effort": Effort.HIGH.name.lower()},
        idempotency_key=f"key-{uuid4()}",
        attempts=0,
        max_attempts=7,
        run_after=now,
        lease_owner=None,
        lease_expires_at=None,
        assigned_engine=None,
        last_error=None,
        created_at=now,
        updated_at=now,
    )


async def test_review_demo_handler_rejects_wrong_kind() -> None:
    handler = ReviewDemoHandler(
        specs=FakeSpecRepository(),
        ledger=FakeReviewLedger(),
        artifacts=FakeReviewArtifactWriter(),
        jobs=FakeJobRepository(),
        clock=FixedClock(),
    )
    outcome = await handler.handle(_make_job(kind="build.verify"))
    assert isinstance(outcome, Failure)
    assert outcome.failure_class == FailureClass.VIBEY


async def test_review_demo_handler_fails_when_spec_missing() -> None:
    handler = ReviewDemoHandler(
        specs=FakeSpecRepository(spec=None),
        ledger=FakeReviewLedger(),
        artifacts=FakeReviewArtifactWriter(),
        jobs=FakeJobRepository(),
        clock=FixedClock(),
    )
    outcome = await handler.handle(_make_job())
    assert isinstance(outcome, Failure)
    assert outcome.failure_class == FailureClass.WORK
    assert "no accepted design spec" in outcome.detail


async def test_review_demo_handler_generates_all_artifacts_and_enqueues_collect() -> None:
    spec = DesignSpec(
        objective="Deliver notes app",
        constraints=(),
        non_goals=(),
        criteria=(
            AcceptanceCriterion(
                criterion_id="AC-1",
                given="a blank notebook",
                when="create note is clicked",
                then="a new note is opened",
                fit="created within 100ms",
            ),
        ),
        nfrs=(),
        walking_skeleton="walking skeleton",
    )
    events = (
        LedgerEvent(
            event_id=uuid4(),
            project_id=uuid4(),
            cycle=1,
            phase=Phase.DESIGN,
            seq=1,
            kind=EventKind.ASSUMPTION_STATED,
            engine_id=EngineId.CLAUDELOOP,
            job_id=uuid4(),
            causation_id=None,
            correlation_id=uuid4(),
            provenance=Provenance.TRUSTED,
            produced_at=NOW,
            payload={"assumption_id": "a-1", "text": "Local sqlite storage"},
            digest="abc",
        ),
    )
    specs = FakeSpecRepository(spec=spec)
    ledger = FakeReviewLedger(events=events)
    artifacts = FakeReviewArtifactWriter()
    jobs = FakeJobRepository()

    handler = ReviewDemoHandler(
        specs=specs,
        ledger=ledger,
        artifacts=artifacts,
        jobs=jobs,
        clock=FixedClock(),
    )

    job = _make_job(payload={"test_report": "<xml>passed</xml>", "coverage": '{"total": 100}'})
    outcome = await handler.handle(job)

    assert isinstance(outcome, Success)
    assert "DEMO.md" in artifacts.written
    assert "run-it.sh" in artifacts.written
    assert "walkthrough.md" in artifacts.written
    assert "deltas.md" in artifacts.written
    assert "evidence/test-report.xml" in artifacts.written
    assert "evidence/coverage.json" in artifacts.written

    # Deltas contains the assumption from ledger
    assert "a-1" in artifacts.written["deltas.md"]
    assert "Local sqlite storage" in artifacts.written["deltas.md"]

    # run-it.sh marked executable
    assert "run-it.sh" in artifacts.executables

    # ARTIFACT_PRODUCED ledger event recorded
    assert any(kind == EventKind.ARTIFACT_PRODUCED for kind, _ in ledger.appended)

    # review.collect job enqueued
    enqueued = list(jobs._jobs.values())
    collect_job = next((j for j in enqueued if j.kind == "review.collect"), None)
    assert collect_job is not None
    assert collect_job.phase == Phase.REVIEW
    assert collect_job.requirement.get("effort") == "high"
