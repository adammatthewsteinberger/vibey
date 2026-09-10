# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Composition root — the only module that wires infrastructure into ports.

CLI and application never import infrastructure; they ask this module.
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import os
import shutil
import sys
import time
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Literal, assert_never

from agyloop.application.dto import TurnOutcome
from agyloop.application.interfaces import DoctorEnvironment
from agyloop.application.ports import AgentGateway, CapacityProbe
from agyloop.application.runner import AutonomousRunner
from agyloop.application.usecases.run_control import (
    EnqueueResult,
    request_prompt,
    request_resource_mutate,
    request_set_model,
    request_set_preset,
    request_stop,
)
from agyloop.domain.budget import Budget
from agyloop.domain.classify import TurnSignals
from agyloop.domain.errors import UnsafeSkipPermissionsError
from agyloop.domain.model_profile import resolve_profile
from agyloop.domain.permission import DEFAULT_USER_PERMISSION_MODE, parse_user_permission_mode
from agyloop.domain.plan import WorkPlan
from agyloop.domain.snapshot import SnapshotRef
from agyloop.domain.verbosity import LogPlan
from agyloop.domain.waiting import WaitPolicyConfig
from agyloop.infrastructure.agent.catalog import RunRegistryCatalog
from agyloop.infrastructure.agent.cli_argv import UNSAFE_SKIP_WARNING
from agyloop.infrastructure.agent.cli_argv import (
    validate_unsafe_skip_permissions as _validate_unsafe_skip_permissions,
)
from agyloop.infrastructure.agent.gateway import AntigravityAgentGateway
from agyloop.infrastructure.agent.gateway_cli import AgyCliAgentGateway
from agyloop.infrastructure.agent.harness_retarget import restore_site_packages_backups
from agyloop.infrastructure.agent.probe import AntigravityCapacityProbe
from agyloop.infrastructure.agent.probe_cli import AgyCliCapacityProbe
from agyloop.infrastructure.api.binder import build_api_click_group as _build_api_click_group
from agyloop.infrastructure.config import load_config
from agyloop.infrastructure.control import FileRunControl
from agyloop.infrastructure.doctor_env import RealDoctorEnvironment, developer_api_key
from agyloop.infrastructure.events import JsonlRunEventSink
from agyloop.infrastructure.git_savepoints import GitSavePointStore
from agyloop.infrastructure.logging import (
    StructlogAppLogger,
    apply_third_party_level,
    configure_logging,
)
from agyloop.infrastructure.notify import StderrNotifier
from agyloop.infrastructure.resources import ResourcePortAdapter, RunResourceStore
from agyloop.infrastructure.rundir import (
    RunDirectory,
    list_run_directories,
    pid_alive,
    resolve_run_directory,
    resolve_run_directory_any,
    runs_root_for,
)
from agyloop.infrastructure.snapshot import RunSnapshotBuilder
from agyloop.infrastructure.state_bus import FileStateBus
from agyloop.infrastructure.stream_ui import dump_transcript, run_textual_app

GatewayKind = Literal["sdk", "cli"]


@dataclass(frozen=True, slots=True)
class RunnerContext:
    runner: AutonomousRunner
    gateway: AgentGateway
    run_dir: RunDirectory
    run_id: str
    trace_id: str


class _SystemClock:
    def now(self) -> datetime:
        return datetime.now(UTC)


class _AsyncioSleeper:
    async def sleep_until(self, instant: datetime) -> None:
        delay = (instant - datetime.now(UTC)).total_seconds()
        if delay > 0:
            await asyncio.sleep(delay)


class _NullAuditLog:
    def record(self, event_type: str, payload: dict[str, Any]) -> None:
        del event_type, payload


class _StderrProgress:
    def turn_sent(self, *, attempt: int) -> None:
        del attempt

    def waiting(self, *, reason: str, until: datetime) -> None:
        del reason, until

    def finished(self, *, success: bool, reason: str) -> None:
        del success, reason


class _NoOpCapacityProbe:
    """Safety dummy for ``--no-probe``: if probe() is called, issue zero chat()."""

    async def probe(self) -> TurnOutcome:
        return TurnOutcome(signals=TurnSignals(), verdict=None, output_text="", session_id=None)


def _run_directory_for_conversation(cwd: Path, conversation_id: str | None) -> RunDirectory | None:
    if not conversation_id:
        return None
    for directory in list_run_directories(cwd):
        meta = directory.read_meta()
        if meta.conversation_id == conversation_id or meta.run_id == conversation_id:
            return directory
    return None


