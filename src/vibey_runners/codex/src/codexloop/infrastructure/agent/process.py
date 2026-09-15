# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Supervised ``codex`` subprocess: concurrent pumps and process-group teardown.

``ProcessResult.stderr_tail`` is the last :data:`STDERR_TAIL_BYTES` (8 KiB) of
stderr, not the full stream. Oversized stdout lines are truncated to
``max_line_bytes`` and counted in ``truncated_lines``; they never raise and
never accumulate past that ceiling.
"""

from __future__ import annotations

import os
import signal
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final

import anyio
from anyio import EndOfStream
from anyio.abc import ByteReceiveStream, Process

from codexloop.domain.errors import CodexBinaryError

STDERR_TAIL_BYTES: Final[int] = 8 * 1024
_KILL_GRACE_SECONDS: Final[float] = 0.5
_RECEIVE_CHUNK: Final[int] = 8192


@dataclass(frozen=True, slots=True)
class ProcessResult:
    stdout_lines: list[str]
    stderr_tail: str
    exit_code: int
    truncated_lines: int


async def run_codex(
    argv: Sequence[str],
    *,
    cwd: str | Path,
    env: Mapping[str, str],
    timeout: float,
    max_line_bytes: int,
) -> ProcessResult:
    """Run ``argv`` (no shell) with concurrent stdout/stderr pumps.

    The child is started in its own session (``start_new_session=True``) so
    timeout and cancellation send ``SIGTERM`` then ``SIGKILL`` to the whole
    process group. Stdin is ``DEVNULL`` (not a TTY; reads return EOF).
    """
    if not argv:
        raise CodexBinaryError("argv must be a non-empty list")

    stdout_collector = _StdoutCollector(max_line_bytes)
    stderr_collector = _StderrTail()
    # Child stdin is not a TTY; reads return EOF immediately.
    devnull_fd = os.open(os.devnull, os.O_RDONLY)
    try:
        process = await anyio.open_process(
            list(argv),
            stdin=devnull_fd,
            cwd=os.fspath(cwd),
            env=dict(env),
            start_new_session=True,
        )
    finally:
        os.close(devnull_fd)
    try:
        with anyio.fail_after(timeout):
            async with anyio.create_task_group() as tg:
                if process.stdout is not None:  # pragma: no branch
                    tg.start_soon(_pump_stdout, process.stdout, stdout_collector, max_line_bytes)
                if process.stderr is not None:  # pragma: no branch
                    tg.start_soon(_pump_stderr, process.stderr, stderr_collector)
                await process.wait()
    except TimeoutError:
        await _terminate_group(process)
        raise CodexBinaryError(f"timed out after {timeout}s") from None
    except BaseException:
        await _terminate_group(process)
        raise
    else:
        code = process.returncode
        return ProcessResult(
            stdout_lines=stdout_collector.lines,
            stderr_tail=stderr_collector.text(),
            exit_code=0 if code is None else code,
            truncated_lines=stdout_collector.truncated_lines,
        )
    finally:
        with anyio.CancelScope(shield=True):
            await process.aclose()


async def _pump_stdout(
    stream: ByteReceiveStream,
    collector: _StdoutCollector,
    max_line_bytes: int,
) -> None:
    chunk_size = max(1, min(_RECEIVE_CHUNK, max_line_bytes))
    try:
        while True:
            try:
                chunk = await stream.receive(chunk_size)
            except EndOfStream:
                break
            collector.feed(chunk)
    finally:
        collector.flush()


async def _pump_stderr(stream: ByteReceiveStream, collector: _StderrTail) -> None:
    while True:
        try:
            chunk = await stream.receive(_RECEIVE_CHUNK)
        except EndOfStream:
            break
        collector.feed(chunk)


async def _terminate_group(process: Process) -> None:
    pid = process.pid
    with anyio.CancelScope(shield=True):
        _signal_group(pid, signal.SIGTERM)
        with anyio.move_on_after(_KILL_GRACE_SECONDS):
            await process.wait()
        _signal_group(pid, signal.SIGKILL)
        with anyio.move_on_after(2.0):
            await process.wait()


def _signal_group(pid: int, sig: int) -> None:
    try:
        os.killpg(pid, sig)
    except ProcessLookupError:  # pragma: no cover — process already gone
        return
    except OSError:  # pragma: no cover — fall back to kill(pid)
        try:
            os.kill(pid, sig)
        except (ProcessLookupError, OSError):
            return


class _StdoutCollector:
    """Bound stdout to ``max_line_bytes`` per line; skip overflow until newline."""

    def __init__(self, max_line_bytes: int) -> None:
        self.max_line_bytes = max_line_bytes
        self.lines: list[str] = []
        self.truncated_lines = 0
        self._buf = bytearray()
        self._skipping = False

    def feed(self, chunk: bytes) -> None:
        offset = 0
        length = len(chunk)
        while offset < length:
            if self._skipping:
                nl = chunk.find(b"\n", offset)
                if nl == -1:
                    return
                self._skipping = False
                offset = nl + 1
                continue
            nl = chunk.find(b"\n", offset)
            end = length if nl == -1 else nl
            piece = chunk[offset:end]
            space = self.max_line_bytes - len(self._buf)
            if len(piece) > space:
                if space > 0:
                    self._buf.extend(piece[:space])
                self._emit(truncated=True)
                if nl == -1:
                    self._skipping = True
                    return
                offset = nl + 1
                continue
            self._buf.extend(piece)
            if nl == -1:
                return
            self._emit(truncated=False)
            offset = nl + 1

    def flush(self) -> None:
        if self._buf:
            self._emit(truncated=False)

    def _emit(self, *, truncated: bool) -> None:
        if truncated:
            self.truncated_lines += 1
        self.lines.append(bytes(self._buf).decode("utf-8", errors="replace"))
        self._buf.clear()


class _StderrTail:
    """Rolling last-``STDERR_TAIL_BYTES`` of stderr."""

    def __init__(self) -> None:
        self._buf = bytearray()

    def feed(self, chunk: bytes) -> None:
        self._buf.extend(chunk)
        extra = len(self._buf) - STDERR_TAIL_BYTES
        if extra > 0:
            del self._buf[:extra]

    def text(self) -> str:
        return bytes(self._buf).decode("utf-8", errors="replace")
