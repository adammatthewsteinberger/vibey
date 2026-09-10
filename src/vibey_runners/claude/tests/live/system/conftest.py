# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Shared helpers for system-live tests (real adapters + scripted/fake agent)."""

from __future__ import annotations

import subprocess  # nosec B404 - fixed-argument git init only
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import pytest

from claudeloop.application.runner import AutonomousRunner
from claudeloop.domain.budget import Budget
from claudeloop.domain.waiting import WaitPolicyConfig
from claudeloop.infrastructure.agent.scripted import ScriptedAgentGateway, ScriptedCapacityProbe
from claudeloop.infrastructure.agent.scripted import ScriptedTurn as InfraScriptedTurn
from claudeloop.infrastructure.audit import JsonlAuditLog
from claudeloop.infrastructure.control import FileRunControl
from claudeloop.infrastructure.events import JsonlRunEventSink
from claudeloop.infrastructure.git_savepoints import GitSavePointStore
from claudeloop.infrastructure.lock import FileSessionLock
from claudeloop.infrastructure.notify import StderrNotifier
from claudeloop.infrastructure.progress import ConsoleProgressReporter
from claudeloop.infrastructure.resources.adapter import ResourcePortAdapter
from claudeloop.infrastructure.resources.store import RunResourceStore
from claudeloop.infrastructure.rundir import RunDirectory, runs_root_for
from claudeloop.infrastructure.snapshot import RunSnapshotBuilder
from claudeloop.infrastructure.state import FileRunStateStore
from claudeloop.infrastructure.state_bus import FileStateBus
from tests.application.fakes import FakeClock, FakeLogger, FakeSleeper, ScriptedTurn

NOW = datetime(2026, 8, 12, 15, 0, tzinfo=timezone.utc)


@pytest.fixture
def git_sandbox(tmp_path: Path) -> Path:
    repo = tmp_path / "sandbox"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "claudeloop-system@example.com"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "claudeloop system"],
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
    clock: FakeClock
    sleeper: object
    run_id: str
    resources: ResourcePortAdapter


def build_system_harness(
    cwd: Path,
    *,
    turns: list[ScriptedTurn],
    probes: list,
    budget: Budget | None = None,
    wait_policy: WaitPolicyConfig | None = None,
    clock: FakeClock | None = None,
    sleeper: object | None = None,
) -> SystemHarness:
    """Compose AutonomousRunner with real FS/git/control + scripted agent."""
    clock = clock or FakeClock(start=NOW)
    sleeper = sleeper or FakeSleeper(clock)
    run_dir = RunDirectory.create(runs_root_for(cwd), cwd=cwd)
    run_id = run_dir.read_meta().run_id
    event_sink = JsonlRunEventSink(run_dir.events_path, run_id=run_id)
    resource_store = RunResourceStore(run_dir.resources_root)
    resource_store.ensure()
    resources = ResourcePortAdapter(resource_store)

    infra_turns = [
        InfraScriptedTurn(
            signals=t.signals,
            verdict=t.verdict,
            output_text=t.output_text,
            session_id=t.session_id,
            cost_usd=t.cost_usd,
            raw_events=getattr(t, "raw_events", ()),
        )
        for t in turns
    ]
    gateway = ScriptedAgentGateway(
        infra_turns,
        on_event=lambda e: event_sink.emit("sdk.message", e),
    )
    probe = ScriptedCapacityProbe(list(probes))
    control = FileRunControl(run_dir.inbox)
    save_points = GitSavePointStore(cwd=cwd, index_path=run_dir.savepoints_path)
    state_bus = FileStateBus(
        status_path=run_dir.root / "status.json",
        bus_path=run_dir.root / "bus.jsonl",
        run_id=run_id,
    )
    snapshot_sink = RunSnapshotBuilder(run_dir, state_bus=state_bus, clock=clock)

    runner = AutonomousRunner(
        agent_gateway=gateway,
        capacity_probe=probe,
        clock=clock,
        sleeper=sleeper,
        audit_log=JsonlAuditLog(run_dir.root / "audit.jsonl", run_id=run_id),
        progress=ConsoleProgressReporter(),
        budget=budget or Budget(),
        wait_policy=wait_policy or WaitPolicyConfig(),
        done_marker="TEST_DONE_MARKER",
        run_id=run_id,
        notifier=StderrNotifier(),
        run_control=control,
        event_sink=event_sink,
        state_store=FileRunStateStore(cwd / ".claudeloop" / "state"),
        session_lock=FileSessionLock(cwd / ".claudeloop" / "locks"),
        save_points=save_points,
        stop_summary_writer=run_dir.write_stop_summary,
        meta_updater=lambda **kwargs: run_dir.update_meta(**kwargs),
        events_path=str(run_dir.events_path),
        state_bus=state_bus,
        logger=FakeLogger(),
        run_resources=resources,
        snapshot_sink=snapshot_sink,
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
        resources=resources,
    )
