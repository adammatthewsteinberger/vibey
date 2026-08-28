# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://hire.adam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
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
import os
import shutil
import subprocess  # nosec B404 - fixed argv, never shell=True
import sys
from collections.abc import AsyncIterator, Mapping
from contextlib import suppress
from dataclasses import dataclass
from datetime import UTC, datetime

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
from vibey.domain.engine import EXIT_CODE_WIND_DOWN, EngineDescriptor, EngineId
from vibey.domain.errors import VibeyError
from vibey.domain.job import FailureClass
from vibey.domain.ledger import EventKind
from vibey.infrastructure.engines.argv import build_argv
from vibey.infrastructure.engines.classify import attribute_failure, classify_capacity
from vibey.infrastructure.engines.loop_events import translate_event_type

logger = structlog.get_logger(__name__)

# Global registry to keep subprocess.Process objects alive so they don't get
# garbage collected (which would close stdin and kill the child process).
# Key: run_id (UUID), Value: asyncio.subprocess.Process
_active_processes: dict[object, asyncio.subprocess.Process] = {}

# `<binary> run --help` output, keyed by binary name. Fetched once per
# process lifetime; --help is static for a given install, so there's
# nothing to invalidate.
_help_text_cache: dict[str, str] = {}


def _render_plan(descriptor: EngineDescriptor, prompt: str) -> str:
    """Render a vendor-compatible work plan without dropping prompt detail."""
    if descriptor.engine_id is not EngineId.CODEXLOOP:
        return prompt

    summary = next((line.strip() for line in prompt.splitlines() if line.strip()), "Complete task")
    return f"# Work Plan\n\n- [ ] {summary}\n\n## Instructions\n\n{prompt}\n"


async def _communicate(
    process: asyncio.subprocess.Process, *, timeout: float
) -> tuple[bytes, bytes]:
    """Collect subprocess output and always reap a failed or timed-out child."""
    communication = asyncio.create_task(process.communicate())
    try:
        return await asyncio.wait_for(communication, timeout=timeout)
    except BaseException:
        communication.cancel()
        with suppress(asyncio.CancelledError, Exception):
            await communication
        if process.returncode is None:
            process.kill()
        await process.wait()
        raise


class ProcessError(VibeyError):
    """Raised when a loop process fails in an unexpected way."""

    pass


def isolate_python_env(
    env: Mapping[str, str], *, venv_prefixes: tuple[str | None, ...]
) -> dict[str, str]:
    """A copy of ``env`` with the orchestrator's Python environment removed.

    Engine sessions inheriting vibey's environment mutated it live, twice:
    with VIRTUAL_ENV set and vibey's .venv/bin first on PATH, a session's
    `pip install -e .` landed editable installs INSIDE vibey's own venv
    (shadowing modules for every later gate run and even downgrading
    vibey's dev tools), and its bare `pytest`/`python` resolved to vibey's
    interpreter. The engine keeps everything else -- auth vars, HOME, the
    rest of PATH -- and provisions its own tooling like any fresh shell.
    """
    isolated = dict(env)
    for key in ("VIRTUAL_ENV", "VIRTUAL_ENV_PROMPT", "PYTHONHOME", "PYTHONPATH"):
        isolated.pop(key, None)
    prefixes = tuple(prefix for prefix in venv_prefixes if prefix)
    path = isolated.get("PATH")
    if prefixes and path:
        isolated["PATH"] = os.pathsep.join(
            part
            for part in path.split(os.pathsep)
            if not any(part == prefix or part.startswith(prefix + os.sep) for prefix in prefixes)
        )
    return isolated


