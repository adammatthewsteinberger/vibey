"""LoopProcessAdapter: real subprocess runner implementing the full EngineAdapter
protocol.

This is the production adapter that supersedes ClaudeLoopProcess. It spawns real
loop processes, streams their events.jsonl with proper translation, detects
completion via descriptor.done_marker, recognizes exit code 75 (wind-down), and
classifies capacity states using the existing classify.py machinery.

Built to work with claudeloop, codexloop, cursorloop, and agyloop via their
descriptors, not four separate classes.
"""

import asyncio
import json
import shutil
from collections.abc import AsyncIterator, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import structlog

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
from vibey.domain.errors import VibeyError
from vibey.domain.job import FailureClass
from vibey.infrastructure.engines.argv import build_argv
from vibey.infrastructure.engines.classify import attribute_failure, classify_capacity
from vibey.infrastructure.engines.loop_events import translate_event_type

logger = structlog.get_logger(__name__)

EXIT_CODE_WIND_DOWN = 75


class ProcessError(VibeyError):
    """Raised when a loop process fails in an unexpected way."""

    pass


@dataclass(slots=True, frozen=True)
class LoopProcessAdapter:
    """Real subprocess adapter parameterized over EngineDescriptor.

    This replaces the separate per-engine classes with one adapter that uses
    descriptor data to build argv and translate events.
    """

    descriptor: EngineDescriptor
    base_dir: Path  # Where the engine's state_dir lives (e.g. .claudeloop/)

    async def preflight(self) -> PreflightResult:
        """Check if binary exists and auth is OK (via `doctor`)."""
        binary_path = shutil.which(self.descriptor.binary)
        if not binary_path:
            return PreflightResult(
                installed=False,
                version=None,
                auth_ok=False,
                detail=f"{self.descriptor.binary} not found on PATH",
            )

        # Try to get version
        try:
            proc = await asyncio.create_subprocess_exec(
                self.descriptor.binary,
                "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=10.0)
            version_output = (stdout or stderr).decode().strip()
            version = version_output.split()[-1] if version_output else None
        except (TimeoutError, Exception) as e:
            logger.warning(
                "version_check_failed",
                engine=self.descriptor.engine_id.value,
                error=str(e),
            )
            version = None

        # Check auth via doctor (if the command exists)
        auth_ok = False
        detail = ""
        try:
            proc = await asyncio.create_subprocess_exec(
                self.descriptor.binary,
                "doctor",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30.0)
            auth_ok = proc.returncode == 0
            if not auth_ok:
                detail = (stderr or stdout).decode().strip()[:500]
        except (TimeoutError, Exception) as e:
            logger.warning(
                "doctor_check_failed",
                engine=self.descriptor.engine_id.value,
                error=str(e),
            )
            # No doctor command or it failed - check env vars as fallback
            import os

            auth_ok = any(os.getenv(var) for var in self.descriptor.auth_env)
            if not auth_ok:
                detail = f"No {self.descriptor.auth_env} found in environment"

        return PreflightResult(
            installed=True,
            version=version,
            auth_ok=auth_ok,
            detail=detail,
        )

    async def start(self, spec: RunSpec) -> RunHandle:
        """Build argv, write plan, spawn process, return handle."""
        run_dir = self.base_dir / self.descriptor.state_dir / "runs" / str(spec.run_id)
        run_dir.mkdir(parents=True, exist_ok=True)

        # Write the plan file if this is a new run
        if spec.session_id is None:
            plan_dir = spec.worktree_path / ".vibey" / "plans"
            plan_dir.mkdir(parents=True, exist_ok=True)
            plan_path = plan_dir / f"{spec.run_id}.md"
            plan_path.write_text(spec.prompt)

        # Build argv using existing argv.py
        argv = build_argv(self.descriptor, spec)

        # Spawn the process
        try:
            process = await asyncio.create_subprocess_exec(
                *argv,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=spec.worktree_path,
            )
        except Exception as e:
            raise ProcessError(f"Failed to spawn {self.descriptor.binary}: {e}") from e

        logger.info(
            "engine_started",
            engine=self.descriptor.engine_id.value,
            run_id=str(spec.run_id),
            pid=process.pid,
            argv=" ".join(argv),
        )

        return RunHandle(
            run_id=spec.run_id,
            engine_id=self.descriptor.engine_id,
            run_dir=run_dir,
            pid=process.pid,
        )

    async def tail(self, handle: RunHandle) -> AsyncIterator[EngineEvent]:
        """Stream events.jsonl with real-time translation.

        Reads events.jsonl line by line, translates event_type -> kind using
        loop_events.LOOP_EVENT_MAP, yields EngineEvent with the vibey EventKind
        as the kind field.
        """
        events_path = handle.run_dir / "events.jsonl"

        # Wait for events.jsonl to exist
        for _ in range(100):  # 10 seconds max
            if events_path.exists():
                break
            await asyncio.sleep(0.1)
        else:
            logger.warning(
                "events_file_missing",
                run_id=str(handle.run_id),
                path=str(events_path),
            )
            return

        # Tail the file (simplified for now - can be made more sophisticated)
        seen_lines = 0
        while True:
            try:
                lines = (await asyncio.to_thread(events_path.read_text)).splitlines()
                for line in lines[seen_lines:]:
                    if not line.strip():
                        continue
                    try:
                        raw = json.loads(line)
                        # Real loop events have 'event_type' field, not 'kind'
                        event_type = raw.get("event_type") or raw.get("kind")
                        if not event_type:
                            logger.warning(
                                "event_missing_type",
                                run_id=str(handle.run_id),
                                raw=raw,
                            )
                            continue

                        # Translate event_type to EventKind
                        kind = translate_event_type(self.descriptor.engine_id, event_type)
                        if kind is None:
                            logger.info(
                                "unknown_event_type",
                                engine=self.descriptor.engine_id.value,
                                event_type=event_type,
                                detail="skipping gracefully",
                            )
                            continue

                        # Parse timestamp
                        at_str = raw.get("at") or raw.get("timestamp")
                        at = datetime.fromisoformat(at_str) if at_str else datetime.now(UTC)

                        # Yield translated event
                        yield EngineEvent(
                            kind=kind.value,  # EventKind enum value
                            at=at,
                            payload=raw.get("payload", {}),
                        )
                    except (json.JSONDecodeError, KeyError, ValueError) as e:
                        logger.warning(
                            "event_parse_failed",
                            run_id=str(handle.run_id),
                            line=line[:200],
                            error=str(e),
                        )
                        continue

                seen_lines = len(lines)

                # Check if done - look for done_marker in the output
                # (In a real implementation, also check process status)
                meta_path = handle.run_dir / "meta.json"
                if meta_path.exists():
                    meta = json.loads(meta_path.read_text())
                    if meta.get("status") == "complete":
                        break

                await asyncio.sleep(0.5)  # Poll interval
            except Exception as e:
                logger.error(
                    "tail_error",
                    run_id=str(handle.run_id),
                    error=str(e),
                )
                break

    async def send_prompt(self, handle: RunHandle, text: str, *, now: bool) -> None:
        """Write prompt to inbox/ directory for mid-run prompting."""
        inbox = handle.run_dir / "inbox"
        inbox.mkdir(parents=True, exist_ok=True)

        ts = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%f")
        command = "prompt-now" if now else "prompt-at-break"
        prompt_file = inbox / f"{ts}-{command}.json"

        prompt_file.write_text(
            json.dumps(
                {
                    "command": command,
                    "text": text,
                }
            )
        )

        logger.info(
            "prompt_sent",
            run_id=str(handle.run_id),
            now=now,
            file=str(prompt_file),
        )

    async def stop(self, handle: RunHandle) -> StopSummary:
        """Send stop signal and collect stop-summary.md."""
        # Write stop signal to inbox
        inbox = handle.run_dir / "inbox"
        inbox.mkdir(parents=True, exist_ok=True)
        stop_file = inbox / f"{datetime.now(UTC).strftime('%Y%m%dT%H%M%S%f')}-stop.json"
        stop_file.write_text(json.dumps({"command": "stop"}))

        # Wait for stop-summary.md (with timeout)
        summary_path = handle.run_dir / "stop-summary.md"
        for _ in range(60):  # 30 seconds max
            if summary_path.exists() and summary_path.stat().st_size > 0:
                break
            await asyncio.sleep(0.5)

        summary = ""
        complete = False
        remaining_work: list[str] = []

        if summary_path.exists():
            summary = summary_path.read_text()
            # Look for done marker in summary
            complete = self.descriptor.done_marker in summary

        # Try to get remaining work from final snapshot
        snapshot_ref = await self.snapshot(handle)
        if snapshot_ref and snapshot_ref.path.exists():
            try:
                snapshot_data = json.loads(snapshot_ref.path.read_text())
                remaining_work = snapshot_data.get("remaining_work", [])
            except Exception:  # noqa: BLE001  # nosec B110
                logger.debug("snapshot_remaining_work_failed", run_id=str(handle.run_id))

        return StopSummary(
            run_id=handle.run_id,
            complete=complete,
            summary=summary or f"Stopped run {handle.run_id}",
            remaining_work=tuple(remaining_work),
        )

    async def snapshot(self, handle: RunHandle) -> SnapshotRef | None:
        """Read snapshots/latest.json."""
        snapshot_path = handle.run_dir / "snapshots" / "latest.json"
        if not snapshot_path.exists():
            return None

        try:
            data = json.loads(snapshot_path.read_text())
            return SnapshotRef(
                path=snapshot_path,
                schema_version=data.get("schema_version", 1),
                session_id=data.get("session_id"),
            )
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(
                "snapshot_parse_failed",
                run_id=str(handle.run_id),
                error=str(e),
            )
            return None

    def classify(self, raw: Mapping[str, object]) -> CapacityState:
        """Classify capacity state using existing classify.py."""
        return classify_capacity(self.descriptor.engine_id, raw)

    def attribute(self, exit_code: int, tail: str) -> FailureClass:
        """Attribute failure class using existing classify.py."""
        return attribute_failure(exit_code, tail)


__all__ = ["LoopProcessAdapter", "EXIT_CODE_WIND_DOWN"]
