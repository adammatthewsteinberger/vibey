# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Run handoff snapshot builder — JSON plus an optional portable bundle."""

from __future__ import annotations

import json
import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

from agyloop.domain.snapshot import (
    BUNDLE_REASONS,
    IMMUTABLE_REASONS,
    SNAPSHOT_SCHEMA_VERSION,
    SnapshotReason,
    SnapshotRef,
    digest_payload,
)
from agyloop.infrastructure.redact import redact
from agyloop.infrastructure.rundir import RunDirectory


class RunSnapshotBuilder:
    """Assemble and write run handoff snapshots under ``snapshots/``."""

    def __init__(self, run_dir: RunDirectory, *, clock: Any | None = None) -> None:
        self._run_dir = run_dir
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
        want_bundle = reason in BUNDLE_REASONS if bundle is None else bundle
        payload = self._build_payload(reason, ctx)
        digest = digest_payload(payload)

        if reason == "status" and digest == self._latest_digest:
            return None

        rel_latest = "snapshots/latest.json"
        latest_path = self._run_dir.root / rel_latest
        latest_path.parent.mkdir(parents=True, exist_ok=True)
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
            bundle_rel = self._write_bundle(reason, payload)

        published_rel = rel_immutable or rel_latest
        del immutable_path
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
        return datetime.now(UTC)

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
        savepoints = _load_savepoints(self._run_dir.savepoints_path)
        conversation_id = ctx.get("session_id") or meta.conversation_id
        status = {
            "phase": ctx.get("phase", meta.phase),
            "status": ctx.get("status", meta.status),
            "session_id": conversation_id,
            "conversation_id": conversation_id,
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
        payload: dict[str, Any] = {
            "schema_version": SNAPSHOT_SCHEMA_VERSION,
            "reason": reason,
            "produced_at": self._now().isoformat(),
            "run_id": meta.run_id,
            "meta": meta.to_dict(),
            "status": status,
            "plan": {
                "plan_path": meta.plan_path,
                "remaining_items": list(ctx.get("remaining_plan_items") or []),
                "remaining_work": list(ctx.get("remaining_work") or []),
            },
            "profile": {
                "model": status["model"],
                "effort": status["effort"],
                "preset": status["preset"],
            },
            "cwd": meta.cwd,
            "budget": {
                "turns_spent": ctx.get("turns_spent"),
                "dollars_spent": ctx.get("dollars_spent"),
                "max_turns": ctx.get("max_turns"),
                "max_dollars": ctx.get("max_dollars"),
                "max_attempts": ctx.get("max_attempts"),
            },
            "savepoints": savepoints,
            "paths": {
                "events": "events.jsonl",
                "savepoints": "savepoints.jsonl",
            },
        }
        return cast(dict[str, Any], redact(payload))

    def _write_bundle(self, reason: SnapshotReason, payload: dict[str, Any]) -> str | None:
        ts = self._now().strftime("%Y%m%dT%H%M%S%fZ")
        rel = f"snapshots/bundles/{ts}-{reason}"
        bundle_root = self._run_dir.root / rel
        try:
            bundle_root.mkdir(parents=True, exist_ok=True)
            (bundle_root / "snapshot.json").write_text(
                json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8"
            )
            plan_copy = self._run_dir.root / "plan.md"
            if plan_copy.is_file():
                shutil.copy2(plan_copy, bundle_root / "plan.md")
        except OSError:
            return None
        return rel


def _load_savepoints(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    rows: list[dict[str, Any]] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        try:
            rows.append(json.loads(stripped))
        except json.JSONDecodeError:
            break
    return rows[-20:]
