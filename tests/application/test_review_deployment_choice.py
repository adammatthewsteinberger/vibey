# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID, uuid4

from tests.application.fakes import FakeJobRepository
from vibey.application.dto import HumanGateRecord, HumanGateRequest, JobRecord, ProjectRecord
from vibey.application.ports import Clock, HumanGateRepository
from vibey.application.review_deployment_choice_handler import (
    PhaseLedger,
    ReviewDeploymentChoiceHandler,
)
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


class FakeReviewDeploymentLedger(PhaseLedger):
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
        self._events.append(
            LedgerEvent(
                event_id=uuid4(),
                project_id=project_id,
                cycle=cycle,
                phase=Phase.REVIEW,
                seq=len(self._events) + 1,
                kind=kind,
                engine_id=EngineId.CLAUDELOOP,
                job_id=job_id,
                causation_id=None,
                correlation_id=uuid4(),
                provenance=Provenance.TRUSTED,
                produced_at=NOW,
                payload=dict(payload),
                digest="abc",
            )
        )


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
            kind="choice",
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
            kind="choice",
            prompt=self.raised[-1].prompt,
            options=self.raised[-1].options,
            default_answer=self.raised[-1].default_answer,
            answer=self._answer,
            raised_at=NOW,
            timeout_at=None,
            answered_at=NOW if self._answer is not None else None,
            answered_by="tester" if self._answer is not None else None,
        )


class FakeProjectRepo:
    def __init__(self, project: ProjectRecord) -> None:
        self.project = project
        self.transitions: list[tuple[Phase, Phase]] = []

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
        self.transitions.append((expected, to))
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


