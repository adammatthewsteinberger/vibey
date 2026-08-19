from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

from tests.application.fakes import FakeJobRepository, make_job
from vibey.application.build_integrate_handler import BuildIntegrateHandler, MergeOutcome
from vibey.application.build_verify_handler import GateResult
from vibey.application.dto import EngineEvent
from vibey.application.worker import Failure, Success
from vibey.domain.job import FailureClass


class FixedClock:
    def now(self) -> datetime:
        return datetime(2026, 8, 14, tzinfo=UTC)


class FakeIntegration:
    def __init__(self, *, merge_outcome: MergeOutcome, path: Path) -> None:
        self._merge_outcome = merge_outcome
        self._path = path
        self.merged: list[str] = []

    async def ensure(self) -> Path:
        return self._path

    async def merge_item(self, item_id: str) -> MergeOutcome:
        self.merged.append(item_id)
        return self._merge_outcome


class FakeGateRunner:
    def __init__(self, *, returncode: int = 0, stderr: str = "") -> None:
        self.returncode = returncode
        self.stderr = stderr
        self.calls: list[tuple[str, ...]] = []

    async def run(self, argv: tuple[str, ...], *, cwd: Path) -> GateResult:
        self.calls.append(argv)
        return GateResult(self.returncode, "", self.stderr)


class FakeLedger:
    def __init__(self) -> None:
        self.recorded: list[EngineEvent] = []

    async def record(self, *, project_id, cycle, job_id, engine_id, correlation_id, event):  # type: ignore[no-untyped-def]
        self.recorded.append(event)


def _job(**overrides: object):  # type: ignore[no-untyped-def]
    job = replace(
        make_job(uuid4()),
        kind="build.integrate",
        work_item_id="item-1",
        payload={"verification": {"commands": ("true",), "criteria_checked": ("AC-1",)}},
    )
    return replace(job, **overrides) if overrides else job


async def test_successful_integrate_merges_and_runs_gates(tmp_path: Path) -> None:
    integration = FakeIntegration(merge_outcome=MergeOutcome(ok=True, detail=""), path=tmp_path)
    gates = FakeGateRunner()
    handler = BuildIntegrateHandler(
        integration=integration,
        gates=gates,
        ledger=FakeLedger(),
        jobs=FakeJobRepository(),
        clock=FixedClock(),
    )

    outcome = await handler.handle(_job())

    assert isinstance(outcome, Success)
    assert outcome.result == {"work_item_id": "item-1"}
    assert integration.merged == ["item-1"]
    assert gates.calls == [("true",)]


async def test_rejects_wrong_kind_and_missing_work_item_id(tmp_path: Path) -> None:
    integration = FakeIntegration(merge_outcome=MergeOutcome(ok=True, detail=""), path=tmp_path)
    handler = BuildIntegrateHandler(
        integration=integration,
        gates=FakeGateRunner(),
        ledger=FakeLedger(),
        jobs=FakeJobRepository(),
        clock=FixedClock(),
    )

    wrong_kind = replace(make_job(uuid4()), kind="build.verify")
    assert await handler.handle(wrong_kind) == Failure(
        FailureClass.VIBEY, "expected build.integrate job"
    )
    missing_item = replace(make_job(uuid4()), kind="build.integrate", work_item_id=None)
    assert await handler.handle(missing_item) == Failure(
        FailureClass.VIBEY, "build.integrate job is missing work_item_id"
    )


async def test_merge_conflict_raises_a_finding_and_repairs_without_failing_other_items(
    tmp_path: Path,
) -> None:
    integration = FakeIntegration(
        merge_outcome=MergeOutcome(ok=False, detail="CONFLICT in src/foo.py"), path=tmp_path
    )
    ledger = FakeLedger()
    jobs = FakeJobRepository()
    handler = BuildIntegrateHandler(
        integration=integration,
        gates=FakeGateRunner(),
        ledger=ledger,
        jobs=jobs,
        clock=FixedClock(),
    )

    job = _job()
    outcome = await handler.handle(job)

    assert isinstance(outcome, Failure)
    assert outcome.failure_class is FailureClass.WORK
    assert "merge conflict" in outcome.detail
    assert "CONFLICT in src/foo.py" in outcome.detail

    assert len(ledger.recorded) == 1
    finding = ledger.recorded[0]
    assert finding.kind == "FindingRaised"
    assert finding.payload["severity"] == "high"
    assert "CONFLICT in src/foo.py" in str(finding.payload["text"])

    repair = await jobs.claim(job.project_id, owner="t", lease=timedelta(seconds=5))
    assert repair is not None
    assert repair.kind == "build.implement"
    assert repair.work_item_id == "item-1"
    assert repair.payload["base_ref"] == "vibey/1/integration"


