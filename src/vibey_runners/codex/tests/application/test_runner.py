# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Autonomous runner: fakes only, never wall-clock sleep."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from datetime import UTC, datetime, timedelta

import pytest

from codexloop.application.dto import ProbeResult, RunResult, TurnOutcome
from codexloop.application.runner import AutonomousRunner, RunnerContext
from codexloop.domain.budget import Budget
from codexloop.domain.capacity import AuthFailed, Available, ThrottleExhausted, WindowExhausted
from codexloop.domain.completion import DEFAULT_DONE_MARKER
from codexloop.domain.control import Stop
from codexloop.domain.forecast import WindDownPolicy
from codexloop.domain.handoff_marker import HandoffMarker
from codexloop.domain.session import Explicit, MostRecent, PlanFile, ThreadRef
from codexloop.domain.signals import TurnSignals
from codexloop.domain.waiting import AdaptiveWaitPolicy, WaitConfig
from tests.application.fakes import (
    FakeAgentGateway,
    FakeCapacityProbe,
    FakeClock,
    FakeRunControl,
    FakeRunStateStore,
    FakeSessionLock,
    FakeSleeper,
    FakeThreadCatalog,
)

NOW = datetime(2026, 8, 13, 12, 0, tzinfo=UTC)
PLAN = "- [ ] Add login\n- [ ] Add logout\n"
THREAD_ID = "thr_test"
ZERO_JITTER = AdaptiveWaitPolicy(WaitConfig(jitter_ratio=0.0), rand=lambda: 0.0)


def _done(*, thread_id: str = THREAD_ID) -> TurnOutcome:
    return TurnOutcome(
        thread_id=thread_id,
        signals=TurnSignals(final_message=DEFAULT_DONE_MARKER),
    )


def _continue(
    remaining: Sequence[str],
    *,
    thread_id: str = THREAD_ID,
    cost_dollars: float = 0.0,
) -> TurnOutcome:
    return TurnOutcome(
        thread_id=thread_id,
        cost_dollars=cost_dollars,
        signals=TurnSignals(
            structured_output={
                "complete": False,
                "remaining_work": list(remaining),
            }
        ),
    )


def _blocked(reason: str, *, thread_id: str = THREAD_ID) -> TurnOutcome:
    return TurnOutcome(
        thread_id=thread_id,
        signals=TurnSignals(
            structured_output={
                "complete": False,
                "remaining_work": [],
                "blocked_on": reason,
            }
        ),
    )


def make_ctx(
    *,
    outcomes: Sequence[TurnOutcome],
    probes: ProbeResult | Sequence[ProbeResult] | None = None,
    budget: Budget | None = None,
    control: FakeRunControl | None = None,
    store: FakeRunStateStore | None = None,
    catalog: FakeThreadCatalog | None = None,
    lock: FakeSessionLock | None = None,
    write_artifact: Callable[[str, str], None] | None = None,
    call_log: list[str] | None = None,
    turn_elapsed: timedelta | None = None,
    max_wait: timedelta | None = None,
    clock: FakeClock | None = None,
    handoff_marker_writer: object | None = None,
    wind_down_policy: WindDownPolicy | None = None,
    logger: object | None = None,
) -> tuple[RunnerContext, FakeAgentGateway, FakeClock, FakeSleeper, FakeRunStateStore]:
    clock = clock or FakeClock(NOW)
    log = call_log
    sleeper = FakeSleeper(clock, call_log=log)
    gateway = FakeAgentGateway(outcomes, clock=clock, turn_elapsed=turn_elapsed, call_log=log)
    store_obj = store or FakeRunStateStore(call_log=log)
    ctx = RunnerContext(
        clock=clock,
        sleeper=sleeper,
        gateway=gateway,
        probe=FakeCapacityProbe(probes, call_log=log),
        store=store_obj,
        control=control or FakeRunControl(call_log=log),
        catalog=catalog,
        lock=FakeSessionLock() if lock is None else lock,
        write_artifact=write_artifact,
        budget=budget or Budget(max_turns=None, max_dollars=None, max_wall_clock=None),
        wait_policy=ZERO_JITTER,
        max_wait=max_wait,
        handoff_marker_writer=handoff_marker_writer,  # type: ignore[arg-type]
        wind_down_policy=wind_down_policy or WindDownPolicy(),
        logger=logger,  # type: ignore[arg-type]
    )
    return ctx, gateway, clock, sleeper, store_obj


