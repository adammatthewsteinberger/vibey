# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""In-process system harness: real rundir/control/git + scripted agent."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from agyloop.application.runner import AutonomousRunner
from agyloop.domain.budget import Budget
from agyloop.domain.waiting import WaitPolicyConfig
from agyloop.infrastructure.control import FileRunControl
from agyloop.infrastructure.notify import StderrNotifier
from agyloop.infrastructure.rundir import RunDirectory, runs_root_for
from tests.application.fakes import (
    FakeAgentGateway,
    FakeAuditLog,
    FakeCapacityProbe,
    FakeClock,
    FakeProgressReporter,
    FakeSleeper,
    ScriptedTurn,
)

NOW = datetime(2026, 8, 13, 18, 0, tzinfo=UTC)


@dataclass
class SystemHarness:
    cwd: Path
    runner: AutonomousRunner
    run_dir: RunDirectory
    control: FileRunControl
    gateway: FakeAgentGateway
    clock: FakeClock
    sleeper: FakeSleeper
    run_id: str


def build_system_harness(
    cwd: Path,
    *,
    turns: list[ScriptedTurn],
    probes: list,
    budget: Budget | None = None,
    wait_policy: WaitPolicyConfig | None = None,
    clock: FakeClock | None = None,
    sleeper: FakeSleeper | None = None,
) -> SystemHarness:
    """Compose AutonomousRunner with real FS/control adapters and a scripted agent."""
    clock = clock or FakeClock(start=NOW)
    sleeper = sleeper or FakeSleeper(clock)
    run_dir = RunDirectory.create(runs_root_for(cwd), cwd=cwd)
    run_id = run_dir.read_meta().run_id
    gateway = FakeAgentGateway(turns)
    probe = FakeCapacityProbe(list(probes))
    control = FileRunControl(run_dir.inbox)
    runner = AutonomousRunner(
        agent_gateway=gateway,
        capacity_probe=probe,
        clock=clock,
        sleeper=sleeper,
        audit_log=FakeAuditLog(),
        progress=FakeProgressReporter(),
        budget=budget or Budget(),
        wait_policy=wait_policy or WaitPolicyConfig(),
        done_marker="AGYLOOP_TASK_FULLY_COMPLETE",
        run_id=run_id,
        notifier=StderrNotifier(),
        run_control=control,
        meta_updater=run_dir.update_meta,
    )
    return SystemHarness(
        cwd=cwd,
        runner=runner,
        run_dir=run_dir,
        control=control,
        gateway=gateway,
        clock=clock,
        sleeper=sleeper,
        run_id=run_id,
    )
