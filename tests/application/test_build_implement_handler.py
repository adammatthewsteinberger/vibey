from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import pytest

from tests.application.fakes import FakeJobRepository, make_job
from vibey.application.build_implement_handler import BuildImplementHandler
from vibey.application.dto import EngineEvent
from vibey.application.worker import Defer, Failure, Park, Success
from vibey.domain.job import FailureClass
from vibey.domain.provision import ProvisionSpec
from vibey.infrastructure.engines.descriptors import CLAUDELOOP
from vibey.infrastructure.engines.scripted import ScriptedEngine


class FixedClock:
    def now(self) -> datetime:
        return datetime(2026, 8, 14, tzinfo=UTC)


class FakeWorktrees:
    def __init__(self, tmp_path: Path) -> None:
        self.tmp_path = tmp_path
        self.created: list[str] = []

    async def create(self, item_id: str, *, base_ref: str = "HEAD") -> Path:
        self.created.append(item_id)
        path = self.tmp_path / item_id
        path.mkdir(parents=True, exist_ok=True)
        return path


class FakeProvisioner:
    def __init__(self) -> None:
        self.calls: list[Path] = []

    async def provision(self, worktree_path: Path, spec: ProvisionSpec) -> tuple[Path, ...]:
        self.calls.append(worktree_path)
        return ()


class FakeLedger:
    def __init__(self) -> None:
        self.recorded: list[EngineEvent] = []

    async def record(self, *, project_id, cycle, job_id, engine_id, correlation_id, event):  # type: ignore[no-untyped-def]
        self.recorded.append(event)


def _job(**overrides: object):  # type: ignore[no-untyped-def]
    job = replace(make_job(uuid4()), kind="build.implement", work_item_id="item-1", attempts=1)
    return replace(job, **overrides) if overrides else job


def _handler(
    tmp_path: Path, *, engine: ScriptedEngine, ledger: FakeLedger
) -> tuple[BuildImplementHandler, FakeWorktrees, FakeProvisioner]:
    worktrees = FakeWorktrees(tmp_path)
    provisioner = FakeProvisioner()
    handler = BuildImplementHandler(
        worktrees=worktrees,
        provisioner=provisioner,
        engine=engine,
        ledger=ledger,
        jobs=FakeJobRepository(),
        clock=FixedClock(),
    )
    return handler, worktrees, provisioner


async def test_successful_run_provisions_and_records_events_and_succeeds(tmp_path: Path) -> None:
    engine = ScriptedEngine(descriptor=CLAUDELOOP, base_dir=tmp_path / "engine")
    ledger = FakeLedger()
    worktrees = FakeWorktrees(tmp_path)
    provisioner = FakeProvisioner()
    jobs = FakeJobRepository()
    handler = BuildImplementHandler(
        worktrees=worktrees,
        provisioner=provisioner,
        engine=engine,
        ledger=ledger,
        jobs=jobs,
        clock=FixedClock(),
    )

    job = _job(payload={"title": "do the thing", "verification": {}})
    outcome = await handler.handle(job)

    assert isinstance(outcome, Success)
    assert outcome.result["work_item_id"] == "item-1"
    assert worktrees.created == ["item-1"]
    assert provisioner.calls == [tmp_path / "item-1"]
    assert any(event.kind == "VerdictRendered" for event in ledger.recorded)

    enqueued = await jobs.claim(job.project_id, owner="t", lease=timedelta(seconds=5))
    assert enqueued is not None
    assert enqueued.kind == "build.verify"
    assert enqueued.work_item_id == "item-1"
    assert enqueued.requirement["implementer_engine_id"] == "claudeloop"


async def test_rejects_wrong_kind_and_missing_work_item_id() -> None:
    engine = ScriptedEngine(descriptor=CLAUDELOOP, base_dir=Path("/tmp/unused"))
    handler, _, _ = _handler(Path("/tmp/unused"), engine=engine, ledger=FakeLedger())

    wrong_kind = replace(make_job(uuid4()), kind="build.decompose")
    assert await handler.handle(wrong_kind) == Failure(
        FailureClass.VIBEY, "expected build.implement job"
    )
    missing_item = replace(make_job(uuid4()), kind="build.implement", work_item_id=None)
    assert await handler.handle(missing_item) == Failure(
        FailureClass.VIBEY, "build.implement job is missing work_item_id"
    )