@dataclass(slots=True, frozen=True)
class LoopProcessAdapter:
    """Real subprocess adapter parameterized over EngineDescriptor.

    This replaces the separate per-engine classes with one adapter that uses
    descriptor data to build argv and translate events.
    """

    descriptor: EngineDescriptor
    doctor_timeout: float = 120.0
    """`<binary> doctor` wall-clock budget for preflight. claudeloop's
    doctor verifies credentials over the network and takes ~60s warm --
    the old hardcoded 30s meant every real claudeloop preflight timed out
    into the env-var fallback, which cannot see CLI-credential auth."""

    @property
    def help_text(self) -> str | None:
        """`<binary> run --help` output, for the flags conformance check to
        verify descriptor.effort_projection/isolation_flags against.

        A plain synchronous property, not async: the conformance check reads
        it via getattr(), a sync attribute access. --help never talks to a
        vendor API or touches the filesystem beyond the binary itself, so a
        short blocking subprocess call here is a fixed, small cost, not an
        open-ended one -- unlike preflight()'s doctor/--version calls, which
        do real auth/network work and stay async.
        """
        binary = self.descriptor.binary
        if binary in _help_text_cache:
            return _help_text_cache[binary]
        if shutil.which(binary) is None:
            return None
        try:
            # A wide COLUMNS keeps Rich-based CLIs (typer/click) from
            # truncating flag names/descriptions when stdout isn't a real
            # terminal -- confirmed directly: piped without this, longer
            # flags like --append-system-prompt get cut to
            # "--append-system-pro…", which would make a real, present flag
            # look missing to a substring check.
            env = dict(os.environ, COLUMNS="250")
            result = subprocess.run(  # nosec B603 - fixed argv, never shell=True
                [binary, "run", "--help"],
                capture_output=True,
                text=True,
                timeout=10.0,
                env=env,
                check=False,
            )
            text = (result.stdout or "") + (result.stderr or "")
        except (OSError, subprocess.TimeoutExpired) as e:
            logger.warning(
                "help_text_fetch_failed",
                engine=self.descriptor.engine_id.value,
                error=str(e),
            )
            return None
        _help_text_cache[binary] = text
        return text

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
            stdout, stderr = await _communicate(proc, timeout=10.0)
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
            stdout, stderr = await _communicate(proc, timeout=self.doctor_timeout)
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
        run_dir = spec.worktree_path / self.descriptor.state_dir / "runs" / str(spec.run_id)
        # Don't create run_dir here - let the engine create it (some engines
        # like agyloop use exist_ok=False and will fail if it already exists)

        # Write the plan file if this is a new run
        if spec.session_id is None:
            plan_dir = spec.worktree_path / ".vibey" / "plans"
            plan_dir.mkdir(parents=True, exist_ok=True)
            plan_path = plan_dir / f"{spec.run_id}.md"
            plan_path.write_text(_render_plan(self.descriptor, spec.prompt))

        # Build argv using existing argv.py
        argv = build_argv(self.descriptor, spec)

        # Spawn the process
        # Don't use PIPE for stdout/stderr since we never drain them - that would
        # cause the child to block when the pipe buffer fills, or cause Python to
        # close stdin on GC when the process object goes out of scope. Use DEVNULL
        # instead since we read state from files, not stdout.
        try:
            logger.debug(
                "spawning_process",
                engine=self.descriptor.engine_id.value,
                argv=" ".join(argv),
                stdout="DEVNULL",
                stderr="DEVNULL",
            )
            process = await asyncio.create_subprocess_exec(
                *argv,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
                cwd=spec.worktree_path,
                env=isolate_python_env(
                    os.environ,
                    venv_prefixes=(os.environ.get("VIRTUAL_ENV"), sys.prefix),
                ),
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

        # Store the process object globally to prevent garbage collection
        # (which would close stdin and kill the child process)
        _active_processes[spec.run_id] = process
        logger.debug(
            "process_stored",
            run_id=str(spec.run_id),
            pid=process.pid,
            active_count=len(_active_processes),
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
        process_exited_without_status_since: float | None = None
        while True:
            try:
                lines = (await asyncio.to_thread(events_path.read_text)).splitlines()
                for line in lines[seen_lines:]:
                    if not line.strip():
                        continue
                    try:
                        raw = json.loads(line)
                        # claudeloop/agyloop write {"event_type": ..., "payload": {...}}.
                        # codexloop passes the wrapped codex CLI's own stream
                        # through nearly verbatim, where the key is "type" and
                        # the fields sit at the top level with no payload
                        # envelope. Accepting only event_type/kind meant every
                        # codexloop event was dropped as "event_missing_type" --
                        # its whole entry in LOOP_EVENT_MAP was unreachable, and
                        # conformance failures downstream (no verdict, no
                        # completion) were really this one parse gap.
                        event_type = raw.get("event_type") or raw.get("kind") or raw.get("type")
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
                        at_str = raw.get("at") or raw.get("timestamp") or raw.get("ts")
                        at = datetime.fromisoformat(at_str) if at_str else datetime.now(UTC)

                        # Enrich payload for verdict events with done_marker.
                        # agyloop's own "finished" event_type covers both
                        # success and failure (see application/runner.py),
                        # distinguished only by payload["success"] -- require
                        # it explicitly True rather than defaulting when
                        # absent, since other engines' verdict payloads use a
                        # different field ("complete", not "success") whose
                        # true/false state this code can't read here. A
                        # missing or falsy "success" must never enrich, or a
                        # failed run could report a false done_marker match.
                        # A flat event (codexloop's shape) is its own payload:
                        # success/complete/done_marker/usage live at the top
                        # level, so an empty dict here would discard exactly
                        # the fields every consumer downstream reads.
                        if "payload" in raw:
                            payload = dict(raw.get("payload", {}))
                        else:
                            payload = {
                                k: v
                                for k, v in raw.items()
                                if k not in {"event_type", "kind", "type", "at", "timestamp", "ts"}
                            }
                        if (
                            kind == EventKind.VERDICT_RENDERED
                            and "done_marker" not in payload
                            and payload.get("success") is True
                        ):
                            payload["done_marker"] = self.descriptor.done_marker
                        # Normalize the completion key: claudeloop/agyloop
                        # verdict payloads say {"success": bool} while every
                        # vibey consumer (run_and_record, the brief builder)
                        # reads {"complete": bool}. Caught live: a real
                        # claudeloop run finished its item, rendered
                        # success=true, and the handler still failed it as
                        # "did not report completion".
                        if (
                            kind == EventKind.VERDICT_RENDERED
                            and "complete" not in payload
                            and "success" in payload
                        ):
                            payload["complete"] = payload.get("success") is True

                        # Yield translated event
                        yield EngineEvent(
                            kind=kind.value,  # EventKind enum value
                            at=at,
                            payload=payload,
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

                # Check if done via meta.json's own status field. Every loop
                # engine's RunMeta documents the same terminal vocabulary
                # (active | stopped | finished | failed) -- none of the four
                # ever write the literal "complete". Checking for that
                # non-existent value meant this loop never broke on its own
                # for any real engine and ran until the read raised (or, if
                # nothing ever raised, forever).
                meta_path = handle.run_dir / "meta.json"
                if meta_path.exists():
                    meta = json.loads(meta_path.read_text())
                    if meta.get("status") in ("finished", "failed", "stopped"):
                        break

                # A well-behaved engine always writes a terminal status
                # before its process exits. A crash, an early validation
                # failure (confirmed real: codexloop exits immediately with
                # "work plan has no checkbox items" and never touches
                # meta.json's status field), or an unhandled signal means
                # nothing will ever flip that status -- without this check
                # the loop above spins forever, exactly the failure mode its
                # own comment already warned about. Give one extra poll
                # interval after first observing the exit, in case the
                # terminal status write and process exit are racing each
                # other, then give up rather than hang indefinitely.
                process = _active_processes.get(handle.run_id)
                if process is not None and process.returncode is not None:
                    now = asyncio.get_running_loop().time()
                    if process_exited_without_status_since is None:
                        process_exited_without_status_since = now
                    elif now - process_exited_without_status_since > 1.0:
                        logger.warning(
                            "process_exited_without_terminal_status",
                            run_id=str(handle.run_id),
                            returncode=process.returncode,
                        )
                        break
                else:
                    process_exited_without_status_since = None

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

    def run_exit_code(self, handle: RunHandle) -> int | None:
        """Optional capability (discovered via ``hasattr``): the spawned
        process's exit code, or None while it still runs or once ``stop``
        has released the process reference. Read it after ``tail`` drains
        and before ``stop`` -- EXIT_CODE_WIND_DOWN here is the wind-down
        handoff signal."""
        process = _active_processes.get(handle.run_id)
        return None if process is None else process.returncode

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

        # Clean up the process reference
        process = _active_processes.pop(handle.run_id, None)
        if process is not None:
            if process.returncode is None:
                try:
                    await asyncio.wait_for(process.wait(), timeout=2.0)
                except TimeoutError:
                    try:
                        process.terminate()
                        await asyncio.wait_for(process.wait(), timeout=1.0)
                    # The process is already removed from the registry; termination is best-effort.
                    except Exception:  # noqa: BLE001  # nosec B110
                        pass
            else:
                await process.wait()

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