def _make_job(
    *,
    project_id: UUID,
    cycle: int = 1,
    kind: str = "review.deployment_choice",
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
        payload={},
        requirement={"effort": Effort.LOW.name.lower()},
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


async def test_review_deployment_choice_handler_rejects_wrong_kind() -> None:
    project_id = uuid4()
    handler = ReviewDeploymentChoiceHandler(
        ledger=FakeReviewDeploymentLedger(),
        gates=FakeGateRepo(),
        jobs=FakeJobRepository(),
        projects=FakeProjectRepo(
            ProjectRecord(
                project_id=project_id,
                name="p1",
                repo_path=Path("/tmp"),
                phase=Phase.REVIEW,
                cycle=1,
                max_cycles=5,
                config={},
                created_at=NOW,
                updated_at=NOW,
            )
        ),
        clock=FixedClock(),
    )
    outcome = await handler.handle(_make_job(project_id=project_id, kind="review.demo"))
    assert isinstance(outcome, Failure)
    assert outcome.failure_class == FailureClass.VIBEY


async def test_review_deployment_choice_handler_parks_with_no_default_as_yes() -> None:
    project_id = uuid4()
    gates = FakeGateRepo(answer=None)
    handler = ReviewDeploymentChoiceHandler(
        ledger=FakeReviewDeploymentLedger(),
        gates=gates,
        jobs=FakeJobRepository(),
        projects=FakeProjectRepo(
            ProjectRecord(
                project_id=project_id,
                name="p1",
                repo_path=Path("/tmp"),
                phase=Phase.REVIEW,
                cycle=1,
                max_cycles=5,
                config={},
                created_at=NOW,
                updated_at=NOW,
            )
        ),
        clock=FixedClock(),
    )
    job = _make_job(project_id=project_id)
    # First call: raises gate and parks
    outcome1 = await handler.handle(job)
    assert isinstance(outcome1, Park)
    assert outcome1.request.default_answer == "local_only"
    assert "local_only" in outcome1.request.options
    assert "deploy" in outcome1.request.options

    # Second call without answer: parks on existing gate
    outcome2 = await handler.handle(job)
    assert isinstance(outcome2, Park)


async def test_review_deployment_choice_opt_out_reaches_done_with_local_completion() -> None:
    project_id = uuid4()
    proj = ProjectRecord(
        project_id=project_id,
        name="p1",
        repo_path=Path("/tmp"),
        phase=Phase.REVIEW,
        cycle=1,
        max_cycles=5,
        config={},
        created_at=NOW,
        updated_at=NOW,
    )
    gates = FakeGateRepo(answer={"choice": "local_only"})
    jobs = FakeJobRepository()
    ledger = FakeReviewDeploymentLedger()
    projects = FakeProjectRepo(proj)

    handler = ReviewDeploymentChoiceHandler(
        ledger=ledger,
        gates=gates,
        jobs=jobs,
        projects=projects,
        clock=FixedClock(),
    )
    job = _make_job(project_id=project_id)
    assert isinstance(await handler.handle(job), Park)
    outcome = await handler.handle(job)
    assert isinstance(outcome, Success)
    assert outcome.result.get("completion_mode") == "local"
    assert outcome.result.get("decision") == "declined"

    # Ledger recorded DeploymentDeclined
    events = [k for k, p in ledger.appended]
    assert EventKind.DEPLOYMENT_DECLINED in events
    assert EventKind.DEPLOYMENT_OPTED_IN not in events

    # Project transitioned to DONE
    assert projects.project.phase is Phase.DONE

    # Enqueued NO deployment jobs
    enqueued = list(jobs._jobs.values())
    assert len(enqueued) == 0


async def test_review_deployment_choice_opt_in_records_event() -> None:
    project_id = uuid4()
    proj = ProjectRecord(
        project_id=project_id,
        name="p1",
        repo_path=Path("/tmp"),
        phase=Phase.REVIEW,
        cycle=1,
        max_cycles=5,
        config={},
        created_at=NOW,
        updated_at=NOW,
    )
    gates = FakeGateRepo(answer={"choice": "deploy"})
    jobs = FakeJobRepository()
    ledger = FakeReviewDeploymentLedger()
    projects = FakeProjectRepo(proj)

    handler = ReviewDeploymentChoiceHandler(
        ledger=ledger,
        gates=gates,
        jobs=jobs,
        projects=projects,
        clock=FixedClock(),
    )
    job = _make_job(project_id=project_id)
    assert isinstance(await handler.handle(job), Park)
    outcome = await handler.handle(job)
    assert isinstance(outcome, Success)
    assert outcome.result.get("decision") == "opted_in"
    assert outcome.result.get("completion_mode") == "deploy"

    # Ledger recorded DeploymentOptedIn
    events = [k for k, p in ledger.appended]
    assert EventKind.DEPLOYMENT_OPTED_IN in events
    assert EventKind.DEPLOYMENT_DECLINED not in events


async def test_review_deployment_choice_opt_in_skips_transition_without_transition_method() -> None:
    project_id = uuid4()
    gates = FakeGateRepo(answer={"choice": "deploy"})
    jobs = FakeJobRepository()
    ledger = FakeReviewDeploymentLedger(
        events=(
            LedgerEvent(
                event_id=uuid4(),
                project_id=project_id,
                cycle=1,
                phase=Phase.REVIEW,
                seq=1,
                kind=EventKind.VERDICT_RENDERED,
                engine_id=EngineId.CLAUDELOOP,
                job_id=uuid4(),
                causation_id=None,
                correlation_id=uuid4(),
                provenance=Provenance.TRUSTED,
                produced_at=NOW,
                payload={"complete": False},
                digest="abc",
            ),
        )
    )

    handler = ReviewDeploymentChoiceHandler(
        ledger=ledger,
        gates=gates,
        jobs=jobs,
        projects=object(),
        clock=FixedClock(),
    )
    job = _make_job(project_id=project_id)
    assert isinstance(await handler.handle(job), Park)
    outcome = await handler.handle(job)
    assert isinstance(outcome, Success)
    assert outcome.result.get("decision") == "opted_in"

    enqueued = list(jobs._jobs.values())
    assert any(j.kind == "deploy.design" for j in enqueued)


async def test_review_deployment_choice_opt_out_skips_transition_no_method() -> None:
    project_id = uuid4()
    gates = FakeGateRepo(answer={"choice": "local_only"})
    jobs = FakeJobRepository()
    ledger = FakeReviewDeploymentLedger()

    handler = ReviewDeploymentChoiceHandler(
        ledger=ledger,
        gates=gates,
        jobs=jobs,
        projects=object(),
        clock=FixedClock(),
    )
    job = _make_job(project_id=project_id)
    assert isinstance(await handler.handle(job), Park)
    outcome = await handler.handle(job)
    assert isinstance(outcome, Success)
    assert outcome.result.get("decision") == "declined"
    assert outcome.result.get("completion_mode") == "local"
