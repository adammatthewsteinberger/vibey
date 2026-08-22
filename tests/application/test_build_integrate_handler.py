# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
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


# ── the integration lock ─────────────────────────────────────────────────────


class FakeIntegrationLock:
    def __init__(self, *, available: bool = True) -> None:
        self.available = available
        self.calls: list[str] = []

    async def try_acquire(self, project_id, cycle):  # type: ignore[no-untyped-def]
        self.calls.append("try_acquire")
        return self.available

    async def release(self, project_id, cycle):  # type: ignore[no-untyped-def]
        self.calls.append("release")


async def test_lock_contention_defers_instead_of_merging(tmp_path: Path) -> None:
    from vibey.application.worker import Defer

    integration = FakeIntegration(merge_outcome=MergeOutcome(ok=True, detail=""), path=tmp_path)
    lock = FakeIntegrationLock(available=False)
    handler = BuildIntegrateHandler(
        integration=integration,
        gates=FakeGateRunner(),
        ledger=FakeLedger(),
        jobs=FakeJobRepository(),
        clock=FixedClock(),
        lock=lock,  # type: ignore[arg-type]
    )

    outcome = await handler.handle(_job())

    assert isinstance(outcome, Defer)
    assert outcome.retry_at == FixedClock().now() + timedelta(seconds=30)
    assert "held by another worker" in outcome.detail
    assert integration.merged == []
    assert lock.calls == ["try_acquire"]


async def test_lock_is_released_after_a_successful_merge(tmp_path: Path) -> None:
    integration = FakeIntegration(merge_outcome=MergeOutcome(ok=True, detail=""), path=tmp_path)
    lock = FakeIntegrationLock()
    handler = BuildIntegrateHandler(
        integration=integration,
        gates=FakeGateRunner(),
        ledger=FakeLedger(),
        jobs=FakeJobRepository(),
        clock=FixedClock(),
        lock=lock,  # type: ignore[arg-type]
    )

    outcome = await handler.handle(_job())

    assert isinstance(outcome, Success)
    assert lock.calls == ["try_acquire", "release"]


async def test_lock_is_released_even_when_the_merge_conflicts(tmp_path: Path) -> None:
    integration = FakeIntegration(
        merge_outcome=MergeOutcome(ok=False, detail="conflict in app.py"), path=tmp_path
    )
    lock = FakeIntegrationLock()
    handler = BuildIntegrateHandler(
        integration=integration,
        gates=FakeGateRunner(),
        ledger=FakeLedger(),
        jobs=FakeJobRepository(),
        clock=FixedClock(),
        lock=lock,  # type: ignore[arg-type]
    )

    outcome = await handler.handle(_job())

    assert isinstance(outcome, Failure)
    assert lock.calls == ["try_acquire", "release"]


async def test_kind_and_item_guards_never_touch_the_lock(tmp_path: Path) -> None:
    lock = FakeIntegrationLock()
    handler = BuildIntegrateHandler(
        integration=FakeIntegration(merge_outcome=MergeOutcome(ok=True, detail=""), path=tmp_path),
        gates=FakeGateRunner(),
        ledger=FakeLedger(),
        jobs=FakeJobRepository(),
        clock=FixedClock(),
        lock=lock,  # type: ignore[arg-type]
    )

    await handler.handle(replace(make_job(uuid4()), kind="build.verify"))
    await handler.handle(replace(make_job(uuid4()), kind="build.integrate", work_item_id=None))

    assert lock.calls == []


