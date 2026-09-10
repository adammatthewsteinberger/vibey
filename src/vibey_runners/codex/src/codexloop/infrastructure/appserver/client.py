# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Stdio JSON-RPC client for ``codex app-server`` (R6).

Newline-delimited JSON with **no** ``"jsonrpc"`` key. Handshake is
``initialize`` (with ``capabilities.experimentalApi: true``) → ``initialized``
→ call. ``account/rateLimitResetCredit/consume`` is never sent.
"""

from __future__ import annotations

import json
import os
import signal
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Final

import anyio
from anyio import EndOfStream
from anyio.abc import ByteReceiveStream, ByteSendStream, Process

from codexloop.application.ports import Logger
from codexloop.domain.capacity import PlanWindows
from codexloop.infrastructure.appserver.ratelimits import plan_windows_from_rpc

DEFAULT_ARGV: Final[list[str]] = ["codex", "app-server", "--stdio"]
DEFAULT_TIMEOUT: Final[float] = 5.0
_KILL_GRACE_SECONDS: Final[float] = 0.5
_RECEIVE_CHUNK: Final[int] = 8192
_MAX_LINE_BYTES: Final[int] = 1_048_576
_READ_METHOD: Final[str] = "account/rateLimits/read"
_CONSUME_METHOD: Final[str] = "account/rateLimitResetCredit/consume"

_INITIALIZE: Final[dict[str, object]] = {
    "id": 1,
    "method": "initialize",
    "params": {
        "clientInfo": {"name": "codexloop", "title": "codexloop", "version": "0.1.0"},
        "capabilities": {"experimentalApi": True},
    },
}
_INITIALIZED: Final[dict[str, object]] = {"method": "initialized", "params": {}}
_READ_RATE_LIMITS: Final[dict[str, object]] = {"id": 2, "method": _READ_METHOD}


class AppServerClient:
    """One-shot stdio session: handshake, ``read_rate_limits``, then teardown."""

    def __init__(
        self,
        *,
        argv: Sequence[str] | None = None,
        cwd: str | Path | None = None,
        env: Mapping[str, str] | None = None,
        timeout: float = DEFAULT_TIMEOUT,
        logger: Logger | None = None,
        now: datetime | None = None,
    ) -> None:
        self._argv = list(DEFAULT_ARGV if argv is None else argv)
        self._cwd = Path.cwd() if cwd is None else Path(cwd)
        self._env = dict(env) if env is not None else None
        self._timeout = timeout
        self._logger = logger
        self._now = now

    async def read_rate_limits(self) -> PlanWindows | None:
        """Return plan windows, or ``None`` on any failure. Never raises."""
        try:
            return await self._read_rate_limits()
        except Exception:  # pragma: no cover — best-effort probe
            return None

    async def _read_rate_limits(self) -> PlanWindows | None:
        env = self._env if self._env is not None else os.environ.copy()
        try:
            process = await anyio.open_process(
                self._argv,
                cwd=os.fspath(self._cwd),
                env=env,
                start_new_session=True,
            )
        except OSError:  # pragma: no cover — spawn failure
            return None
        try:
            return await self._exchange(process)
        finally:
            await _terminate_group(process)
            with anyio.CancelScope(shield=True):
                await process.aclose()

    async def _exchange(self, process: Process) -> PlanWindows | None:
        stdin = process.stdin
        stdout = process.stdout
        if stdin is None or stdout is None:  # pragma: no cover
            return None
        reader = _LineReader(stdout)
        windows: PlanWindows | None = None
        async with anyio.create_task_group() as tg:
            if process.stderr is not None:  # pragma: no branch
                tg.start_soon(_drain_stderr, process.stderr)
            try:
                windows = await self._session(stdin, reader)
            finally:
                tg.cancel_scope.cancel()
        return windows

    async def _session(self, stdin: ByteSendStream, reader: _LineReader) -> PlanWindows | None:
        init = await self._request(stdin, reader, dict(_INITIALIZE), request_id=1)
        if init is None or _rpc_error(init) is not None:
            return None
        await _send(stdin, dict(_INITIALIZED))
        response = await self._request(stdin, reader, dict(_READ_RATE_LIMITS), request_id=2)
        if response is None:
            return None
        error = _rpc_error(response)
        if error is not None:
            self._warn_missing_capability(error)
            return None
        result = response.get("result")
        now = self._now if self._now is not None else datetime.now(UTC)
        return plan_windows_from_rpc(result, now=now)

    async def _request(
        self,
        stdin: ByteSendStream,
        reader: _LineReader,
        message: Mapping[str, object],
        *,
        request_id: int,
    ) -> dict[str, Any] | None:
        if not await _send(stdin, message):  # pragma: no cover — consume guard
            return None
        try:
            with anyio.fail_after(self._timeout):
                return await reader.read_matching(request_id)
        except TimeoutError:  # pragma: no cover
            return None

    def _warn_missing_capability(self, error: Mapping[str, object]) -> None:
        raw = error.get("message")
        text = raw if isinstance(raw, str) else ""
        if "experimentalapi" not in text.lower():
            return
        if self._logger is None:  # pragma: no cover
            return
        self._logger.warning("appserver_missing_capability", error=text)


async def _send(stdin: ByteSendStream, message: Mapping[str, object]) -> bool:
    if message.get("method") == _CONSUME_METHOD:  # pragma: no cover — never-consume
        return False
    payload = dict(message)
    payload.pop("jsonrpc", None)
    line = json.dumps(payload, separators=(",", ":")).encode("utf-8") + b"\n"
    await stdin.send(line)
    return True


def _rpc_error(response: Mapping[str, Any]) -> Mapping[str, object] | None:
    error = response.get("error")
    if isinstance(error, Mapping):
        return dict(error)
    if error is not None:
        return {"message": str(error)}  # pragma: no cover — non-mapping error
    return None


async def _drain_stderr(stream: ByteReceiveStream) -> None:
    while True:
        try:
            await stream.receive(_RECEIVE_CHUNK)
        except EndOfStream:
            break


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
    except ProcessLookupError:  # pragma: no cover
        return
    except OSError:  # pragma: no cover
        try:
            os.kill(pid, sig)
        except (ProcessLookupError, OSError):
            return


class _LineReader:
    def __init__(self, stream: ByteReceiveStream, *, max_line_bytes: int = _MAX_LINE_BYTES) -> None:
        self._stream = stream
        self._max_line_bytes = max_line_bytes
        self._buf = bytearray()
        self._eof = False

    async def read_matching(self, request_id: int) -> dict[str, Any] | None:
        while True:
            line = await self._readline()
            if line is None:
                return None
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                return None
            if not isinstance(obj, dict):  # pragma: no cover
                return None
            if obj.get("id") == request_id:
                return obj

    async def _readline(self) -> str | None:
        while True:
            nl = self._buf.find(b"\n")
            if nl != -1:
                raw = bytes(self._buf[:nl])
                del self._buf[: nl + 1]
                if len(raw) > self._max_line_bytes:  # pragma: no cover
                    return None
                return raw.decode("utf-8", errors="replace")
            if self._eof:
                if not self._buf:  # pragma: no branch — trailing buffer rare
                    return None
                raw = bytes(self._buf)  # pragma: no cover
                self._buf.clear()  # pragma: no cover
                if len(raw) > self._max_line_bytes:  # pragma: no cover
                    return None
                return raw.decode("utf-8", errors="replace")  # pragma: no cover
            try:
                chunk = await self._stream.receive(_RECEIVE_CHUNK)
            except EndOfStream:
                self._eof = True
                continue
            if not chunk:  # pragma: no cover
                self._eof = True
                continue
            self._buf.extend(chunk)
