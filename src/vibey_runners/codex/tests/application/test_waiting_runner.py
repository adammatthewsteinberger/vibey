# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Waiting-loop runner: quota top-up, window cadence, max_wait reason, unknown 429."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime, timedelta

from codexloop.application.dto import ProbeResult, RunResult, TurnOutcome
from codexloop.application.runner import AutonomousRunner, RunnerContext
from codexloop.domain.budget import Budget
from codexloop.domain.capacity import Available, QuotaExhausted, WindowExhausted
from codexloop.domain.completion import DEFAULT_DONE_MARKER
from codexloop.domain.session import PlanFile
from codexloop.domain.signals import TurnSignals
from codexloop.domain.waiting import AdaptiveWaitPolicy, WaitConfig
from tests.application.fakes import (
    FakeAgentGateway,
    FakeCapacityProbe,
    FakeClock,
    FakeNotifier,
    FakeProgressReporter,
    FakeRunControl,
    FakeRunStateStore,
    FakeSleeper,
)

NOW = datetime(2026, 8, 13, 12, 0, tzinfo=UTC)
PLAN = "- [ ] Add login\n- [ ] Add logout\n"
THREAD_ID = "thr_wait"
ZERO_JITTER = AdaptiveWaitPolicy(WaitConfig(jitter_ratio=0.0), rand=lambda: 0.0)
QUOTA_CEILING = WaitConfig().quota_probe_ceiling
WINDOW_INTERVAL = WaitConfig().window_probe_interval


def _done(*, thread_id: str = THREAD_ID) -> TurnOutcome:
    return TurnOutcome(
        thread_id=thread_id,
        signals=TurnSignals(final_message=DEFAULT_DONE_MARKER),
    )


def _ctx(
    *,
    outcomes: Sequence[TurnOutcome],
    probes: ProbeResult | Sequence[ProbeResult],
    notifier: FakeNotifier | None = None,
    reporter: FakeProgressReporter | None = None,
    store: FakeRunStateStore | None = None,
    max_wait: timedelta | None = None,
    run_id: str = "anonymous",
    clock: FakeClock | None = None,
) -> tuple[
    RunnerContext,
    FakeAgentGateway,
    FakeClock,
    FakeSleeper,
    FakeCapacityProbe,
    FakeRunStateStore,
]:
    clock = clock or FakeClock(NOW)
    sleeper = FakeSleeper(clock)
    gateway = FakeAgentGateway(outcomes)
    probe = FakeCapacityProbe(probes)
    store_obj = store or FakeRunStateStore()
    ctx = RunnerContext(
        clock=clock,
        sleeper=sleeper,
        gateway=gateway,
        probe=probe,
        store=store_obj,
        control=FakeRunControl(),
        budget=Budget(max_turns=None, max_dollars=None, max_wall_clock=None),
        wait_policy=ZERO_JITTER,
        max_wait=max_wait,
        run_id=run_id,
        notifier=notifier,
        reporter=reporter,
    )
    return ctx, gateway, clock, sleeper, probe, store_obj


async def test_resumes_when_a_human_tops_up_credit_mid_wait() -> None:
    quota = ProbeResult(outcome=QuotaExhausted(reason="insufficient_quota"))
    available = ProbeResult(outcome=Available())
    notifier = FakeNotifier()
    ctx, gateway, clock, sleeper, probe, _store = _ctx(
        outcomes=[_done()],
        probes=[quota] * 5 + [available],
        notifier=notifier,
    )

    result = await AutonomousRunner(ctx).run(PlanFile("plan.md"), PLAN)

    assert result.success is True
    assert probe.calls == 6
    assert gateway.sent_prompts == [PLAN]
    cursor = NOW
    for when in sleeper.requested:
        assert when <= cursor + QUOTA_CEILING
        if when > cursor:
            cursor = when
    assert notifier.messages
    assert len(notifier.messages) == 1
    assert clock.now() >= sleeper.requested[-1]


async def test_window_exhausted_probes_at_interval_not_five_hour_sleep() -> None:
    reset_at = NOW + timedelta(hours=5)
    ctx, gateway, clock, sleeper, _probe, _store = _ctx(
        outcomes=[_done()],
        probes=[
            ProbeResult(outcome=WindowExhausted(resets_at=reset_at, window="five_hour")),
            ProbeResult(outcome=Available()),
        ],
    )

    result = await AutonomousRunner(ctx).run(PlanFile("plan.md"), PLAN)

    assert result.success is True
    assert sleeper.requested
    # _sleep_interruptible polls every 1 second, so first sleep is 1s, not full interval
    assert sleeper.requested[0] <= NOW + WINDOW_INTERVAL
    assert sleeper.requested[0] > NOW  # Should have slept at least once
    assert clock.now() < reset_at
    assert gateway.sent_prompts == [PLAN]


async def test_max_wait_deadline_persists_reason_in_run_state() -> None:
    store = FakeRunStateStore()
    ctx, gateway, _clock, _sleeper, _probe, store_obj = _ctx(
        outcomes=[],
        probes=ProbeResult(outcome=WindowExhausted()),
        store=store,
        max_wait=timedelta(0),
        run_id="run-deadline",
    )

    result = await AutonomousRunner(ctx).run(PlanFile("plan.md"), PLAN)

    assert result == RunResult(success=False, reason="max_wait", turns=0, thread_id=None)
    assert gateway.sent_prompts == []
    saved = store_obj.load("run-deadline")
    assert saved is not None
    assert saved["reason"] == "max_wait"


async def test_unknown_code_429_bounded_wait_and_reports() -> None:
    reporter = FakeProgressReporter()
    ctx, gateway, _clock, sleeper, probe, _store = _ctx(
        outcomes=[
            TurnOutcome(
                thread_id=THREAD_ID,
                signals=TurnSignals(error_code="some_future_code", http_status=429),
            ),
            _done(),
        ],
        probes=[
            ProbeResult(outcome=Available()),
            ProbeResult(outcome=Available()),
        ],
        reporter=reporter,
    )

    result = await AutonomousRunner(ctx).run(PlanFile("plan.md"), PLAN)

    assert result.success is True
    assert sleeper.requested
    cursor = NOW
    for when in sleeper.requested:
        assert when <= cursor + QUOTA_CEILING
        if when > cursor:
            cursor = when
    # _sleep_interruptible polls every 1 second, so first sleep is 1s, not full base
    assert sleeper.requested[0] <= NOW + WaitConfig().quota_probe_base
    assert sleeper.requested[0] > NOW  # Should have slept at least once
    names = [event for event, _detail in reporter.events]
    assert "capacity.unknown_code" in names
    unknown = next(detail for event, detail in reporter.events if event == "capacity.unknown_code")
    assert unknown["code"] == "some_future_code"
    assert probe.calls >= 2
    assert len(gateway.sent_prompts) == 2


async def test_known_error_code_does_not_emit_unknown_event() -> None:
    reporter = FakeProgressReporter()
    ctx, gateway, _clock, sleeper, _probe, _store = _ctx(
        outcomes=[
            TurnOutcome(
                thread_id=THREAD_ID,
                signals=TurnSignals(error_code="insufficient_quota", http_status=429),
            ),
            _done(),
        ],
        probes=[
            ProbeResult(outcome=Available()),
            ProbeResult(outcome=Available()),
        ],
        reporter=reporter,
    )

    result = await AutonomousRunner(ctx).run(PlanFile("plan.md"), PLAN)

    assert result.success is True
    assert sleeper.requested
    assert "capacity.unknown_code" not in [event for event, _detail in reporter.events]
    assert len(gateway.sent_prompts) == 2