async def test_success_resolves_this_items_open_integrate_findings(tmp_path: Path) -> None:
    """Caught live: 39 stale conflict findings sent an accepted review
    straight back to BUILD long after the conflicts were repaired."""
    from uuid import uuid4 as _uuid4

    from vibey.domain.ledger import EventKind, LedgerEvent, Provenance, digest_event
    from vibey.domain.phase import Phase as _Phase

    def _event(kind: EventKind, finding_id: str, cycle: int = 1) -> LedgerEvent:
        payload: dict[str, object] = {"finding_id": finding_id}
        return LedgerEvent(
            event_id=_uuid4(),
            project_id=_uuid4(),
            cycle=cycle,
            phase=_Phase.BUILD,
            seq=1,
            kind=kind,
            engine_id=None,
            job_id=None,
            causation_id=None,
            correlation_id=_uuid4(),
            provenance=Provenance.AGENT,
            produced_at=datetime(2026, 8, 19, tzinfo=UTC),
            payload=payload,
            digest=digest_event(payload),
        )

    class _Reader:
        def __init__(self, events):  # type: ignore[no-untyped-def]
            self._events = events

        async def all_for_project(self, project_id):  # type: ignore[no-untyped-def]
            return tuple(self._events)

    job = _job()
    events = [
        _event(EventKind.FINDING_RAISED, "f_integrate_item-1_11111111"),
        _event(EventKind.FINDING_RAISED, "f_integrate_item-1_22222222"),
        _event(EventKind.FINDING_RESOLVED, "f_integrate_item-1_11111111"),
        _event(EventKind.FINDING_RAISED, "f_integrate_other_33333333"),
        _event(EventKind.FINDING_RAISED, "f_integrate_item-1_44444444", cycle=2),
        _event(EventKind.DECISION_RECORDED, "f_integrate_item-1_55555555"),
    ]
    ledger = FakeLedger()
    handler = BuildIntegrateHandler(
        integration=FakeIntegration(merge_outcome=MergeOutcome(ok=True, detail=""), path=tmp_path),
        gates=FakeGateRunner(),
        ledger=ledger,
        jobs=FakeJobRepository(),
        clock=FixedClock(),
        ledger_reader=_Reader(events),  # type: ignore[arg-type]
    )

    outcome = await handler.handle(job)

    assert isinstance(outcome, Success)
    resolutions = [e for e in ledger.recorded if e.kind == "FindingResolved"]
    assert [e.payload["finding_id"] for e in resolutions] == ["f_integrate_item-1_22222222"]
    assert "integrates cleanly" in str(resolutions[0].payload["resolution"])


# ── the bounded integrate repair loop ────────────────────────────────────────


def _integrate_finding(kind, finding_id: str, cycle: int = 1):  # type: ignore[no-untyped-def]
    from uuid import uuid4 as _uuid4

    from vibey.domain.ledger import LedgerEvent, Provenance, digest_event
    from vibey.domain.phase import Phase as _Phase

    payload: dict[str, object] = {"finding_id": finding_id}
    return LedgerEvent(
        event_id=_uuid4(),
        project_id=_uuid4(),
        cycle=cycle,
        phase=_Phase.BUILD,
        seq=1,
        kind=kind,
        engine_id=None,
        job_id=None,
        causation_id=None,
        correlation_id=_uuid4(),
        provenance=Provenance.AGENT,
        produced_at=datetime(2026, 8, 19, tzinfo=UTC),
        payload=payload,
        digest=digest_event(payload),
    )


class _EventReader:
    def __init__(self, events):  # type: ignore[no-untyped-def]
        self._events = events

    async def all_for_project(self, project_id):  # type: ignore[no-untyped-def]
        return tuple(self._events)


def _repairing_handler(tmp_path: Path, *, merge_ok: bool, events, jobs=None, ledger=None):  # type: ignore[no-untyped-def]
    return BuildIntegrateHandler(
        integration=FakeIntegration(
            merge_outcome=MergeOutcome(ok=merge_ok, detail="conflict in greet.py"),
            path=tmp_path,
        ),
        gates=FakeGateRunner(),
        ledger=ledger if ledger is not None else FakeLedger(),
        jobs=jobs if jobs is not None else FakeJobRepository(),
        clock=FixedClock(),
        ledger_reader=_EventReader(events),  # type: ignore[arg-type]
    )


async def test_merge_conflict_spawns_one_instructed_repair_and_defers(tmp_path: Path) -> None:
    """The repair session works on the item branch, where nothing looks
    wrong -- without explicit merge instructions it cannot fix a conflict
    that only exists against integration. Caught live as an unbounded
    storm of paid sessions."""
    from vibey.application.worker import Defer

    ledger = FakeLedger()
    jobs = FakeJobRepository()
    handler = _repairing_handler(tmp_path, merge_ok=False, events=[], jobs=jobs, ledger=ledger)

    outcome = await handler.handle(_job())

    assert isinstance(outcome, Defer)
    assert "repair enqueued" in outcome.detail
    (raised,) = [e for e in ledger.recorded if e.kind == "FindingRaised"]
    finding_id = str(raised.payload["finding_id"])
    repair = next(iter(jobs._jobs.values()))
    assert repair.kind == "build.implement"
    assert repair.payload["repair_finding_id"] == finding_id
    detail = str(repair.payload["repair_detail"])
    assert "git merge vibey/1/integration" in detail
    assert "conflict in greet.py" in detail