def _plan_seed_from_registry(cwd: Path, conversation_id: str | None) -> str | None:
    directory = _run_directory_for_conversation(cwd, conversation_id)
    return directory.read_plan_text() if directory is not None else None


def parse_gateway(value: str) -> GatewayKind:
    key = value.strip().lower()
    if key == "sdk":
        return "sdk"
    if key == "cli":
        return "cli"
    raise ValueError(f"unknown gateway {value!r}; expected 'sdk' or 'cli'")


def build_api_click_group() -> Any:
    return _build_api_click_group()


def configure_cli_logging(*, plan: LogPlan, log_file: Path | None = None) -> None:
    """Apply the resolved -v / -q / --log-level plan to this process."""
    configure_logging(log_file=log_file, level=plan.level, human_console=True)
    apply_third_party_level(plan)


def effective_config(cwd: Path) -> dict[str, Any]:
    cfg = load_config(cwd=cwd)
    return {
        "max_turns": cfg.max_turns,
        "max_dollars": cfg.max_dollars,
        "max_tokens": cfg.max_tokens,
        "max_wait_seconds": cfg.max_wait_seconds,
        "log_level": cfg.log_level,
        "log_file": cfg.log_file,
        "model": cfg.model,
        "effort": cfg.effort,
        "preset": cfg.preset,
        "model_low": cfg.model_low,
        "model_medium": cfg.model_medium,
        "model_high": cfg.model_high,
        "gateway": cfg.gateway,
        "ramp": cfg.ramp,
        "permission_mode": cfg.permission_mode,
        "auto_model": cfg.auto_model,
    }


def _build_agent_ports(
    *,
    kind: GatewayKind,
    cwd: Path,
    conversation_id: str | None,
    model: str | None,
    permission_mode: Any,
    plan_seed: str | None,
    strict_autonomy: bool,
    unsafe_skip_permissions: bool,
    no_probe: bool,
    add_dirs: list[str] | None = None,
    on_event: Any = None,
    api_key: str | None = None,
) -> tuple[AgentGateway, CapacityProbe]:
    """Build the turn gateway and the capacity probe together.

    They are returned as a pair on purpose. Building them separately is how
    ``--gateway cli`` ended up with an SDK preflight probe: the transport choice
    was consulted for one and forgotten for the other, so opting out of the
    Antigravity harness still booted it. ``assert_never`` below now makes
    picking a transport for one but not the other impossible.
    """
    probe: CapacityProbe
    match kind:
        case "cli":
            gateway: AgentGateway = AgyCliAgentGateway(
                cwd=str(cwd),
                conversation_id=conversation_id,
                model=model,
                unsafe_skip_permissions=unsafe_skip_permissions,
            )
            probe = (
                _NoOpCapacityProbe()
                if no_probe
                else AgyCliCapacityProbe(
                    cwd=str(cwd),
                    model=model,
                    unsafe_skip_permissions=unsafe_skip_permissions,
                )
            )
            return gateway, probe
        case "sdk":
            gateway = AntigravityAgentGateway(
                cwd=str(cwd),
                conversation_id=conversation_id,
                model=model,
                permission_mode=permission_mode,
                plan_seed=plan_seed,
                strict_autonomy=strict_autonomy,
                add_dirs=add_dirs,
                on_event=on_event,
                api_key=api_key,
            )
            probe = (
                _NoOpCapacityProbe()
                if no_probe
                else AntigravityCapacityProbe(cwd=str(cwd), model=model, api_key=api_key)
            )
            return gateway, probe
        case _:
            assert_never(kind)


