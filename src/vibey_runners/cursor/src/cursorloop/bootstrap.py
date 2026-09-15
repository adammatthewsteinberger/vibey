# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Composition root — the only module permitted to know about every layer.

Wires concrete infrastructure adapters into application ports and hands the
assembled runner to cli/. Nothing outside this file should import both a port
from application/ and its concrete infrastructure implementation.
"""

from __future__ import annotations

import os
import uuid
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path
from typing import Any

from cursorloop.application.ports import AgentCatalog, AgentGateway, CapacityProbe, HookManager
from cursorloop.application.runner import AutonomousRunner, RunnerContext
from cursorloop.domain.budget import Budget
from cursorloop.domain.model_profile import SHIPPED_PRESETS, ModelProfile
from cursorloop.domain.verbosity import LogPlan
from cursorloop.domain.waiting import DEFAULT_WAIT_POLICY_CONFIG
from cursorloop.infrastructure.agent.bridge import LiveBridge, open_live_bridge
from cursorloop.infrastructure.agent.catalog import CursorAgentCatalog
from cursorloop.infrastructure.agent.gateway import CursorAgentGateway
from cursorloop.infrastructure.agent.hooks import ManagedHooks
from cursorloop.infrastructure.agent.probe import CursorCapacityProbe
from cursorloop.infrastructure.agent.scripted import resolve_test_agent_from_env
from cursorloop.infrastructure.agent.watchdog import TurnWatchdog
from cursorloop.infrastructure.audit import JsonlAuditLog
from cursorloop.infrastructure.clock import AnyioSleeper, SystemClock
from cursorloop.infrastructure.config import RunnerConfig
from cursorloop.infrastructure.control import FileRunControl
from cursorloop.infrastructure.events import JsonlRunEventSink
from cursorloop.infrastructure.lock import FileAgentLock
from cursorloop.infrastructure.logging import (
    StructlogAppLogger,
    apply_third_party_level,
    configure_logging,
)
from cursorloop.infrastructure.notify import StderrNotifier
from cursorloop.infrastructure.progress import ConsoleProgressReporter
from cursorloop.infrastructure.rundir import RunDirectory, runs_root_for
from cursorloop.infrastructure.state import FileRunStateStore


class _NullHooks:
    def install(self) -> None:
        return None

    def restore(self) -> bool:
        return False

    def is_installed(self) -> bool:
        return False


@dataclass(frozen=True, slots=True)
class BuiltRunner:
    runner: AutonomousRunner
    gateway: AgentGateway
    run_dir: RunDirectory
    run_id: str
    trace_id: str
    bridge: LiveBridge | None = None

    def close(self) -> None:
        """Release the SDK bridge client when bootstrap owns it."""
        if self.bridge is not None:
            self.bridge.close()


def resolve_profile(config: RunnerConfig) -> ModelProfile:
    if config.model and config.model in SHIPPED_PRESETS:
        return SHIPPED_PRESETS[config.model]
    if config.model:
        return ModelProfile(model_id=config.model)
    return SHIPPED_PRESETS["composer"]


def build_runner(
    *,
    cwd: Path,
    config: RunnerConfig,
    plan_path: Path | None = None,
    resume_agent_id: str | None = None,
    client: Any | None = None,
    launch_bridge: Any | None = None,
    run_id: str | None = None,
) -> BuiltRunner:
    """Assemble an AutonomousRunner for a fresh or resumed run.

    When the scripted test-agent gate is off and no ``client`` is supplied,
    launches ``CursorClient.launch_bridge(workspace=…)`` automatically.
    """
    run_dir = RunDirectory.create(runs_root_for(cwd), cwd=cwd, plan_path=plan_path, run_id=run_id)
    # Rebind to the resolved id: identical to the supplied one when the caller
    # named the run, the freshly minted one otherwise.
    run_id = run_dir.read_meta().run_id
    trace_id = str(uuid.uuid4())
    state_root = cwd / ".cursorloop"
    state_root.mkdir(parents=True, exist_ok=True)

    configure_logging(
        log_file=Path(config.log_file) if config.log_file else None,
        level=config.log_level,
    )

    clock = SystemClock()
    sleeper = AnyioSleeper(clock)
    event_sink = JsonlRunEventSink(run_dir.events_path, run_id=run_id, trace_id=trace_id)
    audit = JsonlAuditLog(run_dir.audit_path, run_id=run_id)
    profile = resolve_profile(config)

    def _forward_event_to_sink(event: dict[str, object]) -> None:
        """Adapt scripted agent's dict-format events to RunEventSink.emit calls."""
        event_dict = dict(event)
        event_type = event_dict.pop("type", "unknown")
        if not isinstance(event_type, str):
            event_type = str(event_type)
        payload = dict(event_dict.items())
        event_sink.emit(event_type, payload)

    scripted = resolve_test_agent_from_env(on_event=_forward_event_to_sink)
    gateway: AgentGateway
    probe: CapacityProbe
    bridge: LiveBridge | None = None
    if scripted is not None:
        gateway, probe = scripted
    else:
        if not config.api_key and client is None and not os.environ.get("CURSOR_API_KEY"):
            raise RuntimeError(
                "CURSOR_API_KEY is unset. Export it from the Cursor dashboard, "
                "or enable the test-agent gate "
                "(CURSORLOOP_ALLOW_TEST_AGENT=1 and CURSORLOOP_TEST_AGENT_SCRIPT)."
            )
        bridge = open_live_bridge(
            workspace=cwd,
            profile=profile,
            api_key=config.api_key,
            resume_agent_id=resume_agent_id,
            client=client,
            launch_bridge=launch_bridge,
        )
        watchdog = TurnWatchdog(
            turn_timeout=timedelta(
                seconds=config.turn_timeout_seconds
                if config.turn_timeout_seconds is not None
                else 30 * 60
            ),
            stall_timeout=timedelta(
                seconds=config.stall_timeout_seconds
                if config.stall_timeout_seconds is not None
                else 10 * 60
            ),
            clock=clock,
        )
        gateway = CursorAgentGateway(
            client=bridge.client,
            agent=bridge.agent,
            profile=profile,
            watchdog=watchdog,
            event_sink=event_sink,
        )
        probe = CursorCapacityProbe(str(cwd), profile, client=bridge.client)

    hooks: HookManager
    if config.managed_hooks:
        hooks = ManagedHooks(workspace=cwd, state_dir=state_root)
    else:
        hooks = _NullHooks()

    wait_policy = DEFAULT_WAIT_POLICY_CONFIG
    if config.max_wait_seconds is not None:
        wait_policy = wait_policy.with_max_wait(timedelta(seconds=config.max_wait_seconds))

    budget = Budget(
        max_turns=config.max_turns,
        max_cost_usd=config.max_dollars,
    )

    ctx = RunnerContext(
        gateway=gateway,
        probe=probe,
        clock=clock,
        sleeper=sleeper,
        reporter=ConsoleProgressReporter(),
        audit=audit,
        notifier=StderrNotifier(),
        logger=StructlogAppLogger(run_id=run_id, trace_id=trace_id),
        hooks=hooks,
        lock=FileAgentLock(state_root / "locks"),
        store=FileRunStateStore(state_root),
        control=FileRunControl(run_dir.inbox),
        budget=budget,
        wait_policy=wait_policy,
        run_id=run_id,
        handoff_marker_writer=run_dir.write_handoff_marker,
    )
    return BuiltRunner(
        runner=AutonomousRunner(ctx),
        gateway=gateway,
        run_dir=run_dir,
        run_id=run_id,
        trace_id=trace_id,
        bridge=bridge,
    )


def build_catalog(*, client: Any) -> AgentCatalog:
    return CursorAgentCatalog(client)


def configure_cli_logging(*, plan: LogPlan, log_file: Path | None = None) -> None:
    """Apply the resolved -v / -q / --log-level plan to this process."""
    configure_logging(log_file=log_file, level=plan.level)
    apply_third_party_level(plan)