async def test_escalation_ladder_exhausted_parks_for_a_human_gate(tmp_path: Path) -> None:
    engine = ScriptedEngine(descriptor=CLAUDELOOP, base_dir=tmp_path / "engine")
    handler, _, _ = _handler(tmp_path, engine=engine, ledger=FakeLedger())

    outcome = await handler.handle(_job(attempts=8))

    assert isinstance(outcome, Park)
    assert "item-1" in outcome.request.prompt
    assert "8 attempts" in outcome.request.prompt


async def test_capacity_rejected_event_defers_the_job(tmp_path: Path) -> None:
    now = datetime(2026, 1, 1, tzinfo=UTC).isoformat()
    engine = ScriptedEngine(
        descriptor=CLAUDELOOP,
        base_dir=tmp_path / "engine",
        script=[
            {"kind": "SessionSeeded", "at": now, "payload": {"seed_digest": "d1"}},
            {
                "kind": "CapacityRejected",
                "at": now,
                "payload": {"capacity_state": "CreditsExhausted", "can_purchase": True},
            },
        ],
    )
    ledger = FakeLedger()
    handler, _, _ = _handler(tmp_path, engine=engine, ledger=ledger)

    outcome = await handler.handle(_job())

    assert isinstance(outcome, Defer)
    assert outcome.retry_at == FixedClock().now() + timedelta(minutes=5)
    assert "capacity rejection" in outcome.detail
    assert any(event.kind == "CapacityRejected" for event in ledger.recorded)


@pytest.mark.parametrize("attempt", [3, 5])
async def test_forced_rotation_rejects_same_engine(tmp_path: Path, attempt: int) -> None:
    """At attempts 3 and 5 the effort tier crosses a boundary, so forces_rotation
    is True.  The handler must reject execution if the injected engine matches the
    previous attempt's engine."""
    engine = ScriptedEngine(descriptor=CLAUDELOOP, base_dir=tmp_path / "engine")
    handler, _, _ = _handler(tmp_path, engine=engine, ledger=FakeLedger())

    job = _job(
        attempts=attempt,
        payload={"title": "t", "previous_engine_id": "claudeloop"},
    )
    outcome = await handler.handle(job)

    assert isinstance(outcome, Failure)
    assert outcome.failure_class is FailureClass.VIBEY
    assert "rotation" in outcome.detail.lower()


@pytest.mark.parametrize("attempt", [3, 5])
async def test_forced_rotation_allows_different_engine(tmp_path: Path, attempt: int) -> None:
    """At rotation-forcing attempts, a *different* engine proceeds normally."""
    engine = ScriptedEngine(descriptor=CLAUDELOOP, base_dir=tmp_path / "engine")
    ledger = FakeLedger()
    handler, _, _ = _handler(tmp_path, engine=engine, ledger=ledger)

    job = _job(
        attempts=attempt,
        payload={"title": "t", "previous_engine_id": "codexloop"},
    )
    outcome = await handler.handle(job)

    assert isinstance(outcome, Success)


@pytest.mark.parametrize("attempt", [1, 2, 4, 6])
async def test_no_forced_rotation_at_non_crossing_attempts(tmp_path: Path, attempt: int) -> None:
    """At attempts where effort does NOT cross a tier, same engine is fine."""
    engine = ScriptedEngine(descriptor=CLAUDELOOP, base_dir=tmp_path / "engine")
    ledger = FakeLedger()
    handler, _, _ = _handler(tmp_path, engine=engine, ledger=ledger)

    job = _job(
        attempts=attempt,
        payload={"title": "t", "previous_engine_id": "claudeloop"},
    )
    outcome = await handler.handle(job)

    is_rotation_failure = (
        isinstance(outcome, Failure)
        and outcome.failure_class is FailureClass.VIBEY
        and "rotation" in outcome.detail.lower()
    )
    assert not is_rotation_failure