def build_runner(
    *,
    cwd: Path,
    plan: WorkPlan | None = None,
    plan_path: Path | None = None,
    conversation_id: str | None = None,
    plan_seed: str | None = None,
    model: str | None = None,
    max_turns: int | None = None,
    max_wait_seconds: float | None = None,
    max_tokens: int | None = None,
    no_probe: bool = False,
    strict_autonomy: bool = False,
    permission_mode: str = DEFAULT_USER_PERMISSION_MODE,
    resume: bool = False,
    ramp: int = 0,
    gateway: str = "sdk",
    unsafe_skip_permissions: bool = False,
    add_dirs: list[str] | None = None,
    max_dollars: float | None = None,
    preset: str | None = None,
    effort: str | None = None,
    run_id: str | None = None,
) -> RunnerContext:
    config = load_config(
        cwd=cwd,
        cli_overrides={
            "model": model,
            "max_turns": max_turns,
            "max_wait_seconds": max_wait_seconds,
            "max_tokens": max_tokens,
            "max_dollars": max_dollars,
            "preset": preset,
            "effort": effort,
            "gateway": gateway,
            "ramp": ramp,
            "permission_mode": permission_mode,
        },
    )
    run_dir = _run_directory_for_conversation(cwd, conversation_id) if resume else None
    if run_dir is None:
        run_dir = RunDirectory.create(
            runs_root_for(cwd), cwd=cwd, plan_path=plan_path, run_id=run_id
        )
    # Rebind to the resolved id: identical to the supplied one when the caller
    # named the run, the freshly minted one otherwise.
    run_id = run_dir.read_meta().run_id
    trace_id = str(uuid.uuid4())
    parsed_mode = parse_user_permission_mode(config.permission_mode)
    seed = plan_seed or _plan_seed_from_registry(cwd, conversation_id)
    if seed is None and plan is not None:
        seed = plan.raw_text
    kind = parse_gateway(gateway)
    event_sink = JsonlRunEventSink(run_dir.events_path, run_id=run_id, trace_id=trace_id)
    state_bus = FileStateBus(
        status_path=run_dir.status_path,
        bus_path=run_dir.bus_path,
        run_id=run_id,
    )
    extra_dirs = list(add_dirs or [])
    api_key, _source = developer_api_key(os.environ)
    agent_gateway, probe = _build_agent_ports(
        kind=kind,
        cwd=cwd,
        conversation_id=conversation_id,
        model=config.model or model,
        permission_mode=parsed_mode,
        plan_seed=seed,
        strict_autonomy=strict_autonomy,
        unsafe_skip_permissions=unsafe_skip_permissions,
        no_probe=no_probe,
        add_dirs=extra_dirs or None,
        on_event=lambda payload: event_sink.emit("sdk.event", dict(payload)),
        api_key=api_key,
    )
    wait_policy = WaitPolicyConfig(
        max_wait=timedelta(seconds=config.max_wait_seconds) if config.max_wait_seconds else None,
        no_probe=no_probe,
    )
    profile = resolve_profile(
        preset=config.preset,
        model=config.model,
        effort=config.effort,
        aliases=config.aliases(),
    )
    save_points = GitSavePointStore(cwd=cwd, index_path=run_dir.savepoints_path)
    resources = ResourcePortAdapter(RunResourceStore(run_dir.resources_root))
    for folder in extra_dirs:
        resources.apply_mutate(action="add", kind="folder", value=folder)
    runner = AutonomousRunner(
        agent_gateway=agent_gateway,
        capacity_probe=probe,
        clock=_SystemClock(),
        sleeper=_AsyncioSleeper(),
        audit_log=_NullAuditLog(),
        progress=_StderrProgress(),
        budget=Budget(
            max_turns=config.max_turns,
            max_tokens=config.max_tokens,
            max_dollars=config.max_dollars,
        ),
        wait_policy=wait_policy,
        run_id=run_id,
        plan=plan,
        meta_updater=run_dir.update_meta,
        trace_id=trace_id,
        profile=profile,
        aliases=config.aliases(),
        permission_mode=parsed_mode,
        notifier=StderrNotifier(),
        no_probe=no_probe,
        run_control=FileRunControl(run_dir.inbox),
        save_points=save_points,
        snapshot_sink=RunSnapshotBuilder(run_dir),
        event_sink=event_sink,
        state_bus=state_bus,
        logger=StructlogAppLogger(),
        events_path=str(run_dir.events_path),
        max_dollars=config.max_dollars,
        run_resources=resources,
        auto_model=config.auto_model,
        ramp=config.ramp if ramp == 0 else ramp,
    )
    return RunnerContext(
        runner=runner,
        gateway=agent_gateway,
        run_dir=run_dir,
        run_id=run_id,
        trace_id=trace_id,
    )


def build_session_catalog() -> RunRegistryCatalog:
    return RunRegistryCatalog()


def build_doctor_environment() -> DoctorEnvironment:
    return RealDoctorEnvironment()


def repair_harness() -> str:
    """Restore a site-packages localharness backup created by agyloop."""
    return restore_site_packages_backups()


def enqueue_stop(cwd: Path, run_id: str | None = None) -> EnqueueResult:
    directory = resolve_run_directory(cwd, run_id)
    inbox = FileRunControl(directory.inbox)
    return request_stop(inbox, run_id=directory.read_meta().run_id)