async def test_happy_path_preflight_turn_done_exits_success() -> None:
    call_log: list[str] = []
    ctx, gateway, _clock, _sleeper, store = make_ctx(outcomes=[_done()], call_log=call_log)

    result = await AutonomousRunner(ctx).run(PlanFile("plan.md"), PLAN)

    assert result == RunResult(success=True, reason="done", turns=1, thread_id=THREAD_ID)
    assert gateway.sent_prompts == [PLAN]
    assert gateway.closed is True
    assert call_log == [
        "poll",
        "probe",
        "send_turn",
        "save",
        "poll",
        "save",
        "close",
    ]
    assert store.saves
    assert store.saves[0][0] == THREAD_ID


async def test_continuation_uses_remaining_work_from_turn_two() -> None:
    remaining = ["Add login", "Add logout"]
    ctx, gateway, *_ = make_ctx(
        outcomes=[
            _continue(remaining),
            _continue(["Add logout"]),
            _continue(["Add logout"]),
            _done(),
        ]
    )

    result = await AutonomousRunner(ctx).run(PlanFile("plan.md"), PLAN)

    assert result.success is True
    assert result.turns == 4
    assert gateway.sent_prompts[0] == PLAN
    for prompt in gateway.sent_prompts[1:]:
        assert prompt != PLAN
        assert "Add logout" in prompt
    assert "Add login" in gateway.sent_prompts[1]
    assert DEFAULT_DONE_MARKER in gateway.sent_prompts[1]


@pytest.mark.parametrize(
    ("budget", "outcome", "turn_elapsed", "named"),
    [
        (
            Budget(max_turns=1, max_dollars=None, max_wall_clock=None),
            _continue(["x"]),
            None,
            "turns",
        ),
        (
            Budget(max_turns=None, max_dollars=1.0, max_wall_clock=None),
            _continue(["x"], cost_dollars=1.0),
            None,
            "dollars",
        ),
        (
            Budget(max_turns=None, max_dollars=None, max_wall_clock=timedelta(seconds=5)),
            _continue(["x"]),
            timedelta(seconds=10),
            "wall_clock",
        ),
    ],
)
async def test_budget_trips_independently(
    budget: Budget,
    outcome: TurnOutcome,
    turn_elapsed: timedelta | None,
    named: str,
) -> None:
    ctx, gateway, *_ = make_ctx(outcomes=[outcome], budget=budget, turn_elapsed=turn_elapsed)

    result = await AutonomousRunner(ctx).run(PlanFile("plan.md"), PLAN)

    assert result.success is False
    assert result.reason == named
    assert result.turns == 1
    assert gateway.sent_prompts == [PLAN]


async def test_state_is_written_after_every_turn_and_fresh_runner_resumes() -> None:
    remaining = ["wire the runner"]
    store = FakeRunStateStore()
    ctx1, gateway1, *_ = make_ctx(
        outcomes=[_continue(remaining), _done()],
        store=store,
    )

    first = await AutonomousRunner(ctx1).run(PlanFile("plan.md"), PLAN)

    assert first.success is True
    assert first.turns == 2
    turn_saves = [snapshot for _key, snapshot in store.saves]
    assert len(turn_saves) >= 2
    mid = next(s for s in turn_saves if s.get("turns") == 1)
    assert mid["remaining_work"] == list(remaining)
    assert mid["first_turn_done"] is True
    assert mid["thread_id"] == THREAD_ID

    seeded = FakeRunStateStore()
    seeded.save(THREAD_ID, mid)
    ctx2, gateway2, *_rest = make_ctx(outcomes=[_done()], store=seeded)

    resumed = await AutonomousRunner(ctx2).run(Explicit(THREAD_ID), PLAN)

    assert resumed.success is True
    assert resumed.thread_id == THREAD_ID
    assert gateway2.sent_prompts[0] != PLAN
    assert "wire the runner" in gateway2.sent_prompts[0]


