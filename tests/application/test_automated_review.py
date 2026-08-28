# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://hire.adam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID, uuid4

from tests.application.fakes import FakeJobRepository
from vibey.application.dto import JobRecord
from vibey.application.ports import Clock
from vibey.application.review_demo_handler import (
    AutomatedFinding,
    AutomatedReviewRunner,
    DesignSpecReader,
    PhaseLedger,
    ReviewArtifactWriter,
    ReviewDemoHandler,
)
from vibey.application.worker import Success
from vibey.domain.effort import Effort
from vibey.domain.job import JobState
from vibey.domain.ledger import EventKind, LedgerEvent
from vibey.domain.phase import Phase
from vibey.domain.review import Ambiguity, Severity
from vibey.domain.spec import AcceptanceCriterion, DesignSpec

NOW = datetime(2026, 8, 15, tzinfo=UTC)


class FixedClock(Clock):
    def now(self) -> datetime:
        return NOW


class FakeSpecRepo(DesignSpecReader):
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
        # Also maintain in-memory events so subsequent reads reflect new appends
        self._events.append(
            LedgerEvent(
                event_id=uuid4(),
                project_id=project_id,
                cycle=cycle,
                phase=Phase.REVIEW,
                seq=len(self._events) + 1,
                kind=kind,
                engine_id=None,
                job_id=job_id,
                causation_id=None,
                correlation_id=uuid4(),
                provenance="trusted",  # type: ignore[arg-type]
                produced_at=NOW,
                payload=dict(payload),
                digest="abc",
            )
        )


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


class FakeAutomatedReviewRunner(AutomatedReviewRunner):
    def __init__(self, findings: Sequence[AutomatedFinding] = ()) -> None:
        self.findings = tuple(findings)

    async def run_automated_reviews(
        self, project_id: UUID, cycle: int
    ) -> tuple[AutomatedFinding, ...]:
        return self.findings


def _make_job() -> JobRecord:
    return JobRecord(
        id=uuid4(),
        project_id=uuid4(),
        cycle=1,
        phase=Phase.REVIEW,
        kind="review.demo",
        state=JobState.READY,
        priority=0,
        work_item_id=None,
        payload={},
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


async def test_review_demo_runs_automated_reviews_and_pre_triages_findings() -> None:
    spec = DesignSpec(
        objective="Deliver notes app",
        constraints=(),
        non_goals=(),
        criteria=(
            AcceptanceCriterion(
                criterion_id="AC-1",
                given="blank note",
                when="create clicked",
                then="note created",
                fit="under 100ms",
            ),
        ),
        nfrs=(),
        walking_skeleton="walking skeleton",
    )
    automated_findings = (
        AutomatedFinding(
            category="security",
            text="Insecure temp file permissions in storage module.",
            severity=Severity.HIGH,
            ambiguity=Ambiguity.CLEAR,
        ),
        AutomatedFinding(
            category="code_review",
            text="Unused variable in notes repository.",
            severity=Severity.LOW,
            ambiguity=Ambiguity.CLEAR,
        ),
    )
    specs = FakeSpecRepo(spec=spec)
    ledger = FakeReviewLedger()
    artifacts = FakeReviewArtifactWriter()
    jobs = FakeJobRepository()
    automated_runner = FakeAutomatedReviewRunner(findings=automated_findings)

    handler = ReviewDemoHandler(
        specs=specs,
        ledger=ledger,
        artifacts=artifacts,
        jobs=jobs,
        clock=FixedClock(),
        automated_reviewer=automated_runner,
    )

    outcome = await handler.handle(_make_job())
    assert isinstance(outcome, Success)

    # Verify FindingRaised events were emitted for both automated findings
    finding_events = [p for k, p in ledger.appended if k == EventKind.FINDING_RAISED]
    assert len(finding_events) == 2
    sec_finding = next(f for f in finding_events if f.get("category") == "security")
    assert sec_finding["severity"] == Severity.HIGH.value
    assert sec_finding["ambiguity"] == Ambiguity.CLEAR.value
    assert "Insecure temp file permissions" in str(sec_finding["text"])

    code_finding = next(f for f in finding_events if f.get("category") == "code_review")
    assert code_finding["severity"] == Severity.LOW.value
    assert code_finding["ambiguity"] == Ambiguity.CLEAR.value
    assert "Unused variable" in str(code_finding["text"])

    # Verify deltas.md contains the automated pre-triaged findings before human review
    deltas_md = artifacts.written["deltas.md"]
    assert "Insecure temp file permissions" in deltas_md
    assert "Unused variable" in deltas_md
    assert "high" in deltas_md.lower()
    assert "clear" in deltas_md.lower()