def enqueue_prompt(
    cwd: Path,
    text: str,
    *,
    immediate: bool,
    run_id: str | None = None,
) -> EnqueueResult:
    directory = resolve_run_directory(cwd, run_id)
    inbox = FileRunControl(directory.inbox)
    return request_prompt(inbox, text, immediate=immediate, run_id=directory.read_meta().run_id)


def validate_unsafe_skip_permissions(cwd: Path, *, sandbox: bool = False) -> None:
    """Refuse ``--unsafe-skip-permissions`` under root / sandbox / non-git cwd."""
    _validate_unsafe_skip_permissions(cwd=cwd, sandbox=sandbox)


def refuse_unsafe_skip_on_sdk_path(cwd: Path) -> None:
    """Gate then fail closed: SDK ``run`` never honors skip-permissions."""
    validate_unsafe_skip_permissions(cwd)
    raise UnsafeSkipPermissionsError(
        "--unsafe-skip-permissions is for the CLI adapter argv builder "
        "(build_agy_argv), not the SDK gateway. The SDK path uses policies / "
        "--yolo for autonomy scope and never emits --dangerously-skip-permissions. "
        f"{UNSAFE_SKIP_WARNING}"
    )


def list_savepoints(cwd: Path, run_id: str | None = None) -> list[dict[str, Any]]:
    directory = resolve_run_directory_any(cwd, run_id)
    meta = directory.read_meta()
    store = GitSavePointStore(cwd=cwd, index_path=directory.savepoints_path)
    return [
        {
            "n": point.n,
            "ref": point.ref,
            "sha": point.sha,
            "label": point.label,
            "at": point.at.isoformat(),
        }
        for point in store.list_points(meta.run_id)
    ]


def unwind_savepoint(
    cwd: Path,
    to: str,
    *,
    backup: bool = True,
    run_id: str | None = None,
) -> dict[str, Any]:
    directory = resolve_run_directory_any(cwd, run_id)
    meta = directory.read_meta()
    if directory.is_active():
        raise RuntimeError(
            f"run {meta.run_id} is still active (pid {meta.pid}); "
            "stop it before unwinding save points"
        )
    store = GitSavePointStore(cwd=cwd, index_path=directory.savepoints_path)
    result = store.unwind(run_id=meta.run_id, to=to, backup=backup)
    return {
        "to_n": result.to.n,
        "to_sha": result.to.sha,
        "backup_ref": result.backup_ref,
        "restored_sha": result.restored_sha,
    }


def emit_snapshot(
    cwd: Path,
    *,
    run_id: str | None = None,
    bundle: bool = True,
    out: Path | None = None,
) -> SnapshotRef:
    directory = resolve_run_directory_any(cwd, run_id)
    builder = RunSnapshotBuilder(directory)
    ref = builder.emit("manual", bundle=bundle)
    if ref is None:
        raise RuntimeError("snapshot emit produced no ref")
    if out is not None:
        src = directory.root / ref.path
        if not src.is_file() and (directory.snapshots_root / "latest.json").is_file():
            src = directory.snapshots_root / "latest.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, out)
    return ref


def enqueue_model(cwd: Path, model: str, *, run_id: str | None = None) -> EnqueueResult:
    directory = resolve_run_directory(cwd, run_id)
    inbox = FileRunControl(directory.inbox)
    return request_set_model(inbox, model, run_id=directory.read_meta().run_id)


def enqueue_preset(cwd: Path, preset: str, *, run_id: str | None = None) -> EnqueueResult:
    directory = resolve_run_directory(cwd, run_id)
    inbox = FileRunControl(directory.inbox)
    return request_set_preset(inbox, preset, run_id=directory.read_meta().run_id)


def enqueue_resource(
    cwd: Path,
    *,
    action: str,
    kind: str,
    value: str,
    name: str | None = None,
    run_id: str | None = None,
) -> EnqueueResult:
    directory = resolve_run_directory(cwd, run_id)
    inbox = FileRunControl(directory.inbox)
    return request_resource_mutate(
        inbox,
        action=action,
        kind=kind,
        value=value,
        name=name,
        run_id=directory.read_meta().run_id,
    )


