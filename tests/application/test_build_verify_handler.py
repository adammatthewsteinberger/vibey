from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

from tests.application.fakes import FakeJobRepository, make_job
from vibey.application.build_verify_handler import BuildVerifyHandler, GateResult
from vibey.application.dto import EngineEvent
from vibey.application.worker import Failure, Success
from vibey.domain.job import FailureClass
from vibey.infrastructure.engines.descriptors import CLAUDELOOP, CODEXLOOP
from vibey.infrastructure.engines.scripted import ScriptedEngine


class FakeWorktrees:
    def __init__(self, path: Path) -> None:
        self._path = path

    def path_for(self, item_id: str) -> Path:
        return self._path


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
        kind="build.verify",
        work_item_id="item-1",
        payload={"verification": {"commands": ("pytest",), "criteria_checked": ("AC-1",)}},
        requirement={"implementer_engine_id": "codexloop"},
    )
    return replace(job, **overrides) if overrides else job


async def test_successful_verify_runs_gates_reviews_the_diff_and_enqueues_integrate(
    tmp_path: Path,
) -> None:
    reviewer = ScriptedEngine(descriptor=CLAUDELOOP, base_dir=tmp_path / "engine")
    gates = FakeGateRunner()
    ledger = FakeLedger()
    jobs = FakeJobRepository()
    handler = BuildVerifyHandler(
        worktrees=FakeWorktrees(tmp_path),
        gates=gates,
        reviewer=reviewer,
        ledger=ledger,
        jobs=jobs,
    )

    job = _job()
    outcome = await handler.handle(job)

    assert isinstance(outcome, Success)
    assert outcome.result == {"work_item_id": "item-1", "gates_run": 1}
    assert gates.calls[0] == ("pytest",)
    assert gates.calls[-1] == ("git", "diff", "HEAD")
    assert any(event.kind == "VerdictRendered" for event in ledger.recorded)

    enqueued = await jobs.claim(job.project_id, owner="t", lease=timedelta(seconds=5))
    assert enqueued is not None
    assert enqueued.kind == "build.integrate"
    assert enqueued.work_item_id == "item-1"


async def test_rejects_wrong_kind_and_missing_work_item_id(tmp_path: Path) -> None:
    reviewer = ScriptedEngine(descriptor=CLAUDELOOP, base_dir=tmp_path / "engine")
    handler = BuildVerifyHandler(
        worktrees=FakeWorktrees(tmp_path),
        gates=FakeGateRunner(),
        reviewer=reviewer,
        ledger=FakeLedger(),
        jobs=FakeJobRepository(),
    )

    wrong_kind = replace(make_job(uuid4()), kind="build.implement")
    assert await handler.handle(wrong_kind) == Failure(
        FailureClass.VIBEY, "expected build.verify job"
    )
    missing_item = replace(make_job(uuid4()), kind="build.verify", work_item_id=None)
    assert await handler.handle(missing_item) == Failure(
        FailureClass.VIBEY, "build.verify job is missing work_item_id"
    )


async def test_rejects_a_reviewer_that_matches_the_implementer(tmp_path: Path) -> None:
    reviewer = ScriptedEngine(descriptor=CLAUDELOOP, base_dir=tmp_path / "engine")
    handler = BuildVerifyHandler(
        worktrees=FakeWorktrees(tmp_path),
        gates=FakeGateRunner(),
        reviewer=reviewer,
        ledger=FakeLedger(),
        jobs=FakeJobRepository(),
    )

    job = _job(requirement={"implementer_engine_id": "claudeloop"})
    outcome = await handler.handle(job)

    assert outcome == Failure(FailureClass.VIBEY, "verifier must differ from the implementer")


async def test_a_failing_gate_command_fails_as_work(tmp_path: Path) -> None:
    reviewer = ScriptedEngine(descriptor=CLAUDELOOP, base_dir=tmp_path / "engine")
    gates = FakeGateRunner(returncode=1, stderr="assertion failed")
    handler = BuildVerifyHandler(
        worktrees=FakeWorktrees(tmp_path),
        gates=gates,
        reviewer=reviewer,
        ledger=FakeLedger(),
        jobs=FakeJobRepository(),
    )

    outcome = await handler.handle(_job())

    assert isinstance(outcome, Failure)
    assert outcome.failure_class is FailureClass.WORK
    assert "pytest" in outcome.detail
    assert "assertion failed" in outcome.detail
    assert gates.calls == [("pytest",)]  # git diff never runs after a gate failure


async def test_no_criteria_checked_fails_as_work(tmp_path: Path) -> None:
    reviewer = ScriptedEngine(descriptor=CLAUDELOOP, base_dir=tmp_path / "engine")
    handler = BuildVerifyHandler(
        worktrees=FakeWorktrees(tmp_path),
        gates=FakeGateRunner(),
        reviewer=reviewer,
        ledger=FakeLedger(),
        jobs=FakeJobRepository(),
    )

    job = _job(payload={"verification": {"commands": (), "criteria_checked": ()}})
    outcome = await handler.handle(job)

    assert isinstance(outcome, Failure)
    assert outcome.failure_class is FailureClass.WORK
    assert "no acceptance criteria" in outcome.detail


async def test_reviewer_rejection_fails_as_work(tmp_path: Path) -> None:
    now = datetime(2026, 1, 1, tzinfo=UTC).isoformat()
    reviewer = ScriptedEngine(
        descriptor=CODEXLOOP,
        base_dir=tmp_path / "engine",
        script=[{"kind": "SessionSeeded", "at": now, "payload": {"seed_digest": "d1"}}],
    )
    handler = BuildVerifyHandler(
        worktrees=FakeWorktrees(tmp_path),
        gates=FakeGateRunner(),
        reviewer=reviewer,
        ledger=FakeLedger(),
        jobs=FakeJobRepository(),
    )

    job = _job(requirement={"implementer_engine_id": "claudeloop"})
    outcome = await handler.handle(job)

    assert outcome == Failure(FailureClass.WORK, "diff review did not approve this work item")
