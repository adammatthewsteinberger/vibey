# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from uuid import UUID, uuid4

from tests.application.fakes import FakeJobRepository
from vibey.application.dto import HumanGateRecord, HumanGateRequest, JobRecord
from vibey.application.ports import Clock, HumanGateRepository
from vibey.application.review_collect_handler import PhaseLedger, ReviewCollectHandler
from vibey.application.worker import Failure, Park, Success
from vibey.domain.effort import Effort
from vibey.domain.engine import EngineId
from vibey.domain.job import FailureClass, JobState
from vibey.domain.ledger import EventKind, LedgerEvent, Provenance
from vibey.domain.phase import Phase

NOW = datetime(2026, 8, 15, tzinfo=UTC)


class FixedClock(Clock):
    def now(self) -> datetime:
        return NOW


class FakeReviewCollectLedger(PhaseLedger):
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


class FakeGateRepo(HumanGateRepository):
    def __init__(self, answer: dict[str, object] | None = None) -> None:
        self._answer = answer
        self.raised: list[HumanGateRequest] = []

    async def raise_gate(
        self, project_id: UUID, job_id: UUID | None, request: HumanGateRequest
    ) -> HumanGateRecord:
        self.raised.append(request)
        return HumanGateRecord(
            gate_id=uuid4(),
            project_id=project_id,
            job_id=job_id,
            kind=request.kind,
            prompt=request.prompt,
            options=request.options,
            default_answer=request.default_answer,
            answer=self._answer,
            raised_at=NOW,
            timeout_at=None,
            answered_at=NOW if self._answer is not None else None,
            answered_by="tester" if self._answer is not None else None,
        )

    async def answer(
        self, gate_id: UUID, *, answer: Mapping[str, object], answered_by: str
    ) -> HumanGateRecord:
        self._answer = dict(answer)
        return HumanGateRecord(
            gate_id=gate_id,
            project_id=uuid4(),
            job_id=uuid4(),
            kind="approval",
            prompt="gate",
            options=(),
            default_answer=None,
            answer=self._answer,
            raised_at=NOW,
            timeout_at=None,
            answered_at=NOW,
            answered_by=answered_by,
        )

    async def latest_for_job(self, job_id: UUID) -> HumanGateRecord | None:
        if not self.raised:
            return None
        return HumanGateRecord(
            gate_id=uuid4(),
            project_id=uuid4(),
            job_id=job_id,
            kind="approval",
            prompt=self.raised[-1].prompt,
            options=self.raised[-1].options,
            default_answer=None,
            answer=self._answer,
            raised_at=NOW,
            timeout_at=None,
            answered_at=NOW if self._answer is not None else None,
            answered_by="tester" if self._answer is not None else None,
        )


def _make_job(
    *,
    kind: str = "review.collect",
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


async def test_review_collect_handler_rejects_wrong_kind() -> None:
    handler = ReviewCollectHandler(
        ledger=FakeReviewCollectLedger(),
        gates=FakeGateRepo(),
        jobs=FakeJobRepository(),
        clock=FixedClock(),
    )
    outcome = await handler.handle(_make_job(kind="review.demo"))
    assert isinstance(outcome, Failure)
    assert outcome.failure_class == FailureClass.VIBEY


async def test_review_collect_handler_parks_if_no_answer() -> None:
    gates = FakeGateRepo(answer=None)
    handler = ReviewCollectHandler(
        ledger=FakeReviewCollectLedger(),
        gates=gates,
        jobs=FakeJobRepository(),
        clock=FixedClock(),
    )
    job = _make_job()
    # 1. No gate yet -> raises and parks
    outcome1 = await handler.handle(job)
    assert isinstance(outcome1, Park)
    # 2. Gate exists but answer is None -> parks
    outcome2 = await handler.handle(job)
    assert isinstance(outcome2, Park)


async def test_review_collect_handler_accept_enqueues_triage() -> None:
    gates = FakeGateRepo(answer={"verdict": "accept"})
    jobs = FakeJobRepository()
    ledger = FakeReviewCollectLedger()
    handler = ReviewCollectHandler(
        ledger=ledger,
        gates=gates,
        jobs=jobs,
        clock=FixedClock(),
    )
    job = _make_job()
    assert isinstance(await handler.handle(job), Park)
    outcome = await handler.handle(job)
    assert isinstance(outcome, Success)

    enqueued = list(jobs._jobs.values())
    triage_job = next((j for j in enqueued if j.kind == "review.triage"), None)
    assert triage_job is not None


async def test_review_collect_handler_cancel_records_and_succeeds() -> None:
    gates = FakeGateRepo(answer={"verdict": "cancel"})
    jobs = FakeJobRepository()
    ledger = FakeReviewCollectLedger()
    handler = ReviewCollectHandler(
        ledger=ledger,
        gates=gates,
        jobs=jobs,
        clock=FixedClock(),
    )
    job = _make_job()
    assert isinstance(await handler.handle(job), Park)
    outcome = await handler.handle(job)
    assert isinstance(outcome, Success)
    assert outcome.result.get("verdict") == "cancel"


async def test_review_collect_handler_turns_free_text_changes_into_finding_events() -> None:
    gates = FakeGateRepo(
        answer={
            "verdict": "changes",
            "feedback": ["Button padding is too small", "Search should be case-insensitive"],
        }
    )
    jobs = FakeJobRepository()
    ledger = FakeReviewCollectLedger()
    handler = ReviewCollectHandler(
        ledger=ledger,
        gates=gates,
        jobs=jobs,
        clock=FixedClock(),
    )
    job = _make_job()
    assert isinstance(await handler.handle(job), Park)
    outcome = await handler.handle(job)
    assert isinstance(outcome, Success)

    findings = [payload for kind, payload in ledger.appended if kind == EventKind.FINDING_RAISED]
    assert len(findings) == 2
    assert "Button padding is too small" in [f["text"] for f in findings]
    assert "Search should be case-insensitive" in [f["text"] for f in findings]

    # Enqueues review.triage
    enqueued = list(jobs._jobs.values())
    triage_job = next((j for j in enqueued if j.kind == "review.triage"), None)
    assert triage_job is not None


async def test_review_collect_handler_answers_why_questions_from_ledger() -> None:
    events = (
        LedgerEvent(
            event_id=uuid4(),
            project_id=uuid4(),
            cycle=1,
            phase=Phase.DESIGN,
            seq=1,
            kind=EventKind.DECISION_RECORDED,
            engine_id=EngineId.CLAUDELOOP,
            job_id=uuid4(),
            causation_id=None,
            correlation_id=uuid4(),
            provenance=Provenance.TRUSTED,
            produced_at=NOW,
            payload={
                "decision_id": "dec-10",
                "title": "Use SQLite",
                "choice": "sqlite",
                "rationale": "Offline-first local file storage.",
            },
            digest="abc",
        ),
    )
    gates = FakeGateRepo(answer={"question": "Why did you use sqlite?"})
    jobs = FakeJobRepository()
    ledger = FakeReviewCollectLedger(events=events)
    handler = ReviewCollectHandler(
        ledger=ledger,
        gates=gates,
        jobs=jobs,
        clock=FixedClock(),
    )
    job = _make_job()
    assert isinstance(await handler.handle(job), Park)
    outcome = await handler.handle(job)
    assert isinstance(outcome, Success)
    assert "dec-10" in str(outcome.result.get("answer"))
    assert "Offline-first local file storage" in str(outcome.result.get("answer"))
