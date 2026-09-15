# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Bootstrap helpers for operator CLI commands (stop/prompt/logs/unwind/runs)."""

from __future__ import annotations

import contextlib
import json
import os
import shutil
import time
from pathlib import Path
from typing import Any

from structlog.stdlib import BoundLogger

from claudeloop.application.usecases import run_control as run_control_uc
from claudeloop.domain.snapshot import SnapshotRef
from claudeloop.infrastructure.chat_meta import ChatMetaStore
from claudeloop.infrastructure.control import FileRunControl
from claudeloop.infrastructure.git_savepoints import GitSavePointStore
from claudeloop.infrastructure.logging import get_logger
from claudeloop.infrastructure.resources.store import RunResourceStore
from claudeloop.infrastructure.rundir import (
    _pid_alive,
    list_run_directories,
    resolve_run_directory,
)
from claudeloop.infrastructure.snapshot import RunSnapshotBuilder
from claudeloop.infrastructure.state_bus import FileStateBus


def _logger() -> BoundLogger:
    return get_logger(component="ops")


def enqueue_wind_down(
    cwd: Path, run_id: str | None = None, *, reason: str = "operator"
) -> run_control_uc.EnqueueResult:
    directory = resolve_run_directory(cwd, run_id)
    inbox = FileRunControl(directory.inbox)
    meta = directory.read_meta()
    result = run_control_uc.request_wind_down(inbox, reason=reason, run_id=meta.run_id)
    _logger().info("ops.wind_down_enqueued", run_id=result.run_id, reason=reason)
    return result


def enqueue_stop(cwd: Path, run_id: str | None = None) -> run_control_uc.EnqueueResult:
    directory = resolve_run_directory(cwd, run_id)
    inbox = FileRunControl(directory.inbox)
    meta = directory.read_meta()
    result = run_control_uc.request_stop(inbox, run_id=meta.run_id)
    _logger().info("ops.stop_enqueued", run_id=result.run_id)
    return result


def enqueue_prompt(
    cwd: Path,
    text: str,
    *,
    immediate: bool,
    run_id: str | None = None,
) -> run_control_uc.EnqueueResult:
    directory = resolve_run_directory(cwd, run_id)
    inbox = FileRunControl(directory.inbox)
    meta = directory.read_meta()
    result = run_control_uc.request_prompt(inbox, text, immediate=immediate, run_id=meta.run_id)
    _logger().info(
        "ops.prompt_enqueued",
        run_id=result.run_id,
        command_type=result.command_type,
        text_len=len(text),
    )
    return result


def enqueue_model(
    cwd: Path, model: str, *, run_id: str | None = None
) -> run_control_uc.EnqueueResult:
    directory = resolve_run_directory(cwd, run_id)
    inbox = FileRunControl(directory.inbox)
    meta = directory.read_meta()
    result = run_control_uc.request_set_model(inbox, model, run_id=meta.run_id)
    _logger().info("ops.model_enqueued", run_id=result.run_id, model=model)
    return result


def enqueue_effort(
    cwd: Path, effort: str, *, run_id: str | None = None
) -> run_control_uc.EnqueueResult:
    directory = resolve_run_directory(cwd, run_id)
    inbox = FileRunControl(directory.inbox)
    meta = directory.read_meta()
    result = run_control_uc.request_set_effort(inbox, effort, run_id=meta.run_id)
    _logger().info("ops.effort_enqueued", run_id=result.run_id, effort=effort)
    return result


def enqueue_preset(
    cwd: Path, preset: str, *, run_id: str | None = None
) -> run_control_uc.EnqueueResult:
    directory = resolve_run_directory(cwd, run_id)
    inbox = FileRunControl(directory.inbox)
    meta = directory.read_meta()
    result = run_control_uc.request_set_preset(inbox, preset, run_id=meta.run_id)
    _logger().info("ops.preset_enqueued", run_id=result.run_id, preset=preset)
    return result


def enqueue_permission_mode(
    cwd: Path, mode: str, *, run_id: str | None = None
) -> run_control_uc.EnqueueResult:
    directory = resolve_run_directory(cwd, run_id)
    inbox = FileRunControl(directory.inbox)
    meta = directory.read_meta()
    result = run_control_uc.request_set_permission_mode(inbox, mode, run_id=meta.run_id)
    _logger().info("ops.permission_mode_enqueued", run_id=result.run_id, mode=mode)
    return result


def enqueue_cwd(cwd: Path, path: str, *, run_id: str | None = None) -> run_control_uc.EnqueueResult:
    directory = resolve_run_directory(cwd, run_id)
    inbox = FileRunControl(directory.inbox)
    meta = directory.read_meta()
    result = run_control_uc.request_set_cwd(inbox, path, run_id=meta.run_id)
    _logger().info("ops.cwd_enqueued", run_id=result.run_id, path=path)
    return result