def list_runs(cwd: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for directory in list_run_directories(cwd):
        meta = directory.read_meta()
        status = meta.status
        if status in {"active", "waiting"} and not pid_alive(meta.pid):
            status = "orphaned"
            with contextlib.suppress(OSError):
                directory.update_meta(status="orphaned")
        rows.append(
            {
                "run_id": meta.run_id,
                "status": status,
                "pid": meta.pid,
                "phase": meta.phase,
                "attempt": meta.attempt,
                "session_id": meta.conversation_id,
                "started_at": meta.started_at,
                "path": str(directory.root),
            }
        )
    return rows


def run_status(cwd: Path, run_id: str | None = None) -> dict[str, Any]:
    directory = resolve_run_directory_any(cwd, run_id)
    meta = directory.read_meta()
    status = meta.status
    alive = pid_alive(meta.pid)
    if status in {"active", "waiting"} and not alive:
        status = "orphaned"
        with contextlib.suppress(OSError):
            directory.update_meta(status="orphaned")
    live: dict[str, Any] = {}
    if directory.status_path.is_file():
        loaded = json.loads(directory.status_path.read_text(encoding="utf-8"))
        if isinstance(loaded, dict):
            live = loaded
    latest_snap = directory.snapshots_root / "latest.json"
    terminal = status in {"failed", "finished", "orphaned"}
    reported = status if terminal else live.get("status", status)
    phase = meta.phase if terminal and meta.phase else live.get("phase", meta.phase)
    return {
        "run_id": meta.run_id,
        "status": reported,
        "pid": meta.pid,
        "pid_alive": alive,
        "phase": phase,
        "attempt": live.get("attempt", meta.attempt),
        "session_id": live.get("session_id", meta.conversation_id),
        "model": live.get("model", meta.model),
        "events_path": str(directory.events_path),
        "status_path": str(directory.status_path),
        "bus_path": str(directory.bus_path),
        "snapshot_latest_path": str(latest_snap) if latest_snap.is_file() else None,
    }


def watch_bus(
    cwd: Path,
    *,
    run_id: str | None = None,
    follow: bool = True,
    poll_seconds: float = 0.25,
) -> None:
    directory = resolve_run_directory_any(cwd, run_id)
    path = directory.bus_path
    offset = 0
    while True:
        if path.is_file():
            with path.open("r", encoding="utf-8") as handle:
                handle.seek(offset)
                chunk = handle.read()
                if chunk:
                    sys.stdout.write(chunk)
                    sys.stdout.flush()
                    offset = handle.tell()
        if not follow:
            return
        time.sleep(poll_seconds)


def tail_events(
    cwd: Path,
    *,
    run_id: str | None = None,
    follow: bool = False,
    chatter_only: bool = False,
    poll_seconds: float = 0.25,
) -> None:
    directory = resolve_run_directory_any(cwd, run_id)
    path = directory.events_path
    offset = 0
    while True:
        if path.is_file():
            with path.open("r", encoding="utf-8") as handle:
                handle.seek(offset)
                chunk = handle.read()
                if chunk:
                    if not chatter_only:
                        sys.stdout.write(chunk)
                        sys.stdout.flush()
                    else:
                        for line in chunk.splitlines():
                            try:
                                record = json.loads(line)
                            except json.JSONDecodeError:
                                continue
                            et = str(record.get("event_type") or "")
                            if et.startswith("chatter."):
                                sys.stdout.write(line + "\n")
                        sys.stdout.flush()
                    offset = handle.tell()
        if not follow:
            return
        time.sleep(poll_seconds)


def run_stream_ui(
    cwd: Path,
    *,
    run_id: str | None = None,
    follow: bool = True,
    replay: bool = False,
    speed: float = 1.0,
) -> None:
    directory = resolve_run_directory_any(cwd, run_id)
    events = directory.events_path
    if replay and not sys.stdout.isatty():
        dump_transcript(events)
        return
    run_textual_app(events_path=events, follow=follow, replay=replay, speed=speed)


def reset_project_state(cwd: Path, *, yes: bool) -> dict[str, Any]:
    root = cwd / ".agyloop"
    if not yes:
        raise ValueError("refusing to reset without --yes")
    if not root.exists():
        raise FileNotFoundError(f"no control plane at {root}")
    for directory in list_run_directories(cwd):
        meta = directory.read_meta()
        if meta.status in {"active", "waiting"} and pid_alive(meta.pid):
            raise RuntimeError(
                f"run {meta.run_id} is still active (pid {meta.pid}); "
                "stop it with `agyloop stop` before reset"
            )
    shutil.rmtree(root)
    return {"path": str(root)}
