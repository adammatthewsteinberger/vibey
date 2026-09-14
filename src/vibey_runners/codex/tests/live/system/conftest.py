# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Shared helpers for system-live tests (real adapters + scripted agent)."""

from __future__ import annotations

import subprocess  # nosec B404 — fixed-argument git init only
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from codexloop.application.runner import AutonomousRunner, RunnerContext
from codexloop.domain.budget import Budget
from codexloop.domain.completion import DEFAULT_DONE_MARKER
from codexloop.domain.signals import TurnSignals
from codexloop.domain.waiting import AdaptiveWaitPolicy, WaitConfig
from codexloop.infrastructure.agent.scripted import (
    ScriptedAgentGateway,
    ScriptedCapacityProbe,
    ScriptedTurn,
)
from codexloop.infrastructure.control import FileRunControl
from codexloop.infrastructure.lock import AdvisoryFileLock
from codexloop.infrastructure.rundir import RunDirectory, runs_root_for
from codexloop.infrastructure.state import FileRunStateStore
from tests.application.fakes import FakeClock, FakeNotifier, FakeProgressReporter, FakeSleeper

NOW = datetime(2026, 8, 13, 15, 0, tzinfo=UTC)
ZERO_WAIT = AdaptiveWaitPolicy(
    WaitConfig(
        jitter_ratio=0.0,
        quota_probe_base=timedelta(seconds=120),
        quota_probe_ceiling=timedelta(seconds=600),
        window_probe_interval=timedelta(seconds=60),
        grace=timedelta(seconds=2),
        backoff_base=timedelta(seconds=1),
    ),
    rand=lambda: 0.0,
)


@pytest.fixture
def git_sandbox(tmp_path: Path) -> Path:
    repo = tmp_path / "sandbox"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "codexloop-system@example.com"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "codexloop system"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    (repo / "README.md").write_text("sandbox\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=repo, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-q", "-m", "init"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    return repo


@dataclass
class SystemHarness:
    cwd: Path
    runner: AutonomousRunner
    run_dir: RunDirectory
    control: FileRunControl
    gateway: ScriptedAgentGateway
    probe: ScriptedCapacityProbe
    clock: FakeClock
    sleeper: FakeSleeper
    notifier: FakeNotifier
    reporter: FakeProgressReporter


def available() -> TurnSignals:
    return TurnSignals()


def done_turn(*, thread_id: str = "scripted") -> ScriptedTurn:
    return ScriptedTurn(
        signals=TurnSignals(final_message=DEFAULT_DONE_MARKER),
        thread_id=thread_id,
    )


def build_system_harness(
    cwd: Path,
    *,
    turns: list[ScriptedTurn],
    probes: list[TurnSignals],
    max_wait: timedelta | None = None,
    clock: FakeClock | None = None,
) -> SystemHarness:
    clock = clock or FakeClock(NOW)
    sleeper = FakeSleeper(clock)
    run_dir = RunDirectory.create(runs_root_for(cwd))
    control = FileRunControl(run_dir.inbox)
    gateway = ScriptedAgentGateway(turns)
    probe = ScriptedCapacityProbe(probes)
    notifier = FakeNotifier()
    reporter = FakeProgressReporter()
    ctx = RunnerContext(
        clock=clock,
        sleeper=sleeper,
        gateway=gateway,
        probe=probe,
        store=FileRunStateStore(runs_root_for(cwd)),
        control=control,
        lock=AdvisoryFileLock(cwd / ".codexloop" / "locks"),
        notifier=notifier,
        reporter=reporter,
        budget=Budget(max_turns=None, max_dollars=None, max_wall_clock=None),
        wait_policy=ZERO_WAIT,
        max_wait=max_wait,
        run_id=run_dir.run_id,
        cwd=str(cwd),
        model="gpt-5",
    )
    return SystemHarness(
        cwd=cwd,
        runner=AutonomousRunner(ctx),
        run_dir=run_dir,
        control=control,
        gateway=gateway,
        probe=probe,
        clock=clock,
        sleeper=sleeper,
        notifier=notifier,
        reporter=reporter,
    )