async def test_gate_failure_after_merge_raises_a_finding_and_repairs(tmp_path: Path) -> None:
    integration = FakeIntegration(merge_outcome=MergeOutcome(ok=True, detail=""), path=tmp_path)
    gates = FakeGateRunner(returncode=1, stderr="integration test failed")
    ledger = FakeLedger()
    jobs = FakeJobRepository()
    handler = BuildIntegrateHandler(
        integration=integration, gates=gates, ledger=ledger, jobs=jobs, clock=FixedClock()
    )

    job = _job()
    outcome = await handler.handle(job)

    assert isinstance(outcome, Failure)
    assert outcome.failure_class is FailureClass.WORK
    assert "gate failed after merging" in outcome.detail
    assert len(ledger.recorded) == 1
    assert ledger.recorded[0].kind == "FindingRaised"

    repair = await jobs.claim(job.project_id, owner="t", lease=timedelta(seconds=5))
    assert repair is not None
    assert repair.kind == "build.implement"


class FakeTransitioner:
    def __init__(self, *, raises: bool = False) -> None:
        self.calls: list[tuple[object, object]] = []
        self._raises = raises

    async def transition(self, project_id, *, expected, to, cycle=None):  # type: ignore[no-untyped-def]
        self.calls.append((expected, to))
        if self._raises:
            raise ValueError("not in expected phase")


async def test_last_integrate_transitions_to_review_and_enqueues_demo(tmp_path: Path) -> None:
    jobs = FakeJobRepository()
    projects = FakeTransitioner()
    handler = BuildIntegrateHandler(
        integration=FakeIntegration(merge_outcome=MergeOutcome(True, ""), path=tmp_path),
        gates=FakeGateRunner(),
        ledger=FakeLedger(),
        jobs=jobs,
        clock=FixedClock(),
        projects=projects,
    )

    outcome = await handler.handle(_job())

    assert isinstance(outcome, Success)
    assert projects.calls == [("build", "review")]
    demo_jobs = [j for j in jobs._jobs.values() if j.kind == "review.demo"]
    assert len(demo_jobs) == 1


async def test_integrate_with_unsettled_siblings_does_not_enter_review(tmp_path: Path) -> None:
    job = _job()
    sibling = replace(make_job(job.project_id), kind="build.implement")
    jobs = FakeJobRepository([sibling])
    projects = FakeTransitioner()
    handler = BuildIntegrateHandler(
        integration=FakeIntegration(merge_outcome=MergeOutcome(True, ""), path=tmp_path),
        gates=FakeGateRunner(),
        ledger=FakeLedger(),
        jobs=jobs,
        clock=FixedClock(),
        projects=projects,
    )

    outcome = await handler.handle(job)

    assert isinstance(outcome, Success)
    assert projects.calls == []
    assert not any(j.kind == "review.demo" for j in jobs._jobs.values())


async def test_integrate_review_bridge_tolerates_cas_miss(tmp_path: Path) -> None:
    """A replay whose transition already happened must still (idempotently)
    enqueue review.demo and settle as success -- never poison the job."""
    jobs = FakeJobRepository()
    projects = FakeTransitioner(raises=True)
    handler = BuildIntegrateHandler(
        integration=FakeIntegration(merge_outcome=MergeOutcome(True, ""), path=tmp_path),
        gates=FakeGateRunner(),
        ledger=FakeLedger(),
        jobs=jobs,
        clock=FixedClock(),
        projects=projects,
    )

    outcome = await handler.handle(_job())

    assert isinstance(outcome, Success)
    assert any(j.kind == "review.demo" for j in jobs._jobs.values())
