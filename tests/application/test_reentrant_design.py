# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://hire.adam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
from datetime import UTC, datetime
from uuid import UUID, uuid4

from tests.application.fakes import FakeHumanGateRepository, FakeJobRepository, make_job
from vibey.application.design import (
    DESIGN_STAGES,
    REENTRANT_DESIGN_STAGES,
    DesignEvent,
    DesignQuestion,
    DesignStage,
    QuestionBatch,
    stages_for_cycle,
)
from vibey.application.design_handler import DesignInterviewHandler
from vibey.application.worker import Park, Success
from vibey.domain.engine import EngineId
from vibey.domain.phase import Phase


class FixedClock:
    def now(self) -> datetime:
        return datetime(2026, 8, 15, tzinfo=UTC)


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
    async def batch(self, stage: DesignStage, prior_events: object) -> QuestionBatch:
        return QuestionBatch(
            stage,
            (
                DesignQuestion(
                    f"q-{stage.value}",
                    f"Question for {stage.value}?",
                    "default-answer",
                    blocking=False,
                ),
            ),
        )


def test_stages_for_cycle() -> None:
    # Cycle 1: all 7 stages
    assert stages_for_cycle(1) == DESIGN_STAGES
    assert len(stages_for_cycle(1)) == 7

    # Cycle 2+ (re-entrant design): scoped stages <= 5 batches
    reentrant = stages_for_cycle(2)
    assert reentrant == REENTRANT_DESIGN_STAGES
    assert len(reentrant) <= 5
    assert len(reentrant) == 4


async def test_reentrant_design_interview_runs_scoped_stages() -> None:
    project_id = uuid4()
    job = make_job(project_id)
    job = job.__class__(
        **{
            field: getattr(job, field)
            for field in job.__dataclass_fields__
            if field not in {"phase", "kind", "cycle"}
        },
        phase=Phase.DESIGN,
        kind="design.interview",
        cycle=2,  # Re-entrant design cycle
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

    # Re-entrant cycle 2 only runs the 4 scoped stages (<= 5 question batches)
    for stage in REENTRANT_DESIGN_STAGES:
        outcome = await handler.handle(job)
        assert isinstance(outcome, Park)
        assert stage.value in outcome.request.prompt
        raised = await gates.raise_gate(project_id, job.id, outcome.request)
        answer = {"answers": {f"q-{stage.value}": f"reentrant-answer-{stage.value}"}}
        await gates.answer(raised.gate_id, answer=answer, answered_by="tester")

    outcome = await handler.handle(job)
    assert isinstance(outcome, Success)
    assert outcome.result.get("stages") == 4
    assert outcome.result.get("stages") <= 5

    # Enqueued downstream synthesis & spec jobs carry cycle 2
    enqueued = list(jobs._jobs.values())
    synth = next(record for record in enqueued if record.kind == "design.synthesize")
    spec = next(record for record in enqueued if record.kind == "design.spec")
    assert synth.cycle == 2
    assert spec.cycle == 2
