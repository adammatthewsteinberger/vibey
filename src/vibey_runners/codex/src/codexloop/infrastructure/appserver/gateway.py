# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Long-lived ``codex app-server`` session implementing :class:`AgentGateway`.

Optional second transport (R10 / ADR 0009). Speaks newline-delimited JSON-RPC
without a ``"jsonrpc"`` key. Auto-answers approval requests. Mid-turn stop and
steer use ``turn/interrupt`` / ``turn/steer``.

The fake shim under ``tests/shim/fake_appserver.py`` defines the contract this
adapter is tested against. Live ``codex app-server`` remains experimental; when
capability probing fails, bootstrap falls back to exec.
"""

from __future__ import annotations

import json
import os
import signal
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final, assert_never

import anyio
from anyio import EndOfStream
from anyio.abc import ByteReceiveStream, ByteSendStream, Process

from codexloop.application.dto import TokenUsage, TurnOutcome
from codexloop.application.ports import Logger, PermissionMode
from codexloop.domain.approval import ApprovalPolicy, SandboxMode
from codexloop.domain.model_profile import ModelEffortProfile
from codexloop.domain.signals import TurnSignals
from codexloop.infrastructure.appserver.client import DEFAULT_ARGV

_KILL_GRACE_SECONDS: Final[float] = 0.5
_RECEIVE_CHUNK: Final[int] = 8192
_MAX_LINE_BYTES: Final[int] = 1_048_576
_DEFAULT_TIMEOUT: Final[float] = 30.0
_CONSUME_METHOD: Final[str] = "account/rateLimitResetCredit/consume"


@dataclass(slots=True)
class _PendingTurn:
    turn_id: str | None = None
    final_message: str | None = None
    completed: bool = False
    failed: bool = False
    error_code: str | None = None
    error_type: str | None = None


class CodexAppServerGateway:
    """Bidirectional app-server adapter behind :class:`AgentGateway`."""

    def __init__(
        self,
        *,
        cwd: str | Path,
        argv: Sequence[str] | None = None,
        env: Mapping[str, str] | None = None,
        timeout: float = _DEFAULT_TIMEOUT,
        logger: Logger | None = None,
        model: str | None = None,
        approval: ApprovalPolicy = ApprovalPolicy.NEVER,
        sandbox: SandboxMode = SandboxMode.WORKSPACE_WRITE,
    ) -> None:
        self._cwd = Path(cwd)
        self._argv = list(DEFAULT_ARGV if argv is None else argv)
        self._env = dict(env) if env is not None else None
        self._timeout = timeout
        self._logger = logger
        self._model = model
        self._approval = approval
        self._sandbox = sandbox
        self._thread_id: str | None = None
        self._closed = False
        self._process: Process | None = None
        self._stdin: ByteSendStream | None = None
        self._reader: _LineReader | None = None
        self._next_id = 1
        self._pending: _PendingTurn | None = None
        self._lock = anyio.Lock()

    async def probe_capabilities(self) -> bool:
        """Return True when initialize + initialized succeed."""
        try:
            await self._ensure_session()
            return True
        except Exception:
            await self.close()
            return False

    async def send_turn(self, prompt: str) -> TurnOutcome:
        async with self._lock:
            await self._ensure_session()
            if self._stdin is None or self._reader is None:  # pragma: no cover
                msg = "app-server session missing streams"
                raise RuntimeError(msg)
            if self._thread_id is None:
                self._pending = _PendingTurn()
                started = await self._request(
                    "thread/start",
                    {
                        "input": [{"type": "text", "text": prompt}],
                        "model": self._model,
                    },
                )
                self._thread_id = _dig_str(started, "thread", "id") or _dig_str(started, "id")
                if self._thread_id is None:  # pragma: no cover — shim always returns an id
                    self._pending = None
                    return _failed_outcome("thread_start_missing_id")
            else:
                self._pending = _PendingTurn()
                await self._request(
                    "turn/start",
                    {
                        "threadId": self._thread_id,
                        "input": [{"type": "text", "text": prompt}],
                    },
                )
            await self._drain_until_turn_done()
            pending = self._pending
            self._pending = None
            if pending is None:  # pragma: no cover — pending set before drain
                return _failed_outcome("turn_missing_state")
            signals = TurnSignals(
                error_code=pending.error_code,
                error_type=pending.error_type,
                completed=pending.completed and not pending.failed,
                failed=pending.failed,
                final_message=pending.final_message,
                exit_code=1 if pending.failed else 0,
            )
            return TurnOutcome(
                signals=signals,
                usage=TokenUsage(),
                exit_code=signals.exit_code,
                thread_id=self._thread_id,
            )

    async def interrupt_turn(self) -> None:
        """True mid-turn stop via ``turn/interrupt``."""
        async with self._lock:
            if self._pending is None or self._pending.turn_id is None:
                return
            await self._request("turn/interrupt", {"turnId": self._pending.turn_id})

    async def steer_turn(self, text: str) -> None:
        """Inject an operator prompt into the running turn via ``turn/steer``."""
        async with self._lock:
            if self._pending is None or self._pending.turn_id is None:
                return
            await self._request(
                "turn/steer",
                {
                    "turnId": self._pending.turn_id,
                    "input": [{"type": "text", "text": text}],
                },
            )

    async def close(self) -> None:
        if self._closed and self._process is None:
            return
        self._closed = True
        process = self._process
        self._process = None
        self._stdin = None
        self._reader = None
        if process is not None:
            await _terminate_group(process)
            with anyio.CancelScope(shield=True):
                await process.aclose()

    async def set_profile(self, profile: ModelEffortProfile) -> None:
        self._model = profile.model

    async def set_permission_mode(self, mode: PermissionMode) -> None:
        match mode:
            case PermissionMode.AUTONOMOUS:
                self._approval, self._sandbox = (
                    ApprovalPolicy.NEVER,
                    SandboxMode.WORKSPACE_WRITE,
                )
            case PermissionMode.READ_ONLY:
                self._approval, self._sandbox = ApprovalPolicy.NEVER, SandboxMode.READ_ONLY
            case PermissionMode.FULL_ACCESS:
                self._approval, self._sandbox = (
                    ApprovalPolicy.NEVER,
                    SandboxMode.DANGER_FULL_ACCESS,
                )
            case _:  # pragma: no cover — exhaustive StrEnum
                assert_never(mode)

    async def set_cwd(self, path: str) -> None:
        self._cwd = Path(path)

    async def set_session_resources(self, resources: Mapping[str, object]) -> None:
        approval = resources.get("approval_policy")
        if isinstance(approval, str):
            self._approval = ApprovalPolicy(approval)
        sandbox = resources.get("sandbox_mode")
        if isinstance(sandbox, str):
            self._sandbox = SandboxMode(sandbox)

    def resolve_tool_approval(self, request_id: str, *, allow: bool, reason: str = "") -> bool:
        del request_id, reason
        return allow

    async def _ensure_session(self) -> None:
        if self._process is not None and self._stdin is not None and self._reader is not None:
            self._closed = False
            return
        env = self._env if self._env is not None else os.environ.copy()
        process = await anyio.open_process(
            self._argv,
            cwd=os.fspath(self._cwd),
            env=env,
            start_new_session=True,
        )
        if process.stdin is None or process.stdout is None:  # pragma: no cover
            await process.aclose()
            msg = "app-server process missing stdio"
            raise RuntimeError(msg)
        self._process = process
        self._stdin = process.stdin
        self._reader = _LineReader(process.stdout)
        self._closed = False
        init = await self._request(
            "initialize",
            {
                "clientInfo": {
                    "name": "codexloop",
                    "title": "codexloop",
                    "version": "0.1.0",
                },
                "capabilities": {"experimentalApi": True},
            },
        )
        if init is None:  # pragma: no cover — probed via shim init_fail
            msg = "app-server initialize failed"
            raise RuntimeError(msg)
        await _send(self._stdin, {"method": "initialized", "params": {}})

    async def _request(
        self,
        method: str,
        params: Mapping[str, object] | None = None,
    ) -> dict[str, Any] | None:
        if self._stdin is None or self._reader is None:  # pragma: no cover
            return None
        req_id = self._next_id
        self._next_id += 1
        message: dict[str, object] = {"id": req_id, "method": method}
        if params is not None:
            message["params"] = dict(params)
        if not await _send(self._stdin, message):  # pragma: no cover — consume guard
            return None
        try:
            with anyio.fail_after(self._timeout):
                while True:
                    msg = await self._reader.read_line()
                    if msg is None:  # pragma: no cover — EOF mid-request
                        return None
                    if await self._handle_notification(msg):
                        continue  # pragma: no cover — notifications usually arrive in drain
                    if msg.get("id") == req_id:
                        if _rpc_error(msg) is not None:  # pragma: no cover
                            return None
                        result = msg.get("result")
                        return dict(result) if isinstance(result, Mapping) else {"result": result}
        except TimeoutError:  # pragma: no cover — timed waits covered elsewhere
            return None

    async def _drain_until_turn_done(self) -> None:
        if self._reader is None or self._pending is None:  # pragma: no cover
            return
        try:
            with anyio.fail_after(self._timeout):
                while not self._pending.completed and not self._pending.failed:
                    msg = await self._reader.read_line()
                    if msg is None:  # pragma: no cover
                        self._pending.failed = True
                        self._pending.error_code = "stream_ended"
                        return
                    await self._handle_notification(msg)
        except TimeoutError:  # pragma: no cover
            self._pending.failed = True
            self._pending.error_code = "turn_timeout"

    async def _handle_notification(self, msg: Mapping[str, Any]) -> bool:
        method = msg.get("method")
        if not isinstance(method, str):
            return False
        params = msg.get("params")
        params_map = dict(params) if isinstance(params, Mapping) else {}
        if method in {"turn/started", "turn.started"}:
            if self._pending is not None:  # pragma: no branch
                self._pending.turn_id = _dig_str(params_map, "turn", "id") or _dig_str(
                    params_map, "turnId"
                )
            return True
        if method in {"item/agentMessage/delta", "turn/outputDelta"}:
            text = params_map.get("delta") or params_map.get("text")
            if self._pending is not None and isinstance(text, str):  # pragma: no branch
                prev = self._pending.final_message or ""
                self._pending.final_message = prev + text
            return True
        if method in {"turn/completed", "turn.completed"}:
            if self._pending is not None:  # pragma: no branch
                self._pending.completed = True
                final = params_map.get("finalMessage") or params_map.get("message")
                if isinstance(final, str):  # pragma: no branch
                    self._pending.final_message = final
            return True
        if method in {"turn/failed", "turn.failed"}:
            if self._pending is not None:  # pragma: no branch
                self._pending.failed = True
                self._pending.error_code = str(params_map.get("code") or "turn_failed")
                err_type = params_map.get("type")
                self._pending.error_type = str(err_type) if err_type is not None else None
            return True
        if method in {"approval/request", "tool/approval/request"}:
            req_id = params_map.get("requestId") or params_map.get("id")
            await self._answer_approval(str(req_id) if req_id is not None else "0", allow=True)
            return True
        return False

    async def _answer_approval(self, request_id: str, *, allow: bool) -> None:
        if self._stdin is None:  # pragma: no cover
            return
        await _send(
            self._stdin,
            {
                "method": "approval/respond",
                "params": {"requestId": request_id, "allow": allow},
            },
        )


def _failed_outcome(code: str) -> TurnOutcome:  # pragma: no cover — defensive helper
    return TurnOutcome(
        signals=TurnSignals(failed=True, error_code=code, exit_code=1),
        exit_code=1,
    )


def _dig_str(obj: Mapping[str, Any] | None, *keys: str) -> str | None:
    cur: Any = obj
    for key in keys:
        if not isinstance(cur, Mapping):
            return None
        cur = cur.get(key)
    return cur if isinstance(cur, str) else None


async def _send(stdin: ByteSendStream, message: Mapping[str, object]) -> bool:
    if message.get("method") == _CONSUME_METHOD:  # pragma: no cover — never-consume guard
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
    if error is not None:  # pragma: no cover — non-mapping error payloads
        return {"message": str(error)}
    return None


async def _terminate_group(process: Process) -> None:  # pragma: no cover — process teardown races
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
    except ProcessLookupError:  # pragma: no cover — race with process exit
        return
    except OSError:  # pragma: no cover — fallback when killpg unsupported
        try:
            os.kill(pid, sig)
        except (ProcessLookupError, OSError):
            return


class _LineReader:
    def __init__(self, stream: ByteReceiveStream) -> None:
        self._stream = stream
        self._buf = bytearray()

    async def read_line(self) -> dict[str, Any] | None:
        while True:
            newline = self._buf.find(b"\n")
            if newline >= 0:
                raw = bytes(self._buf[:newline])
                del self._buf[: newline + 1]
                if not raw.strip():
                    continue
                try:
                    data = json.loads(raw.decode("utf-8"))
                except (UnicodeDecodeError, json.JSONDecodeError):  # pragma: no cover
                    continue
                return data if isinstance(data, dict) else None
            if len(self._buf) > _MAX_LINE_BYTES:  # pragma: no cover — pathological line
                self._buf.clear()
                return None
            try:
                chunk = await self._stream.receive(_RECEIVE_CHUNK)
            except EndOfStream:
                return None
            if not chunk:  # pragma: no cover
                return None
            self._buf.extend(chunk)


async def probe_app_server_transport(
    *,
    cwd: Path,
    argv: Sequence[str] | None = None,
    env: Mapping[str, str] | None = None,
) -> tuple[CodexAppServerGateway | None, str | None]:
    """Capability probe. Returns ``(gateway, None)`` or ``(None, reason)``."""
    gateway = CodexAppServerGateway(cwd=cwd, argv=argv, env=env, timeout=5.0)
    ok = await gateway.probe_capabilities()
    if ok:
        return gateway, None
    return None, "app-server initialize failed; falling back to exec"