def enqueue_slash(
    cwd: Path, text: str, *, run_id: str | None = None
) -> run_control_uc.EnqueueResult:
    directory = resolve_run_directory(cwd, run_id)
    inbox = FileRunControl(directory.inbox)
    meta = directory.read_meta()
    result = run_control_uc.request_slash(inbox, text, run_id=meta.run_id)
    _logger().info("ops.slash_enqueued", run_id=result.run_id, text_len=len(text))
    return result


def enqueue_tool_decision(
    cwd: Path,
    request_id: str,
    *,
    allow: bool,
    reason: str = "",
    run_id: str | None = None,
) -> run_control_uc.EnqueueResult:
    directory = resolve_run_directory(cwd, run_id)
    inbox = FileRunControl(directory.inbox)
    meta = directory.read_meta()
    result = run_control_uc.request_tool_decision(
        inbox, request_id, allow=allow, reason=reason, run_id=meta.run_id
    )
    _logger().info(
        "ops.tool_decision_enqueued",
        run_id=result.run_id,
        command_type=result.command_type,
        request_id=request_id,
    )
    return result


def enqueue_resource(
    cwd: Path,
    *,
    action: str,
    kind: str,
    value: str,
    name: str | None = None,
    run_id: str | None = None,
) -> run_control_uc.EnqueueResult:
    directory = resolve_run_directory(cwd, run_id)
    inbox = FileRunControl(directory.inbox)
    meta = directory.read_meta()
    result = run_control_uc.request_resource_mutate(
        inbox,
        action=action,
        kind=kind,
        value=value,
        name=name,
        run_id=meta.run_id,
    )
    _logger().info(
        "ops.resource_enqueued",
        run_id=result.run_id,
        action=action,
        kind=kind,
    )
    return result


def enqueue_response_feedback(
    cwd: Path, verdict: str, *, note: str = "", run_id: str | None = None
) -> run_control_uc.EnqueueResult:
    directory = resolve_run_directory(cwd, run_id)
    inbox = FileRunControl(directory.inbox)
    meta = directory.read_meta()
    result = run_control_uc.request_response_feedback(inbox, verdict, note=note, run_id=meta.run_id)
    _logger().info(
        "ops.response_feedback_enqueued",
        run_id=result.run_id,
        verdict=verdict,
    )
    return result


def enqueue_response_retry(cwd: Path, *, run_id: str | None = None) -> run_control_uc.EnqueueResult:
    directory = resolve_run_directory(cwd, run_id)
    inbox = FileRunControl(directory.inbox)
    meta = directory.read_meta()
    result = run_control_uc.request_response_retry(inbox, run_id=meta.run_id)
    _logger().info("ops.response_retry_enqueued", run_id=result.run_id)
    return result


def get_resource_store(cwd: Path, run_id: str | None = None) -> RunResourceStore:
    directory = resolve_run_directory(cwd, run_id)
    store = RunResourceStore(directory.resources_root)
    store.ensure()
    return store


def _chat_store(cwd: Path) -> ChatMetaStore:
    return ChatMetaStore(cwd / ".claudeloop" / "chats")


def memory_list(cwd: Path, run_id: str | None = None) -> list[dict[str, str]]:
    return get_resource_store(cwd, run_id).list_memories()


def memory_get(cwd: Path, name: str, run_id: str | None = None) -> str:
    return get_resource_store(cwd, run_id).get_memory(name)


def memory_set(cwd: Path, name: str, body: str, run_id: str | None = None) -> Path:
    path = get_resource_store(cwd, run_id).set_memory(name, body)
    _logger().info("ops.memory_set", name=name, path=str(path))
    return path


def memory_rm(cwd: Path, name: str, run_id: str | None = None) -> None:
    get_resource_store(cwd, run_id).remove_memory(name)
    _logger().info("ops.memory_rm", name=name)


def artifact_list(cwd: Path, run_id: str | None = None) -> list[str]:
    return get_resource_store(cwd, run_id).list_artifacts()


def artifact_get(cwd: Path, name: str, run_id: str | None = None) -> Path:
    return get_resource_store(cwd, run_id).get_artifact(name)


def artifact_put(cwd: Path, name: str, source: Path, run_id: str | None = None) -> Path:
    path = get_resource_store(cwd, run_id).put_artifact(name, source)
    _logger().info("ops.artifact_put", name=name, path=str(path))
    return path


def artifact_rm(cwd: Path, name: str, run_id: str | None = None) -> None:
    get_resource_store(cwd, run_id).remove_artifact(name)
    _logger().info("ops.artifact_rm", name=name)


def chat_list(cwd: Path) -> list[dict[str, Any]]:
    return [m.to_dict() for m in _chat_store(cwd).list_all()]


