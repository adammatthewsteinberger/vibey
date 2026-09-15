# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Composition root — the only module permitted to import every onion layer."""

from __future__ import annotations

import json
import os
import sys
from collections.abc import Callable, Mapping, Sequence
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import anyio

from codexloop.application.ports import (
    AgentGateway,
    CapacityProbe,
    RunEventSink,
    RunSnapshotSink,
)
from codexloop.application.runner import RunnerContext
from codexloop.application.usecases.doctor import DoctorReport, run_doctor
from codexloop.application.usecases.run_control import enqueue_control
from codexloop.domain.budget import Budget
from codexloop.domain.capacity import PlanWindows
from codexloop.domain.control import ControlCommand, Stop
from codexloop.domain.errors import ConfigurationError
from codexloop.domain.handoff_marker import HandoffMarker
from codexloop.domain.savepoint import SavePointRef, UnwindResult
from codexloop.domain.session import ThreadRef
from codexloop.domain.verbosity import LogPlan
from codexloop.domain.waiting import AdaptiveWaitPolicy, WaitConfig
from codexloop.infrastructure.agent.argv import ExecOpts
from codexloop.infrastructure.agent.gateway import CodexExecGateway
from codexloop.infrastructure.agent.probe import ExecCapacityProbe
from codexloop.infrastructure.agent.scripted import resolve_test_agent_from_env
from codexloop.infrastructure.api.binder import build_api_typer_app as _build_api_typer_app
from codexloop.infrastructure.appserver.client import AppServerClient
from codexloop.infrastructure.appserver.gateway import probe_app_server_transport
from codexloop.infrastructure.capacity_probe import CompositeCapacityProbe
from codexloop.infrastructure.clock import AnyioSleeper, SystemClock
from codexloop.infrastructure.config import RunnerConfig, load_config
from codexloop.infrastructure.control import CompositeRunControl, FileRunControl
from codexloop.infrastructure.doctor_env import CodexDoctorEnvironment
from codexloop.infrastructure.events import JsonlRunEventSink
from codexloop.infrastructure.git_savepoints import GitSavePointStore
from codexloop.infrastructure.lock import AdvisoryFileLock
from codexloop.infrastructure.logging import (
    apply_third_party_level,
    configure_logging,
)
from codexloop.infrastructure.notify import CommandNotifier
from codexloop.infrastructure.progress import LoggingProgressReporter
from codexloop.infrastructure.rollout import read_rollout_rate_limits
from codexloop.infrastructure.run_snapshot import RunDirSnapshotSink
from codexloop.infrastructure.rundir import RunDirectory, runs_root_for, write_handoff_marker
from codexloop.infrastructure.snapshot import create_snapshot, restore_snapshot
from codexloop.infrastructure.state import FileRunStateStore
from codexloop.infrastructure.state_bus import read_state
from codexloop.infrastructure.stream_ui import run_stream_ui

__all__ = [
    "DrainControl",
    "RunnerConfig",
    "build_api_typer_app",
    "build_runner",
    "current_drain",
    "create_savepoint",
    "enqueue_run_control",
    "events_path_for_run",
    "list_run_records",
    "list_savepoints",
    "read_capacity_windows",
    "read_run_events",
    "read_run_record",
    "read_run_state",
    "register_drain",
    "restore_run_snapshot",
    "run_doctor_checks",
    "run_is_live",
    "run_stream_ui_for_events",
    "take_snapshot",
    "unwind_savepoint",
]

_ACTIVE_DRAIN: DrainControl | None = None


class DrainControl:
    """RunControl that surfaces SIGINT/SIGTERM as a domain ``Stop``."""

    def __init__(self) -> None:
        self._stop = False

    def request_stop(self) -> None:
        self._stop = True

    def poll(self) -> Sequence[ControlCommand]:
        if not self._stop:
            return []
        self._stop = False
        return [Stop()]


def current_drain() -> DrainControl | None:
    return _ACTIVE_DRAIN


def register_drain(control: DrainControl | None = None) -> DrainControl:
    """Install the process-wide drain. Pass a control to replace; omit to reuse."""
    global _ACTIVE_DRAIN
    if control is not None:
        _ACTIVE_DRAIN = control
        return control
    if _ACTIVE_DRAIN is None:
        _ACTIVE_DRAIN = DrainControl()
    return _ACTIVE_DRAIN


