# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Thin use-case wrappers around AutonomousRunner and the ports."""

from __future__ import annotations

from datetime import UTC, datetime

from codexloop.application.dto import ProbeResult, RunResult, TurnOutcome
from codexloop.application.runner import RunnerContext
from codexloop.application.usecases.list_threads import list_threads
from codexloop.application.usecases.preflight import preflight
from codexloop.application.usecases.resume_thread import resume_thread
from codexloop.application.usecases.run_plan import run_plan
from codexloop.domain.budget import Budget
from codexloop.domain.capacity import Available, QuotaExhausted
from codexloop.domain.completion import DEFAULT_DONE_MARKER
from codexloop.domain.session import PlanFile, ThreadRef
from codexloop.domain.signals import TurnSignals
from tests.application.fakes import (
    FakeAgentGateway,
    FakeCapacityProbe,
    FakeClock,
    FakeRunControl,
    FakeRunStateStore,
    FakeSleeper,
    FakeThreadCatalog,
)

NOW = datetime(2026, 8, 13, 12, 0, tzinfo=UTC)
PLAN = "- [ ] Add login\n"
THREAD_ID = "thr_use"


def _ctx(
    *,
    outcomes: list[TurnOutcome],
    probes: ProbeResult | None = None,
    catalog: FakeThreadCatalog | None = None,
    store: FakeRunStateStore | None = None,
) -> RunnerContext:
    clock = FakeClock(NOW)
    return RunnerContext(
        clock=clock,
        sleeper=FakeSleeper(clock),
        gateway=FakeAgentGateway(outcomes),
        probe=FakeCapacityProbe(probes),
        store=store or FakeRunStateStore(),
        control=FakeRunControl(),
        catalog=catalog,
        budget=Budget(max_turns=None, max_dollars=None, max_wall_clock=None),
    )


def _done() -> TurnOutcome:
    return TurnOutcome(
        thread_id=THREAD_ID,
        signals=TurnSignals(final_message=DEFAULT_DONE_MARKER),
    )


async def test_run_plan_drives_the_runner_to_done() -> None:
    result = await run_plan(_ctx(outcomes=[_done()]), PlanFile("plan.md"), PLAN)
    assert result == RunResult(success=True, reason="done", turns=1, thread_id=THREAD_ID)


async def test_resume_thread_uses_explicit_selector() -> None:
    store = FakeRunStateStore()
    store.save(
        THREAD_ID,
        {
            "thread_id": THREAD_ID,
            "turns": 1,
            "remaining_work": ["Add login"],
            "first_turn_done": True,
            "plan_text": PLAN,
            "dollars": 0.0,
            "elapsed_seconds": 0.0,
        },
    )
    result = await resume_thread(
        _ctx(outcomes=[_done()], store=store),
        THREAD_ID,
        PLAN,
    )
    assert result.success is True
    assert result.thread_id == THREAD_ID
    assert isinstance(result, RunResult)


async def test_preflight_returns_probe_result() -> None:
    exhausted = ProbeResult(outcome=QuotaExhausted(reason="insufficient_quota"))
    result = await preflight(_ctx(outcomes=[_done()], probes=exhausted))
    assert result == exhausted


def test_list_threads_delegates_to_catalog() -> None:
    catalog = FakeThreadCatalog()
    ref = ThreadRef(thread_id="thr_a", cwd="/work", started_at=NOW, model="gpt-5")
    catalog.record(ref)
    assert list(list_threads(_ctx(outcomes=[_done()], catalog=catalog))) == [ref]


def test_list_threads_without_catalog_is_empty() -> None:
    assert list(list_threads(_ctx(outcomes=[_done()], catalog=None))) == []


async def test_preflight_available_by_default() -> None:
    result = await preflight(_ctx(outcomes=[_done()]))
    assert result == ProbeResult(outcome=Available())


class _RecordingSink:
    """Captures what the runner publishes to events.jsonl."""

    def __init__(self) -> None:
        self.events: list[dict[str, object]] = []

    def emit(self, event: object) -> None:
        self.events.append(dict(event))  # type: ignore[arg-type]


class _RecordingSnapshots:
    def __init__(self) -> None:
        self.writes: list[dict[str, object]] = []

    def write(self, snapshot: object) -> None:
        self.writes.append(dict(snapshot))  # type: ignore[arg-type]


async def test_a_completed_run_publishes_its_verdict_with_the_done_marker() -> None:
    """The done marker was purely an INPUT -- the string the runner scans
    for in model output. Nothing published it, so a reader of the event
    stream could not distinguish a completed run from an abandoned one."""
    sink = _RecordingSink()
    ctx = _ctx(outcomes=[_done()])
    ctx.event_sink = sink

    result = await run_plan(ctx, PlanFile("plan.md"), "- [ ] work")

    assert result.success is True
    verdicts = [e for e in sink.events if e.get("type") == "run.verdict"]
    assert len(verdicts) == 1
    assert verdicts[0]["success"] is True
    assert verdicts[0]["complete"] is True
    assert verdicts[0]["done_marker"] == DEFAULT_DONE_MARKER


async def test_the_runner_snapshots_run_state_at_turn_boundaries() -> None:
    snapshots = _RecordingSnapshots()
    ctx = _ctx(outcomes=[_done()])
    ctx.snapshot_sink = snapshots

    await run_plan(ctx, PlanFile("plan.md"), "- [ ] work")

    assert snapshots.writes
    assert snapshots.writes[-1]["session_id"] == THREAD_ID


async def test_verdict_and_snapshot_are_optional_collaborators() -> None:
    """Neither sink is required: a run with both omitted still completes."""
    result = await run_plan(_ctx(outcomes=[_done()]), PlanFile("plan.md"), "- [ ] work")

    assert result.success is True


async def test_a_blocked_run_publishes_an_unsuccessful_verdict_without_the_marker() -> None:
    """The marker asserts completion, so a blocked run must not carry it --
    otherwise a reader would count an abandoned run as done. This also
    covers a run that never obtained a thread id."""
    sink = _RecordingSink()
    ctx = _ctx(
        outcomes=[
            TurnOutcome(
                thread_id=None,
                signals=TurnSignals(
                    structured_output={"complete": False, "blocked_on": "needs a credential"}
                ),
            )
        ]
    )
    ctx.event_sink = sink

    result = await run_plan(ctx, PlanFile("plan.md"), "- [ ] work")

    assert result.success is False
    verdicts = [e for e in sink.events if e.get("type") == "run.verdict"]
    assert len(verdicts) == 1
    assert verdicts[0]["success"] is False
    assert "done_marker" not in verdicts[0]
    assert "thread_id" not in verdicts[0]
