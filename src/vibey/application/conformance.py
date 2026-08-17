"""`vibey doctor --conformance`: the 9 checks from
rotation-and-engines.md §8.2, run against whatever EngineAdapter is handed
in -- ScriptedEngine in CI, a real adapter locally. A failing check sets
conformance_ok = false and makes the engine ineligible for rotation
(degraded, not broken); it never crashes the caller."""

import asyncio
import tempfile
from collections.abc import Sequence
from pathlib import Path
from uuid import uuid4

from vibey.application.dto import (
    ConformanceCheckResult,
    ConformanceReport,
    RunSpec,
)
from vibey.application.ports import EngineAdapter
from vibey.domain.capacity import CapacityState
from vibey.domain.effort import Effort
from vibey.domain.engine import Capability, EngineDescriptor, IsolationLevel


def _version_at_least(actual: str, minimum: str) -> bool:
    def parts(v: str) -> tuple[int, ...]:
        return tuple(int(p) for p in v.split(".") if p.isdigit())

    return parts(actual) >= parts(minimum)


async def run_conformance(
    adapter: EngineAdapter,
    *,
    capacity_fixtures: Sequence[tuple[str, dict[str, object], type[CapacityState]]] = (),
    trivial_worktree: str | None = None,
    run_dir_poll_seconds: float = 30.0,
) -> ConformanceReport:
    descriptor: EngineDescriptor = adapter.descriptor
    checks: list[ConformanceCheckResult] = []
    if trivial_worktree is None:
        trivial_worktree = str(Path(tempfile.gettempdir()) / "vibey-conformance")

    # 1. binary
    preflight = await adapter.preflight()
    if not preflight.installed:
        checks.append(ConformanceCheckResult("binary", ok=False, detail="not installed"))
    elif preflight.version is None or not _version_at_least(
        preflight.version, descriptor.min_version
    ):
        checks.append(
            ConformanceCheckResult(
                "binary",
                ok=False,
                detail=f"version {preflight.version} < min {descriptor.min_version}",
            )
        )
    else:
        checks.append(ConformanceCheckResult("binary", ok=True))

    # 2. flags
    help_text = getattr(adapter, "help_text", None)
    if help_text is None:
        checks.append(
            ConformanceCheckResult("flags", ok=False, detail="adapter exposes no help text")
        )
    else:
        claimed_flags = {
            flag for invocation in descriptor.effort_projection.values() for flag in invocation.argv
        }
        for flags in descriptor.isolation_flags.values():
            claimed_flags.update(flags)
        missing = sorted(f for f in claimed_flags if f not in help_text)
        checks.append(
            ConformanceCheckResult(
                "flags",
                ok=not missing,
                detail=f"missing from --help: {missing}" if missing else "",
            )
        )

    # A trivial scripted run backs state_dir, run_dir_shape, snapshot_schema,
    # done_marker, control_plane, and structured_verdict.
    handle = None
    try:
        spec = RunSpec(
            run_id=uuid4(),
            worktree_path=Path(trivial_worktree),
            prompt="conformance check",
            effort=Effort.TRIVIAL,
            isolation=IsolationLevel.WORKTREE,
        )
        handle = await adapter.start(spec)
    except Exception as exc:  # noqa: BLE001 - any start() failure fails the run, not this process
        detail = f"adapter.start() raised: {exc}"
        for name in (
            "state_dir",
            "run_dir_shape",
            "snapshot_schema",
            "done_marker",
            "control_plane",
            "structured_verdict",
        ):
            checks.append(ConformanceCheckResult(name, ok=False, detail=detail))
        return ConformanceReport(engine_id=descriptor.engine_id, checks=tuple(checks))

    # 3. state_dir
    checks.append(
        ConformanceCheckResult("state_dir", ok=descriptor.state_dir in str(handle.run_dir))
    )

    # 4. run_dir_shape
    # adapter.start() only spawns the process; a real engine's own startup
    # sequence (SDK client init, first API round-trip, first write) can
    # trail the subprocess spawn by many seconds, more under degraded
    # conditions (rate-limit retries). Poll rather than judging
    # run_dir_shape on whatever happened to exist the instant start()
    # returned -- a ScriptedEngine's files are already there, so this never
    # adds latency to the fake-backed test suite. run_dir_poll_seconds
    # defaults to 30s, matching this module's own stop()-equivalent poll
    # budget elsewhere in the adapter; tests that deliberately model a file
    # that never appears should pass a small value so the negative case
    # doesn't cost real wall-clock time.
    required = ("meta.json", "events.jsonl")
    snapshot_path = handle.run_dir / "snapshots" / "latest.json"
    missing_files = [f for f in required if not (handle.run_dir / f).exists()]
    if missing_files or not snapshot_path.exists():
        step = 0.5
        deadline = asyncio.get_running_loop().time() + run_dir_poll_seconds
        while asyncio.get_running_loop().time() < deadline:
            missing_files = [f for f in required if not (handle.run_dir / f).exists()]
            if not missing_files and snapshot_path.exists():
                break
            await asyncio.sleep(min(step, run_dir_poll_seconds))
    if not snapshot_path.exists():
        missing_files.append("snapshots/latest.json")
    checks.append(
        ConformanceCheckResult(
            "run_dir_shape",
            ok=not missing_files,
            detail=f"missing: {missing_files}" if missing_files else "",
        )
    )

    # 5. snapshot_schema
    snapshot = await adapter.snapshot(handle)
    if snapshot is None:
        checks.append(ConformanceCheckResult("snapshot_schema", ok=False, detail="no snapshot"))
    else:
        checks.append(
            ConformanceCheckResult(
                "snapshot_schema",
                ok=snapshot.schema_version == 1,
                detail=f"schema_version={snapshot.schema_version}"
                if snapshot.schema_version != 1
                else "",
            )
        )

    # 6. capacity_map
    if not capacity_fixtures:
        checks.append(
            ConformanceCheckResult("capacity_map", ok=True, detail="no fixtures supplied")
        )
    else:
        mismatches = []
        for label, raw, expected_type in capacity_fixtures:
            result = adapter.classify(raw)
            if not isinstance(result, expected_type):
                mismatches.append(
                    f"{label}: expected {expected_type.__name__}, got {type(result).__name__}"
                )
        checks.append(
            ConformanceCheckResult("capacity_map", ok=not mismatches, detail="; ".join(mismatches))
        )

    # 7. done_marker
    done_marker_found = False
    events = [e async for e in adapter.tail(handle)]
    for event in events:
        if str(event.payload.get("done_marker", "")) == descriptor.done_marker:
            done_marker_found = True
    checks.append(
        ConformanceCheckResult(
            "done_marker",
            ok=done_marker_found,
            detail=""
            if done_marker_found
            else f"expected {descriptor.done_marker!r} in a verdict event",
        )
    )

    # 8. control_plane
    try:
        await adapter.send_prompt(handle, "conformance check prompt", now=True)
        inbox = handle.run_dir / "inbox"
        control_plane_ok = inbox.is_dir() and any(inbox.iterdir())
    except Exception as exc:  # noqa: BLE001 - a raising adapter fails this check, not the suite
        control_plane_ok = False
        checks.append(ConformanceCheckResult("control_plane", ok=False, detail=str(exc)))
    else:
        checks.append(ConformanceCheckResult("control_plane", ok=control_plane_ok))

    # 9. structured_verdict
    if Capability.STRUCTURED_VERDICT not in descriptor.capabilities:
        checks.append(ConformanceCheckResult("structured_verdict", ok=True, detail="not claimed"))
    else:
        verdict_events = [e for e in events if e.kind == "VerdictRendered"]
        checks.append(
            ConformanceCheckResult(
                "structured_verdict",
                ok=bool(verdict_events)
                and all(isinstance(e.payload, dict) for e in verdict_events),
                detail="" if verdict_events else "no VerdictRendered event in scripted run",
            )
        )

    return ConformanceReport(engine_id=descriptor.engine_id, checks=tuple(checks))