class _JsonThreadCatalog:
    def __init__(self, path: Path) -> None:
        self._path = path
        self._threads: dict[str, ThreadRef] = {}
        self._load()

    def _load(self) -> None:
        if not self._path.is_file():
            return
        try:
            raw = json.loads(self._path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return
        if not isinstance(raw, list):
            return
        for item in raw:
            if not isinstance(item, dict):
                continue
            try:
                ref = ThreadRef(
                    thread_id=str(item["thread_id"]),
                    cwd=str(item["cwd"]),
                    started_at=datetime.fromisoformat(str(item["started_at"])),
                    model=str(item["model"]),
                )
            except (KeyError, TypeError, ValueError):
                continue
            self._threads[ref.thread_id] = ref

    def _save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        payload = [
            {
                "thread_id": ref.thread_id,
                "cwd": ref.cwd,
                "started_at": ref.started_at.isoformat(),
                "model": ref.model,
            }
            for ref in self._threads.values()
        ]
        self._path.write_text(json.dumps(payload) + "\n", encoding="utf-8")

    def list_threads(self) -> Sequence[ThreadRef]:
        return list(self._threads.values())

    def get(self, thread_id: str) -> ThreadRef | None:
        return self._threads.get(thread_id)

    def record(self, ref: ThreadRef) -> None:
        self._threads[ref.thread_id] = ref
        self._save()


def _select_gateway(
    transport: str,
    *,
    cwd: Path,
    config: RunnerConfig,
    event_sink: RunEventSink | None = None,
) -> AgentGateway:
    opts = ExecOpts(
        prompt="",
        model=config.model,
        add_dirs=config.add_dirs,
        network_access=config.network_access,
    )
    if transport == "app-server":
        if config.network_access:
            print(
                "codexloop: network access requires exec transport; using exec",
                file=sys.stderr,
            )
            return CodexExecGateway(cwd=cwd, opts=opts, event_sink=event_sink)

        async def _probe() -> tuple[AgentGateway | None, str | None]:
            return await probe_app_server_transport(cwd=cwd)

        gateway, reason = anyio.run(_probe)
        if gateway is not None:
            return gateway
        if reason:
            print(f"codexloop: {reason}", file=sys.stderr)
        return CodexExecGateway(
            cwd=cwd,
            opts=opts,
            event_sink=event_sink,
        )
    if transport != "exec":
        raise ConfigurationError(f"unknown transport {transport!r}")
    return CodexExecGateway(
        cwd=cwd,
        opts=opts,
        event_sink=event_sink,
    )


def build_runner(
    config: RunnerConfig | None = None,
    *,
    transport: str = "exec",
    cwd: Path | None = None,
    flags: Mapping[str, object] | None = None,
    ensure_run: bool = True,
    run_id: str | None = None,
) -> RunnerContext:
    """Wire ports for one CLI invocation. ``cli/`` must not import infrastructure."""
    cwd = Path.cwd() if cwd is None else cwd
    if config is None:
        config = load_config(cwd=cwd, flags=flags)

    configure_logging(
        level=config.log_level,
        json_logs=config.json_logs,
        log_file=Path(config.log_file) if config.log_file else None,
    )

    runs_root = runs_root_for(cwd)
    rundir: RunDirectory | None = (
        RunDirectory.create(runs_root, run_id=run_id) if ensure_run else None
    )
    clock = SystemClock()

    def write_artifact(name: str, content: str) -> None:
        if rundir is None:
            return
        (rundir.root / name).write_text(content, encoding="utf-8")

    app_server = AppServerClient(cwd=cwd)
    gateway: AgentGateway
    probe: CapacityProbe
    scripted = resolve_test_agent_from_env()

    # Create event sink if we have a run directory
    event_sink: RunEventSink | None = None
    snapshot_sink: RunSnapshotSink | None = None
    if rundir is not None:
        rundir.update_meta(
            {
                "sandbox_mode": "workspace-write",
                "network_access": config.network_access,
            }
        )
        event_sink = JsonlRunEventSink(rundir.events_path)
        snapshot_sink = RunDirSnapshotSink(rundir.snapshots)

    if scripted is not None:
        gateway, probe = scripted
        wait_policy = AdaptiveWaitPolicy(
            WaitConfig(
                jitter_ratio=0.0,
                quota_probe_base=timedelta(milliseconds=50),
                quota_probe_ceiling=timedelta(milliseconds=200),
                window_probe_interval=timedelta(milliseconds=50),
                throttle_ceiling=timedelta(milliseconds=200),
                aggressive_ceiling=timedelta(milliseconds=200),
                transient_ceiling=timedelta(milliseconds=200),
                backoff_base=timedelta(milliseconds=50),
                grace=timedelta(0),
            ),
            rand=lambda: 0.0,
        )
    else:
        gateway = _select_gateway(transport, cwd=cwd, config=config, event_sink=event_sink)
        probe = CompositeCapacityProbe(
            ExecCapacityProbe(cwd=cwd),
            app_server=app_server.read_rate_limits,
            rollout=read_rollout_rate_limits,
        )
        wait_policy = AdaptiveWaitPolicy(WaitConfig())

    drain = register_drain()
    if rundir is not None:
        inbox = FileRunControl(rundir.inbox)
        control: DrainControl | CompositeRunControl = CompositeRunControl(drain, inbox)

        def handoff_writer(marker: HandoffMarker) -> None:
            write_handoff_marker(rundir.root, marker)

        handoff_marker_writer: Callable[[HandoffMarker], None] | None = handoff_writer
    else:
        control = drain
        handoff_marker_writer = None

    return RunnerContext(
        clock=clock,
        sleeper=AnyioSleeper(clock),
        gateway=gateway,
        probe=probe,
        store=FileRunStateStore(runs_root),
        control=control,
        catalog=_JsonThreadCatalog(cwd / ".codexloop" / "threads.json"),
        lock=AdvisoryFileLock(cwd / ".codexloop" / "locks"),
        write_artifact=write_artifact,
        notifier=CommandNotifier(config.notify_command),
        reporter=LoggingProgressReporter(),
        budget=Budget(max_turns=config.max_turns, max_dollars=None, max_wall_clock=None),
        wait_policy=wait_policy,
        max_wait=config.max_wait,
        handoff_marker_writer=handoff_marker_writer,
        snapshot_sink=snapshot_sink,
        event_sink=event_sink,
        run_id=rundir.run_id if rundir is not None else "anonymous",
        cwd=str(cwd),
        model=config.model or "codex-default",
    )


def list_run_records(cwd: Path | None = None) -> list[dict[str, Any]]:
    root = runs_root_for(Path.cwd() if cwd is None else cwd)
    if not root.is_dir():
        return []
    return [_record_from_dir(child) for child in sorted(root.iterdir()) if child.is_dir()]


def _latest_run_key(record: dict[str, Any]) -> datetime:
    meta = record.get("meta")
    if isinstance(meta, dict):
        raw = meta.get("started_at")
        if isinstance(raw, str):
            try:
                return datetime.fromisoformat(raw)
            except ValueError:
                pass
    try:
        return datetime.fromtimestamp(Path(str(record["root"])).stat().st_mtime, tz=UTC)
    except OSError:
        return datetime.min.replace(tzinfo=UTC)


def read_run_record(run_id: str | None = None, *, cwd: Path | None = None) -> dict[str, Any] | None:
    records = list_run_records(cwd)
    if not records:
        return None
    if run_id is None:
        return max(records, key=_latest_run_key)
    for record in records:
        if record["run_id"] == run_id:
            return record
    return None


def read_run_events(run_id: str | None = None, *, cwd: Path | None = None) -> str:
    record = read_run_record(run_id, cwd=cwd)
    if record is None:
        return ""
    events_path = Path(str(record["root"])) / "events.jsonl"
    if not events_path.is_file():
        return ""
    return events_path.read_text(encoding="utf-8")


def _record_from_dir(root: Path) -> dict[str, Any]:
    meta: dict[str, Any] = {}
    state: dict[str, Any] = {}
    meta_path = root / "meta.json"
    state_path = root / "state.json"
    if meta_path.is_file():
        loaded = json.loads(meta_path.read_text(encoding="utf-8"))
        if isinstance(loaded, dict):
            meta = loaded
    if state_path.is_file():
        loaded = json.loads(state_path.read_text(encoding="utf-8"))
        if isinstance(loaded, dict):
            state = loaded
    return {"run_id": root.name, "root": str(root), "meta": meta, "state": state}


def _run_directory(run_id: str | None = None, *, cwd: Path | None = None) -> RunDirectory:
    record = read_run_record(run_id, cwd=cwd)
    if record is None:
        raise ConfigurationError("no run found — start one with `codexloop run` first")
    directory = RunDirectory(Path(str(record["root"])))
    directory.ensure_layout()
    return directory


def enqueue_run_control(
    command: ControlCommand,
    *,
    run_id: str | None = None,
    cwd: Path | None = None,
) -> Path:
    directory = _run_directory(run_id, cwd=cwd)
    return enqueue_control(FileRunControl(directory.inbox), command)


def run_doctor_checks(*, cwd: Path | None = None) -> DoctorReport:
    root = Path.cwd() if cwd is None else cwd
    env = CodexDoctorEnvironment(
        rollout_live=lambda: (Path.home() / ".codex").is_dir(),
    )
    return run_doctor(env, cwd=root)


def read_capacity_windows(*, cwd: Path | None = None) -> PlanWindows | None:
    del cwd
    return read_rollout_rate_limits()


def read_run_state(run_id: str | None = None, *, cwd: Path | None = None) -> dict[str, object]:
    record = read_run_record(run_id, cwd=cwd)
    if record is None:
        return {}
    return read_state(Path(str(record["root"])) / "state.json")


def run_is_live(run_id: str | None = None, *, cwd: Path | None = None) -> bool:
    record = read_run_record(run_id, cwd=cwd)
    if record is None:
        return False
    meta = record.get("meta")
    if not isinstance(meta, dict):
        return False
    pid = meta.get("pid")
    if not isinstance(pid, int):
        return False
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def list_savepoints(run_id: str | None = None, *, cwd: Path | None = None) -> list[SavePointRef]:
    root = Path.cwd() if cwd is None else cwd
    directory = _run_directory(run_id, cwd=root)
    store = GitSavePointStore(cwd=root, index_path=directory.savepoints_path)
    return store.list_points(directory.run_id)


def create_savepoint(
    *,
    label: str = "manual",
    run_id: str | None = None,
    cwd: Path | None = None,
    attempt: int | None = None,
    summary: str = "",
) -> SavePointRef | None:
    root = Path.cwd() if cwd is None else cwd
    directory = _run_directory(run_id, cwd=root)
    store = GitSavePointStore(cwd=root, index_path=directory.savepoints_path)
    return store.create(
        run_id=directory.run_id,
        label=label,
        attempt=attempt,
        summary=summary,
    )


def unwind_savepoint(
    to: str,
    *,
    run_id: str | None = None,
    cwd: Path | None = None,
    backup: bool = True,
) -> UnwindResult:
    root = Path.cwd() if cwd is None else cwd
    directory = _run_directory(run_id, cwd=root)
    if run_is_live(directory.run_id, cwd=root):
        raise ConfigurationError("unwind refuses while a run is live")
    store = GitSavePointStore(cwd=root, index_path=directory.savepoints_path)
    return store.unwind(run_id=directory.run_id, to=to, backup=backup, live=False)


def take_snapshot(
    *,
    run_id: str | None = None,
    cwd: Path | None = None,
    name: str | None = None,
) -> Path:
    root = Path.cwd() if cwd is None else cwd
    directory = _run_directory(run_id, cwd=root)
    stamp = name or datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    dest = directory.snapshots / stamp
    return create_snapshot(cwd=root, dest=dest)


def restore_run_snapshot(
    name: str,
    *,
    run_id: str | None = None,
    cwd: Path | None = None,
) -> None:
    root = Path.cwd() if cwd is None else cwd
    directory = _run_directory(run_id, cwd=root)
    restore_snapshot(snapshot=directory.snapshots / name, cwd=root)


def build_api_typer_app() -> Any:
    """Compose the generated ``codexloop api`` Typer sub-app (M4)."""
    return _build_api_typer_app()


def run_stream_ui_for_events(path: Path) -> None:
    """Launch the optional Textual stream UI against an events JSONL file."""
    run_stream_ui(path)


def events_path_for_run(run_id: str | None = None, *, cwd: Path | None = None) -> Path:
    return _run_directory(run_id, cwd=cwd).events_path


def configure_cli_logging(*, plan: LogPlan, log_file: Path | None = None) -> None:
    """Apply the resolved -v / -q / --log-level plan to this process."""
    configure_logging(level=plan.level, log_file=log_file)
    apply_third_party_level(plan)
