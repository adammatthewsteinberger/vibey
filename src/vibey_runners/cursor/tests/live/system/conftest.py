# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Deterministic system-live harness: real FS adapters + scripted agent + FakeClock."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path

import anyio
import pytest

from cursorloop.application.runner import AutonomousRunner, RunnerContext
from cursorloop.application.usecases.run_plan import run_from_plan_file
from cursorloop.cli.render import exit_code_for
from cursorloop.domain.budget import Budget
from cursorloop.domain.control import Stop
from cursorloop.domain.waiting import DEFAULT_WAIT_POLICY_CONFIG
from cursorloop.infrastructure.agent.scripted import (
    ScriptedAgentGateway,
    ScriptedCapacityProbe,
    load_agent_script,
)
from cursorloop.infrastructure.audit import JsonlAuditLog
from cursorloop.infrastructure.control import FileRunControl
from cursorloop.infrastructure.events import JsonlRunEventSink
from cursorloop.infrastructure.lock import FileAgentLock
from cursorloop.infrastructure.logging import NullAppLogger
from cursorloop.infrastructure.notify import StderrNotifier
from cursorloop.infrastructure.progress import ConsoleProgressReporter
from cursorloop.infrastructure.rundir import RunDirectory, runs_root_for
from cursorloop.infrastructure.state import FileRunStateStore
from tests.application import fakes

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "agent_scripts"


@dataclass
class SystemResult:
    exit_code: int
    stdout: str
    reason: str


@dataclass
class SystemEnv:
    workspace: Path
    clock: fakes.FakeClock
    sleeper: fakes.FakeSleeper
    run_dir: RunDirectory | None = None

    def audit_events(self) -> list[dict[object, object]]:
        assert self.run_dir is not None
        lines = self.run_dir.audit_path.read_text(encoding="utf-8").splitlines()
        return [json.loads(line) for line in lines if line.strip()]

    def run_events(self) -> list[dict[object, object]]:
        assert self.run_dir is not None
        lines = self.run_dir.events_path.read_text(encoding="utf-8").splitlines()
        return [json.loads(line) for line in lines if line.strip()]

    def state(self) -> dict[str, object]:
        assert self.run_dir is not None
        store = FileRunStateStore(self.workspace / ".cursorloop")
        loaded = store.load(self.run_dir.read_meta().run_id)
        return loaded or {}

    def hooks_restored(self) -> bool:
        return True

    async def _run_async(
        self,
        script: str,
        *,
        max_wait: str | None = None,
        pre_enqueue_stop: bool = False,
    ) -> SystemResult:
        agent_script = load_agent_script(FIXTURES / script)
        plan = self.workspace / "plan.md"
        # No open checkboxes — Done verdicts must not be reconciled back to Continue.
        plan.write_text("# Goal\n\n- [x] finish the work\n", encoding="utf-8")
        self.run_dir = RunDirectory.create(
            runs_root_for(self.workspace), cwd=self.workspace, plan_path=plan
        )
        run_id = self.run_dir.read_meta().run_id
        trace_id = "test-trace-id"
        control = FileRunControl(self.run_dir.inbox)
        if pre_enqueue_stop:
            control.enqueue(Stop())

        wait = DEFAULT_WAIT_POLICY_CONFIG
        if max_wait is not None:
            seconds = float(max_wait.rstrip("s"))
            wait = wait.with_max_wait(timedelta(seconds=seconds))

        event_sink = JsonlRunEventSink(self.run_dir.events_path, run_id=run_id, trace_id=trace_id)

        def _forward_event_to_sink(event: dict[str, object]) -> None:
            """Adapt scripted agent's dict-format events to RunEventSink.emit calls."""
            event_dict = dict(event)
            event_type = event_dict.pop("type", "unknown")
            if not isinstance(event_type, str):
                event_type = str(event_type)
            payload = dict(event_dict.items())
            event_sink.emit(event_type, payload)

        class _NullHooks:
            def install(self) -> None:
                return None

            def restore(self) -> bool:
                return True

            def is_installed(self) -> bool:
                return False

        ctx = RunnerContext(
            gateway=ScriptedAgentGateway(list(agent_script.turns), on_event=_forward_event_to_sink),
            probe=ScriptedCapacityProbe(list(agent_script.probes)),
            clock=self.clock,
            sleeper=self.sleeper,
            reporter=ConsoleProgressReporter(),
            audit=JsonlAuditLog(self.run_dir.audit_path, run_id=run_id),
            notifier=StderrNotifier(),
            logger=NullAppLogger(),
            hooks=_NullHooks(),
            lock=FileAgentLock(self.workspace / ".cursorloop" / "locks"),
            store=FileRunStateStore(self.workspace / ".cursorloop"),
            control=control,
            budget=Budget(max_turns=20),
            wait_policy=wait,
            run_id=run_id,
        )
        result = await run_from_plan_file(AutonomousRunner(ctx), plan)
        return SystemResult(
            exit_code=exit_code_for(result),
            stdout=result.reason,
            reason=result.reason,
        )

    def run(
        self,
        script: str,
        *,
        max_wait: str | None = None,
        stop_after_seconds: float | None = None,
    ) -> SystemResult:
        return anyio.run(
            lambda: self._run_async(
                script,
                max_wait=max_wait,
                pre_enqueue_stop=stop_after_seconds is not None,
            )
        )


@pytest.fixture
def system_env(tmp_path: Path) -> SystemEnv:
    clock = fakes.FakeClock()
    sleeper = fakes.FakeSleeper(clock)
    return SystemEnv(workspace=tmp_path, clock=clock, sleeper=sleeper)