def chat_show(cwd: Path, session_id: str) -> dict[str, Any]:
    return _chat_store(cwd).get(session_id).to_dict()


def chat_rename(cwd: Path, session_id: str, alias: str) -> dict[str, Any]:
    return _chat_store(cwd).rename(session_id, alias).to_dict()


def chat_delete(cwd: Path, session_id: str) -> bool:
    return _chat_store(cwd).delete(session_id)


def chat_pin(cwd: Path, session_id: str) -> dict[str, Any]:
    return _chat_store(cwd).set_pinned(session_id, True).to_dict()


def chat_unpin(cwd: Path, session_id: str) -> dict[str, Any]:
    return _chat_store(cwd).set_pinned(session_id, False).to_dict()


def chat_unread(cwd: Path, session_id: str) -> dict[str, Any]:
    return _chat_store(cwd).set_unread(session_id, True).to_dict()


def chat_read(cwd: Path, session_id: str) -> dict[str, Any]:
    return _chat_store(cwd).set_unread(session_id, False).to_dict()


def chat_share(cwd: Path, session_id: str) -> dict[str, str]:
    bundle_dir = cwd / ".claudeloop" / "shares"
    return _chat_store(cwd).share(session_id, bundle_dir=bundle_dir)


def chat_project(cwd: Path, session_id: str, project: str) -> dict[str, Any]:
    return _chat_store(cwd).set_project(session_id, project).to_dict()


def last_response_text(cwd: Path, run_id: str | None = None) -> str:
    import json

    directory = resolve_run_directory(cwd, run_id)
    path = directory.events_path
    if not path.is_file():
        return ""
    for line in reversed(path.read_text(encoding="utf-8").splitlines()):
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        et = str(record.get("event_type") or "")
        payload = record.get("payload") or {}
        if not isinstance(payload, dict):
            continue
        if et == "chatter.assistant":
            text = payload.get("text")
            if isinstance(text, str) and text.strip():
                return text
        if et == "sdk.message" and payload.get("type") == "ResultMessage":
            result = payload.get("result")
            if isinstance(result, str) and result.strip():
                return result
    return ""


def copy_response(cwd: Path, run_id: str | None = None) -> str:
    return last_response_text(cwd, run_id)


def research_status(cwd: Path, run_id: str | None = None) -> list[dict[str, Any]]:
    return get_resource_store(cwd, run_id).research_status()


def list_runs(cwd: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for directory in list_run_directories(cwd):
        meta = directory.read_meta()
        status = meta.status
        if status in {"active", "waiting"} and not _pid_alive(meta.pid):
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
                "session_id": meta.session_id,
                "started_at": meta.started_at,
                "path": str(directory.root),
            }
        )
    return rows


def run_status(cwd: Path, run_id: str | None = None) -> dict[str, Any]:
    directory = resolve_run_directory(cwd, run_id)
    meta = directory.read_meta()
    status = meta.status
    pid_alive = _pid_alive(meta.pid)
    if status in {"active", "waiting"} and not pid_alive:
        status = "orphaned"
        with contextlib.suppress(OSError):
            directory.update_meta(status="orphaned")
    status_path = directory.root / "status.json"
    live: dict[str, Any] = {}
    if status_path.is_file():
        live = json.loads(status_path.read_text(encoding="utf-8"))
    latest_snap = directory.snapshots_root / "latest.json"
    reported = status if status == "orphaned" else live.get("status", status)
    return {
        "run_id": meta.run_id,
        "status": reported,
        "pid": meta.pid,
        "pid_alive": pid_alive,
        "phase": live.get("phase", meta.phase),
        "attempt": live.get("attempt", meta.attempt),
        "waiting_until": meta.waiting_until,
        "session_id": live.get("session_id", meta.session_id),
        "model": live.get("model", meta.model),
        "effort": live.get("effort", meta.effort),
        "preset": live.get("preset", meta.preset),
        "capacity": live.get("capacity", meta.capacity),
        "plan_path": meta.plan_path,
        "started_at": meta.started_at,
        "turns_spent": live.get("turns_spent"),
        "dollars_spent": live.get("dollars_spent"),
        "events_path": str(directory.events_path),
        "status_path": str(status_path),
        "bus_path": str(directory.root / "bus.jsonl"),
        "stop_summary_path": str(directory.stop_summary_path),
        "snapshot_latest_path": str(latest_snap) if latest_snap.is_file() else None,
        "snapshot_path": live.get("snapshot_path"),
        "snapshot_digest": live.get("snapshot_digest"),
        "snapshot_reason": live.get("snapshot_reason"),
    }