async def test_stop_mid_run_finishes_inflight_turn_and_writes_stop_summary() -> None:
    artifacts: dict[str, str] = {}
    control = FakeRunControl(script=[[], [Stop()]])
    ctx, gateway, *_ = make_ctx(
        outcomes=[_continue(["Add login"])],
        control=control,
        write_artifact=artifacts.__setitem__,
    )

    result = await AutonomousRunner(ctx).run(PlanFile("plan.md"), PLAN)

    assert result == RunResult(success=False, reason="stop", turns=1, thread_id=THREAD_ID)
    assert gateway.sent_prompts == [PLAN]
    assert gateway.closed is True
    assert "stop-summary.md" in artifacts
    summary = artifacts["stop-summary.md"]
    assert "stop" in summary.lower()
    assert "Add login" in summary


async def test_wait_until_uses_adaptive_policy_not_sentinel_now() -> None:
    call_log: list[str] = []
    window = WindowExhausted(resets_at=NOW + timedelta(days=7), window="weekly")
    ctx, gateway, clock, sleeper, _store = make_ctx(
        outcomes=[_done()],
        probes=[
            ProbeResult(outcome=window),
            ProbeResult(outcome=Available()),
        ],
        call_log=call_log,
    )

    result = await AutonomousRunner(ctx).run(PlanFile("plan.md"), PLAN)

    assert result.success is True
    assert sleeper.requested
    assert sleeper.requested[0] > NOW
    assert clock.now() >= sleeper.requested[0]
    assert "sleep_until" in call_log
    assert gateway.sent_prompts == [PLAN]


async def test_throttle_backoff_sleeps_via_adaptive_policy() -> None:
    ctx, gateway, _clock, sleeper, _store = make_ctx(
        outcomes=[_done()],
        probes=[
            ProbeResult(outcome=ThrottleExhausted()),
            ProbeResult(outcome=Available()),
        ],
    )

    result = await AutonomousRunner(ctx).run(PlanFile("plan.md"), PLAN)

    assert result.success is True
    assert sleeper.requested
    assert gateway.sent_prompts == [PLAN]


async def test_preflight_auth_failure_never_sends_a_turn() -> None:
    ctx, gateway, *_ = make_ctx(
        outcomes=[],
        probes=ProbeResult(outcome=AuthFailed(reason="invalid_api_key")),
    )

    result = await AutonomousRunner(ctx).run(PlanFile("plan.md"), PLAN)

    assert result.success is False
    assert result.reason == "auth"
    assert gateway.sent_prompts == []


async def test_blocked_completion_fails_with_blocked_reason() -> None:
    ctx, gateway, *_ = make_ctx(outcomes=[_blocked("needs human")])

    result = await AutonomousRunner(ctx).run(PlanFile("plan.md"), PLAN)

    assert result.success is False
    assert result.reason == "needs human"
    assert gateway.sent_prompts == [PLAN]


async def test_max_wait_deadline_fails_without_sending() -> None:
    ctx, gateway, *_ = make_ctx(
        outcomes=[],
        probes=ProbeResult(outcome=WindowExhausted()),
        max_wait=timedelta(0),
    )

    result = await AutonomousRunner(ctx).run(PlanFile("plan.md"), PLAN)

    assert result.success is False
    assert result.reason == "max_wait"
    assert gateway.sent_prompts == []


async def test_most_recent_selector_resumes_latest_catalog_thread() -> None:
    catalog = FakeThreadCatalog()
    catalog.record(
        ThreadRef(thread_id="old", cwd=".", started_at=NOW - timedelta(hours=2), model="gpt-5")
    )
    catalog.record(ThreadRef(thread_id=THREAD_ID, cwd=".", started_at=NOW, model="gpt-5"))
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
    ctx, gateway, *_ = make_ctx(outcomes=[_done()], store=store, catalog=catalog)

    result = await AutonomousRunner(ctx).run(MostRecent(), PLAN)

    assert result.success is True
    assert result.thread_id == THREAD_ID
    assert gateway.sent_prompts[0] != PLAN
    assert "Add login" in gateway.sent_prompts[0]


