"""ScriptedEngine: a fake runner that writes the real run-directory shape
(architecture doc §8.1 / rotation-and-engines.md §8.1) without spawning a
process or touching the network. Every later test in M3+ that needs "an
engine" uses this instead of a real vendor binary, and it is what the
conformance suite runs against in CI."""

import json
from collections.abc import AsyncIterator, Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

from vibey.application.dto import (
    EngineEvent,
    PreflightResult,
    RunHandle,
    RunSpec,
    SnapshotRef,
    StopSummary,
)
from vibey.domain.capacity import CapacityState
from vibey.domain.engine import EngineDescriptor
from vibey.domain.job import FailureClass

SCHEMA_VERSION = 1


def _default_script(run_id: UUID, done_marker: str) -> list[dict[str, object]]:
    now = datetime.now(UTC).isoformat()
    return [
        {"kind": "SessionSeeded", "at": now, "payload": {"seed_digest": "deadbeef"}},
        {
            "kind": "TurnCompleted",
            "at": now,
            "payload": {
                "output_digest": "cafebabe",
                "cost_usd": 0.01,
                "tokens_in": 100,
                "tokens_out": 50,
            },
        },
        {
            "kind": "VerdictRendered",
            "at": now,
            "payload": {
                "complete": True,
                "remaining_work": [],
                "blocked_on": None,
                "summary": f"scripted run {run_id} complete",
                "done_marker": done_marker,
            },
        },
    ]


@dataclass(slots=True)
class ScriptedEngine:
    descriptor: EngineDescriptor
    base_dir: Path
    installed: bool = True
    auth_ok: bool = True
    script: list[dict[str, object]] | None = None
    scripts: list[list[dict[str, object]]] | None = None
    """Per-run event scripts, consumed one per ``start`` call in order.
    When the queue is exhausted (or None), ``script`` -- and failing that
    the default script -- covers every remaining run. This is what lets a
    test script "run 1 winds down, run 2 completes" on one engine."""
    exit_code_script: list[int | None] | None = None
    """Per-run exit codes, consumed one per ``start`` in order; runs past
    the end of the queue report None. EXIT_CODE_WIND_DOWN here scripts a
    graceful wind-down for the ``run_exit_code`` capability."""
    stop_remaining: tuple[str, ...] = ()
    """What ``stop`` reports as StopSummary.remaining_work -- the scripted
    stand-in for a real engine's final-snapshot remaining list."""
    help_text: str | None = None
    """`<binary> run --help` output stand-in. Defaults to a string
    containing every flag the descriptor claims, so the conformance
    suite's flags check passes by construction; a test can override this
    with an incomplete string to prove the check catches a real gap."""
    _handles: dict[UUID, Path] = field(default_factory=dict)
    _exit_codes: dict[UUID, int | None] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.help_text is None:
            all_flags = {
                flag
                for invocation in self.descriptor.effort_projection.values()
                for flag in invocation.argv
            }
            for flags in self.descriptor.isolation_flags.values():
                all_flags.update(flags)
            if self.descriptor.plan_flag is not None:
                all_flags.add(self.descriptor.plan_flag)
            self.help_text = " ".join(sorted(all_flags))

    async def preflight(self) -> PreflightResult:
        if not self.installed:
            return PreflightResult(installed=False, version=None, auth_ok=False)
        return PreflightResult(
            installed=True, version=self.descriptor.min_version, auth_ok=self.auth_ok
        )

    async def start(self, spec: RunSpec) -> RunHandle:
        run_dir = self.base_dir / self.descriptor.state_dir / "runs" / str(spec.run_id)
        (run_dir / "inbox").mkdir(parents=True, exist_ok=True)
        (run_dir / "snapshots").mkdir(parents=True, exist_ok=True)

        meta = {
            "run_id": str(spec.run_id),
            "pid": 0,
            "cwd": str(spec.worktree_path),
            "session_id": spec.session_id or f"sess-{spec.run_id}",
            "status": "running",
            "phase": None,
            "attempt": 1,
            "waiting_until": None,
            "model": None,
            "effort": spec.effort.name.lower(),
            "preset": None,
            "capacity": "Available",
        }
        (run_dir / "meta.json").write_text(json.dumps(meta))

        per_run = self.scripts.pop(0) if self.scripts else None
        events = per_run or self.script or _default_script(spec.run_id, self.descriptor.done_marker)
        self._exit_codes[spec.run_id] = (
            self.exit_code_script.pop(0) if self.exit_code_script else None
        )
        with (run_dir / "events.jsonl").open("w") as f:
            for event in events:
                f.write(json.dumps(event) + "\n")

        (run_dir / "audit.jsonl").write_text("")
        (run_dir / "bus.jsonl").write_text("")
        (run_dir / "status.json").write_text(json.dumps({"status": "running"}))
        (run_dir / "savepoints.jsonl").write_text("")
        (run_dir / "stop-summary.md").write_text("")

        snapshot = {
            "schema_version": SCHEMA_VERSION,
            "session_id": meta["session_id"],
            "run_id": str(spec.run_id),
            "remaining_work": [],
        }
        (run_dir / "snapshots" / "latest.json").write_text(json.dumps(snapshot))

        self._handles[spec.run_id] = run_dir
        return RunHandle(
            run_id=spec.run_id, engine_id=self.descriptor.engine_id, run_dir=run_dir, pid=None
        )

    async def tail(self, handle: RunHandle) -> AsyncIterator[EngineEvent]:
        events_path = handle.run_dir / "events.jsonl"
        for line in events_path.read_text().splitlines():
            if not line.strip():
                continue
            raw = json.loads(line)
            yield EngineEvent(
                kind=raw["kind"],
                at=datetime.fromisoformat(raw["at"]),
                payload=raw["payload"],
            )

    async def send_prompt(self, handle: RunHandle, text: str, *, now: bool) -> None:
        inbox = handle.run_dir / "inbox"
        inbox.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%f")
        command = "prompt-now" if now else "prompt-at-break"
        (inbox / f"{ts}-{command}.json").write_text(json.dumps({"command": command, "text": text}))

    def run_exit_code(self, handle: RunHandle) -> int | None:
        return self._exit_codes.get(handle.run_id)

    async def stop(self, handle: RunHandle) -> StopSummary:
        (handle.run_dir / "stop-summary.md").write_text("Scripted run stopped cleanly.\n")
        return StopSummary(
            run_id=handle.run_id,
            complete=True,
            summary="Scripted run stopped cleanly.",
            remaining_work=self.stop_remaining,
        )

    async def snapshot(self, handle: RunHandle) -> SnapshotRef | None:
        path = handle.run_dir / "snapshots" / "latest.json"
        if not path.exists():
            return None
        data = json.loads(path.read_text())
        return SnapshotRef(
            path=path,
            schema_version=data["schema_version"],
            session_id=data.get("session_id"),
        )

    def classify(self, raw: Mapping[str, object]) -> CapacityState:
        from vibey.infrastructure.engines.classify import classify_capacity

        return classify_capacity(self.descriptor.engine_id, raw)

    def attribute(self, exit_code: int, tail: str) -> FailureClass:
        from vibey.infrastructure.engines.classify import attribute_failure

        return attribute_failure(exit_code, tail)


def scripted_available_run(descriptor: EngineDescriptor, base_dir: Path) -> ScriptedEngine:
    return ScriptedEngine(descriptor=descriptor, base_dir=base_dir)