async def test_budget_exceeded_parks_before_escalation(tmp_path: Path) -> None:
    """When the projected cost of an escalated attempt would exceed the budget,
    the handler must park for a human gate instead of proceeding."""
    from vibey.domain.budget import BudgetLedger as BudgetLedgerDC

    class FixedBudgetSource:
        def __init__(self, ledger: BudgetLedgerDC) -> None:
            self._ledger = ledger

        async def current(self, project_id: object, cycle: int) -> BudgetLedgerDC:
            return self._ledger

    engine = ScriptedEngine(descriptor=CLAUDELOOP, base_dir=tmp_path / "engine")
    budget = BudgetLedgerDC(turns_spent=0, dollars_spent=9.50, max_turns=None, max_dollars=10.0)
    worktrees = FakeWorktrees(tmp_path)
    provisioner = FakeProvisioner()
    handler = BuildImplementHandler(
        worktrees=worktrees,
        provisioner=provisioner,
        engine=engine,
        ledger=FakeLedger(),
        jobs=FakeJobRepository(),
        clock=FixedClock(),
        budget_source=FixedBudgetSource(budget),
    )

    job = _job(
        attempts=2,
        payload={"title": "t", "projected_cost_per_attempt": 1.00},
    )
    outcome = await handler.handle(job)

    assert isinstance(outcome, Park)
    assert "budget" in outcome.request.prompt.lower()


async def test_budget_at_exact_cap_is_allowed(tmp_path: Path) -> None:
    """An escalation that lands exactly at the cap is allowed."""
    from vibey.domain.budget import BudgetLedger as BudgetLedgerDC

    class FixedBudgetSource:
        def __init__(self, ledger: BudgetLedgerDC) -> None:
            self._ledger = ledger

        async def current(self, project_id: object, cycle: int) -> BudgetLedgerDC:
            return self._ledger

    engine = ScriptedEngine(descriptor=CLAUDELOOP, base_dir=tmp_path / "engine")
    budget = BudgetLedgerDC(turns_spent=0, dollars_spent=9.00, max_turns=None, max_dollars=10.0)
    worktrees = FakeWorktrees(tmp_path)
    provisioner = FakeProvisioner()
    handler = BuildImplementHandler(
        worktrees=worktrees,
        provisioner=provisioner,
        engine=engine,
        ledger=FakeLedger(),
        jobs=FakeJobRepository(),
        clock=FixedClock(),
        budget_source=FixedBudgetSource(budget),
    )

    job = _job(
        attempts=2,
        payload={"title": "t", "projected_cost_per_attempt": 1.00},
    )
    outcome = await handler.handle(job)

    assert isinstance(outcome, Success)


async def test_no_budget_source_skips_check(tmp_path: Path) -> None:
    """When no budget source is provided, the handler proceeds normally."""
    engine = ScriptedEngine(descriptor=CLAUDELOOP, base_dir=tmp_path / "engine")
    handler, _, _ = _handler(tmp_path, engine=engine, ledger=FakeLedger())

    job = _job(
        attempts=2,
        payload={"title": "t", "projected_cost_per_attempt": 999.0},
    )
    outcome = await handler.handle(job)

    assert isinstance(outcome, Success)


async def test_non_numeric_projected_cost_skips_budget_check(tmp_path: Path) -> None:
    """When projected_cost_per_attempt is a non-numeric value (e.g. a string),
    isinstance(projected, int | float) is False and the budget check is skipped."""
    from vibey.domain.budget import BudgetLedger as BudgetLedgerDC

    class FixedBudgetSource:
        def __init__(self, ledger: BudgetLedgerDC) -> None:
            self._ledger = ledger

        async def current(self, project_id: object, cycle: int) -> BudgetLedgerDC:
            return self._ledger

    engine = ScriptedEngine(descriptor=CLAUDELOOP, base_dir=tmp_path / "engine")
    budget = BudgetLedgerDC(turns_spent=0, dollars_spent=9.50, max_turns=None, max_dollars=10.0)
    worktrees = FakeWorktrees(tmp_path)
    provisioner = FakeProvisioner()
    handler = BuildImplementHandler(
        worktrees=worktrees,
        provisioner=provisioner,
        engine=engine,
        ledger=FakeLedger(),
        jobs=FakeJobRepository(),
        clock=FixedClock(),
        budget_source=FixedBudgetSource(budget),
    )

    job = _job(
        attempts=2,
        payload={"title": "t", "projected_cost_per_attempt": "not-a-number"},
    )
    outcome = await handler.handle(job)
    assert isinstance(outcome, Success)


async def test_run_without_a_completion_verdict_fails_as_work(tmp_path: Path) -> None:
    now = datetime(2026, 1, 1, tzinfo=UTC).isoformat()
    engine = ScriptedEngine(
        descriptor=CLAUDELOOP,
        base_dir=tmp_path / "engine",
        script=[{"kind": "SessionSeeded", "at": now, "payload": {"seed_digest": "d1"}}],
    )
    handler, _, _ = _handler(tmp_path, engine=engine, ledger=FakeLedger())

    outcome = await handler.handle(_job())

    assert outcome == Failure(FailureClass.WORK, "engine run did not report completion")