def emit_snapshot(
    cwd: Path,
    *,
    run_id: str | None = None,
    bundle: bool = True,
    out: Path | None = None,
) -> SnapshotRef:
    """Write a manual handoff snapshot for a run; optionally copy JSON to ``out``."""
    directory = resolve_run_directory(cwd, run_id)
    state_bus = FileStateBus(
        status_path=directory.root / "status.json",
        bus_path=directory.root / "bus.jsonl",
        run_id=directory.read_meta().run_id,
    )
    builder = RunSnapshotBuilder(directory, state_bus=state_bus)
    ref = builder.emit("manual", bundle=bundle)
    if ref is None:  # pragma: no cover - manual never digest-skips
        raise RuntimeError("snapshot emit produced no ref")
    if out is not None:
        src = directory.root / ref.path
        if not src.is_file() and (directory.snapshots_root / "latest.json").is_file():
            src = directory.snapshots_root / "latest.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, out)
    _logger().info(
        "ops.snapshot_written",
        run_id=directory.read_meta().run_id,
        path=ref.path,
        digest=ref.digest,
        bundle_path=ref.bundle_path,
    )
    return ref


def watch_bus(
    cwd: Path,
    *,
    run_id: str | None = None,
    follow: bool = True,
    poll_seconds: float = 0.25,
) -> None:
    """Print bus.jsonl (state publications) to stdout; optionally follow."""
    import sys
    import time

    directory = resolve_run_directory(cwd, run_id)
    path = directory.root / "bus.jsonl"
    offset = 0
    while True:
        if path.is_file():
            with path.open("r", encoding="utf-8") as f:
                f.seek(offset)
                chunk = f.read()
                if chunk:
                    sys.stdout.write(chunk)
                    sys.stdout.flush()
                    offset = f.tell()
        if not follow:
            return
        time.sleep(poll_seconds)


def list_savepoints(cwd: Path, run_id: str | None = None) -> list[dict[str, Any]]:
    directory = resolve_run_directory(cwd, run_id)
    meta = directory.read_meta()
    store = GitSavePointStore(cwd=cwd, index_path=directory.savepoints_path)
    return [
        {
            "n": p.n,
            "ref": p.ref,
            "sha": p.sha,
            "label": p.label,
            "at": p.at.isoformat(),
        }
        for p in store.list_points(meta.run_id)
    ]


def unwind_savepoint(
    cwd: Path,
    to: str,
    *,
    backup: bool = True,
    run_id: str | None = None,
) -> dict[str, Any]:
    directory = resolve_run_directory(cwd, run_id)
    meta = directory.read_meta()
    if meta.status == "active":
        try:
            os.kill(meta.pid, 0)
            alive = True
        except ProcessLookupError:
            alive = False
        except PermissionError:  # pragma: no cover
            alive = True
        if alive:
            raise RuntimeError(
                f"run {meta.run_id} is still active (pid {meta.pid}); "
                "stop it before unwinding save points"
            )
    store = GitSavePointStore(cwd=cwd, index_path=directory.savepoints_path)
    result = store.unwind(run_id=meta.run_id, to=to, backup=backup)
    out = {
        "to_n": result.to.n,
        "to_sha": result.to.sha,
        "backup_ref": result.backup_ref,
        "restored_sha": result.restored_sha,
    }
    _logger().info(
        "ops.unwind",
        run_id=meta.run_id,
        to=to,
        to_n=out["to_n"],
        backup_ref=out["backup_ref"],
        restored_sha=out["restored_sha"],
    )
    return out


def reset_project_state(cwd: Path, *, yes: bool) -> dict[str, Any]:
    """Delete the entire project `.claudeloop/` tree.

    Refuses without ``yes=True``. Refuses if any run still has a live pid.
    Never touches the git worktree or ``~/.claude/``.
    """
    root = cwd / ".claudeloop"
    if not yes:
        raise ValueError("refusing to reset without --yes")
    if not root.exists():
        raise FileNotFoundError(f"no control plane at {root}")
    for directory in list_run_directories(cwd):
        meta = directory.read_meta()
        if meta.status in {"active", "waiting"} and _pid_alive(meta.pid):
            raise RuntimeError(
                f"run {meta.run_id} is still active (pid {meta.pid}); "
                "stop it with `claudeloop stop` before reset"
            )
    shutil.rmtree(root)
    _logger().info("ops.reset", path=str(root))
    return {"path": str(root)}


def tail_events(
    cwd: Path,
    *,
    run_id: str | None = None,
    follow: bool = False,
    since_bytes: int = 0,
    poll_seconds: float = 0.25,
    chatter_only: bool = False,
) -> None:
    import json
    import sys

    directory = resolve_run_directory(cwd, run_id)
    path = directory.events_path
    offset = since_bytes
    while True:
        if path.is_file():
            with path.open("r", encoding="utf-8") as f:
                f.seek(offset)
                chunk = f.read()
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
                    offset = f.tell()
        if not follow:
            return
        time.sleep(poll_seconds)