async def test_lock_held_fails_before_sending() -> None:
    lock = FakeSessionLock()
    assert lock.acquire(THREAD_ID) is True
    ctx, gateway, *_ = make_ctx(outcomes=[_done()], lock=lock)

    result = await AutonomousRunner(ctx).run(Explicit(THREAD_ID), PLAN)

    assert result.success is False
    assert result.reason == "lock"
    assert gateway.sent_prompts == []


async def test_none_signals_continue_then_done() -> None:
    ctx, gateway, *_ = make_ctx(
        outcomes=[
            TurnOutcome(thread_id=THREAD_ID, signals=None),
            _done(),
        ]
    )

    result = await AutonomousRunner(ctx).run(PlanFile("plan.md"), PLAN)

    assert result.success is True
    assert result.turns == 2
    assert len(gateway.sent_prompts) == 2


async def test_stop_without_artifact_writer_still_returns_stop() -> None:
    control = FakeRunControl(script=[[], [Stop()]])
    ctx, _gateway, *_ = make_ctx(outcomes=[_continue(["x"])], control=control)

    result = await AutonomousRunner(ctx).run(PlanFile("plan.md"), PLAN)

    assert result.success is False
    assert result.reason == "stop"


async def test_most_recent_without_catalog_starts_fresh() -> None:
    ctx, gateway, *_ = make_ctx(outcomes=[_done()])

    result = await AutonomousRunner(ctx).run(MostRecent(), PLAN)

    assert result.success is True
    assert gateway.sent_prompts == [PLAN]


async def test_most_recent_with_empty_catalog_starts_fresh() -> None:
    ctx, gateway, *_ = make_ctx(outcomes=[_done()], catalog=FakeThreadCatalog())

    result = await AutonomousRunner(ctx).run(MostRecent(), PLAN)

    assert result.success is True
    assert gateway.sent_prompts == [PLAN]


async def test_empty_plan_text_skips_parse() -> None:
    ctx, gateway, *_ = make_ctx(outcomes=[_done()])

    result = await AutonomousRunner(ctx).run(PlanFile("plan.md"), "")

    assert result.success is True
    assert gateway.sent_prompts == [""]


async def test_turn_without_thread_id_still_completes() -> None:
    ctx, gateway, *_ = make_ctx(
        outcomes=[TurnOutcome(signals=TurnSignals(final_message=DEFAULT_DONE_MARKER))]
    )

    result = await AutonomousRunner(ctx).run(PlanFile("plan.md"), PLAN)

    assert result.success is True
    assert result.thread_id is None
    assert gateway.sent_prompts == [PLAN]


async def test_resume_with_zeroed_ledger_and_non_list_remaining() -> None:
    store = FakeRunStateStore()
    store.save(
        THREAD_ID,
        {
            "thread_id": THREAD_ID,
            "turns": "not-an-int",
            "remaining_work": "not-a-list",
            "first_turn_done": True,
            "plan_text": PLAN,
            "dollars": "not-a-float",
            "elapsed_seconds": None,
        },
    )
    ctx, gateway, *_ = make_ctx(outcomes=[_done()], store=store)

    result = await AutonomousRunner(ctx).run(Explicit(THREAD_ID), PLAN)

    assert result.success is True
    assert gateway.sent_prompts[0] != PLAN


async def test_post_turn_lock_failure_does_not_abort_run() -> None:
    lock = FakeSessionLock()
    assert lock.acquire(THREAD_ID) is True
    ctx, gateway, *_ = make_ctx(outcomes=[_done()], lock=lock)

    result = await AutonomousRunner(ctx).run(PlanFile("plan.md"), PLAN)

    assert result.success is True
    assert gateway.sent_prompts == [PLAN]


async def test_stop_with_empty_remaining_work_writes_none() -> None:
    artifacts: dict[str, str] = {}
    control = FakeRunControl(script=[[], [Stop()]])
    ctx, _gateway, *_ = make_ctx(
        outcomes=[TurnOutcome(thread_id=THREAD_ID, signals=None)],
        control=control,
        write_artifact=artifacts.__setitem__,
    )

    result = await AutonomousRunner(ctx).run(PlanFile("plan.md"), PLAN)

    assert result.reason == "stop"
    assert "_none_" in artifacts["stop-summary.md"]


