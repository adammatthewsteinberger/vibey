# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Composition root — the only module permitted to know about every layer at
once. Wires concrete infrastructure adapters into application ports and hands
the assembled AutonomousRunner (or a lighter-weight use-case dependency) to
cli/. Nothing outside this file should import both a port name from
application/ports.py and its concrete infrastructure implementation."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import click

from claudeloop.application.interfaces import DoctorEnvironment
from claudeloop.application.ports import AgentGateway, CapacityProbe, StreamUi
from claudeloop.application.runner import AutonomousRunner
from claudeloop.domain.budget import Budget
from claudeloop.domain.control import SlashCommand
from claudeloop.domain.permission import parse_user_permission_mode
from claudeloop.domain.plan import WorkPlan
from claudeloop.domain.verbosity import LogPlan
from claudeloop.domain.waiting import ProgressWaitConfig, WaitPolicyConfig
from claudeloop.infrastructure.agent.catalog import SdkSessionCatalog
from claudeloop.infrastructure.agent.gateway import ClaudeAgentGateway, ClaudeCapacityProbe
from claudeloop.infrastructure.agent.scripted import resolve_test_agent_from_env
from claudeloop.infrastructure.audit import JsonlAuditLog
from claudeloop.infrastructure.chatter_log import summarize_tool
from claudeloop.infrastructure.clock import AnyioSleeper, SystemClock
from claudeloop.infrastructure.config import RunnerConfig
from claudeloop.infrastructure.control import FileRunControl
from claudeloop.infrastructure.doctor_env import RealDoctorEnvironment
from claudeloop.infrastructure.events import JsonlRunEventSink
from claudeloop.infrastructure.git_savepoints import GitSavePointStore
from claudeloop.infrastructure.lock import FileSessionLock
from claudeloop.infrastructure.logging import (
    StructlogAppLogger,
    apply_third_party_level,
    configure_logging,
    get_logger,
)
from claudeloop.infrastructure.notify import StderrNotifier
from claudeloop.infrastructure.progress import ConsoleProgressReporter
from claudeloop.infrastructure.resources.adapter import ResourcePortAdapter
from claudeloop.infrastructure.resources.store import RunResourceStore
from claudeloop.infrastructure.rundir import RunDirectory, runs_root_for
from claudeloop.infrastructure.snapshot import RunSnapshotBuilder
from claudeloop.infrastructure.state import FileRunStateStore
from claudeloop.infrastructure.state_bus import FileStateBus


@dataclass(frozen=True, slots=True)
class RunnerContext:
    runner: AutonomousRunner
    gateway: AgentGateway
    run_dir: RunDirectory
    run_id: str
    trace_id: str


