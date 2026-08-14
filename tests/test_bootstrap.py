from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

from tests.application.fakes import FakeHumanGateRepository, FakeJobRepository, make_job
from vibey.application.design import DesignEvent
from vibey.application.dto import ProjectRecord
from vibey.bootstrap import build_design_worker
from vibey.domain.job import JobState
from vibey.domain.phase import Phase
from vibey.infrastructure.engines.scripted_design import ScriptedDesignProvider


class FakeLedger:
    def __init__(self) -> None:
        self.events: list[DesignEvent] = []

    async def append(self, project_id, cycle, job_id, engine_id, event):  # type: ignore[no-untyped-def]
        self.events.append(event)

    async def all_for_project(self, project_id):  # type: ignore[no-untyped-def]
        return tuple(self.events)


async def test_build_design_worker_composes_an_executable_interview(tmp_path: Path) -> None:
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
    jobs = FakeJobRepository([job])
    gates = FakeHumanGateRepository()
    resources = SimpleNamespace(
        jobs=jobs,
        gates=gates,
        design_ledger=FakeLedger(),
        design_specs=SimpleNamespace(),
    )
    project = ProjectRecord(
        project_id=project_id,
        name="idea",
        repo_path=tmp_path,
        phase=Phase.DESIGN,
        cycle=1,
        max_cycles=10,
        config={},
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    worker = build_design_worker(
        resources=resources,  # type: ignore[arg-type]
        project=project,
        provider=ScriptedDesignProvider(),
        owner="test-worker",
    )

    assert await worker.run_once(project_id)
    stored = await jobs.get(job.id)
    assert stored is not None
    assert stored.state is JobState.AWAITING_HUMAN
    assert len(gates.raised) == 1