async def test_capacity_rejected_turn_keeps_prior_remaining_work() -> None:
    remaining = ["Add login", "Add logout"]
    artifacts: dict[str, str] = {}
    ctx, _gateway, _clock, _sleeper, store = make_ctx(
        outcomes=[
            _continue(remaining),
            TurnOutcome(
                thread_id=THREAD_ID,
                signals=TurnSignals(
                    http_status=429,
                    error_code="usage_limit_reached",
                    error_type="usage_limit_reached",
                ),
            ),
        ],
        write_artifact=artifacts.__setitem__,
        control=FakeRunControl(script=[[], [], [Stop()]]),
    )

    result = await AutonomousRunner(ctx).run(PlanFile("plan.md"), PLAN)

    assert result.success is not True
    rejected = next(snapshot for _key, snapshot in store.saves if snapshot.get("turns") == 2)
    assert rejected["remaining_work"] == list(remaining)
    assert "Add login" in artifacts["stop-summary.md"]
    assert "Add logout" in artifacts["stop-summary.md"]


@pytest.mark.parametrize("error_code", ["insufficient_quota", "usage_limit_reached"])
async def test_done_looking_capacity_rejected_turn_waits(error_code: str) -> None:
    ctx, _gateway, _clock, sleeper, _store = make_ctx(
        outcomes=[
            TurnOutcome(
                thread_id=THREAD_ID,
                signals=TurnSignals(
                    final_message=DEFAULT_DONE_MARKER,
                    http_status=429,
                    error_code=error_code,
                    error_type=error_code,
                    structured_output={"complete": True, "remaining_work": []},
                ),
            ),
        ],
        max_wait=timedelta(seconds=1),
    )

    result = await AutonomousRunner(ctx).run(PlanFile("plan.md"), PLAN)

    assert result.success is not True
    assert sleeper.requested


async def test_fatal_error_code_fails_run_without_burning_budget() -> None:
    ctx, gateway, *_ = make_ctx(
        outcomes=[
            TurnOutcome(
                thread_id=THREAD_ID,
                signals=TurnSignals(
                    error_code="context_length_exceeded",
                    http_status=400,
                    failed=True,
                ),
            ),
            _done(),
        ],
        budget=Budget(max_turns=5, max_dollars=None, max_wall_clock=None),
    )

    result = await AutonomousRunner(ctx).run(PlanFile("plan.md"), PLAN)

    assert result.success is False
    assert result.reason == "context_length_exceeded"
    assert result.turns == 1
    assert gateway.sent_prompts == [PLAN]


async def test_failed_turn_without_capacity_code_is_blocked() -> None:
    ctx, gateway, *_ = make_ctx(
        outcomes=[
            TurnOutcome(
                thread_id=THREAD_ID,
                signals=TurnSignals(failed=True, final_message="boom"),
            ),
            _done(),
        ]
    )

    result = await AutonomousRunner(ctx).run(PlanFile("plan.md"), PLAN)

    assert result.success is False
    assert result.reason == "turn_failed"
    assert gateway.sent_prompts == [PLAN]


async def test_mid_run_controls_reach_gateway() -> None:
    from codexloop.application.ports import PermissionMode
    from codexloop.domain.approval import ApprovalPolicy, SandboxMode
    from codexloop.domain.control import (
        Prompt,
        PromptTiming,
        ResourceMutate,
        SetApproval,
        SetCwd,
        SetEffort,
        SetModel,
        SetSandbox,
        Snapshot,
    )
    from codexloop.domain.model_profile import Effort

    artifacts: dict[str, str] = {}
    control = FakeRunControl(
        script=[
            [],
            [
                SetModel(model="o3"),
                SetEffort(effort=Effort.HIGH),
                SetApproval(policy=ApprovalPolicy.ON_REQUEST),
                SetSandbox(sandbox=SandboxMode.READ_ONLY),
                SetCwd(cwd="/tmp/work"),
                ResourceMutate(payload={"add_dirs": ["/extra"]}),
                Snapshot(),
                Prompt(text="operator nudge", timing=PromptTiming.NEXT_TURN),
            ],
        ]
    )
    ctx, gateway, *_ = make_ctx(
        outcomes=[_continue(["x"]), _done()],
        control=control,
        write_artifact=artifacts.__setitem__,
    )

    result = await AutonomousRunner(ctx).run(PlanFile("plan.md"), PLAN)

    assert result.success is True
    assert gateway.profiles[-1].model == "o3"
    assert gateway.profiles[-1].effort is Effort.HIGH
    assert PermissionMode.READ_ONLY in gateway.permission_modes
    assert gateway.cwds == ["/tmp/work"]
    assert any(item.get("add_dirs") == ["/extra"] for item in gateway.resource_updates)
    assert "snapshot.json" in artifacts
    assert gateway.sent_prompts[1] == "operator nudge"


