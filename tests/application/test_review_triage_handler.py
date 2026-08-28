# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://hire.adam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from uuid import UUID, uuid4

from tests.application.fakes import FakeJobRepository
from vibey.application.dto import JobRecord
from vibey.application.ports import Clock
from vibey.application.review_demo_handler import DesignSpecReader
from vibey.application.review_triage_handler import PhaseLedger, ReviewTriageHandler
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


class FakeReviewTriageLedger(PhaseLedger):
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


class FakeSpecRepo(DesignSpecReader):
    def __init__(self, spec: DesignSpec | None = None) -> None:
        self.spec = spec

    async def load(self, project_id: UUID, cycle: int) -> DesignSpec | None:
        return self.spec


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
    kind: str = "review.triage",
    phase: Phase = Phase.REVIEW,
) -> JobRecord:
    return JobRecord(
        id=uuid4(),
        project_id=uuid4(),
        cycle=1,
        phase=phase,
        kind=kind,
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


async def test_review_triage_handler_rejects_wrong_kind() -> None:
    handler = ReviewTriageHandler(
        ledger=FakeReviewTriageLedger(),
        specs=FakeSpecRepo(),
        jobs=FakeJobRepository(),
        clock=FixedClock(),
    )
    outcome = await handler.handle(_make_job(kind="review.demo"))
    assert isinstance(outcome, Failure)
    assert outcome.failure_class == FailureClass.VIBEY


async def test_review_triage_handler_no_findings_routes_to_done_and_deployment_gate() -> None:
    jobs = FakeJobRepository()
    ledger = FakeReviewTriageLedger()
    handler = ReviewTriageHandler(
        ledger=ledger,
        specs=FakeSpecRepo(spec=_make_spec()),
        jobs=jobs,
        clock=FixedClock(),
    )
    outcome = await handler.handle(_make_job())
    assert isinstance(outcome, Success)
    assert outcome.result.get("next_phase") == Phase.DONE.value

    enqueued = list(jobs._jobs.values())
    gate_job = next((j for j in enqueued if j.kind == "review.deployment_choice"), None)
    assert gate_job is not None
    # A completed review (no findings, next_phase DONE) must not also queue a
    # build -- that would restart work the review just closed out.
    assert not any(j.kind == "build.plan" for j in enqueued)


async def test_review_triage_handler_clear_findings_routes_to_build_fast_loop() -> None:
    events = (
        _make_event(
            EventKind.FINDING_RAISED,
            {
                "finding_id": "f-1",
                "text": "Trim leading and trailing whitespace on note title during save.",
            },
            seq=1,
        ),
    )
    jobs = FakeJobRepository()
    ledger = FakeReviewTriageLedger(events=events)
    handler = ReviewTriageHandler(
        ledger=ledger,
        specs=FakeSpecRepo(spec=_make_spec()),
        jobs=jobs,
        clock=FixedClock(),
    )
    outcome = await handler.handle(_make_job())
    assert isinstance(outcome, Success)
    assert outcome.result.get("next_phase") == Phase.BUILD.value

    enqueued = list(jobs._jobs.values())
    build_job = next((j for j in enqueued if j.kind == "build.plan"), None)
    assert build_job is not None


async def test_review_triage_handler_unclear_or_critical_sets_max_effort() -> None:
    events = (
        _make_event(
            EventKind.FINDING_RAISED,
            {
                "finding_id": "f-sec",
                "text": (
                    "Security vulnerability in auth session cookie parsing. "
                    "Maybe rethink the whole architecture."
                ),
            },
            seq=1,
        ),
    )
    jobs = FakeJobRepository()
    ledger = FakeReviewTriageLedger(events=events)
    handler = ReviewTriageHandler(
        ledger=ledger,
        specs=FakeSpecRepo(spec=_make_spec()),
        jobs=jobs,
        clock=FixedClock(),
    )
    outcome = await handler.handle(_make_job())
    assert isinstance(outcome, Success)
    assert outcome.result.get("next_phase") == Phase.DESIGN.value
    assert outcome.result.get("has_critical") is True

    enqueued = list(jobs._jobs.values())
    design_job = next((j for j in enqueued if j.kind == "design.interview"), None)
    assert design_job is not None
    assert design_job.requirement.get("effort") == Effort.MAX.name.lower()


class FakeProjectTransitioner:
    def __init__(self) -> None:
        self.transitions: list[tuple[UUID, Phase, Phase, int]] = []

    async def transition(self, project_id: UUID, *, expected: Phase, to: Phase, cycle: int) -> None:
        self.transitions.append((project_id, expected, to, cycle))


async def test_review_triage_handler_transitions_project_when_projects_provided() -> None:
    """When a projects transitioner is passed, the handler calls transition."""
    events = (
        _make_event(
            EventKind.FINDING_RAISED,
            {
                "finding_id": "f-1",
                "text": "Trim leading and trailing whitespace on note title during save.",
            },
            seq=1,
        ),
    )
    jobs = FakeJobRepository()
    ledger = FakeReviewTriageLedger(events=events)
    projects = FakeProjectTransitioner()
    handler = ReviewTriageHandler(
        ledger=ledger,
        specs=FakeSpecRepo(spec=_make_spec()),
        jobs=jobs,
        clock=FixedClock(),
        projects=projects,
    )
    job = _make_job()
    outcome = await handler.handle(job)
    assert isinstance(outcome, Success)
    assert outcome.result.get("next_phase") == Phase.BUILD.value
    assert len(projects.transitions) == 1
    assert projects.transitions[0][2] is Phase.BUILD
    assert projects.transitions[0][3] == 2


async def test_review_triage_handler_skips_transition_without_transition_method() -> None:
    """When projects is a plain object without transition, no error occurs."""
    events = (
        _make_event(
            EventKind.FINDING_RAISED,
            {"finding_id": "f-1", "text": "Minor issue."},
            seq=1,
        ),
    )
    jobs = FakeJobRepository()
    handler = ReviewTriageHandler(
        ledger=FakeReviewTriageLedger(events=events),
        specs=FakeSpecRepo(spec=_make_spec()),
        jobs=jobs,
        clock=FixedClock(),
        projects=object(),
    )
    outcome = await handler.handle(_make_job())
    assert isinstance(outcome, Success)


class FakeSpecStore(FakeSpecRepo):
    def __init__(self, spec: DesignSpec | None = None) -> None:
        super().__init__(spec)
        self.saved: list[tuple[int, DesignSpec]] = []

    async def save(self, project_id: UUID, cycle: int, spec: DesignSpec) -> None:
        self.saved.append((cycle, spec))

    async def publish(self, project_id: UUID, cycle: int, spec: DesignSpec) -> None:
        raise NotImplementedError


async def test_fast_loopback_carries_the_spec_to_the_next_cycle() -> None:
    """build.plan decomposes at cycle+1, but the spec store is cycle-scoped
    -- the triage handler must copy the accepted spec forward explicitly."""
    events = (
        _make_event(
            EventKind.FINDING_RAISED,
            {
                "finding_id": "f-1",
                "text": "Trim leading and trailing whitespace on note title during save.",
            },
            seq=1,
        ),
    )
    spec = _make_spec()
    store = FakeSpecStore(spec=spec)
    jobs = FakeJobRepository()
    handler = ReviewTriageHandler(
        ledger=FakeReviewTriageLedger(events=events),
        specs=FakeSpecRepo(spec=spec),
        jobs=jobs,
        clock=FixedClock(),
        spec_store=store,
    )

    outcome = await handler.handle(_make_job())

    assert isinstance(outcome, Success)
    assert outcome.result.get("next_phase") == Phase.BUILD.value
    assert store.saved == [(2, spec)]


async def test_fast_loopback_without_a_loaded_spec_skips_the_carry() -> None:
    events = (
        _make_event(
            EventKind.FINDING_RAISED,
            {
                "finding_id": "f-1",
                "text": "Trim leading and trailing whitespace on note title during save.",
            },
            seq=1,
        ),
    )
    store = FakeSpecStore(spec=None)
    handler = ReviewTriageHandler(
        ledger=FakeReviewTriageLedger(events=events),
        specs=FakeSpecRepo(spec=None),
        jobs=FakeJobRepository(),
        clock=FixedClock(),
        spec_store=store,
    )

    outcome = await handler.handle(_make_job())

    assert isinstance(outcome, Success)
    assert store.saved == []
