# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""In-process system matrix: real FS/control + scripted agent + FakeClock."""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

import pytest

from codexloop.domain.control import Stop
from codexloop.domain.session import PlanFile
from codexloop.domain.signals import TurnSignals
from codexloop.domain.waiting import WaitConfig
from codexloop.infrastructure.agent.scripted import ScriptedTurn
from tests.application.fakes import FakeClock, FakeSleeper
from tests.live.system.conftest import (
    NOW,
    SystemHarness,
    available,
    build_system_harness,
    done_turn,
)

pytestmark = pytest.mark.system

PLAN = "- [ ] Add login\n"


class _StopEnqueueingSleeper(FakeSleeper):
    def __init__(self, clock: FakeClock, harness: SystemHarness) -> None:
        super().__init__(clock)
        self._harness = harness
        self._fired = False

    async def sleep_until(self, when: datetime) -> None:
        if not self._fired:
            self._fired = True
            self._harness.control.enqueue(Stop())
        await super().sleep_until(when)


async def test_happy_complete_one_turn(git_sandbox: Path) -> None:
    h = build_system_harness(git_sandbox, turns=[done_turn()], probes=[available()])
    result = await h.runner.run(PlanFile("plan.md"), PLAN)
    assert result.success is True
    assert result.reason == "done"
    assert h.gateway.closed is True
    assert h.run_dir.state_path.is_file()


async def test_quota_topup_resumes_on_scripted_probe(git_sandbox: Path) -> None:
    quota = TurnSignals(error_code="insufficient_quota", http_status=429)
    h = build_system_harness(
        git_sandbox,
        turns=[done_turn()],
        probes=[quota] * 5 + [available()],
    )
    result = await h.runner.run(PlanFile("plan.md"), PLAN)
    assert result.success is True
    assert h.probe.calls == 6
    assert h.sleeper.requested
    ceiling = WaitConfig().quota_probe_ceiling
    cursor = NOW
    for when in h.sleeper.requested:
        assert when <= cursor + ceiling
        if when > cursor:
            cursor = when
    assert len(h.notifier.messages) == 1


async def test_seven_day_wait_runs_in_microseconds(git_sandbox: Path) -> None:
    """Simulated long wait: FakeClock advances; no wall sleep."""
    from codexloop.application.runner import AutonomousRunner, RunnerContext
    from codexloop.domain.budget import Budget
    from codexloop.domain.waiting import AdaptiveWaitPolicy, WaitConfig
    from codexloop.infrastructure.agent.scripted import ScriptedAgentGateway, ScriptedCapacityProbe
    from codexloop.infrastructure.control import FileRunControl
    from codexloop.infrastructure.lock import AdvisoryFileLock
    from codexloop.infrastructure.rundir import RunDirectory, runs_root_for
    from codexloop.infrastructure.state import FileRunStateStore
    from tests.application.fakes import FakeClock, FakeNotifier, FakeProgressReporter, FakeSleeper

    quota = TurnSignals(error_code="insufficient_quota", http_status=429)
    clock = FakeClock(NOW)
    sleeper = FakeSleeper(clock)
    run_dir = RunDirectory.create(runs_root_for(git_sandbox))
    policy = AdaptiveWaitPolicy(
        WaitConfig(
            jitter_ratio=0.0,
            quota_probe_base=timedelta(days=1),
            quota_probe_ceiling=timedelta(days=1),
            backoff_base=timedelta(days=1),
        ),
        rand=lambda: 0.0,
    )
    gateway = ScriptedAgentGateway([done_turn()])
    probe = ScriptedCapacityProbe([quota] * 7 + [available()])
    ctx = RunnerContext(
        clock=clock,
        sleeper=sleeper,
        gateway=gateway,
        probe=probe,
        store=FileRunStateStore(runs_root_for(git_sandbox)),
        control=FileRunControl(run_dir.inbox),
        lock=AdvisoryFileLock(git_sandbox / ".codexloop" / "locks"),
        notifier=FakeNotifier(),
        reporter=FakeProgressReporter(),
        budget=Budget(max_turns=None, max_dollars=None, max_wall_clock=None),
        wait_policy=policy,
        run_id=run_dir.run_id,
        cwd=str(git_sandbox),
    )
    result = await AutonomousRunner(ctx).run(PlanFile("plan.md"), PLAN)
    assert result.success is True
    assert clock.now() - NOW >= timedelta(days=7)
    assert sleeper.requested


async def test_max_wait_persists_reason_on_disk(git_sandbox: Path) -> None:
    window = TurnSignals(error_code="usage_limit_reached", http_status=429)
    h = build_system_harness(
        git_sandbox,
        turns=[],
        probes=[window],
        max_wait=timedelta(0),
    )
    result = await h.runner.run(PlanFile("plan.md"), PLAN)
    assert result.success is False
    assert result.reason == "max_wait"
    saved = h.runner._store.load(h.run_dir.run_id)  # noqa: SLF001
    assert saved is not None
    assert saved["reason"] == "max_wait"


async def test_unknown_429_emits_capacity_unknown_code(git_sandbox: Path) -> None:
    h = build_system_harness(
        git_sandbox,
        turns=[
            ScriptedTurn(
                signals=TurnSignals(error_code="some_future_code", http_status=429),
                thread_id="u1",
            ),
            done_turn(thread_id="u1"),
        ],
        probes=[available(), available()],
    )
    result = await h.runner.run(PlanFile("plan.md"), PLAN)
    assert result.success is True
    names = [event for event, _ in h.reporter.events]
    assert "capacity.unknown_code" in names


async def test_stop_mid_wait_exits_with_stop_reason(git_sandbox: Path) -> None:
    quota = TurnSignals(error_code="insufficient_quota", http_status=429)
    h = build_system_harness(
        git_sandbox,
        turns=[done_turn()],
        probes=[quota] * 20 + [available()],
    )
    h.runner._sleeper = _StopEnqueueingSleeper(h.clock, h)  # noqa: SLF001
    result = await h.runner.run(PlanFile("plan.md"), PLAN)
    assert result.success is False
    assert result.reason == "stop"