async def test_full_access_sandbox_control_maps_permission_mode() -> None:
    from codexloop.application.ports import PermissionMode
    from codexloop.domain.approval import SandboxMode
    from codexloop.domain.control import SetSandbox

    control = FakeRunControl(script=[[SetSandbox(sandbox=SandboxMode.DANGER_FULL_ACCESS)], []])
    ctx, gateway, *_ = make_ctx(outcomes=[_done()], control=control)
    result = await AutonomousRunner(ctx).run(PlanFile("plan.md"), PLAN)
    assert result.success is True
    assert PermissionMode.FULL_ACCESS in gateway.permission_modes


async def test_fatal_error_type_alone_blocks_run() -> None:
    ctx, gateway, *_ = make_ctx(
        outcomes=[
            TurnOutcome(
                thread_id=THREAD_ID,
                signals=TurnSignals(error_type="invalid_prompt", failed=False),
            )
        ]
    )
    result = await AutonomousRunner(ctx).run(PlanFile("plan.md"), PLAN)
    assert result.success is False
    assert result.reason == "invalid_prompt"
    assert gateway.sent_prompts == [PLAN]


async def test_a_wind_down_hands_off_instead_of_finishing() -> None:
    """A supervisor has to tell "resume me elsewhere" from "this is done"."""
    markers: list[HandoffMarker] = []
    ctx, _gateway, _clock, _sleeper, _store = make_ctx(
        outcomes=[_continue(["finish the thing"]), _done()],
        # One turn of headroom against a reserve of two: the first completed
        # turn is already inside the reserve.
        budget=Budget(max_turns=2, max_dollars=10.0, max_wall_clock=None),
        handoff_marker_writer=markers.append,
        wind_down_policy=WindDownPolicy(enabled=True),
    )

    result = await AutonomousRunner(ctx).run(PlanFile("plan.md"), PLAN)

    assert result.success is False
    assert result.reason.startswith("wind-down:")
    assert markers and markers[0].reason == "turn_reserve"
    assert markers[0].remaining_work is not None


async def test_a_wind_down_without_a_marker_writer_still_finishes() -> None:
    """No writer means no marker, which is the honest signal: a supervisor that
    finds no handoff.json falls back to the reactive path."""
    ctx, _gateway, _clock, _sleeper, _store = make_ctx(
        outcomes=[_continue(["finish the thing"]), _done()],
        budget=Budget(max_turns=2, max_dollars=10.0, max_wall_clock=None),
        wind_down_policy=WindDownPolicy(enabled=True),
    )

    result = await AutonomousRunner(ctx).run(PlanFile("plan.md"), PLAN)

    assert result.success is False
    assert "wind-down" in result.reason


async def test_the_policy_off_leaves_the_run_untouched() -> None:
    """The predictive path is strictly additive."""
    ctx, _gateway, _clock, _sleeper, _store = make_ctx(
        outcomes=[_done()],
        budget=Budget(max_turns=2, max_dollars=10.0, max_wall_clock=None),
    )

    result = await AutonomousRunner(ctx).run(PlanFile("plan.md"), PLAN)

    assert result.success is True


async def test_diagnostics_are_optional() -> None:
    """A run must not require a logger to be wired; the null logger absorbs
    every level rather than the runner branching on whether one exists."""
    from codexloop.application.runner import _NullLogger

    null = _NullLogger()
    assert null.bind(run_id="r") is null
    for level in ("debug", "info", "warning", "error"):
        getattr(null, level)("event", key="value")
