# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Run handoff snapshot builder — JSON + optional bundle + Claude transcript."""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from claudeloop.application.ports import StateBus
from claudeloop.domain.snapshot import (
    BUNDLE_REASONS,
    IMMUTABLE_REASONS,
    SNAPSHOT_SCHEMA_VERSION,
    SnapshotReason,
    SnapshotRef,
    digest_payload,
)
from claudeloop.infrastructure.redact import redact
from claudeloop.infrastructure.resources.store import RunResourceStore
from claudeloop.infrastructure.rundir import RunDirectory


def sanitize_cwd_for_project_dir(cwd: str) -> str:
    """Claude Code project dir slug: every ``/`` becomes ``-`` (best-effort)."""
    return cwd.replace("/", "-")


def claude_projects_dir(*, home: Path | None = None) -> Path:
    return (home or Path.home()) / ".claude" / "projects"


def locate_claude_transcript(
    *,
    session_id: str | None,
    cwd: str | None,
    home: Path | None = None,
) -> dict[str, Any]:
    """Best-effort locate a Claude Code ``*.jsonl`` transcript for this session."""
    if not session_id:
        return {"found": False, "reason": "no session_id"}
    if not cwd:
        return {"found": False, "reason": "no cwd", "session_id": session_id}
    project = claude_projects_dir(home=home) / sanitize_cwd_for_project_dir(cwd)
    if not project.is_dir():
        return {
            "found": False,
            "reason": "project_dir_missing",
            "session_id": session_id,
            "project_dir": str(project),
        }
    candidate = project / f"{session_id}.jsonl"
    if candidate.is_file():
        return {
            "found": True,
            "session_id": session_id,
            "transcript_path": str(candidate),
            "project_dir": str(project),
        }
    # Fall back: any jsonl whose stem matches / contains session id
    matches = sorted(
        (p for p in project.glob("*.jsonl") if session_id in p.stem),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if matches:
        return {
            "found": True,
            "session_id": session_id,
            "transcript_path": str(matches[0]),
            "project_dir": str(project),
        }
    return {
        "found": False,
        "reason": "transcript_missing",
        "session_id": session_id,
        "project_dir": str(project),
    }


class RunSnapshotBuilder:
    """Assemble, write, and bus-publish run handoff snapshots."""

    def __init__(
        self,
        run_dir: RunDirectory,
        *,
        state_bus: StateBus,
        home: Path | None = None,
        clock: Any | None = None,
    ) -> None:
        self._run_dir = run_dir
        self._bus = state_bus
        self._home = home
        self._clock = clock
        self._snapshots = run_dir.snapshots_root
        self._snapshots.mkdir(parents=True, exist_ok=True)
        self._latest_digest: str | None = self._read_latest_digest()

    def emit(
        self,
        reason: SnapshotReason,
        *,
        context: dict[str, Any] | None = None,
        bundle: bool | None = None,
    ) -> SnapshotRef | None:
        ctx = dict(context or {})
        want_bundle = BUNDLE_REASONS.__contains__(reason) if bundle is None else bundle
        payload = self._build_payload(reason, ctx)
        digest = digest_payload(payload)

        if reason == "status" and digest == self._latest_digest:
            return None

        rel_latest = "snapshots/latest.json"
        latest_path = self._run_dir.root / rel_latest
        latest_path.write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")
        self._latest_digest = digest

        immutable_path: Path | None = None
        rel_immutable: str | None = None
        if reason in IMMUTABLE_REASONS:
            ts = self._now().strftime("%Y%m%dT%H%M%S%fZ")
            rel_immutable = f"snapshots/{ts}-{reason}.json"
            immutable_path = self._run_dir.root / rel_immutable
            immutable_path.write_text(
                json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8"
            )

        bundle_rel: str | None = None
        if want_bundle:
            bundle_rel = self._write_bundle(reason, payload, ctx)

        published_rel = rel_immutable or rel_latest
        event_type = "snapshot.written" if reason in IMMUTABLE_REASONS else "snapshot.latest"
        self._bus.publish(
            event_type,
            {
                "snapshot_path": published_rel,
                "snapshot_digest": digest,
                "snapshot_reason": reason,
                "latest_path": rel_latest,
                **({"bundle_path": bundle_rel} if bundle_rel else {}),
            },
        )
        return SnapshotRef(
            path=published_rel,
            digest=digest,
            reason=reason,
            immutable=reason in IMMUTABLE_REASONS,
            bundle_path=bundle_rel,
        )

    def _now(self) -> datetime:
        if self._clock is not None:
            now = self._clock.now()
            if not isinstance(now, datetime):
                raise TypeError(f"clock.now() must return datetime, got {type(now)!r}")
            return now
        return datetime.now(timezone.utc)

    def _read_latest_digest(self) -> str | None:
        path = self._snapshots / "latest.json"
        if not path.is_file():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        if isinstance(data, dict):
            return digest_payload(data)
        return None

    def _build_payload(self, reason: SnapshotReason, ctx: dict[str, Any]) -> dict[str, Any]:
        meta = self._run_dir.read_meta()
        store = RunResourceStore(self._run_dir.resources_root)
        resources = store.snapshot().to_dict()
        attachment_inventory = [
            {
                "name": p.name,
                "size": p.stat().st_size,
                "path": f"resources/attachments/{p.name}",
            }
            for p in sorted(store.attachments_dir.iterdir())
            if p.is_file()
        ]
        memories = _safe_json(store.memories_index)
        artifacts = (
            sorted(p.name for p in store.artifacts_dir.iterdir() if p.is_file())
            if store.artifacts_dir.is_dir()
            else []
        )
        savepoints = _load_savepoints(self._run_dir.savepoints_path)
        session_id = ctx.get("session_id") or meta.session_id
        cwd = ctx.get("cwd") or meta.cwd
        claude = locate_claude_transcript(
            session_id=session_id if isinstance(session_id, str) else None,
            cwd=cwd if isinstance(cwd, str) else None,
            home=self._home,
        )
        # Copy transcript into snapshots/claude/ when found (standalone JSON still works)
        if claude.get("found") and claude.get("transcript_path"):
            copied = self._copy_claude_transcript(
                Path(str(claude["transcript_path"])),
                str(claude.get("session_id") or session_id),
            )
            if copied:
                claude = {**claude, "transcript_copied": copied}

        status = {
            "phase": ctx.get("phase", meta.phase),
            "status": ctx.get("status", meta.status),
            "session_id": session_id,
            "attempt": ctx.get("attempt", meta.attempt),
            "turns_spent": ctx.get("turns_spent"),
            "dollars_spent": ctx.get("dollars_spent"),
            "probe_count": ctx.get("probe_count"),
            "started_waiting_at": ctx.get("started_waiting_at"),
            "waiting_until": ctx.get("waiting_until", meta.waiting_until),
            "model": ctx.get("model", meta.model),
            "effort": ctx.get("effort", meta.effort),
            "preset": ctx.get("preset", meta.preset),
            "capacity": ctx.get("capacity", meta.capacity),
        }
        profile = {
            "model": status["model"],
            "effort": status["effort"],
            "preset": status["preset"],
        }
        plan = {
            "plan_path": meta.plan_path,
            "remaining_items": list(ctx.get("remaining_plan_items") or []),
            "remaining_work": list(ctx.get("remaining_work") or []),
        }
        budget = {
            "turns_spent": ctx.get("turns_spent"),
            "dollars_spent": ctx.get("dollars_spent"),
            "max_turns": ctx.get("max_turns"),
            "max_dollars": ctx.get("max_dollars"),
            "max_attempts": ctx.get("max_attempts"),
        }
        paths = {
            "events": "events.jsonl",
            "audit": "audit.jsonl",
            "bus": "bus.jsonl",
            "status": "status.json",
            "stop_summary": "stop-summary.md",
            "savepoints": "savepoints.jsonl",
        }
        payload: dict[str, Any] = {
            "schema_version": SNAPSHOT_SCHEMA_VERSION,
            "reason": reason,
            "produced_at": self._now().isoformat(),
            "run_id": meta.run_id,
            "meta": meta.to_dict(),
            "status": status,
            "resources": {**resources, "attachment_inventory": attachment_inventory},
            "memories": memories,
            "artifacts": artifacts,
            "plan": plan,
            "profile": profile,
            "permission_mode": resources.get("permission_mode"),
            "cwd": resources.get("cwd") or meta.cwd,
            "budget": budget,
            "savepoints": savepoints,
            "paths": paths,
            "claude_session": claude,
        }
        return redact(payload)

    def _copy_claude_transcript(self, src: Path, session_id: str) -> str | None:
        dest_dir = self._snapshots / "claude"
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / f"{session_id}.jsonl"
        try:
            shutil.copy2(src, dest)
        except OSError:
            return None
        return f"snapshots/claude/{session_id}.jsonl"

    def _write_bundle(
        self, reason: SnapshotReason, payload: dict[str, Any], ctx: dict[str, Any]
    ) -> str | None:
        ts = self._now().strftime("%Y%m%dT%H%M%S%fZ")
        rel = f"snapshots/bundles/{ts}-{reason}"
        bundle_root = self._run_dir.root / rel
        try:
            bundle_root.mkdir(parents=True, exist_ok=True)
            (bundle_root / "snapshot.json").write_text(
                json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8"
            )
            for name in ("attachments",):
                src = self._run_dir.resources_root / name
                if src.is_dir():
                    dest = bundle_root / "resources" / name
                    if dest.exists():
                        shutil.rmtree(dest)
                    shutil.copytree(src, dest)
            for name in ("memories", "artifacts"):
                src = self._run_dir.root / name
                if src.is_dir():
                    dest = bundle_root / name
                    if dest.exists():
                        shutil.rmtree(dest)
                    shutil.copytree(src, dest)
            claude = payload.get("claude_session") or {}
            copied = claude.get("transcript_copied")
            src_path = claude.get("transcript_path")
            if copied:
                src_file = self._run_dir.root / str(copied)
                if src_file.is_file():
                    dest = bundle_root / "claude" / src_file.name
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src_file, dest)
            elif src_path and Path(str(src_path)).is_file():
                dest = bundle_root / "claude" / Path(str(src_path)).name
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(Path(str(src_path)), dest)
        except OSError:
            return None
        del ctx
        return rel


def _safe_json(path: Path) -> Any:
    if not path.is_file():
        return {"items": []}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"items": [], "error": "unreadable"}


def _load_savepoints(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    rows: list[dict[str, Any]] = []
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    except (OSError, json.JSONDecodeError):
        return rows
    return rows[-20:]