def build_runner(
    *,
    cwd: Path,
    config: RunnerConfig,
    session_id: str | None = None,
    resume: str | None = None,
    continue_conversation: bool = False,
    log_file: Path | None = None,
    plan: WorkPlan | None = None,
    plan_path: Path | None = None,
    stream_ui: StreamUi | None = None,
    attach: list[Path] | None = None,
    add_folders: list[Path] | None = None,
    skills: list[str] | None = None,
    plugins: list[str] | None = None,
    connectors: dict[str, Any] | None = None,
    from_github: str | None = None,
    import_issue: str | None = None,
    slash: str | None = None,
    run_id: str | None = None,
    append_system_prompt: str | None = None,
    wind_down_at: datetime | None = None,
) -> RunnerContext:
    run_dir = RunDirectory.create(runs_root_for(cwd), cwd=cwd, plan_path=plan_path, run_id=run_id)
    run_id = run_dir.read_meta().run_id
    trace_id = str(uuid.uuid4())
    profile = config.resolved_profile()
    log_chatter = config.effective_log_chatter()
    include_partial = config.effective_partial_messages()
    permission_mode = parse_user_permission_mode(config.permission_mode)

    resource_store = RunResourceStore(run_dir.resources_root)
    resource_store.ensure()
    resource_store.set_flag(
        permission_mode=permission_mode,
        cwd=str(cwd.resolve()),
        web_search=config.web_search,
        deep_research=config.deep_research,
        cli_system_prompt_append=append_system_prompt or "",
    )
    for path in attach or []:
        resource_store.attach(path)
    for folder in add_folders or []:
        resource_store.add_folder(str(folder))
    for skill in skills or []:
        resource_store.add_skill(skill)
    for plugin in plugins or []:
        resource_store.add_plugin(plugin)
    for name, cfg in (connectors or {}).items():
        resource_store.set_connector(name, cfg if isinstance(cfg, dict) else {"url": str(cfg)})
    resources = ResourcePortAdapter(resource_store)
    if from_github:
        resources.apply_mutate(action="add", kind="github", value=from_github)
    if import_issue:
        resources.apply_mutate(action="add", kind="issue", value=import_issue)

    event_sink = JsonlRunEventSink(run_dir.events_path, run_id=run_id, trace_id=trace_id)
    event_sink.bind(trace_id=trace_id)
    delta_seq = {"n": 0}
    ui = stream_ui

    def _on_event(event: dict[str, object]) -> None:
        if event.get("chatter") == "delta" or (
            event.get("type") == "StreamEvent" and event.get("delta_text")
        ):
            delta_seq["n"] += 1
            text = str(event.get("delta_text") or "")
            turn_id = str(event.get("turn_id") or "")
            seq_raw = event.get("seq")
            seq = int(seq_raw) if isinstance(seq_raw, int) else delta_seq["n"]
            payload = {
                "text": text,
                "seq": seq,
            }
            event_sink.emit("chatter.delta", payload)
            if ui is not None:
                ui.on_delta(text, turn_id=turn_id, seq=seq)
            return
        tools_raw = event.get("tools")
        if event.get("type") == "AssistantMessage" and isinstance(tools_raw, list):
            mode = log_chatter
            for tool in tools_raw:
                if isinstance(tool, dict):
                    name = str(tool.get("name") or "tool")
                    summarized = summarize_tool(name, tool, mode=mode)
                    if summarized is not None:
                        event_sink.emit("chatter.tool", summarized)
                        if ui is not None:
                            ui.on_tool(name, str(summarized.get("preview") or name))
        event_sink.emit("sdk.message", event)

    # Test-only: CLAUDELOOP_ALLOW_TEST_AGENT=1 + CLAUDELOOP_TEST_AGENT_SCRIPT
    # swap the real Claude adapters for a JSON-scripted pair. Never a user feature.
    scripted = resolve_test_agent_from_env(on_event=_on_event)
    gateway: AgentGateway
    probe: CapacityProbe
    app_log = StructlogAppLogger(component="bootstrap", run_id=run_id, trace_id=trace_id)
    if scripted is not None:
        gateway, probe = scripted
        app_log.warning(
            "test_agent.active",
            detail="CLAUDELOOP_TEST_AGENT_SCRIPT is active — not for production",
        )
    else:
        snap = resource_store.snapshot()
        gw_payload = resources.gateway_payload()
        gateway = ClaudeAgentGateway(
            cwd=str(cwd),
            session_id=session_id,
            resume=resume,
            continue_conversation=continue_conversation,
            max_turns=config.max_turns,
            max_budget_usd=config.max_dollars,
            retry_watchdog=config.retry_watchdog,
            model=profile.model,
            effort=profile.effort,
            on_event=_on_event,
            max_buffer_size=config.max_buffer_size,
            include_partial_messages=include_partial,
            permission_mode=permission_mode,
            add_dirs=list(snap.folders),
            skills=list(snap.skills) or None,
            plugins=list(snap.plugins),
            mcp_servers=dict(snap.connectors) or None,
            system_prompt_append=str(gw_payload.get("system_prompt_append") or ""),
            allowed_tools=list(gw_payload.get("allowed_tools") or []) or None,
            tool_approval_timeout=config.tool_approval_timeout_seconds,
        )
        probe = ClaudeCapacityProbe(
            cwd=str(cwd),
            on_event=_on_event,
            max_buffer_size=config.max_buffer_size,
            model=profile.model,
        )
    app_log.info(
        "runner.config",
        max_turns=config.max_turns,
        max_dollars=config.max_dollars,
        max_wait_seconds=config.max_wait_seconds,
        model=profile.model,
        effort=profile.effort,
        preset=profile.preset,
        auto_model=config.auto_model,
        permission_mode=permission_mode,
        log_chatter=log_chatter,
        max_buffer_size=config.max_buffer_size,
        done_marker=config.done_marker,
        retry_watchdog=config.retry_watchdog,
        cwd=str(cwd),
    )
    clock = SystemClock()
    sleeper = AnyioSleeper(clock)

    # Audit JSONL is always under the run dir — never the structlog --log-file path.
    audit_log = JsonlAuditLog(run_dir.root / "audit.jsonl", run_id=run_id)
    progress = ConsoleProgressReporter()
    notifier = StderrNotifier()
    state_store = FileRunStateStore(cwd / ".claudeloop" / "state")
    session_lock = FileSessionLock(cwd / ".claudeloop" / "locks")
    run_control = FileRunControl(run_dir.inbox)
    save_points = GitSavePointStore(cwd=cwd, index_path=run_dir.savepoints_path)
    state_bus = FileStateBus(
        status_path=run_dir.root / "status.json",
        bus_path=run_dir.root / "bus.jsonl",
        run_id=run_id,
    )
    snapshot_sink = RunSnapshotBuilder(run_dir, state_bus=state_bus)

    budget = Budget(
        max_turns=config.max_turns,
        max_dollars=config.max_dollars,
        max_attempts=config.max_attempts,
    )
    wait_policy = WaitPolicyConfig(
        credits_probe_interval=timedelta(seconds=config.credits_probe_interval_seconds),
        credits_probe_ceiling=timedelta(seconds=config.credits_probe_ceiling_seconds),
        window_probe_interval=timedelta(seconds=config.window_probe_interval_seconds),
        reset_grace=timedelta(seconds=config.reset_grace_seconds),
        max_wait=(
            timedelta(seconds=config.max_wait_seconds)
            if config.max_wait_seconds is not None
            else None
        ),
    )
    progress_wait = ProgressWaitConfig(
        initial_seconds=config.progress_wait_initial_seconds,
        factor=config.progress_wait_factor,
        ceiling_seconds=config.progress_wait_ceiling_seconds,
    )

    def _meta_updater(**kwargs: Any) -> None:
        run_dir.update_meta(**kwargs)

    runner = AutonomousRunner(
        agent_gateway=gateway,
        capacity_probe=probe,
        clock=clock,
        sleeper=sleeper,
        audit_log=audit_log,
        progress=progress,
        budget=budget,
        wait_policy=wait_policy,
        progress_wait=progress_wait,
        done_marker=config.done_marker,
        run_id=run_id,
        notifier=notifier,
        run_control=run_control,
        event_sink=event_sink,
        state_store=state_store,
        session_lock=session_lock,
        save_points=save_points,
        plan=plan,
        stop_summary_writer=run_dir.write_stop_summary,
        handoff_marker_writer=run_dir.write_handoff_marker,
        wind_down_at=wind_down_at,
        meta_updater=_meta_updater,
        events_path=str(run_dir.events_path),
        state_bus=state_bus,
        logger=StructlogAppLogger(get_logger(component="runner", run_id=run_id, trace_id=trace_id)),
        trace_id=trace_id,
        profile=profile,
        aliases=config.aliases(),
        auto_model=config.auto_model,
        log_chatter=log_chatter,
        stream_ui=ui,
        max_dollars=config.max_dollars,
        run_resources=resources,
        permission_mode=permission_mode,
        snapshot_sink=snapshot_sink,
        known_session_id=resume or session_id,
    )
    if slash:
        run_control.enqueue(SlashCommand(text=slash))
    # log_file is reserved for structlog (configure_logging); keep unused here
    # so callers can pass it without colliding with audit JSONL.
    del log_file
    return RunnerContext(
        runner=runner,
        gateway=gateway,
        run_dir=run_dir,
        run_id=run_id,
        trace_id=trace_id,
    )


def build_session_catalog() -> SdkSessionCatalog:
    return SdkSessionCatalog()


def build_doctor_environment() -> DoctorEnvironment:
    return RealDoctorEnvironment()


_CACHED_API_GROUP: click.Group | None = None


def build_api_click_group() -> click.Group:
    from claudeloop.infrastructure.api.binder import build_api_click_group as _build

    global _CACHED_API_GROUP
    if _CACHED_API_GROUP is None:
        _CACHED_API_GROUP = _build()
    return _CACHED_API_GROUP


def configure_cli_logging(*, plan: LogPlan, log_file: Path | None = None) -> None:
    """Apply the resolved -v / -q / --log-level plan to this process."""
    configure_logging(log_file=log_file, level=plan.level)
    apply_third_party_level(plan)