# ── wind-down (exit code 75) ─────────────────────────────────────────────────


class _RecordingWindDown:
    """Stands in for WindDownOrchestrator: records the call and returns a
    sentinel Success so the test can prove delegation, not re-test the
    orchestrator's own pipeline."""

    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    async def execute(self, *, job, worktree_path, engine_id, effort, stop):  # type: ignore[no-untyped-def]
        self.calls.append(
            {
                "job_id": job.id,
                "worktree_path": worktree_path,
                "engine_id": engine_id,
                "effort": effort,
                "stop": stop,
            }
        )
        return Success({"wind_down": True})


def _wind_down_script() -> list[dict[str, object]]:
    now = datetime(2026, 1, 1, tzinfo=UTC).isoformat()
    return [{"kind": "SessionSeeded", "at": now, "payload": {"seed_digest": "d1"}}]


async def test_exit_75_with_an_orchestrator_stops_and_delegates(tmp_path: Path) -> None:
    engine = ScriptedEngine(
        descriptor=CLAUDELOOP,
        base_dir=tmp_path / "engine",
        script=_wind_down_script(),
        exit_code_script=[75],
        stop_remaining=("resume from the snapshot",),
    )
    wind_down = _RecordingWindDown()
    handler = BuildImplementHandler(
        worktrees=FakeWorktrees(tmp_path),
        provisioner=FakeProvisioner(),
        engine=engine,
        ledger=FakeLedger(),
        jobs=FakeJobRepository(),
        clock=FixedClock(),
        wind_down=wind_down,  # type: ignore[arg-type]
    )

    outcome = await handler.handle(_job())

    assert outcome == Success({"wind_down": True})
    (call,) = wind_down.calls
    assert call["engine_id"] == CLAUDELOOP.engine_id
    assert call["worktree_path"] == tmp_path / "item-1"
    stop = call["stop"]
    assert stop.remaining_work == ("resume from the snapshot",)


async def test_exit_75_without_an_orchestrator_keeps_the_old_failure_path(
    tmp_path: Path,
) -> None:
    engine = ScriptedEngine(
        descriptor=CLAUDELOOP,
        base_dir=tmp_path / "engine",
        script=_wind_down_script(),
        exit_code_script=[75],
    )
    handler, _, _ = _handler(tmp_path, engine=engine, ledger=FakeLedger())

    outcome = await handler.handle(_job())

    assert outcome == Failure(FailureClass.WORK, "engine run did not report completion")


async def test_normal_exit_with_an_orchestrator_never_winds_down(tmp_path: Path) -> None:
    engine = ScriptedEngine(
        descriptor=CLAUDELOOP,
        base_dir=tmp_path / "engine",
        exit_code_script=[0],
    )
    wind_down = _RecordingWindDown()
    handler = BuildImplementHandler(
        worktrees=FakeWorktrees(tmp_path),
        provisioner=FakeProvisioner(),
        engine=engine,
        ledger=FakeLedger(),
        jobs=FakeJobRepository(),
        clock=FixedClock(),
        wind_down=wind_down,  # type: ignore[arg-type]
    )

    outcome = await handler.handle(_job(payload={"title": "t"}))

    assert isinstance(outcome, Success)
    assert wind_down.calls == []


async def test_seed_prompt_in_the_payload_reaches_the_engine_verbatim(tmp_path: Path) -> None:
    engine = ScriptedEngine(descriptor=CLAUDELOOP, base_dir=tmp_path / "engine")
    handler, _, _ = _handler(tmp_path, engine=engine, ledger=FakeLedger())
    seed = "Objective: resume the relay.\nNext action: close [q-77]."

    outcome = await handler.handle(_job(payload={"title": "ignored", "seed_prompt": seed}))

    assert isinstance(outcome, Success)
    # ScriptedEngine ignores the prompt, so prove it through the renderer.
    from vibey.application.build_implement_handler import _render_prompt

    assert _render_prompt("item-1", {"seed_prompt": seed}) == seed
    assert "Implement work item" in _render_prompt("item-1", {"seed_prompt": ""})
