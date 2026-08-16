from datetime import UTC, datetime
from uuid import UUID, uuid4

from tests.application.fakes import FakeHumanGateRepository, FakeJobRepository, make_job
from vibey.application.design import DESIGN_STAGES, DesignEvent, DesignQuestion, QuestionBatch
from vibey.application.design_handler import DesignInterviewHandler
from vibey.application.worker import Park, Success
from vibey.domain.engine import EngineId
from vibey.domain.ledger import EventKind
from vibey.domain.phase import Phase


class FixedClock:
    def now(self) -> datetime:
        return datetime(2026, 8, 14, tzinfo=UTC)


class FakeDesignLedger:
    def __init__(self) -> None:
        self.events: list[DesignEvent] = []

    async def append(
        self, project_id: UUID, cycle: int, job_id: UUID, engine_id: EngineId, event: DesignEvent
    ) -> None:
        self.events.append(event)

    async def all_for_project(self, project_id: UUID) -> tuple[DesignEvent, ...]:
        return tuple(self.events)


class ScriptedQuestionProvider:
    async def batch(self, stage, prior_events):  # type: ignore[no-untyped-def]
        number = DESIGN_STAGES.index(stage) + 1
        return QuestionBatch(
            stage,
            (
                DesignQuestion(
                    f"q-{number}",
                    f"Stage {number}?",
                    f"default-{number}",
                    blocking=number == 1,
                ),
            ),
        )


async def test_scripted_user_completes_all_seven_stages_and_enqueues_design_jobs() -> None:
    project_id = uuid4()
    job = make_job(project_id)
    job = job.__class__(
        **{
            field: getattr(job, field)
            for field in job.__dataclass_fields__
            if field not in {"phase", "kind"}
        },
        phase=Phase.DESIGN,
        kind="design.interview",
    )
    jobs = FakeJobRepository()
    gates = FakeHumanGateRepository()
    ledger = FakeDesignLedger()
    handler = DesignInterviewHandler(
        ledger=ledger,
        jobs=jobs,
        gates=gates,
        questions=ScriptedQuestionProvider(),
        clock=FixedClock(),
        interviewer=EngineId.CLAUDELOOP,
    )

    for index, stage in enumerate(DESIGN_STAGES):
        outcome = await handler.handle(job)
        assert isinstance(outcome, Park)
        assert stage.value in outcome.request.prompt
        raised = await gates.raise_gate(project_id, job.id, outcome.request)
        answer = {"answers": {f"q-{index + 1}": f"answer-{index + 1}"}}
        await gates.answer(raised.gate_id, answer=answer, answered_by="scripted-user")

    outcome = await handler.handle(job)
    assert isinstance(outcome, Success)
    kinds = [event.kind for event in ledger.events]
    assert kinds.count(EventKind.QUESTION_ASKED) == 7
    assert kinds.count(EventKind.ANSWER_GIVEN) == 7

    enqueued = list(jobs._jobs.values())
    assert [record.kind for record in enqueued].count("design.research") == 3
    synth = next(record for record in enqueued if record.kind == "design.synthesize")
    spec = next(record for record in enqueued if record.kind == "design.spec")
    assert synth.requirement["excluded"] == [EngineId.CLAUDELOOP.value]
    assert spec.phase is Phase.DESIGN


async def test_replay_does_not_duplicate_an_open_question_batch() -> None:
    project_id = uuid4()
    job = make_job(project_id)
    ledger = FakeDesignLedger()
    handler = DesignInterviewHandler(
        ledger=ledger,
        jobs=FakeJobRepository(),
        gates=FakeHumanGateRepository(),
        questions=ScriptedQuestionProvider(),
        clock=FixedClock(),
        interviewer=EngineId.CODEXLOOP,
    )
    first = await handler.handle(job)
    second = await handler.handle(job)
    assert isinstance(first, Park)
    assert isinstance(second, Park)
    assert len(ledger.events) == 1


async def test_nonblocking_default_is_recorded_when_batch_answer_omits_it() -> None:
    project_id = uuid4()
    job = make_job(project_id)
    ledger = FakeDesignLedger()
    gates = FakeHumanGateRepository()
    handler = DesignInterviewHandler(
        ledger=ledger,
        jobs=FakeJobRepository(),
        gates=gates,
        questions=ScriptedQuestionProvider(),
        clock=FixedClock(),
        interviewer=EngineId.CURSORLOOP,
    )
    first = await handler.handle(job)
    assert isinstance(first, Park)
    gate = await gates.raise_gate(project_id, job.id, first.request)
    await gates.answer(gate.gate_id, answer={"answers": {"q-1": "yes"}}, answered_by="user")
    second = await handler.handle(job)
    assert isinstance(second, Park)
    gate = await gates.raise_gate(project_id, job.id, second.request)
    await gates.answer(gate.gate_id, answer={"answers": {}}, answered_by="user")
    await handler.handle(job)
    assumption = next(event for event in ledger.events if event.kind is EventKind.ASSUMPTION_STATED)
    assert assumption.payload["text"] == "default-2"


async def test_blocking_question_reparks_when_answer_payload_is_missing() -> None:
    project_id = uuid4()
    job = make_job(project_id)
    ledger = FakeDesignLedger()
    gates = FakeHumanGateRepository()
    handler = DesignInterviewHandler(
        ledger=ledger,
        jobs=FakeJobRepository(),
        gates=gates,
        questions=ScriptedQuestionProvider(),
        clock=FixedClock(),
        interviewer=EngineId.AGYLOOP,
    )
    first = await handler.handle(job)
    assert isinstance(first, Park)
    gate = await gates.raise_gate(project_id, job.id, first.request)
    await gates.answer(gate.gate_id, answer={"text": "not structured"}, answered_by="user")
    replay = await handler.handle(job)
    assert isinstance(replay, Park)
    assert "q-1" in replay.request.prompt