async def test_integrate_failure_with_repair_in_flight_only_defers(tmp_path: Path) -> None:
    from vibey.application.worker import Defer
    from vibey.domain.ledger import EventKind

    job = _job()
    events = [
        _integrate_finding(
            EventKind.FINDING_RAISED, "f_integrate_item-1_aaaa1111", cycle=job.cycle
        ),
        # Noise the scan must skip: wrong cycle, wrong item, non-finding kind.
        _integrate_finding(
            EventKind.FINDING_RAISED, "f_integrate_item-1_bbbb2222", cycle=job.cycle + 1
        ),
        _integrate_finding(EventKind.FINDING_RAISED, "f_verify_item-1_cccc3333", cycle=job.cycle),
        _integrate_finding(
            EventKind.DECISION_RECORDED, "f_integrate_item-1_dddd4444", cycle=job.cycle
        ),
    ]
    ledger = FakeLedger()
    jobs = FakeJobRepository()
    handler = _repairing_handler(tmp_path, merge_ok=False, events=events, jobs=jobs, ledger=ledger)

    outcome = await handler.handle(job)

    assert isinstance(outcome, Defer)
    assert "in flight" in outcome.detail
    assert ledger.recorded == []
    assert jobs._jobs == {}


async def test_exhausted_integrate_repairs_park_for_a_human(tmp_path: Path) -> None:
    from vibey.application.worker import Park
    from vibey.domain.ledger import EventKind

    job = _job()
    history = []
    for index in range(3):
        fid = f"f_integrate_item-1_{index:08d}"
        history.append(_integrate_finding(EventKind.FINDING_RAISED, fid, cycle=job.cycle))
        history.append(_integrate_finding(EventKind.FINDING_RESOLVED, fid, cycle=job.cycle))
    handler = _repairing_handler(tmp_path, merge_ok=False, events=history)

    outcome = await handler.handle(job)

    assert isinstance(outcome, Park)
    assert outcome.request.kind == "integrate_repair_exhausted"


async def test_post_merge_gate_failure_instructs_a_fix_not_a_merge(tmp_path: Path) -> None:
    from vibey.application.worker import Defer

    jobs = FakeJobRepository()
    handler = BuildIntegrateHandler(
        integration=FakeIntegration(merge_outcome=MergeOutcome(ok=True, detail=""), path=tmp_path),
        gates=FakeGateRunner(returncode=1, stderr="tests exploded"),
        ledger=FakeLedger(),
        jobs=jobs,
        clock=FixedClock(),
        ledger_reader=_EventReader([]),  # type: ignore[arg-type]
    )

    outcome = await handler.handle(_job())

    assert isinstance(outcome, Defer)
    repair = next(iter(jobs._jobs.values()))
    detail = str(repair.payload["repair_detail"])
    assert "without weakening the checks" in detail
    assert "git merge" not in detail


async def test_without_a_ledger_reader_the_original_failure_path_stands(
    tmp_path: Path,
) -> None:
    jobs = FakeJobRepository()
    handler = BuildIntegrateHandler(
        integration=FakeIntegration(
            merge_outcome=MergeOutcome(ok=False, detail="conflict"), path=tmp_path
        ),
        gates=FakeGateRunner(),
        ledger=FakeLedger(),
        jobs=jobs,
        clock=FixedClock(),
    )

    outcome = await handler.handle(_job())

    assert isinstance(outcome, Failure)
    repair = next(iter(jobs._jobs.values()))
    assert "repair_detail" not in repair.payload


async def test_an_answered_gate_grants_integrate_repair_rounds_too(tmp_path: Path) -> None:
    from tests.application.fakes import FakeHumanGateRepository
    from vibey.application.worker import Defer, Park
    from vibey.domain.ledger import EventKind

    job = _job()
    history = []
    for index in range(3):
        fid = f"f_integrate_item-1_{index:08d}"
        history.append(_integrate_finding(EventKind.FINDING_RAISED, fid, cycle=job.cycle))
        history.append(_integrate_finding(EventKind.FINDING_RESOLVED, fid, cycle=job.cycle))

    gates = FakeHumanGateRepository()

    def _handler():  # type: ignore[no-untyped-def]
        return BuildIntegrateHandler(
            integration=FakeIntegration(
                merge_outcome=MergeOutcome(ok=False, detail="conflict"), path=tmp_path
            ),
            gates=FakeGateRunner(),
            ledger=FakeLedger(),
            jobs=FakeJobRepository(),
            clock=FixedClock(),
            ledger_reader=_EventReader(history),  # type: ignore[arg-type]
            human_gates=gates,  # type: ignore[arg-type]
        )

    parked = await _handler().handle(job)
    assert isinstance(parked, Park)
    assert '"max_rounds"' in parked.request.prompt

    gate = await gates.raise_gate(job.project_id, job.id, parked.request)
    await gates.answer(gate.gate_id, answer={"max_rounds": 6}, answered_by="operator")
    retried = await _handler().handle(job)
    assert isinstance(retried, Defer)
    assert "repair enqueued" in retried.detail

    # A grant at or below the burned rounds still parks.
    await gates.answer(gate.gate_id, answer={"max_rounds": 2}, answered_by="operator")
    still_parked = await _handler().handle(job)
    assert isinstance(still_parked, Park)
