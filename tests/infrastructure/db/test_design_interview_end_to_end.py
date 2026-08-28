# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://hire.adam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
from datetime import UTC, datetime, timedelta

import asyncpg

from vibey.application.design_acceptance import DesignAcceptanceService
from vibey.application.design_handler import DesignInterviewHandler
from vibey.application.design_research_handler import DesignResearchHandler
from vibey.application.design_synthesis_handler import DesignSpecHandler, DesignSynthesizeHandler
from vibey.application.dto import EnqueueRequest
from vibey.application.job_dispatcher import JobDispatcher
from vibey.application.worker import WorkerLoop
from vibey.domain.engine import EngineId
from vibey.domain.job import JobState, idempotency_key
from vibey.domain.ledger import EventKind
from vibey.domain.phase import Phase
from vibey.infrastructure.db.design_ledger import PostgresDesignLedger
from vibey.infrastructure.db.design_spec_repository import FileDesignSpecRepository
from vibey.infrastructure.db.human_gate_repository import PostgresHumanGateRepository
from vibey.infrastructure.db.job_repository import PostgresJobRepository
from vibey.infrastructure.db.ledger_repository import PostgresLedgerRepository
from vibey.infrastructure.db.project_repository import PostgresProjectRepository
from vibey.infrastructure.engines.scripted_design import ScriptedDesignProvider


class FixedClock:
    def now(self) -> datetime:
        return datetime(2026, 8, 14, tzinfo=UTC)


async def test_real_queue_runs_and_resumes_all_seven_interview_stages(
    migrated_pool: asyncpg.Pool, tmp_path
) -> None:
    projects = PostgresProjectRepository(migrated_pool)
    project = await projects.create("scripted-design", tmp_path, max_cycles=10, config={})
    project = await projects.transition(project.project_id, expected=Phase.INTAKE, to=Phase.DESIGN)
    project_id = project.project_id
    jobs = PostgresJobRepository(migrated_pool)
    gates = PostgresHumanGateRepository(migrated_pool)
    durable_ledger = PostgresLedgerRepository(migrated_pool)
    ledger = PostgresDesignLedger(durable_ledger)
    interview = await jobs.enqueue(
        EnqueueRequest(
            project_id=project_id,
            cycle=1,
            phase=Phase.DESIGN,
            kind="design.interview",
            idempotency_key=idempotency_key(project_id, 1, "design.interview", "integration"),
        )
    )
    provider = ScriptedDesignProvider()
    handler = DesignInterviewHandler(
        ledger=ledger,
        jobs=jobs,
        gates=gates,
        questions=provider,
        clock=FixedClock(),
        interviewer=EngineId.CLAUDELOOP,
    )
    worker = WorkerLoop(
        jobs=jobs,
        gates=gates,
        handler=handler,
        owner="design-worker",
        lease=timedelta(seconds=5),
    )

    for number in range(1, 8):
        assert await worker.run_once(project_id)
        parked = await jobs.get(interview.id)
        assert parked is not None
        assert parked.state is JobState.AWAITING_HUMAN
        gate = await gates.latest_for_job(interview.id)
        assert gate is not None
        await gates.answer(
            gate.gate_id,
            answer={"answers": {f"q-{number}": f"answer-{number}"}},
            answered_by="scripted-user",
        )

    assert await worker.run_once(project_id)
    completed = await jobs.get(interview.id)
    assert completed is not None
    assert completed.state is JobState.SUCCEEDED

    events = await durable_ledger.all_for_project(project_id)
    assert [event.kind for event in events].count(EventKind.QUESTION_ASKED) == 7
    assert [event.kind for event in events].count(EventKind.ANSWER_GIVEN) == 7
    assert all(event.produced_at == datetime(2026, 8, 14, tzinfo=UTC) for event in events)

    async with migrated_pool.acquire() as conn:
        kinds = await conn.fetch("SELECT kind, count(*) AS n FROM job GROUP BY kind")
        counts = {row["kind"]: row["n"] for row in kinds}
        dependency_count = await conn.fetchval("SELECT count(*) FROM job_dependency")
    assert counts == {
        "design.interview": 1,
        "design.research": 3,
        "design.synthesize": 1,
        "design.spec": 1,
    }
    assert dependency_count == 4

    specs = FileDesignSpecRepository(projects)
    dispatcher = JobDispatcher(
        {
            "design.research": DesignResearchHandler(
                ledger=ledger,
                researcher=provider,
                clock=FixedClock(),
                engine_id=EngineId.CODEXLOOP,
            ),
            "design.synthesize": DesignSynthesizeHandler(
                ledger=ledger, synthesizer=provider, specs=specs
            ),
            "design.spec": DesignSpecHandler(specs=specs),
        }
    )
    phase_worker = WorkerLoop(jobs=jobs, gates=gates, handler=dispatcher, owner="phase-worker")
    for _ in range(5):
        assert await phase_worker.run_once(project_id)
    assert not await phase_worker.run_once(project_id)

    async with migrated_pool.acquire() as conn:
        states = await conn.fetch("SELECT kind, state FROM job ORDER BY created_at, id")
    assert all(row["state"] == JobState.SUCCEEDED.value for row in states)
    assert (tmp_path / ".vibey/context/spec.md").exists()
    assert (tmp_path / ".vibey/context/acceptance.md").exists()
    research = [
        event
        for event in await durable_ledger.all_for_project(project_id)
        if event.kind is EventKind.ARTIFACT_PRODUCED
    ]
    assert len(research) == 3
    assert all(event.provenance.value == "untrusted" for event in research)

    accepted = await DesignAcceptanceService(
        projects=projects, ledger=ledger, specs=specs, jobs=jobs, clock=FixedClock()
    ).accept(project_id)
    assert accepted.phase is Phase.BUILD
    assert (await specs.load(project_id, 1)).is_buildable() == ()  # type: ignore[union-attr]
